# Component: Tab Swipe (좌우 스와이프로 탭 전환)

절차는 앞선 여섯 문서와 동일: `ux-standards-architecture.md` §1(우선순위)
→ §2(식별 신호) → §4(라벨) 순서를 따른다. 검증 방법도 동일하게 **검색을
통한 1차 문서 확인**이며, 실기기 직접 관찰이 아니다.

---

## 식별 신호 (§2)

```
- 화면 하단에 탭 바(아이콘+라벨)가 있고, 탭을 눌러야만 화면이 바뀌는
  디자인 → iOS 기본값(아래 1번), 스와이프 기대하면 안 됨
- 화면 상단/중간에 가로로 나열된 탭(밑줄/알약 형태 인디케이터)이 있고
  좌우로 스와이프하면 콘텐츠 전체가 옆으로 넘어가는 디자인 → Android
  기본 패턴(아래 2번)에 해당할 가능성
- 탭 콘텐츠 자체가 세로로 스크롤되는 리스트/페이지라면 → 가로 탭
  전환 스와이프와 세로 스크롤의 축 충돌 문제. C9 참조
- 탭이 하단 탭 바인지 상단 세그먼트/탭 스트립인지에 따라 이 컴포넌트의
  "표준" 판단이 완전히 달라진다는 점 자체가 이번 조사의 핵심 발견
  (아래 판정 참조)
```

---

## 1. iOS — `UITabBarController`는 스와이프를 지원하지 않는다 (확인됨)

> `UITabBarController` — "The tab bar interface displays tabs at the
> bottom of the window for selecting between the different modes...
> **When the user selects a specific tab, the tab bar controller
> displays the root view of the corresponding view controller**...
> (**User taps** always display the root view of the tab, regardless of
> which tab was previously selected.)"
> — [Apple Developer Documentation, `UITabBarController`](https://developer.apple.com/documentation/uikit/uitabbarcontroller)

**[표준] (원문 직접 확인).** 클래스 전체 설명에서 탭 전환 메커니즘은
오직 "User taps"로만 서술된다. 스와이프 관련 언급은 문서 전체에 단
한 곳뿐이며, 그것도 tvOS 전용이다:

> "In tvOS, swiping down from the tab bar moves focus into the content
> view... **In iOS, the tab bar always remains in focus at the bottom of
> the screen.**"
> — [Apple Developer Documentation, `UITabBarController`](https://developer.apple.com/documentation/uikit/uitabbarcontroller)

**[표준] (원문 직접 확인) — 이번 조사에서 사용자가 지정한 "주의, 확인
후 라벨링" 항목의 답이다.** iOS의 표준 탭 바 컨트롤러는 좌우 스와이프로
탭을 전환하는 기능을 **API 레벨에서 아예 제공하지 않는다.** 이건
추측이나 3자 포럼 의견이 아니라 공식 클래스 레퍼런스 원문에서 직접
확인한 사실이다.

### App Store 등 "특정 앱의 자체 구현" 사례 — 확인하지 못함

Apple 공식 문서나 WWDC 세션 트랜스크립트(예: WWDC22 "Explore navigation
design for iOS")에서 특정 1st-party 앱이 하단 탭 바를 스와이프로
전환하도록 커스텀 구현했다는 서술은 **찾지 못했다.** 위 WWDC 세션의
"swipe" 언급은 전부 **뒤로가기 인터랙티브 스와이프**(내비게이션 스택
pop)에 관한 것이지, 탭 전환에 관한 것이 아니었다 — 이것도 원문으로
확인한 사실이다:

> "As views push in, **it feels natural to swipe left to right to go
> back** to where you came from without losing access to hierarchies in
> other tabs where your state should be preserved."
> — [Apple Developer, WWDC22 — Explore navigation design for iOS](https://developer.apple.com/videos/play/wwdc2022/10001/) (트랜스크립트 원문)

**🚧 미확정.** "특정 앱이 하단 탭 바를 스와이프로 전환하게 커스텀
구현한 사례"는 이번 검색 범위(Apple 공식 문서·WWDC 트랜스크립트)에서
확인하지 못했다 — 존재하지 않는다는 뜻이 아니라, 1차 출처로 확인하지
못했다는 뜻이다. 추측으로 채우지 않는다.

---

## 2. Android — `ViewPager2` + `TabLayout`은 공식 문서가 명시하는 표준 패턴

> "Create swipe views with tabs using ViewPager2 — ... **You can create
> swipe views for switching between tabs** and how to show a title strip
> instead of tabs." / "**Implement swipe views** — You can create swipe
> views using AndroidX's `ViewPager2` widget."
> — [Android Developers, Create swipe views with tabs using ViewPager2](https://developer.android.com/guide/navigation/navigation-swipe-view-2)

**[표준] (원문 직접 확인).** Android는 iOS와 정반대다 — "스와이프로 탭
전환"이 공식 문서 제목에 그대로 등장하는, 명시적으로 권장되는 1급
패턴이다. `TabLayoutMediator`로 `TabLayout`(가로 탭 인디케이터)과
`ViewPager2`(스와이프 가능한 페이지 콘텐츠)를 연결하는 게 표준
구현법으로 문서화되어 있다.

탭 개수가 많을 때의 처리도 공식 문서화되어 있다:

> "If you have a large or potentially infinite number of pages, set the
> `android:tabMode` attribute on your `TabLayout` to `\"scrollable\"`,
> which prevents `TabLayout` from trying to fit all tabs on the screen
> at once and allows users to scroll through the list of tabs."
> — [Android Developers, Create swipe views with tabs using ViewPager2](https://developer.android.com/guide/navigation/navigation-swipe-view-2)

**[표준] (검색 결과 요약으로 확인 — 이 세션에서 이 특정 문장은 원문
페이지 재조회로 직접 재확인하지 못했다, 🚧 부분 미확정).** 나머지
인용문("swipe views for switching between tabs", "Implement swipe
views")은 이 세션에서 원문 HTML을 직접 확인했다.

### 판정 — 핵심 발견

| 판단 | 라벨 | 근거 |
|---|---|---|
| iOS 표준 하단 탭 바(`UITabBarController`)는 스와이프 전환을 지원하지 않는다 — 탭으로만 전환된다 | [표준] | 공식 클래스 레퍼런스 원문, 스와이프 언급은 tvOS 전용 1곳뿐 |
| Android는 `ViewPager2`+`TabLayout` 조합으로 스와이프 탭 전환을 공식 문서가 직접 권장한다 | [표준] | 공식 가이드 문서 제목·본문 원문 |
| **결론: "탭 전환에 스와이프를 쓰는 게 표준인가"의 답은 플랫폼마다 정반대다** — 이건 이번 조사에서 가장 명확하게 갈린 이분법이다 | [표준] (위 두 사실의 직접 귀결) | 다른 6개 컴포넌트는 대부분 스펙트럼/뉘앙스가 있었는데, 이 컴포넌트는 두 플랫폼이 정확히 반대 방향으로 표준화되어 있다는 점이 특이하다 |
| iOS 1st-party 앱이 하단 탭 바를 스와이프 가능하게 커스텀 구현한 확인된 사례 | **🚧 미확정** | 공식 문서·WWDC 트랜스크립트에서 확인 못함 |

---

## 3. 세로 스크롤 콘텐츠 안의 가로 탭 전환 스와이프 — 새 실측 아님

사용자 지정대로 새로 조사하지 않고 연결만 한다.

- Android `ViewPager2`로 구현한 스와이프 탭 안에 세로로 스크롤되는
  콘텐츠(리스트 등)가 있을 때의 축 충돌은
  [C9 — Drag ↔ Swipe](/CONFLICTS.md#c9--drag--swipe)의 실측이 그대로
  적용된다.
- iOS는 표준 `UITabBarController`에 이 문제가 원천적으로 없다(스와이프
  전환 자체를 안 쓰므로) — 다만 위에서 확인하지 못한 "커스텀 스와이프
  탭 구현"을 실제로 한다면 동일하게 C9이 적용될 것이다.

---

## CONFLICTS.md 연결

| 시나리오 | 연결 | 비고 |
|---|---|---|
| Android `ViewPager2` 탭 전환 스와이프와 탭 내부 세로 스크롤의 축 충돌 | [C9 — Drag ↔ Swipe](/CONFLICTS.md#c9--drag--swipe) | 재실측 없음, 연결만 |
| iOS 커스텀 스와이프 탭 구현 시의 동일 축 충돌 | [C9 — Drag ↔ Swipe](/CONFLICTS.md#c9--drag--swipe) (가정적) | 실제 구현 사례를 확인 못해 가정적 연결 — 🚧 미확정 |

---

## 다음 문서와의 접점

이 컴포넌트는 롱프레스를 트리거로 쓰지 않으므로 5/6번(multi-select,
context-menu)의 롱프레스 오염 문제와 겹치지 않는다. 다른 문서들과
식별 신호 충돌도 없다.

---

## 출처 전체 목록

- [Apple Developer Documentation — `UITabBarController`](https://developer.apple.com/documentation/uikit/uitabbarcontroller) (원문 직접 확인)
- [Apple Developer — WWDC22, Explore navigation design for iOS](https://developer.apple.com/videos/play/wwdc2022/10001/) (트랜스크립트 원문 직접 확인)
- [Android Developers — Create swipe views with tabs using ViewPager2](https://developer.android.com/guide/navigation/navigation-swipe-view-2) (본문 대부분 원문 직접 확인, `tabMode="scrollable"` 인용문만 검색 요약)
- 확인 시도했으나 못 찾은 것: iOS 1st-party 또는 유명 앱이 하단 탭 바를
  스와이프로 전환하게 커스텀 구현한 공식 확인 사례, Apple HIG의 "Tab
  bars" 페이지 원문(JS 렌더링이라 이 세션에서 텍스트 추출 불가) — 전부
  **🚧 미확정**으로 본문에 개별 표시했다.

**방법론 고지**: 이전 문서들과 동일하게, [관성]에 해당하는 확인은 전부
"공식 지원 문서 검색 확인"이며 실기기 직접 관찰이 아니다. 이번 문서는
[관성] 라벨이 사용되지 않았다 — 두 플랫폼 모두 API/공식 가이드 문서
레벨에서 명확한 답이 나와서 1st-party 소비자 앱 사례를 추가로 인용할
필요가 없었다.
