#!/usr/bin/env node
// evals/run-gemini.js
//
// 지금까지 사용자가 수동으로 하던 "시나리오별 noskill/skill 프로젝트
// 생성 → Gemini에 request.txt 전달 → 결과 저장"을 자동화한다.
// Google AI Studio에서 발급받은 Gemini API 키(Gemini Interactions API,
// generativelanguage.googleapis.com)를 쓴다.
//
// [조사 결과 — 지어내지 않음, 원문 인용]
// Gemini API(REST, API 키로 직접 호출)에는 "파일 시스템 기반 스킬 자동
// 발견" 기능이 없다. 그건 Gemini CLI/Antigravity라는 *클라이언트*의
// 기능이다 — Gemini CLI 공식 문서: "Gemini CLI automatically discovers
// skills in the .gemini/skills directory... injects the name and
// description of all enabled skills into the system prompt."
// (geminicli.com/docs/cli/skills/, ai.google.dev와는 다른 문서다)
// 반면 공식 API 레퍼런스(ai.google.dev/gemini-api/docs/tools)에는
// "skills"라는 단어 자체가 등장하지 않는다 — REST API 레벨에서는
// 존재하지 않는 개념이다.
// 그래서 여기서는 "SKILL.md + references/*.md 전체 내용을
// system_instruction에 통째로 주입하는 방식"으로 Claude Code의 스킬
// 로딩과 개념적으로 대응시킨다 — Claude Code도 Messages API 레벨에는
// "스킬"이 없고, Claude Code(클라이언트)가 스킬 본문을 컨텍스트에
// 주입하는 것과 정확히 같은 구조다.
//
// [절대 원칙 1] Gemini에게 가는 "사용자 메시지"(input)는 항상
// evals/subjects/{N}/request.txt 내용 그대로다. 테스트 메타정보
// (시나리오 번호, 컴포넌트 이름, 채점 기준 등)를 어떤 형태로도 섞지
// 않는다. 파일 내용과 응답 형식 지시는 user 메시지가 아니라
// system_instruction(맥락)에 넣는다 — 지시 2번("파일 내용을 컨텍스트로
// 포함, request.txt를 사용자 메시지로")이 명시한 그 구분을 그대로
// 따른 것이다.
//
// [절대 원칙 6] 각 호출은 멀티턴 히스토리 없는 단일 요청이다 —
// Interactions API에 대화 ID를 넘기지 않는다. 이전 시나리오의 맥락이
// 다음 호출로 새지 않는다.
//
// [무료 티어 rate limit 조사 — 확인된 것과 못 한 것을 구분한다]
// 공식 문서(ai.google.dev/gemini-api/docs/rate-limits)를 직접 확인한
// 결과, 모델별 정확한 RPM/RPD 수치는 그 문서에 실려 있지 않다 — 문서
// 원문: "Rate limits depend on a variety of factors (such as your usage
// tier) and can be viewed in Google AI Studio." 즉 정확한 숫자는
// 로그인한 AI Studio 대시보드에서만 보이고, 이 스크립트(API 키만 있는
// 비대화형 환경)는 그 대시보드에 접근할 수 없다 — **정확한 한도는
// 미확인**이다. 여러 비공식 3rd-party 요약(aifreeapi.com,
// tinkerllm.com 등, ai.google.dev 원문 아님)이 최근 Flash 계열
// 무료 티어를 대략 "10 RPM" 안팎으로 공통되게 적고 있어 참고 삼아
// 안전 여유를 크게 두는 근거로만 쓴다 — 이건 [관행] 수준의 정황이지
// [표준]이 아니다.
// 그래서 호출 사이에 고정 지연을 넣는다: 12회(6개 시나리오 ×
// noskill/skill)를 8초 간격으로 실행하면 어떤 1분 구간에도 최대
// 7~8회만 들어가서, 위 정황상 하한(10 RPM)보다 충분히 낮다.
const SLEEP_BETWEEN_CALLS_MS = 8000;

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const SUBJECTS_DIR = path.join(__dirname, "subjects");
const SKILL_DIR = path.join(ROOT, ".claude", "skills", "interaction-doctor");
const RUNS_DIR = path.join(__dirname, "runs");

// 2026-08-30 밤 실행에서 fetch() 호출에 타임아웃이 전혀 없다는 게
// grep으로 직접 확인됐다("fetch(" 딱 1곳, AbortController/timeout/
// signal 전부 0건) — 05~08번 8건이 전부 뭉뚱그려진 "fetch failed"로
// 실패했고, 시도 사이 간격이 20분~2시간까지 벌어져서 진짜 멈춘
// 건지 응답을 오래 기다린 건지조차 구분할 수 없었다. 아래 세 상수가
// 그걸 고친다.
const FETCH_TIMEOUT_MS = 30000;
const MAX_RETRIES = 2; // 최초 시도 + 최대 재시도 2회 = 최대 3회 시도
const RETRY_DELAY_MS = 5000;

const API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions";
const MODEL = process.env.GEMINI_MODEL || "gemini-3.6-flash";
// gemini-3.6-flash: 공식 문서 표현 그대로 "Our most intelligent model for
// sustained frontier performance in agentic and coding tasks" — 코딩
// 과제라 이걸 기본값으로 쓴다. 특정 버전에 고정해서 실험 재현성을
// 지킨다("latest" 별칭 대신).

// 출처: https://ai.google.dev/gemini-api/docs/pricing (2026-08-30 확인,
// gemini-3.6-flash, Standard tier, 2026-12-31까지 유효한 가격).
// "$0.75 through December 31, 2026" (input) / "$3.75 through December
// 31, 2026" (output), 둘 다 1M 토큰당. 아래 추정치는 문자수/4를 토큰
// 수 근사치로 쓰는 대략적인 상한 추정이다 — 실제 청구액과 다를 수
// 있다(모델의 실제 토크나이저 기준이 아님을 명시).
const PRICE_PER_1M_INPUT_TOKENS_USD = 0.75;
const PRICE_PER_1M_OUTPUT_TOKENS_USD = 3.75;
const CHARS_PER_TOKEN_APPROX = 4;
const ASSUMED_OUTPUT_TOKENS_APPROX = 2000; // 이전 4회 실측(코드 2.6~4.1KB) 기준 여유있게 잡은 상한

function estimateCostUsd(systemInstructionLen, userInputLen) {
	const inputTokens = (systemInstructionLen + userInputLen) / CHARS_PER_TOKEN_APPROX;
	const inputCost = (inputTokens / 1_000_000) * PRICE_PER_1M_INPUT_TOKENS_USD;
	const outputCost = (ASSUMED_OUTPUT_TOKENS_APPROX / 1_000_000) * PRICE_PER_1M_OUTPUT_TOKENS_USD;
	return inputCost + outputCost;
}

// ---- .env 로더 (의존성 추가 없이 직접 파싱, 프로젝트 루트 기준) ----
function loadDotEnv() {
	const envPath = path.join(ROOT, ".env");
	if (!fs.existsSync(envPath)) return;
	const lines = fs.readFileSync(envPath, "utf8").split("\n");
	for (const raw of lines) {
		const line = raw.trim();
		if (!line || line.startsWith("#")) continue;
		const eq = line.indexOf("=");
		if (eq === -1) continue;
		const key = line.slice(0, eq).trim();
		let value = line.slice(eq + 1).trim();
		if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
			value = value.slice(1, -1);
		}
		if (!(key in process.env)) process.env[key] = value; // 이미 있는 실제 env var 우선
	}
}
loadDotEnv();

const API_KEY = process.env.GEMINI_API_KEY;
// 키 값 자체는 로그에 절대 남기지 않는다 — 아래 saveJson 등에서 이
// 변수를 직접 넘기지 않도록 주의해서 다룬다.

function listScenarios() {
	return fs
		.readdirSync(SUBJECTS_DIR, { withFileTypes: true })
		.filter((d) => d.isDirectory())
		.map((d) => d.name)
		.sort();
}

function readSkillContent() {
	const skillMd = fs.readFileSync(path.join(SKILL_DIR, "SKILL.md"), "utf8");
	const refsDir = path.join(SKILL_DIR, "references");
	const refFiles = fs.readdirSync(refsDir).filter((f) => f.endsWith(".md")).sort();
	const refs = refFiles.map((f) => `\n\n--- references/${f} ---\n\n` + fs.readFileSync(path.join(refsDir, f), "utf8"));
	return `--- SKILL.md ---\n\n${skillMd}${refs.join("")}`;
}

const RESPONSE_FORMAT_INSTRUCTION =
	"작업을 마치면, 수정된 파일 전체 내용을 마크다운 코드 블록(예: ```html ... ```) " +
	"하나에 담아 응답 마지막에 포함하라. 코드 블록 안에는 파일 전체(부분 diff가 아니라 " +
	"처음부터 끝까지)를 넣는다. 설명은 코드 블록 앞에 자유롭게 써도 된다.";

function buildSystemInstruction({ withSkill, fileContent }) {
	const parts = [];
	if (withSkill) {
		parts.push(readSkillContent());
	}
	parts.push(
		"다음은 사용자가 작업 중인 프로젝트의 파일(index.html) 전체 내용이다:\n\n```html\n" +
			fileContent +
			"\n```",
	);
	parts.push(RESPONSE_FORMAT_INSTRUCTION);
	return parts.join("\n\n---\n\n");
}

// ---- Gemini Interactions API 호출 (타임아웃 1회분) ----
async function callGeminiOnce({ systemInstruction, userInput }) {
	if (!API_KEY) {
		throw new Error("GEMINI_API_KEY가 설정되지 않았다 — 프로젝트 루트 .env 또는 환경변수를 확인할 것.");
	}
	const body = {
		model: MODEL,
		system_instruction: systemInstruction,
		input: userInput,
	};
	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
	let res;
	try {
		res = await fetch(API_ENDPOINT, {
			method: "POST",
			headers: {
				"x-goog-api-key": API_KEY,
				"Content-Type": "application/json",
			},
			body: JSON.stringify(body),
			signal: controller.signal,
		});
	} catch (e) {
		// AbortError는 타임아웃이 원인일 때만 발생한다(우리가 controller를
		// abort()하는 유일한 경우) — DNS 실패/연결 거부 등 다른 네트워크
		// 에러와 확실히 구분되는 메시지를 남긴다.
		if (e.name === "AbortError") {
			throw new Error(`TIMEOUT — ${FETCH_TIMEOUT_MS}ms 안에 응답을 못 받음`);
		}
		throw new Error(`NETWORK_ERROR — ${e.message}`);
	} finally {
		clearTimeout(timeoutId);
	}
	const text = await res.text();
	let json;
	try {
		json = JSON.parse(text);
	} catch (e) {
		throw new Error(`응답이 JSON이 아님 (HTTP ${res.status}): ${text.slice(0, 500)}`);
	}
	if (!res.ok) {
		throw new Error(`Gemini API 오류 (HTTP ${res.status}): ${JSON.stringify(json).slice(0, 800)}`);
	}
	return { body, response: json };
}

// ---- 재시도 래퍼: 최대 MAX_RETRIES회 재시도, 매 시도의 시작/종료
// 시각을 명시적으로 로그에 남긴다. 한 시나리오가 전부 실패해도
// 예외를 위로 던지기만 하고, 어디서 멈추는지는 runOne()이 처리한다
// (한 건 실패로 전체 순회가 죽지 않는다).
async function callGemini({ systemInstruction, userInput, logLine }) {
	let lastError;
	for (let attempt = 1; attempt <= MAX_RETRIES + 1; attempt++) {
		const startedAt = new Date().toISOString();
		logLine(`  시도 ${attempt}/${MAX_RETRIES + 1} 시작 — ${startedAt}`);
		try {
			const result = await callGeminiOnce({ systemInstruction, userInput });
			logLine(`  시도 ${attempt} 성공 — ${new Date().toISOString()}`);
			return result;
		} catch (e) {
			lastError = e;
			logLine(`  시도 ${attempt} 실패 — ${new Date().toISOString()} — ${e.message}`);
			if (attempt <= MAX_RETRIES) {
				logLine(`  ${RETRY_DELAY_MS / 1000}초 후 재시도`);
				await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
			}
		}
	}
	throw lastError;
}

// 응답 steps에서 마지막 model_output의 텍스트를 전부 이어붙인다
function extractResponseText(apiResponse) {
	const steps = apiResponse.steps || [];
	const modelOutputs = steps.filter((s) => s.type === "model_output");
	if (modelOutputs.length === 0) return null;
	const last = modelOutputs[modelOutputs.length - 1];
	const textParts = (last.content || []).filter((c) => c.type === "text").map((c) => c.text);
	if (textParts.length === 0) return null;
	return textParts.join("\n");
}

// ---- 코드 블록 추출 ----
// 응답 텍스트에서 펜스 코드 블록을 전부 찾고, "완전한 HTML 문서로
// 보이는"(<!doctype 또는 <html로 시작) 블록 중 마지막 것을 고른다.
// 그런 블록이 없으면 가장 긴 코드 블록을 대안으로 쓰되, 그마저 없으면
// null을 반환한다 — 실패를 조용히 삼키지 않는다.
function extractCodeBlock(responseText) {
	if (!responseText) return { code: null, reason: "응답 텍스트 자체가 없음(model_output 파싱 실패)" };
	const fenceRe = /```[a-zA-Z]*\n([\s\S]*?)```/g;
	const blocks = [];
	let m;
	while ((m = fenceRe.exec(responseText)) !== null) {
		blocks.push(m[1]);
	}
	if (blocks.length === 0) {
		return { code: null, reason: "응답에서 마크다운 코드 블록(``` ... ```)을 하나도 못 찾음" };
	}
	const htmlLike = blocks.filter((b) => /^\s*<!doctype html/i.test(b) || /^\s*<html/i.test(b));
	if (htmlLike.length > 0) {
		return { code: htmlLike[htmlLike.length - 1], reason: null };
	}
	// 완전한 HTML 문서로 안 보여도, 가장 긴 블록을 최선의 추정치로 쓰되 경고를 남긴다
	const longest = blocks.reduce((a, b) => (b.length > a.length ? b : a));
	return { code: longest, reason: "코드 블록은 찾았지만 <!doctype html>/<html>로 시작하지 않음 — 완전한 문서가 아닐 수 있음(경고만, 저장은 함)" };
}

// ---- 실행 단위: 시나리오 하나 × 조건 하나(noskill|skill) ----
async function runOne({ scenario, condition, runDir }) {
	const projectDir = path.join(SUBJECTS_DIR, scenario, "project");
	const requestPath = path.join(SUBJECTS_DIR, scenario, "request.txt");
	const indexPath = path.join(projectDir, "index.html");

	const requestText = fs.readFileSync(requestPath, "utf8").trim();
	const fileContent = fs.readFileSync(indexPath, "utf8");

	const systemInstruction = buildSystemInstruction({ withSkill: condition === "skill", fileContent });

	const outDir = path.join(runDir, scenario, condition);
	fs.mkdirSync(outDir, { recursive: true });

	const log = [];
	const logLine = (s) => { log.push(s); console.log(`[${scenario}/${condition}] ${s}`); };

	// ---- 이중 게이트의 2단계: 실제 호출 직전, 매번 확인 ----
	// 1단계(require.main 가드)는 스크립트가 CLI로 직접 실행될 때만
	// main()이 도는 걸 막는다. 이 게이트는 그것과 별개로, runOne()이
	// (예: 다른 코드에서 직접 import해서, 혹은 코드 리뷰 중 실수로)
	// 어떤 경로로 호출되든 실제 네트워크 호출 자체를 막는다 — 오늘
	// require()만으로 main()이 돌아버린 사고가 정확히 이 두 번째 방어선이
	// 없어서 났다.
	const estimatedCostUsd = estimateCostUsd(systemInstruction.length, requestText.length);
	logLine(
		`다음 호출을 실행합니다: ${scenario}, ${condition} · model=${MODEL} · ` +
			`systemInstruction ${systemInstruction.length}자, input(request.txt) ${requestText.length}자 · ` +
			`예상 비용 추정 ≈ $${estimatedCostUsd.toFixed(4)} USD(대략치, 출력 ${ASSUMED_OUTPUT_TOKENS_APPROX}토큰 가정 — 실제 청구액과 다를 수 있음)`,
	);
	if (process.env.CONFIRM_GEMINI_CALLS !== "yes") {
		logLine(`차단됨 — 환경변수 CONFIRM_GEMINI_CALLS=yes 가 설정되지 않아 실제 API 호출을 하지 않고 건너뜀.`);
		fs.writeFileSync(path.join(outDir, "blocked.log"), log.join("\n") + "\n");
		return { scenario, condition, ok: false, reason: "blocked_missing_confirmation" };
	}

	logLine(`API 호출 시작 (model=${MODEL}, systemInstruction ${systemInstruction.length}자, input(request.txt) ${requestText.length}자)`);

	let apiResult;
	try {
		apiResult = await callGemini({ systemInstruction, userInput: requestText, logLine });
	} catch (e) {
		logLine(`실패 — ${MAX_RETRIES + 1}회 시도 전부 실패, 이 시나리오/조건은 건너뜀: ${e.message}`);
		fs.writeFileSync(path.join(outDir, "error.log"), log.join("\n") + "\n");
		return { scenario, condition, ok: false, reason: "api_call_failed" };
	}

	// 실제로 보낸 요청(감사용) — API 키는 포함하지 않는다
	fs.writeFileSync(path.join(outDir, "request-sent.json"), JSON.stringify(apiResult.body, null, 2));
	fs.writeFileSync(path.join(outDir, "response-raw.json"), JSON.stringify(apiResult.response, null, 2));

	const responseText = extractResponseText(apiResult.response);
	const { code, reason } = extractCodeBlock(responseText);

	if (!code) {
		logLine(`실패 — 코드 추출 실패: ${reason}`);
		fs.writeFileSync(path.join(outDir, "error.log"), log.join("\n") + "\n");
		if (responseText) fs.writeFileSync(path.join(outDir, "response-text.txt"), responseText);
		return { scenario, condition, ok: false, reason: "code_extraction_failed" };
	}

	if (reason) logLine(`경고 — ${reason}`);

	fs.mkdirSync(path.join(outDir, "project"), { recursive: true });
	fs.writeFileSync(path.join(outDir, "project", "index.html"), code);
	if (responseText) fs.writeFileSync(path.join(outDir, "response-text.txt"), responseText);

	logLine(`성공 — 코드 ${code.length}자를 project/index.html로 저장함`);
	fs.writeFileSync(path.join(outDir, "run.log"), log.join("\n") + "\n");

	return { scenario, condition, ok: true, codeLength: code.length, warning: reason || null };
}

// ---- CLI ----
async function main() {
	const args = process.argv.slice(2);
	const scenarioArg = args.find((a) => a.startsWith("--scenario="))?.split("=")[1];
	const conditionArg = args.find((a) => a.startsWith("--condition="))?.split("=")[1] || "both";

	const allScenarios = listScenarios();
	// --scenario=04 (접두어 매칭 1개) 또는 --scenario=04,05,06 (쉼표로
	// 여러 개, 각각 접두어 매칭) 둘 다 지원한다.
	const scenarios = scenarioArg
		? scenarioArg
				.split(",")
				.map((s) => s.trim())
				.flatMap((s) => allScenarios.filter((full) => full === s || full.startsWith(s)))
		: allScenarios;
	if (scenarios.length === 0) {
		console.error(`시나리오를 못 찾음: --scenario=${scenarioArg}. 사용 가능: ${allScenarios.join(", ")}`);
		process.exit(1);
	}
	const conditions = conditionArg === "both" ? ["noskill", "skill"] : [conditionArg];

	const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
	const runDir = path.join(RUNS_DIR, timestamp);
	fs.mkdirSync(runDir, { recursive: true });

	console.log(`실행 대상: ${scenarios.length}개 시나리오 × ${conditions.length}개 조건 = ${scenarios.length * conditions.length}회 호출`);
	console.log(`결과 저장 위치: ${path.relative(ROOT, runDir)}/`);

	const results = [];
	let isFirstCall = true;
	for (const scenario of scenarios) {
		for (const condition of conditions) {
			if (!isFirstCall) {
				console.log(`  (무료 티어 rate limit 여유를 위해 ${SLEEP_BETWEEN_CALLS_MS / 1000}초 대기)`);
				// eslint-disable-next-line no-await-in-loop
				await new Promise((r) => setTimeout(r, SLEEP_BETWEEN_CALLS_MS));
			}
			isFirstCall = false;
			// 순차 실행 — 시나리오 간 동시성 없음, 각 호출은 독립된 단일 요청
			// eslint-disable-next-line no-await-in-loop
			const r = await runOne({ scenario, condition, runDir });
			results.push(r);
		}
	}

	console.log("\n=== 요약 ===");
	for (const r of results) {
		const status = r.ok ? `성공(${r.codeLength}자)${r.warning ? " [경고]" : ""}` : `실패(${r.reason})`;
		console.log(`  ${r.scenario}/${r.condition}: ${status}`);
	}
	fs.writeFileSync(path.join(runDir, "summary.json"), JSON.stringify(results, null, 2));
}

// ---- 이중 게이트의 1단계 ----
// 이 파일이 CLI로 직접 실행될 때만(`node run-gemini.js ...`) main()이
// 돈다. `require("./run-gemini.js")`로 다른 스크립트/REPL에서 그냥
// 불러오기만 해도 main()이 실행되던 게 오늘 사고(스캐폴딩 확인하려고
// require했다가 18회 호출이 나가버림)의 직접 원인이었다 — 이 가드가
// 그걸 막는다. 2단계 게이트(CONFIRM_GEMINI_CALLS)는 runOne() 안에,
// 이 파일이 어떻게 호출되든(예: 다른 스크립트가 runOne을 직접 부르는
// 경우까지) 실제 네트워크 호출 자체를 막는 형태로 따로 들어있다.
if (require.main === module) {
	main().catch((e) => {
		console.error("스크립트 실행 중 예외:", e);
		process.exit(1);
	});
} else {
	module.exports = { listScenarios, buildSystemInstruction, extractCodeBlock, extractResponseText, runOne, estimateCostUsd };
}
