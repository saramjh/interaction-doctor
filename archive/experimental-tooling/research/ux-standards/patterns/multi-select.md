# Component: Multi-select via Long Press (롱프레스로 다중 선택 모드 진입)

절차는 앞선 네 문서와 동일: `ux-standards-architecture.md` §1(우선순위)
→ §2(식별 신호) → §4(라벨) 순서를 따른다. 검증 방법도 동일하게 **검색을
통한 1차 문서 확인**이며, 실기기 직접 관찰이 아니다.

**이 문서는 §3-2(오염 방지)와 직결된다.** reorderable-list.md의
"핸들 없음" 케이스는 롱프레스로 재정렬을 시작하는데, 이 컴포넌트도
롱프레스로 다중 선택을 시작할 수 있다 — 같은 트리거가 다른 두 모드를
연다면 어느 게 이기는지는 아래 별도 섹션에서 **표시만 하고 해소하지
않는다.**

---

## 식별 신호 (§2)

```
- 리스트/그리드 항목을 길게 누르면 화면 상단에 개수 표시("3개 선택됨")와
  함께 체크마크/원형 선택 표시가 항목마다 나타나는 디자인 → 다중 선택
- 화면 상단(또는 하단)에 항상 "선택" 텍스트 버튼이 보이는 디자인 →
  버튼으로 진입하는 방식일 수 있음 (아래 1번 참조 — 플랫폼마다 다름)
- 선택 모드 진입 후 다른 항목들 위로 손가락을 미끄러뜨리면 연쇄로
  체크되는 듯한 디자인 → "드래그로 확장 선택" (아래 3번)
- 같은 항목에 재정렬 핸들(6-dot 아이콘)도 같이 있으면 →
  reorderable-list.md와 신호 겹침. 아래 "겹침" 섹션 참조
- 길게 눌렀을 때 확대 미리보기 + 메뉴가 뜨면 → 다중 선택이 아니라
  context-menu.md 쪽. 아래 "겹침" 섹션 참조
```

---

## 1. 진입 트리거 — iOS와 Android가 실제로 다르다

### iOS — 1st-party 앱: 롱프레스가 아니라 명시적 버튼

**Photos**:
> "Delete or hide multiple photos and videos — Go to the Photos app on
> your iPhone. View your library or open a collection. **Tap Select**,
> then tap the photos and videos you want to delete or hide."
> — [Apple Support, Delete or hide photos and videos on iPhone](https://support.apple.com/guide/iphone/delete-or-hide-photos-and-videos-iphb4defbde9/ios)

**Files**:
> "Touch and hold the file or folder, then choose an option: Copy, Move,
> Rename, Compress, Duplicate, or Delete. **To modify multiple files or
> folders at the same time, tap [menu], tap Select**, tap to select the
> files or folders you want to modify, then tap an option at the bottom
> of the screen."
> — [Apple Support, Organize files and folders in Files on iPhone](https://support.apple.com/guide/iphone/organize-files-and-folders-iphab82e0798/ios)

**[관성] (Apple 1st-party 앱 공식 지원 문서, 기기 미확인) — 이번 조사의
핵심 발견이다.** 두 앱 모두 다중 선택 **진입**은 롱프레스가 아니라
명시적 "Select" 텍스트 버튼이다. Files 앱은 오히려 **같은 화면에서
롱프레스를 완전히 다른 용도**(단일 항목 컨텍스트 메뉴: Copy/Move/
Rename/Compress/Duplicate/Delete)로 쓰고 있다 — 즉 Apple 자사 앱들은
"롱프레스=컨텍스트 메뉴, 버튼=다중 선택 진입"으로 **트리거 자체를
분리**해서 이 프로젝트가 우려하는 충돌을 원천적으로 피하고 있다.

### Android — 1st-party 앱: 롱프레스가 진입 트리거

**Google Photos** / **Files by Google**:
> "To select multiple photo or video files in Google Photos on Android,
> **touch and hold** the first file, then tap the other files that you
> want to delete." / "To select multiple files in Files by Google on
> Android, you can **touch and hold** them."
> — [Google Photos Help, Delete photos & videos (Android)](https://support.google.com/photos/answer/6128858?co=GENIE.Platform%3DAndroid&hl=en) / [Files by Google Help](https://support.google.com/files/answer/9808833)

**[관성] (Google 1st-party 앱, 기기 미확인) — 단, 이 인용은 검색 결과
요약을 통해서만 확인했다.** support.google.com 도움말 페이지는
JavaScript로 콘텐츠를 렌더링해 이 세션에서 원문 HTML을 직접 재조회하지
못했다(`swipe-actions.md`의 M3 가이드라인 페이지와 같은 제약). 검색
엔진이 인덱싱한 발췌문을 인용했으며, 완전한 원문 재확인은 **🚧 부분
미확정**으로 남긴다.

Android 공식 API(`androidx.recyclerview.selection`)는 롱프레스를 명시적
개념("gesture selection")으로 문서화한다 — 단, 이건 "선택 모드 최초
진입"이 아니라 "이미 선택이 있는 상태에서 새 항목을 롱프레스해 확장
선택을 시작하는" 시나리오로 정의돼 있다:

> "A provisional selection can be abandoned, or merged into the primary
> selection... or when there's **an active gesture selection (which can
> be initiated by long pressing an unselected item while there is an
> existing selection)**."
> — [Android Developers, `SelectionTracker`](https://developer.android.com/reference/androidx/recyclerview/selection/SelectionTracker)

**[표준] (developer.android.com 공식 API 문서, 이번 세션에서 원문 직접
확인).** 이 문서 자체는 "최초 진입"에 롱프레스가 쓰이는지를 직접
규정하지 않는다 — "이미 선택이 있을 때"라는 조건이 붙어 있다. 최초
진입 트리거(빈 상태에서 첫 항목을 어떻게 선택하는지)는 이 API 문서
만으로는 확인되지 않았다 — **🚧 미확정**(다만 위 Google Photos/Files
소비자 도움말은 최초 진입도 touch and hold라고 서술한다 — 공식
API 문서와 소비자 도움말 사이에 서술 범위 차이가 있다는 점 자체를
사실로 기록해 둔다).

### 판정

| 판단 | 라벨 | 근거 |
|---|---|---|
| iOS 1st-party 앱(Photos, Files)은 다중 선택 진입에 롱프레스를 쓰지 않고 명시적 버튼을 쓴다 | [관성] | Apple Support 공식 문서 2건 |
| Android 1st-party 앱(Photos, Files by Google)은 다중 선택 진입에 롱프레스(touch and hold)를 쓴다 | [관성] (검색 결과 요약, 원문 재확인 못함 — 🚧 부분 미확정) | Google Help 공식 문서 |
| Android 공식 API 문서는 롱프레스를 "기존 선택 확장(gesture selection)" 맥락에서 정의하며, "최초 진입" 트리거는 별도로 규정하지 않는다 | [표준] | `SelectionTracker` 공식 문서, 원문 직접 확인 |
| **결론: 진입 트리거는 플랫폼 공용의 단일 표준이 아니다 — iOS는 버튼, Android 소비자 앱은 롱프레스** | [관성]의 직접 귀결 | 위 두 항목의 비교 |

---

## 2. 진입 후 단일 탭이 "선택 토글"로 바뀌는 동작

### iOS

Photos: "Tap Select, then **tap the photos and videos** you want to
delete or hide." — Select 모드 진입 후에는 탭이 곧 선택/해제 토글이
된다는 게 문장 구조 자체에서 확인된다.
— [Apple Support, Delete or hide photos and videos on iPhone](https://support.apple.com/guide/iphone/delete-or-hide-photos-and-videos-iphb4defbde9/ios)

**[관성].**

### Android

Google Photos: "touch and hold the first file, **then tap the other
files** that you want to delete." — 첫 항목은 롱프레스로 진입, 이후
항목은 탭으로 추가 선택. Android 공식 API 문서에서도 `SelectionPredicate`
가 "탭 = 선택 토글" 정책을 애플리케이션이 규정하도록 설계돼 있다:

> "Which items can be selected by the user is a matter of policy in an
> Application. Developers supply these policies by way of
> `SelectionPredicate`."
> — [Android Developers, `SelectionTracker`](https://developer.android.com/reference/androidx/recyclerview/selection/SelectionTracker)

**[표준] (정책이 앱에 위임된다는 사실 자체는 확인됨) — 단, "탭=토글"이
플랫폼이 강제하는 기본값인지, 각 앱이 관행적으로 그렇게 구현할 뿐인지는
API 문서가 구분해 말하지 않는다.** 이 구분은 **🚧 미확정**으로 남긴다.

### 판정

| 판단 | 라벨 | 근거 |
|---|---|---|
| 두 플랫폼 모두 선택 모드에서 단일 탭 = 선택/해제 토글이라는 사용 패턴이 확인된다 | [관성] | 1st-party 앱 도움말 문서의 문장 구조 |
| 이게 플랫폼이 강제하는 표준 동작인지, 관행적으로 그럴 뿐인지 | **🚧 미확정** | Android는 정책을 앱에 위임한다고 명시(`SelectionPredicate`), iOS 쪽은 강제/관행 여부를 확인할 API 문서를 찾지 못함 |

---

## 3. 드래그로 연쇄 선택 — 예상 밖의 대칭 발견

### iOS

> "Open Photos. Tap Select, then tap multiple photos or **slide your
> finger across multiple photos** to select more than one."
> — [Apple Support, Delete photos on your iPhone or iPad](https://support.apple.com/en-us/104967)

**[관성].** 탭 하나씩이 아니라, 손가락을 뗀 채로 미끄러뜨려 여러 항목을
한 번에 선택하는 방식이 Apple 자사 문서에 공식적으로 안내돼 있다.

### Android

바로 위 1번에서 인용한 `SelectionTracker`의 "gesture selection"이 구조적으로
같은 기능이다 — 롱프레스로 시작한 뒤 손가락을 이동시키면 지나간 항목들이
연쇄로 선택되는 방식.

**[표준] (Android는 API 문서로, iOS는 소비자 도움말로 — 확인 방법은
다르지만 두 플랫폼 모두 "드래그로 연쇄 선택"을 공식 지원한다는 결론은
동일).** 이건 이번 조사에서 예상하지 못했던 대칭성이다 — 두 플랫폼이
"진입 트리거"는 다르게 설계했지만(1번), "선택 확장 방식"은 같은
드래그 기반 패턴으로 수렴했다.

---

## 4. 진입/해제 트리거

### 해제(Cancel/Done) — 양쪽 다 확인됨

iOS: "If you want to delete all the photos and videos in the album,
**tap Cancel**, then tap Select again."
— [Apple Support, Delete photos on your iPhone or iPad](https://support.apple.com/en-us/104967)

**[관성].**

Android: "The action mode is disabled and the contextual action bar
disappears when **the user deselects all items, taps the Back button,
or taps the Done action** on the left side of the bar."
— [Android Developers, Add and handle actions (Menus)](https://developer.android.com/develop/ui/views/components/menus)

**[표준] (developer.android.com 공식 가이드, 원문 직접 확인).** Android는
세 가지 해제 트리거(전체 해제 / 뒤로가기 / Done 버튼)를 공식 문서 한
문장에 명시한다 — iOS보다 더 구체적으로 문서화돼 있다.

### 판정

| 판단 | 라벨 | 근거 |
|---|---|---|
| iOS는 "Cancel" 버튼으로 선택 모드를 해제한다 | [관성] | Apple Support 문서 |
| Android는 전체 해제/뒤로가기/Done 버튼 셋 다 공식 해제 트리거다 | [표준] | Android Developers 공식 가이드, 원문 확인 |
| iOS가 "뒤로가기 스와이프"로도 선택 모드를 해제하는지 | **🚧 미확정** | Apple 공식 문서에서 확인 못함 |

---

## 겹침 — reorderable-list.md와 롱프레스 트리거 공유 가능성 (해소하지 않음)

`ux-standards-architecture.md` §3(오염 방지)가 지정한 대로, 여기서는
**문제를 표시만 하고 우선순위를 정하지 않는다.**

- reorderable-list.md의 "핸들 없음"(3-B) 케이스: 행 전체를 롱프레스하면
  재정렬 모드로 들어간다(Android 기준 `isLongPressDragEnabled()` 기본값
  `true`, 확인 완료).
- 이 문서의 Android 소비자 앱 사례: 행 전체를 롱프레스하면 다중 선택
  모드로 들어간다(Google Photos/Files, 위 1번 확인).
- **같은 행에 "재정렬도 되고 다중 선택도 되는" 요구가 동시에 오면, 같은
  롱프레스 트리거가 두 모드 중 무엇을 열어야 하는지는 이 문서도
  reorderable-list.md도 답하지 않는다.** 8개 문서가 끝난 뒤 오염 방지
  섹션에서 다룬다.

**단, 이번 조사로 새로 드러난 비대칭 하나는 사실로 기록해 둔다**: 이
충돌은 **플랫폼에 따라 발생 여부 자체가 다르다.** iOS 1st-party 앱들은
다중 선택 진입에 애초에 롱프레스를 쓰지 않으므로(1번), reorderable-list.md의
iOS 사례(Reminders, 롱프레스로 재정렬 — `reorderable-list.md` 3-B 참조)와
이 문서의 iOS 사례가 트리거를 공유하지 않는다 — **iOS에서는 이 충돌이
Apple 자사 앱 설계상 아예 발생하지 않는다는 관찰이 이번 조사로
확인됐다.** 반면 Android 소비자 앱은 재정렬(롱프레스)과 다중 선택
(롱프레스)이 **같은 트리거를 실제로 공유한다** — 즉 이 오염 문제는
**Android 쪽에서 더 실재하는 문제**라는 것이 지금까지의 근거로 시사된다.
이 판단 자체도 최종 해소가 아니라 8번 섹션에 넘길 정보로만 기록한다.

---

## CONFLICTS.md 연결

| 시나리오 | 연결 | 비고 |
|---|---|---|
| 다중 선택 모드 진입을 위한 롱프레스 자체의 타이밍/거리 | [C6 — LongPress ↔ Drag](/CONFLICTS.md#c6--longpress--drag) | 진입 메커니즘이 롱프레스인 경우(Android), C6의 실측 그대로 적용 |
| 선택 모드 진입 전, 같은 항목의 일반 탭(항목 열기)과의 경계 | [C2 — Tap ↔ LongPress](/CONFLICTS.md#c2--tap--longpress) | 롱프레스 진입 방식(Android)에서만 해당. iOS는 버튼 진입이라 해당 없음 |
| 드래그로 연쇄 선택(3번) 도중 리스트 자체의 스크롤과의 경합 | [C10 — Drag ↔ Scroll](/CONFLICTS.md#c10--drag--scroll) | 재실측 없음, 연결만 |
| 재정렬과 다중 선택의 롱프레스 트리거 공유 | 연결 없음 — 오염방지(§3) 후보, 위 "겹침" 섹션 | 해소하지 않음 |

---

## 출처 전체 목록

- [Apple Support — Delete or hide photos and videos on iPhone](https://support.apple.com/guide/iphone/delete-or-hide-photos-and-videos-iphb4defbde9/ios)
- [Apple Support — Delete photos on your iPhone or iPad](https://support.apple.com/en-us/104967)
- [Apple Support — Organize files and folders in Files on iPhone](https://support.apple.com/guide/iphone/organize-files-and-folders-iphab82e0798/ios)
- [Google Photos Help — Delete photos & videos (Android)](https://support.google.com/photos/answer/6128858?co=GENIE.Platform%3DAndroid&hl=en) (검색 결과 요약으로만 확인 — 🚧 부분 미확정)
- [Files by Google Help — Move files to an existing folder](https://support.google.com/files/answer/9808833) (검색 결과 요약으로만 확인 — 🚧 부분 미확정)
- [Android Developers — `androidx.recyclerview.selection.SelectionTracker`](https://developer.android.com/reference/androidx/recyclerview/selection/SelectionTracker) (원문 직접 확인)
- [Android Developers — Add and handle actions (contextual action bar / action mode)](https://developer.android.com/develop/ui/views/components/menus) (원문 직접 확인)
- 확인 시도했으나 못 찾은 것: Android 소비자 앱에서 "최초 진입"이 정말
  롱프레스인지의 원문 재확인(JS 렌더링으로 이번 세션에서 재조회 불가),
  "탭=토글"이 플랫폼 강제 표준인지 관행인지, iOS의 뒤로가기 스와이프로
  선택 모드가 해제되는지 — 전부 **🚧 미확정**으로 본문에 개별 표시했다.

**방법론 고지**: 이전 문서들과 동일하게, [관성] 라벨은 "공식 지원 문서
검색 확인"이며 실기기 직접 관찰이 아니다. 이번 문서는 Google 도움말
페이지 2건을 JS 렌더링 문제로 원문 재확인하지 못해 검색 결과 요약에
의존한 부분이 있다는 걸 특히 명시해 둔다.
