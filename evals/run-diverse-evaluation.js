#!/usr/bin/env node
// evals/run-diverse-evaluation.js
// 
// 10개 일반 시나리오 (신규 5개 + 개선 5개) A/B 테스트 (429/500 재시도 복구 포함)

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const SKILL_DIR = path.join(ROOT, "skills", "interaction-doctor");
// 기존 run 폴더가 있으면 재사용하여 누락분만 채움
const RUNS_ROOT = path.join(__dirname, "runs");
let targetRunDir = path.join(RUNS_ROOT, "diverse-eval-master");

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

// 재시도 래퍼
async function callGeminiBlind({ systemInstruction, userPrompt, maxRetries = 4 }) {
  const body = {
    model: MODEL,
    system_instruction: systemInstruction,
    input: userPrompt
  };

  let lastError;
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
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
        // 429 또는 500/503 이면 대기 후 재시도
        if (res.status === 429 || res.status >= 500) {
          const waitSec = attempt * 18; // 18s, 36s, 54s 점진 증가
          console.log(`    ⚠️ HTTP ${res.status} 발생 (시도 ${attempt}/${maxRetries}) -> ${waitSec}초 대기 후 재시도...`);
          await new Promise((r) => setTimeout(r, waitSec * 1000));
          continue;
        }
        throw new Error(`Gemini API Error (HTTP ${res.status}): ${errText}`);
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

      const fenceRe = /```(?:html)?\n([\s\S]*?)```/gi;
      let match;
      let lastCode = null;
      while ((match = fenceRe.exec(rawText)) !== null) {
        lastCode = match[1];
      }
      const code = lastCode || rawText;
      return { rawText, code };
    } catch (e) {
      lastError = e;
      if (attempt < maxRetries) {
        const waitSec = attempt * 15;
        console.log(`    ⚠️ 네트워크/API 예외 (시도 ${attempt}/${maxRetries}): ${e.message} -> ${waitSec}초 대기 후 재시도...`);
        await new Promise((r) => setTimeout(r, waitSec * 1000));
      }
    }
  }
  throw lastError;
}

const scenarios = [
  {
    id: "create-1-tabs",
    category: "신규 생성",
    title: "모바일 스와이프 탭 뷰",
    userPrompt: "모바일 웹에서 상단 탭 버튼(홈, 탐색, 설정)을 누르거나 화면을 좌우로 스와이프해서 탭을 부드럽게 전환하는 스와이프 탭 페이지를 만들어줘. 내부 세로 스크롤과 좌우 스와이프가 서로 간섭하지 않게 해줘. 단일 index.html로 작성해줘."
  },
  {
    id: "create-2-rangeslider",
    category: "신규 생성",
    title: "듀얼 썸 가격 범위 슬라이더",
    userPrompt: "모바일 터치로 최소값과 최대값을 조절할 수 있는 듀얼 썸(양쪽 핸들) 범위 슬라이더 컴포넌트를 만들어줘. 두 핸들을 터치해서 좌우로 끌 때 화면 스크롤이나 확대가 방해하지 않고 손가락을 1:1로 부드럽게 따라와야 해. 단일 index.html로 작성해줘."
  },
  {
    id: "create-3-imagezoom",
    category: "신규 생성",
    title: "두 손가락 핀치 줌 이미지 뷰어",
    userPrompt: "사진을 터치해서 두 손가락으로 핀치 확대/축소하고 드래그로 팬(이동)할 수 있는 모바일 이미지 뷰어를 만들어줘. 모바일 브라우저의 기본 페이지 줌과 충돌하지 않고 사진 안에서만 부드럽게 줌/팬이 동작해야 해. 단일 index.html로 작성해줘."
  },
  {
    id: "create-4-pullrefresh",
    category: "신규 생성",
    title: "당겨서 새로고침 (Pull-to-Refresh)",
    userPrompt: "모바일 리스트 화면에서 맨 위에서 아래로 당겼을 때 로딩 인디케이터가 부드럽게 내려오고 손을 놓으면 새로고침되는 Pull-to-Refresh 컴포넌트를 만들어줘. 리스트 중간을 스크롤할 때는 절대 인디케이터가 트리거되지 않아야 해. 단일 index.html로 작성해줘."
  },
  {
    id: "create-5-sortablegrid",
    category: "신규 생성",
    title: "갤러리 사진 그리드 터치 재배치",
    userPrompt: "사진 갤러리 2열 격자(Grid) 화면에서 사진 카드를 길게 누르면 카드가 살짝 떠오르고, 다른 위치로 드래그해서 순서를 바꿀 수 있는 모바일 그리드 재배치 페이지를 만들어줘. 평소 세로 스크롤과 충돌하지 않아야 해. 단일 index.html로 작성해줘."
  },
  {
    id: "refactor-1-drawer",
    category: "코드 개선",
    title: "사이드 드로어 메뉴 제스처 충돌 수정",
    userPrompt: `내가 만든 사이드 네비게이션 드로어 메뉴인데, 모바일에서 메뉴를 열고 스크롤하려고 하면 뒤의 본문 페이지까지 같이 스크롤되고, 드로어를 스와이프로 닫으려고 할 때 iOS 뒤로가기 제스처와 겹쳐서 동작이 꼬여. 배경 스크롤 락과 부드러운 스와이프 닫기가 동작하게 고쳐줘.

다음은 현재 코드이다:
\`\`\`html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { margin:0; font-family:sans-serif; height:200vh; padding:20px; background:#f0f0f0; }
.drawer { position:fixed; top:0; left:-280px; width:280px; height:100%; background:#fff; z-index:100; transition:left 0.3s; padding:20px; box-shadow:2px 0 10px rgba(0,0,0,0.1); }
.drawer.open { left:0; }
.overlay { position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); display:none; z-index:90; }
.overlay.open { display:block; }
</style>
</head>
<body>
<button id="btnOpen">메뉴 열기</button>
<div class="overlay" id="overlay"></div>
<div class="drawer" id="drawer">
  <h2>메뉴</h2>
  <p>메뉴 항목 1</p><p>메뉴 항목 2</p><p>메뉴 항목 3</p>
</div>
<script>
const btn = document.getElementById('btnOpen');
const drawer = document.getElementById('drawer');
const overlay = document.getElementById('overlay');
btn.onclick = () => { drawer.classList.add('open'); overlay.classList.add('open'); };
overlay.onclick = () => { drawer.classList.remove('open'); overlay.classList.remove('open'); };
</script>
</body>
</html>
\`\`\``
  },
  {
    id: "refactor-2-carousel",
    category: "코드 개선",
    title: "무한 캐러셀 터치 스냅 및 간섭 수정",
    userPrompt: `모바일 이미지 캐러셀인데, 손가락으로 드래그할 때 손가락을 떼면 다음 슬라이드에 딱 맞게 스냅되지 않고 중간에 걸치거나, 드래그 중에도 자동 슬라이드가 넘어가서 화면이 튑니다. 터치 중에는 자동 슬라이드가 일시정지되고, 스와이프 시 부드럽게 다음 카드로 스냅되게 고쳐줘.

다음은 현재 코드이다:
\`\`\`html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { margin:0; padding:20px; background:#111; color:#fff; }
.carousel-track { display:flex; gap:10px; overflow-x:auto; width:100%; }
.card { flex:0 0 80%; height:150px; background:#333; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:20px; }
</style>
</head>
<body>
<div class="carousel-track" id="track">
  <div class="card">Slide 1</div>
  <div class="card">Slide 2</div>
  <div class="card">Slide 3</div>
</div>
</body>
</html>
\`\`\``
  },
  {
    id: "refactor-3-segmented",
    category: "코드 개선",
    title: "iOS 스타일 세그먼트 컨트롤 터치 개선",
    userPrompt: `iOS 스타일 세그먼트 컨트롤인데, 탭할 때 300ms 딜레이가 느껴지고 슬라이딩 인디케이터를 손가락으로 끌어서 옮기려고 하면 텍스트 선택이 일어나면서 드래그가 씹혀. 즉각적인 탭 반응과 부드러운 터치 드래그 이동이 모두 지원되도록 고쳐줘.

다음은 현재 코드이다:
\`\`\`html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { padding:40px; background:#f5f5f7; display:flex; justify-content:center; }
.segmented { display:flex; background:#e3e3e8; border-radius:9px; padding:2px; width:300px; position:relative; }
.segment { flex:1; text-align:center; padding:8px 0; font-size:14px; z-index:2; cursor:pointer; }
.indicator { position:absolute; top:2px; left:2px; width:33.33%; height:calc(100% - 4px); background:#fff; border-radius:7px; box-shadow:0 1px 3px rgba(0,0,0,0.15); transition:transform 0.2s; z-index:1; }
</style>
</head>
<body>
<div class="segmented" id="seg">
  <div class="indicator" id="ind"></div>
  <div class="segment" data-idx="0">일간</div>
  <div class="segment" data-idx="1">주간</div>
  <div class="segment" data-idx="2">월간</div>
</div>
</body>
</html>
\`\`\``
  },
  {
    id: "refactor-4-tooltip",
    category: "코드 개선",
    title: "모바일 툴팁/팝오버 바깥 터치 닫기 충돌 수정",
    userPrompt: `아이콘을 누르면 설명 툴팁이 뜨는 컴포넌트인데, 모바일에서 툴팁을 띄운 뒤 화면을 스크롤하거나 다른 곳을 터치하면 툴팁이 닫히지 않고 그대로 남아있거나, 툴팁을 누르려다 뒤의 버튼이 눌리는 문제가 있어. 툴팁 외부 터치 시 안전하게 닫히고 클릭 간섭이 없도록 고쳐줘.

다음은 현재 코드이다:
\`\`\`html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { padding:40px; height:150vh; font-family:sans-serif; }
.btn-help { padding:8px 12px; font-size:16px; position:relative; }
.tooltip { position:absolute; bottom:120%; left:50%; transform:translateX(-50%); background:#333; color:#fff; padding:8px 12px; border-radius:6px; font-size:13px; display:none; width:180px; }
.tooltip.show { display:block; }
</style>
</head>
<body>
<button class="btn-help" id="btnHelp">도움말 ℹ️
  <div class="tooltip" id="tooltip">여기에 상세한 안내 문구가 표시됩니다.</div>
</button>
<script>
const btn = document.getElementById('btnHelp');
const tt = document.getElementById('tooltip');
btn.onclick = () => tt.classList.toggle('show');
</script>
</body>
</html>
\`\`\``
  },
  {
    id: "refactor-5-accordion",
    category: "코드 개선",
    title: "FAQ 아코디언 터치 딜레이 및 텍스트 선택 간섭 수정",
    userPrompt: `FAQ 아코디언 메뉴인데, 모바일에서 연속으로 질문을 터치하면 더블탭으로 인식되어 화면이 줌인되거나 텍스트가 파랗게 선택되어 버려. 더블탭 줌과 텍스트 선택 간섭 없이 빠릿하게 접히고 펼쳐지도록 고쳐줘.

다음은 현재 코드이다:
\`\`\`html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { padding:20px; font-family:sans-serif; background:#fafafa; }
.accordion-item { border-bottom:1px solid #ddd; padding:15px 0; }
.title { font-weight:bold; cursor:pointer; font-size:16px; }
.content { display:none; padding-top:10px; color:#666; }
.content.open { display:block; }
</style>
</head>
<body>
<div class="accordion-item">
  <div class="title">환불 규정은 어떻게 되나요?</div>
  <div class="content">구매 후 7일 이내에 미사용 시 100% 환불 가능합니다.</div>
</div>
<div class="accordion-item">
  <div class="title">배송 기간은 얼마나 걸리나요?</div>
  <div class="content">평일 기준 2~3일 내에 배송됩니다.</div>
</div>
<script>
document.querySelectorAll('.title').forEach(t => {
  t.onclick = () => t.nextElementSibling.classList.toggle('open');
});
</script>
</body>
</html>
\`\`\``
  }
];

async function run() {
  console.log("==================================================================");
  console.log("  Diverse Evaluation: 10 Scenarios (Smart Retry & Recovery)");
  console.log(`  Model: ${MODEL} | Target: ${targetRunDir}`);
  console.log("==================================================================\n");

  fs.mkdirSync(targetRunDir, { recursive: true });
  const results = [];

  for (let i = 0; i < scenarios.length; i++) {
    const sc = scenarios[i];
    console.log(`\n▶ [${i + 1}/${scenarios.length}] [${sc.category}] ${sc.id} — ${sc.title}`);
    const scDir = path.join(targetRunDir, sc.id);
    fs.mkdirSync(scDir, { recursive: true });

    for (const condition of ["without_skill", "with_skill"]) {
      const condDir = path.join(scDir, condition);
      fs.mkdirSync(condDir, { recursive: true });

      const indexFile = path.join(condDir, "index.html");
      if (fs.existsSync(indexFile) && fs.readFileSync(indexFile, "utf8").length > 500) {
        console.log(`  - Condition: ${condition} (이미 성공 완료됨, 건너뜀)`);
        results.push({ scenario: sc.id, condition, ok: true });
        continue;
      }

      console.log(`  - Condition: ${condition} 호출 시작...`);
      let systemInstruction = "";
      if (condition === "with_skill") {
        systemInstruction = readSkillContent() + "\n\n---\n\n" + RESPONSE_FORMAT_INSTRUCTION;
      } else {
        systemInstruction = "You are an expert frontend web developer.\n" + RESPONSE_FORMAT_INSTRUCTION;
      }

      try {
        const { rawText, code } = await callGeminiBlind({ systemInstruction, userPrompt: sc.userPrompt });
        fs.writeFileSync(path.join(condDir, "response.txt"), rawText);
        fs.writeFileSync(path.join(condDir, "index.html"), code);
        console.log(`    ✓ 성공 (${code ? code.length : 0}자 저장)`);
        results.push({ scenario: sc.id, condition, ok: true });
      } catch (err) {
        const errMsg = err && err.message ? err.message : String(err);
        console.error(`    ✗ 최종 실패: ${errMsg}`);
        results.push({ scenario: sc.id, condition, ok: false, error: errMsg });
      }

      // 안전 지연 12초
      await new Promise((r) => setTimeout(r, 12000));
    }
  }

  // 최신 링크 갱신
  const linkDir = path.join(RUNS_ROOT, "latest-diverse-run");
  if (fs.existsSync(linkDir)) fs.rmSync(linkDir, { recursive: true, force: true });
  try {
    fs.symlinkSync(targetRunDir, linkDir, "dir");
  } catch(e) {
    // Windows fallback
  }

  fs.writeFileSync(path.join(targetRunDir, "summary.json"), JSON.stringify(results, null, 2));
  console.log(`\n🎉 완료! 위치: ${targetRunDir}`);
}

run().catch((e) => {
  console.error("실행 실패:", e);
  process.exit(1);
});
