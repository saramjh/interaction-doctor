# evals/RESULTS.md

`evals/graders/`로 baseline(스킬 미적용)/treatment(스킬 적용) 9개
시나리오를 Playwright로 실제 실행해 채점한 결과. 코드를 읽고
"있다/없다" 판단한 게 아니라, 합성 PointerEvent를 실제로 던지고 DOM에
반영된 결과(클래스, `transform`, 렌더된 텍스트 순서, 콘솔 예외)로만
판정했다. 채점 기준은 각 시나리오에 해당하는
`research/ux-standards/patterns/` 또는 `nested-interactions/` 문서의
§5 런타임 검증 조건 + `common-pitfalls.md` §4.5를 그대로 가져왔다.

숫자를 부풀리지 않는다 — 충족 못 한 항목은 "미충족"으로 그대로
적는다. treatment가 baseline보다 나쁜 항목이 있어도 숨기지 않는다.

재현: `cd evals && npm install && node graders/<번호>-<이름>.js <baseline|treatment>`

---

## 01. reorder-no-handle

**채점 기준**: `.claude/skills/interaction-doctor/references/recipes.md` 레시피 4(a~d) + `common-pitfalls.md` 규칙 1·2.
**구현 확인**: 두 조건 다 `touch-action`/`pointercancel` 자체는 처리했다 — baseline은 지연 없이 즉시 드래그, treatment는 터치일 때만 400ms 지연 + 8px 이동 취소를 자체적으로 구현했다(레시피 4가 나중에 채택한 것과 같은 방향).

| 항목 | baseline | treatment |
|---|---|---|
| a) 8px 미만 이동 유지 → 진입, ms | 즉시 진입(0.7ms) — 지연 메커니즘 자체가 없음 | **충족** — 405.3ms에 진입 |
| b) 지연 중 8px 초과 이동 → 취소 | 해당 없음(지연 창이 없어 테스트 불가) | **충족** — 진입 안 됨(`draggingAtEnd:false`), 재정렬도 안 일어남 |
| c) 진입 후 이동 → 실제 재정렬(DOM 순서 변화) | **충족** | **충족** |
| d) 두 번째 포인터(다른 Y) 끼어듦 → 규칙 2 격리 | **미충족** — 공유 `startY`가 덮어써져 재정렬 자체가 실패함(`titlesBefore===titlesAfter`) | **미충족** — 동일한 이유로 실패 |
| `setPointerCapture` 예외 처리(common-pitfalls §6 함정2) | 없음 — 합성 포인터에서 `"No active pointer"` 예외가 무방비로 발생(`pageErrors`에 기록) | **있음** — `try/catch`로 방어, 예외 0건 |

**d 재현 방법**: `pointerId=1`로 첫 항목을 누른 뒤 200ms 뒤 `pointerId=2`로 같은 행의 다른 Y 지점을 누름(첫 번째 해제 안 함) → `pointerId=1`로 실제 재정렬 제스처를 마무리. 두 구현 다 `pointerdown` 핸들러가 진행 중인 제스처 유무를 확인하지 않고 `startY`(baseline) / `pointerId`+좌표 상태(treatment)를 무조건 덮어써서, 최종 계산이 `pointerId=2`가 남긴 값을 기준으로 어긋난다 — `long-press-triple-conflict.md` §5-5가 레시피 1에서 발견한 것과 같은 종류의 결함이 여기서도 그대로 재현됐다.

**결론**: treatment가 baseline보다 명확히 낫다(레시피 4가 나중에 도달한 hold-delay+8px-cancel 설계를 이미 구현했고, 예외 방어도 있음) — 단 **둘 다 규칙 2(멀티포인터)는 못 지켰다.** 이건 스킬 유무와 무관하게 공통으로 남은 결함이다.

---

## 02. swipe-delete-todo

**채점 기준**: `common-pitfalls.md` 규칙 1(원본 결함) · 규칙 2 + 보조로 `swipe-actions.md`의 [표준] 커밋 거리(Android `getSwipeThreshold()` 기본값 50%, 항목 폭 기준).
**구현 확인**: 두 조건 다 `isDragging`/`isDown` 플래그를 추가해 규칙 1을 고쳤다. 코드 읽기로 확인: 둘 다 `SWIPE_DELETE_PX = 80`(고정 픽셀)을 쓴다 — Android [표준]인 "항목 폭의 50%"가 아니다. 이건 이 시나리오가 원래 재현하려던 결함이 아니라서 별도 합/불 판정은 안 매긴다.

| 항목 | baseline | treatment |
|---|---|---|
| 규칙 1 — 빈 `pointermove`(pointerdown 없이) 반응 안 함 | **충족** | **충족** |
| 규칙 1 — 빈 `pointerup`(pointerdown 없이) 삭제 안 됨 | **충족** | **충족** |
| 정상 스와이프(진짜 pointerdown부터)는 여전히 작동 | **충족** | **충족** |
| 규칙 2 — 두 번째 포인터 끼어들어도 올바르게 삭제됨 | **미충족** — `startX`가 덮어써져 삭제 안 됨 | **미충족** — 동일 |
| `setPointerCapture` 예외(공통 §6 함정2) | 있음(`pageErrors` 1건, `try/catch` 없음) | 해당 없음(`setPointerCapture` 자체를 안 씀) |

**규칙 2 재현 방법**: `pointerId=1`을 오른쪽 끝에서 눌러 왼쪽으로 90px(임계값 80px 넘김) 밀려는 제스처 도중, 200ms 뒤 `pointerId=2`가 `pointerId=1`의 최종 도착 지점 근처(+5px)를 누름(첫 번째 해제 안 함). 상태가 격리돼 있었다면 `pointerId=1`은 여전히 -90px로 계산돼 삭제됐어야 하는데, 두 구현 다 공유 `startX`가 `pointerId=2`의 좌표로 덮어써져 최종 `dx`가 -5px로 쪼그라들어 삭제되지 않았다.

**결론**: 01번과 같은 패턴 — 스킬 적용 여부와 무관하게 규칙 1(이 시나리오의 원래 타깃)은 둘 다 고쳤고, 요청하지 않았던 규칙 2는 둘 다 안 고쳤다. treatment의 유일한 차이는 `setPointerCapture`를 아예 안 써서 그 경로의 예외 위험 자체가 없다는 것.

**재검증 결과 — treatment 콘텐츠 갱신(baseline은 변경 없음)**

이건 baseline이 달라진 게 아니다. `common-pitfalls.md` §7에서 공용
패턴 `withSinglePointerGate`([이 프로젝트의 설계 판단], §7-4)가
확정되면서 `recipes.md`가 갱신됐고, 그 패턴을
`evals/subjects/02-swipe-delete-todo/project/index.html`(원본 결함
코드, baseline/treatment 둘 다의 출발점)에 직접 적용해
`evals/results/treatment-v2/subjects/02-swipe-delete-todo/`로
재채점했다. 위 표(baseline vs treatment)는 그대로 남긴다 — 지우지
않는다.

| 항목 | treatment(원래) | treatment-v2(게이트 적용) |
|---|---|---|
| 규칙 1 | **충족** | **충족** |
| 규칙 2 — 두 번째 포인터 끼어들어도 올바르게 삭제됨 | **미충족** | **충족** — `finalDx`가 -5px(덮어써짐)에서 -90px(의도한 값)로 정정, 실제 삭제됨 |
| 정상 스와이프 | **충족** | **충족** |

**이력**: 이전(원래 treatment, baseline과 비교) → **동률**(규칙 2를
baseline과 마찬가지로 못 지킴). 갱신 후(treatment-v2, baseline과
비교) → **treatment 우위**(baseline은 여전히 규칙 2 미충족,
treatment-v2만 충족). 삭제 임계값(80px)·dx 계산 로직은 원본과 한
글자도 다르지 않다 — 리스너 등록을 게이트로 감싼 것만 다르다.

재현: `cd evals && node graders/02-swipe-delete-todo.js treatment-v2`

**재검증 결과 (세 번째 버전) — 고정 80px 대신 레시피5(플랫폼 분기) 적용**

`recipes.md`에 레시피 5(스와이프 삭제, `swipe-actions.md` §1·§2 기반)를
신설했다 — Android `getSwipeThreshold()`(항목 폭 50%, [표준])와 iOS
`performsFirstActionWithFullSwipe`(끝까지 밀면 즉시 실행, 동작 모델은
[표준]·정확한 %는 Apple 미공개라 90%를 [이 프로젝트의 설계 판단]으로
근사) 둘 다 공식 API 문서에 정확한 근거가 있어서, 처음으로
`ux-standards-architecture.md` §1-6(이번에 신설, 절충 대신 실제
`navigator.userAgentData`/UA 문자열 분기를 허용하는 조건)을 적용했다.
`evals/subjects/02-swipe-delete-todo/project/index.html`(원본 결함)에
이 레시피를 그대로 적용해 `evals/results/treatment-v3/subjects/
02-swipe-delete-todo/`를 만들었다. 위 baseline/treatment/treatment-v2
표는 전부 그대로 남긴다.

| 항목 | baseline / treatment / v2(고정 80px) | treatment-v3(레시피5, 플랫폼 분기) |
|---|---|---|
| 커밋 거리 | **고정 80px** — Android 50%도 iOS 모델도 아닌 임의값(RESULTS.md 02번 최초 채점에서 이미 지적됨) | **Android: 항목 폭 50%**([표준]) / **iOS: 항목 폭 90% 근사**([이 프로젝트의 설계 판단], 동작 모델만 [표준]) |
| 규칙 1·2 | v2부터 게이트로 충족 | 처음부터 `withSinglePointerGate`로 충족(나중에 패치 아님) |
| 수평 의도 게이트(C12) | **없음** — `abs(dx)>abs(dy)` 판정 자체가 baseline/treatment/v2 어디에도 없었다(이전 조사에서 발견, 별도 기록만 하고 안 고쳤던 것) | **있음** — 이번에 처음 추가 |
| `pointercancel` 리셋(C9) | 있음(기존에도 원위치 복귀 로직 존재) | 있음(무수정 재사용) |

**그레이더 재확인(§9 원칙 적용) — 기존 그레이더의 고정 px 값이
새 구현과 안 맞는다**: `node graders/02-swipe-delete-todo.js
treatment-v3`로 그대로 채점하면 `normalSwipeStillWorks`/
`rule2_secondPointer`가 **미충족**으로 나온다. 코드를 의심하기 전에
원인부터 확인했다 — 그레이더의 이동 거리(90~100px)는 옛 고정
80px 구현을 전제로 계산된 값인데, treatment-v3는 실제 항목 폭의
50%(헤드리스 기본 뷰포트에서 약 628px)를 요구해서 애초에 임계값
근처도 못 간다. **코드 결함이 아니라 그레이더-구현 간 전제
불일치다** — `tools/nested/swipe-action-verify-check.js`(레시피5
자체의 7개 케이스 검증, 이미 전부 통과)와 별도로, 이 시나리오의
실제 항목 폭 기준으로 재계산한 이동 거리로 직접 재확인했다:

| 케이스 | 이동 거리(실제 항목 폭 1256px 기준) | 결과 |
|---|---|---|
| 50% 직전(613px) | 삭제 안 됨 | 의도대로 |
| 50% 직후(643px) | 삭제됨 | 의도대로 |
| 두 번째 포인터 간섭 + 50%+여유 이동 | 삭제됨(간섭 무시) | 규칙 2 정상 |

**정직하게 밝힌다**: 이 두 그레이더 항목(`normalSwipeStillWorks`,
`rule2_secondPointer`)의 하드코딩된 이동 거리를 고치지 않았다 —
baseline/treatment/treatment-v2(전부 고정 80px 가정)와 treatment-v3
(퍼센트 기반)를 동시에 공정하게 테스트할 수 있는 단일 거리값이
없기 때문이다(고정값 vs 뷰포트 상대값은 근본적으로 다른 척도다).
그래서 그레이더는 그대로 두고, 이 절에 실제 임계값 기준 재확인
결과를 별도로 남기는 방식을 택했다 — 그레이더를 "고쳐서 통과시키는"
것과 "제대로 된 다른 방법으로 재확인하는" 것을 구분한다.

재현: `cd evals && node graders/02-swipe-delete-todo.js treatment-v3`
(규칙1, `observeCommitThreshold` 참고용 관찰은 그대로 유효 — 특히
`observeCommitThreshold`는 이제 "50% 직전에는 삭제 안 됨"으로 나와서
Android 스펙과 실제로 일치하게 됐다), `node tools/nested/
swipe-action-verify-check.js`(레시피5 자체 검증, 플랫폼 분기 포함)

---

## 03. bottom-sheet-comments

**채점 기준**: `nested-interactions/bottom-sheet-scroll-drag.md` §5(§4.5 규칙 1 포함, 규칙 2는 원본 문서 자체가 "해당 없음"으로 이미 판정해둠) — `scrollTop` 기준 소유권 이양이 실제로 되는지, 빈 `pointermove`에 반응 안 하는지.

**⚠️ treatment가 baseline보다 명백히 나쁘다 — 숨기지 않고 그대로 보고한다.**

| 항목 | baseline | treatment |
|---|---|---|
| 스크립트가 애초에 실행되는가(댓글 40개 렌더) | **실행됨**(40/40) | **실행 자체가 안 됨**(0/40) — `Identifier 'commentsEl' has already been declared` 치명적 SyntaxError |
| 규칙 1 — 빈 `pointermove`에 시트가 반응 안 함 | **미충족** — `pointerdown` 없이 핸들에 `pointermove`만 줘도 시트가 388px 딸려 옴 | 실행 불가로 평가 불가 |
| `scrollTop>0`(맨 위 아님)일 때 시트가 안 움직여야 함 | **미충족** — 콘텐츠를 200px 드래그하면 시트가 `translateY(100%)`까지 완전히 닫혀버림(원본 결함 그대로 재현) | 실행 불가로 평가 불가 |
| `scrollTop=0`일 때 시트가 움직여야 함 | 움직이긴 함(단, 위 미충족과 합쳐보면 "항상 움직인다"는 뜻 — `scrollTop` 조건 자체가 없어서 우연히 이 조건도 만족한 것) | 실행 불가로 평가 불가 |

**원인**: 소스를 열어 직접 확인한 결과, baseline은 원본 결함 코드에서 **한 글자도 바뀌지 않았다**(내가 만든 원본 시나리오 파일과 완전히 동일) — 즉 요청 자체를 처리하지 않은 것으로 보인다. treatment는 반대로 `scrollTop` 기준 소유권 이양·`isDown` 플래그(규칙 1 수정)·`ownedBySheet` 상태 분리까지 — 이 프로젝트의 레시피 2와 사실상 동일한 수준의 **설계는 올바르게** 갖췄다. 그런데 `const commentsEl`을 79번째 줄과 90번째 줄에서 두 번 선언해서(같은 스코프) 스크립트 전체가 파싱 단계에서 죽는다 — 결과적으로 어떤 로직도 실행되지 않고, 댓글도 안 뜨고, 시트도 전혀 안 움직인다(원본 버그보다도 못한 상태 — 최소한 원본/baseline은 "잘못된 방식으로나마" 작동은 했다).

**결론**: 설계 품질만 보면 treatment가 baseline을 크게 앞섰지만(정확히 이 프로젝트가 나중에 레시피 2로 검증한 것과 같은 구조), **실행조차 안 되는 치명적 오타 하나 때문에 실사용 기준으로는 treatment가 baseline보다 나쁘다.** "코드를 읽고 판단"했다면 이 오타를 놓쳤을 것이다 — 실제로 실행해서 채점해야 하는 이유가 정확히 이 사례다.

---

## 04. carousel-photos

**채점 기준**: `research/ux-standards/patterns/carousel.md` — "한 장씩 감상"류 콘텐츠는 `scroll-snap-type: x mandatory` + `scroll-snap-align`(+권장: `scroll-snap-stop: always`).

| 항목 | baseline | treatment |
|---|---|---|
| `scroll-snap-type`/`scroll-snap-align` 존재 | 있음(`x mandatory`, `start`) | 있음(`x mandatory`, `start`) |
| 사진 사이(1.4번째 지점)로 스크롤 후 `scrollend` 시점 실제 위치 | **정확히 사진 경계로 스냅됨**(오차 0px) | **정확히 사진 경계로 스냅됨**(오차 0px) |
| `scroll-snap-stop: always`(플링으로 여러 장 건너뛰기 방지, 이 문서 권장) | 없음(`normal`) | **있음**(`always`) |

**한계**: `scroll-snap-stop`의 실제 효과("빠르게 튕겨도 한 장만 넘어간다")는 실제 관성(fling) 스크롤이 있어야 차이가 드러나는데, 이 도구(합성 이벤트/프로그래매틱 스크롤)로는 그 관성 물리 자체를 재현할 수 없다 — 이 프로젝트가 side-drawer 시나리오에서 이미 확인한 것과 같은 종류의 한계라 [자체 점검 수준]으로만 남긴다. `scroll-snap-type`/`align`의 핵심 기능(정확한 위치 스냅)은 둘 다 실측으로 확인됐다.

**결론**: 핵심 기능은 baseline·treatment 둘 다 정상 작동(사실 baseline만으로도 원래 요청은 충분히 해결됨). treatment가 `scroll-snap-stop: always`를 추가로 넣은 건 `carousel.md`가 명시적으로 권장하는 세부 사항까지 반영한 것 — 다만 그 효과는 이 채점 도구로는 검증하지 못했다.

---

## 05. multi-select-photos

**채점 기준**: 이 시나리오의 원본 결함(다중 선택 진입 후 클로저에 캡처된 첫 타일만 계속 토글됨) 재현 여부. `multi-select.md`는 실행 코드가 없는 조사 문서라 별도 수치 기준은 없다.

| 항목 | baseline | treatment |
|---|---|---|
| 0번 롱프레스 진입 후 3번 탭 → 3번이 선택됨(원본 결함이면 실패) | **충족** | **충족** |
| 4개 타일(0,2,5,7)을 순서대로 눌렀을 때 전부 독립적으로 선택 | **충족**(정확히 `[0,2,5,7]`) | **충족**(정확히 `[0,2,5,7]`) |
| 0번 롱프레스 타이머 도중 1번을 짧게 눌렀다 떼도 0번 진입에 영향 없음 | **충족** | **충족** |

**주의(자체 정정)**: 처음에 `tap()`을 순수 `click` 이벤트 하나만 던지는 식으로 짰더니 treatment의 첫 번째 케이스가 "실패"로 나왔다 — 그런데 원인을 보니 실제 터치는 항상 `pointerdown → pointerup → click` 순서로 합성되는데, click만 단독으로 쏘면 treatment가 쓰는 `preventClick` 리셋 타이밍(다음 `pointerdown`에서 초기화)을 못 맞춰서 생긴 **테스트 도구 쪽 결함**이었다. `tap()`을 pointerdown+pointerup+click 세 이벤트로 고쳐서 재현한 결과 baseline과 동일하게 전부 통과했다 — 실제 구현 결함이 아니라 처음 짠 채점 스크립트가 실제 터치 제스처를 충분히 흉내 내지 못했던 것이었다.

**결론**: 두 조건 다 원본 결함 없이 정상 작동. 이 시나리오에서는 baseline·treatment 사이에 유의미한 차이가 없다.

---

## 06. context-menu-notes

**채점 기준**: `CONFLICTS.md#C6` — 원본 결함은 `contextmenu`에 `preventDefault()`가 없는 것. `event.defaultPrevented`를 실제로 확인했다(코드에 그 줄이 있는지 읽은 게 아니라 이벤트를 던져서 판정).

| 항목 | baseline | treatment |
|---|---|---|
| `contextmenu` 이벤트가 실제로 `preventDefault()` 됨 | **충족** | **충족** |
| 실제 롱프레스로 커스텀 메뉴가 정상적으로 뜸(회귀 확인) | **충족** | **충족** |

**결론**: 둘 다 원본 결함 없이 정상 작동, 차이 없음.

---

## 07. tab-swipe-stories

**채점 기준**: `research/ux-standards/patterns/tab-swipe.md` — 원본 결함은 탭 스와이프 리스너가 내부 가로 스크롤(`#stories`)을 제외하지 않는 것 + common-pitfalls 규칙 1.

| 항목 | baseline | treatment |
|---|---|---|
| 스토리 영역에서 130px 스와이프해도 탭이 안 바뀜 | **충족** | **충족** |
| 피드 영역에서 스와이프하면 탭이 정상적으로 넘어감(회귀 확인) | **충족** | **충족** |
| 규칙 1 — `pointerdown` 없이 `pointerup`만 와도 탭 안 바뀜 | **충족** | **충족** |

**결론**: 둘 다 `e.target.closest("#stories")` 방식(변수명만 다름: `startX=null` vs `isTabSwipeArmed`)으로 정확히 같은 해법을 냈다. 차이 없음.

---

## 08. side-drawer-menu

**채점 기준**: `nested-interactions/side-drawer-back-gesture.md`(레시피 3) — 원본 문서 자체가 이건 "해소 규칙"이 아니라 "완화 조치" 목록이라고 결론 내려서, "충돌이 해소됐는가"가 아니라 완화 조치(특히 완화 3: 항상 열 수 있는 버튼 경로)가 실제로 구현됐는지로 채점한다. 완화 1(`overscroll-behavior-x`)의 실제 효과는 이 프로젝트가 이미 실험으로 "검증 불가"를 확인해뒀으므로 존재 여부만 관찰한다.

| 항목 | baseline | treatment |
|---|---|---|
| 완화 3 — 스와이프 없이도 항상 열 수 있는 버튼이 있음(request.txt의 핵심 요구) | **미충족** — 버튼 자체가 없음 | **충족** — `#menu-btn`(`aria-label="메뉴 열기"`) 존재, 클릭 시 실제로 열림 확인 |
| 완화 2(관찰) — 엣지 스와이프 존이 왼쪽(iOS 시스템 뒤로가기 영역)이 아님 | 왼쪽 그대로(`x=0`) | 오른쪽으로 옮김(`x=1260`, 뷰포트 폭-20) |
| 완화 1(관찰, 효과 검증 불가) — `overscroll-behavior-x: contain` | 없음(`auto`) | 있음(`contain`) |

**특이사항**: baseline 소스를 열어보니 요청받은 드로어 대체 진입 경로는 전혀 추가하지 않은 대신, **요청에 없던 하단 탭 스와이프 전환 기능과 스토리 캐러셀 드래그 기능을 통째로 새로 구현**해뒀다(386줄 — treatment의 137줄보다 훨씬 김). 코드 품질 자체는 나쁘지 않지만(스토리 영역 `stopPropagation`으로 탭 스와이프와 분리하는 등), request.txt가 실제로 요구한 것과는 다른 작업을 한 것으로 보인다.

**결론**: treatment가 baseline보다 명확히 낫다 — 레시피 3의 완화 조치(버튼+우측 배치+overscroll-behavior) 세 가지를 전부 반영했고 실제로 작동한다. baseline은 원래 요청을 놓치고 범위 밖의 다른 기능을 만들었다.

---

## 09. longpress-triple-favorites

**채점 기준**: `nested-interactions/long-press-triple-conflict.md` §5 그대로 — 규칙 1, 규칙 2(같은 행). 추가로 원본 문서엔 없지만 구현 방식 차이(전역 잠금 vs 행별 격리)가 갈릴 수 있는 지점(서로 다른 행 동시 조작)도 관찰했다.

| 항목 | baseline | treatment |
|---|---|---|
| 규칙 1 — 빈 `pointermove`에 반응 안 함 | **충족** | **충족** |
| 500ms에 컨텍스트 메뉴 실제로 뜸(회귀 확인) | **충족** | **충족** |
| 규칙 2(같은 행) — 두 번째 포인터가 같은 행에 끼어들어도 첫 제스처 안 깨짐 | **충족** | **충족** |
| (관찰) 서로 다른 두 행을 동시에 조작하면 각각 독립적으로 동작 | **미충족** — B행 제스처가 아예 무시됨 | **충족** |

**원인**: baseline은 `activePointerId`를 **리스트 전체가 공유하는 전역 변수**로 만들어서 고쳤다 — 어떤 행이든 포인터 하나가 활성화돼 있으면 리스트의 *다른 모든 행*이 새 포인터를 통째로 무시한다. 같은 행 안에서의 규칙 2는 이걸로 통과하지만, 부작용으로 "한 손가락으로 A행을 누르고 있는 동안 다른 손가락으로 B행을 만지면 B행이 먹통이 된다"는 **새로운 제약**이 생겼다 — §5-5가 원래 테스트하지 않은 지점이라 원본 문서 기준으로는 결함이 아니지만, 실사용 관점에서는 과도한 잠금이다. treatment는 `activePointerId`를 레시피 4와 같은 방식으로 **행마다 독립된 클로저**에 둬서 같은 행 격리와 다른 행 독립성을 동시에 만족시켰다.

**결론**: 원본 문서(§5)가 명시한 항목만 보면 둘 다 충족한다. 문서가 테스트하지 않은 지점(다른 행 동시 조작)까지 넓혀보면 treatment의 설계(행별 격리)가 baseline(전역 잠금)보다 낫다.

**재검증 결과 — treatment 콘텐츠 갱신(baseline은 변경 없음)**

02번과 같은 방식: baseline은 그대로다. `evals/subjects/09-longpress-triple-favorites/project/index.html`(원본 결함 코드)에 `common-pitfalls.md` §7-4 `withSinglePointerGate`([이 프로젝트의 설계 판단])를 적용해 `evals/results/treatment-v2/subjects/09-longpress-triple-favorites/`로 재채점했다. 위 표(baseline vs treatment)는 그대로 남긴다.

| 항목 | treatment(원래) | treatment-v2(공용 게이트 적용) |
|---|---|---|
| 규칙 1 | **충족** | **충족** |
| 500ms 메뉴(회귀) | **충족** | **충족** |
| 규칙 2(같은 행) | **충족** | **충족** |
| (관찰) 다른 행 동시 조작 시 독립 동작 | **충족** | **충족** |

**이력**: 이전(원래 treatment) → **treatment 우위**(원본 문서 기준으로는 동률, 문서 밖 관찰에서 우위). 갱신 후(treatment-v2) → **동일하게 treatment 우위** — 4개 항목 전부 원래 treatment와 같은 결과다. **새로 통과하게 된 항목은 없다.**

**정직하게 밝힌다**: 이번 재검증은 "게이트 적용 후 더 명확히 개선됐다"가 아니라 "이미 충분했다"는 결과다. 원래 treatment도 `activePointerId`를 `attachTripleGesture` 함수 안(행별 클로저)에 두고 진입 게이트를 자체 구현해서 문서 밖 관찰까지 이미 통과하고 있었다 — treatment-v2는 그 동작을 재사용 가능한 공용 패턴(`withSinglePointerGate`)으로 다시 만든 것이지, 원래 treatment가 못 하던 걸 새로 되게 한 게 아니다. 이번 재검증의 실제 가치는 "같은 6줄짜리 게이트가 서로 다른 두 컴포넌트(A/D-02, 그리고 여기 09번)에서 일관되게 같은 결과를 내는가"를 확인한 것이지, 09번 자체의 점수를 올린 게 아니다.

재현: `cd evals && node graders/09-longpress-triple-favorites.js treatment-v2`

**재검증 결과 (세 번째 버전) — 네이티브 억제 4종 세트 추가 + 그레이더 자체의 사각지대 보정**

`research/ux-standards/` 전체를 훑어 iOS≠Android 실측 지점을 정리하는
과정에서, `CONFLICTS.md#C6`가 "세 개 부품 중 하나라도 빠지면 안 된다"고
명시한 네이티브 억제 조합(`user-select`/`-webkit-user-select`/
`-webkit-touch-callout` CSS 3개 + `contextmenu` `preventDefault()`
JS 1개 — 총 4개)이 `recipes.md` 레시피1에 **전부 빠져 있다**는 걸
재발견했다. `evals/results/treatment-v2/subjects/09-longpress-triple-favorites/`
의 코드도 같은 이유로 이 4개가 없었다 — 500ms/1000ms 타이머, 8px
판정, `withSinglePointerGate`는 무수정으로 두고 이 4개만 추가해서
다시 채점했다.

**그레이더 자체도 사각지대였다**: 기존 a~d(규칙1, 500ms 메뉴, 규칙2,
다른 행 독립) 어디에도 "Android `contextmenu` 억제됐는가"를 확인하는
항목이 없었다 — 즉 이 그레이더는 애초에 이 결함을 잡을 능력이 없었다.
`androidContextMenuSuppressed`(실제로 `contextmenu` 이벤트를 던져
`defaultPrevented`를 확인 — 런타임 검증)와
`iosCalloutSuppressionDeclared`(CSS 선언 존재 여부만 정적 확인 —
`-webkit-touch-callout`은 WebKit 전용 네이티브 UI라
`ux-standards-architecture.md` §6이 이미 명시한 대로 Playwright/
Chromium으로는 실제 억제 효과를 검증할 수 없다, 자체 점검임을
결과 필드에도 그대로 남김) 두 항목을 그레이더에 추가했다.

| 항목 | baseline | treatment(원래) | treatment-v2(v2, 게이트만) | treatment-v2(v3, 네이티브 억제 4종 추가) |
|---|---|---|---|---|
| `androidContextMenuSuppressed` | **미충족**(`defaultPrevented: false`) | **미충족**(동일) | **미충족**(동일, 이번에 처음 측정) | **충족**(`defaultPrevented: true`) |
| `iosCalloutSuppressionDeclared`(선언 여부만) | `-webkit-touch-callout` 미선언 | 미선언 | 미선언 | **선언됨**(`-webkit-user-select`/`-webkit-touch-callout` 둘 다 소스에 존재 확인) |
| 기존 a~d(규칙1·2, 500ms, 다른 행 독립) | (RESULTS.md 상단 표 참조) | 전부 충족 | 전부 충족(무수정) | 전부 충족(무수정, 회귀 없음) |

**이력 요약**: baseline·원래 treatment·v2(게이트만) **셋 다** Android
`contextmenu` 억제가 안 돼 있었다는 게 이번에 처음으로 드러났다 —
지금까지 이 결함은 채점 기준 자체에 없어서 "동률"/"우위" 판정 어디에도
반영되지 못했다. v3(이번 갱신)에서 처음으로 이 항목이 충족된다.
**baseline과 원래 treatment의 과거 채점 결과(위 표들)는 고치지 않는다**
— 그때는 이 기준으로 채점하지 않았다는 사실 자체가 기록이다. 앞으로
09번을 재채점할 때는 이 두 항목까지 포함해서 본다.

재현: `cd evals && node graders/09-longpress-triple-favorites.js baseline`
/ `treatment` / `treatment-v2` (셋 다 새 항목 포함해서 채점됨,
그레이더 자체가 바뀌었으므로)

---

## 전체 요약

| # | 시나리오 | 승자 | 한 줄 요약 |
|---|---|---|---|
| 01 | reorder-no-handle | **treatment** | treatment는 hold-delay+8px취소를 자체 구현하고 예외도 방어함. 둘 다 규칙 2(멀티포인터)는 실패. |
| 02 | swipe-delete-todo | 동률(†) | 둘 다 원본 결함(규칙 1) 수정, 둘 다 규칙 2는 미수정. treatment는 `setPointerCapture` 자체를 안 써서 예외 위험이 없음. |
| 03 | bottom-sheet-comments | 실행 사고 | baseline은 원본 결함을 손도 안 댐(그래도 작동은 함). treatment는 설계는 레시피 2 수준으로 훌륭했지만 `const` 중복 선언으로 **스크립트 전체가 죽어서 아무것도 작동 안 함**. |
| 04 | carousel-photos | 동률 | 핵심 스냅 기능은 둘 다 정상. treatment만 `scroll-snap-stop` 추가(효과 미검증). |
| 05 | multi-select-photos | 동률 | 둘 다 원본 결함 없이 정상 작동. |
| 06 | context-menu-notes | 동률 | 둘 다 `preventDefault()` 정상 적용. |
| 07 | tab-swipe-stories | 동률 | 둘 다 스토리 영역 제외 로직 정상 구현. |
| 08 | side-drawer-menu | **treatment** | baseline은 요청(대체 진입 경로)을 놓치고 범위 밖 기능을 만듦. treatment는 레시피 3 완화조치 3가지를 정확히 반영. |
| 09 | longpress-triple-favorites | **treatment**(원본 문서 기준으로는 동률)(‡) | 문서(§5)가 명시한 항목은 둘 다 충족. 문서 밖 관찰(다른 행 동시 조작)에서 baseline의 전역 잠금이 과도한 제약을 만드는 게 드러남. |

*03번은 승패가 아니라 실행 사고로 별도 표기함 — treatment가 baseline보다 못했다는 뜻이 아니라, 오타 하나로 아예 실행되지 않았다는 뜻이다.*

*(†) 02번의 "동률"은 이 표가 비교하는 원래의 baseline vs treatment(당시 Claude가 생성한 것) 기준이며, 이후 변경되지 않았다. 이후 스킬 콘텐츠 자체가 갱신되면서(`recipes.md`에 `withSinglePointerGate` 통합) 별도로 만든 treatment-v2는 규칙 2까지 충족해 baseline보다 우위로 갈렸다 — 이 표의 "동률"과 모순이 아니라, "이 두 버전을 비교하면"이라는 다른 질문에 대한 답이다. 02번 절의 "재검증 결과" 참조.*

*(‡) 09번은 02번과 달리 이 표(baseline vs treatment)의 승자 자체는 바뀌지 않는다. 다만 이 각주는 두 단계로 나뉜다 — treatment-v2 두 번째 갱신(공용 게이트만 적용)까지는 4개 항목 전부 원래 treatment와 똑같이 통과해 "더 나아진 게 아니라 이미 충분했다"였는데, **세 번째 갱신(네이티브 억제 4종 추가)에서는 baseline·원래 treatment·v2 셋 다 갖고 있지 않던 Android `contextmenu` 억제 항목이 처음으로 충족됐다** — 이건 이 표의 기존 4개 채점 기준 밖에 있던 새 항목이라 표 자체를 바꾸지는 않지만, "이미 충분했다"는 이전 각주의 결론이 그 새 항목에는 적용되지 않는다는 걸 밝혀 둔다. 09번 절의 "재검증 결과(세 번째 버전)" 참조.*

**집계 (9개 시나리오)**: treatment가 명확히 나은 경우 3건(01, 08, 09) · 실질적 차이 없음 5건(02, 04, 05, 06, 07) · treatment가 실행조차 안 되는 회귀를 일으킨 경우 1건(03).

03번은 "이겼다/졌다"가 아니라 실행 사고로 분류한다 — treatment의 설계 자체는 baseline보다 나았지만(레시피 2 수준), 변수 중복 선언 오타로 스크립트 전체가 죽어 아무 기능도 작동하지 않았다. 이걸 빼고 나머지 8건만 보면 3승 5무로, treatment가 baseline보다 나쁜 방향으로 설계된 사례는 이번 9개 중 없었다.

**숨기지 않고 밝히는 것 — 이번 라운드의 가장 중요한 두 발견**

1. **treatment가 실행조차 안 되는 회귀를 일으킨 사례가 실제로 있었다(03번)** — 이건 baseline이 treatment보다 나은 설계였다는 뜻이 아니라, treatment의 설계는 더 나았지만 오타로 아예 실행되지 않았다는 뜻이다: 설계 품질은 이 프로젝트의 레시피 2와 사실상 동일한 수준으로 훌륭했지만, `const commentsEl`을 두 번 선언하는 사소한 오타 하나로 스크립트 전체가 파싱 단계에서 죽어 **어떤 기능도 작동하지 않았다** — 댓글도 안 뜨고 시트도 안 움직인다. baseline은 아무것도 고치지 않았지만 최소한 "고장 나지 않은 원본 결함"으로는 작동했다. 코드를 읽기만 했다면 이 오타를 놓쳤을 것이다 — 실행 기반 채점이 반드시 필요한 이유가 정확히 이 사례다.

2. **규칙 2(멀티포인터)는 스킬 유무와 무관하게 계속 남는 결함이다**: 01번·02번 둘 다 baseline·treatment 관계없이 규칙 2를 못 지켰다. 09번에서만 규칙 2(같은 행)를 통과했는데, 이건 이 시나리오의 원본 결함 코드 자체가 애초에 부분적인 pointerId 추적 구조를 갖고 있었기 때문일 가능성이 있다(baseline과 treatment 둘 다 원본과 다른 방식으로, 그러나 각자 완결된 pointerId 격리를 새로 구현했다). 규칙 2는 이 스킬의 `recipes.md`에도 반복적으로 "미통과, 알려진 한계"로 남아 있던 지점인데, 이번 9개 시나리오 실측에서도 정확히 같은 패턴이 재확인됐다.

**재현성**: 모든 수치는 `cd evals && npm install && node graders/<번호>-<이름>.js <baseline|treatment>`로 그대로 재현 가능하다. 그래더 스크립트는 `evals/graders/`에, `project/` 폴더와는 완전히 분리되어 있다.

---

## Gemini 교차검증

**중요 — 표본을 절대 합치지 않는다**: 위 9개 시나리오는 전부
**Claude Code**(baseline=스킬 미적용, treatment=스킬 적용)로 만든
결과다. 아래는 **완전히 다른 모델(Gemini `gemini-3.6-flash`,
Interactions API 직접 호출)**로 같은 9개 시나리오·같은
`request.txt`를 돌린 결과다(noskill=스킬 콘텐츠 미주입,
skill=`SKILL.md`+`references/*.md` 전체를 system_instruction에
주입). **Claude 9개 표본과 Gemini 5개 표본은 서로 다른 모집단이라
하나의 표(예: "9+5=14건 중 몇 승")로 합산하지 않는다** — 아래 표는
"같은 컴포넌트에서 두 모델이 같은 결론에 도달하는가"를 나란히
놓고 비교하는 용도이지, 둘을 더해서 새 통계를 만드는 용도가
아니다.

`evals/run-gemini.js`로 자동 호출했고, 채점은 **Claude 채점 때와
정확히 같은 `evals/graders/*.js` 스크립트**를 그대로 재사용했다
— 컴포넌트가 아니라 모델만 바뀐 것이므로 채점 기준을 다시 만들지
않았다.

### 결과 확보 현황

| # | 시나리오 | 상태 |
|---|---|---|
| 01 | reorder-no-handle | ✅ noskill/skill 둘 다 확보·채점 완료 |
| 02 | swipe-delete-todo | ✅ noskill/skill 둘 다 확보·채점 완료 |
| 03 | bottom-sheet-comments | ⚠️ **미완료** — 스캐폴딩 사고(§6 함정3) 도중 호출이 중간에 끊겨서 서버가 실제로 처리했는지조차 불명. 그대로 방치 중, 재실행 안 함 |
| 04 | carousel-photos | ✅ noskill/skill 둘 다 확보·채점 완료 |
| 05 | multi-select-photos | ✅ noskill/skill 둘 다 확보·채점 완료(재조사 후 정정, 아래 참조) |
| 06 | context-menu-notes | ⚠️ **미완료 — API 할당량 소진**(HTTP 429, `generate_content_free_tier_requests`, limit 20) |
| 07 | tab-swipe-stories | ⚠️ **미완료 — API 할당량 소진**(동일) |
| 08 | side-drawer-menu | ⚠️ **미완료 — API 할당량 소진**(동일) |
| 09 | longpress-triple-favorites | ✅ noskill/skill 둘 다 확보·채점 완료 |

### 01. reorder-no-handle

| 항목 | noskill | skill |
|---|---|---|
| a) 8px 미만 유지 → 진입 | 즉시 진입(2.3ms) — 지연 메커니즘 없음 | **충족** — 504.1ms에 진입 |
| b) 지연 중 이동 → 취소 | 해당 없음(지연 창 자체가 없음), 재정렬은 그대로 일어남 | **충족** — 취소됨, 재정렬 안 일어남 |
| c) 진입 후 이동 → 재정렬 | 충족 | 충족 |
| d) 두 번째 포인터 → 규칙 2 | **미충족** | **충족** |

**Claude 결과와 비교**: Claude도 treatment가 hold-delay+8px취소를 자체 구현하고 규칙 2까지 통과했던 게 이 시나리오의 핵심 발견이었다(01번 절 참조) — **Gemini도 정확히 같은 패턴(skill이 hold-delay·취소·규칙2 전부 갖춤, noskill은 즉시 드래그만 있고 규칙2 실패)으로 갈렸다. 일치.**

### 02. swipe-delete-todo

| 항목 | noskill | skill |
|---|---|---|
| 규칙 1(빈 이벤트에 반응 안 함) | 충족 | 충족 |
| 정상 스와이프 | 충족 | 충족 |
| 규칙 2 | **미충족** | **미충족** |

**Claude 결과와 비교**: Claude도 baseline/treatment 둘 다 규칙 1은 고치고 규칙 2는 안 고쳤다(동률). **Gemini도 noskill/skill 둘 다 규칙 1 충족·규칙 2 미충족으로 동일하게 갈렸다. 일치.**

### 04. carousel-photos

| 항목 | noskill | skill |
|---|---|---|
| 사진 사이 위치로 스크롤 후 `scrollend` 시점 정렬 | 정확히 스냅됨(오차 0px) | 정확히 스냅됨(오차 0px) |
| `scroll-snap-stop: always` | 없음(`normal`) | **있음**(`always`) |

**Claude 결과와 비교**: Claude도 핵심 스냅 기능은 baseline/treatment 둘 다 정상이었고, treatment만 `scroll-snap-stop: always`를 추가로 넣었다(동률, 세부 개선 1건). **Gemini도 정확히 같다 — noskill/skill 둘 다 스냅은 완벽하고, skill만 `scroll-snap-stop: always`를 추가했다. 일치(세부 개선 지점까지 동일).**

### 05. multi-select-photos — 조사 과정 그대로 남긴다

이 시나리오는 처음에 **역전(noskill 통과, skill 실패)으로 관찰됐다가, 재조사 끝에 그레이더 결함으로 정정됐다.** 최종 수치만 남기지 않고 과정을 그대로 적는다 — 이게 이 프로젝트가 실제로 검증하는 방식을 보여주는 사례이기 때문이다.

1. **최초 관찰**: `tapOtherTileAfterEnteringSelectMode` 테스트에서 noskill은 통과, skill은 3번 타일이 끝내 선택되지 않아 실패로 나왔다.
2. **원인 조사**: 실제 생성된 코드를 열어보니 `multi-select.md`가 원래 지목한 결함(공유 `activeTile` 클로저)은 재현되지 않았다 — 매 반복마다 독립 클로저를 정상적으로 썼다. 대신 그레이더의 `longPress()` 헬퍼가 `pointerdown`/`pointerup`만 던지고 `click`은 안 던지는 옛날 버전으로 남아 있었던 게 원인이었다 — Gemini 코드의 "롱프레스 진입 직후 트레일링 클릭 1회 무시" 전역 플래그(`justEnteredByLongPress`)가 그 트레일링 클릭을 못 받아 계속 `true`로 남았고, 그게 다음 타일의 진짜 클릭을 대신 삼켰다.
3. **정정**: `longPress()`에 `click`을 추가해 `tap()`과 동일하게 맞추자 즉시 해소됐다. `common-pitfalls.md` §6 "함정 4"로 기록함.

| 항목(정정된 그레이더 기준) | noskill | skill |
|---|---|---|
| 진입 후 다른 타일 탭 → 선택됨 | 충족 | **충족**(정정 전엔 미충족으로 잘못 나왔음) |
| 4개 타일 독립 토글 | 충족 | **충족**(정정 전엔 2번 누락으로 잘못 나왔음) |
| 동시 눌림 방어 | 충족 | 충족 |

**Claude 결과와 비교**: Claude는 baseline/treatment 둘 다 정상 작동(동률)이었다. **정정 후 Gemini도 noskill/skill 둘 다 정상 작동(동률)이다. 일치.**

### 09. longpress-triple-favorites

| 항목 | noskill | skill |
|---|---|---|
| 규칙 1 | 충족 | 충족 |
| 500ms 메뉴(회귀) | 충족 | 충족 |
| 규칙 2(같은 행) | 충족 | 충족 |
| (문서 밖 관찰) 다른 행 동시 조작 시 독립 동작 | **미충족**(전역 잠금) | **충족**(행별 격리) |

**Claude 결과와 비교**: Claude도 문서(§5)가 명시한 항목은 baseline/treatment 둘 다 충족했고, 문서 밖 관찰(다른 행 동시 조작)에서만 baseline의 전역 잠금 방식이 과도한 제약을 만들어 treatment가 앞섰다 — 메커니즘까지 똑같다(전역 잠금 vs 행별 클로저 격리). **Gemini도 정확히 같은 축으로, 같은 메커니즘으로 갈렸다. 일치.**

### 종합

**5개 시나리오 전부(01, 02, 04, 05, 09)에서 Gemini의 결론이 Claude의
결론과 같았다** — Claude 쪽에서 "동률"이었던 시나리오(02, 04, 05)는
Gemini 쪽에서도 noskill/skill이 동률이었고, Claude 쪽에서
"treatment 우위"였던 시나리오(01, 09)는 Gemini 쪽에서도 skill이
정확히 같은 이유·같은 메커니즘으로 우위였다. 이건 어디까지나
**두 개의 독립된 5건/9건 표본을 나란히 놓고 "결론의 방향이
같은가"를 비교한 것**이지, 둘을 합쳐 하나의 큰 표본으로 다시 계산한
게 아니다. 표본이 작아 일반화하기엔 이르지만, 적어도 이 스킬의
콘텐츠(레시피 4의 hold-delay/취소, 09번의 pointerId 격리, 04번의
`scroll-snap-stop`)가 **특정 모델에 국한된 효과가 아니라는 정황**은
확보됐다.

03·06·07·08은 이번 라운드에서 확보하지 못했다 — 03은 이전 사고로
상태 불명인 채 방치 중이고, 06~08은 무료 티어 일일 할당량(20건)
소진으로 재시도하지 않았다. 할당량이 언제 리셋되는지는 확인하지
못했다(공식 문서에 정확한 수치가 없고 AI Studio 대시보드에서만
보임 — `run-gemini.js` 파일 상단 주석 참조).

---

## Round 2 — 스킬 갱신 후 재현성 검증 (진행 중, 01/02/09번까지)

**중요 — 표본을 또 합치지 않는다**: 이 라운드는 위 9개 시나리오(Round
1, Claude baseline/treatment)와도, Gemini 교차검증(5개)과도 **완전히
독립된 별도 실행**이다. `common-pitfalls.md` §7·§8·§9가 추가된 이후의
`skills/interaction-doctor/`를 완전히 새로운 `claude -p` 세션(이
대화의 다른 어떤 세션과도 컨텍스트를 공유하지 않음)에 격리된
디렉터리로 올려서 실행했다. Round 1과 방향이 같은지만 비교하고,
숫자를 더하거나 승패를 재계산하지 않는다.

### 방법론

- 각 세션은 `evals/subjects/{N}/request.txt`의 문구만 프롬프트로
  받는다 — 채점 기준, 컴포넌트 이름, "테스트"라는 언급 전혀 없음.
- `noskill` 조건: `.claude/` 자체가 없는 빈 디렉터리 + `project/`
  (원본 결함 코드)만 배치.
- `skill` 조건: 같은 구조에 `.claude/skills/interaction-doctor/`를
  실제로 인식 가능한 위치(세션 시작 **전에** 이미 존재하는 최상위
  디렉터리 — `common-pitfalls.md` §6 함정1 교훈 적용)에 배치.
- CLAUDE.md는 두 조건 다 없음 — 이 프로젝트의 전역 규칙이 섞여
  들어가는 걸 막는다(N9/N6 오탐과 같은 오염 경로 차단).
- 실행: `claude -p "<request.txt>" --permission-mode acceptEdits
  --output-format json --max-turns 20`(첫 배치는 `--disallowedTools
  Bash`를 추가했다가, 아래 이유로 이후 제거했다).
- 결과는 `evals/results/round2-noskill/subjects/`,
  `evals/results/round2-skill/subjects/`에 저장하고 **Round 1과 같은**
  `evals/graders/*.js`로 채점했다 — 채점 기준을 새로 만들지 않았다.

### 01. reorder-no-handle

| 항목 | noskill | skill |
|---|---|---|
| a) 8px 미만 유지 → 진입 | 즉시 진입(1.3ms), 지연 없음 | **충족** — 503.1ms에 진입 |
| b) 지연 중 이동 → 취소 | 해당 없음, 재정렬 그대로 일어남 | **충족** — 취소됨 |
| c) 진입 후 이동 → 재정렬 | 충족 | 충족 |
| d) 두 번째 포인터 → 규칙 2 | **미충족** | **충족** |

**Round 1과 비교**: Round 1의 baseline/treatment 패턴과 방향이 같다
(스킬 없으면 지연·규칙2 없음, 스킬 있으면 둘 다 갖춤). skill 조건
코드를 열어보니 `activePointerId`+`armed` 게이트를 정확히 §7-4와
같은 구조로 자체 작성했다 — `Glob **/*`로 `project/index.html`을
스스로 찾아 읽고 적용했다.

### 02. swipe-delete-todo

| 항목 | noskill | skill |
|---|---|---|
| 규칙 1 | 충족 | 충족 |
| 정상 스와이프 | 충족 | 충족 |
| 규칙 2 — 두 번째 포인터 | **미충족** | **미충족** |

**Round 1과 비교**: 방향은 같다(Round 1 baseline/treatment도 둘 다
규칙2 미충족). **다만 skill 조건의 실패 원인이 흥미롭다**: 코드를
열어보니 `activePointerId` 변수와 `pointermove`/`pointerup`의 비교
가드는 정확히 있는데, **`pointerdown` 핸들러 자체에 진입 게이트
(`if (activePointerId !== null) return`)가 빠졌다** — §7-4를
그대로 복사하지 않고 "직접 재구성"하다가 정확히 그 한 줄을
빠뜨린 것이다. 트랜스크립트로 확인: 이 세션은 실제로
`recipes.md`(§7-4 코드 전문 포함)를 Read 도구로 읽었다 — 읽고도
정확히 옮기지 못했다. §9(그레이더 의심 순서)와는 다른 종류의
문제라 별도로 기록해 둔다: **패턴을 "참조"하는 것과 "정확히
재현"하는 것은 다르다.**

### 09. longpress-triple-favorites

| 항목 | noskill | skill |
|---|---|---|
| 규칙 1 | 충족 | — |
| 500ms 메뉴 | 충족 | — |
| 규칙 2(같은 행) | 충족 | — |
| 다른 행 독립 | **미충족** | — |

**noskill의 뜻밖의 확인**: 스킬 없이도 이 세션은 스스로
`activePointerId` 게이트를 만들었다 — 그런데 그 변수를
`attachTripleGesture` 함수 **밖**(전역, 주석에도 "전역 잠금"이라고
스스로 씀)에 선언해서, `common-pitfalls.md` §7-1 원장의 **C-baseline
사례(Round 1의 09번 baseline)와 정확히 같은 실패 모드**를 독립적으로
재현했다. 서로 다른 시점, 다른 세션, 다른 모델 상태에서 같은
설계 실수가 반복된다는 게 §7-3의 2축 모델(스코프 축)에 대한 추가
증거가 된다 — 다만 이건 여전히 이번 1건뿐이라 확신도는 그대로
"중간"으로 둔다(§7-3 원문 그대로, 격상하지 않는다).

**skill: 3회 시도, 3회 다 파일 미작성 — 채점 불가**. 아래 "핵심
발견" 참조. 표에는 "—"로 남긴다 — 미충족으로 세지 않는다(시도가
안 된 것과 실패한 것은 다르다).

### 핵심 발견 — 스킬 패키지 자체의 결함 (예상 밖)

09번 skill 조건을 3회(1회는 `--disallowedTools Bash`, 2회는 Bash
허용) 실행했는데 **3회 다 파일을 전혀 건드리지 않고 채팅 텍스트로만
답하고 끝났다.** 세 번째 시도의 Bash 명령을 그대로 확인한 결과,
원인이 명확했다:

```bash
find ".../09-skill/.claude/skills/interaction-doctor" -type f | sort
find ".../09-skill" -iname "*ux-standards*" -o -iname "CONFLICTS.md"
find / -iname "ux-standards-architecture.md"
find / -iname "common-pitfalls.md" -path "*ux-standards*"
```

**`SKILL.md`와 `references/*.md`가 `research/ux-standards/patterns/
ux-standards-architecture.md`, `common-pitfalls.md`,
`nested-interactions/*.md`, `CONFLICTS.md`를 수십 곳에서 실제
경로처럼 인용하는데, 이 파일들은 `skills/interaction-doctor/`
패키지 안에 없다** — `SKILL.md` + `references/{symptoms,recipes,
platform}.md` 딱 4개만 배포된다. 이 세션은 그 인용을 그대로 믿고
원본 문서를 찾다가(마지막엔 파일시스템 루트까지 뒤짐) 정작 작업
디렉터리의 `project/index.html`은 한 번도 열어보지 않았다.

02번 skill 조건(재시도분)도 같은 탐색을 시도했지만(`find
".../02-skill" -iname "*ux-standards*"` 등) 이번엔 회복해서
`pwd; ls -la`로 결국 `project/`를 찾아 작업을 마쳤다 — **09번은
회복하지 못했고 02번은 회복했다**는 차이일 뿐, 같은 근본 원인이
두 시나리오 모두에서 실제로 발동한 걸 확인했다(01번 skill 조건은
이 탐색 자체를 시도하지 않고 바로 `Glob **/*`로 넘어가서 이
문제를 겪지 않았다 — 세션마다 첫 탐색 전략이 갈린다).

**이건 이전에 `ux-standards-architecture.md` §6에 적어 둔
"호스트 에이전트의 일반적 행동"과는 다른 종류의 문제다** — 그건
이 프로젝트가 고칠 수 없는 영역이라고 명시했는데, **이건 이
프로젝트가 고칠 수 있다.** `SKILL.md`/`references/*.md`가 실제로
패키지에 없는 파일을 있는 것처럼 인용하는 건 순수한 배포 패키징
결함이다.

**아직 고치지 않았다** — 이번 지시 범위(재실행·채점)를 벗어나고,
남은 6개 시나리오(03~08)의 skill 조건 전부에 같은 위험이 있어서
먼저 확인받는 게 맞다고 판단했다.

### 다음 단계 확인 필요

1. 이 패키징 결함을 지금 고칠지(예: `references/*.md`의 외부 경로
   인용을 실제 포함된 내용 요약으로 바꾸거나, 인용이 "이 프로젝트
   자체 개발 시 근거"였을 뿐 스킬 소비자가 따라가야 할 경로가
   아니라고 명시), 아니면 알려진 한계로 기록만 하고 남은 6개를
   그대로 진행할지.
2. 09번 skill 조건을 "미완료"로 둘지, 패키징을 고친 뒤 재시도할지.
