# common-pitfalls.md

**이건 조사 문서가 아니다.** 다른 `research/ux-standards/` 문서들은
iOS/Android 공식 문서를 검색해 확인하지만, 이 문서의 원료는 외부
근거가 아니라 **이 프로젝트가 스스로 작성한 코드에서 Playwright
런타임 검증으로 실제 재현된 버그**다. 대상은 정확히 "§4(자체
점검)가 스스로는 못 잡았지만 §5(런타임 검증)에서 잡힌 것"으로
한정한다 — §4가 이미 주석으로 예상해 둔 문제(예:
`bottom-sheet-scroll-drag.md`의 passive/preventDefault 모순)는
자체 점검이 실제로 작동한 사례이지 이 문서의 대상이 아니다.

---

## 1. 발견된 결함 원장 — 일반화하기 전에 사실관계부터

| 발견 문서 | 결함 | 증상 | 원인 |
|---|---|---|---|
| `nested-interactions/bottom-sheet-scroll-drag.md` §5-0 | pointerdown 미확인 | 클릭 없이 마우스를 콘텐츠 위로 올려놓기만 해도 `onSheetMove`가 발동함(호출 횟수 0→1, `sheet.translateY`가 402.6px로 변함) | `pointermove` 핸들러가 `pointerdown`에서만 초기화되는 `startY`(초기값 0)를 그대로 써서 `dy = e.clientY - 0`을 계산 — 포인터가 실제로 눌려 있는지(`isDown`) 확인하는 코드가 없었음 |
| `nested-interactions/long-press-triple-conflict.md` §5-0 | pointerdown 미확인 | 동일 패턴: 호버만으로 `onReorder`가 스퓨리어스하게 호출됨(호출 횟수 0→1) | 위와 동일 — `startX`/`startY`/`moved`/`contextMenuFired`가 `pointerdown` 안에서만 초기화되는 공유 변수였고, `pointermove`가 "눌린 상태(armed)"인지 확인하지 않았음 |
| `nested-interactions/long-press-triple-conflict.md` §5-5 | 멀티 포인터(또는 겹치는 연속 입력) 미처리 | 두 번째 `pointerdown`(다른 `pointerId`)이 첫 번째를 해제하지 않은 채 들어오면, `onContextMenu`와 `onMultiSelect`가 각각 1회씩이 아니라 **2회씩** 호출됨 | `contextMenuTimer`/`escalateTimer`가 `pointerId`로 구분되지 않는 공유 변수라서, 두 번째 `pointerdown`이 변수를 덮어쓰면 첫 번째 제스처가 예약해 둔 타이머가 정리되지 않은 채 고아 상태로 남아 나중에 그대로 발동함 |

이 세 행이 지금까지 확보한 전부다. `bottom-sheet-scroll-drag.md`와
`long-press-triple-conflict.md`는 각각 독립적으로 작성된 코드이고,
서로를 참조하거나 베끼지 않았다 — 그런데도 첫 번째와 두 번째 행이
정확히 같은 결함 패턴을 보였다는 것 자체가 아래 규칙 1의 확신도를
지지하는 근거다.

`side-drawer-back-gesture.md` §4는 이 원장에 없다 — 그 문서의 §4
코드는 CSS 배치 선언과 버튼 `onclick` 하나뿐이라 애초에
`pointermove`/멀티 포인터 로직 자체가 없다. 아래 체크리스트가 적용될
대상이 아니다.

---

## 2. 일반화 규칙 — 확신도는 독립 사례 개수로만 매긴다

### 규칙 1 — 포인터가 실제로 눌려 있는지 먼저 확인하지 않으면 호버만으로 오작동한다

**확신도: 높음 — 독립 사례 2건**(bottom-sheet, long-press-triple-conflict).

`pointerdown` 핸들러 안에서만 초기화되는 상태(시작 좌표, `moved`류
플래그)를 `pointermove`나 다른 리스너가 그대로 참조하면, 그 상태의
"초기값"이 실제로는 "포인터가 아직 눌리지 않은 상태"를 의미하는데도
코드는 이를 구분하지 못한다. 페이지 로드 직후의 첫 `pointermove`(단순
호버)조차 `pointerdown`이 설정했어야 할 값과 똑같은 모양의 데이터를
만들어내고, 활성화 조건(거리 임계값 등)을 우연히 통과시켜 버린다.

**대응**: `pointerdown`에서 `true`로, `pointerup`/`pointercancel`에서
`false`로 설정하는 별도 boolean(`armed`, `isDown` 등)을 두고,
`pointermove` 로직의 맨 앞에서 그 플래그부터 확인한다. 상태 변수의
"초기값"과 "리셋값"이 우연히 같아 보여도, "포인터가 눌려 있다"는
사실 자체는 별도 플래그로 명시해야지 좌표값의 형태로 추론하면 안
된다.

### 규칙 2 — 같은 요소에 포인터가 겹칠 수 있으면 pointerId로 상태를 구분해야 한다

**확신도: 중간 — 독립 사례 1건**(long-press-triple-conflict). 추가
사례가 나오면 격상한다.

제스처별 상태(타이머 참조, 플래그)를 요소 하나당 공유 변수 하나에만
저장하면, 이전 제스처가 아직 끝나지 않은 채(=`pointerup`/
`pointercancel`이 오지 않은 채) 새 `pointerdown`이 들어오는 순간
그 변수가 덮어써진다. 덮어써진 이전 값(예: `setTimeout`이 반환한
타이머 ID)은 어디서도 참조할 수 없게 되어 `clearTimeout`으로 정리할
방법이 사라지고, 그 타이머는 콜백 실행 시점에 **그때의(새 제스처의)
공유 상태**를 읽어 예상 못한 시점에 발동한다.

**대응**: 여러 포인터가 한 요소에 동시에 닿을 수 있는 상황(멀티터치,
또는 사용자가 손을 떼지 않고 다른 손가락을 추가로 대는 경우, 또는
동일 지점에 빠르게 연속 입력이 들어오는 경우)에서는 제스처별 상태를
`Map<pointerId, GestureState>` 같은 구조로 분리해서 저장하거나,
최소한 새 `pointerdown`이 들어왔을 때 "이미 진행 중인 다른
`pointerId`가 있는가"를 확인해 무시하거나 명시적으로 처리해야 한다.

### 관찰(규칙 아님, 참고용) — 두 규칙의 공통점

두 규칙 다 "제스처의 시작과 경계를 명시적으로 표시하지 않으면
상태가 새어나간다"는 같은 방향을 가리킨다 — 규칙 1은 "제스처가
시작됐는가"를, 규칙 2는 "지금 다루는 상태가 어느 제스처의 것인가"를
명시하지 않아서 생겼다. 이건 확신도를 매길 수 있는 별도 규칙이
아니라, 두 사례를 나란히 보고 나서야 보이는 편집자적 관찰이다 —
체크리스트 항목으로 올리지 않는다.

---

## 3. §4.5 체크리스트 — 자체 점검의 하위 게이트

`research/ux-standards/patterns/ux-standards-architecture.md` §5.5가 규정한 대로, **자체
점검(self-review)은 "선언과 코드가 논리적으로 어긋나지 않는가"를
보는 것**이다. 이 체크리스트는 그 자체 점검 절차 **안에** 새로
삽입되는 하위 게이트다 — `patterns/`나 `nested-interactions/`
어디서든 "## 4. 코드 형태의 예시" 같은 실행 코드 블록을 작성한
직후, 아래 항목을 전부 통과시키기 전에는 "자체 점검 완료"라고 표시할
수 없다. 통과 여부와 그 근거는 코드 블록 바로 다음에 "## 4.5. 자체
점검 — common-pitfalls.md 체크리스트" 섹션으로 명시한다.

```
□ [규칙 1] 이 코드에 pointerdown(또는 이와 동등한 제스처 시작
  이벤트)에서만 초기화되는 상태 변수가 있는가?
  있다면 → pointermove(또는 다른 리스너)가 그 상태를 쓰기 전에
  "이 포인터가 지금 실제로 눌려 있다"는 걸 확인하는 별도 boolean이
  존재하는가? 없으면 통과 실패 — 추가하거나, 왜 필요 없는지 근거를
  남긴다.

□ [규칙 2] 이 코드가 붙는 요소에 두 개 이상의 포인터가 동시에 닿을
  수 있는가(멀티터치), 또는 하나가 끝나기 전에 새 포인터가 겹쳐
  들어올 수 있는가(빠른 연속 입력)?
  그렇다면 → 제스처별 상태(타이머 참조, 플래그)가 e.pointerId로
  구분되어 있는가? 공유 변수 하나에만 저장하고 있다면 통과 실패 —
  구분하거나, 왜 이 요소에서는 겹칠 수 없는지 근거를 남긴다.

□ 이 체크리스트를 통과했다고 해서 "버그가 없다"는 뜻이 아니라는 걸
  응답에 명시했는가? 통과는 딱 이 두 특정 패턴이 없다는 것만
  보장한다 — 원장(1번)에 없는 종류의 결함은 이 체크리스트로 못
  잡는다.
```

**이 체크리스트 자체도 원장이 늘어나면 같이 늘어난다.** 지금은 2개
규칙(하나는 확신도 높음, 하나는 중간)뿐이다 — 새로운 런타임 검증에서
또 다른 반복 가능한 결함이 나오면 이 문서의 1번 표에 행을 추가하고,
2번에 규칙을 추가하거나 기존 규칙의 확신도를 격상시키고, 3번
체크리스트에도 항목을 추가한다.

---

## 4. 기존 §4 코드 블록 전수 점검 — 목록만, 소급 수정 안 함

`patterns/` 8개와 `nested-interactions/` 3개 문서를 전부 훑었다.

**`patterns/` 8개(reorderable-list, swipe-actions, bottom-sheet,
carousel, multi-select, context-menu, tab-swipe, side-drawer)는 전부
해당 없음** — 이 문서들은 조사·인용 문서라 "## 4. 코드 형태의 예시"
같은 실행 코드 블록 자체가 없다(직접 확인: 8개 파일 전체에 `js`/
`css`/`html` 코드 펜스가 0개). 체크리스트가 적용될 대상이 없다.

**`nested-interactions/` 3개는 이미 §5 런타임 검증을 거쳤다** —
새로 발견되는 것은 없었고, 체크리스트를 소급 적용한 결과는 이미 알고
있는 것과 정확히 일치한다:

| 문서 | 규칙 1(pointerdown 미확인) | 규칙 2(멀티 포인터) |
|---|---|---|
| `bottom-sheet-scroll-drag.md` §4 | **해당됨 — 이미 §5-0에서 발견·수정(검증 페이지에서만, §4 원문은 그대로)** | 해당 없음(이 코드는 단일 포인터 가정이 합리적인 시나리오 — 시트를 두 손가락으로 동시에 드래그하는 상황은 조사하지 않았음, 별도 미확정) |
| `long-press-triple-conflict.md` §4 | **해당됨 — 이미 §5-0에서 발견·수정(검증 페이지에서만, §4 원문은 그대로)** | **해당됨 — 이미 §5-5에서 발견, 수정하지 않고 관찰만 함(§4 원문도, 검증 페이지도 그대로)** |
| `side-drawer-back-gesture.md` §4 | 해당 없음(`pointermove` 로직 자체가 없음) | 해당 없음(위와 동일 이유) |

**소급 수정하지 않는다** — 이건 작업 지시대로 별도 과제로 남긴다.
특히 `long-press-triple-conflict.md`의 규칙 2 결함(멀티 포인터)은
`nested-interactions/long-press-triple-conflict.md` §5-5가 이미
"tasks a–e에 필요하지 않았고, 고치는 순간 새로운 설계 판단이
필요해진다"고 밝혀 둔 대로 미해결 상태로 남아 있다.

---

## 5. 이 문서의 위상

이 문서는 `research/ux-standards/patterns/ux-standards-architecture.md` §5.5("자체
점검"과 "런타임 검증"을 구분하는 절차) 안에 삽입되는 하위 게이트다.
§5.5 자체와 §5(자체 점검 체크리스트)에도 이 문서를 참조하라는 항목을
추가했다. `.claude/CLAUDE.md`의 절대 규칙에도 한 줄을 추가해 앞으로
이 프로젝트에서 작성되는 모든 인터랙션 코드가 이 게이트를 거치도록
했다.

---

## 6. 배포/테스트 절차의 함정 — 코드 결함이 아님

**이 섹션은 1~5절과 성격이 다르다.** 1~5절은 Playwright로 재현한
*코드* 결함(§4.5 체크리스트 대상)이다. 아래는 코드가 아니라 "스킬을
추가하고 같은 세션에서 바로 테스트한다"는 *작업 절차* 자체의 함정이다
— §4.5 체크리스트에 넣지 않는다. 세션 타임스탬프 포렌식(jsonl 로그
직접 대조)으로 확인했다.

### 함정 1 — 이미 실행 중인 세션에서 새 스킬 최상위 디렉터리를 만들면, 그 세션의 서브에이전트도 인식하지 못한다

**확신도: 이 프로젝트에서 실측 재현된 사례 1건 + 공식 문서 근거.**

**사실관계 (jsonl 로그 타임스탬프, UTC)**:

| 사건 | 시각 (UTC) | 시각 (KST) |
|---|---|---|
| 세션 `2e9c153b` 시작 | 2026-08-29T00:53:54Z | 08-29 09:53:54 |
| `.claude/skills/interaction-doctor/` 생성 (같은 세션 안에서 `cp -r`) | 2026-08-30T01:02:22Z | 08-30 10:02:22 |
| 같은 세션에서 "T1 트리거 테스트" 서브에이전트 실행 | 2026-08-30T01:02:31Z | 08-30 10:02:31 |
| → T1 결과: "interaction-doctor는 인식되지 않았습니다" | 2026-08-30T01:05:44Z | 08-30 10:05:44 |
| 세션 `2e9c153b` 종료(이 로그의 마지막 항목) | 2026-08-30T01:05:44Z | 08-30 10:05:44 |
| **새** 세션 `20f3783d` 시작 | 2026-08-30T01:06:00Z | 08-30 10:06:00 |
| 그 새 세션에서 `interaction-doctor`가 available-skills 목록에 정상 표시됨 | (이 대화 전체가 증거) | — |

디렉터리 생성(10:02:22)은 T1 서브에이전트 실행(10:02:31)보다 **9초
먼저** 일어났다 — 즉 "테스트할 때 파일이 아직 없었다"는 단순한
경합(race) 문제가 아니다. 그런데도 같은 세션 안에서는 실패했고,
불과 16초 뒤에 시작된 완전히 새 세션에서는 별다른 대기 없이 바로
인식됐다.

**원인 [표준 — `code.claude.com/docs/en/skills` "Live change detection" 원문]**:

> Claude Code watches skill directories for file changes. When you add,
> edit, or remove a skill under `~/.claude/skills/`, the project
> `.claude/skills/`, or a `.claude/skills/` inside an `--add-dir`
> directory, Claude Code picks up the change within the current
> session, without a restart. **If you create a top-level skills
> directory that didn't exist when the session started, restart Claude
> Code so it can watch the new directory.**

관건은 "생성 시점과 테스트 시점 사이에 시간이 얼마나 지났는가"가
아니라 **"그 세션(프로세스)이 시작될 때 그 최상위 디렉터리가 이미
존재했는가"**다. 세션 `2e9c153b`는 `.claude/skills/`가 생기기
꼬박 하루 전(08-29 09:53:54)에 시작됐으므로, 이 프로세스의 워치
목록에는 애초에 `.claude/skills/`가 없다. 그 세션 안에서 서브에이전트
(`Agent` 툴)를 새로 띄워도 서브에이전트는 부모 프로세스의 스킬
디스커버리 결과를 물려받을 뿐, 최상위 스킬 디렉터리를 자체적으로
다시 스캔하지 않는다 — 그래서 파일이 9초 전에 이미 완성돼 있었어도
보이지 않았다.

**대응**: 새 스킬 폴더, 특히 이전에 없던 최상위 `.claude/skills/`
디렉터리 자체를 프로젝트에 처음 추가했을 때는, 지금 열려 있는 세션
안에서 (서브에이전트를 통해서든 직접 트리거해서든) 곧바로 인식
테스트를 하지 않는다. **반드시 완전히 새 세션(새 `claude` 프로세스)을
시작한 뒤 테스트한다.** 생성과 테스트 사이에 몇 초를 두든 며칠을
두든 관계없다 — 지금 그 절차를 실행 중인 세션이 그 디렉터리보다
먼저 시작됐다는 사실 자체가 원인이므로, 그 세션 안에서는 무엇을 해도
고쳐지지 않는다.

이미 존재하는 `.claude/skills/` 아래에 스킬 하나를 새로 추가/수정하는
경우는 이 함정에 해당하지 않는다 — 그건 "Live change detection"이
정상적으로 커버하는 경우이고, 위 사례처럼 최상위 `.claude/skills/`
디렉터리 자체가 세션 도중 처음 생겨난 경우에만 해당한다.

### 함정 2 — 검증 스크립트를 짤 때 지켜야 할 절차: Pointer Capture API

**이것도 함정 1과 같은 이유로 §4.5 체크리스트에 넣지 않는다** —
검증 대상 컴포넌트의 코드 결함이 아니라, 그 컴포넌트를 검증하는
*스크립트 자체*를 어떻게 짜야 하는가의 절차 문제다.

**[검증됨] — `tools/c10-drag-vs-scroll.html`이 실제로 지키고 있는
세 가지 안전 패턴**

이 파일은 CONFLICTS.md#C10의 실측 전부(Precedence 표 192건 이상의
실기기 시행)를 만들어낸 바로 그 도구다 — "How to verify: Use
`tools/c10-drag-vs-scroll.html` on a real device over LAN"과
"Verified on: Android 10/Chrome 143, iPadOS 26.6, iOS 18.7"이 그
증거다. 즉 아래 호출 구조는 코드를 읽고 "괜찮아 보인다"고 판단한
게 아니라, 이 정확한 형태로 실기기에서 수백 회 반복 실행되고도
멈추거나 예외로 죽지 않았다는 게 C10의 실측 결과 자체로 확인된
것이다:

```js
items.forEach(function (el) { el.addEventListener('pointerdown', onDown); });
// ...
function onDown(e) {
  // ... (실제 pointerdown 이벤트 리스너 콜백 안)
  if (cfg.cap) {
    try { S.el.setPointerCapture(e.pointerId); log(rel() + ' setPointerCapture ok'); }
    catch (err) { log(rel() + ' setPointerCapture FAILED'); }
  }
}
```

— `tools/c10-drag-vs-scroll.html`

1. **`setPointerCapture`를 진짜 `pointerdown` 이벤트 리스너 콜백
   안에서만 호출한다.** 페이지 로드 시 즉시 호출하거나, 합성
   포인터 ID를 미리 만들어서 호출하지 않는다.
2. **`try`/`catch`로 감싼다.** 헤드리스·자동화 환경에서 이 API가
   예외를 던지더라도 로그만 남기고 스크립트가 멈추거나 죽지 않는다.
3. **capture 자체가 필수가 아님을 on/off 토글(`cfg.cap`)로 직접
   실측 대상에 넣었다.** 그 결과가 CONFLICTS.md#C10의 *"`none` —
   drag always wins. Measured: 16/16 drags succeeded, and 12/12 still
   succeeded with `setPointerCapture` disabled, so capture is not a
   prerequisite."* — capture를 아예 안 쓰는 선택지도 이미 검증돼
   있다.

**대응**: 터치/포인터 검증 스크립트에서 `setPointerCapture`를 쓸
때는 위 세 가지를 그대로 따른다. 특히 3번 — capture가 필수가
아니라는 게 이미 실측됐으므로, 헤드리스 환경에서 이 API가 문제를
일으킨다면 가장 먼저 시도할 것은 "고치기"가 아니라 "아예 안 쓰기"다.

---

**[정황 — 원본 미확보] "Gemini가 이 세 가지를 안 지켰을 가능성"**

이 문단은 위 [검증됨] 내용과 확신도가 다르다 — **섞어서 읽지
않는다.** Gemini 실험이 실행됐던 프로젝트 디렉터리(`~/.gemini/tmp/c10test`,
`~/.gemini/history/c10test`의 `.project_root`가 가리키는
`/Users/ojihun/DEV/c10test`)는 **현재 디스크에서 삭제되어 존재하지
않는다** — 확인 시도했으나 `ls`가 "No such file or directory"를
반환했다. 그래서 Gemini의 실제 검증 스크립트 코드를 한 줄도 확보하지
못했고, 위 세 패턴과 줄 단위로 대조하는 건 불가능하다.

"결함 A(Playwright Hang)"가 이 프로젝트의 `tools/c10-drag-vs-scroll.html`은
겪지 않은 문제라는 사실 하나는 확인됐다 — 같은 API를 같은 종류의
자동화 환경(브라우저 자동화)에서 수백 회 써도 이 파일은 멈추지
않았다. 여기서 나올 수 있는 가장 개연성 있는 추정은 "Gemini의
스크립트가 위 세 패턴 중 하나 이상(특히 1번·2번)을 안 지켰다"는
것이지만, **이건 추정이지 확인이 아니다.** 원본 스크립트가 복구되면
이 문단을 [검증됨] 또는 [반증됨]으로 갱신한다 — 그 전까지는 이
라벨([정황 — 원본 미확보])을 유지한다.

### 함정 3 — 자동화 스크립트의 부주의 실행: `require()`만 해도 유료 API 호출이 나갈 수 있다

**확신도: 이 프로젝트에서 실제로 재현된 사고 1건.** 함정 1·2와 같은
이유로 §4.5 체크리스트에 넣지 않는다 — 검증 대상 컴포넌트의 코드
결함이 아니라, 그 컴포넌트를 만드는(또는 호출하는) *스크립트 자체*의
실행 안전성 문제다.

**사실관계**: `evals/run-gemini.js`(Gemini API를 자동 호출해 noskill/skill
결과를 만드는 스크립트)의 스캐폴딩이 제대로 됐는지 확인하려고
`require("./run-gemini.js")`로 그냥 불러오기만 했다. 이 파일은
`require.main === module` 가드 없이 파일 맨 끝에서 무조건
`main()`을 실행하는 구조였고, `main()`은 `--scenario` 인자가 없으면
"9개 시나리오 × noskill/skill 2조건 = 18회"를 기본값으로 순회하도록
짜여 있었다. 그 결과 **승인받은 범위(1개 시나리오 1회)를 훨씬 넘는
실제 유료 API 호출이 나갔다** — 확인된 것만 4건 완료(`01`, `02`
시나리오의 noskill/skill), `03` 시나리오 1건은 호출 도중에 프로세스를
죽여서 서버가 실제로 처리했는지 클라이언트 쪽에서는 확신할 수 없는
상태로 남았다. (추가 확인: 실제로는 Google AI Studio 무료 티어로
호출하고 있어서 이번 사고로 금전 비용이 발생하지는 않았다 — 다만
무료 티어는 보통 분당/일당 요청 수(RPM/RPD) 제한이 있어서, 승인 없이
반복 호출이 나가면 비용이 아니라 **그 한도 초과**로 이어질 수 있다는
게 진짜 위험이다.)

**원인 두 가지, 겹쳐서 사고가 났다**:
1. `require.main === module` 가드 누락 — 파일을 "불러오기만" 해도
   최상위 실행 코드가 그대로 돎.
2. CLI 인자가 없을 때의 기본값이 "안전한 아무것도 안 함"이 아니라
   "전체 실행"이었음 — 이 두 번째 문제가 없었다면 첫 번째 문제가
   있었어도 최소한 시나리오 1개짜리 사고로 끝났을 것이다.

**재발 방지책 — 이중 게이트**:
- **1단계(가드)**: 파일 최하단을 `if (require.main === module) { main()... }`로 감싼다 —
  CLI로 직접 실행(`node run-gemini.js ...`)할 때만 진입점이 돈다.
  다른 스크립트가 `require()`로 불러와도(리뷰·재사용 목적이든 실수든)
  아무 일도 안 일어난다.
- **2단계(실행 직전 확인)**: 1단계와 별개로, 실제 네트워크 호출
  함수(`runOne()`) 안, `fetch` 직전에 `"다음 호출을 실행합니다:
  {시나리오}, {noskill|skill} · 예상 비용 추정 ≈ $X"`를 콘솔에 찍고,
  환경변수 `CONFIRM_GEMINI_CALLS=yes`가 없으면 그 자리에서 호출하지
  않고 종료한다. 이건 1단계가 어떤 이유로든 우회되더라도(예: 다른
  코드가 `runOne()`을 직접 불러 쓰는 경우) 실제 과금이 발생하는
  지점 자체를 한 번 더 막는 방어선이다 — 가드 하나에만 의존하지
  않는다.

**교훈**: "스크립트 구조만 확인하려는" 의도였어도, 최상위 실행 코드가
있는 파일을 `require`/`import`하는 것 자체가 이미 "실행"이라는 걸
잊으면 안 된다. 특히 그 파일이 과금·발송·삭제 같은 부작용이 있는
동작을 한다면, 가드 하나가 아니라 **서로 독립된 두 개 이상의
방어선**을 겹쳐야 한다 — 하나가 뚫려도 다른 하나가 막도록.

### 함정 4 — 합성 이벤트 헬퍼 함수 두 개가 서로 다른 이벤트 시퀀스를 흉내내면, 같은 버그를 두 번 "발견"하게 된다

**확신도: 이 프로젝트에서 실제로 두 번 재현된 사고(같은 그레이더
파일, 같은 근본 원인).** 검증 대상 컴포넌트(05번 시나리오,
multi-select)의 코드 결함이 아니라, 그걸 채점하는 *그레이더
스크립트 자체*의 일관성 문제다.

**사실관계**: `evals/graders/05-multi-select-photos.js`에는 탭을
흉내내는 `tap()`과 롱프레스를 흉내내는 `longPress()` 두 헬퍼가
있다. 실제 터치 기기에서는 롱프레스든 짧은 탭이든 손가락을 뗄 때
(움직이지 않았다면) 둘 다 `pointerdown → pointerup → click` 순서로
`click`까지 합성된다 — 그런데 `tap()`은 이 세 이벤트를 다 던지도록
고쳐져 있었지만(이전 세션에서 한 번 발견하고 고침), **`longPress()`는
`pointerdown`/`pointerup`만 던지고 `click`은 안 던지는 채로 남아
있었다.** 그 결과 "0번을 롱프레스로 진입 → 3번을 탭"을 검증하는
테스트에서, Gemini skill 조건이 3번 선택에 실패하는 것처럼 보였다
— 실제로는 Gemini의 코드가 진입 직후의 트레일링 클릭을 한 번만
삼키도록 짠 전역 플래그(`justEnteredByLongPress`)를 쓰고 있었는데,
`longPress()`가 그 트레일링 클릭 자체를 안 던져서 플래그가 계속
`true`로 남아 있다가 **다음에 들어온(3번의) 진짜 클릭을 대신
삼켜버린 것**이었다. `longPress()`에도 똑같이 트레일링 `click`을
추가하자 문제가 완전히 사라졌다(baseline/treatment/noskill/skill
네 조건 전부 동일하게 통과).

**두 종류의 "오탐"을 구분한다**: 이건 `research/ux-standards/patterns/multi-select.md`가
원래 지목한 결함(클로저에 캡처된 공유 `activeTile` 변수 — 어느
타일을 눌러도 최초 타일만 계속 토글되는 것)과는 **다른 종류다.**
실제로 확인한 결과 Gemini의 코드는 매 반복(`for` 루프)마다 별도
클로저(`pressTimer`, `startX`, `startY`, `isDown`)를 쓰고 `click`
핸들러도 그 반복의 `tile`/`i`를 그대로 캡처해서 — 그 결함 자체는
재현되지 않았다. 대신 **전역으로 공유되는 다른 변수
(`justEnteredByLongPress`, "방금 롱프레스로 진입했다"는 1회성
플래그)가, 테스트 쪽에서 그 플래그를 소비할 이벤트를 안 보내서
꼬인 것** — 컴포넌트 코드의 결함이 아니라 그레이더의 결함이었다.

**스킬 콘텐츠 오용 여부(별도로 확인한 것)**: `SKILL.md`/`recipes.md`에
multi-select 전용 코드 레시피는 없다 — `research/ux-standards/patterns/multi-select.md`는
여전히 실행 코드가 없는 조사 문서이고, `recipes.md`의 4개 레시피
중 multi-select를 다루는 건 "레시피 1 — 롱프레스 3중 충돌(재정렬
↔ 다중선택 ↔ 컨텍스트메뉴)"뿐이다. Gemini가 생성한 코드의
`MOVE_THRESHOLD_PX = 8`·`LONG_PRESS_DELAY_MS = 500`이라는 상수명과
값이 레시피 1의 `MOVE_THRESHOLD_PX`/`CONTEXT_MENU_DELAY_MS`와
정확히 일치해서, **레시피 1을 순수 다중선택 케이스에 맞게 축약해서
가져다 쓴 것으로 보인다** — 이건 "엉뚱한 레시피를 잘못 끌어왔다"가
아니라 "이 스킬에서 multi-select를 다루는 유일한 코드가 레시피
1이라, 그걸 재사용한 게 합리적인 선택이었고 실제로도 정상 작동한
것"이다. [정황 — Gemini의 실제 추론 과정을 볼 수 없어 확정은 아님,
다만 상수명·값의 일치가 강한 정황 증거]

**재발 방지책**: 같은 종류의 합성 이벤트(포인터 다운→업→클릭)를
흉내내는 헬퍼가 여러 개면, 한 군데를 고칠 때 **같은 패턴을 쓰는
다른 헬퍼도 같이 점검한다.** 하나만 고치고 넘어가면, 안 고친 쪽이
나중에 "새 결함을 발견한 것"처럼 보이는 오탐을 다시 만든다 —
바로 이번이 그 경우였다.

---

## 7. 공용 해법: 멀티포인터 격리

**목적**: 규칙 2(멀티포인터 미처리)가 컴포넌트마다 개별로 등장할
때마다 각자 다르게 땜질하지 않고, 재사용 가능한 표준 패턴 하나로
정의한다. 이 절은 진행 중이다 — 아래는 1단계(원장 정리)만 완료된
상태다. 새로 조사하지 않고, 이미 이 프로젝트에 있는 코드만 모았다.

### 7-1. 원장 — 규칙 2가 등장한 모든 사례

| # | 출처 | 무엇을 보여주는가 | 결과 |
|---|---|---|---|
| A | `nested-interactions/long-press-triple-conflict.md` §5-5 | 규칙 2 결함을 **최초로 발견**한 곳. `pointerId`를 전혀 추적하지 않는 원본 §4 코드에서, 첫 포인터가 해제되기 전 두 번째 `pointerId`가 들어오면 `contextMenuTimer`/`escalateTimer` 참조가 덮어써져 콜백이 2회씩 발동함 | 발견만 됨, **고치지 않고 관찰만** 남김(§5-5 원문: "tasks a–e에 필요하지 않았고, 고치는 순간 새로운 설계 판단이 필요해진다") |
| B | `tools/nested/reorder-hold-delay-verify.html`(레시피 4) | `armed`(boolean) + `activePointerId`(단일 변수) 조합으로 규칙 1+2를 함께 통과시킨 가드 패턴. `pointerdown`에서 `activePointerId !== null`이면 새 포인터를 아예 무시, 이후 모든 리스너가 `e.pointerId === activePointerId`를 먼저 확인 | §5 런타임 검증 통과(규칙 1+2 둘 다) — 단, **단일 요소 하나**에 대해서만 검증됨(리스트/여러 행 상황 아님) |
| C | `evals/results/{baseline,treatment}/subjects/09-longpress-triple-favorites/project/index.html` | 실제 diff로 확인: baseline은 `let activePointerId = null;`을 `attachTripleGesture` 함수 **밖**(모듈 전역, 리스트의 모든 행이 공유)에 선언하고 `pointerdown`에서 "이미 다른 포인터가 활성화돼 있으면 무시"로 **행 구분 없이** 차단. treatment는 같은 변수를 함수 **안**(행마다 독립된 클로저)에 선언하고 `armed && activePointerId === e.pointerId` 비교 가드를 씀 | `evals/RESULTS.md` 09번 채점: baseline은 같은 행 안의 규칙 2는 통과하지만 **다른 행을 동시에 조작하면 두 번째 행이 통째로 무시됨**(문서 밖 관찰, §5 범위 밖의 새 결함). treatment는 같은 행 규칙 2와 다른 행 독립성을 **둘 다** 통과 |
| D | `evals/RESULTS.md` 01(reorder-no-handle)·02(swipe-delete-todo) | baseline·treatment **둘 다** 규칙 2 실패. 원인: `activePointerId` 같은 가드 변수 자체가 없고, 공유 `startY`(01)/`startX`(02)만 있어서 두 번째 `pointerdown`이 비교 없이 그냥 덮어씀 | 두 조건 다 미충족 — 스킬 적용 여부와 무관하게 남은 공통 결함으로 `RESULTS.md`에 이미 기록됨 |

### 7-2. 코드 인용 — B와 C의 핵심 차이

**B(레시피 4, 단일 요소)** — `tools/nested/reorder-hold-delay-verify.html:63-83`:

```js
function attachVerticalReorderResolver(el, { onReorderStart, onReorderMove, onReorderEnd }) {
	let armed = false;          // 결함 방지: pointerdown 여부를 명시적으로 확인 (규칙 1)
	let activePointerId = null; // 결함 방지: 다른 포인터가 끼어들면 무시 (규칙 2)
	...
	el.addEventListener("pointerdown", (e) => {
		if (activePointerId !== null) return; // 이미 진행 중인 다른 포인터 — 무시
		activePointerId = e.pointerId;
		armed = true;
		...
	});
```

호출부(`reorder-hold-delay-verify.html:148`)는 `attachVerticalReorderResolver(target, ...)`를 **단 한 번**만 부른다 — 리스트 상황에서 이 클로저 스코프가 행마다 독립되는지는 이 파일만으로는 확인되지 않는다.

**C-baseline(09번, 리스트, 전역 변수)** — `evals/results/baseline/.../index.html:118-134`:

```js
// 글로벌 활성 포인터 트래커
let activePointerId = null;

function attachTripleGesture(row, index) {
	...
	row.addEventListener("pointerdown", (e) => {
		// 이미 다른 포인터가 활성화되어 있다면 무시 (멀티터치 방어)
		if (activePointerId !== null) return;
		activePointerId = e.pointerId;
		...
```

**C-treatment(09번, 리스트, 행별 클로저)** — `evals/results/treatment/.../index.html:128-133`:

```js
function attachTripleGesture(row, index) {
	let startX = 0;
	let startY = 0;
	let moved = false;
	let contextMenuTimer = null;
	let escalateTimer = null;
	let contextMenuFired = false;
	let armed = false;
	let activePointerId = null;

	row.addEventListener("pointerdown", (e) => {
		if (activePointerId !== null) return; // 진입 게이트 — B와 동일한 형태
		activePointerId = e.pointerId;
		...
		armed = true;
		...
	});
```

`attachTripleGesture(row, i)`가 각 행마다 새로 호출되므로, `activePointerId`가 함수 안에 선언된 treatment는 행마다 독립된 클로저를 얻는다 — baseline은 같은 변수를 함수 밖에 선언해서 모든 행이 공유한다. **이 한 줄의 위치(함수 안/밖) 차이가 09번 채점의 "같은 행 규칙2는 둘 다 통과, 다른 행 독립성은 treatment만 통과"라는 결과와 정확히 대응한다.**

원장은 여기까지다. 구조적 차이를 "성공 패턴 vs 실패 패턴"으로 일반화하는 건 2단계에서 한다.

---

### 7-3. 구조적 비교(2단계) — 스코프 축과 게이트 축은 서로 다른 축이다

**작업 지시대로 A, B, D의 실제 코드를 다시 열어 C에서 나온 가설("함수
밖 선언 vs 함수 안 선언")이 그대로 반복되는지 확인했다.** 결과:
**반복되지 않는다.** A와 D는 스코프가 아니라 다른 원인으로 실패한다
— 아래는 그 재확인 과정과, 그 결과로 나온 2축 모델이다.

**D(01/02 baseline) 재확인 — 스코프는 맞다, 게이트가 없다**

`evals/results/baseline/subjects/01-reorder-no-handle/project/index.html:95-104`:

```js
function attachDrag(row) {
	let startY = 0;
	let originY = 0;

	row.addEventListener("pointerdown", (e) => {
		startY = e.clientY;              // 진행 중인 제스처가 있는지 확인 없이 무조건 덮어씀
		originY = row.getBoundingClientRect().top;
		row.classList.add("dragging");
		row.setPointerCapture(e.pointerId);
	});
```

`startY`는 `attachDrag(row)` 함수 **안**에 선언돼 있다 — C-treatment와
똑같은 클로저 스코프다. `evals/results/baseline/subjects/02-swipe-delete-todo/project/index.html:91-99`도 동일 구조(`startX`/`isDragging`이
`attachSwipe(item, row, index)` 안에 선언됨). **그런데도 실패한다** —
`pointerdown`이 "이미 이 행에서 제스처가 진행 중인가"를 확인하는 코드
자체가 없어서, 같은 행에 두 번째 `pointerId`가 들어오면 무조건
`startY`/`startX`를 덮어쓴다. 스코프는 옳고, **진입 게이트가 통째로
없다.**

**A(레시피 1 원본 §4) 재확인 — 같은 실패 모드**

`nested-interactions/long-press-triple-conflict.md` §4(위 인용,
211-236행)의 `attachTripleConflictResolver`도 `startX/startY/moved/
contextMenuFired`를 함수 안에 정확히 클로저로 선언한다. 그런데도
`pointerdown`이 `activePointerId` 같은 변수 자체를 두지 않고 무조건
상태를 리셋한다 — **D와 정확히 같은 실패 모드**(스코프 문제 아님,
게이트 부재).

**B/C-treatment(성공) 재확인 — 둘 다 갖췄다**

B(`reorder-hold-delay-verify.html:71`)와 C-treatment(위 인용)는 둘 다
`pointerdown` 맨 앞에 `if (activePointerId !== null) return;` 형태의
**진입 게이트**를 갖고 있다 — 새 포인터가 들어와도 이미 활성 포인터가
있으면 상태를 건드리지 않고 그냥 무시한다. C-baseline도 이 게이트
**자체는** 갖고 있다(451행, "이미 다른 포인터가 활성화되어 있다면
무시") — 다만 그 게이트가 지키는 변수(`activePointerId`)가 전역이라
게이트가 적용되는 범위가 "이 행"이 아니라 "전체 리스트"로 잘못
넓어진 것이다.

**2축 모델**

| | 스코프(변수가 어디 선언됐는가) | 게이트(`pointerdown`에 진입 확인이 있는가) | 결과 |
|---|---|---|---|
| A(레시피1 원본) | 클로저(정상) | **없음** | 같은 요소 안에서도 실패 |
| B(레시피4) | 클로저(정상, 단일 요소만 확인) | 있음 | 통과 |
| C-baseline | **전역**(잘못됨) | 있음 | 같은 행은 통과, **다른 행까지 차단**(과잉 격리) |
| C-treatment | 클로저(정상, 행별) | 있음 | 통과(같은 행 + 다른 행 독립 둘 다) |
| D-01 | 클로저(정상) | **없음** | 같은 요소 안에서도 실패 |
| D-02 | 클로저(정상) | **없음** | 같은 요소 안에서도 실패 |

**두 축은 서로 다른 실패를 만든다**: 스코프가 틀리면(C-baseline, 1
사례) 무관한 다른 요소까지 서로 막는 **과잉 격리**가 생긴다. 게이트가
없으면(A, D-01, D-02 — 독립 3사례) 같은 요소 안에서 두 번째 포인터가
첫 번째의 상태를 그냥 덮어쓰는 **격리 실패**가 생긴다. 성공한 두
사례(B, C-treatment)는 이 둘을 **동시에** 만족한 경우뿐이다 — 스코프만
맞고 게이트가 없어도(D 유형), 게이트만 있고 스코프가 틀려도(C-baseline
유형) 규칙 2는 부분적으로만 통과한다.

**확신도**: 게이트 부재 실패 모드는 A/D-01/D-02 **3개의 독립 사례**에서
반복됐다(같은 프로젝트 안이지만 서로 다른 컴포넌트·서로 다른 시점에
작성된 코드) — 높음. 스코프 실패 모드는 C-baseline **1개 사례**뿐이다
— 중간, 추가 사례가 나오면 격상한다. (규칙 1/2의 확신도 표기 방식과
동일하게 맞췄다.)

2단계는 여기까지다. 이 2축 모델을 3단계(공용 패턴 작성)의 근거로
쓸 수 있을지는 승인 후 진행한다.

---

### 7-4. 공용 패턴 — `withSinglePointerGate` [이 프로젝트의 설계 판단]

**이 패턴 전체가 [이 프로젝트의 설계 판단]이다.** 표준(W3C/HIG/
Material)도 관행(주요 제품 3개 이상 관찰)도 아니다 — 7-1~7-3에서
이 프로젝트 자신의 코드를 비교해서 나온 결론이다. "포인터 하나가
겹치면 두 번째는 거부한다"는 설계도 하나의 선택이다 — 여러 포인터를
`Map<pointerId, state>`로 동시에 추적하는 대안도 있을 수 있지만,
B/C-treatment 어느 쪽도 그렇게 하지 않았고 그 대안이 필요한 사례가
이 원장에 없어서 채택하지 않았다.

**게이트 축을 먼저 쓴다** [확신도: 높음 — 독립 사례 3건, A·D-01·D-02].
이게 01/02번을 실제로 고치는 핵심이다 — 아래 7-5에서 실측으로
확인한다.

```js
// common-pitfalls.md §7-4 — 단일 활성 포인터 게이트
// [이 프로젝트의 설계 판단]
function withSinglePointerGate(el, { onStart, onMove, onEnd } = {}) {
	let activePointerId = null; // 스코프 축 — 반드시 "요소 하나" 단위 클로저에 둔다

	el.addEventListener("pointerdown", (e) => {
		if (activePointerId !== null) return; // 게이트 축 [확신도: 높음, 독립 사례 3건]
		activePointerId = e.pointerId;
		onStart?.(e);
	});

	el.addEventListener("pointermove", (e) => {
		if (e.pointerId !== activePointerId) return; // 게이트 축
		onMove?.(e);
	});

	function release(e, cancelled) {
		if (e.pointerId !== activePointerId) return; // 게이트 축
		activePointerId = null;
		onEnd?.(e, { cancelled });
	}
	el.addEventListener("pointerup", (e) => release(e, false));
	el.addEventListener("pointercancel", (e) => release(e, true));
}
```

**스코프 축은 게이트와 별개로 명시한다** [확신도: 중간 — 독립 사례
1건, C-baseline뿐. 추가 사례가 나오면 격상한다]: `activePointerId`
선언 위치가 이 패턴이 지켜지는 범위를 결정한다.

```js
// 리스트에 적용할 때 — 요소(행)마다 새로 호출해서 각자 독립된
// 클로저를 갖게 한다. 이게 스코프 축이다.
items.forEach((row) => {
	withSinglePointerGate(row, {
		onStart(e) { /* 이 행의 제스처 로직 */ },
		onMove(e) { /* ... */ },
		onEnd(e, { cancelled }) { /* ... */ },
	});
});

// 금지 — activePointerId를 반복문 밖(모듈/전역 스코프)에 두면
// 09번 baseline과 똑같이 무관한 다른 행까지 서로 차단한다.
```

**게이트만 있고 스코프가 틀리면(C-baseline 유형), 또는 스코프만
맞고 게이트가 없으면(D 유형) 규칙 2는 부분적으로만 통과한다** — 이
패턴은 두 축을 동시에 충족시켜야 완전하다는 7-3의 결론을 그대로
코드로 옮긴 것이다.

---

### 7-5. 런타임 검증 — 레시피1(A)과 evals 02번(D-02)에 적용

**§5.5 기준 런타임 검증.** 자체 점검이 아니라 Playwright로 실제
포인터 이벤트를 흘려 확인했다. 두 사례 모두 **게이트 코드 이외에는
한 줄도 바꾸지 않았다** — 타이머 상수, dx 계산, 삭제 임계값(80px)
전부 원본 그대로다. "게이트 추가만으로 고쳐지는가"가 이번 검증의
유일한 질문이기 때문이다.

**재현 페이지**: `tools/nested/multipointer-gate-verify-longpress.html`
(A 재검증, `?buggy=1`로 게이트 없는 원본 재현 모드),
`tools/nested/multipointer-gate-verify-swipe.html`(D-02 재검증, 동일).

**A — 사례 A(레시피1)에 게이트만 추가**

재현 절차는 `long-press-triple-conflict.md` §5-5와 동일: `pointerId=1`
`pointerdown`(해제 안 함) → 200ms 후 `pointerId=2` `pointerdown`(첫
번째 해제 안 함, 같은 요소) → 1100ms 대기.

| | `onContextMenu` 호출 횟수 | `onMultiSelect` 호출 횟수 |
|---|---|---|
| 게이트 없음(`?buggy=1`, §5-5 원본 재현) | **2** | **2** |
| 게이트 적용 | **1** | **1** |

**검증됨**: 게이트 없는 쪽은 §5-5가 발견했던 결함(콜백 2회 중복
발동)을 그대로 재현한다. 게이트를 추가하자(다른 로직은 무수정)
의도한 대로 각 콜백이 정확히 1회씩만 발동한다.

**D-02 — 사례 D-02(evals 02번 baseline)에 게이트만 추가**

재현 절차는 `RESULTS.md` 02번 "규칙 2 재현 방법"과 동일: `pointerId=1`을
오른쪽 끝에서 눌러 왼쪽으로 90px(삭제 임계값 80px 초과) 이동 완료 →
200ms 후 `pointerId=2`가 도착 지점 근처(+5px)를 누름(첫 번째 해제 안
함) → `pointerId=1`이 손을 뗌.

| | 최종 `dx` | 삭제 여부 |
|---|---|---|
| 게이트 없음(`?buggy=1`, baseline 원본 재현) | **-5.0px** | 삭제 안 됨 |
| 게이트 적용 | **-90.0px** | **삭제됨**("우유 사기") |

**검증됨**: 게이트 없는 쪽은 `RESULTS.md`가 기록한 정확한 실패(두
번째 포인터가 `startX`를 덮어써서 -90px가 -5px로 쪼그라듦)를 그대로
재현한다. 게이트를 추가하자(삭제 임계값·dx 계산 무수정) `pointerId=2`의
`pointerdown`이 게이트에서 거부되어 `startX`가 보존되고, 최종 dx가
의도한 -90px 그대로 나와 삭제가 정상적으로 일어난다.

**결론**: "게이트 추가만으로 D가 실제로 고쳐지는가"라는 이번 작업의
핵심 질문에 **그렇다**로 답한다 — 서로 다른 컴포넌트(3중 분기
제스처, 스와이프 삭제)에 같은 6줄짜리 게이트를 얹는 것만으로 각자의
규칙 2 결함이 사라졌다. 스코프 축(요소당 클로저)은 이번 두 사례
모두 원래도 정상이었어서 이번 검증이 스코프 축까지 새로 확인하지는
않는다 — 그건 이미 7-3에서 C 하나로만 확인된 채로 남아 있다
(확신도 중간).

---

## 8. 상숫값 [Guess] 금지

**원인**: activation delay(ms)나 activation distance(px) 같은 수치는
코드를 짜는 그 순간 "이 정도면 되겠지"로 즉석에서 채워 넣기가
제일 쉽다 — 컴파일도 되고 눈으로 보기에도 그럴듯하게 동작한다.
그런데 이렇게 채운 숫자는 나중에 [표준]/[관성]/[관행] 중 어느
것도 아니면서 코드에는 마치 근거가 있는 것처럼 상수 이름을 달고
박제된다. `.claude/CLAUDE.md` 절대 규칙 1이 반면교사로 드는
사고("핸들이 있는데 근거 없이 롱프레스를 강제했던 사고")가 바로
이 실패 모드다 — 근거 없는 판단이 라벨 없이 코드에 들어간 것.

**근거**: 이 프로젝트에는 이미 이 규율을 지킨 사례와, 지키지 않으면
어떻게 되는지를 보여주는 반면교사가 둘 다 있다.
- 지킨 사례: `long-press-triple-conflict.md` §2-2의
  `ESCALATE_DELAY_MS = 1000`은 "🚧 [이 프로젝트의 설계 판단],
  실기기 미검증"으로 명시적으로 라벨돼 있다 — 코드 주석
  (`recipes.md` 레시피1)에도 "🚧 이 프로젝트의 설계 판단, 실기기
  미검증"이 그대로 따라간다. §5-6이 "타이머가 맞게 도는가"(검증
  가능)와 "1000ms가 맞는 값인가"(검증 불가, UX 판단)를 명시적으로
  분리해서, 전자가 [검증됨]이 됐다고 후자까지 검증된 것처럼 말하지
  않는다.
- 반면교사: CLAUDE.md가 프로젝트 최상단에 못박아 둔 그 사고 —
  레퍼런스에 핸들이 있었는데도(탭↔드래그 충돌이 구조적으로 이미
  분리된 상황) 근거 없이 롱프레스를 강제해서 만들어졌다. 근거를
  먼저 찾지 않고 "표준이겠지"로 짠 판단이 라벨 없이 코드에 들어간
  전형이다.

**금지 사항(구체적으로)**: 새 컴포넌트의 activation delay/distance
같은 수치를 정할 때, 아래 순서를 거치지 않고 즉석에서 숫자를
채워 넣는 것을 금지한다.
1. 먼저 기존 실측값(CONFLICTS.md의 C1~C13, `patterns/*.md`의 판정
   표)에서 같은 종류의 값을 찾는다 — 8px(터치 슬롭), 500ms(Android
   `contextmenu` 실측) 같은 값은 이미 이 프로젝트 안에 있다. 새로
   재는 게 아니라 재사용한다.
2. 찾지 못했으면, 그 값을 코드에 넣기 **전에** 라벨을 먼저 정한다
   — 플랫폼 공식 문서/실기기 관찰로 뒷받침되면 [표준]/[관성]/[관행]
   중 해당하는 것을, 아무 근거 없이 이 프로젝트가 처음 정하는
   값이면 **[이 프로젝트의 설계 판단]**을 코드 주석과 서술 양쪽에
   붙인다.
3. 근거 없이 상수를 만들어 놓고 라벨을 아예 안 붙이는 것 — 이게
   금지 대상이다. **[이 프로젝트의 설계 판단]이라는 라벨 자체는
   허용된다**(§7 전체가 이 라벨로 작성됐다) — 금지되는 건 라벨을
   생략한 채 "이미 확인된 값"인 것처럼 코드에 넣는 행위다.

**재발 방지책**: 인터랙션 코드에 새 ms/px 상수를 추가할 때는
`common-pitfalls.md` §4.5 체크리스트를 통과시키는 시점에 이 상수의
출처(C번호, patterns 문서, 또는 [이 프로젝트의 설계 판단])도 같이
적는다 — 규칙 1·2 체크리스트 항목 옆에 "상수 출처 확인"을 추가
항목으로 취급한다.

---

## 9. 실측이 예상과 다를 때의 조사 순서 — 코드보다 그레이더를 먼저 의심한다

**원인**: Playwright로 합성 포인터 이벤트를 던지는 그레이더/검증
스크립트는 실제 브라우저의 네이티브 입력 처리를 **흉내**낼 뿐이다
— `pointerdown`→`pointerup`만 던지고 뒤따르는 `click`을 안 던기거나
(함정 4), `setPointerCapture`가 예외를 던지거나(함정 2), 이런 흉내의
불완전함은 컴포넌트 코드와 무관하게 채점 결과를 오염시킬 수 있다.
결과가 "이 조건에서만 결함이 있다"처럼 예상과 다르게 나왔을 때,
바로 컴포넌트 코드를 의심하고 고치려 들면 **그레이더 자체의 결함을
컴포넌트 결함으로 오진**할 위험이 있다.

**근거**: 05번(multi-select-photos) 사례를 인용한다(전체 서술은 §6
함정 4 참조, 여기서는 "조사 순서"라는 원칙만 추출한다). Gemini
skill 조건이 "0번 롱프레스 진입 → 3번 탭" 테스트에서 3번 선택에
실패하는 것처럼 보였다. 코드부터 의심했다면 "Gemini가
`multi-select.md`의 클로저 캡처 결함을 재현했다"거나 "스킬 콘텐츠를
오용했다"는 잘못된 결론으로 갔을 것이다. 실제로는 그레이더의
`longPress()` 헬퍼가 `pointerdown`/`pointerup`만 던지고 `click`은
안 던지는 옛날 버전으로 남아 있었던 게 원인이었다 — 컴포넌트의
전역 플래그(`justEnteredByLongPress`)가 트레일링 클릭을 못 받아
계속 `true`로 남았고, 그게 다음 타일의 진짜 클릭을 대신 삼켰다.
`longPress()`에 `click`을 추가하자(그레이더만 수정, 컴포넌트 코드는
무수정) 문제가 완전히 사라졌다.

**재발 방지책 — 조사 순서**: 실측 결과가 기대와 어긋나면(baseline/
treatment 중 한쪽만 실패, 또는 이전 실측과 다른 결과) 아래 순서로
확인한다 — 순서를 바꾸지 않는다.
1. **그레이더의 이벤트 시퀀스가 실제 브라우저의 네이티브 입력과
   같은 모양인가**부터 확인한다. 같은 시나리오 파일 안에 비슷한
   합성 이벤트를 던지는 다른 헬퍼(§6 함정4처럼 `tap()`/`longPress()`
   같은 짝)가 있으면 서로 일관된 시퀀스를 던지는지 대조한다.
2. 그레이더가 맞다고 확인된 뒤에야, 실제 생성된 코드(`project/
   index.html`)를 열어 컴포넌트 자체의 로직을 의심한다.
3. 컴포넌트 결함으로 확정하기 전에, 그게 이 프로젝트가 이미 원장에
   올려둔 알려진 결함 패턴(§1 원장, §7-1 원장)과 같은 종류인지,
   아니면 새로운 것인지 구분한다 — 05번처럼 "같은 결함의 재현"이라고
   성급히 단정하지 않는다.
4. 원인을 확정하지 못하면 [정황]으로, 확정되면 [검증됨]으로
   표시한다 — 코드를 읽고 논리적으로 그럴듯하다고 결론 내리는 건
   [정황]이지 [검증됨]이 아니다.

---

## 10. 이 문서(와 §4.5·§7)가 검증하는 층, 그리고 검증하지 않는 층

**지금까지 §4.5·§7·evals 전체가 잰 건 전부 "물리 정확성"이다** —
타이머가 선언한 시간에 도는가, 좌표 계산이 맞는가, 멀티포인터가
격리되는가, 게이트가 두 번째 포인터를 거부하는가. `perception-
parameters.md`는 여기에 **다른 층 하나**를 추가한다 — 3축으로
조사했다:

- **입력(Input Fidelity)**: 사용자의 액션이 의도된 요소에 실제로
  도달하는가. `getBoundingClientRect()`+`elementFromPoint()`로
  가려짐(occlusion)을 판정할 수 있다는 것, 그리고 규칙1·2가 사실
  "요소 오식별"이 아니라 "액션 종류/입력 소유권 오판정"이라는
  다른 경로의 방해였다는 재해석(§1).
- **출력(Output Visibility)**: 시스템 반응이 실제로 보이는가 —
  가려짐/뷰포트 이탈(구조적으로 안 보임)과 대비 부족(구조적으로는
  보이는데 지각적으로 구분 안 됨) 둘 다 포함. 핸들 아이콘 대비
  1.21:1(WCAG 3:1 기준의 40%)이라는 신규 결함을 여기서 찾았다(§2).
- **속도(Response Latency vs Animation Duration)**: "처리 시작
  지연"(NN/G 0.1/1/10초)과 "애니메이션 재생 길이"(Material 3
  duration 토큰)는 다른 기준이고, 이 프로젝트의 500ms/8px류 값은
  둘 중 어느 것도 아닌 "제스처 판정 시간"이라는 제3의 범주라는 걸
  구분했다(§3).

**이 문서(common-pitfalls.md) §4.5·§7과 `perception-parameters.md`는
서로 다른 층을 잰다 — 섞지 않는다.**

| | 무엇을 확인하는가 | 통과해도 보장하는 것 |
|---|---|---|
| §4.5·§7 (물리 정확성) | 코드가 선언한 타이밍/좌표/포인터 격리대로 실제로 동작하는가 | "코드가 자기 자신의 명세를 지킨다" |
| `perception-parameters.md` (지각 파라미터) | 입력이 도달 가능한가, 출력이 보이는가, 속도가 인간 지각 한계 안에 있는가 | "물리적으로 맞는 동작이 사람에게도 인지·조작 가능한 형태로 도달한다" |

**그리고 이 프로젝트 어느 것도 증명하지 않는 것**: 물리 정확성도,
지각 파라미터 충족도 **"사용자가 실제로 이 상호작용을 만족스럽다고
느끼는가"를 증명하지 않는다.** 이 프로젝트에는 사용성 테스트
참가자가 없다(`perception-parameters.md` §0) — 만족도는 HCI
연구·접근성 표준으로 대리 측정한 파라미터의 집합일 뿐, 실제
사용자 반응 그 자체가 아니다. 이 구분은
`ux-standards-architecture.md` 최상단에도 명시했다(§0-1 "이
프로젝트가 증명하는 것과 증명하지 않는 것") — 두 문서가 같은
경계선을 두 번 다른 각도로 그은 것이다.

### 10-1. §4.5를 지금 강제 게이트로 승격할지 — 결정: 승격하지 않는다

**질문**: `perception-parameters.md`(입력 도달성, 속도 분류)를
§4.5처럼 "통과 전에는 자체 점검 완료라고 표시하지 않는다"는 강제
게이트로 승격할지.

**결정: 지금은 승격하지 않는다. 참고 문서로 유지한다.**

**근거**:
- §4.5의 규칙 1·2는 **거의 모든** pointer 이벤트 코드에 기계적으로
  적용 가능하다(pointerdown 확인 여부, pointerId 비교 — 코드를
  보면 있다/없다가 바로 판정된다) — 그래서 예외 없이 강제해도
  비용이 낮고 신호가 명확하다.
- `perception-parameters.md`의 항목은 그 정도로 균일하지 않다.
  "속도 분류"(처리 지연/재생 길이/제스처 판정 시간 중 어느
  것인지)는 판단이 필요하고, "입력 도달성"(`elementFromPoint`
  히트테스트)은 겹침·z-index 위험이 실제로 있는 컴포넌트에서만
  의미가 있다 — 위험이 없는 곳에도 기계적으로 강제하면 §8이 금지한
  것과 같은 종류의 문제(근거 없이 형식만 채우는 것)가 될 수 있다.
- `perception-parameters.md` 자체가 아직 소수 사례(핸들 대비 1건,
  재정렬 undo 부재 1건)에서만 실제 결함을 잡았다 — `common-
  pitfalls.md` §2가 규칙 1·2에 적용하는 것과 같은 원칙("확신도는
  독립 사례 개수로만 매긴다")을 이 문서에도 그대로 적용하면, 아직
  강제 게이트로 승격할 만큼 사례가 쌓이지 않았다.

**재검토 조건**: 이후 다른 레시피(5, 6 등)에 이 파라미터를 적용해
독립적으로 실제 결함을 잡는 사례가 몇 건 더 쌓이면(§2가 규칙
2를 "확신도: 중간, 1건 → 추가 사례 시 격상"이라고 열어둔 것과
같은 방식으로) 재검토한다. 그 전까지는 레시피 작성 시 "참고했는가"
정도로만 다루고, §4.5처럼 응답을 막는 하드 게이트로는 쓰지 않는다.

**상세**: `research/ux-standards/perception-parameters.md`(전체),
`ux-standards-architecture.md` §0-1
