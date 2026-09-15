# Component: Bottom Sheet (드래그로 닫히는 바텀시트, 스냅 포인트)

절차는 `reorderable-list.md`, `swipe-actions.md`와 동일:
`ux-standards-architecture.md` §1(우선순위) → §2(식별 신호) → §4(라벨)
순서를 따른다. 검증 방법도 동일하게 **검색을 통한 1차 문서 확인**이며,
실기기 직접 관찰이 아니다.

---

## 식별 신호 (§2)

```
- 화면 하단에서 위로 슬라이드해 올라오는 패널, 배경이 어두워짐(스크림)
  → 모달 바텀시트
- 화면 하단에 항상 붙어 있고 배경이 어두워지지 않으며, 나머지 화면과
  동시에 상호작용 가능 → 퍼시스턴트/스탠다드 바텀시트 (지도 앱류)
- 패널 상단에 짧은 가로 막대(grabber/handle) → 드래그로 리사이즈/닫기
  가능하다는 표준 시각 신호
- 패널이 여러 높이 단계(예: 화면의 30%/60%/100%)를 오가며 멈추는
  듯한 디자인 → 스냅 포인트(디텐트) 여러 개
- 패널 안에 자체 스크롤 가능한 리스트가 있는 디자인 → 아래 5번
  "내부 스크롤 우선순위" 항목 확인 필요
```

---

## 1. iOS — 공유 시트 / 지도 앱류 하단 패널

### API 레벨 (표준 스펙)

iOS 15부터 시트 프레젠테이션 전용 API가 존재하며, 시스템 정의 두 단계
디텐트를 명시적으로 제공한다:

> `UISheetPresentationController.Detent` — "An object that represents a
> height where a sheet naturally rests."
> 시스템 정의 디텐트로 `.medium()`(약 절반 높이)과 `.large()`(완전 확장)
> 두 가지가 iOS 15에서 노출됨.
> — [Apple Developer Documentation, `UISheetPresentationController.Detent`](https://developer.apple.com/documentation/uikit/uisheetpresentationcontroller/detent)

**[표준].**

### 1st-party 앱 실제 사례 — Maps

> "Display, lengthen, or shorten the card ... **To resize the card, drag
> the top of the card up or down.**"
> — [Apple Support, Search for places in Maps on iPhone](https://support.apple.com/guide/iphone/search-for-places-iph1df24639/ios)

**[표준] (Apple 자사 지원 문서, 현재 유지 중).** Maps의 검색 결과 카드는
드래그로 리사이즈 가능한 하단 패널이라는 것까지는 확인된다. 그러나 이
문서는 정확히 몇 단계(스냅 포인트 개수)로 멈추는지, 완전히 닫을(hide)
수 있는지는 언급하지 않는다 — **🚧 미확정**. Maps의 카드는 검색바 자체가
항상 최소한으로 보이는 구조라(퍼시스턴트 유형에 가까움) API의
`.medium()`/`.large()` 두 단계와 정확히 같은 것인지, 커스텀 디텐트를
쓰는지는 이 문서만으로 확정할 수 없다.

공유 시트(Share Sheet) 자체의 드래그-닫기 동작을 서술하는 별도의 Apple
1st-party 지원 문서는 이번 검색으로 찾지 못했다 — **🚧 미확정**.

---

## 2. Android — Material Design 공식 스펙 (Standard vs Modal)

Material Design(archived 공식 스펙)은 이 구분을 정확히 "Modal" 대
"Persistent"(현재 M3/Compose 문서에서는 "Standard"로 재명명됨)로
정의한다:

> "Bottom sheets slide up from the bottom of the screen to reveal more
> content. **Modal bottom sheets** are primarily for mobile and can also
> present deep-linked content from other apps. **Persistent bottom
> sheets** integrate with the app to display supporting content."
> "Elevation — Modal bottom sheets: Higher than the app / Persistent
> bottom sheets: Same elevation as the app."
> "[Modal bottom sheets] ... must be dismissed in order to interact with
> the underlying content. When a modal bottom sheet slides into the
> screen, **the rest of the screen dims**, giving focus to the bottom
> sheet."
> — [Material Design (archived), Components — Bottom sheets](https://material.io/archive/guidelines/components/bottom-sheets.html)

**[표준] (Google 공식 아카이브 스펙).** 모달=스크림 있음+배경 상호작용
차단, 퍼시스턴트/스탠다드=스크림 없음+배경과 동시 상호작용 가능이라는
구분이 명문화되어 있다.

이 구분은 API 레벨에서도 그대로 클래스 분리로 나타난다 — 같은
`BottomSheetBehavior`를 뷰에 직접 붙이면 퍼시스턴트, `BottomSheetDialog`
(스크림 포함)로 감싸면 모달:

> `BottomSheetBehavior` — 상태 상수로 `STATE_COLLAPSED`, `STATE_DRAGGING`,
> `STATE_EXPANDED`, `STATE_HALF_EXPANDED`("used when fitToContents is
> false" — 즉 3단계 스냅), `STATE_HIDDEN`, `STATE_SETTLING`을 공식
> 문서화.
> — [Android Developers, `BottomSheetBehavior`](https://developer.android.com/reference/com/google/android/material/bottomsheet/BottomSheetBehavior)

**[표준].** `halfExpandedRatio`(중간 단계 높이 비율), `peekHeight`(축소
상태 높이)까지 공개 필드로 존재해 **스냅 포인트가 최소 3단계(collapsed/
half-expanded/expanded)까지 공식 지원됨**이 확인된다.

---

## 3. 드래그로 닫는 임계 거리/속도

### Android — 수치화된 공식 답이 있다

> `isHideable()` — "Gets whether this bottom sheet can hide **when it is
> swiped down**." / `setHideable(boolean)` — "Sets whether this bottom
> sheet can hide."
> `hideFriction` (공개 필드), `significantVelocityThreshold` /
> `getSignificantVelocityThreshold()` — "Returns the significant
> velocity threshold."
> — [Android Developers, `BottomSheetBehavior`](https://developer.android.com/reference/com/google/android/material/bottomsheet/BottomSheetBehavior)

**[표준] (거리 기반 스냅 + 속도 기반 조기 확정, 두 경로 모두 API에
존재함이 확인됨) — 단, 정확한 기본 px/dp/velocity 수치 자체는 이번
검색으로 문서 본문에서 확인하지 못했다(필드/메서드 존재는 확인, 기본값
수치는 **🚧 미확정**).** 이건 `swipe-actions.md`에서 확인한 Android의
"거리(50%) 또는 속도" 이중 확정 모델과 구조적으로 동일한 패턴이다 — 같은
플랫폼 팀이 같은 설계 철학을 재사용했다는 정황.

모달 바텀시트(`BottomSheetDialog`)의 취소 트리거는 명시적으로 문서화되어
있다:

> `cancel()` — "This function can be called from a few different use
> cases, including **Swiping the dialog down** or calling `dismiss()`
> from a `BottomSheetDialogFragment`, **tapping outside a dialog**,
> etc..."
> — [Android Developers, `BottomSheetDialog`](https://developer.android.com/reference/com/google/android/material/bottomsheet/BottomSheetDialog)

**[표준].** 이게 4번(스크림 탭+드래그 공존)의 Android 쪽 직접 답이다.

### iOS — 정성적 스위치는 있으나 정확한 수치는 미확정

> `isModalInPresentation` — "A Boolean value indicating whether the view
> controller enforces a modal behavior." "The default value of this
> property is `false`. When you set it to `true`, UIKit ignores events
> outside the view controller's bounds and **prevents the interactive
> dismissal** of the view controller while it is onscreen."
> — [Apple Developer Documentation, `UIViewController.isModalInPresentation`](https://developer.apple.com/documentation/uikit/uiviewcontroller/ismodalinpresentation)

**[표준].** 기본값(`false`)에서는 (a) 인터랙티브 드래그 닫기, (b) 뷰
컨트롤러 바깥(=배경 딤 영역) 이벤트 처리 — 둘 다 활성화되어 있다는 게
공식 문서의 직접 진술이다. "탭하면 닫힌다"는 단어 자체는 이 문서에
없지만, "이벤트를 무시하지 않는다"는 서술이 논리적으로 함의하는 바다.
정확한 드래그 거리/속도 임계값(px, pt, 또는 %)은 Android처럼 공개
필드/메서드로 노출돼 있지 않다 — **🚧 미확정**.

### 판정

| 판단 | 라벨 | 근거 |
|---|---|---|
| Android는 거리(hideFriction 기반) 또는 속도(significantVelocityThreshold) 중 하나로 드래그 닫기가 확정되는 이중 모델을 공식 API로 노출한다 | [표준] (존재 확인) / 🚧 미확정 (정확한 기본 수치) | `BottomSheetBehavior` 필드/메서드 |
| iOS는 기본적으로 드래그 닫기와 배경 탭 처리가 모두 활성화되어 있다(끄려면 `isModalInPresentation=true`) | [표준] | `isModalInPresentation` 공식 문서 |
| iOS의 정확한 드래그 커밋 거리/속도 수치 | **🚧 미확정** | 공식 문서에 수치 없음 |

---

## 4. 배경(스크림) 탭으로 닫기와 드래그로 닫기의 공존

이미 3번에서 양쪽 다 확인됐다 — 재정리만 한다.

| 플랫폼 | 스크림 탭 닫기 | 드래그 닫기 | 공존 여부 | 라벨 |
|---|---|---|---|---|
| Android (모달, `BottomSheetDialog`) | 지원 ("tapping outside a dialog") | 지원 ("Swiping the dialog down") | 같은 `cancel()`이 두 트리거를 동등하게 취급 | [표준] |
| iOS (기본값) | 지원 시사(이벤트를 무시하지 않음) | 지원 (인터랙티브 dismiss 기본 활성) | 같은 플래그(`isModalInPresentation`)가 둘 다 묶어서 켜고 끔 | [표준] |

**두 플랫폼 모두 "스크림 탭"과 "드래그 닫기"를 별개 기능이 아니라 하나의
스위치로 묶어서 설계했다는 공통점이 있다** — Android는 `cancel()` 하나가
두 입력을 동일 취급, iOS는 `isModalInPresentation` 하나가 두 입력을
동시에 켜고 끈다. 이 대칭성 자체는 두 공식 문서에서 각각 확인된
사실이므로 [표준]으로 진술한다.

---

## 5. 내부 스크롤 콘텐츠 vs 시트-닫기 드래그의 우선순위

사용자가 이 항목은 "C10에 없으면 🚧 미확정 + 8번 오염방지 후보"로
표시하라고 지정했다. 조사 결과: **두 플랫폼 모두 이 정확한 조합(시트
안의 스크롤 가능한 콘텐츠 vs 시트 자체를 드래그로 닫기)에 대해 API
레벨의 공식 스위치를 이미 가지고 있다** — CONFLICTS.md의 C10(브라우저
`touch-action` 기반 실측)과는 완전히 다른 층위의, 네이티브 프레임워크
자체 중재 메커니즘이다.

### iOS

> `prefersScrollingExpandsWhenScrolledToEdge` — "A Boolean value that
> determines whether scrolling expands the sheet to a larger detent."
> "The default value is `true`, which means if the sheet can expand to a
> larger detent than `selectedDetentIdentifier`, **scrolling up in the
> sheet increases its detent instead of scrolling the sheet's content.
> After the sheet reaches its largest detent, scrolling begins.**"
> "Set this value to `false` if you want to avoid letting a scroll
> gesture expand the sheet."
> — [Apple Developer Documentation, `UISheetPresentationController.prefersScrollingExpandsWhenScrolledToEdge`](https://developer.apple.com/documentation/uikit/uisheetpresentationcontroller/prefersscrollingexpandswhenscrolledtoedge)

**[표준] — 단, 위로 스크롤(확장) 방향만 명시적으로 설명한다.** 콘텐츠가
맨 위로 스크롤된 상태에서 아래로 더 당길 때 "시트가 축소/닫히는가,
아니면 스크롤뷰가 그냥 바운스하는가"라는 **반대 방향(닫기)의 대칭
동작은 이 문서에 명시돼 있지 않다.** 이건 실제로 대부분의 iOS 시트
구현에서 자연스럽게 기대되는 동작이지만(위로 스크롤=확장이 문서화됐다면
아래로 당김=축소/닫기가 대칭적으로 있을 개연성은 높다), **공식 문서
문장으로 직접 확인하지 못했다 — 🚧 미확정.**

### Android

> `setDraggableOnNestedScroll(boolean draggableOnNestedScroll)` — "Sets
> whether this bottom sheet can be collapsed/expanded by dragging on
> the nested scrolling child view." / `isDraggableOnNestedScroll()`
> (getter, 대응 메서드).
> — [Android Developers, `BottomSheetBehavior#setDraggableOnNestedScroll()`](https://developer.android.com/reference/com/google/android/material/bottomsheet/BottomSheetBehavior#setDraggableOnNestedScroll(boolean))

**[표준].** Android는 이 문제를 정면으로 다루는 전용 API를 공식
제공한다 — "중첩 스크롤 자식 뷰 위에서의 드래그로 시트를 접고/펼 수
있는지"를 개발자가 직접 켜고 끌 수 있다. 이건 `CoordinatorLayout`의
중첩 스크롤(nested scrolling) 메커니즘과 `BottomSheetBehavior`가
공식적으로 통합돼 있다는 뜻이다.

### 판정 — 오염방지 후보 표시

| 판단 | 라벨 | CONFLICTS.md 연결 |
|---|---|---|
| Android는 "시트 안 중첩 스크롤 vs 시트 드래그" 우선순위를 다루는 전용 공식 API(`setDraggableOnNestedScroll`)가 존재한다 | [표준] | C10에는 없음 — 네이티브 프레임워크 전용 개념이라 브라우저 실측과 별개 |
| iOS는 "스크롤 위로 확장" 방향만 공식 문서화되어 있고, "스크롤 맨 위에서 아래로 당겨 닫기" 대칭 동작은 미확정 | [표준](확장 방향) + 🚧 미확정(축소/닫기 방향) | 위와 동일 |

**8번(오염 방지) 후보로 표시**: iOS의 "축소/닫기 방향 대칭 동작 미확정"
부분과, 웹 구현(이 프로젝트 CONFLICTS.md의 실제 대상)에서 바텀시트를
직접 만들 때 "시트 내부 스크롤 콘텐츠"와 "시트를 닫는 드래그"가 같은
세로축을 공유하는 문제는 **C10이 다루는 2자 충돌(Drag↔Scroll) 하나가
아니라, "시트 컨테이너 자체의 드래그"와 "시트 안 콘텐츠의 스크롤"이라는
두 개의 서로 다른 스크롤/드래그 인식기가 중첩된 문제**다. 이건
`ux-standards-architecture.md` §3-2가 이미 예견한 "n중 중첩" 카테고리에
정확히 해당한다 — 이 문서에서 해소하지 않고 표시만 해 둔다.

---

## CONFLICTS.md 연결

| 시나리오 | 연결 | 비고 |
|---|---|---|
| 시트를 세로로 드래그해서 닫는 동작 자체 (콘텐츠 없이 시트만) | [C10 — Drag ↔ Scroll](/CONFLICTS.md#c10--drag--scroll) | 시트를 감싼 배경 페이지가 스크롤 가능한 경우, 시트 드래그와 배경 스크롤의 축 경쟁은 C10 실측이 그대로 적용됨 |
| 시트 내부의 스크롤 가능한 콘텐츠와 시트 자체의 닫기 드래그 우선순위 | **연결 없음 — 🚧 미확정 + 오염방지(§3-2 n중 중첩) 후보** | 5번 참조. C10은 2자 충돌만 다루고 이 문제는 중첩 소유권 문제 |
| 시트를 열기 위한 트리거(탭/버튼)와 시트 자체의 드래그 | 해당 없음 | 이 컴포넌트는 롱프레스 트리거를 쓰지 않아 5/6번 문서와 겹치지 않음 |

---

## 출처 전체 목록

- [Apple Developer Documentation — `UISheetPresentationController.Detent`](https://developer.apple.com/documentation/uikit/uisheetpresentationcontroller/detent)
- [Apple Developer Documentation — `UISheetPresentationController.prefersScrollingExpandsWhenScrolledToEdge`](https://developer.apple.com/documentation/uikit/uisheetpresentationcontroller/prefersscrollingexpandswhenscrolledtoedge)
- [Apple Developer Documentation — `UISheetPresentationController.largestUndimmedDetentIdentifier`](https://developer.apple.com/documentation/uikit/uisheetpresentationcontroller/largestundimmeddetentidentifier)
- [Apple Developer Documentation — `UISheetPresentationController.prefersGrabberVisible`](https://developer.apple.com/documentation/uikit/uisheetpresentationcontroller/prefersgrabbervisible)
- [Apple Developer Documentation — `UIViewController.isModalInPresentation`](https://developer.apple.com/documentation/uikit/uiviewcontroller/ismodalinpresentation)
- [Apple Support — Search for places in Maps on iPhone](https://support.apple.com/guide/iphone/search-for-places-iph1df24639/ios)
- [Android Developers — `BottomSheetBehavior`](https://developer.android.com/reference/com/google/android/material/bottomsheet/BottomSheetBehavior)
- [Android Developers — `BottomSheetBehavior#setDraggableOnNestedScroll()`](https://developer.android.com/reference/com/google/android/material/bottomsheet/BottomSheetBehavior#setDraggableOnNestedScroll(boolean))
- [Android Developers — `BottomSheetDialog`](https://developer.android.com/reference/com/google/android/material/bottomsheet/BottomSheetDialog)
- [Material Design (archived) — Components, Bottom sheets](https://material.io/archive/guidelines/components/bottom-sheets.html)
- 확인 시도했으나 못 찾은 것: Apple 1st-party 공유 시트(Share Sheet)의
  드래그-닫기를 서술하는 지원 문서, Maps 카드의 정확한 스냅 포인트
  개수/완전 닫힘 가능 여부, iOS의 정확한 드래그 커밋 거리/속도 수치,
  iOS에서 "스크롤 맨 위 + 아래로 당김"이 시트를 축소/닫는지에 대한
  명시적 문서 — 전부 **🚧 미확정**으로 본문에 개별 표시했다.

**방법론 고지**: 이전 두 문서와 동일하게, [관성]/[표준] 라벨은 "공식
문서 검색 확인"이며 실기기 직접 관찰이 아니다.
