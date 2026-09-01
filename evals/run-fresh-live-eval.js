#!/usr/bin/env node
// evals/run-fresh-live-eval.js
// 
// 완전히 새로운 10개 실무 시나리오(신규 5개 + 개선 5개)
// 완전 무상태(Stateless) 격리 블라인드 실증 A/B 테스트

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const SKILL_DIR = path.join(ROOT, "skills", "interaction-doctor");
const OUT_DIR = path.join(__dirname, "runs", "fresh-live-eval-master");

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

async function callGeminiBlind({ systemInstruction, userPrompt, maxRetries = 5 }) {
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
        if (res.status === 429 || res.status >= 500) {
          const waitSec = attempt * 20;
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

// 10개 완전히 새로운 블라인드 프롬프트
const freshScenarios = [
  // [신규 5종]
  {
    id: "fresh-create-1-rangeslider-vertical",
    category: "신규 생성",
    title: "세로형 볼륨/EQ 슬라이더",
    userPrompt: "모바일 웹에서 손가락으로 볼륨을 조절할 수 있는 세로형 슬라이더 컴포넌트를 만들어줘. 슬라이더 핸들을 위아래로 끌 때 화면 스크롤이 간섭하지 않고 손가락을 1:1로 부드럽게 따라와야 해. 단일 index.html로 작성해줘."
  },
  {
    id: "fresh-create-2-signature-pad",
    category: "신규 생성",
    title: "캔버스 전자 서명 패드",
    userPrompt: "모바일 계약서에 들어갈 전자 서명 캔버스 컴포넌트를 만들어줘. 서명 패드 위에서 손가락이나 터치펜으로 서명할 때 화면 스크롤이나 바운스가 발생하지 않고 부드럽게 선이 그려져야 해. 초기화(지우기) 버튼도 포함해서 단일 index.html로 작성해줘."
  },
  {
    id: "fresh-create-3-colorpicker",
    category: "신규 생성",
    title: "2D 원형 색상 팔레트 피커",
    userPrompt: "원형 컬러 휠 안에서 터치 드래그로 색상(Hue/Saturation)을 선택하는 모바일 2D 컬러 피커를 만들어줘. 원 바깥으로 손가락이 나가도 가장자리에 부드럽게 붙어서 선택이 유지되어야 하고 텍스트 선택이나 롱프레스 팝업이 방해하지 않아야 해. 단일 index.html로 작성해줘."
  },
  {
    id: "fresh-create-4-swipe-actions",
    category: "신규 생성",
    title: "iOS 스타일 리스트 스와이프 삭제",
    userPrompt: "모바일 알림 리스트에서 항목을 왼쪽으로 스와이프하면 삭제 버튼이 나타나고, 끝까지 시원하게 밀면 항목이 바로 삭제되는 스와이프 액션 리스트를 만들어줘. 평소 세로 스크롤할 때는 좌우 스와이프가 실수로 열리지 않아야 해. 단일 index.html로 작성해줘."
  },
  {
    id: "fresh-create-5-virtual-joystick",
    category: "신규 생성",
    title: "모바일 가상 조이스틱 터치패드",
    userPrompt: "모바일 웹 게임에서 캐릭터를 조종할 수 있는 가상 조이스틱을 만들어줘. 화면 터치 드래그로 스틱이 움직이고 손을 떼면 즉시 중앙으로 돌아와야 해. 멀티터치 상태에서도 간섭 없이 안정적으로 동작해야 해. 단일 index.html로 작성해줘."
  },

  // [개선 5종]
  {
    id: "fresh-refactor-1-modal-scroll",
    category: "코드 개선",
    title: "모달 내부 스크롤 시 배경 누수(Scroll Chaining) 수정",
    userPrompt: `모달 팝업인데, 모바일에서 모달 내부 긴 약관을 스크롤하다가 끝에 도달하면 뒤의 본문 화면까지 같이 스크롤되어 버려. 모달이 열려 있을 때는 뒷배경 스크롤이 완벽히 잠기고 모달 안에서만 스크롤되도록 고쳐줘.

다음은 현재 코드이다:
\`\`\`html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { margin:0; padding:20px; font-family:sans-serif; height:200vh; background:#f0f0f0; }
.modal-overlay { position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); display:none; align-items:center; justify-content:center; }
.modal-overlay.open { display:flex; }
.modal-box { width:80%; max-height:250px; background:#fff; border-radius:8px; padding:20px; overflow-y:scroll; }
</style>
</head>
<body>
<button id="btnOpen">모달 열기</button>
<div class="modal-overlay" id="overlay">
  <div class="modal-box" id="box">
    <h3>이용약관</h3>
    <p>약관 내용 1</p><p>약관 내용 2</p><p>약관 내용 3</p><p>약관 내용 4</p><p>약관 내용 5</p><p>약관 내용 6</p>
  </div>
</div>
<script>
const btn = document.getElementById('btnOpen');
const overlay = document.getElementById('overlay');
btn.onclick = () => overlay.classList.add('open');
overlay.onclick = (e) => { if(e.target === overlay) overlay.classList.remove('open'); };
</script>
</body>
</html>
\`\`\``
  },
  {
    id: "fresh-refactor-2-image-slider",
    category: "코드 개선",
    title: "Before/After 이미지 비교 슬라이더 드래그 튐 수정",
    userPrompt: `이미지 비교 슬라이더인데, 모바일에서 가운데 구분선을 잡고 좌우로 드래그할 때 텍스트 선택이 파랗게 되거나 손가락이 슬라이더 바깥으로 나가면 드래그가 끊겨버려. 손가락이 조금 벗어나도 1:1로 부드럽게 따라오도록 고쳐줘.

다음은 현재 코드이다:
\`\`\`html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { margin:0; padding:20px; background:#222; color:#fff; display:flex; flex-direction:column; align-items:center; }
.compare-container { position:relative; width:300px; height:200px; overflow:hidden; }
.img-before { position:absolute; top:0; left:0; width:100%; height:100%; background:#4a90e2; display:flex; align-items:center; justify-content:center; }
.img-after { position:absolute; top:0; left:0; width:50%; height:100%; background:#38ef7d; overflow:hidden; display:flex; align-items:center; justify-content:center; }
.handle { position:absolute; top:0; left:50%; width:4px; height:100%; background:#fff; cursor:ew-resize; }
</style>
</head>
<body>
<div class="compare-container" id="container">
  <div class="img-before">BEFORE</div>
  <div class="img-after" id="after">AFTER</div>
  <div class="handle" id="handle"></div>
</div>
<script>
const container = document.getElementById('container');
const after = document.getElementById('after');
const handle = document.getElementById('handle');
let isDown = false;
handle.ontouchstart = () => isDown = true;
window.ontouchend = () => isDown = false;
window.addEventListener('touchmove', (e) => {
  if (!isDown) return;
  const rect = container.getBoundingClientRect();
  const x = e.touches[0].clientX - rect.left;
  const pct = Math.max(0, Math.min(100, (x / rect.width) * 100));
  handle.style.left = pct + '%';
  after.style.width = pct + '%';
});
</script>
</body>
</html>
\`\`\``
  },
  {
    id: "fresh-refactor-3-tree-view",
    category: "코드 개선",
    title: "파일 탐색기 롱터치 팝업 vs 폴더 열기 충돌 수정",
    userPrompt: `파일 탐색기인데, 모바일에서 폴더를 길게 누르면 컨텍스트 메뉴(삭제/이름바꾸기)가 떠야 하는데, 손을 떼는 순간 클릭 이벤트까지 발생해서 폴더가 열려버리는 충돌이 있어. 롱터치 시에는 폴더가 열리지 않고 메뉴만 뜨도록 고쳐줘.

다음은 현재 코드이다:
\`\`\`html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { font-family:sans-serif; padding:20px; }
.tree-node { padding:12px; border-bottom:1px solid #ddd; cursor:pointer; }
.context-menu { position:fixed; background:#333; color:#fff; padding:10px; border-radius:6px; display:none; }
</style>
</head>
<body>
<div class="tree-node" id="node1">📁 프로젝트 폴더 A</div>
<div class="context-menu" id="menu">
  <div>이름 바꾸기</div><div>삭제</div>
</div>
<script>
const menu = document.getElementById('menu');
const node1 = document.getElementById('node1');
let timer;
node1.ontouchstart = (e) => {
  timer = setTimeout(() => {
    menu.style.left = e.touches[0].clientX + 'px';
    menu.style.top = e.touches[0].clientY + 'px';
    menu.style.display = 'block';
  }, 500);
};
node1.ontouchend = () => clearTimeout(timer);
node1.onclick = () => alert('폴더 열림');
</script>
</body>
</html>
\`\`\``
  },
  {
    id: "fresh-refactor-4-sticky-header",
    category: "코드 개선",
    title: "스마트 스크롤 고정 헤더 레이아웃 시프트(CLS) 수정",
    userPrompt: `스크롤을 내리면 헤더가 작아지는 스크롤 헤더인데, 스크롤할 때마다 헤더의 height가 직접 바뀌면서 아래 본문 전체가 덜컹거리는 레이아웃 시프트(CLS)가 발생해. 본문이 전혀 흔들리지 않고 부드럽게 헤더가 전환되도록 고쳐줘.

다음은 현재 코드이다:
\`\`\`html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { margin:0; font-family:sans-serif; height:200vh; background:#f0f0f0; }
.header { position:fixed; top:0; left:0; width:100%; height:80px; background:#fff; display:flex; align-items:center; justify-content:center; box-shadow:0 2px 5px rgba(0,0,0,0.1); transition:height 0.2s; }
.content { margin-top:80px; padding:20px; }
</style>
</head>
<body>
<div class="header" id="header">메인 헤더</div>
<div class="content"><p>본문 내용...</p></div>
<script>
window.onscroll = () => {
  const h = document.getElementById('header');
  if (window.scrollY > 50) h.style.height = '40px';
  else h.style.height = '80px';
};
</script>
</body>
</html>
\`\`\``
  },
  {
    id: "fresh-refactor-5-dropdown-select",
    category: "코드 개선",
    title: "커스텀 드롭다운 선택창 300ms 딜레이 및 바깥 터치 닫기 수정",
    userPrompt: `커스텀 셀렉트 드롭다운인데, 모바일에서 버튼을 누를 때 300ms 터치 딜레이가 느껴지고, 메뉴가 열린 상태에서 다른 곳을 터치해도 메뉴가 닫히지 않고 계속 떠 있어. 탭 딜레이 없이 즉시 열리고 바깥 터치 시 깔끔하게 닫히도록 고쳐줘.

다음은 현재 코드이다:
\`\`\`html
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
body { font-family:sans-serif; padding:40px; background:#f5f5f5; }
.dropdown { position:relative; width:200px; }
.btn { width:100%; padding:10px; background:#fff; border:1px solid #ccc; cursor:pointer; }
.menu { position:absolute; top:100%; left:0; width:100%; background:#fff; border:1px solid #ccc; display:none; }
.menu.open { display:block; }
.item { padding:10px; cursor:pointer; }
</style>
</head>
<body>
<div class="dropdown">
  <button class="btn" id="btn">옵션 선택 ▼</button>
  <div class="menu" id="menu">
    <div class="item">옵션 1</div><div class="item">옵션 2</div>
  </div>
</div>
<script>
const btn = document.getElementById('btn');
const menu = document.getElementById('menu');
btn.onclick = () => menu.classList.toggle('open');
document.querySelectorAll('.item').forEach(it => {
  it.onclick = () => { btn.textContent = it.textContent + ' ▼'; menu.classList.remove('open'); };
});
</script>
</body>
</html>
\`\`\``
  }
];

async function run() {
  console.log("==================================================================");
  console.log("  Fresh Live Evaluation: 10 Scenarios × 2 Conditions (Strict Blind)");
  console.log(`  Model: ${MODEL} | Target: ${OUT_DIR}`);
  console.log("==================================================================\n");

  fs.mkdirSync(OUT_DIR, { recursive: true });
  const results = [];

  for (let i = 0; i < freshScenarios.length; i++) {
    const sc = freshScenarios[i];
    console.log(`\n▶ [${i + 1}/${freshScenarios.length}] [${sc.category}] ${sc.id} — ${sc.title}`);
    const scDir = path.join(OUT_DIR, sc.id);
    fs.mkdirSync(scDir, { recursive: true });

    for (const condition of ["without_skill", "with_skill"]) {
      const condDir = path.join(scDir, condition);
      fs.mkdirSync(condDir, { recursive: true });

      const indexFile = path.join(condDir, "index.html");
      if (fs.existsSync(indexFile) && fs.readFileSync(indexFile, "utf8").length > 500) {
        console.log(`  - Condition: ${condition} (이미 완료됨, 건너뜀)`);
        results.push({ scenario: sc.id, condition, ok: true });
        continue;
      }

      console.log(`  - Condition: ${condition} (완전 무상태 API 호출 중)...`);
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
        console.error(`    ✗ 실패: ${errMsg}`);
        results.push({ scenario: sc.id, condition, ok: false, error: errMsg });
      }

      // 안전 지연 12초
      await new Promise((r) => setTimeout(r, 12000));
    }
  }

  fs.writeFileSync(path.join(OUT_DIR, "summary.json"), JSON.stringify(results, null, 2));
  console.log(`\n🎉 완료! 위치: ${OUT_DIR}`);
}

run().catch((e) => {
  console.error("실행 실패:", e);
  process.exit(1);
});
