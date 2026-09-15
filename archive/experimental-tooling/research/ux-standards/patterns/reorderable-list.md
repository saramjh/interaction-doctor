# Component: Reorderable List (재정렬 가능한 리스트)

절차: `ux-standards-architecture.md` §1(우선순위 5단계) → §2(식별 신호) →
§4(라벨) 순서를 그대로 따른다. 이 문서가 다루는 건 §1의 3순위(OS/1st-party
앱 관성)이며, 검증 방법은 **검색을 통한 1차 문서 확인**이다 — 실제 기기
직접 관찰이 아니다. 이 차이를 §5.5의 자체점검/런타임검증 구분과 동일한
방식으로 매번 명시한다.

---

## 식별 신호 (§2)

레퍼런스/디자인만 왔을 때 이 컴포넌트인지, 그리고 3-A/3-B 중 어느 쪽인지
판별하는 시각적 단서.

```
- 항목 오른쪽(또는 왼쪽)에 6-dot/hamburger 아이콘, 다른 액션과 분리된
  별도 터치 영역 → 3-A. 핸들 있음
- 아이콘 없이 카드/행 전체가 하나의 터치 타겟 → 3-B. 핸들 없음
- "Edit" / "편집" 버튼이 화면에 별도로 존재하고, 그걸 눌러야 재정렬
  아이콘이나 삭제 아이콘이 나타나는 디자인 → 편집 모드 게이팅 있음
  (핸들 유무와는 독립적인 축 — 아래 3-A/3-B 안에서 각각 있을 수 있음)
- 항목에 X/휴지통 아이콘 + 좌우 여백 → 스와이프 삭제일 가능성,
  swipe-actions.md 쪽으로 재확인
- 리스트가 가로 스크롤 + 카드가 균일 폭 → carousel.md일 가능성,
  재정렬이 아닐 수 있음
```

두 신호가 겹치면(핸들도 있고 편집 모드도 없는데 스와이프 삭제도 될 것 같은
디자인) §1의 5순위로 떨어진다 — 사용자에게 되묻는다.

---

## 3-A. 핸들 있음 — 별도 아이콘이 드래그 전용 타겟

### iOS — 검색 확인 결과

**Google Keep의 iOS/Android 버전 자체는 Google 제품이라 아래 Android
항목에서 다루고, 여기서는 Apple 1st-party 앱과 API 문서만 다룬다.**

구버전(2017년 이전, UIKit `UITableViewCellEditingStyle` 시대) 공식
프로그래밍 가이드는 명확히 "그립 아이콘을 드래그한다"고만 설명하고
롱프레스를 언급하지 않는다:

> "The user drags a row by its reordering control up or down the table
> view." / "A table view goes into editing mode when it receives a
> `setEditing:animated:` message. This normally happens when the user taps
> an Edit button."
> — [Apple, Table View Programming Guide — Managing the Reordering of Rows](https://developer.apple.com/library/archive/documentation/UserExperience/Conceptual/TableView_iPhone/ManageReorderRow/ManageReorderRow.html) (archived)

**[표준] — 단, 이 문서는 2017년 이전 API(구 편집 스타일) 기준이라 현재
OS 동작과 반드시 일치한다는 보장이 없다.** 아래에서 이 문서가 실제로
깨진다는 걸 확인했다.

현재(2026년 기준) Apple 1st-party 앱의 실제 지원 문서는 다르게 말한다.
Mail의 메일박스 재정렬(편집 모드 게이팅 + 사실상 핸들처럼 동작하는 행)은:

> "Tap Edit, then do any of the following: ... Reorder mailboxes: **Touch
> and hold** next to a mailbox until it lifts up, then drag it to the new
> position."
> — [Apple Support, Organize email in mailboxes on iPhone](https://support.apple.com/guide/iphone/organize-your-email-iph376ef8aa3/ios)

**[표준] (Apple 자사 지원 문서, 현재 유지 중인 페이지).** 편집 모드에
들어간 뒤에도 "터치 후 즉시 드래그"가 아니라 "touch and hold ... until it
lifts up"라는 동일한 동사구를 쓴다 — 아래 iOS 일반 드래그앤드롭 안내와
표현이 완전히 같다.

### Android — 검색 확인 결과

Google Keep(핸들 아이콘 "Move"가 항목 좌측에 별도로 존재):

> "At the left of the item you want to move, **tap and hold** Move, and
> drag it where you want."
> — [Google Keep Help, Make a list — Android](https://support.google.com/keep/answer/6395451?co=GENIE.Platform%3DAndroid&hl=en)

**[관성] (Google 1st-party 앱의 공식 도움말 문서로 확인, 기기 직접 관찰
아님).** 핸들 아이콘이 있는데도 "tap and hold"라는 동일 표현을 쓴다.

API 레벨 공식 문서(Android 개발자 문서)는 핸들 기반 드래그를 이렇게
규정한다 — 그리고 여기서는 시간 지연이 없다:

> `isLongPressDragEnabled()` — "Default value returns true but you may
> want to disable this if you want to start dragging on a custom view
> touch using `startDrag`."
> `startDrag(RecyclerView.ViewHolder)` — "Starts dragging the provided
> ViewHolder."
> — [Android Developers, `ItemTouchHelper.Callback#isLongPressDragEnabled()`](https://developer.android.com/reference/androidx/recyclerview/widget/ItemTouchHelper.Callback#isLongPressDragEnabled())
> / [`ItemTouchHelper#startDrag()`](https://developer.android.com/reference/androidx/recyclerview/widget/ItemTouchHelper#startDrag(androidx.recyclerview.widget.RecyclerView.ViewHolder))

**[표준] — 이건 명확하다.** 핸들 구현 시 `isLongPressDragEnabled()`를
`false`로 끄고, 핸들 뷰의 `ACTION_DOWN`에서 `startDrag()`를 직접 호출하는
게 공식 API 패턴이다. 여기엔 인위적 지연이 없다 — `ACTION_DOWN` 즉시
드래그가 시작된다.

Material Design의 공식 스펙(archived — 현재 M3 가이드라인 페이지에는
재정렬 관련 서술이 없음, 아래 "확인 안 됨" 참조)은 핸들을 별도 터치
타겟으로 규정한다:

> "Reorder — Type: secondary action. Usually a separate target ...
> Allows dragging of the list item to other locations within the list.
> It usually appears in list editing mode. The reorder icon is the
> secondary action for the list item."
> — [Material Design (archived), Lists — controls](https://material.io/archive/guidelines/components/lists-controls.html)

**[표준] (Google 공식 도메인의 아카이브 스펙).** "별도 타겟"이라는 표현이
API 문서의 handle 패턴과 정확히 일치한다.

### 3-A 판정

| 판단 | 라벨 | 근거 |
|---|---|---|
| 핸들은 다른 액션(탭=열기 등)과 분리된 별도 터치 타겟이다 | [표준] | Apple 구 API 문서 + Material archived 스펙 + Android API 문서, 3개 독립 출처 일치 |
| 핸들 터치 시 인위적 지연(long-press timer) 없이 즉시 드래그를 시작하는 것이 **Android API 레벨**의 공식 패턴이다 | [표준] | `startDrag()`는 `ACTION_DOWN`에서 직접 호출하도록 문서화됨 — 지연 없음이 명시적 |
| iOS/Google 1st-party 앱들은 핸들이 있어도 소비자 도움말에서 "touch/tap and hold"라는 동일 표현을 쓴다 | [관성] (문서 기반, 기기 미확인) | Apple Mail, Google Keep 지원 문서 |
| "touch and hold"라는 소비자 문구가 실제로 인위적 지연(≈500ms급 타이머)을 의미하는지, 아니면 그냥 "누른 채로 손을 떼지 말라"는 일반적 지시문인지 | **🚧 미확정** | 소비자 도움말 문서는 일반 사용자 대상 자연어라 이 둘을 구분하지 못한다. ms 단위 실측은 네이티브 앱 계측이 필요하고 이 조사(웹 문서 검색) 범위 밖이다. |

**결론(라벨 붙여서만 진술)**: 핸들이 있으면 [표준]으로 "탭으로 여는 행위와
드래그로 옮기는 행위가 물리적으로 다른 타겟에서 일어난다"는 것까지는
확정된다. 그러나 "핸들 = 지연 없는 즉시 드래그"라는 원래 가설은 Android
API 레벨에서만 [표준]으로 확인됐고, iOS·Google 1st-party 앱 문서는 오히려
반례처럼 읽히는 표현("tap and hold")을 쓴다 — 이 지점은 **🚧 미확정**으로
남긴다. 자세한 재검증 필요 사항은 아래 "예상과 다른 발견" 절 참조.

---

## 3-B. 핸들 없음 — 행 전체가 하나의 타겟

### iOS — 검색 확인 결과

Reminders(편집 모드 진입 없이, 리스트를 보는 중 바로 재정렬 가능):

> "Reorder or recategorize items in a list — ... While viewing a list,
> **touch and hold** an item you want to move, then drag it to a new
> location."
> — [Apple Support, Edit and organize a list in Reminders on iPhone](https://support.apple.com/guide/iphone/edit-and-organize-a-list-iph82596cb20/ios)

**[표준] (Apple 자사 지원 문서).** 편집 모드(Edit 버튼) 없이도 바로
재정렬 가능하다는 점이 3-A(Mail 메일박스, Edit 모드 필요)와 다르다.

iOS 전반의 드래그앤드롭 제스처 자체도 동일한 동사구로 문서화되어 있다:

> "Move an item — Locate the item you want to move. **Touch and hold**
> the item until it lifts up (if it's text, select it first). Drag it to
> another location within the app."
> — [Apple Support, Drag and drop on iPad](https://support.apple.com/guide/ipad/drag-and-drop-ipadaa83b207/ipados)

**[표준].** 이 페이지는 iPad용으로 게시되어 있다 — iPhone 전용 동등
페이지는 검색으로 찾지 못했다(**🚧 미확정**, iPhone도 같은 UIKit
드래그앤드롭 API를 쓰므로 동일할 개연성은 높으나 iPhone 이름이 붙은
Apple 자사 문서로 직접 확인하지는 못했다).

### Android — 검색 확인 결과

Google Tasks(핸들 없이, 행 자체가 타겟):

> "Touch and hold a task and move the task where you want."
> — [Google Tasks Help, Organize your tasks — Android](https://support.google.com/tasks/answer/7675629?co=GENIE.Platform%3DAndroid&hl=en)

**[관성] (Google 1st-party 앱 공식 도움말, 기기 미확인).**

API 레벨에서는 이 경로가 정확히 "핸들 없음"의 기본값이다:

> `isLongPressDragEnabled()` — "Returns whether ItemTouchHelper should
> start a drag and drop operation if an item is long pressed. **Default
> value returns true**."
> — [Android Developers, `ItemTouchHelper.Callback#isLongPressDragEnabled()`](https://developer.android.com/reference/androidx/recyclerview/widget/ItemTouchHelper.Callback#isLongPressDragEnabled())

**[표준].** 기본값이 "롱프레스로 드래그 시작"이다 — 즉 핸들을 따로 구현하지
않으면 Android의 공식 기본 동작 자체가 롱프레스 기반이라는 뜻. 정확한
타이머 ms 값(플랫폼의 `ViewConfiguration.getLongPressTimeout()`)은 이
문서에 없다 — `research/c10-sources.md`에서 이미 확인한 `TOUCH_SLOP` 계열
상수와는 별개 상수이므로 별도 확인이 필요하다(**🚧 미확정**, 이 문서
범위에서는 미조사).

### 3-B 판정

| 판단 | 라벨 | 근거 |
|---|---|---|
| 핸들이 없으면 행 전체가 탭(열기 등 다른 동작)과 드래그를 동시에 담당하는 하나의 타겟이 된다 | [표준] | 식별 신호 자체의 정의 — 재론 불필요 |
| Android는 이 경우 공식 기본값 자체가 "롱프레스로 드래그 시작"이다 | [표준] | `isLongPressDragEnabled()` 기본값 `true`, API 문서 명시 |
| iOS/Android 1st-party 앱(Reminders, Google Tasks)은 핸들 없는 재정렬을 "touch/tap and hold, then drag"로 안내한다 | [관성] (문서 기반) | Apple Support, Google Tasks Help |
| 정확한 지연 시간(ms) | **🚧 미확정** | 소비자 문서는 정성적 표현("hold")만 제공. Android의 `getLongPressTimeout()` 실제 기본값도 이 문서에서는 미조사 |

---

## 예상과 다른 발견 — 재검증 필요

`ux-standards-architecture.md`가 반면교사로 든 실패("핸들 있는 리스트에
근거 없이 롱프레스를 강제")는 **핸들이 있으면 롱프레스가 필요 없다**는
암묵적 가정에 기반해 있었다. 이번 검색 결과는 그 가정을 부분적으로만
지지한다.

**확인된 것 (핸들의 실제 효과)**: 핸들은 "탭으로 여는 행위"와 "드래그로
옮기는 행위"를 **서로 다른 물리적 타겟으로 분리**한다. 이게 [C2 — Tap ↔
LongPress](/CONFLICTS.md#c2--tap--longpress)가 설명하는 충돌 자체를
구조적으로 없앤다 — C2의 원인은 "탭이 끝나지 않은 상태가 롱프레스"라서
같은 타겟에서 둘을 구분해야 한다는 것인데, 핸들은 애초에 그 타겟을
분리해버린다. 이 점은 [표준]으로 확정할 수 있다(Android API 문서가 핸들
패턴을 별도 타겟으로 명문화).

**확인되지 않은 것 (그리고 원래 가정과 반대로 보이는 것)**: "타겟이
분리됐으니 지연 없이 즉시 드래그해도 된다"는 결론은 Android
`startDrag()` API에서만 [표준]으로 확인됐다. iOS의 Mail(핸들처럼 동작하는
행, Edit 모드)과 Google Keep의 실제 핸들 아이콘 모두, 공식 지원 문서가
"touch/tap and hold"라는 동일한 문구를 쓴다. 이게 정말 인위적 지연을
의미하는지, 아니면 단지 "누르고 있다가 옮기라"는 일반적 안내 문구일
뿐인지는 **소비자용 도움말 텍스트만으로는 구분할 수 없다** — 이건 확인
방법의 한계이지, 확인된 사실이 아니다. 🚧 미확정으로 남기고, 실기기
계측(네이티브 앱 대상, 이 프로젝트의 브라우저 하네스로는 측정 불가)이
있어야 해소된다.

**실무적 함의(라벨 붙여 진술)**: 웹 구현에서 핸들을 둘 때 "탭↔드래그
분리"라는 [표준] 효과는 그대로 가져올 수 있다. 그러나 "핸들이면 지연 0ms"
라고 단정하는 건 [미확정]인 근거 위에 [표준]인 것처럼 코드를 작성하는
셈이 된다 — §4 라벨 규율 위반. 핸들에도 최소한의 `activation_distance`
또는 짧은 `activation_delay`를 두는 쪽이 이 문서가 실제로 확인한 근거와
더 일치한다.

---

## CONFLICTS.md 연결

| 시나리오 | 연결되는 C번호 | 이유 |
|---|---|---|
| 핸들 없음 — 행 전체가 탭/롱프레스/드래그 세 동작을 공유 | [C2 — Tap ↔ LongPress](/CONFLICTS.md#c2--tap--longpress), [C6 — LongPress ↔ Drag](/CONFLICTS.md#c6--longpress--drag) | 정확히 이 두 섹션이 다루는 시나리오. C6의 실측 `activation_delay`(500ms 계열)가 그대로 적용 대상 |
| 핸들 있음/없음 공통 — 드래그가 시작된 뒤 리스트 자체의 세로 스크롤과 경합 | [C10 — Drag ↔ Scroll](/CONFLICTS.md#c10--drag--scroll) | 재정렬 드래그는 항상 스크롤 가능한 컨테이너 안에서 일어난다. C10의 `touch-action`/거리 임계값 실측이 그대로 적용 대상 |
| 핸들 있음 — 작은 아이콘 타겟에서의 탭 대 드래그 시작 경계 | [C3 — Tap ↔ Drag](/CONFLICTS.md#c3--tap--drag) | 핸들 자체도 아주 짧은 이동에서는 탭인지 드래그 시작인지 구분이 필요할 수 있음(핸들에 다른 탭 동작이 없다면 실무적 영향은 작음 — C2/C6만큼 심각하지 않음) |

---

## 다음 문서와의 접점 (해결하지 않음, 표시만)

5번(multi-select.md), 6번(context-menu.md)은 이 컴포넌트와 같은 카드에서
**같은 롱프레스 트리거**를 요구할 수 있다("핸들 없음" 케이스에서 특히).
세 기능(재정렬/다중선택/컨텍스트메뉴)이 한 카드에 동시에 요구되면 어느
게 이기는지는 **여기서 답하지 않는다** — 8개 문서가 끝난 뒤 오염 방지
섹션에서 별도로 다룬다 (`ux-standards-architecture.md` §3 참조).

---

## 출처 전체 목록

- [Apple, Table View Programming Guide — Managing the Reordering of Rows](https://developer.apple.com/library/archive/documentation/UserExperience/Conceptual/TableView_iPhone/ManageReorderRow/ManageReorderRow.html) (archived, pre-iOS 11 API)
- [Apple Support — Organize email in mailboxes on iPhone](https://support.apple.com/guide/iphone/organize-your-email-iph376ef8aa3/ios)
- [Apple Support — Edit and organize a list in Reminders on iPhone](https://support.apple.com/guide/iphone/edit-and-organize-a-list-iph82596cb20/ios)
- [Apple Support — Drag and drop on iPad](https://support.apple.com/guide/ipad/drag-and-drop-ipadaa83b207/ipados)
- [Android Developers — `ItemTouchHelper.Callback#isLongPressDragEnabled()`](https://developer.android.com/reference/androidx/recyclerview/widget/ItemTouchHelper.Callback#isLongPressDragEnabled())
- [Android Developers — `ItemTouchHelper#startDrag()`](https://developer.android.com/reference/androidx/recyclerview/widget/ItemTouchHelper#startDrag(androidx.recyclerview.widget.RecyclerView.ViewHolder))
- [Google Keep Help — Make a list (Android)](https://support.google.com/keep/answer/6395451?co=GENIE.Platform%3DAndroid&hl=en)
- [Google Tasks Help — Organize your tasks (Android)](https://support.google.com/tasks/answer/7675629?co=GENIE.Platform%3DAndroid&hl=en)
- [Material Design (archived) — Lists, controls](https://material.io/archive/guidelines/components/lists-controls.html)
- 확인 시도했으나 정적 콘텐츠를 가져오지 못해 **미확인**으로 남긴 것: 현재 Material Design 3 공식 가이드라인 페이지(`m3.material.io/components/lists/guidelines`)는 reorder/drag/handle/long-press 관련 서술을 이 조사에서 찾지 못했다 — 페이지가 없다는 뜻이 아니라, 이 조사(자동 텍스트 추출)로는 확인하지 못했다는 뜻이다.

**방법론 고지**: 이 문서의 모든 [관성] 라벨은 "공식 지원 문서 검색 확인"이며,
`ux-standards-architecture.md` §5.5가 구분하는 "런타임 검증"(실기기에서
직접 눌러본 것)이 아니다. 이 프로젝트가 CONFLICTS.md에서 지키는 실기기
계측 규율과는 확인 방법이 다르다는 걸 여기 명시해둔다.
