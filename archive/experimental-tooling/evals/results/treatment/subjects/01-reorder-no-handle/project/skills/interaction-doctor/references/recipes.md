# recipes.md

`research/ux-standards/nested-interactions/` 3개 문서의 §2(해소
규칙)와 §5(런타임 검증 결과)를 압축한다. **코드는 §4 원본이 아니라
§5 런타임 검증을 거친 버전을 쓴다** — 검증 과정에서 발견된 결함 중
고친 것(각 레시피의 `common-pitfalls.md` §4.5 표에서 "통과"로 표시된
것)과, 고치지 않고 한계로 남긴 것(같은 표에서 "미통과"/"해당 없음"으로
표시되거나 "한계" 섹션에 명시된 것)을 명확히 구분한다. §4 원본에는
`nested-interactions/*.md` §5-0이 실제로 재현한 결함(pointerdown
미확인)이 그대로 들어 있어서 스킬에 다시 넣지 않는다.

---

## 레시피 1 — 롱프레스 3중 충돌 (재정렬 ↔ 다중선택 ↔ 컨텍스트메뉴)

**문제**: 같은 리스트 항목에 세 기능이 전부 필요할 때, 같은 롱프레스가
무엇을 열어야 하는가.

**해소 규칙** (근거: `long-press-triple-conflict.md` §2)
- 1단계(이동 여부, 8px) — 사례 B(Android Pixel 런처, [표준] 상속)
  기반. 움직이면 재정렬이 무조건 이긴다.
- 2단계(시간 확전, 500ms→1000ms) — 사례 A(iOS 홈 화면, [표준]
  구조만 상속)의 구조를 다중 선택이라는 다른 목적지에 적용. **이
  조합과 1000ms 수치 자체는 `[이 프로젝트의 설계 판단]`** — 실기기로
  검증된 값이 아니다.
- 8px·500ms 수치는 이 프로젝트 자체 실측(C6, CONFLICTS.md) 재사용.

**코드** (§5-0에서 발견된 pointerdown 미확인 버그를 고친 버전 —
`tools/nested/long-press-triple-conflict-verify.html`에서 실제로
검증됨)

```js
const MOVE_THRESHOLD_PX = 8;       // C6 재사용
const CONTEXT_MENU_DELAY_MS = 500; // C6 실측(Android contextmenu 494–513ms)
const ESCALATE_DELAY_MS = 1000;    // 🚧 이 프로젝트의 설계 판단, 실기기 미검증

function attachTripleConflictResolver(el, { onReorder, onContextMenu, onMultiSelect }) {
	let startX = 0, startY = 0;
	let moved = false;
	let contextMenuTimer = null;
	let escalateTimer = null;
	let contextMenuFired = false;
	let armed = false; // 결함 수정: pointerdown 여부를 명시적으로 확인

	el.addEventListener("pointerdown", (e) => {
		startX = e.clientX;
		startY = e.clientY;
		moved = false;
		contextMenuFired = false;
		armed = true;

		contextMenuTimer = setTimeout(() => {
			if (!moved) {
				contextMenuFired = true;
				onContextMenu(e);
				escalateTimer = setTimeout(() => {
					if (!moved) onMultiSelect(e);
				}, ESCALATE_DELAY_MS - CONTEXT_MENU_DELAY_MS);
			}
		}, CONTEXT_MENU_DELAY_MS);
	});

	el.addEventListener("pointermove", (e) => {
		if (!armed) return; // 결함 수정 지점 — 호버만으로 오작동하는 걸 막는다
		if (moved) return;
		const dx = e.clientX - startX;
		const dy = e.clientY - startY;
		if (Math.hypot(dx, dy) > MOVE_THRESHOLD_PX) {
			moved = true;
			clearTimeout(contextMenuTimer);
			clearTimeout(escalateTimer);
			if (!contextMenuFired) onReorder(e);
			// 메뉴가 이미 뜬 뒤 이동하면 어떤 콜백도 안 부른다 — §4가
			// 답하지 않은 케이스, 관찰만 하고 정답을 정하지 않음
		}
	});

	["pointerup", "pointercancel"].forEach((type) => {
		el.addEventListener(type, () => {
			armed = false;
			clearTimeout(contextMenuTimer);
			clearTimeout(escalateTimer);
		});
	});
}
```

**런타임 검증** (`long-press-triple-conflict.md` §5, Playwright 실측)
- 500ms 시점 `onContextMenu` 1회 발동: **501.2ms**(오차 +1.2ms)
- 1000ms 확전 `onMultiSelect` 1회, `onContextMenu` 재호출 없음: **1003.1ms**
- 300ms에 이동 → `onReorder` 즉시(326.1ms), 700ms까지 지켜봐도 타이머
  실제로 취소되어 늦게 안 뜸
- 200ms에 해제 → 900ms 더 기다려도 둘 다 끝내 발동 안 함(정리 확인)

**common-pitfalls.md §4.5 체크리스트**
- 규칙 1(pointerdown 미확인) — **통과**(위 `armed` 플래그로 고침, 원래는
  실패였음)
- 규칙 2(멀티 포인터) — **미통과, 알려진 한계**. 두 번째 `pointerdown`
  (다른 `pointerId`)이 첫 번째를 해제하지 않고 들어오면
  `onContextMenu`/`onMultiSelect`가 각 2회씩 호출됨(`long-press-triple-conflict.md`
  §5-5, 실측 확인). **의도적으로 고치지 않았다** — 단일 포인터
  시나리오에는 필요 없고, 고치려면 새 설계 판단이 필요하다. 멀티터치가
  가능한 화면에 이 레시피를 쓸 거면 `pointerId`로 상태를 분리하는
  작업을 직접 추가해야 한다.

**한계**: 이동 후(메뉴가 뜬 상태에서 다시 이동하는) 네 번째 케이스는
관찰만 됐고 규칙이 없다. 1000ms 수치의 UX 적절성은 검증 대상이
아니다(§5-6, "타이머가 맞게 도는가"와 "값이 맞는가"는 다른 질문).

**상세**: `research/ux-standards/nested-interactions/long-press-triple-conflict.md`

---

## 레시피 2 — 바텀시트 내부 스크롤 vs 시트 자체 드래그

**문제**: 바텀시트 안 스크롤 가능한 리스트를 드래그할 때, 콘텐츠
스크롤과 시트 리사이즈/닫기 중 무엇이 이겨야 하는가.

**해소 규칙** (근거: `bottom-sheet-scroll-drag.md` §2)
- 경계 조건 기반 소유권 이양 — iOS `prefersScrollingExpandsWhenScrolledToEdge`
  가 확인해 준 "경계 도달 여부가 소유권을 결정한다"는 **구조**([표준]
  상속)를 그대로 가져온다.
- 이 구조를 iOS 공식 문서가 다루지 않는 **반대 방향**(콘텐츠가
  `scrollTop===0`에서 계속 아래로 당길 때 시트 축소/닫기)에 대칭
  적용하는 것 자체는 **`[이 프로젝트의 설계 판단]`**.
- 활성화 거리 8px는 C6 재사용(이 시나리오 고유 실측은 아님).

**코드** (§5-0에서 발견된 pointerdown 미확인 버그를 고친 버전 —
`tools/nested/bottom-sheet-scroll-drag-verify.html`에서 실제로 검증됨)

```js
const COLLAPSE_ACTIVATION_PX = 8; // C6 재사용

function attachSheetNestedScrollResolver(contentEl, sheetEl, { onSheetMove }) {
	let startY = 0;
	let ownedBySheet = false;
	let isDown = false; // 결함 수정: pointerdown 여부를 명시적으로 확인

	contentEl.addEventListener("pointerdown", (e) => {
		startY = e.clientY;
		ownedBySheet = false;
		isDown = true;
	});

	contentEl.addEventListener(
		"pointermove",
		(e) => {
			if (!isDown) return; // 결함 수정 지점 — 호버만으로 오작동하는 걸 막는다

			const dy = e.clientY - startY;
			const draggingDown = dy > 0;
			const atTop = contentEl.scrollTop <= 0;

			if (ownedBySheet) {
				e.preventDefault();
				onSheetMove(dy);
				return;
			}
			if (!draggingDown && !sheetEl.isAtLargestDetent) {
				onSheetMove(dy); // 확장 방향 — iOS가 확인한 부분
				return;
			}
			if (draggingDown && atTop && Math.abs(dy) > COLLAPSE_ACTIVATION_PX) {
				ownedBySheet = true;
				e.preventDefault();
				onSheetMove(dy); // 축소/닫기 방향 — 이 프로젝트의 대칭 가정
				return;
			}
			// 그 외에는 콘텐츠 스크롤이 기본 동작을 그대로 갖는다
		},
		{ passive: true }, // 아래 "한계" 참조 — 이 자체가 모순을 안고 있다
	);

	["pointerup", "pointercancel"].forEach((type) => {
		contentEl.addEventListener(type, () => {
			ownedBySheet = false;
			isDown = false;
		});
	});
}
```

**런타임 검증** (`bottom-sheet-scroll-drag.md` §5, Playwright 실측)
- `scrollTop=300`(맨 위 아님)에서 200px 드래그 → `onSheetMove` 0회,
  시트 `transform` 변화 없음 — innerScroll 승리 확인
- `scrollTop=0`에서 200px 드래그 → `onSheetMove` 12회, 최종
  `translateY(200px)` — 드래그 거리와 정확히 일치
- `preventDefault()`가 `{ passive: true }` 리스너 안에서 매번 콘솔
  에러(`Unable to preventDefault inside passive event listener
  invocation.`)를 냄 — 활성화 이후 매 `pointermove`마다 재현(20회
  드래그에서 20회)

**common-pitfalls.md §4.5 체크리스트**
- 규칙 1(pointerdown 미확인) — **통과**(위 `isDown` 플래그로 고침, 원래는
  실패였음)
- 규칙 2(멀티 포인터) — **해당 없음**. 이 요소는 단일 포인터 가정이
  합리적인 시나리오다(시트를 두 손가락으로 동시에 드래그하는 상황은
  조사하지 않았음 — 별도 미확정으로 남김).

**한계**: `{ passive: true }`로 등록했는데 `preventDefault()`가 필요한
모순을 의도적으로 고치지 않고 한계로 남겼다 — 콘텐츠가 실제로 계속 스크롤되며 이중으로
움직이는 버그로 이어지는지는 마우스 시뮬레이션으로는 확인 불가(🚧
미확정, 실기기 필요). 반대 방향(축소/닫기)에 이 구조를 적용한다는
가정 자체가 iOS/Android 공식 문서로 직접 확인된 게 아니라는 것도
그대로 남는다.

**상세**: `research/ux-standards/nested-interactions/bottom-sheet-scroll-drag.md`

---

## 레시피 3 — 사이드 드로어 vs 브라우저 뒤로가기 (완화 조치, 해소 규칙 아님)

**문제**: 사이드 드로어의 엣지 스와이프가 모바일 브라우저의 시스템
뒤로가기 제스처와 같은 물리적 화면 영역을 두고 겹친다.

**먼저 밝힌다 — 이건 "해소 규칙"이 아니라 "완화 조치" 목록이다**
(근거: `side-drawer-back-gesture.md` §2). 이 문제는 §3(오염 방지) 모델
자체가 적용되지 않는 범주다 — 브라우저가 엣지 영역의 터치를 페이지에
아예 안 줄 수도 있고, 그러면 페이지 쪽에 어떤 인식기를 선언해도
무관하다.

**완화 조치 3가지** (전부 `[이 프로젝트의 설계 판단]`, 약한 정황
있는 것도 있음 — §2-3 참조)

```css
/* 완화 1 — 시스템 제스처 억제 시도. 실제 억제 여부는 미확정. */
html {
	overscroll-behavior-x: contain;
}

/* 완화 2 — 왼쪽(iOS 시스템 뒤로가기 영역) 대신 오른쪽에서 연다 */
.drawer-trigger-zone {
	right: 0;
	left: auto;
}
```

```html
<!-- 완화 3 — 스와이프가 시스템에 뺏겨도 항상 열 수 있는 경로 -->
<button type="button" aria-label="메뉴 열기" onclick="openDrawer()">☰</button>
```

**런타임 검증** (`side-drawer-back-gesture.md` §5, Playwright 실측)
- **완화 1은 검증 불가능함을 실험으로 확인함** — CDP로 화면 왼쪽
  가장자리(x=1)에서 시작하는 완전한 터치 스트림을 주입(터치가 페이지에
  정상 도달함은 별도 확인)해도, 데스크톱 트랙패드 스타일 휠 스와이프를
  시도해도, headless/headed·`overscroll-behavior-x` 유무 어느 조합도
  실제 페이지 내비게이션을 발생시키지 못했다. **이건 실패가 아니라
  Playwright가 브라우저 엔진만 자동화하고 네이티브 브라우저 셸의
  시스템 제스처는 자동화 대상 밖이라는 걸 확인한 것**이다
  (`research/ux-standards/patterns/ux-standards-architecture.md` §6에
  일반 한계로 등재됨).
- 완화 2 — **검증됨**. 트리거존이 왼쪽 가장자리(x=0)에 안 닿고
  오른쪽에 정확히 닿음(`x=370, width=20`, 뷰포트 폭 390).
  닫힌 드로어는 화면 밖(x=390)에 대기.
  - 완화 3 — **검증됨**. 버튼 클릭 하나만으로(스와이프 시뮬레이션 없이)
  드로어가 `x=150`(완전히 화면 안)까지 열림.

**common-pitfalls.md §4.5 체크리스트**
- 규칙 1·2 — **해당 없음**. 이 코드는 CSS 배치 선언과 버튼 `onclick`
  뿐이라 `pointermove`/멀티 포인터 로직 자체가 없다.

**한계**: 완화 2·3은 "선언한 대로 배치/동작한다"는 것만 검증됐다 —
"충돌이 해소된다"는 뜻이 아니다. 완화 1이 실제로 효과가 있는지는
**이 프로젝트가 가진 도구로는 앞으로도 확인할 수 없다** — 답이
필요하면 실기기 필드 테스트 외에 방법이 없다.

**상세**: `research/ux-standards/nested-interactions/side-drawer-back-gesture.md`

---

## 레시피 4 — 세로 리스트 안의 세로 드래그(재정렬) vs 리스트 스크롤

**문제**: 핸들 없이 항목 전체가 드래그 타겟인 세로 리스트에서, 세로
방향 재정렬 드래그와 리스트 자체의 세로 스크롤을 어떻게 구분하는가.

**해소 규칙** (근거: `CONFLICTS.md#C10`, 원문 그대로 인용)

> "Vertical drag in a vertical list has no clean CSS answer. `pan-y`
> cancels every vertical drag (16/16 across three devices), and `none`
> kills list scrolling. Any vertical reorder must therefore
> distinguish the two gestures by something other than direction —
> typically a hold delay before drag activation, which is the approach
> dnd-kit's touch sensor takes."
> — CONFLICTS.md#C10

`pan-y`를 골라서 거리 기반(예: 8px 이동하면 드래그)으로 판정하는
접근은 채택하지 않는다 — 그 임계값보다 브라우저가 먼저 취소해버리는
경우가 실측으로 확인돼 있기 때문이다:

> "Android    8.1 – 10.3 px    n=11   (consistent with ViewConfiguration TOUCH_SLOP = 8dp)
> iPadOS    10.5 – 13.5 px    n=10
> iOS        5.5 – 14.5 px    n=10"
> — CONFLICTS.md#C10, Observed cancellation thresholds

> "One iPhone trial cancelled at **5.5 px** — below a conventional 8 px
> activation threshold. **Do not assume your own slop will fire before
> the browser cancels.**"
> — CONFLICTS.md#C10

**추가 확정 [표준]** — "hold-delay 도중 이동하면 타이머가 취소되는가"는
`research/ux-standards/patterns/reorderable-list.md`에는 없었지만
(재검색 확인, 언급 자체가 없음), iOS의 공식 롱프레스 제스처
인식기가 정확히 이 질문에 답한다:

> "The maximum movement of the fingers on the view before the gesture
> fails." ... "The allowable distance, measured in points. The default
> distance is 10 points."
> — [Apple Developer Documentation, `UILongPressGestureRecognizer.allowableMovement`](https://developer.apple.com/documentation/uikit/uilongpressgesturerecognizer/allowablemovement)

즉 iOS 플랫폼 API 레벨에서 롱프레스 계열 제스처는 **대기 도중 일정
거리 이상 움직이면 인식 자체가 실패(취소)한다**는 게 공식 문서로
확정된다. `CONFLICTS.md#C10`이 이미 근거로 인용한 dnd-kit의 touch
sensor도 독립적으로 동일한 설계를 쓴다 — `activationConstraint`의
`tolerance` 옵션 공식 문서: *"the distance, in pixels, of motion that
is tolerated before the drag operation is aborted... the operation
will only be aborted if the pointer is moved by more than \[tolerance\]
pixels during the delay."*(dnd-kit 공식 문서, Pointer/Touch Sensor)
— 두 개의 독립 출처(Apple 플랫폼 API, dnd-kit — C10이 이미 참조 모델로
지목한 바로 그 라이브러리)가 같은 결론으로 수렴한다.

**따라서 레시피 4를 정정한다.** 이전 버전은 "hold-delay 이전의
이동은 의도적으로 무시한다"고 설계했었는데, 이건 위 근거와 어긋난다
— 지금 코드는 이동 취소 로직을 추가한다. 다만 **정확한 취소
임계값(px)** 자체는 이 프로젝트가 이미 쓰고 있는 값(C6 재사용,
8px)을 그대로 유지한다 — Apple의 10pt나 dnd-kit 예제의 5px을 새로
들여오지 않는다. "이동하면 취소해야 한다"는 결정은 [표준]/[관행]
근거로 확정됐지만, "정확히 몇 px인가"는 여전히 `[이 프로젝트의 설계
판단]`이다(레시피 1·2와 같은 8px 재사용 관행을 그대로 따름) — 이
둘을 같은 확신도로 섞지 않는다.

그래서 이 레시피는 `touch-action: none`을 항목에 **정적으로**(제스처
도중에 동적으로 바꾸지 않고) 건다 — `touch-action`은 제스처 시작
시점에 한 번 확정되고 이후 바뀌어도 진행 중인 제스처에는 적용되지
않는다는 것 자체가 C10의 근거 문서(MDN, Chrome 팀 블로그)에 있으므로,
"hold-delay 이후에 `touch-action`을 켠다"는 접근은 애초에 성립하지
않는다. 대신 hold-delay(500ms, C6 재사용 — 레시피 1과 동일 패턴)는
"터치가 곧바로 드래그로 취급되는 것"을 막는 UX 안전장치로만 쓴다 —
브라우저와의 경합을 막는 용도가 아니다(`none`이 이미 16/16으로 항상
이긴다):

> "`none` — drag always wins. Measured: 16/16 drags succeeded, and
> 12/12 still succeeded with `setPointerCapture` disabled, so capture
> is not a prerequisite."
> — CONFLICTS.md#C10

**코드** (자체 점검만 완료 — 아래 "런타임 검증" 참조)

```css
.reorder-item {
	touch-action: none; /* 정적으로 고정. C10: pan-y는 세로 드래그를
	                        취소하고(6/6·5/5·5/5), none만 항상 이긴다(16/16) */
}
```

```js
const REORDER_HOLD_DELAY_MS = 500; // C6 재사용(레시피 1과 동일 패턴)
const MOVE_CANCEL_THRESHOLD_PX = 8; // C6 재사용 — 정확한 값 자체는 [이 프로젝트의
                                     // 설계 판단], "취소해야 한다"는 결정만 [표준]
                                     // (Apple allowableMovement)·dnd-kit(tolerance)

function attachVerticalReorderResolver(el, { onReorderStart, onReorderMove, onReorderEnd }) {
	let armed = false;          // 결함 방지: pointerdown 여부를 명시적으로 확인 (규칙 1)
	let activePointerId = null; // 결함 방지: 다른 포인터가 끼어들면 무시 (규칙 2)
	let startY = 0;
	let holdTimer = null;
	let dragging = false;

	el.addEventListener("pointerdown", (e) => {
		if (activePointerId !== null) return; // 이미 진행 중인 다른 포인터 — 무시
		activePointerId = e.pointerId;
		armed = true;
		dragging = false;
		startY = e.clientY;

		holdTimer = setTimeout(() => {
			if (armed && activePointerId === e.pointerId) {
				dragging = true;
				onReorderStart(e);
			}
		}, REORDER_HOLD_DELAY_MS);
	});

	el.addEventListener("pointermove", (e) => {
		if (!armed || e.pointerId !== activePointerId) return; // 규칙 1+2
		if (dragging) {
			onReorderMove(e, e.clientY - startY);
			return;
		}
		// hold-delay가 아직 안 끝났다 — 이동이 임계값을 넘으면 진입 자체를
		// 취소한다. iOS `UILongPressGestureRecognizer.allowableMovement`
		// ("The maximum movement of the fingers on the view before the
		// gesture fails.")와 dnd-kit의 `activationConstraint.tolerance`가
		// 독립적으로 같은 결론이라 이 분기 자체는 [표준]/[관행] 근거가
		// 있다 — 8px이라는 정확한 값만 [이 프로젝트의 설계 판단](C6 재사용).
		if (Math.abs(e.clientY - startY) > MOVE_CANCEL_THRESHOLD_PX) {
			clearTimeout(holdTimer);
			armed = false;
			activePointerId = null;
		}
	});

	function release(e) {
		if (e.pointerId !== activePointerId) return; // 규칙 2
		clearTimeout(holdTimer);
		if (dragging) onReorderEnd(e);
		armed = false;
		dragging = false;
		activePointerId = null;
	}

	// C10: "Always handle pointercancel. It is the only signal you get
	// when the browser wins, and pointerup will not follow."
	el.addEventListener("pointerup", release);
	el.addEventListener("pointercancel", release);
}
```

## 런타임 검증 결과

**[검증됨]** — Playwright(Chromium, headless)로 `tools/nested/reorder-hold-delay-verify.html`을
실제로 실행해 확인했다. `pointerId`를 직접 지정한 합성
`PointerEvent`를 페이지 자체의 `setTimeout` 시퀀스 안에서 디스패치해
(도구 호출 왕복 지연이 타이밍에 섞이지 않게) 4개 케이스를 재현했다.

**a. 8px 미만 이동 + 500ms 유지 → 재정렬 모드 진입, 정확한 ms 기록**
— **[검증됨]**. `onReorderStart`가 `pointerdown` 후 **502.6ms**에 1회
발동, `dragging` 시각 신호(배경색 변경) 적용 확인. 스크린샷:
`research/ux-standards/nested-interactions/verification/reorder-a-hold-delay-entered.png`.

**b. 500ms 전에 8px 넘게 이동 → 진입이 취소되는가** — **[구버전 코드로
검증, 이후 코드 수정됨 — 아래 "b (재검증)" 참조]**. 최초 실측(취소
안 됨, `onReorderStart`가 501.6ms에 그대로 발동)에서 "이동하면
취소된다"는 원래 전제가 코드와 어긋난다는 게 드러났다. 근거 조사
결과 [표준](Apple `allowableMovement`)·독립 출처(dnd-kit `tolerance`)
둘 다 "취소해야 한다"고 확정해서 코드를 고쳤다 — 아래 "b (재검증)"이
새 코드의 실측이다. 이 문단은 구버전 코드의 기록으로 남긴다.

**b (재검증). 코드 수정 후 다시 실행** — **[검증됨]**. 수정된
`tools/nested/reorder-hold-delay-verify.html`로 동일 시퀀스(100ms에
40px 이동)를 다시 실행했다. `onReorderStart`는 **끝내 발동하지
않았다**(650ms 넘게 대기해도 로그 비어 있음, `dragging=false` 유지).
취소는 이동 직후 **102.9ms**(`pointerdown` 대비)에 기록됐다 —
`MOVE_CANCEL_THRESHOLD_PX(8px)`를 넘은 즉시 취소되는 것까지 확인.
(a)·(c)·(d)는 이번 수정이 건드리지 않은 코드 경로라 재검증하지
않았다 — `pointermove` 핸들러 안에서 `dragging===true`일 때는 여전히
맨 위 `if (dragging) { ...; return; }`로 즉시 빠지므로 새로 추가된
취소 분기(else 경로)에 도달하지 않고, `pointerdown`/`release()`/규칙
1·2 로직도 이번에 한 글자도 바뀌지 않았다 — 코드 경로가 겹치지
않는다는 것 자체가 재검증을 생략한 근거다.

**c. 진입 후 세로 이동 → 실제로 재정렬되는가(좌표 변화로 확인)**
— **[검증됨]**. `onReorderStart`(501.5ms) 이후 `pointermove`(dy=+40)
→ `transform: translateY(40px)`, DOM 실측 `rectTop` 286→296. 이어서
`pointermove`(dy=−20) → `transform: translateY(-20px)`, `rectTop`
296→236(두 지점 사이 이동량 −60px과 정확히 일치). `pointerup` →
`transform` 초기화, `dragging=false`. 스크린샷:
`research/ux-standards/nested-interactions/verification/reorder-c-dragging-moved.png`.

**d. 두 번째 포인터 추가 → 규칙 2를 실제로 통과하는가**
— **[검증됨]**. `long-press-triple-conflict.md §5-5`와 동일한 절차
(`pointerId=1` pointerdown, 해제 안 함 → **200ms** 후 `pointerId=2`
pointerdown, 첫 번째를 해제하지 않은 채)로 재현했다. 결과:
`onReorderStart`가 **1회만** 발동 — 레시피 1이 이 정확한 시나리오에서
`onContextMenu`/`onMultiSelect` 각 2회 발동으로 "미통과, 알려진
한계"로 남겼던 지점이 이번엔 통과한다. 추가로 확인: `pointerId=2`의
`pointermove`는 완전히 무시됨(`transform` 불변), `pointerId=1`의
`pointermove`는 정상 작동(`transform: translateY(30px)`),
`pointerId=2`의 `pointerup`도 무시됨(`dragging` 유지,
`onReorderEnd` 미발동), `pointerId=1`의 `pointerup`만 정상적으로
제스처를 종료(`onReorderEnd` 1회). 최종 카운트:
`onReorderStart=1, onReorderMove=1, onReorderEnd=1`.

**발견된 불일치 — (b)의 전제와 실측이 달랐고, 근거를 찾아 해소했다**

최초 코드는 "이동 거리로 진입을 취소"하지 않았다 — `pointerdown` 후
500ms가 지나면 그 사이에 얼마나 움직였든 재정렬 모드로 진입했다.
`reorderable-list.md`를 재검색했지만 "hold-delay 도중 이동하면
타이머가 취소되는가"를 다룬 부분은 없었다. 대신 iOS 공식 API에서
직접 답을 찾았다:

> "The maximum movement of the fingers on the view before the gesture
> fails." ... "The default distance is 10 points."
> — [Apple Developer Documentation, `UILongPressGestureRecognizer.allowableMovement`](https://developer.apple.com/documentation/uikit/uilongpressgesturerecognizer/allowablemovement)

**[표준]** 근거가 확보됐으므로 "검증 범위 밖"으로 비워두지 않고
코드를 정정했다 — 위 코드 블록의 `pointermove` 핸들러가 이제
`MOVE_CANCEL_THRESHOLD_PX`(8px, C6 재사용)를 넘는 이동을 hold-delay
도중에 감지하면 `holdTimer`를 취소하고 `armed`/`activePointerId`를
리셋한다. "취소해야 한다"는 결정 자체는 [표준](Apple)·독립 출처
(dnd-kit `tolerance`, C10이 이미 참조 모델로 지목한 라이브러리)
둘로 확정됐지만, 정확한 8px 값은 여전히 `[이 프로젝트의 설계
판단]`이다(Apple 10pt·dnd-kit 예제 5px을 새로 들여오지 않고 C6
재사용값을 유지) — 이 둘의 확신도를 섞지 않는다. 재검증 결과는
아래 "b (재검증)" 참조.

**common-pitfalls.md §4.5 체크리스트** (자체 점검 — 코드를 읽고
논리적으로 어긋나지 않는지 재검토한 것이지, 실행해서 확인한 게
아니다)
- 규칙 1(pointerdown 미확인) — **통과(자체 점검)**. `armed` 플래그가
  `pointerdown`에서만 켜지고, `pointermove`는 이걸 제일 먼저 확인한다.
- 규칙 2(멀티 포인터) — **통과(자체 점검)**. `activePointerId`로 상태를
  단일 포인터에 묶고, 이미 진행 중인 포인터가 있으면 새 `pointerdown`을
  무시하며, `pointermove`/`pointerup`/`pointercancel` 전부
  `e.pointerId === activePointerId`를 확인한다. 레시피 1이 "미통과,
  알려진 한계"로 남겼던 지점을 이번엔 닫았다 — 단, 두 번째 손가락이
  완전히 무시된다는 대가는 아래 "한계"에 남는다.

**한계**
- **네이티브 스크롤을 항목 위에서 못 쓴다.** `touch-action: none`을
  정적으로 걸었으므로 hold-delay 결과와 무관하게 항목을 터치하면
  스크롤이 절대 안 된다. C10 원문이 이 대가를 그대로 짚는다: *"The
  cost of `none` is real but narrower than it looks. `none` only
  suppresses scrolling for gestures that begin on that element.
  Touching the container padding between items still scrolls normally
  (8/9 trials). In a dense list, however, every touch lands on an
  item, so the user experiences it as 'the list will not scroll' —
  this is exactly the trade-off reported in dnd-kit #453."* 이 레시피는
  이 대가를 상쇄하는 수동 스크롤 보정(예: 리스트 가장자리 근처에서
  자동 스크롤)을 구현하지 않는다 — 범위 밖으로 남긴다.
- **두 번째 포인터는 완전히 무시된다.** §4.5 규칙 2를 "구분"이 아니라
  "무시"로 통과시켰다 — 멀티터치로 두 항목을 동시에 조작하는 시나리오
  자체가 이 레시피의 대상이 아니라고 가정했다. 그 가정이 맞는지는
  검증 대상이 아니다.
- hold-delay 500ms는 C6 재사용이지 이 시나리오 고유 실측이 아니다 —
  레시피 1의 `ESCALATE_DELAY_MS`와 같은 성격의 `[이 프로젝트의 설계
  판단]`.
- pan-y 취소 임계값(8.1–14.5px)은 이 레시피가 실제로 쓰는 값이
  아니다(애초에 `pan-y`를 안 쓰므로) — `pan-y` 대신 `none`을 고른
  근거로만 인용했다.

**상세**: `CONFLICTS.md#C10` (원본 실측), `research/measurements/DERIVED.md`
(임계값 산출 방식)
