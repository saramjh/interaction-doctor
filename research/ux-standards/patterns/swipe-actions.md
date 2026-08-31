# Component: Swipe Actions (좌우 스와이프로 액션 노출)

절차는 `reorderable-list.md`와 동일: `ux-standards-architecture.md`
§1(우선순위 5단계) → §2(식별 신호) → §4(라벨) 순서를 따른다. 검증 방법도
동일하게 **검색을 통한 1차 문서 확인**이며, 실기기 직접 관찰이 아니다 —
이 구분은 매번 라벨 옆에 명시한다.

---

## 식별 신호 (§2)

레퍼런스/디자인만 왔을 때 이게 재정렬이 아니라 스와이프 액션인지 구분하는
시각적 단서.

```
- 항목 옆(보통 오른쪽 끝, 때로는 양쪽)에 X/휴지통/보관함 아이콘이
  평소엔 숨어 있다가 스와이프해야 드러나는 디자인 → 스와이프 액션
- 아이콘이 항상 보이고 카드 자체는 안 움직인다 → 이건 스와이프 액션이
  아니라 그냥 보이는 보조 액션 버튼(제스처 불필요)
- 카드 전체 폭이 좌우로 밀리면서 배경색이 드러나는 디자인(빨강=삭제 등)
  → 전체 스와이프(swipe to delete)형
- 카드는 그대로 있고 그 뒤에서 버튼 폭만큼만 아이콘이 살짝 드러나는
  디자인 → 부분 노출(swipe to reveal)형. 아래 "전체 vs 부분" 참조
- 6-dot/hamburger 핸들이 같이 있으면 → reorderable-list.md와 신호가
  겹친다. §1의 5순위(사용자에게 재확인)로 떨어뜨린다
```

---

## 1. 커밋 거리 — 얼마나 밀어야 액션이 확정되는가

### Android — 검색 확인 결과

Android의 공식 리스트 스와이프 API(`RecyclerView` + `ItemTouchHelper`)는
정확한 수치를 문서화하고 있다:

> `getSwipeThreshold(RecyclerView.ViewHolder viewHolder)` — "Returns the
> fraction that the user should move the View to be considered as swiped.
> The fraction is calculated with respect to RecyclerView's bounds.
> **Default value is .5f**, which means, to swipe a View, user must move
> the View at least half of RecyclerView's width or height, depending on
> the swipe direction."
> — [Android Developers, `ItemTouchHelper.Callback#getSwipeThreshold()`](https://developer.android.com/reference/androidx/recyclerview/widget/ItemTouchHelper.Callback#getSwipeThreshold(androidx.recyclerview.widget.RecyclerView.ViewHolder))

**[표준].** Android 플랫폼 API 레벨의 기본 커밋 거리는 **항목 폭(또는
높이)의 50%**다. 이건 정확한 수치가 공식 문서에 명시된 몇 안 되는
사례다.

### iOS — 검색 확인 결과

Apple의 `UISwipeActionsConfiguration` 공식 문서는 **거리(px/%)를 전혀
공개하지 않는다.** 대신 "완전히 스와이프했는가"를 불리언 스위치로만
규정한다 (아래 2번 참조). 정확한 px/% 임계값은 **🚧 미확정** — 공식
문서에서 검색으로 찾지 못했다. Apple은 이 종류의 내부 상수(예:
`research/c10-sources.md`의 Android touch slop처럼)를 iOS 쪽에서는
거의 공개하지 않는다는 패턴이 여기서도 반복된다.

### 판정

| 판단 | 라벨 | 근거 |
|---|---|---|
| Android 플랫폼 API의 공식 커밋 거리 기본값은 항목 크기의 50% | [표준] | `ItemTouchHelper.Callback#getSwipeThreshold()` 공식 문서, 수치 명시 |
| iOS의 정확한 커밋 거리(px/%) | **🚧 미확정** | 공식 문서에 수치 없음. 있는 건 "완전 스와이프냐 아니냐"라는 불리언뿐 |

---

## 2. 전체 스와이프 vs 부분 노출 — 같은 컴포넌트의 변형인가

### iOS — 검색 확인 결과 (API 레벨에서 명시적으로 하나의 컴포넌트로 통합)

Apple의 공식 API 문서가 이 질문에 직접 답한다. 하나의 프로퍼티가 두
동작을 스위치로 연결한다:

> `performsFirstActionWithFullSwipe` — "A Boolean value indicating
> whether a full swipe automatically performs the first action." /
> "When this property is set to `true`, a full swipe in the row performs
> the first action listed in the `actions` property. **The default value
> of this property is `true`.**"
> — [Apple Developer Documentation, `UISwipeActionsConfiguration.performsFirstActionWithFullSwipe`](https://developer.apple.com/documentation/uikit/uiswipeactionsconfiguration/performsfirstactionwithfullswipe)

**[표준].** 이건 이 조사의 핵심 발견이다: iOS는 "부분 노출로 버튼을
드러낸 뒤 탭해서 확정"과 "끝까지 밀면 즉시 확정"을 **같은 컴포넌트의
연속된 두 결과**로 취급한다. 별도 컴포넌트가 아니라 하나의 제스처가 밀린
거리에 따라 다른 결과를 내는 것 — 부분(버튼 노출, 대기)과 전체(첫 번째
액션 즉시 실행)가 동일한 인식기의 두 종점이다. 개발자는 이 스위치를 꺼서
"부분 노출만 허용, 항상 탭으로 확정"하게 만들 수도 있다.

방향에 따라 다른 액션 집합을 등록하는 것도 API 레벨에서 명시적으로
분리되어 있다:

> `tableView(_:leadingSwipeActionsConfigurationForRowAt:)` — "Returns
> the swipe actions to display on the leading edge of the row."
> `tableView(_:trailingSwipeActionsConfigurationForRowAt:)` — "Returns
> the swipe actions to display on the trailing edge of the row."
> — [Apple Developer Documentation](https://developer.apple.com/documentation/uikit/uitableviewdelegate/tableview(_:leadingswipeactionsconfigurationforrowat:)) / [trailing 쪽](https://developer.apple.com/documentation/uikit/uitableviewdelegate/tableview(_:trailingswipeactionsconfigurationforrowat:))

**[표준].** 왼쪽 스와이프(trailing, LTR 기준)와 오른쪽 스와이프(leading)는
API 자체가 서로 다른 델리게이트 메서드로 분리해 둔 서로 다른 액션
집합이다 — 우연히 다른 게 아니라 플랫폼이 그렇게 설계했다.

### Android — 검색 확인 결과 (플랫폼 API에는 부분-노출 개념이 약함)

`ItemTouchHelper`의 공식 문서 전체에서 "부분 노출 후 탭으로 확정"에
해당하는 프로퍼티나 콜백은 검색으로 찾지 못했다. `onSwiped(ViewHolder,
direction)`만 있고, 이건 50% 임계값(또는 속도 임계값, 3번 참조)을 넘겨
"완전히 스와이프됨"이 확정된 뒤에만 호출된다.

> `onSwiped(RecyclerView.ViewHolder viewHolder, int direction)` — "Called
> when a ViewHolder is swiped by the user."
> — [Android Developers, `ItemTouchHelper.Callback#onSwiped()`](https://developer.android.com/reference/androidx/recyclerview/widget/ItemTouchHelper.Callback#onSwiped(androidx.recyclerview.widget.RecyclerView.ViewHolder,int))

**[표준] (API 레벨 확인) — 단, "Android가 부분 노출을 지원하지 않는다"는
뜻은 아니다.** `onChildDraw()` 콜백에서 개발자가 직접 배경 아이콘을
그리는 동안 특정 오프셋에서 손을 떼면 그 상태로 스냅하도록 직접 구현하는
건 가능하다 — 다만 그게 **플랫폼이 기본 제공하는 프로퍼티**는 아니고,
iOS의 `performsFirstActionWithFullSwipe`처럼 "이것만 끄면 부분 노출
모드"인 공식 스위치가 없다는 뜻이다.

Google의 1st-party 앱(Gmail)이 실제로 어느 쪽을 쓰는지는 공식 도움말이
답을 준다:

> "Swipe actions: When this setting is on, swipe left or right on a
> message in your messages list to delete it. From the general settings,
> you can change the right- or left-swipe to: archive, delete, mark as
> read/unread, move to a label, or snooze messages. **By default, you can
> swipe messages to the left or right to delete them** depending on which
> setting you chose as your default action."
> — [Gmail Help, Change your Gmail settings — Android](https://support.google.com/mail/answer/6562?co=GENIE.Platform%3DAndroid&hl=en)

**[관성] (Google 1st-party 앱 공식 도움말, 기기 미확인).** 이 문서 어디에도
"밀면 버튼 몇 개가 드러나고 그중 하나를 고른다"는 서술이 없다 —
방향(왼쪽/오른쪽)마다 **미리 정해진 액션 하나**가 실행되는 모델이다. 이건
iOS Mail의 "부분 노출 = 여러 버튼 메뉴"와 구조적으로 다르다(아래 3번).

Material Design(archived 공식 스펙)은 오히려 두 변형을 별개 명칭으로
구분해서 정의한다:

> **Dismiss**: "A dismiss gesture originates on a swipeable element, such
> as a list item or card, orthogonal to the direction of scrolling...
> The dismiss gesture is committed based on crossing a threshold."
> — [Material Design (archived), Patterns — Gestures](https://material.io/archive/guidelines/patterns/gestures.html)
>
> **Leave-behind**: "A leave-behind is an informative hint as to what
> swiping a list item away will do to that item. The leave-behind can
> transform into an action. Swiping on a list item from either direction
> will reveal an icon indicating the action. After swiping, a follow-up
> action can appear as a text button within the space of the list item."
> — [Material Design (archived), Lists — controls](https://material.io/archive/guidelines/components/lists-controls.html)

**[표준] (Google 공식 아카이브 스펙).** Material Design은 "Dismiss"(완전
제거, 임계값 기반 확정)와 "Leave-behind"(스와이프 후 아이콘/텍스트
버튼으로 대기, 사용자가 확정하거나 취소)를 **이름부터 다른 두 패턴**으로
문서화한다 — iOS처럼 한 프로퍼티의 두 종점이 아니라, Android/Material
쪽에서는 애초에 별도 개념으로 설계됐다는 뜻이다.

### 판정 — "같은 컴포넌트의 변형인가?"

| 판단 | 라벨 | 근거 |
|---|---|---|
| iOS는 전체 스와이프(즉시 확정)와 부분 노출(버튼 표시 후 탭)을 **하나의 API/컴포넌트의 두 결과**로 설계했다 | [표준] | `performsFirstActionWithFullSwipe` 하나가 이 둘을 스위치함 |
| Material Design(Android 계열)은 이 둘을 **Dismiss / Leave-behind라는 별도 이름의 두 패턴**으로 설계했다 | [표준] | archived 공식 스펙이 두 용어를 각각 정의 |
| 따라서 "같은 컴포넌트의 변형인지, 다른 컴포넌트인지"는 **플랫폼마다 답이 다르다** | [표준] (위 두 사실의 직접 귀결) | iOS=하나의 컴포넌트, Android/Material=개념적으로 별개 |
| Gmail이 실제로 부분 노출(여러 액션 중 선택)을 구현하는지 | **🚧 미확정** | 공식 도움말은 "방향당 액션 하나"만 서술 — 여러 버튼 노출 UI가 있는지는 이 문서로 확인 불가, 기기 관찰 필요 |

---

## 3. iOS 표준 사례 — Mail의 스와이프 삭제/보관/플래그

> "In a message list, do any of the following: Reveal a list of actions:
> **Slowly drag** a message to the left until the menu appears, then tap
> an item. Quickly use the rightmost action: **Swipe all the way** to the
> left. Reveal other actions: **Swipe right**."
> — [Apple Support, Organize your email in mailboxes (iPhone)](https://support.apple.com/guide/iphone/organize-your-email-iph376ef8aa3/ios)

> "Swipe left quickly over a single email." (즉시 삭제) / "You can also
> swipe left on individual emails in a message list to delete a specific
> email." (밀어서 확정)
> — [Apple Support, Delete emails on your iPhone or iPad](https://support.apple.com/en-us/102428)

**[표준] (Apple 자사 지원 문서, 현재 유지 중).** 정리하면:

- **속도가 의미를 바꾼다**: 천천히 밀면(slowly drag) 메뉴가 드러나고
  멈춘 채 탭해서 고르는 모드, 빠르게 끝까지 밀면(swipe all the way /
  quickly) 첫 번째 액션이 즉시 실행되는 모드 — 이건 2번에서 확인한
  `performsFirstActionWithFullSwipe`가 실제 Mail 앱에서 정확히 이렇게
  구현돼 있다는 [관성] 증거이기도 하다.
- **왼쪽과 오른쪽은 다른 메뉴다**: 왼쪽 스와이프는 "the menu"(삭제류 액션
  묶음), 오른쪽 스와이프는 "other actions"(플래그 등) — Mail 문서가
  둘을 명시적으로 구분해서 서술한다. 어느 쪽이 무슨 액션인지 구체적
  라벨(예: "플래그"라는 단어 자체)까지는 이 페이지에서 확인하지 못했다
  (**🚧 미확정** — 다른 지원 문서 페이지에 있을 수 있으나 이번 검색
  범위에서 못 찾음).

---

## 4. Android 표준 사례 — Gmail의 스와이프 액션 / Material 공식 문서

> "Swipe actions: ... swipe left or right on a message in your messages
> list to delete it. From the general settings, you can change the
> right- or left-swipe to: archive, delete, mark as read/unread, move to
> a label, or snooze messages."
> — [Gmail Help, Change your Gmail settings — Android](https://support.google.com/mail/answer/6562?co=GENIE.Platform%3DAndroid&hl=en)

**[관성] (Google 1st-party 앱 공식 도움말, 기기 미확인).** iOS Mail과
구조적으로 다른 점: Gmail은 왼쪽/오른쪽 각각에 **사용자가 설정에서 미리
고정한 액션 하나**를 배정하는 모델이다. iOS처럼 "부분 노출 시 여러 버튼
중 선택"이 아니라 "스와이프 = 정해진 그 액션"에 가깝다. 이 문서만으로
"부분 노출 UI가 아예 없다"고 확정할 수는 없다 — 없다는 걸 증명하는 건
있다는 걸 증명하는 것보다 어렵다. 이 지점은 **🚧 미확정**으로 남긴다.

Material Design 공식 스펙(archived)의 Dismiss/Leave-behind 정의는 3번
항목에 이미 인용했다 — 재인용하지 않는다.

---

## 5. 스와이프 도중 손을 떼면 어떻게 되는가

### Android — 검색 확인 결과 (거리 OR 속도, 둘 중 하나만 넘으면 확정)

50% 거리 임계값(1번) 외에, Android 공식 API는 **속도 기반 확정 경로**도
별도로 문서화한다 — 느리게 50%를 넘기지 못했어도 빠르게 튕기면(fling)
확정될 수 있다는 뜻:

> `getSwipeEscapeVelocity(float defaultValue)` — "Defines the minimum
> velocity which will be considered as a swipe action by the user. ...
> Keep in mind that ItemTouchHelper also checks the perpendicular
> velocity and makes sure current direction velocity is larger [than]
> the perpendicular one. Otherwise, user's movement is ambiguous."
> — [Android Developers, `ItemTouchHelper.Callback#getSwipeEscapeVelocity()`](https://developer.android.com/reference/androidx/recyclerview/widget/ItemTouchHelper.Callback#getSwipeEscapeVelocity(float))

**[표준].** 확정 조건은 "50% 이상 이동" **또는** "충분한 속도로 튕김" 중
하나 — 둘 다 못 넘기면 원위치로 스냅한다는 게 논리적 귀결이다(공식
문서가 "스냅백"이라는 단어를 직접 쓰지는 않지만, `onChildDraw`와
`clearView` 콜백 구조상 확정되지 않은 스와이프는 원래 위치로 애니메이션
복귀하는 것이 `ItemTouchHelper`의 기본 구현이다 — 이 마지막 문장은
API 문서의 구조적 귀결이며, "스냅백"이라는 단어 자체를 인용한 건 아니다).
애니메이션 길이는 상수로 공개되어 있다:

> `DEFAULT_SWIPE_ANIMATION_DURATION = 250` (밀리초, 스와이프 확정/취소
>애니메이션 길이)
> — [Android Developers, `ItemTouchHelper.Callback#DEFAULT_SWIPE_ANIMATION_DURATION`](https://developer.android.com/reference/androidx/recyclerview/widget/ItemTouchHelper.Callback#DEFAULT_SWIPE_ANIMATION_DURATION())

### iOS — 검색 확인 결과 (거리 기반 스위치만 공개, 속도 기반 여부 미확인)

`performsFirstActionWithFullSwipe`(2번)는 "완전히 끝까지 밀었는가"라는
거리/완주 기준만 언급한다. 속도(fling)만으로 완주 전에 확정되는지는
공식 문서에서 확인하지 못했다 — **🚧 미확정**.

### 판정

| 판단 | 라벨 | 근거 |
|---|---|---|
| Android는 "거리 임계값(50%) 또는 속도 임계값" 중 하나만 넘으면 확정, 둘 다 못 넘으면 스냅 복귀 | [표준] (확정 조건은 API 문서 직접 인용, "스냅백" 자체는 API 구조상의 귀결) | `getSwipeThreshold`, `getSwipeEscapeVelocity`, `DEFAULT_SWIPE_ANIMATION_DURATION` |
| iOS도 거리(완주 여부) 기반 확정 스위치는 있다 | [표준] | `performsFirstActionWithFullSwipe` |
| iOS가 속도(fling)만으로 완주 전에 확정을 허용하는지 | **🚧 미확정** | 공식 문서에서 확인 못 함 |

---

## 6. CONFLICTS.md 연결 — 새 실측 아님, 기존 실측을 그대로 적용

세로 스크롤 리스트 안에서 좌우 스와이프가 세로 스크롤·드래그와 축이
갈리는 문제는 **이 문서가 새로 확인할 대상이 아니다.** 이미 실기기로
측정되어 있다:

- [C9 — Drag ↔ Swipe](/CONFLICTS.md#c9--drag--swipe)
- [C12 — Swipe ↔ Scroll](/CONFLICTS.md#c12--swipe--scroll)

이 두 섹션의 `touch-action`/축 판정 실측값이 스와이프 액션 컴포넌트에도
그대로 적용된다는 **연결만** 여기 명시한다. 재측정하지 않는다.

추가로, 1~5번에서 확인한 "50% 커밋 거리"나 "완전 스와이프 스위치"는
브라우저의 `touch-action`이 관여하는 지점보다 상위(제스처가 이미
브라우저에 의해 "가로 이동"으로 판정된 *이후*, 어느 시점에 액션을
확정할지 결정하는) 레이어의 문제다 — 즉 C9/C12가 푸는 "이게 스크롤인가
스와이프인가"와 이 문서가 다루는 "스와이프로 판정된 뒤 얼마나 밀어야
확정인가"는 서로 다른 질문이라는 점을 분명히 해 둔다.

---

## 다음 문서와의 접점

이 컴포넌트는 트리거가 롱프레스가 아니라 수평 드래그이므로, 5/6번
(multi-select, context-menu)의 롱프레스 오염 문제와는 겹치지 않는다.
reorderable-list.md와는 "카드 옆 아이콘"이라는 시각 신호가 겹칠 수 있어
식별 신호 섹션에서 상호 참조만 남겼다 — 별도 해소 불필요.

---

## 출처 전체 목록

- [Android Developers — `ItemTouchHelper.Callback#getSwipeThreshold()`](https://developer.android.com/reference/androidx/recyclerview/widget/ItemTouchHelper.Callback#getSwipeThreshold(androidx.recyclerview.widget.RecyclerView.ViewHolder))
- [Android Developers — `ItemTouchHelper.Callback#getSwipeEscapeVelocity()`](https://developer.android.com/reference/androidx/recyclerview/widget/ItemTouchHelper.Callback#getSwipeEscapeVelocity(float))
- [Android Developers — `ItemTouchHelper.Callback#onSwiped()`](https://developer.android.com/reference/androidx/recyclerview/widget/ItemTouchHelper.Callback#onSwiped(androidx.recyclerview.widget.RecyclerView.ViewHolder,int))
- [Android Developers — `ItemTouchHelper.Callback#DEFAULT_SWIPE_ANIMATION_DURATION`](https://developer.android.com/reference/androidx/recyclerview/widget/ItemTouchHelper.Callback#DEFAULT_SWIPE_ANIMATION_DURATION())
- [Apple Developer Documentation — `UISwipeActionsConfiguration.performsFirstActionWithFullSwipe`](https://developer.apple.com/documentation/uikit/uiswipeactionsconfiguration/performsfirstactionwithfullswipe)
- [Apple Developer Documentation — `tableView(_:leadingSwipeActionsConfigurationForRowAt:)`](https://developer.apple.com/documentation/uikit/uitableviewdelegate/tableview(_:leadingswipeactionsconfigurationforrowat:))
- [Apple Developer Documentation — `tableView(_:trailingSwipeActionsConfigurationForRowAt:)`](https://developer.apple.com/documentation/uikit/uitableviewdelegate/tableview(_:trailingswipeactionsconfigurationforrowat:))
- [Apple Support — Organize your email in mailboxes on iPhone](https://support.apple.com/guide/iphone/organize-your-email-iph376ef8aa3/ios)
- [Apple Support — Delete emails on your iPhone or iPad](https://support.apple.com/en-us/102428)
- [Gmail Help — Change your Gmail settings (Android)](https://support.google.com/mail/answer/6562?co=GENIE.Platform%3DAndroid&hl=en)
- [Material Design (archived) — Patterns, Gestures](https://material.io/archive/guidelines/patterns/gestures.html)
- [Material Design (archived) — Lists, controls (Leave-behind 정의)](https://material.io/archive/guidelines/components/lists-controls.html)
- 확인 시도했으나 못 찾은 것: iOS의 정확한 스와이프 커밋 거리(px/%), iOS의
  속도 기반(fling) 조기 확정 여부, Gmail의 부분 노출(다중 버튼) UI 존재
  여부, Mail 왼쪽/오른쪽 스와이프의 정확한 액션 라벨 — 전부 **🚧
  미확정**으로 위 본문에 개별 명시했다.

**방법론 고지**: `reorderable-list.md`와 동일하게, 이 문서의 [관성]
라벨은 전부 "공식 지원 문서 검색 확인"이며 실기기 직접 관찰이 아니다.
