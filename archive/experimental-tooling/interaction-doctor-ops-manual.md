# interaction-doctor — 운용 매뉴얼

> 플레이북의 부속 문서. **무엇으로, 어디에, 어떻게 만드는가.**
> 소프트웨어 스택 / 배포 채널 / Claude Code 프롬프트 라이브러리

v1.0 / 2026-08

---

# Part 1. 소프트웨어 스택

## 1.1 결정 요약

| 영역 | 선택 | 이유 |
|---|---|---|
| 저장소 | GitHub (public, MIT) | 스타가 목표. 다른 선택지 없음 |
| 패키지 매니저 | pnpm | workspace 필요 시 대비. npm도 무방 |
| 언어 | TypeScript | doctor 패키지에 필요 |
| Inspector 빌드 | **Vite + Vanilla TS** | React 불필요. 번들 작고 로드 빠름 |
| Inspector 호스팅 | Cloudflare Pages | 무료, 커스텀 도메인, 자동 배포 |
| 문서 사이트 | **만들지 않음** | README + CONFLICTS.md로 충분. 나중에 필요하면 Astro Starlight |
| doctor 번들 | tsup | 설정 거의 없음. dev 전용이라 최적화 불필요 |
| GIF 캡처 | Kap (macOS) | 무료, GIF 직출력 |
| eval 실행 | `claude -p` + bash | Part 5 참조 |
| 트래픽 분석 | Cloudflare Web Analytics | 무료, 쿠키 없음 |
| 스타 추적 | star-history.com | 런칭 후 README에 삽입 |

## 1.2 실기기 테스트 환경 — 가장 중요

**이 프로젝트의 신뢰는 전적으로 여기서 나옵니다.** 시뮬레이터로 검증한 내용을 올리면 틀립니다. `touch-action`, 관성 스크롤, `pointercancel` 발생 조건은 **실기기에서만 정확히 재현됩니다.**

M3 MacBook Air 환경 기준 구성:

```
데스크톱     Chrome / Safari / Firefox — 로컬
Android     실기기 USB 연결 → chrome://inspect/#devices
            (Chrome DevTools 원격 디버깅, 콘솔·요소 검사 전부 가능)
iOS         실기기 USB 연결 → Safari > 개발자용 > [기기명]
            (기기: 설정 > Safari > 고급 > 웹 속성 켜기)
```

로컬 dev 서버를 실기기에서 열려면 터널이 필요합니다.

```bash
# Vite를 LAN에 노출
pnpm dev --host

# 또는 HTTPS가 필요할 때 (일부 포인터 API는 보안 컨텍스트 요구)
npx cloudflared tunnel --url http://localhost:5173
```

**iOS Simulator는 쓰지 마십시오.** 트랙패드 입력이 실제 터치로 매핑되지 않아 `touch-action` 동작이 다릅니다. 검증 결과로 인정하지 않습니다.

**보유 기기가 부족하면**: 안드로이드 저가 실기기 한 대만 사도 충분합니다. iOS는 본인 아이폰이면 됩니다. 두 기기 커버리지로 매트릭스 검증의 90%가 됩니다.

## 1.3 도메인

```
interaction-doctor.dev     ~$15/년   (Cloudflare Registrar 원가)
```

없어도 되지만 `github.io` 링크보다 공유 시 신뢰도가 확연히 높습니다. 런칭 자산에 들어가는 링크이므로 W4 전까지 확보.

## 1.4 총 비용

```
도메인          $15/년
호스팅          $0
Android 기기    $0~150 (없을 경우)
eval API        $30~60 (Part 5 산정)
──────────────────────
합계            $45 ~ $225
```

---

# Part 2. 서비스 제공 방식

## 2.1 배포 채널 매트릭스

| 채널 | 대상 | 설치 | 시점 |
|---|---|---|---|
| GitHub README + CONFLICTS.md | 전원 | 없음 (읽기) | **W1** |
| Agent Skill (직접 복사) | 모든 에이전트 | `cp -r` | W3 |
| Claude Code 플러그인 마켓플레이스 | Claude Code | `/plugin marketplace add` | W3 |
| skills.sh | 40+ 에이전트 | `npx skills add` | W3 |
| npm (dev 패키지) | 시니어 | `npm i -D` | W6 |
| Inspector 웹 | 전원 | 없음 | W4 |
| MCP 서버 | — | — | **보류** |

## 2.2 스킬 배포의 실제

Agent Skills는 개방 표준이고, Claude Code에서는 개인용 `~/.claude/skills/` 또는 프로젝트용 `.claude/skills/`에 두거나 플러그인으로 공유할 수 있습니다. 즉 **설치 경로가 세 갈래**이고, README에 셋 다 적어야 마찰이 0에 가까워집니다.

```markdown
## Install

**Claude Code (플러그인)**
```
/plugin marketplace add interaction-doctor/interaction-doctor
/plugin install interaction-doctor@interaction-doctor
```

**모든 에이전트 (skills.sh)**
```
npx skills add interaction-doctor/interaction-doctor
```

**수동**
```
git clone https://github.com/interaction-doctor/interaction-doctor
cp -r interaction-doctor/skills/interaction-doctor ~/.claude/skills/
```
```

플러그인 배포를 위해 저장소 루트에 `plugin.json`을, `skills/` 디렉터리에 스킬을 둡니다. 플러그인 이름이 `~/.claude/skills/` 아래 디렉터리명이자 스킬 네임스페이스가 되므로 공백이나 경로 구분자를 넣으면 안 됩니다.

## 2.3 저장소 최종 레이아웃

```
interaction-doctor/
├── README.md
├── CONFLICTS.md              ← W1. 스타 자산
├── LICENSE
├── plugin.json               ← 플러그인 배포용
│
├── skills/
│   └── interaction-doctor/
│       ├── SKILL.md
│       └── references/
│           ├── symptoms.md
│           ├── conflicts.md   (CONFLICTS.md 심볼릭 아님, 복사본)
│           ├── recipes.md
│           └── platform.md
│
├── apps/
│   └── inspector/            ← W4. Vite
│
├── packages/
│   └── doctor/               ← W6. 조건부
│
├── evals/
│   ├── broken/               ← 결함 컴포넌트 10개
│   ├── run.sh
│   └── results/
│
├── research/
│   └── demand.md             ← W0 수요 데이터
│
└── .github/
    ├── workflows/ci.yml
    └── ISSUE_TEMPLATE/
        ├── new-conflict.md   ← 매트릭스 빈칸 기여 유도
        └── wrong-diagnosis.md
```

## 2.4 MCP를 보류하는 이유

스킬은 에이전트에게 무엇을 할지 알려주는 레시피이고, MCP는 그걸 실행할 도구입니다. 스킬은 코드를 실행하거나 실행 중인 앱과 상호작용할 수 없습니다.

이 프로젝트의 내용은 95%가 지식이므로 스킬이 맞습니다. MCP가 정당화되는 건 **실행 중인 페이지를 관측할 때**뿐이고, 그건 W6의 doctor가 완성된 뒤에야 감쌀 대상이 생깁니다. 순서를 지키십시오.

---

# Part 3. Claude Code 운용 원칙

## 3.1 경계선 — 이게 가장 중요합니다

**인터랙션 지식을 Claude Code에게 생성시키면 안 됩니다.**

이 프로젝트의 존재 이유가 "에이전트가 기억에서 재구성하는 인터랙션 지식이 부정확하다"는 것입니다. 그 지식을 에이전트에게 생성시켜 그대로 올리면, **고치려던 문제를 그대로 배포하는 것**입니다. 그리고 대상 사용자는 검증 능력이 없어서 틀린 걸 그대로 믿습니다.

| 작업 | 담당 | 이유 |
|---|---|---|
| CONFLICTS.md 내용 | **본인** (CC는 골격만) | 프로젝트 신뢰의 근원 |
| symptoms.md 원인/수정 | **본인** (실기기 재현 후) | 위와 동일 |
| Inspector 구현 코드 | CC | 검증 가능. 눈으로 확인됨 |
| doctor 탐지 로직 | CC + 본인 검수 | 오탐 0이 목표 |
| eval 러너 스크립트 | CC 전담 | 결과가 곧 검증 |
| 결함 컴포넌트 10개 | CC 전담 | 의도적으로 틀린 코드 |
| README 초안 | CC | 본인이 문장 확정 |
| 런칭 문구 | CC 후보 생성 → 본인 선택 | — |

**규칙**: CC가 만든 인터랙션 지식은 전부 `🚧 unverified` 태그를 달고, 실기기 확인 후에만 태그를 뗍니다. 태그가 붙은 항목은 배포하지 않습니다.

## 3.2 CLAUDE.md

프로젝트 루트에 두면 CC가 자동으로 읽습니다. 매 프롬프트에 반복할 내용을 여기 넣습니다.

```markdown
# interaction-doctor

## 프로젝트 목적
AI 코딩 에이전트가 생성한 UI 코드의 인터랙션 결함을
진단하고 수정하도록 돕는다. GitHub 스타가 1차 목표.

## 절대 규칙

1. **인터랙션 지식을 기억에서 생성하지 말 것.**
   touch-action 값, 임계값, 이벤트 동작 등을 단정하지 않는다.
   불확실하면 `🚧 unverified — 출처 필요` 로 표시하고 멈춘다.
   잘못된 항목 하나가 프로젝트 전체 신뢰를 무너뜨린다.

2. **모든 사실 주장에 출처 링크를 단다.**
   MDN, W3C 스펙, WCAG, 플랫폼 공식 문서만 허용.
   블로그·StackOverflow는 출처로 쓰지 않는다.

3. **자체 런타임 라이브러리를 제안하지 않는다.**
   재정렬은 dnd-kit, 바텀시트는 vaul, 캐러셀은 embla를
   권장한다. 이 정직함이 프로젝트의 차별점이다.

4. **완성도보다 공개 가능한 최소 단위.**
   21칸 매트릭스 중 10칸만 채운다. 빈칸은 그대로 둔다.

## 스택
Vite + Vanilla TS (Inspector) / tsup (doctor) / pnpm

## 톤
문서는 한국어와 영어 병기하지 않는다. 영어가 기본.
README와 CONFLICTS.md는 영어. 개발 노트만 한국어.
```

## 3.3 작업 분리 전략

한 세션에 여러 층을 섞지 마십시오. Inspector 만들다가 스킬 문구를 손대면 둘 다 품질이 떨어집니다.

```
세션 1  Inspector 골격
세션 2  Inspector 시나리오 5개
세션 3  결함 컴포넌트 10개
세션 4  eval 러너
세션 5  doctor 탐지 로직
```

각 세션 시작 시 `/clear`로 컨텍스트를 비웁니다.

---

# Part 4. 프롬프트 라이브러리

그대로 복사해서 쓸 수 있게 작성했습니다. `[ ]` 부분만 채우십시오.

---

## W0 — 수요 조사

```
research/demand.md 를 만들어줘.

목적: 이 프로젝트가 해결하려는 문제(모바일 웹에서 드래그·스크롤·
롱프레스 제스처 충돌)가 실제로 얼마나 자주 발생하는지 공개
데이터로 확인하는 것.

작업:
1. 아래 저장소들의 GitHub Issues를 웹에서 검색해서
   각 쿼리의 히트 수와 최근 1년 비중을 조사해줘.
   - clauderic/dnd-kit
   - motiondivision/motion
   - davidjerleke/embla-carousel
   - emilkowalski/vaul
   쿼리: touch-action, scroll conflict, mobile drag,
        pointercancel, drag not working mobile

2. 각 저장소별로 가장 대표적인 이슈 3개의 제목과 URL을
   기록해줘. 이슈 본문에서 사용자가 증상을 어떤 말로
   표현했는지 원문 그대로 인용해줘. (나중에 symptoms.md의
   증상 문장을 실제 사용자 언어로 맞추는 데 쓸 것)

3. 표 형식으로 정리하고, 마지막에 총 히트 수를 합산해줘.

주의: 추정하지 마. 실제로 검색해서 확인한 수치만 적어.
확인 못 한 항목은 "확인 불가"로 표시해.
```

**이 프롬프트의 부가 가치**: 2번에서 나오는 **사용자 원문 표현**이 곧 `symptoms.md`의 증상 문장이 됩니다. 당신이 상상한 표현이 아니라 실제 사람들이 쓴 표현이라 매칭률이 훨씬 높아집니다.

---

## W1 — 충돌 매트릭스

**주의**: 여기서 CC에게 내용을 쓰게 하면 안 됩니다. **골격과 조사만** 시킵니다.

### 1단계 — 골격

```
CONFLICTS.md 의 골격만 만들어줘. 내용은 채우지 마.

구조:
1. 상단에 7×7 매트릭스 표 (Tap, DoubleTap, LongPress, Drag,
   Swipe, Scroll, Pinch). 각 셀에는 충돌 ID(C1~C13) 또는
   "ok" 또는 "—"만 넣어줘.
2. 아래에 C1부터 C13까지 섹션을 만들되, 각 섹션은
   빈 템플릿으로만 채워줘:

### C{n} — {A} ↔ {B}
**증상**
🚧 unverified
**원인**
🚧 unverified
**해소**
🚧 unverified
**우선순위 규칙**
🚧 unverified
**검증 방법**
🚧 unverified
**근거**
🚧 unverified

3. 파일 상단에 다음 주의문을 넣어줘:
   "Every entry is verified on real devices (desktop Chrome,
   iOS Safari, Android Chrome). Unverified entries are marked
   and excluded from the skill."

내용을 추측해서 채우지 마. 템플릿만.
```

### 2단계 — 출처 조사 (내용 생성이 아님)

```
C10 (Drag ↔ Scroll)에 대해 조사만 해줘. 결론을 쓰지 말고
1차 출처를 찾아서 정리만 해줘.

찾을 것:
1. CSS touch-action의 W3C 스펙 원문 URL과, pan-y / none /
   manipulation 각각의 정의 문장
2. MDN의 touch-action 페이지에서 스크롤 시작 시점에 관한
   설명 부분
3. 브라우저가 스크롤을 컴포지터 스레드에서 처리한다는
   내용의 1차 출처 (Chrome 개발자 문서 등)
4. setPointerCapture의 MDN 문서

출력 형식:
- 각 항목마다 [URL] + 해당 부분의 핵심 내용 요약 2문장

주의:
- 블로그, StackOverflow, Medium은 제외
- "이렇게 하면 됩니다" 같은 결론을 쓰지 마. 출처만.
- 못 찾은 항목은 "미발견"으로 표시
```

**이후 실기기 검증은 당신이 직접 합니다.** CC가 정리한 출처를 읽고, Inspector나 임시 페이지로 재현하고, 그 결과로 항목을 씁니다.

### 3단계 — 영문 교정

```
CONFLICTS.md 의 C10 섹션 내용을 내가 한국어로 썼어.
아래 원칙에 맞게 영어로 옮겨줘.

- 개발자가 읽는 기술 문서 톤. 격식 낮추고 직설적으로
- 문장 짧게. 수식어 최소화
- 코드 블록은 그대로 유지
- "you should" 대신 명령형 사용
- 마케팅 표현 금지 ("powerful", "seamless" 등)

[한국어 원문 붙여넣기]
```

---

## W2–W3 — Skill

### SKILL.md 초안

```
skills/interaction-doctor/SKILL.md 를 만들어줘.

이 스킬의 목적:
코딩 에이전트가 터치·포인터 인터랙션 문제를 진단하고
수정할 때 참조하는 지식. 예방보다 **디버깅**이 주 용도.

구조 (순서 고정):
1. frontmatter — name, description
2. 사용 순서 (증상 매칭 → 충돌 확인 → 레시피)
3. 진단 우선 규칙 (추측 금지, 확인할 것 3가지)
4. 절대 하지 않을 것 (안티패턴 4개)
5. 완료 전 자가 점검 체크리스트

references/ 파일 목록:
- symptoms.md, conflicts.md, recipes.md, platform.md

중요:
- description은 에이전트가 이 문장만 보고 로드 여부를
  결정한다. 디버깅 상황 문장을 앞에, 신규 구현을 뒤에.
- 본문은 짧게. 상세 내용은 references/로 미룬다.
- 인터랙션 지식 자체를 SKILL.md에 쓰지 마. 참조 구조만.
```

### description 튜닝 — 반복 필수

```
아래 description으로 스킬을 만들었는데, 실제로 트리거되는지
테스트할 케이스 12개를 만들어줘.

[현재 description 붙여넣기]

케이스 구성:
- 반드시 트리거되어야 하는 요청 6개
  (예: "모바일에서 드래그가 이상해", "스와이프 삭제 만들어줘")
- 트리거되면 안 되는 요청 6개
  (예: "버튼 색깔 바꿔줘", "API 응답 파싱해줘")

각 케이스를 실제 프롬프트 문장으로 써줘.
나중에 내가 하나씩 새 세션에서 던져보고 트리거 여부를
기록할 거야.
```

이 12개를 실제로 돌려보고, 오탐/미탐이 있으면 description을 고쳐 재실행합니다. **최소 3회 반복**하십시오. description이 스킬 품질의 절반입니다.

### symptoms.md 골격

```
references/symptoms.md 의 골격을 만들어줘.

research/demand.md 에 기록된 실제 GitHub 이슈 원문 표현을
참고해서, 증상 문장 25개를 뽑아줘.

규칙:
- 증상 문장은 **사용자가 실제로 쓸 법한 말**로. 전문용어 금지.
  좋음: "모바일에서 드래그하면 화면이 같이 움직여요"
  나쁨: "touch-action이 설정되지 않았습니다"
- 카테고리로 묶어줘 (드래그·스크롤 / 상태복구 / 탭·롱프레스 /
  스와이프 / 핀치 / 기타)
- 각 항목 아래는 아래 템플릿으로 비워둬:

**원인** 🚧 unverified
**확인** 🚧 unverified
**수정** 🚧 unverified
**부작용** 🚧 unverified
**관련** 🚧 unverified

원인과 수정을 추측해서 채우지 마.
```

---

## W4 — Inspector

### 골격

```
apps/inspector 를 만들어줘. Vite + Vanilla TypeScript.
React 쓰지 마.

기능:
1. 상단: 시나리오 선택 드롭다운 (지금은 "Drag in Scroll" 하나만)
2. 중앙: 스크롤 가능한 리스트 (항목 5개), 각 항목은 드래그 가능
3. 우측 상단: touch-action 실시간 토글 (auto / pan-y / none)
   — 토글하면 즉시 적용되어야 함. 가장 중요한 기능
4. 하단 패널 (실시간 갱신):
   - pointer type, pointerId, isPrimary
   - 경과 시간(ms), 누적 이동거리(px), 방향각(deg)
   - 현재 computed touch-action 값
   - 후보 제스처 / 승자 / 취소된 것과 그 이유
   - 이벤트 로그 (시각, 타입, 거리)

기술 요구사항:
- pointerdown/move/up/cancel 전부 기록
- touchstart/move/end/cancel 도 별도로 기록
  (같은 제스처가 두 계통으로 중복 발화하는 걸 보여주는 게 목적)
- 이동 임계값 8px를 기준선으로 시각 표시
- pointercancel 발생 시 로그 항목을 빨간색으로 강조
- 세션 로그를 JSON으로 다운로드하는 버튼

스타일:
- 다크 배경, 모노스페이스 폰트
- 장식 없이 계기판처럼. 애니메이션 최소
- 모바일 세로 화면에서 테스트 영역과 패널이 모두 보여야 함

만들지 말 것:
- 로그인, 저장, 공유 기능
- 코드 생성 기능
- 라우팅
```

### 시나리오 추가

```
Inspector에 시나리오를 4개 추가해줘.
기존 "Drag in Scroll"과 같은 구조를 유지하고,
시나리오별로 테스트 영역만 교체되게 해줘.

1. Tap vs Long Press
   - 카드 하나. 탭하면 색 변화, 500ms 롱프레스면 메뉴
   - 패널에 500ms 카운트다운 표시
2. Swipe vs Scroll
   - 세로 스크롤 리스트, 항목을 왼쪽으로 밀면 삭제 버튼
3. Drag vs Selection
   - 텍스트가 있는 카드를 드래그. 데스크톱에서 selectstart 관찰
4. Pinch vs Page Zoom
   - 이미지 영역. 핀치 시 브라우저 줌과의 경쟁 관찰

각 시나리오에서 해당 충돌에 관련된 CSS 속성을 실시간
토글할 수 있게 해줘 (user-select, touch-action 등).
```

### 실기기 대응

```
Inspector를 실기기에서 테스트하려고 해. 아래를 해줘.

1. vite.config.ts에서 --host로 LAN 노출 설정
2. 하단 패널이 모바일 세로 화면에서 잘리지 않도록 레이아웃 수정
   (테스트 영역 40vh, 패널 60vh, 패널 내부 스크롤)
3. 패널의 폰트 크기를 모바일에서 읽을 수 있게 조정
4. 화면 상단에 현재 접속 기기 정보 표시
   (userAgent에서 OS/브라우저만 추출, navigator.maxTouchPoints)
5. iOS Safari의 주소창 리사이즈로 레이아웃이 깨지지 않게
   dvh 단위 사용
```

---

## W5–W6 — doctor

```
packages/doctor 를 만들어줘. dev 전용 진단 도구.

사용법:
  npm i -D interaction-doctor
  <InteractionDoctor />   // React
  initDoctor()            // vanilla

동작:
1. 마운트 시 document 전체에서 포인터 핸들러가 붙은 요소를 수집
   (로드 시점에 EventTarget.prototype.addEventListener를 후킹해서
   등록 내역을 기록. React 합성 이벤트도 감안할 것)
2. 각 대상 요소에 대해 다음을 검사:
   - getComputedStyle(el).touchAction 값
   - 조상 중 스크롤 컨테이너 존재 여부 (overflow 검사)
   - pointercancel 리스너 등록 여부
   - tabIndex / 키보드 리스너 존재 여부
3. 실제 사용자 조작을 관측해서 추가 판정:
   - 드래그 활성화까지의 최소 이동거리 (임계값 유무 추정)
   - pointercancel 후 요소 transform이 복구되는지
4. 콘솔에 진단 출력

출력 형식 (에이전트가 그대로 읽을 수 있게):

[interaction-doctor] 2 issues

▸ .card-item
  observed:  pointerdown → pointermove(24px) → pointercancel
  computed touch-action: auto
  listeners: pointerdown, pointermove, pointerup
  
  ✗ touch-action not declared (drag inside scroll container)
    → .card-item { touch-action: pan-y }
  ✗ no pointercancel handler
    → drag state will not recover on interruption
  
  ref: C10, symptom #1, #6

절대 원칙:
- **오탐 0.** 확신이 없으면 보고하지 않는다.
  개발 콘솔에 오탐이 뜨는 도구는 즉시 제거된다.
- production 번들에 포함되지 않도록 할 것
- 성능 영향 최소화. 관측은 이벤트 기반, 폴링 금지
```

---

## W7 — eval

### 결함 컴포넌트

```
evals/broken/ 에 의도적으로 결함이 있는 React 컴포넌트
10개를 만들어줘. 각각 디렉터리 하나씩.

각 디렉터리 구성:
  Component.tsx    결함이 있는 구현
  SYMPTOM.md       사용자가 말할 법한 증상 한 문장
  EXPECTED.md      올바른 수정 내용 (채점 기준)

결함 목록:
01  스크롤 컨테이너 안 드래그, touch-action 없음
02  pointercancel 미처리로 드래그 상태 잔류
03  setTimeout만으로 구현한 롱프레스 (취소 불가)
04  임계값 없이 pointerdown에서 즉시 드래그 활성화
05  mouse 이벤트만 사용 (모바일 미동작)
06  onClick과 드래그가 우선순위 없이 공존
07  스와이프 삭제가 세로 스크롤을 차단
08  드래그 시 텍스트 선택 발생 (user-select 미설정)
09  키보드로 재정렬 불가 (WCAG 2.5.7)
10  pointer와 touch 이벤트 병용으로 중복 발화

주의:
- 결함은 자연스러워야 함. AI가 실제로 만들 법한 코드로.
- 일부러 이상하게 쓰지 말 것. 겉보기엔 멀쩡해야 함
- SYMPTOM.md는 전문용어 없이. "모바일에서 드래그하면
  화면이 같이 움직여요" 같은 문장으로
- 각 컴포넌트는 독립 실행 가능해야 함
```

### 측정 러너

```
evals/run.sh 를 만들어줘.

목적: 스킬 유무에 따른 디버깅 왕복 횟수와 비용 비교.

Claude Code의 print 모드를 쓴다:
- baseline: claude -p --bare  (스킬·CLAUDE.md 등 자동 발견을
  전부 건너뛰므로 깨끗한 대조군이 됨)
- treatment: 스킬이 설치된 상태에서 claude -p

--output-format json 으로 받으면 num_turns, total_cost_usd,
duration_ms 가 포함되므로 그걸 그대로 지표로 쓴다.

스크립트 동작:
1. evals/broken/ 의 각 케이스에 대해
2. 임시 작업 디렉터리에 Component.tsx 복사
3. SYMPTOM.md 내용을 프롬프트로 전달
4. baseline / treatment 각 조건으로 실행
5. 조건당 3회 반복
6. 결과를 CSV로 evals/results/ 에 저장
   컬럼: case, condition, run, num_turns, cost_usd, duration_ms, fixed
7. 'fixed' 판정은 EXPECTED.md의 조건을 만족하는지
   별도 검사 스크립트로 확인

--max-turns 로 상한을 걸어서 무한 루프를 막아줘.
--permission-mode 와 --allowedTools 로 파일 편집만 허용해줘.
```

**핵심**: `--output-format json`의 `num_turns`와 `total_cost_usd`가 정확히 당신이 README에 쓸 두 숫자입니다. 별도 계측 코드가 필요 없습니다.

### 결과 분석

```
evals/results/ 의 CSV를 분석해서 evals/RESULTS.md 를 만들어줘.

산출:
1. 조건별 평균 왕복 횟수, 중앙값, 표준편차
2. 조건별 평균 비용, 총 절감률
3. 케이스별 비교 표 (어떤 결함에서 효과가 큰지)
4. 수정 성공률 (fixed 비율)
5. 모델별 차이

주의:
- 반올림해서 좋아 보이게 만들지 마
- 효과가 없는 케이스는 그대로 표시해
- n과 신뢰구간을 명시해
- 표본이 작으면 작다고 써
```

---

## W8 — 런칭 자산

### README

```
README.md를 써줘. 영어. 아래 순서 고정.

1. 한 줄: "Other skills help agents build UI.
   This one helps them fix interactions that broke."
2. GIF 자리 (내가 넣을 것) — ![](docs/demo.gif)
3. "Sound familiar?" — 증상 5개 불릿 (symptoms.md에서)
4. Install — 세 가지 방법 (plugin / skills.sh / manual)
5. Before/After — 에이전트 대화 로그 비교
   (evals 실제 세션 로그를 넣을 자리만 만들어줘)
6. Numbers — evals/RESULTS.md 요약
7. Conflict matrix — CONFLICTS.md의 표를 README에 직접 삽입
   (링크만 걸지 말 것)
8. Inspector 링크
9. Why this exists — research/demand.md 요약
10. Prior art — 무엇을 대체하지 않는지
    (W3C Pointer Events, touch-action, WCAG 2.5.x,
     dnd-kit, RNGH, Flutter Gesture Arena)
11. Contributing — 매트릭스 빈칸 11개
12. License

톤:
- 마케팅 표현 금지
- 과장 금지. 숫자는 측정값 그대로
- 첫 3줄 안에 무슨 문제인지 이해되어야 함
```

### 런칭 문구

```
런칭용 문구 후보를 만들어줘. 각 채널별로 3개씩.

원칙:
- 제목은 **해법이 아니라 문제**를 말한다
- 도구 이름을 제목에 넣지 않는다
- 과장 금지

채널:
1. Hacker News (Show HN) — 영어, 80자 이내
2. Reddit r/webdev — 영어, 본문 3문단 포함
3. X/Twitter — 영어, 스레드 5개 트윗
4. GeekNews — 한국어, 제목 + 본문 3문단

각 후보마다 왜 그렇게 썼는지 한 줄 설명을 붙여줘.
```

### 이슈 템플릿

```
.github/ISSUE_TEMPLATE/ 에 템플릿 2개를 만들어줘.

1. new-conflict.md — 매트릭스 빈칸 기여용
   - 어떤 두 제스처의 충돌인지
   - 재현 환경 (기기, OS, 브라우저)
   - 증상
   - 확인한 원인과 출처
   - 실기기 검증 여부 체크박스 (필수)

2. wrong-diagnosis.md — 잘못된 진단 신고용
   - 어떤 항목이 틀렸는지
   - 실제 동작
   - 재현 환경

그리고 good first issue 라벨을 붙일 이슈 5개의 제목과
본문 초안을 만들어줘. 전부 매트릭스 빈칸을 채우는 작업으로.
```

---

# Part 5. eval 자동화 상세

## 5.1 왜 Claude Code가 계측기로 적합한가

print 모드는 `-p`(또는 `--print`)로 실행되며 에이전트 루프를 그대로 돌린 뒤 결과를 출력하고 종료합니다. `--output-format`은 text·json·stream-json을 지원하고, json 응답에는 `session_id`, `total_cost_usd`, `duration_ms`, `num_turns`가 포함됩니다.

즉 **왕복 횟수와 비용이 도구 자체에서 나옵니다.** 별도 계측이 필요 없습니다.

그리고 `--bare`는 훅·스킬·커맨드·서브에이전트·플러그인·MCP 서버·자동 메모리·CLAUDE.md의 자동 발견을 전부 건너뜁니다. **이게 완벽한 대조군입니다.** 스킬 설치 여부를 수동으로 껐다 켤 필요가 없습니다.

## 5.2 실행 형태

```bash
# 대조군 — 스킬 없음, 프로젝트 설정 없음
claude -p --bare --max-turns 12 --output-format json \
  "$(cat SYMPTOM.md)"

# 실험군 — 스킬 설치된 상태
claude -p --max-turns 12 --output-format json \
  "$(cat SYMPTOM.md)"
```

`--bare`는 OAuth와 키체인 읽기도 건너뛰므로 `ANTHROPIC_API_KEY`가 필요합니다.

## 5.3 비용 산정

```
케이스 10 × 조건 2 × 모델 2 × 반복 3 = 120 세션
세션당 평균 $0.20 ~ $0.50 가정
──────────────────────────────
총 $24 ~ $60
```

먼저 케이스 2개로 파일럿을 돌려 실제 세션 비용을 확인하고 전체 규모를 확정하십시오.

## 5.4 주의

- `--max-turns` 없이 돌리면 무한 루프로 비용이 폭주합니다. 반드시 상한을 거십시오
- `--permission-mode`와 `--allowedTools`로 파일 편집만 허용하십시오
- 세션 로그 원본을 보관하십시오. **README의 Before/After 캡처가 여기서 나옵니다**

---

# 부록 — 첫 주 체크리스트

```
□ GitHub 저장소 생성 (public, MIT)
□ CLAUDE.md 작성 (Part 3.2 템플릿)
□ 도메인 확보
□ Android 실기기 확보 및 chrome://inspect 연결 확인
□ iOS 실기기 웹 속성 활성화 및 Safari 개발자 메뉴 연결 확인
□ W0-V1 수요 조사 프롬프트 실행 → research/demand.md
□ W0-V2 시니어 인터뷰 10명
□ 게이트 판정: 총 히트 50건 이상인가
□ 게이트 판정: L3 doctor 포함 여부 결정
```

**여기까지가 5시간입니다.** 이후 일정은 두 게이트 결과가 정합니다.
