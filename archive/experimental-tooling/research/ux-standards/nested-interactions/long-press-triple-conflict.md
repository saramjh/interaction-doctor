# Long-press triple conflict — Reorder ↔ Multi-select ↔ Context Menu

이건 오염 방지 작업 세 유형(A/B/C) 중 **유형 A**: 같은 항목 안에서
롱프레스 하나가 세 가지 서로 다른 모드(재정렬 시작, 다중 선택 진입,
컨텍스트 메뉴 열기) 중 무엇을 열어야 하는지를 다룬다. 유형 B(같은
컨테이너 안 다른 축의 드래그 중첩)와 유형 C(웹페이지 대 브라우저
크롬의 물리적 경합)는 이 문서의 범위가 아니다 — 다음 파일에서 각각
다룬다.

절차는 `research/ux-standards/patterns/ux-standards-architecture.md` §3(오염 방지)의
activation_distance/activation_delay/axis/relations 모델을 그대로
쓴다. 새 알고리즘을 만들지 않는다 — 아래 1번에서 정리한, `patterns/`
세 문서가 이미 확인해 둔 실제 사례만 근거로 쓴다.

(참고: `research/ux-standards/patterns/ux-standards-architecture.md` §3-2는 이 카테고리의 경로를
`research/nested-interactions/`로 스케치했었다. 이번 작업 지시는
`research/ux-standards/nested-interactions/`로 지정했으므로 후자를
따른다 — 스케치와 실제 경로가 다르다는 것만 기록해 둔다.)

---

## 1. 이미 확인된 사실 — 재조사 없이 인용만

### 1-1. 이 충돌이 플랫폼별로 실제로 발생하는가

`multi-select.md`의 "겹침" 섹션이 이미 확인해 둔 내용을 그대로
인용한다 — 재조사하지 않는다:

> "iOS 1st-party 앱들은 다중 선택 진입에 애초에 롱프레스를 쓰지
> 않으므로(1번), reorderable-list.md의 iOS 사례(Reminders, 롱프레스로
> 재정렬)와 이 문서의 iOS 사례가 트리거를 공유하지 않는다 — **iOS에서는
> 이 충돌이 Apple 자사 앱 설계상 아예 발생하지 않는다**는 관찰이 이번
> 조사로 확인됐다. 반면 Android 소비자 앱은 재정렬(롱프레스)과 다중
> 선택(롱프레스)이 **같은 트리거를 실제로 공유한다** — 즉 이 오염
> 문제는 **Android 쪽에서 더 실재하는 문제**라는 것이 지금까지의
> 근거로 시사된다."
> — `research/ux-standards/patterns/multi-select.md`, "겹침" 섹션

| 플랫폼 | 이 3자 충돌이 실제로 발생하는가 | 근거 |
|---|---|---|
| iOS | **발생하지 않음** (1st-party 앱 설계 기준) | 다중 선택 진입이 버튼(Select) 기반이라 롱프레스와 트리거를 공유하지 않음 |
| Android | **발생함** | 재정렬(`isLongPressDragEnabled` 기본값 `true`)과 다중 선택(Google Photos/Files 소비자 앱)이 같은 롱프레스를 공유 |

**따라서 이 문서가 설계하는 해소 규칙은 실질적으로 Android(및 Android와
동일한 방식으로 세 기능을 한 항목에 몰아넣기로 선택한 웹 구현)에
적용된다.** iOS 스타일로 다중 선택을 버튼 진입으로 분리하면 이 문서
전체가 불필요해진다 — 그 선택지 자체가 유효한 회피책이라는 점을 먼저
밝혀 둔다(이것도 이 프로젝트의 판단이 아니라 iOS가 실제로 그렇게 하고
있다는 관찰이다).

### 1-2. 컨텍스트 메뉴가 이미 확인해 둔 두 실전 해소 사례

`context-menu.md`의 "겹침" 섹션이 확인한 두 사례를 그대로 인용한다 —
재조사하지 않는다.

**사례 A — iOS 홈 화면: 시간 기반 확전(escalation) + 타겟 분리**

> "아이콘 위 롱프레스는 먼저 컨텍스트 메뉴(Quick Actions)를 연다.
> 사용자가 메뉴에서 아무것도 고르지 않고 계속 누르고 있으면, 그 누름이
> 지속된 시간이 임계값을 넘는 순간 전체 아이콘이 흔들리는 재배치
> (jiggle) 모드로 확전된다 — 시간을 두 번째 판정축으로 쓴다."
> — `research/ux-standards/patterns/context-menu.md`, 사례 A
> (원출처: [Apple Support, Perform quick actions on iPhone](https://support.apple.com/guide/iphone/perform-quick-actions-iphcc8f419db/ios))

**사례 B — Android Pixel 런처: 이동 여부 기반 분기**

> "같은 롱프레스라도 손가락을 뗄 때까지 움직이지 않았으면 바로가기
> 메뉴, 떼기 전에 이동(드래그)했으면 앱을 옮기는 동작으로 갈린다 —
> 시간이 아니라 이동 여부/거리를 판정축으로 쓴다."
> — `research/ux-standards/patterns/context-menu.md`, 사례 B
> (원출처: [Pixel Phone Help, Home screen](https://support.google.com/pixelphone/answer/2781850?hl=en))

**둘 다 2지 분기만 실증한다는 한계**: 사례 A는 {컨텍스트 메뉴 ↔ 재배치}
둘 중 하나를, 사례 B는 {바로가기 메뉴 ↔ 이동} 둘 중 하나를 가른다.
이 프로젝트가 풀어야 하는 건 3지 분기(재정렬/다중선택/컨텍스트메뉴)다
— **어느 플랫폼도 이 정확한 3자 조합의 실전 사례를 갖고 있지 않다.**
2번에서 두 사례를 어떻게 조합하는지, 그리고 조합 자체가 왜 필요한지를
명시한다.

---

## 2. 이 프로젝트가 채택하는 해소 규칙

### 2-1. 설계 결정과 그 근거

**1단계 분기축 = 이동 여부/거리 (사례 B 기반)**

손가락을 뗄 때까지 8px 넘게 움직였는지를 먼저 본다. 움직였으면
재정렬(drag)이 무조건 이긴다 — 나머지 둘(다중 선택, 컨텍스트 메뉴)은
애초에 후보에서 탈락한다.

**왜 이걸 1단계로 두는가**: 사례 B(Pixel 런처)가 실증한 축일 뿐 아니라,
이 프로젝트의 매트릭스(CONFLICTS.md) 자체가 C6/C9/C10에서 이미
"움직임 여부/거리"를 1차 판정축으로 쓰고 있다 — 특히 C6의 해소 코드는
`pointermove`에서 8px(`movedBeyond(8)`)를 넘으면 롱프레스 타이머 자체를
취소하도록 되어 있다. 이 프로젝트 안에서 이미 확립된 규약과 정확히
같은 숫자, 같은 로직을 재사용하는 것이다 — 새 숫자를 지어내지 않았다.

**2단계 분기축 = 시간 확전 (사례 A의 구조를 차용, 목적지만 다르게)**

1단계에서 살아남은 경우(8px 미만으로 유지된 채 손가락을 대고 있는
상태)에 한해, **누르고 있는 시간**으로 컨텍스트 메뉴와 다중 선택을
가른다:

- 500ms(C6 실측 근거, Android `contextmenu` 494–513ms에 맞춘 값)에
  도달하면 컨텍스트 메뉴가 뜬다.
- 사용자가 메뉴에서 아무 것도 고르지 않고 **계속 누르고 있으면**,
  추가 500ms(합계 1000ms 시점)에 컨텍스트 메뉴가 다중 선택 모드로
  **확전**된다 — 사례 A(iOS 홈 화면)가 실증한 "먼저 메뉴, 계속 누르면
  더 강한 모드로 전환"이라는 **구조**를 그대로 가져온 것이다.

**왜 두 사례를 섞었는가 (사용자가 요구한 설명)**: 1번에서 밝혔듯
어느 사례도 3지 분기를 실증하지 않는다. 사례 B는 "정지 상태"라는
하나의 결과만 만들 뿐 그 정지 상태 내부를 컨텍스트 메뉴와 다중 선택
둘로 다시 가르는 방법을 보여주지 않는다. 사례 A는 정확히 그런 종류의
"정지 상태를 둘로 가르는" 구조(짧게 누르면 A, 계속 누르면 B로 전환)를
갖고 있다. 그래서 **사례 B로 1단계(움직임 vs 정지)를 가르고, 그 정지
쪽 결과 안에서 사례 A의 구조로 2단계(짧은 시간 vs 긴 시간)를 다시
가른다** — 두 사례를 순차적으로 합성했지, 뒤섞어 하나로 뭉갠 게 아니다.

**이 합성 자체, 그리고 "1000ms"라는 두 번째 시간 임계값은 이 프로젝트의
설계 판단이다.** 사례 A의 원문(Apple Support)은 확전이 일어나는 정확한
ms 수치를 공개하지 않는다(`context-menu.md`에 이미 🚧 미확정으로
표시됨). 500ms의 정수배(500+500)를 택한 것은 "C6이 이미 쓰는 500ms
단위를 그대로 두 번 쓴다"는 내부 일관성 이상의 근거가 없다 — 실기기
계측으로 검증된 값이 아니다.

### 2-2. §3 모델로 명시한 선언

```
recognizers:

  dragReorder:
    activation_distance: 8        # px — Android touch slop, C6/research/c10-sources.md 재사용
    axis: free                     # 재정렬은 리스트 축(보통 세로)으로 제한하는 게 실무적으로
                                    # 맞겠지만, 축 제한 자체는 C3/C10의 몫이지 이 문서의 몫이
                                    # 아니다 — 여기서는 값을 확정하지 않는다 (🚧 미확정)
    relations:
      blockedBy: []
      requireFailureOf: []
      simultaneousWith: []
    # 승리 조건: pointerdown 이후 pointerup 전에 8px 초과 이동이 한 번이라도
    # 발생하면 즉시 승리, 나머지 두 인식기를 취소한다.

  contextMenu:
    activation_delay: 500          # ms — C6 실측(Android contextmenu 494–513ms, n=73)
    activation_distance_cap: 8     # 이 값을 넘으면 dragReorder에 패배(취소)
    relations:
      blockedBy: [dragReorder]
      requireFailureOf: []
      simultaneousWith: []
    # 승리 조건: 500ms 시점에 8px 이내로 정지 상태 유지 중이면 발화.
    # 발화 후에도 계속 눌려 있으면 escalatesTo로 이관한다 (아래 참조).

  multiSelect:
    activation_delay: 1000         # ms — 🚧 [이 프로젝트의 설계 판단], 실기기 미검증
    activation_distance_cap: 8
    relations:
      blockedBy: [dragReorder]
      requireFailureOf: []
      escalatesFrom: [contextMenu] # ⚠ §3 원 모델에 없는 새 relation — 아래 설명 참조
    # 승리 조건: contextMenu가 먼저 발화했고(500ms), 사용자가 메뉴에서
    # 아무 것도 고르지 않은 채 1000ms까지 8px 이내로 계속 누르고 있으면
    # contextMenu를 취소하고 multiSelect로 전환한다.
```

**`escalatesFrom`에 대한 정직한 표시**: `research/ux-standards/patterns/ux-standards-architecture.md`
§3이 정의한 relations는 `requireFailureOf`/`blockedBy`/`simultaneousWith`
세 가지뿐이다. "먼저 발화했던 인식기를 취소하고 다른 인식기로 넘긴다"는
동작(에스컬레이션)은 이 세 가지 중 어느 것으로도 정확히 표현되지 않는다
— `requireFailureOf`는 "다른 게 탈락해야 활성화"인데, 여기서는 반대로
contextMenu가 **성공(발화)해야** multiSelect가 이어받는다. 그래서
`escalatesFrom`이라는 새 relation을 여기서 도입했다 — **이건 §3
모델의 확장이며, 원본에 없던 것을 이 문서가 추가했다는 사실을 숨기지
않는다.** 이 확장이 타당한지는 검증되지 않았다 — 8번(오염 방지) 작업
전체가 끝난 뒤 별도로 재검토가 필요하다.

---

## 3. 라벨

| 요소 | 라벨 | 근거/사유 |
|---|---|---|
| 1단계 분기축으로 "이동 여부"를 쓴다는 결정 | [표준] (상속) | `context-menu.md` 사례 B, 원출처 Google 공식 지원 문서(`context-menu.md`에서 이미 [표준]으로 라벨됨) — 그 라벨을 그대로 물려받는다 |
| 2단계에서 "시간 확전" 구조를 쓴다는 결정 | [표준] (상속) | `context-menu.md` 사례 A, 원출처 Apple 공식 지원 문서(마찬가지로 [표준] 상속) — 단, 그 사례의 목적지(재배치 모드)는 여기서 다중 선택으로 바뀌었다는 점은 아래 항목에서 별도 표시 |
| 8px, 500ms라는 구체적 수치 | 이 프로젝트 자체 실측 (C6, CONFLICTS.md) — [표준]/[관성]/[관행]/[미확정] 4라벨 체계 밖 | C6는 이 프로젝트가 실기기로 직접 측정한 값이다. 외부 플랫폼 문서의 권위를 인용하는 §4 라벨 체계와는 성격이 다른, "우리가 이미 검증해 둔 값"이라는 세 번째 근거 유형이다 |
| "사례 A의 구조를 다중 선택이라는 다른 목적지에 적용한다"는 합성 | **[이 프로젝트의 설계 판단]** | 어느 플랫폼도 이 정확한 3지 조합을 실증하지 않음. 명시적으로 이 프로젝트가 내린 판단이다 |
| 두 번째 시간 임계값(1000ms, 즉 500ms 확전 간격) | **[이 프로젝트의 설계 판단]**, 🚧 미확정 (실기기 미검증) | 사례 A 원문에 수치가 없음. C6의 500ms를 그대로 두 번 쓴 것 이상의 근거 없음 |
| `escalatesFrom` relation 자체 | **[이 프로젝트의 설계 판단]** | §3 원 모델(`requireFailureOf`/`blockedBy`/`simultaneousWith`)에 없는 확장 |
| `dragReorder`의 `axis` 값 | 🚧 미확정 | 이 문서가 정할 범위가 아님(C3/C10의 몫) |

**업계 표준으로 포장하지 않는다는 원칙 재확인**: 위 표에서
[이 프로젝트의 설계 판단]으로 명시된 항목은 iOS도 Android도 실제로
이렇게 하고 있다는 근거가 없다. Apple/Google 문서를 인용했다고 해서
그 조합 자체가 검증됐다는 뜻이 아니다.

---

## 4. 코드 형태의 예시 — 자체 점검일 뿐, 런타임 검증 아님

```js
// interaction-doctor 예시 — long-press triple conflict resolver
// 상태: 자체 점검(self-review)만 완료. §5.5 기준 런타임 검증 아님.
// 실제 기기/브라우저에서 이 로직이 의도대로 동작하는지는
// 아직 아무 도구로도 확인하지 않았다. Playwright 검증은 다음 단계.

const MOVE_THRESHOLD_PX = 8       // C6 / research/c10-sources.md
const CONTEXT_MENU_DELAY_MS = 500 // C6 실측 (Android contextmenu 494–513ms)
const ESCALATE_DELAY_MS = 1000    // 🚧 이 프로젝트의 설계 판단, 미검증

function attachTripleConflictResolver(el, { onReorder, onContextMenu, onMultiSelect }) {
	let startX = 0, startY = 0
	let moved = false
	let contextMenuTimer = null
	let escalateTimer = null
	let contextMenuFired = false

	el.addEventListener("pointerdown", (e) => {
		startX = e.clientX
		startY = e.clientY
		moved = false
		contextMenuFired = false

		contextMenuTimer = setTimeout(() => {
			if (!moved) {
				contextMenuFired = true
				onContextMenu(e)
				// 확전 타이머: 메뉴가 뜬 뒤에도 계속 눌려 있으면 escalatesFrom
				escalateTimer = setTimeout(() => {
					if (!moved) {
						onMultiSelect(e) // contextMenu를 다중 선택으로 대체
					}
				}, ESCALATE_DELAY_MS - CONTEXT_MENU_DELAY_MS)
			}
		}, CONTEXT_MENU_DELAY_MS)
	})

	el.addEventListener("pointermove", (e) => {
		if (moved) return
		const dx = e.clientX - startX
		const dy = e.clientY - startY
		if (Math.hypot(dx, dy) > MOVE_THRESHOLD_PX) {
			moved = true
			clearTimeout(contextMenuTimer)
			clearTimeout(escalateTimer)
			if (!contextMenuFired) {
				onReorder(e) // dragReorder 승리 — blockedBy 관계의 실제 구현
			}
			// contextMenuFired가 이미 true인 상태에서 8px을 넘으면 어떻게
			// 되어야 하는지는 이 문서가 답하지 않는다 — 🚧 미확정
			// (메뉴가 뜬 뒤의 이동은 사례 A/B 어디에도 없는 네 번째 케이스)
		}
	})

	;["pointerup", "pointercancel"].forEach((type) => {
		el.addEventListener(type, () => {
			clearTimeout(contextMenuTimer)
			clearTimeout(escalateTimer)
		})
	})
}
```

**이 코드에 대한 정직한 한계 표시**:

- `MOVE_THRESHOLD_PX`, `CONTEXT_MENU_DELAY_MS`는 C6 실측값을 그대로
  가져왔다는 근거가 있다. `ESCALATE_DELAY_MS`는 없다 — 주석에 그대로
  표시해 뒀다.
- 위 §2-2에서 이미 지적한 "메뉴가 뜬 뒤에 8px 넘게 움직이면 어떻게
  되는가"라는 네 번째 케이스는 사례 A에도 사례 B에도 없다. 코드
  주석에 미확정으로 남겨 뒀다 — 임의로 동작을 정해 채우지 않았다.
- **이건 §5.5 기준 자체 점검(self-review)이다.** 선언(§2-2)과 코드가
  논리적으로 어긋나지 않는지만 재검토했을 뿐, 실제 기기나 브라우저에서
  손가락으로 눌러 본 적이 없다. "검증됨"이라고 말하지 않는다.
- 실행 도구(Playwright 등)로 실제 터치 이벤트를 재현해 이 로직이
  의도한 대로 동작하는지 확인하는 건 **이 문서의 다음 단계**이며,
  아직 하지 않았다.

---

## 5. 런타임 검증 결과 — §5.5 기준 "검증됨"으로 승격되는 부분

**§4의 코드를 실제로 동작하는 페이지로 옮기고 Chromium(Playwright)에서
실제 포인터 이벤트를 흘려 확인했다.** `bottom-sheet-scroll-drag.md`의
검증과 같은 절차를 따른다 — 아래에서 "검증됨"이라고 쓴 부분만 §5.5
기준 런타임 검증을 통과한 것이고, 나머지(1000ms라는 숫자가 실제
사용자 경험으로 옳은지 등)는 여전히 미확정이다.

**환경**: Chromium(Playwright 1.62.1, headless), 마우스로 시뮬레이션한
`pointerdown`/`pointermove`/`pointerup` 시퀀스(일부는 `pointerId`를
직접 지정한 합성 `PointerEvent`). 재현 페이지:
`tools/nested/long-press-triple-conflict-verify.html`(`?buggy=1`로
아래 5-0의 결함 재현 모드 진입). 원시 결과:
`research/ux-standards/nested-interactions/verification/triple-conflict-results.json`.
타이밍은 페이지 안에서 `performance.now()`로 각 콜백 호출 시점을
`pointerdown` 시점 대비 상대값으로 기록했다 — Node 쪽 `Date.now()`가
아니라 브라우저 자체 시계로 잰 값이다.

### 5-0. 코드를 다시 의심하며 읽은 결과 — 페이지를 만들기 전에 찾은 것

작업 지시대로 페이지를 만들기 전에 §4 코드를 처음부터 다시 의심하며
읽었다. 두 가지를 코드 검토만으로 예상했고, 둘 다 실제로 재현됐다.

**의심 1(bottom-sheet 검증 때와 같은 종류 — 재현됨)**: `pointermove`
핸들러가 `pointerdown`이 실제로 있었는지 확인하지 않는다. `startX`/
`startY`/`moved`/`contextMenuFired`는 `pointerdown` 안에서만 초기화되는
공유 클로저 변수라서, `pointerdown` 없이 `pointermove`만 발생해도
`dx=clientX-0, dy=clientY-0`로 계산되고, 화면 대부분의 지점에서
`Math.hypot(dx,dy)`가 8px을 가볍게 넘는다.

| 항목 | 값 |
|---|---|
| 재현 조작 | `page.mouse.move(x, y)` 단 1회, `down`/`up` 없음(`?buggy=1`로 가드 비활성화) |
| 호출 전 카운트 | `onReorder=0` |
| 호출 후 카운트 | **`onReorder=1`** |

**검증됨**: 클릭 없는 호버만으로 `onReorder`가 스퓨리어스하게
호출된다. `armed` 플래그 한 줄(`pointerdown`에서 `true`,
`pointerup`/`pointercancel`에서 `false`)로 검증 페이지에서만 고쳤다 —
§4 코드 블록 자체는 소급 수정하지 않는다(위 원칙 그대로).

**의심 2(작업 지시 1번이 지목한 "여러 손가락/빠른 연속 클릭" —
재현됨, 아래 5-5)**: `pointerId`를 전혀 추적하지 않는다. 이건 tasks
a–e(전부 단일 포인터)에는 필요 없는 수정이라 **고치지 않고 그대로
관찰만 했다** — 5-5 참조.

### 5-1. 검증 a — 8px 미만으로 500ms 유지 → onContextMenu 1회

| 항목 | 값 |
|---|---|
| 조작 | `pointerdown` 후 이동 없이 550ms(벽시계) 대기 |
| `onContextMenu` 호출 시점(페이지 자체 시계, `pointerdown` 대비) | **501.2ms** |
| 호출 횟수 | 1 |
| `onReorder`/`onMultiSelect` 호출 횟수 | 0 / 0 |

**검증됨**: `CONTEXT_MENU_DELAY_MS = 500`으로 선언된 타이머가 실제
브라우저에서 501.2ms(오차 +1.2ms, `setTimeout`의 통상적 지연 범위
안)에 정확히 1회 발동한다.

### 5-2. 검증 b — 이어서 1000ms까지 유지 → onMultiSelect 1회, onContextMenu는 재호출 안 됨

| 항목 | 값 |
|---|---|
| 조작 | `pointerdown` 후 이동/해제 없이 1050ms(벽시계) 대기 |
| `onContextMenu` 호출 시점 | 501.5ms (1회) |
| `onMultiSelect` 호출 시점 | **1003.1ms** (1회) |
| `onContextMenu` 최종 호출 횟수 | **1**(재호출 안 됨) |

**검증됨**: `ESCALATE_DELAY_MS - CONTEXT_MENU_DELAY_MS = 500`으로
스케줄된 두 번째 타이머가 1003.1ms(오차 +3.1ms)에 발동하고,
`onContextMenu`는 확전 이후에도 다시 불리지 않는다 — §2-2가 선언한
"contextMenu를 multiSelect로 대체"가 실제로 대체(재호출 없음)로
동작한다.

### 5-3. 검증 c — 300ms 시점에 8px 초과 이동 → onReorder 즉시, 타이머는 실제로 취소됨

| 항목 | 값 |
|---|---|
| 조작 | `pointerdown` → 300ms 대기 → 30px 이동 → 추가로 400ms(총 ~700ms) 더 대기 |
| `onReorder` 호출 시점 | **326.1ms**(300ms 대기 + 이동 디스패치·처리 오버헤드 ~26ms) |
| 이동 직후 `onContextMenu` 횟수 | 0 |
| **700ms 시점까지 더 기다린 뒤** `onContextMenu` 횟수 | **여전히 0** |

**검증됨**: 이동이 임계값을 넘는 순간 `onReorder`가 즉시 호출되고,
원래 500ms에 발동했어야 할 `contextMenuTimer`는 **실제로 취소되어
늦게라도 발동하지 않는다.** "타이머가 실제로 꼬여서 늦게 뜨는" 실패
모드가 없다는 것까지 확인했다 — 단순히 "이동 시점에 아직 안 떴다"만
본 게 아니라 그 이후까지 지켜봤다.

### 5-4. 관찰 d — 메뉴가 이미 뜬 뒤 8px 초과 이동 (§4가 답하지 않은 네 번째 케이스, 관찰만)

작업 지시대로 **정답을 정하지 않고 코드가 실제로 무엇을 하는지만
기록한다.**

| 항목 | 값 |
|---|---|
| 조작 | `pointerdown` → 550ms 대기(`onContextMenu` 발동) → 30px 이동 → 추가로 600ms(총 ~1160ms) 더 대기 |
| 메뉴 발동 시점 | 501.7ms |
| 이동 직후 상태 | `onContextMenu` 여전히 1회, `onReorder`/`onMultiSelect` 여전히 0회 — **이동 자체가 아무 콜백도 부르지 않았다** |
| 관찰 종료 시점(~1160ms)까지 상태 | 변화 없음 — `onMultiSelect`는 끝내 호출되지 않았다 |

**관찰된 사실(검증도 미검증도 아닌, 있는 그대로의 기록)**: 이동이
일어나면 `moved=true`가 설정되어 대기 중이던 `escalateTimer`가
`clearTimeout`으로 취소된다(그래서 1000ms 지점에 `onMultiSelect`가
안 뜬다) — 그러나 `onReorder`는 `if (!contextMenuFired)` 가드 때문에
호출되지 않는다(메뉴가 이미 떴으므로 `contextMenuFired=true`). **결과:
이 이동은 어떤 콜백도 발생시키지 않고, 단지 예정돼 있던 확전만
조용히 취소시킨다.** 이게 옳은 동작인지는 이 문서도, §4도 판단하지
않는다 — 코드가 실제로 이렇게 동작한다는 사실만 기록한다.

### 5-5. 관찰 F(보너스, tasks a–e 밖) — 겹치는 포인터(여러 손가락/빠른 연속 클릭)

작업 지시 1번이 미리 의심하라고 한 항목을 실제로 재현했다. tasks
a–e는 전부 단일 포인터라 이 수정 없이도 통과하므로, **고치지 않고
그대로 관찰만 했다.**

| 항목 | 값 |
|---|---|
| 조작 | `pointerId=1`로 `pointerdown`(해제 안 함) → 200ms 후 `pointerId=2`로 `pointerdown`(첫 번째를 해제하지 않은 채) → 1100ms 대기 |
| `onContextMenu` 호출 횟수 | **2** (297.8ms, 501.5ms) |
| `onMultiSelect` 호출 횟수 | **2** (800.0ms, 1003.1ms) |
| 스크린샷 | `research/ux-standards/nested-interactions/verification/triple-f-overlapping-pointerids.png` |

**검증됨(결함으로서)**: 설계 의도는 한 제스처당 `onContextMenu` 1회,
`onMultiSelect` 1회다. 두 번째 `pointerdown`이 먼저 것을 해제하지 않은
채 들어오면 `contextMenuTimer`/`escalateTimer` 참조가 두 번째
`pointerdown`에 덮어써지고, **첫 번째 제스처가 예약해 둔 타이머는
정리되지 않은 채 그대로 살아남아** 나중에 각각 발동한다 — 그 결과
두 콜백이 모두 두 번씩 불린다. 이건 §4가 예상하지 못한, 코드 검토
단계에서 의심했던 그대로의 결함이며, **§4도 이 검증 페이지도 고치지
않았다** — tasks a–e에 필요하지 않았고, 고치는 순간 "이 정확한 3자
조합을 실증하는 사례가 없다"는 §1의 한계와 마찬가지로 새로운 설계
판단(예: 어느 포인터를 우선할 것인가)이 필요해지기 때문이다. 이건
8번(오염 방지) 작업 전체가 끝난 뒤, 또는 별도 요청 시 다룰 후보로
남긴다.

### 5-6. "타이머가 맞게 도는가"와 "1000ms가 맞는 값인가"는 다른 질문이다

작업 지시가 요구한 구분을 명시적으로 적는다.

| 질문 | 이번 검증으로 답이 나오는가 | 결과 |
|---|---|---|
| `ESCALATE_DELAY_MS=1000`으로 선언하면 실제 브라우저가 1000ms 근처에서 정확히 그 타이머를 발동시키는가(코드/브라우저 동작의 검증) | **예 — §5.5 기준 검증 가능한 질문** | **검증됨**: 1003.1ms에 1회 발동(5-2) |
| 1000ms(메뉴 노출 후 추가 500ms)가 실제 사용자에게 "적절한 확전 시점"으로 느껴지는가(UX 판단) | **아니오 — 이 프로젝트가 가진 도구로 검증 불가** | 여전히 **🚧 미확정**, §3 라벨 표의 "[이 프로젝트의 설계 판단], 실기기 미검증"이 그대로 유지됨 |

**둘을 섞지 않는다**: 전자가 "검증됨"이 됐다고 해서 후자가 검증된
것처럼 말하지 않는다 — 1000ms라는 수치가 정확히 1000ms에 발동하는
것과, 그 1000ms가 사용자 경험상 옳은 값인지는 완전히 다른 질문이고,
이번 Playwright 검증은 전자에만 답할 수 있다. 후자는 실제 사용자를
대상으로 한 사용성 테스트가 있어야 하며, 이건 §5.5가 말하는 런타임
검증의 범위 밖이다.

---

## 다음 단계

- 유형 B(바텀시트 자체 드래그 vs 내부 스크롤)와 유형 C(사이드 드로어
  vs 브라우저 뒤로가기)는 이후 각각 `bottom-sheet-scroll-drag.md`,
  `side-drawer-back-gesture.md`로 완료됨.
- 이 문서의 §2 규칙에 대한 런타임 검증(Playwright)은 §5에서 완료됨.
  다만 5-5(겹치는 포인터 결함)는 발견만 되고 해소되지 않았다 — 별도
  요청 시 진행.
- §5-6이 구분한 대로, 1000ms라는 수치 자체의 UX 적절성은 이 프로젝트가
  검증할 수 있는 범위 밖으로 남는다.
