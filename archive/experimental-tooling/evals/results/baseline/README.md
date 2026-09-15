# evals/

`interaction-doctor` 스킬의 실제 효용을 측정하기 위한 평가 하네스.
`demo/experiment_report.md`가 임시로 수행한 스킬 有/無 비교(1개
과제, 세션 로그 대조)를 여러 시나리오·정량 채점으로 확장한다.

## 역할 분담 (반드시 지킨다)

이 저장소의 자동화 규모가 커지면 "누가 어디까지 했는지"가 흐려지기
쉽다 — 그래서 매 단계 시작 전에 이 표를 다시 읽는다.

| 단계 | 주체 | 범위 |
|---|---|---|
| 1. `evals/subjects/` 제작 | **Claude Code(이 세션)** | 결함이 심어진 실제 프로젝트(`project/`) + 사용자 요청문(`request.txt`) 작성까지 |
| 2. `evals/graders/` 제작 | **Claude Code(이 세션)** | 시나리오별 Playwright 채점 스크립트 작성까지 |
| 3. Gemini/Antigravity 세션 실행 | **사용자** | `evals/subjects/*/project/` + `request.txt`를 Gemini CLI/Antigravity에 수동으로 넣고 직접 실행한다. **이 저장소 안의 어떤 스크립트도 Gemini/Antigravity를 자동으로 호출하지 않는다** — 이번 작업 지시 범위 밖이며, 앞으로도 별도 명시적 요청 없이는 만들지 않는다. |
| 4. 결과 채점 | **Claude Code(이 세션), 재개** | 사용자가 3단계 결과물(Gemini가 만든 코드)을 가져오면 그때 `evals/graders/`로 채점하고 `evals/RESULTS.md`를 채운다. **이번 지시 범위 밖** — 별도 요청 시 진행한다. |

1~2단계만 지금 순서대로(1→2→3, "3"은 이 README 자체 포함 전체
`evals/` 스캐폴딩의 3번째 산출물인 `RESULTS.md` 템플릿을 가리킨다)
만들고, 만들 때마다 보고하고 멈춘다.

## 이 하네스가 측정하려는 것

`experiment_report.md`의 대조군/실험군 비교는 세션 1개, 과제 1개,
사후 로그 분석이라는 한계가 있었다("정량적 실험 데이터"라고 표는
붙였지만 n=1). `evals/`는 그 한계를 좁힌다:

- **시나리오 수를 늘린다**: 8개 컴포넌트(`research/ux-standards/patterns/`)
  + 오염방지 3유형(`ux-standards-architecture.md` §3) 전부에서 최소
  1개씩, 8~10개.
- **채점을 스크립트화한다**: "코드 안정성 점수 95/100" 같은 주관적
  채점 대신, Playwright로 정확한 수치(픽셀 이동량, ms 타이밍, 이벤트
  발생 횟수)를 판정한다 — 이 프로젝트가 `CONFLICTS.md`와
  `common-pitfalls.md`에서 이미 지키는 규율(추측 대신 실측)을 평가
  하네스에도 그대로 적용한다.
- **Gemini 실험의 실제 결함을 최소 1개 재현한다**: `demo/experiment_report.md`가
  기록한 런타임 오동작("무한루프, 드래그 불능, 정렬 씹힘") 중
  재현 가능한 것을 시나리오에 심어서, "그때 그 결함이 다시 나오는가"를
  직접 물을 수 있게 한다.

## 디렉터리 구조

```
evals/
├── README.md              이 파일
├── subjects/               1단계 산출물
│   └── NN-scenario-name/
│       ├── project/        결함이 심어진 실제 프로젝트(단일 HTML, 이 저장소의
│       │                   demo/*.html·tools/*.html 관례를 따름)
│       └── request.txt     사용자가 실제로 할 법한 요청 한 줄(내부 용어 금지)
├── graders/                2단계 산출물 — project/ 폴더 밖에 완전히 분리
│   └── NN-scenario-name.spec.(js|ts) 또는 동등한 Playwright 스크립트
└── RESULTS.md              3단계 산출물 — baseline/treatment 비교 빈 템플릿
```

## `request.txt` 작성 규칙

`evals/subjects/*/request.txt`는 이 스킬이나 이 프로젝트를 전혀 모르는
실제 사용자가 답답해서 던지는 말 한 줄이어야 한다. 다음을 절대
쓰지 않는다:

- 컴포넌트 이름("재정렬 리스트", "바텀시트" 같은 이 프로젝트의 분류어)
- "레시피", "오염방지", "C10", "activation delay" 같은 이 프로젝트
  내부 용어
- 채점 기준이나 기대 동작에 대한 힌트("8px 넘으면", "500ms 안에" 등)

대신 증상만 자연스러운 사용자 말투로 적는다("눌러서 옮기려는데
그냥 화면이 스크롤돼버려요" 같은 식).

## `project/` 작성 규칙

- 단일 HTML 파일(인라인 CSS/JS)로 만든다 — 이 저장소의 기존
  `demo/broken-*.html` 관례와 동일. 빌드 스텝이 필요 없어야 Gemini/
  Antigravity 어느 쪽에 넣어도 바로 열린다.
  - UI는 재생목록·할일목록·사진첩·받은편지함 등 그럴듯한 실제
    제품처럼 보이게 만든다 — 연구 문서 티(주석에 "C10", "규칙 1"
    같은 내부 용어)가 나지 않게 한다.
- 결함은 **정확히 하나**, 이 프로젝트가 이미 실측·문서화한 패턴 중
  하나를 재현한다 — 새로 발명한 결함을 넣지 않는다. 어떤 문서의
  어떤 결함을 재현했는지는 `project/` 밖(이 README의 시나리오
  목록이나 커밋 메시지)에만 남기고, `project/` 파일 자체에는 남기지
  않는다 — Gemini/Antigravity가 힌트를 보고 정답을 맞히면 채점
  의미가 없어진다.

## 시나리오 목록

9개. 8개 컴포넌트 전부 + 오염방지 3유형 전부를 최소 1개씩 커버한다
(바텀시트=오염방지 B, 사이드드로어=오염방지 C가 컴포넌트와 자연히
겹치고, 롱프레스 3중 충돌은 오염방지 A를 단독으로 다룬다). 어떤
결함을 재현했는지는 여기(및 아래 표)에만 적고 `project/` 안에는
적지 않는다 — 채점 대상이 힌트를 보면 채점 의미가 없어진다.

| # | 시나리오 | 컴포넌트 / 오염방지 유형 | 재현한 결함 | 근거 문서 |
|---|---|---|---|---|
| 01 | reorder-no-handle | reorderable-list (핸들 없음) | `touch-action` 기본값(`auto`)으로 세로 드래그가 항상 취소되고, `pointercancel` 미처리로 드래그가 중간에 멈춘 채 복구 안 됨. **Gemini 실험(`demo/experiment_report.md`)의 "드래그 불능" 결함 재현.** | `CONFLICTS.md#C10` |
| 02 | swipe-delete-todo | swipe-actions | `pointerdown` 없이도 `pointermove`/`pointerup`이 반응(공유 변수 `startX`가 `pointerdown` 안에서만 초기화됨) — 건드리지 않아도 스와이프 판정이 나서 삭제까지 됨 | `common-pitfalls.md` 규칙 1 |
| 03 | bottom-sheet-comments | bottom-sheet + 오염방지 유형 B | 시트 드래그 핸들러가 내부 리스트의 `scrollTop`을 확인하지 않아, 리스트 스크롤 중에도 시트 전체가 딸려 옴(원본 미수정 버전) | `nested-interactions/bottom-sheet-scroll-drag.md` §4 |
| 04 | carousel-photos | carousel | `scroll-snap-type` 자체가 없어 스와이프 후 사진 사이 임의 위치에 정지 | `research/ux-standards/patterns/carousel.md` |
| 05 | multi-select-photos | multi-select | 다중 선택 모드 진입 후 탭 핸들러가 클릭된 타일이 아니라 클로저에 캡처된 최초 타일(`activeTile`)만 토글 — 다른 사진을 눌러도 선택 안 됨 | `research/ux-standards/patterns/multi-select.md` |
| 06 | context-menu-notes | context-menu | `contextmenu` 이벤트에 `preventDefault()` 호출 자체가 없어 커스텀 메뉴와 브라우저 기본 메뉴가 같이 뜸 | `CONFLICTS.md#C6` |
| 07 | tab-swipe-stories | tab-swipe | 탭 전환 스와이프 리스너가 내부 가로 스크롤 스토리 목록을 제외하지 않고 이벤트 버블링을 그대로 받아, 스토리를 넘기면 탭이 바뀜 | `research/ux-standards/patterns/tab-swipe.md` |
| 08 | side-drawer-menu | side-drawer + 오염방지 유형 C | 엣지 스와이프가 유일한 진입 경로 — 항상 열 수 있는 버튼 등 대체 경로가 없음(iOS 시스템 뒤로가기 제스처와 겹치는 영역) | `nested-interactions/side-drawer-back-gesture.md` |
| 09 | longpress-triple-favorites | 오염방지 유형 A | 롱프레스 3중 분기(재정렬/메뉴/다중선택)에 `armed` 플래그·`pointerId` 추적이 둘 다 없음 — 호버만으로 오작동, 두 손가락이 같은 항목을 누르면 콜백이 중복 발동 | `nested-interactions/long-press-triple-conflict.md` §4(원본, 수정 전) |

각 `project/index.html`은 빌드 스텝 없이 브라우저로 바로 열린다.
`request.txt`는 위 "재현한 결함" 열의 내용을 전혀 언급하지 않고,
증상만 자연스러운 사용자 말투로 적었다.
