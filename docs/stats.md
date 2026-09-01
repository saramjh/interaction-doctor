# interaction-doctor — 실측 수치

이 문서에 나오는 모든 숫자는 아래 셋 중 하나에서 그대로 가져온
것이다. 추정치나 반올림은 없다.

- `evals/RESULTS.md` — Claude Code 9개 시나리오 baseline/treatment 실행 채점 + Gemini 5개 시나리오 noskill/skill 교차검증
- 21개 트리거 테스트(T1~T11, N1~N10) — 독립 서브에이전트 실행, 세션 기록 기반
- `research/ux-standards/common-pitfalls.md` — Playwright 런타임 검증으로 실제 재현된 결함 원장

**표본 크기는 항상 분모와 함께 쓴다. %로 바꾸지 않는다. Claude 표본과
Gemini 표본은 절대 합산하지 않는다.**

---

## 1. Claude Code 9개 시나리오 (n=9)

baseline = 스킬 미적용, treatment = 스킬 적용. 둘 다 같은 Claude Code
세션, 같은 `request.txt`, 같은 `evals/graders/*.js`로 채점.

| # | 시나리오 | 결과 | 재현 명령 |
|---|---|---|---|
| 01 | reorder-no-handle | **treatment 우위** | `cd evals && node graders/01-reorder-no-handle.js baseline` / `treatment` |
| 02 | swipe-delete-todo | 동률 | `node graders/02-swipe-delete-todo.js baseline` / `treatment` |
| 03 | bottom-sheet-comments | **실행 사고**(승패 아님) | `node graders/03-bottom-sheet-comments.js baseline` / `treatment` |
| 04 | carousel-photos | 동률 | `node graders/04-carousel-photos.js baseline` / `treatment` |
| 05 | multi-select-photos | 동률 | `node graders/05-multi-select-photos.js baseline` / `treatment` |
| 06 | context-menu-notes | 동률 | `node graders/06-context-menu-notes.js baseline` / `treatment` |
| 07 | tab-swipe-stories | 동률 | `node graders/07-tab-swipe-stories.js baseline` / `treatment` |
| 08 | side-drawer-menu | **treatment 우위** | `node graders/08-side-drawer-menu.js baseline` / `treatment` |
| 09 | longpress-triple-favorites | **treatment 우위**(문서 밖 관찰) | `node graders/09-longpress-triple-favorites.js baseline` / `treatment` |

**집계 (n=9)**: treatment 우위 3/9(01, 08, 09) · 동률 5/9(02, 04, 05,
06, 07) · 실행 사고 1/9(03, `const` 중복 선언으로 스크립트 전체가
죽어 실행 자체가 안 됨 — treatment 설계 자체는 baseline보다 나았음,
승패로 세지 않음).

**03을 제외한 실질 비교(n=8)**: treatment가 baseline보다 나쁜 방향으로
설계된 사례는 0/8이다.

전체 명령 전제: `cd evals && npm install` 먼저 실행. 근거·상세 서술은
`evals/RESULTS.md` §1~9, §전체요약 참조.

---

## 2. Gemini 교차검증 (n=5, Claude의 n=9와 별개 모집단 — 합산하지 않음)

noskill = 스킬 콘텐츠 미주입, skill = `SKILL.md`+`references/*.md`
전체를 system_instruction에 주입. 채점은 Claude 채점 때와 **동일한**
`evals/graders/*.js`를 재사용(모델만 바뀌었으므로 채점 기준을 새로
만들지 않음).

| # | 시나리오 | 결과 | Claude(n=9)와 방향 일치 | 재현 명령 |
|---|---|---|---|---|
| 01 | reorder-no-handle | skill 우위 | 일치 | `node graders/01-reorder-no-handle.js runs:2026-08-30T12-58-10-481Z:noskill` / `:skill` |
| 02 | swipe-delete-todo | 동률 | 일치 | `node graders/02-swipe-delete-todo.js runs:2026-08-30T12-58-10-481Z:noskill` / `:skill` |
| 04 | carousel-photos | 동률 | 일치 | `node graders/04-carousel-photos.js runs:2026-08-30T15-49-00-439Z:noskill` / `:skill` |
| 05 | multi-select-photos | 동률(재조사 후 정정, 아래 §4 함정4 참조) | 일치 | `node graders/05-multi-select-photos.js runs:2026-08-31T00-29-04-322Z:noskill` / `:skill` |
| 09 | longpress-triple-favorites | skill 우위(문서 밖 관찰) | 일치 | `node graders/09-longpress-triple-favorites.js runs:2026-08-30T15-49-00-439Z:noskill` / `:skill` |

**집계 (n=5)**: 확보한 5개 전부 Claude 쪽 결론과 방향이 같았다(5/5).
표본이 5개뿐이라 일반화 근거로는 약하지만, 특정 모델에 국한된
효과가 아니라는 정황은 된다.

**03, 06, 07, 08은 미확보 — 표본에서 제외, 채우지 않음**:
- 03: 스캐폴딩 사고(아래 §4 함정3) 도중 호출이 끊겨 서버 처리 여부조차 불명. 재시도 안 함.
- 06, 07, 08: HTTP 429 — 무료 티어 일일 할당량(`generate_content_free_tier_requests`, limit 20) 소진. 리셋 시점은 공식 문서에 없음(AI Studio 대시보드 전용).

상세 서술·표는 `evals/RESULTS.md` "## Gemini 교차검증" 참조.

---

## 3. 스킬 트리거 정확도 (n=21: T1~T11 n=11, N1~N10 n=10)

**판정 기준**: 요청에 대한 응답이 `symptoms.md`/`recipes.md`/
`platform.md`/`architecture.md`/`common-pitfalls.md` 5개 중 하나라도
실제로 Read/Grep 도구로 열렸으면 "트리거됨". `SKILL.md` 자체(Skill
도구 자동 반환)는 이 5개에 포함 안 함. 각 케이스는 독립된 새
서브에이전트 세션에서 실행해 앞 케이스 컨텍스트가 섞이지 않게 했다.

| 항목 | 결과 |
|---|---|
| 미탐 (T1~T11 중 트리거 안 됨) | **0/11** |
| 오탐 (N1~N10 중 트리거됨) | **1/10**(N9) — 최초 측정 시엔 2/10(N6, N9)이었으나 `SKILL.md` description 수정 후 재검증에서 N6 해소 |
| 부분 실패 (트리거는 됐지만 기대와 다른 컴포넌트/유형 참조) | **0/11** |

**N9(1/10, 미해소)**: 독립 핀치줌 요청. `interaction-doctor` 스킬
자체(Skill 도구)는 호출되지 않았다 — `architecture.md`/
`common-pitfalls.md`가 열린 건 스킬의 `description`이 유인한 게
아니라, `.claude/CLAUDE.md`의 프로젝트 전역 규칙("인터랙션을
구현하기 전에 반드시 읽는다")이 스킬과 무관하게 직접 발동한 것.
description 수정으로는 손댈 수 없는 영역이라 미해소로 남아 있다.

**N6(해소됨, 참고용)**: 데스크톱 마우스 우클릭 컨텍스트 메뉴 요청.
`SKILL.md`의 "컴포넌트를 처음부터 새로 구현할 때" 절이 모바일
터치·포인터 범위를 명시하지 않아 오탐이었다. description에
"모바일 터치·포인터 기반 구현" 한정 + "데스크톱 마우스 우클릭...은
대상이 아니다" 명시 문구를 추가한 뒤 완전히 새 세션에서 동일 요청을
재실행 → Skill 도구 호출 자체가 없어짐(해소 확인).

**재현 방법**: 이 21개는 grader 스크립트가 아니라 서브에이전트
판정이라 `node ...` 한 줄로 재현되지 않는다. 재현하려면 동일한
21개 프롬프트를, 매번 완전히 새로운 세션에서, 위 5개 참조 파일의
Read/Grep 여부로 판정해야 한다. 원본 케이스 21개 문장과 각 세션의
실제 판정 근거(어떤 파일을 열었는지, 원문 인용)는 이 세션의 기록에
있다 — 아직 저장소 파일로 옮겨지지 않았다(별도 과제).

---

## 4. 이 스킬이 예방하는 구체적 실수 목록

`research/ux-standards/common-pitfalls.md`가 Playwright 런타임
검증으로 실제 재현한 것만 나열한다 — 코드를 읽고 "이럴 것 같다"고
판단한 게 아니라, 실행해서 재현·확인된 것만이다.

### §4.5 체크리스트 — 컴포넌트 코드 자체의 결함 패턴 (n=2)

| 규칙 | 확신도 | 독립 재현 사례 |
|---|---|---|
| 규칙 1 — `pointerdown`에서만 초기화되는 상태를 `pointermove`가 "포인터가 눌려 있다"는 확인 없이 그대로 쓰면, 호버만으로 오작동한다 | 높음 | 2건 — `bottom-sheet-scroll-drag.md` §5-0, `long-press-triple-conflict.md` §5-0 |
| 규칙 2 — 같은 요소에 포인터가 겹칠 수 있는데 상태를 `pointerId`로 구분하지 않으면, 먼저 시작한 제스처의 타이머가 나중 제스처의 상태를 잘못 참조한다 | 중간 | 1건 — `long-press-triple-conflict.md` §5-5 |

### §6 — 배포/테스트 절차의 함정, 코드 결함 아님 (n=4)

| 함정 | 무엇이 문제였는가 | 확신도 |
|---|---|---|
| 함정 1 | 세션(프로세스) 시작 시점에 `.claude/skills/` 최상위 디렉터리가 없었으면, 그 세션 안에서 나중에 디렉터리를 만들어도 서브에이전트가 인식 못 함 — 새 세션 재시작 필요 | 이 프로젝트 실측 재현 1건 + [표준] 공식 문서(`code.claude.com/docs/en/skills` "Live change detection") |
| 함정 2 | `setPointerCapture`는 진짜 `pointerdown` 콜백 안에서만, `try/catch`로 감싸서 호출해야 헤드리스 자동화 환경에서 죽지 않는다 | [검증됨] — `tools/c10-drag-vs-scroll.html`이 C10 실측 192건+ 전체에서 지킨 패턴 |
| 함정 3 | `require.main === module` 가드 없이 파일 끝에서 무조건 실행하는 스크립트는, `require()`로 불러오기만 해도(리뷰 목적이든 실수든) 유료/과금 API 호출이 나간다 — CLI 인자 없을 때 기본값이 "전체 실행"이면 특히 위험 | 이 프로젝트에서 실제 재현된 사고 1건(승인 1건 대비 실제 호출 4건 완료+1건 상태불명) |
| 함정 4 | 같은 종류의 합성 이벤트(pointerdown→up→click)를 흉내내는 헬퍼가 여러 개일 때 하나만 고치면, 안 고친 쪽이 나중에 "새 버그 발견"처럼 보이는 오탐을 만든다 | 이 프로젝트에서 같은 근본 원인으로 2번 재현(`tap()`을 먼저 고치고, 나중에 `longPress()`에서 같은 문제가 다시 나옴) |

**함정 1~4는 §4.5와 성격이 다르다** — 컴포넌트 코드 결함이 아니라
배포/테스트 절차 자체의 함정이라 §4.5 체크리스트에는 포함하지
않는다. 원문 전체(원인 분석, 대응책, 재발 방지책)는
`common-pitfalls.md` §6 참조.

---

## 재현성 원칙

이 문서의 모든 표는 옆에 실제로 돌릴 수 있는 명령을 붙였다(§3의
21개 트리거 테스트만 예외 — 서브에이전트 판정이라 스크립트화되어
있지 않다는 것까지 명시했다). "이 스킬은 계속 발전한다"거나
"대부분의 문제를 해결한다" 같은 검증 불가능한 표현은 이 문서에
쓰지 않는다 — 숫자와 분모, 그리고 그 숫자를 만들어낸 명령만 남긴다.
