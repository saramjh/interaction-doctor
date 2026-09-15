// 공용 유틸. 시나리오별 채점 스크립트가 공유한다.
// project/ 폴더 밖에 둔다 — 채점 로직이 결함 심어진 프로젝트와 섞이지 않게.

const { chromium } = require("playwright");
const path = require("path");

function targetUrl(condition, scenarioDir) {
	// condition: 'subjects' (원본 결함 버전) | 'baseline' | 'treatment'
	//          | 'runs:<timestamp>:<noskill|skill>' (run-gemini.js 산출물,
	//            evals/runs/<timestamp>/<scenario>/<noskill|skill>/project/index.html)
	if (condition.startsWith("runs:")) {
		const [, timestamp, subCondition] = condition.split(":");
		if (!timestamp || !subCondition) {
			throw new Error(`잘못된 condition 형식: "${condition}" — "runs:<timestamp>:<noskill|skill>"이어야 함`);
		}
		const abs = path.resolve(__dirname, "..", "runs", timestamp, scenarioDir, subCondition, "project", "index.html");
		return "file://" + abs;
	}
	const base = condition === "subjects" ? "subjects" : `results/${condition}/subjects`;
	const abs = path.resolve(__dirname, "..", base, scenarioDir, "project", "index.html");
	return "file://" + abs;
}

async function withPage(fn, opts = {}) {
	const browser = await chromium.launch();
	const page = await browser.newPage();
	const pageErrors = [];
	page.on("pageerror", (e) => pageErrors.push(String(e && e.message ? e.message : e)));
	if (opts.stubPointerCapture) {
		// 진단용(디폴트 아님): Playwright의 합성 PointerEvent에는 실제 OS
		// 포인터 세션이 없어서 setPointerCapture/releasePointerCapture가
		// "No active pointer" 예외를 던진다(common-pitfalls.md §6 함정2).
		// 원본 결과(스텁 없음)가 항상 1차 채점 기준이고, 이건 "그 예외만
		// 없었다면 나머지 로직은 맞는가"를 별도로 확인하려는 것뿐이다.
		await page.addInitScript(() => {
			Element.prototype.setPointerCapture = function () {};
			Element.prototype.releasePointerCapture = function () {};
		});
	}
	try {
		const result = await fn(page);
		return { result, pageErrors };
	} finally {
		await browser.close();
	}
}

// 서브테스트(a/b/c/d)마다 완전히 새로 goto해서 이전 서브테스트의 DOM
// 변형(재정렬 등)이 다음 서브테스트의 "이전 상태" 가정을 오염시키지
// 않게 한다 — 브라우저 인스턴스 하나를 재사용해 속도만 아낀다.
async function withFreshPages(url, subtests, opts = {}) {
	const browser = await chromium.launch();
	const allPageErrors = [];
	const results = {};
	try {
		for (const [name, fn] of Object.entries(subtests)) {
			const page = await browser.newPage();
			const pageErrors = [];
			page.on("pageerror", (e) => pageErrors.push(String(e && e.message ? e.message : e)));
			if (opts.stubPointerCapture) {
				await page.addInitScript(() => {
					Element.prototype.setPointerCapture = function () {};
					Element.prototype.releasePointerCapture = function () {};
				});
			}
			await page.goto(url);
			results[name] = await fn(page);
			allPageErrors.push(...pageErrors.map((m) => `[${name}] ${m}`));
			await page.close();
		}
		return { results, pageErrors: allPageErrors };
	} finally {
		await browser.close();
	}
}

// dispatch a synthetic PointerEvent inside the page — 실제 도구 왕복 지연이
// 타이밍에 섞이지 않도록, 각 시나리오 스크립트는 시퀀스 전체를 하나의
// page.evaluate 안에서(내부 setTimeout으로) 실행한다. 이 헬퍼는 그 안에서
// 쓰는 이벤트 생성자 코드 조각을 문자열로 재사용하기 위한 것이 아니라,
// evaluate에 넘길 함수 안에서 직접 new PointerEvent(...)를 쓰면 된다는
// 걸 문서화해두는 자리다.

function runScenario(condition, scenarioDir, gradeFn, opts = {}) {
	return (async () => {
		const url = targetUrl(condition, scenarioDir);
		const { result, pageErrors } = await withPage(async (page) => {
			await page.goto(url);
			return await gradeFn(page);
		}, opts);
		const output = { scenario: scenarioDir, condition, stubPointerCapture: !!opts.stubPointerCapture, pageErrors, ...result };
		console.log(JSON.stringify(output, null, 2));
		return output;
	})();
}

function runScenarioFresh(condition, scenarioDir, subtests, opts = {}) {
	return (async () => {
		const url = targetUrl(condition, scenarioDir);
		const { results, pageErrors } = await withFreshPages(url, subtests, opts);
		const output = { scenario: scenarioDir, condition, stubPointerCapture: !!opts.stubPointerCapture, pageErrors, ...results };
		console.log(JSON.stringify(output, null, 2));
		return output;
	})();
}

module.exports = { targetUrl, withPage, withFreshPages, runScenario, runScenarioFresh };
