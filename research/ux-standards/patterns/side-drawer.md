# Component: Side Drawer (에지 스와이프로 열리는 사이드 드로어)

절차는 앞선 일곱 문서와 동일: `ux-standards-architecture.md` §1(우선순위)
→ §2(식별 신호) → §4(라벨) 순서를 따른다. 검증 방법도 동일하게 **검색을
통한 1차 문서 확인**이며, 실기기 직접 관찰이 아니다.

이 문서는 8개 중 마지막이며, 사용자가 미리 경고한 대로 **iOS 쪽은
정직하게 약한 근거만 나올 가능성이 높다** — 억지로 표준화하지 않는다.

---

## 식별 신호 (§2)

```
- 화면 왼쪽(또는 오른쪽) 가장자리를 안쪽으로 스와이프하면 메뉴 패널이
  슬라이드해 들어오는 디자인 → 사이드 드로어
- 상단에 hamburger(☰) 아이콘이 있고 탭하면 같은 패널이 열림 → 진입
  방법이 탭+스와이프 둘 다일 수 있음
- 패널이 열릴 때 배경이 어두워짐(스크림) → 모달형 드로어
- 이 컴포넌트는 화면 가장자리를 쓴다는 점에서 시스템 뒤로가기
  제스처(엣지 스와이프)와 같은 물리적 화면 영역을 두고 경합할 가능성이
  구조적으로 내재되어 있다 — 아래 3번 참조
```

---

## 1. iOS — 표준 패턴이 약하다 (확인된 사실)

### HIG에 전용 가이드 페이지가 없다

Apple Human Interface Guidelines에서 "side menu", "navigation drawer",
"hamburger"에 해당하는 전용 가이드 페이지를 검색으로 찾지 못했다 —
tab bars, sheets, lists 같은 다른 컴포넌트들이 각자 전용 HIG 페이지를
갖고 있는 것과 대조적이다.

**🚧 미확정이 아니라 확인된 부재로 기록한다**: 없다는 것 자체가
검색으로 확인된 사실이다(단, HIG 전체를 빠짐없이 훑은 것은 아니므로
"전용 페이지가 존재하지 않는다"를 100% 확정하지는 않는다 — 이 페이지들이
JavaScript로 렌더링되어 이번 세션에서 원문 전수 조사가 불가능했다는
한계도 있다). 이건 이 프로젝트가 다른 7개 컴포넌트에서 확인한 것과
질적으로 다르다 — 다른 컴포넌트는 API/HIG 양쪽에 최소한 부분적 근거가
있었는데, 이 컴포넌트는 iOS 쪽에 그런 1차 출처 자체가 약하다.

### 엣지 스와이프는 이미 시스템 뒤로가기가 선점하고 있다

> `UINavigationController.interactivePopGestureRecognizer` — "The
> navigation controller installs this gesture recognizer on its view and
> uses it to pop the topmost view controller off the navigation stack
> **when a person swipes horizontally from the leading edge of the
> screen**. Use this property to retrieve the gesture recognizer **and
> tie it to the behavior of other gesture recognizers in your user
> interface**."
> — [Apple Developer Documentation, `UINavigationController.interactivePopGestureRecognizer`](https://developer.apple.com/documentation/uikit/uinavigationcontroller/interactivepopgesturerecognizer)

**[표준] (원문 직접 확인) — 이번 조사의 핵심 발견이다.** iOS는 화면
왼쪽 가장자리(leading edge)에서 안쪽으로 스와이프하는 제스처를 **이미
시스템 뒤로가기 내비게이션에 공식 할당**해 뒀다. 공식 문서가 "다른
제스처 인식기의 동작과 묶어서 처리하라"고 직접 권고한다는 것 자체가,
같은 엣지 영역에 다른 제스처(사이드 드로어 열기 등)를 두면 **개발자가
수동으로 조정해야 하는 문제가 생긴다는 걸 Apple이 인지하고 있다**는
뜻이다. 자동 해소 메커니즘은 제공되지 않는다.

밑바탕 클래스의 엣지 인식 범위(정확히 몇 pt 폭인지)는 공개돼 있지
않다:

> `UIScreenEdgePanGestureRecognizer` — "A continuous gesture recognizer
> that interprets panning gestures that start near an edge of the
> screen." "You use this property to specify the edges where the gesture
> can start."
> — [Apple Developer Documentation, `UIScreenEdgePanGestureRecognizer`](https://developer.apple.com/documentation/uikit/uiscreenedgepangesturerecognizer)

**[표준] (존재 확인) — 정확한 엣지 인식 폭(pt)은 🚧 미확정.** "near an
edge"라고만 서술하고 수치를 공개하지 않는다 — `research/c10-sources.md`,
`carousel.md`에서 이미 반복 확인된 "Apple은 내부 상수를 잘 공개하지
않는다"는 패턴이 여기서도 반복된다.

### 판정

| 판단 | 라벨 | 근거 |
|---|---|---|
| iOS HIG에 사이드 드로어 전용 가이드 페이지가 없다(검색 범위 내) | 확인된 부재 (라벨 부여 보류 — 아래 참조) | 검색으로 못 찾음, HIG 전수 조사는 못 함 |
| iOS는 화면 왼쪽 엣지 스와이프를 시스템 뒤로가기에 이미 공식 할당했다 | [표준] | `interactivePopGestureRecognizer` 공식 문서, 원문 확인 |
| 이 때문에 커스텀 엣지 스와이프 드로어를 만들면 개발자가 직접 두 제스처를 조정해야 한다 | [표준] (공식 문서의 권고 문구에서 직접 도출) | 같은 문서의 "tie it to the behavior of other gesture recognizers" |
| 정확한 엣지 인식 폭(pt) | **🚧 미확정** | 공식 문서에 수치 없음 |

**라벨에 대한 메모**: "HIG 페이지가 없다"는 판단 자체에는 §4의 4개
라벨 중 어느 것도 정확히 들어맞지 않는다 — [표준]은 출처가 있다는
뜻이고 [미확정]은 상충하거나 불명확하다는 뜻인데, 이건 "검색해서 없는
것을 확인했다"는 제3의 상태다. 억지로 라벨을 끼워 맞추지 않고 그대로
서술한다.

---

## 2. Android — Material `DrawerLayout` 공식 스펙

### 클래스 정의와 배치

> `DrawerLayout` — "DrawerLayout acts as a top-level container for
> window content that allows for interactive 'drawer' views to be pulled
> out from one or both vertical edges of the window. Drawer positioning
> and layout is controlled using the `android:layout_gravity` attribute
> on child views... Note that you can only have one drawer view for each
> vertical edge of the window."
> — [Android Developers, `DrawerLayout`](https://developer.android.com/reference/androidx/drawerlayout/widget/DrawerLayout)

**[표준] (원문 직접 확인).**

Material Design(archived 공식 스펙)은 드로어 폭까지 수치로 규정한다:

> "Maximum width: The maximum width of the nav drawer is **280dp on
> mobile and 320dp on tablet**. This is calculated by multiplying the
> standard increment by five (the standard increment is 56dp on mobile
> and 64dp on tablet)." "Resting elevation 16dp."
> — [Material Design (archived), Patterns — Navigation drawer](https://material.io/archive/guidelines/patterns/navigation-drawer.html)

**[표준] (Google 공식 아카이브 스펙, 원문 직접 확인).** 정확한 **엣지
스와이프 인식 폭(열기를 시작하는 데 필요한 가장자리 폭)**은 이 페이지의
"Behavior" 섹션까지 확인했으나 구체적 dp 수치를 찾지 못했다 — **🚧
미확정.**

### Android는 이 정확한 충돌을 이미 겪었고, 공식 패치로 대응했다

> "**DrawerLayout now takes into account the size of any gesture
> navigation insets, expanding the area available to users to long press
> and swipe to open the drawer when gesture navigation is enabled.**"
> — [Android Jetpack, `androidx.drawerlayout` release notes, v1.1.0 (2020-06-24)](https://developer.android.com/jetpack/androidx/releases/drawerlayout)

**[표준] (원문 직접 확인) — 이번 조사에서 가장 중요한 발견이다.**
Android는 시스템 제스처 내비게이션(엣지 스와이프 뒤로가기)이 도입된
뒤, `DrawerLayout`의 엣지 인식 영역이 시스템 제스처 인셋(inset)과
겹쳐서 좁아지는 문제를 실제로 겪었고, **라이브러리 버전 1.1.0에서
공식적으로 이를 보정**했다 — 시스템 제스처 인셋 크기를 고려해 드로어를
열 수 있는 영역을 확장했다. 동시에 "long press and swipe"라는 표현으로
**롱프레스도 드로어 열기의 대체 진입 경로로 병기**하고 있다는 것도
이 한 문장에서 확인된다.

이건 이번 문서가 3번에서 다룰 "iOS/웹에서 아직 안 풀린 문제"를 Android가
공식 라이브러리 패치로 실제 해결한 사례다 — 단, 이것 역시 §3-2(오염
방지)의 일반 해법으로 일반화하지 않는다. Android 자체의 특정 버전 패치
내용일 뿐이다.

### 판정

| 판단 | 라벨 | 근거 |
|---|---|---|
| Android `DrawerLayout`은 좌우 엣지에서 끌어낼 수 있는 표준 위젯으로 공식 문서화되어 있다 | [표준] | 클래스 레퍼런스 원문 |
| 드로어 최대 폭은 모바일 280dp, 태블릿 320dp로 공식 규정되어 있다 | [표준] | Material archived 스펙 원문 |
| Android는 시스템 제스처 내비게이션과 드로어 엣지 스와이프의 충돌을 실제로 겪었고 라이브러리 패치(v1.1.0)로 인식 영역을 확장해 대응했다 | [표준] | Jetpack 공식 릴리스 노트 원문 |
| 정확한 엣지 인식 폭(dp) 수치 | **🚧 미확정** | 공식 문서에서 확인 못함 |

---

## 3. 모바일 브라우저의 뒤로가기 제스처와의 물리적 경합 — 새로운 충돌, 오염방지 후보

사용자가 지정한 대로 이 항목은 **C10에 없는 새로운 충돌**이며,
새로 실측하지 않고 **문제로만 명시**한다.

**관찰된 사실(추측 아님)**: 모바일 Safari와 Android Chrome은 둘 다
화면 가장자리에서 안쪽으로 스와이프하면 브라우저 자체의 뒤로가기(이전
페이지로 이동)를 실행하는 제스처를 갖고 있다 — 이건 위 1번에서 확인한
iOS 네이티브 앱의 `interactivePopGestureRecognizer`와 **정확히 같은
화면 물리적 영역**(왼쪽 가장자리)을 쓴다. 웹페이지 안에 사이드 드로어를
만들어 같은 가장자리에서 `touchstart`/`touchmove`로 열기를 구현하면,
**브라우저 네이티브 뒤로가기 제스처와 물리적으로 같은 입력을 두고
경합한다.**

이 문제는 CONFLICTS.md의 어떤 기존 C번호에도 없다:
- C10(Drag↔Scroll)은 콘텐츠 내부의 스크롤 대 드래그 문제이지, 브라우저
  자체의 시스템 제스처(페이지 밖 내비게이션)와의 충돌이 아니다.
- 나머지 C1~C13 전부 "웹페이지 안에서 일어나는 두 제스처"를 다루지,
  "웹페이지 대 브라우저 크롬(chrome)의 시스템 제스처"를 다루지 않는다.

**🚧 미확정 + 8번(오염 방지) 섹션 후보로 표시한다.** 구체적으로 남는
질문들(전부 미확정, 이 문서에서 답하지 않음):
- 브라우저 뒤로가기 제스처가 인식하는 정확한 엣지 폭(px)은 얼마이며
  플랫폼/브라우저별로 다른가
- `touch-action`이나 다른 CSS 선언으로 이 특정 시스템 제스처를 막을 수
  있는가, 아니면 원천적으로 웹 콘텐츠가 개입할 수 없는 영역인가
- 만약 페이지 내부에 자체 사이드 드로어를 만든다면, 웹 개발자 관행상
  "왼쪽 가장자리를 피하고 오른쪽에서 여는" 회피책이 실제로 통용되는지

---

## CONFLICTS.md 연결

| 시나리오 | 연결 | 비고 |
|---|---|---|
| 드로어가 열린 뒤 드로어 내부 콘텐츠의 세로 스크롤과 드로어 자체를 닫는 스와이프의 경합 | [C10 — Drag ↔ Scroll](/CONFLICTS.md#c10--drag--scroll) | 재실측 없음, 연결만 — bottom-sheet.md의 5번 항목과 구조적으로 같은 유형의 중첩 문제 |
| 사이드 드로어 엣지 스와이프와 브라우저 시스템 뒤로가기 제스처의 물리적 경합 | **연결 없음 — 새로운 충돌, 🚧 미확정, 오염방지 후보** | 위 3번 참조. C1~C13 어디에도 해당 없음 |

---

## 다음 문서와의 접점

이 컴포넌트는 롱프레스를 주 트리거로 쓰지 않으므로(Android
`DrawerLayout`이 대체 경로로 롱프레스를 병기한다는 점은 2번에서
확인했으나 주 트리거는 아님) 5/6번(multi-select, context-menu)과 강하게
겹치지 않는다. 다만 Android의 "long press and swipe" 병기 사실은 8번
오염방지 작업 시 참고할 만하다.

---

## 출처 전체 목록

- [Apple Developer Documentation — `UINavigationController.interactivePopGestureRecognizer`](https://developer.apple.com/documentation/uikit/uinavigationcontroller/interactivepopgesturerecognizer) (원문 직접 확인)
- [Apple Developer Documentation — `UIScreenEdgePanGestureRecognizer`](https://developer.apple.com/documentation/uikit/uiscreenedgepangesturerecognizer) (원문 직접 확인)
- [Android Developers — `DrawerLayout`](https://developer.android.com/reference/androidx/drawerlayout/widget/DrawerLayout) (원문 직접 확인)
- [Android Jetpack — `androidx.drawerlayout` release notes](https://developer.android.com/jetpack/androidx/releases/drawerlayout) (원문 직접 확인, v1.1.0 항목)
- [Material Design (archived) — Patterns, Navigation drawer](https://material.io/archive/guidelines/patterns/navigation-drawer.html) (원문 직접 확인)
- [C10 — Drag ↔ Scroll](/CONFLICTS.md#c10--drag--scroll) (재사용, 재실측 아님)
- 확인 시도했으나 못 찾은 것: iOS HIG의 사이드 드로어 전용 페이지(전수
  조사 불가), iOS/Android 각각의 정확한 엣지 인식 폭(pt/dp) 수치, 모바일
  Safari/Chrome의 뒤로가기 제스처 정확한 인식 폭과 `touch-action`으로의
  차단 가능 여부 — 전부 **🚧 미확정**으로 본문에 개별 표시했다.

**방법론 고지**: 이전 문서들과 동일하게, [관성]에 해당하는 확인은
"공식 지원 문서 검색 확인"이며 실기기 직접 관찰이 아니다. 이번 문서는
1st-party 소비자 앱 도움말을 인용하지 않았다 — 사이드 드로어는 iOS
1st-party 앱에서 흔한 패턴이 아니라는 정황과도 일치한다(직접 검증하지
않은 정황 판단이므로 이 문장 자체는 결론에 포함하지 않는다).
