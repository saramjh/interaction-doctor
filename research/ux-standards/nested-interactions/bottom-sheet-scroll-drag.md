# Bottom Sheet Nested Scroll — Sheet Drag ↔ Internal Scroll

오염 방지 유형 **B**: 같은 컨테이너(바텀시트) 안에서, 시트 자체를
움직이는 드래그(리사이즈/닫기)와 시트 내부 콘텐츠의 스크롤이 같은
세로축을 두고 경합하는 문제. 유형 A(`long-press-triple-conflict.md`)와
같은 절차를 따른다 — `research/ux-standards/patterns/ux-standards-architecture.md` §3의
activation_distance/activation_delay/axis/relations 모델을 그대로
쓰고, 새 알고리즘을 발명하지 않는다. `patterns/bottom-sheet.md`가 이미
확인해 둔 사실만 근거로 삼는다.

---

## 1. 이미 확인된 사실 — 재조사 없이 인용만

`patterns/bottom-sheet.md`의 5번 섹션("내부 스크롤 콘텐츠 vs
시트-닫기 드래그의 우선순위")이 이미 확인해 둔 내용을 그대로
인용한다.

### iOS — 확장(위) 방향은 확인됨, 축소(아래) 방향은 미확정

> `prefersScrollingExpandsWhenScrolledToEdge` — "The default value is
> `true`, which means if the sheet can expand to a larger detent than
> `selectedDetentIdentifier`, **scrolling up in the sheet increases its
> detent instead of scrolling the sheet's content. After the sheet
> reaches its largest detent, scrolling begins.**"
> — `patterns/bottom-sheet.md` §5, 원출처 [Apple Developer Documentation](https://developer.apple.com/documentation/uikit/uisheetpresentationcontroller/prefersscrollingexpandswhenscrolledtoedge)

`bottom-sheet.md`가 이미 명시한 한계를 그대로 가져온다:

> "콘텐츠가 맨 위로 스크롤된 상태에서 아래로 더 당길 때 '시트가
> 축소/닫히는가, 아니면 스크롤뷰가 그냥 바운스하는가'라는 **반대
> 방향(닫기)의 대칭 동작은 이 문서에 명시돼 있지 않다.**"
> — `patterns/bottom-sheet.md` §5

### Android — 전용 토글은 있으나 기본값/세부 동작은 미확정

> `setDraggableOnNestedScroll(boolean)` / `isDraggableOnNestedScroll()`
> — "Sets whether this bottom sheet can be collapsed/expanded by
> dragging on the nested scrolling child view."
> — `patterns/bottom-sheet.md` §5, 원출처 [Android Developers](https://developer.android.com/reference/com/google/android/material/bottomsheet/BottomSheetBehavior#setDraggableOnNestedScroll(boolean))

이 메서드의 **기본값**(개발자가 아무 것도 설정하지 않았을 때 `true`인지
`false`인지)은 `bottom-sheet.md`에 인용된 범위에 없다 — 재조사하지
않고 **🚧 미확정으로 그대로 유지**한다.

| 항목 | iOS | Android |
|---|---|---|
| 전용 공식 메커니즘 존재 | 있음 (`prefersScrollingExpandsWhenScrolledToEdge`) | 있음 (`setDraggableOnNestedScroll`) |
| 확장(시트를 더 크게) 방향 동작 | 확인됨 — 콘텐츠가 아직 최대 디텐트가 아니면 스크롤이 디텐트를 키움 | 미확정 |
| 축소/닫기 방향 동작 | **미확정** | 미확정 |
| 기본값 | `true` (확인됨) | 미확정 |

**따라서 이 문서가 실제로 새로 설계해야 하는 부분은 좁다**: 두
플랫폼 다 "이런 조정이 필요하다"는 것 자체는 공식적으로 인정하지만,
**콘텐츠가 스크롤 맨 위에 있는 상태에서 계속 아래로 당길 때 시트가
줄어들거나 닫혀야 한다**는, 이 문제의 핵심 시나리오를 명시적으로
확인해 주는 1차 출처는 이번 조사로 찾지 못했다.

---

## 2. 이 프로젝트가 채택하는 해소 규칙

### 2-1. 설계 결정과 그 근거

**경계 조건 기반 소유권 이양 — iOS의 확인된 메커니즘을 구조만 재사용**

iOS가 확인해 준 것은 정확히 이거다: **콘텐츠 스크롤이 이미 끝(경계)에
도달해 있을 때만, 계속되는 같은 방향의 제스처가 콘텐츠가 아니라
컨테이너(시트)로 넘어간다.** ("scrolling up... After the sheet reaches
its largest detent, scrolling begins" — 뒤집어 읽으면: 시트가 아직 최대
디텐트가 아닌 동안은 스크롤이 컨테이너로 가고, 시트가 한계에 도달한
뒤에야 콘텐츠 스크롤로 넘어간다는 뜻이다.)

이 프로젝트는 이 **구조**(경계 도달 여부가 소유권을 결정한다)를 그대로
가져와서, iOS 공식 문서가 다루지 않는 **반대 방향**(콘텐츠가
`scrollTop === 0`에 있는 상태에서 계속 아래로 당길 때)에 대칭적으로
적용한다:

- 콘텐츠의 `scrollTop > 0`이면: 내부 스크롤이 이긴다. 시트는 움직이지
  않는다.
- 콘텐츠의 `scrollTop === 0`이고 포인터가 계속 아래로 이동하면: 그
  시점부터 시트 자체의 드래그(축소/닫기)로 소유권이 넘어간다.

**이 대칭 적용 자체가 이 프로젝트의 설계 판단이다.** iOS 공식 문서는
위쪽 방향만 말했지 아래쪽을 말하지 않았다 — "대칭일 것"이라는 가정은
합리적으로 보이지만 어느 1차 출처로도 확인되지 않았다(`bottom-sheet.md`
가 이미 이렇게 명시함). Android의 `setDraggableOnNestedScroll`은 이
문제를 다루는 공식 토글이 존재한다는 사실만 확인해 줄 뿐, 정확히 이
경계 조건 로직을 쓰는지는 확인되지 않았다.

### 2-2. §3 모델로 명시한 선언

```
recognizers:

  innerScroll:
    axis: vertical
    activation_condition: "scrollTop > 0 || dragDirection === 'up'"
      # ⚠ §3 원 모델에 없는 새 필드 — 아래 설명 참조
    relations:
      blockedBy: []
      requireFailureOf: []
      simultaneousWith: []
    # 콘텐츠가 맨 위가 아니거나, 위로 스크롤하는 중이면 무조건 이긴다.
    # "위로 스크롤"은 항상 콘텐츠 우선 — iOS 확인 사실(확장 방향)의
    # 반대쪽 절반: 시트가 아직 최대 디텐트가 아닐 때 위로 스크롤하면
    # 시트를 키우는 게 iOS 규칙이지만, 이건 "시트 확장"이지 "콘텐츠
    # 스크롤"이 아니다 — 이 recognizer는 콘텐츠 스크롤만 다룬다.
    # 시트 확장 자체는 sheetExpand recognizer(아래, 미확정 상태로 남김)의 몫.

  sheetCollapseOrClose:
    axis: vertical
    activation_condition: "scrollTop === 0 && dragDirection === 'down'"
    activation_distance: 8   # px — C6/research/c10-sources.md 재사용,
                              # "우연한 1px 떨림"으로 오작동하지 않게 하는
                              # 최소 여유값. 이 시나리오 전용으로 검증된
                              # 값은 아니다 — 🚧 재사용일 뿐 이 상황에 대한
                              # 고유 실측은 없음
    relations:
      blockedBy: [innerScroll]
      requireFailureOf: []
      simultaneousWith: []

  sheetExpand:
    axis: vertical
    activation_condition: "!isAtLargestDetent && dragDirection === 'up'"
    relations:
      blockedBy: []
      requireFailureOf: []
      simultaneousWith: []
    # iOS `prefersScrollingExpandsWhenScrolledToEdge` 기본값(true)이
    # 실제로 확인해 준 부분 — [표준] 상속. activation_distance는
    # 명시하지 않는다 — 원문에 수치 없음, 🚧 미확정.
```

**`activation_condition`에 대한 정직한 표시**: 유형 A 문서에서
`escalatesFrom`을 추가했던 것과 같은 이유로, 여기서도 §3 원 모델
(`activation_distance`/`activation_delay`/`axis`/`relations`)에 없는
필드를 추가했다. 유형 A의 세 인식기는 "같은 트리거의 결과가 갈리는"
문제라 시간/거리 임계값 하나로 표현이 됐지만, 유형 B는 애초에 "콘텐츠
스크롤 위치"라는 **제스처 자체와 무관한 상태값**이 있어야 판정이
가능하다 — 순수 시간/거리 모델로는 표현할 수 없다. 이것도 §3 모델의
확장이며, 검증되지 않았다는 걸 숨기지 않는다.

---

## 3. 라벨

| 요소 | 라벨 | 근거/사유 |
|---|---|---|
| "경계 도달 여부가 소유권을 결정한다"는 구조 | [표준] (상속) | iOS `prefersScrollingExpandsWhenScrolledToEdge` 공식 문서, `bottom-sheet.md`에서 이미 [표준]으로 확인됨 |
| 위쪽 방향(시트 확장) 규칙 자체 | [표준] (상속) | 위와 동일 출처, 원문이 직접 다루는 방향 |
| 아래쪽 방향(시트 축소/닫기)에 같은 구조를 대칭 적용하는 것 | **[이 프로젝트의 설계 판단]** | 원문이 다루지 않는 방향. `bottom-sheet.md`가 이미 미확정으로 명시해 둔 지점을 이 문서가 대칭 가정으로 메웠다 |
| `activation_distance: 8`(축소 판정에 재사용) | 이 프로젝트 자체 실측(C6) 재사용 — 4라벨 체계 밖 | 다만 "경계 도달 후 아래로 당기는" 이 정확한 시나리오에 대한 고유 실측은 없다 — 값의 출처는 있지만 이 맥락에 대한 검증은 없다는 이중 상태 |
| `activation_condition` 필드 자체 | **[이 프로젝트의 설계 판단]** | §3 원 모델에 없는 확장(유형 A의 `escalatesFrom`과 같은 종류의 확장) |
| Android가 실제로 이 경계 조건 로직을 쓰는지 | 🚧 미확정 | `setDraggableOnNestedScroll`의 존재만 확인됨, 내부 판정 로직은 공식 문서에 없음 |

---

## 4. 코드 형태의 예시 — 자체 점검일 뿐, 런타임 검증 아님

```js
// interaction-doctor 예시 — bottom sheet nested scroll resolver
// 상태: 자체 점검(self-review)만 완료. §5.5 기준 런타임 검증 아님.
// 아래쪽(축소/닫기) 방향의 대칭 가정은 이 프로젝트의 설계 판단이며
// iOS/Android 어느 공식 문서로도 직접 확인되지 않았다.

const COLLAPSE_ACTIVATION_PX = 8 // C6 재사용, 이 시나리오 고유 실측 아님

function attachSheetNestedScrollResolver(contentEl, sheetEl, { onSheetMove }) {
	let startY = 0
	let ownedBySheet = false

	contentEl.addEventListener("pointerdown", (e) => {
		startY = e.clientY
		ownedBySheet = false
	})

	contentEl.addEventListener(
		"pointermove",
		(e) => {
			const dy = e.clientY - startY
			const draggingDown = dy > 0
			const atTop = contentEl.scrollTop <= 0

			if (ownedBySheet) {
				onSheetMove(dy)
				return
			}

			// 확장 방향: iOS가 확인한 부분. 시트가 최대 디텐트가 아니면
			// 위로 스크롤하는 제스처는 콘텐츠가 아니라 시트 확장으로 간다.
			// activation_distance를 원문이 안 줘서 여기서는 즉시 위임한다 —
			// 🚧 미확정 (지연/거리 없이 즉시 처리하는 게 맞는지 불명확)
			if (!draggingDown && !sheetEl.isAtLargestDetent) {
				onSheetMove(dy)
				return
			}

			// 축소/닫기 방향: 이 프로젝트의 대칭 가정.
			if (draggingDown && atTop && Math.abs(dy) > COLLAPSE_ACTIVATION_PX) {
				ownedBySheet = true
				onSheetMove(dy)
				return
			}

			// 그 외에는 콘텐츠 스크롤이 기본 동작을 그대로 갖는다
			// (여기서 preventDefault를 호출하지 않음)
		},
		{ passive: true },
	)

	;["pointerup", "pointercancel"].forEach((type) => {
		contentEl.addEventListener(type, () => {
			ownedBySheet = false
		})
	})
}
```

**이 코드에 대한 정직한 한계 표시**:

- `{ passive: true }`로 등록했다는 것 자체가 문제다 — 이 리스너 안에서
  실제로 시트를 움직이려면(콘텐츠의 기본 스크롤을 막아야 하는 시점에)
  `preventDefault()`가 필요한데, passive 리스너에서는 호출할 수 없다.
  `research/c10-sources.md`가 이미 확인한 WHATWG DOM 스펙의 "default
  passive value" 문제가 여기서 그대로 재현된다 — 이 코드는 그 모순을
  해결하지 않은 채로 남겨 뒀다. 실제 구현에서는 `{ passive: false }`가
  필요할 가능성이 높지만, 그러면 스크롤 성능에 미치는 영향(C10 참조)을
  같이 고려해야 한다 — 이 문서는 이 트레이드오프를 **해소하지 않고
  지적만 한다.**
- 위쪽(확장) 분기의 "즉시 위임"이 올바른지는 미확정으로 주석에 남겼다.
- **이건 §5.5 기준 자체 점검이다.** 실제 iOS/Android 브라우저에서
  손가락으로 눌러 본 적이 없다. "검증됨"이라고 말하지 않는다.

---

## 5. 런타임 검증 결과 — §5.5 기준 "검증됨"으로 승격되는 부분

**§4의 코드를 실제로 동작하는 페이지로 옮기고 Chromium(Playwright)에서
실제 포인터 이벤트를 흘려 확인했다.** 아래에서 "검증됨"이라고 쓴
부분만 §5.5 기준 런타임 검증을 통과한 것이다 — 이 섹션 밖의 나머지
내용(특히 §2-1의 iOS/Android 대칭 가정, iOS Safari/실제 터치스크린
동작)은 여전히 미확정이며, 이번 검증이 문서 전체를 검증된 것으로
바꾸지 않는다.

**환경**: Chromium(Playwright 1.62.1, headless), 뷰포트 390×844(iPhone
크기 흉내), 마우스로 시뮬레이션한 `pointerdown`/`pointermove`/
`pointerup` 시퀀스. **이건 실제 터치스크린이 아니다** — 브라우저는
실제 신뢰된(trusted) Pointer Event를 발생시키지만 `pointerType`은
`"mouse"`다. CONFLICTS.md가 지켜온 "시뮬레이터/터치 에뮬레이션 불인정"
원칙과는 다른 종류의 한계이므로 구분해 밝힌다 — 이건 시뮬레이터가
아니라 실제 브라우저 엔진이지만, 입력 장치가 터치가 아니라 마우스라는
뜻이다. 재현 페이지: `tools/nested/bottom-sheet-scroll-drag-verify.html`
(`?buggy=1` 쿼리로 아래 5-0의 결함 재현 모드 진입). 원시 결과:
`research/ux-standards/nested-interactions/verification/results.json`.

### 5-0. 예상 밖의 발견 — §4 코드 자체의 결함 (자체 점검이 놓쳤던 것)

실제로 페이지를 띄우자마자, **클릭을 한 번도 하지 않고 마우스를
콘텐츠 위로 가져다 놓기만 해도 시트가 아래로 400px 넘게 움직였다.**

원인: §4의 `pointermove` 핸들러가 `pointerdown`이 실제로 일어났는지
확인하지 않는다. `startY`가 페이지 로드 시 `0`으로 초기화된 채,
`pointermove`는 마우스 버튼을 누르지 않아도(단순 호버에도) 발생하므로
`dy = e.clientY - 0 ≈ 400`이 되어 `Math.abs(dy) > 8`을 곧바로
만족시킨다.

| 항목 | 값 |
|---|---|
| 재현 조작 | `page.mouse.move(x, y)` 단 1회, `mouse.down()`/`up()` 없음 |
| 호버 지점 | x=195, y=402.609375 (뷰포트 좌표) |
| 호버 전 상태 | `onSheetMove call count = 0`, `sheet.translateY = 0` |
| 호버 후 상태 | `onSheetMove call count = 1`, `sheet.translateY = 402.609375` |
| 콘솔 | `Unable to preventDefault inside passive event listener invocation.` (이때 이미 발생) |

**검증됨**: §4의 원본 코드 스니펫은 포인터가 눌린 상태인지 확인하지
않아, 클릭 없는 호버만으로 시트 이동을 오작동시킨다. 이건 §5.5가
정확히 예견한 상황이다 — §4를 작성할 때의 자체 점검("선언과 코드가
논리적으로 맞는가")은 이 결함을 잡지 못했다. 코드를 읽기만 해서는
`startY`의 초기값이 실제로 문제가 되는지 알 수 없었다.

**조치**: 검증용 페이지에 `isDown` 플래그 한 줄을 추가해 이 결함을
고쳤다 — `pointerdown`에서 `true`, `pointerup`/`pointercancel`에서
`false`로 설정하고, `pointermove` 맨 앞에서 `if (!isDown) return`으로
막았다. 이 수정은 `tools/nested/bottom-sheet-scroll-drag-verify.html`
안에 정확히 어디를 왜 고쳤는지 주석으로 남겨 뒀다. **§4의 코드 블록
자체는 이 문서에서 소급 수정하지 않는다** — 그 코드가 실제로 무엇을
놓쳤는지의 기록으로 그대로 남겨 두고, 이 §5가 그 위에 무엇이
발견됐는지를 덧붙이는 방식을 택했다.

### 5-1. 검증 a — scrollTop > 0일 때 아래로 드래그 → 콘텐츠 우선

수정된(위 5-0의 `isDown` 가드 적용) 코드로 검증했다.

| 항목 | 값 |
|---|---|
| 사전 조건 | `content.scrollTop = 300` (프로그램적으로 설정) |
| 조작 | `#content` 안에서 아래로 200px 드래그(누름→12스텝 이동→뗌) |
| 결과: `onSheetMove` 호출 횟수 | **0** |
| 결과: `sheet`의 `transform` | `matrix(1, 0, 0, 1, 0, 0)` (드래그 전과 동일, 변화 없음) |
| 결과: `content.scrollTop` | 300 (드래그 전후 동일) |
| 콘솔 | 없음 |
| 스크린샷 | `research/ux-standards/nested-interactions/verification/test-a-scrolltop-gt-0.png` |

**검증됨**: `scrollTop > 0`일 때 `sheetCollapseOrClose`가 전혀
활성화되지 않는다(`onSheetMove` 0회) — §2-2가 선언한
`blockedBy: [innerScroll]`이 실제로 그렇게 동작한다.

**검증되지 않은 부분(정직하게 표시)**: `content.scrollTop`이 드래그
전후로 300에서 그대로였다는 게 "콘텐츠가 실제로 스크롤됐다"는 증거는
아니다 — 마우스로 시뮬레이션한 `pointermove`는 브라우저의 네이티브
스크롤 물리를 일으키지 않는다(실제 터치 드래그와 달리, 마우스
이동만으로는 스크롤 컨테이너가 자동으로 스크롤되지 않는다). 이 검증이
실제로 확인한 건 **"리졸버가 시트 소유권을 주장하지 않았다"**는
것이지 **"콘텐츠가 대신 스크롤됐다"**는 것이 아니다 — 후자는 실제
터치 입력이 있어야 확인 가능하며, 이번 검증 범위 밖이다.

### 5-2. 검증 b — scrollTop === 0일 때 아래로 드래그 → 시트 우선

| 항목 | 값 |
|---|---|
| 사전 조건 | `content.scrollTop = 0` (페이지 로드 직후 기본값) |
| 조작 | `#content` 안에서 아래로 200px 드래그(누름→12스텝 이동→뗌) |
| 결과: `onSheetMove` 호출 횟수 | **12** (스텝마다 1회) |
| 결과: `sheet`의 `transform` | `matrix(1, 0, 0, 1, 0, 200)` |
| 결과: `sheet.style.transform`(인라인) | `translateY(200px)` — 드래그 거리(200px)와 정확히 일치 |
| 콘솔 | `Unable to preventDefault inside passive event listener invocation.` × 12 (활성화 이후 매 `pointermove`마다) |
| 스크린샷 | `research/ux-standards/nested-interactions/verification/test-b-scrolltop-eq-0.png` |

**검증됨**: `scrollTop === 0`이고 8px 넘게 아래로 이동하면
`sheetCollapseOrClose`가 활성화되어 `onSheetMove`가 실제로 호출되고,
시트의 `transform`이 드래그 거리만큼 정확히 움직인다. §2-2가 선언한
`activation_distance: 8`, `activation_condition: "scrollTop === 0 &&
dragDirection === 'down'"`이 실제 브라우저에서 그대로 재현된다.

### 5-3. 검증 c — 문서가 스스로 지적한 passive/preventDefault 모순

§4 자체가 이미 "`{ passive: true }`로 등록했는데 `preventDefault()`가
필요한 순간이 있다"는 모순을 자체 점검으로 지적해 뒀다. 이걸 실제
브라우저 콘솔로 재현했다.

| 항목 | 값 |
|---|---|
| 조작 | `scrollTop=0`에서 아래로 300px 드래그(20스텝) |
| 콘솔 에러 원문(정확히 이 문자열) | `Unable to preventDefault inside passive event listener invocation.` |
| 발생 횟수 | 20회 (활성화 이후 매 `pointermove`마다 1회씩, 즉 매번 실패) |
| 페이지 레벨 예외(`pageerror`) | 없음 — `preventDefault()`가 패시브 리스너 안에서 호출되는 건 스펙상 조용한 무시(no-op)이지 예외가 아니다(§4에서 이미 이 점을 명시함, 이번에 실측으로 확인) |
| 실제 동작에 미치는 영향 | 이 결과만으로는 **콘텐츠가 실제로 계속 스크롤되는지(모순이 실제 버그로 이어지는지)는 확인 못 함** — 마우스 시뮬레이션이 애초에 네이티브 스크롤을 일으키지 않으므로(5-1 참조), "스크롤이 부적절하게 계속된다"는 실패 모드는 이 마우스 기반 검증으로는 관찰할 수 없다. 실제 터치 기기에서만 확인 가능 — 🚧 미확정으로 남긴다. |

**검증됨**: `{ passive: true }`로 등록된 리스너 안에서 `preventDefault()`
를 호출하면 Chromium이 정확히 이 문자열의 콘솔 에러를 매번 낸다는 것,
그리고 이게 페이지를 중단시키는 예외는 아니라는 것.

**검증되지 않은 것**: 이 모순이 실제 터치 기기에서 "콘텐츠가 계속
스크롤되며 시트도 같이 움직이는" 이중 스크롤 버그로 실제 나타나는지
— 이건 여전히 🚧 미확정이다. §4가 이미 "해소하지 않고 지적만 한다"고
밝혔던 트레이드오프는 이번 런타임 검증 이후에도 미해소 상태로
남는다.

### 5-4. 이번 검증이 바꾸지 않은 것 — 여전히 미확정인 부분

§5.5 규율대로, 위에서 "검증됨"이라고 명시한 세 가지(5-1의 비활성화
조건, 5-2의 활성화·거리 정확성, 5-3의 콘솔 에러 문자열) **외의
모든 내용은 검증 상태가 바뀌지 않는다**:

- §2-1의 "iOS가 확인한 확장 방향 구조를 축소 방향에 대칭 적용한다"는
  **[이 프로젝트의 설계 판단]** — 여전히 iOS/Android 어느 공식 문서로도
  확인되지 않음.
- 실제 iOS Safari/Android Chrome의 **터치스크린**에서 이 페이지가
  동일하게 동작하는지 — 이번 검증은 마우스 시뮬레이션이었을 뿐이다.
  🚧 미확정.
- 위쪽(확장) 분기(`sheetExpand`, `!sheetEl.isAtLargestDetent`)는 이번
  검증에서 아예 건드리지 않았다 — 이 페이지는 `isAtLargestDetent`를
  항상 `true`로 고정해 뒀기 때문이다(작업 지시 2a/2b가 아래쪽 방향만
  요구했음). 🚧 미확정으로 그대로 남는다.
- 5-3에서 지적한 "이중 스크롤 실제 발생 여부"도 미확정.

---

## 다음 단계

- 유형 C(사이드 드로어 vs 브라우저 뒤로가기)는 이후
  `side-drawer-back-gesture.md`로 완료됨. 이 문서가 지적한
  passive/preventDefault 모순은 실제로 그 문서에서도 다시 등장했다
  (사이드 드로어도 엣지 스와이프를 가로채야 하므로) — §5.3에서 예견한
  대로다.
- 이 문서의 §2 규칙에 대한 런타임 검증(Playwright)은 §5에서 완료됨.
  §5-4가 명시한 미확정 사항(iOS/Android 대칭 가정, 실제 터치스크린
  동작, 확장 방향 분기, 이중 스크롤 실제 발생 여부)은 여전히 남아
  있다 — 별도 요청 시 진행.
