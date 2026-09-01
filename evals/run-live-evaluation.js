#!/usr/bin/env node
// evals/run-live-evaluation.js
// 
// 사용자의 요구에 따른 2가지 시나리오 블라인드 A/B 테스트 (Without Skill vs With Skill)
// 1. 기능 신규 생성 시나리오: 캔버스 박스 드래그 (간섭 차단 및 즉각 반응)
// 2. 기존 코드 개선 시나리오: 바텀시트 스크롤 vs 드래그 충돌 수정

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const ROOT = path.resolve(__dirname, "..");
const SKILL_DIR = path.join(ROOT, "skills", "interaction-doctor");
const OUT_DIR = path.join(__dirname, "runs", "live-eval-" + new Date().toISOString().replace(/[:.]/g, "-"));

// .env 로드
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
    let val = line.slice(eq + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    if (!(key in process.env)) process.env[key] = val;
  }
}
loadDotEnv();

const API_KEY = process.env.GEMINI_API_KEY;
const MODEL = process.env.GEMINI_MODEL || "gemini-3.6-flash";
const API_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/interactions";

function readSkillContent() {
  const skillMd = fs.readFileSync(path.join(SKILL_DIR, "SKILL.md"), "utf8");
  const refsDir = path.join(SKILL_DIR, "references");
  const refFiles = fs.readdirSync(refsDir).filter((f) => f.endsWith(".md")).sort();
  const refs = refFiles.map((f) => `\n\n--- references/${f} ---\n\n` + fs.readFileSync(path.join(refsDir, f), "utf8"));
  return `--- SKILL.md ---\n\n${skillMd}${refs.join("")}`;
}

const RESPONSE_FORMAT_INSTRUCTION =
  "작업을 마치면, 완성/수정된 HTML 파일 전체 내용을 반드시 마크다운 코드 블록(```html ... ```) 하나에 담아 응답 마지막에 포함하라. 코드 블록 안에는 파일 전체(<!DOCTYPE html>부터 </html>까지)를 넣는다.";

async function callGeminiBlind({ systemInstruction, userPrompt }) {
  const body = {
    model: MODEL,
    system_instruction: systemInstruction,
    input: userPrompt
  };

  const res = await fetch(API_ENDPOINT, {
    method: "POST",
    headers: {
      "x-goog-api-key": API_KEY,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(body)
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`Gemini Interactions API Error (HTTP ${res.status}): ${errText}`);
  }

  const data = await res.json();
  const steps = data.steps || [];
  const modelOutputs = steps.filter((s) => s.type === "model_output");
  let rawText = "";
  if (modelOutputs.length > 0) {
    const last = modelOutputs[modelOutputs.length - 1];
    const textParts = (last.content || []).filter((c) => c.type === "text").map((c) => c.text);
    rawText = textParts.join("\n");
  }

  // HTML 코드 블록 추출
  const fenceRe = /```(?:html)?\n([\s\S]*?)```/gi;
  let match;
  let lastCode = null;
  while ((match = fenceRe.exec(rawText)) !== null) {
    lastCode = match[1];
  }
  const code = lastCode || rawText;

  return { rawText, code };
}

// -------------------------------------------------------------
// 시나리오 정의 (순수 사용자 프롬프트 - 테스트 인지 불가)
// -------------------------------------------------------------
const scenarios = [
  {
    id: "scenario-A-create",
    title: "신규 기능 생성 (캔버스 개체 드래그 & 간섭 방지)",
    userPrompt:
      "모바일 웹에서 동작하는 간단한 캔버스 박스 드래그 페이지를 만들어줘. 화면 중앙에 드래그 가능한 박스(id='dragBox')가 있고, 손가락으로 터치해서 움직이면 즉시 부드럽게 따라 움직여야 해. 모바일 브라우저의 기본 스크롤이나 텍스트 선택, 롱프레스 팝업 메뉴 때문에 드래그가 씹히거나 방해받지 않고 온전히 박스만 끌려야 해. 단일 index.html 파일로 작성해줘.",
    baseHtml: null
  },
  {
    id: "scenario-B-refactor",
    title: "기존 코드 개선 (바텀시트 내부 스크롤 vs 시트 드래그 충돌 수정)",
    userPrompt:
      "내가 만든 바텀시트 코드인데, 모바일에서 리스트를 아래로 스크롤하려고 손가락을 내리면 리스트가 스크롤되는 게 아니라 바텀시트 전체가 닫혀버려. 리스트가 맨 위(scrollTop이 0)에 도달해 있을 때 아래로 당기면 시트가 닫히고, 리스트 중간을 스크롤 중일 때는 리스트 스크롤이 정상 동작하도록 코드를 고쳐줘.",
    baseHtml: fs.readFileSync(path.join(ROOT, "demo", "broken-bottomsheet-drag.html"), "utf8")
  }
];

// -------------------------------------------------------------
// Playwright 자동 채점기 (3축 상호작용 및 간섭 평가)
// -------------------------------------------------------------
async function gradeScenarioA(htmlCode) {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setContent(htmlCode);

  const grade = await page.evaluate(async () => {
    const box = document.getElementById("dragBox") || document.querySelector(".box") || document.querySelector("div");
    if (!box) return { ok: false, error: "박스 요소를 찾을 수 없음" };

    const style = window.getComputedStyle(box);
    const bodyStyle = window.getComputedStyle(document.body);

    // 1. 간섭 방지 (Interference Checklist)
    const hasTouchActionGuard = style.touchAction === "none" || style.touchAction === "pan-y" || bodyStyle.touchAction === "none";
    const hasUserSelectGuard = style.userSelect === "none" || style.webkitUserSelect === "none" || bodyStyle.userSelect === "none";

    // 2. 터치 드래그 테스트
    const rect = box.getBoundingClientRect();
    const startX = rect.left + rect.width / 2;
    const startY = rect.top + rect.height / 2;

    const mk = (type, x, y) =>
      new PointerEvent(type, {
        pointerId: 1,
        clientX: x,
        clientY: y,
        bubbles: true,
        cancelable: true,
        pointerType: "touch"
      });

    box.dispatchEvent(mk("pointerdown", startX, startY));
    await new Promise((r) => setTimeout(r, 30));
    box.dispatchEvent(mk("pointermove", startX + 50, startY + 50));
    await new Promise((r) => setTimeout(r, 30));

    const movedRect = box.getBoundingClientRect();
    const isDirectlyTracking = (movedRect.left !== rect.left) || (box.style.transform && box.style.transform.includes("px")) || (box.style.left && box.style.left !== "");

    box.dispatchEvent(mk("pointerup", startX + 50, startY + 50));

    return {
      ok: true,
      hasTouchActionInterferenceGuard: hasTouchActionGuard,  // 브라우저 스크롤 간섭 방지 (touch-action)
      hasUserSelectInterferenceGuard: hasUserSelectGuard,    // 텍스트 선택 간섭 방지 (user-select)
      isDirectlyTracking                                     // 즉각적인 1:1 위치 추종
    };
  });

  await browser.close();
  return grade;
}

async function gradeScenarioB(htmlCode) {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setContent(htmlCode);

  const grade = await page.evaluate(async () => {
    const scrollContent = document.getElementById("scrollContent") || document.querySelector(".scroll-content");
    const sheet = document.getElementById("sheet") || document.querySelector(".sheet");
    if (!scrollContent || !sheet) return { ok: false, error: "바텀시트/스크롤 요소를 찾을 수 없음" };

    const mk = (type, y) =>
      new PointerEvent(type, {
        pointerId: 1,
        clientX: 150,
        clientY: y,
        bubbles: true,
        cancelable: true,
        pointerType: "touch"
      });

    // Test 1: 스크롤 중간(scrollTop = 150)에서 아래로 80px 드래그 시 시트가 끌려내려오지 않아야 함
    scrollContent.scrollTop = 150;
    scrollContent.dispatchEvent(mk("pointerdown", 200));
    await new Promise((r) => setTimeout(r, 20));
    scrollContent.dispatchEvent(mk("pointermove", 280));
    await new Promise((r) => setTimeout(r, 20));
    const transformMiddle = sheet.style.transform || "";
    const sheetDraggedDuringScroll = transformMiddle.includes("80px") || (transformMiddle.includes("translateY(") && !transformMiddle.includes("translateY(0"));
    scrollContent.dispatchEvent(mk("pointerup", 280));

    // Test 2: 맨 위(scrollTop = 0)에서 아래로 80px 드래그 시 시트가 닫힘 제스처로 동작해야 함
    scrollContent.scrollTop = 0;
    scrollContent.dispatchEvent(mk("pointerdown", 200));
    await new Promise((r) => setTimeout(r, 20));
    scrollContent.dispatchEvent(mk("pointermove", 280));
    await new Promise((r) => setTimeout(r, 20));
    const transformTop = sheet.style.transform || "";
    const sheetMovedAtTop = transformTop.includes("translateY") && !transformTop.includes("translateY(0px)") && !transformTop.includes("translateY(0)");
    scrollContent.dispatchEvent(mk("pointerup", 280));

    return {
      ok: true,
      innerScrollProtected: !sheetDraggedDuringScroll, // 스크롤 중간 시트 간섭 차단 여부
      sheetCollapseAtTopAllowed: sheetMovedAtTop       // 맨 위에서 시트 닫기 허용 여부
    };
  });

  await browser.close();
  return grade;
}

// -------------------------------------------------------------
// 메인 실행 루프
// -------------------------------------------------------------
async function run() {
  console.log("==================================================================");
  console.log("  Live Blind A/B Evaluation (Without Skill vs With Skill)");
  console.log(`  Model: ${MODEL} | Target: 2 Scenarios × 2 Conditions = 4 Runs`);
  console.log("==================================================================\n");

  fs.mkdirSync(OUT_DIR, { recursive: true });
  const finalResults = [];

  for (const sc of scenarios) {
    console.log(`\n▶ [${sc.id}] ${sc.title}`);
    const scDir = path.join(OUT_DIR, sc.id);
    fs.mkdirSync(scDir, { recursive: true });

    for (const condition of ["without_skill", "with_skill"]) {
      console.log(`  - Running condition: ${condition}...`);
      const condDir = path.join(scDir, condition);
      fs.mkdirSync(condDir, { recursive: true });

      let systemInstruction = "";
      if (condition === "with_skill") {
        systemInstruction = readSkillContent() + "\n\n---\n\n" + RESPONSE_FORMAT_INSTRUCTION;
      } else {
        systemInstruction = "You are a professional frontend web developer.\n" + RESPONSE_FORMAT_INSTRUCTION;
      }

      let userPrompt = sc.userPrompt;
      if (sc.baseHtml) {
        userPrompt += "\n\n다음은 현재 기존 코드이다:\n```html\n" + sc.baseHtml + "\n```";
      }

      try {
        const { rawText, code } = await callGeminiBlind({ systemInstruction, userPrompt });
        fs.writeFileSync(path.join(condDir, "response.txt"), rawText);
        fs.writeFileSync(path.join(condDir, "index.html"), code);

        // 채점
        let gradeResult = null;
        if (sc.id === "scenario-A-create") {
          gradeResult = await gradeScenarioA(code);
        } else if (sc.id === "scenario-B-refactor") {
          gradeResult = await gradeScenarioB(code);
        }

        console.log(`    결과:`, gradeResult);
        fs.writeFileSync(path.join(condDir, "grade.json"), JSON.stringify(gradeResult, null, 2));

        finalResults.push({
          scenario: sc.id,
          condition,
          grade: gradeResult
        });
      } catch (err) {
        console.error(`    에러: ${err.message}`);
        finalResults.push({
          scenario: sc.id,
          condition,
          error: err.message
        });
      }

      // Rate limit 여유 대기 (8초)
      await new Promise((r) => setTimeout(r, 8000));
    }
  }

  fs.writeFileSync(path.join(OUT_DIR, "summary.json"), JSON.stringify(finalResults, null, 2));
  console.log(`\n✅ 평가 완료! 결과 저장 위치: ${OUT_DIR}`);
}

run().catch((e) => {
  console.error("실행 실패:", e);
  process.exit(1);
});
