# Component: Carousel (가로 스크롤 갤러리, 스냅 여부)

절차는 앞선 세 문서와 동일: `ux-standards-architecture.md` §1(우선순위)
→ §2(식별 신호) → §4(라벨) 순서를 따른다. 검증 방법도 동일하게 **검색을
통한 1차 문서 확인**이며, 실기기 직접 관찰이 아니다.

---

## 식별 신호 (§2)

```
- 카드/이미지가 가로로 나열되어 있고 화면 밖으로 일부가 잘려 보임
  ("다음 카드가 살짝 보인다") → 캐러셀
- 카드 폭이 화면 전체와 같고 한 번에 하나씩만 보임 → 풀스크린/페이징형
  캐러셀 (예: 사진 앱 전체화면 보기)
- 카드 폭이 제각각이고(하나는 크게, 나머지는 작게) → 히어로(hero)형
- 카드가 균일한 작은 폭으로 여러 개 동시에 보임 → 멀티브라우즈형
- 스크롤을 멈췄을 때 카드 경계가 화면 경계에 딱 맞춰 정렬되면 → 스냅
  적용됨. 어중간한 위치에 걸쳐 멈추면 → 자유 스크롤(스냅 없음)
- 카드 안에 버튼/링크 등 자체 탭 액션이 있으면 → 2번 항목(탭↔스와이프
  경계) 확인 필요
- 세로로 스크롤되는 페이지 안에 이 가로 캐러셀이 끼어 있으면 →
  reorderable-list.md/swipe-actions.md와 달리 축이 다른 두 스크롤이
  중첩된 구조. C9 참조
```

---

## 1. 스냅이 표준인가, 자유 스크롤이 표준인가 — 콘텐츠 유형별로 다른가

### iOS — API 레벨 (표준 스펙): 스펙트럼으로 존재, 강제 없음

`UICollectionLayoutSectionOrthogonalScrollingBehavior`(iOS 13+ 컴포지셔널
레이아웃)는 캐러셀류 가로 스크롤의 정지 방식을 6단계 열거형으로
공식 정의한다:

> `none` — "The section does not allow users to scroll its content
> orthogonally." (가로 스크롤 자체 없음)
> `continuous` — "The section allows users to scroll its content
> orthogonally with continuous scrolling." (자유 스크롤, 스냅 없음)
> `continuousGroupLeadingBoundary` — "The section allows users to scroll
> its content orthogonally, coming to a natural stop at the leading
> boundary of the visible group." (약한 스냅 — 그룹 선행 경계에서만
> 자연스럽게 멈춤)
> `paging` — "The section allows users to page its content
> orthogonally." (화면 폭 단위 페이징)
> `groupPaging` — "The section allows users to page its content
> orthogonally one group at a time." (그룹 단위 페이징, 선행 정렬)
> — [Apple Developer Documentation, `UICollectionLayoutSectionOrthogonalScrollingBehavior`](https://developer.apple.com/documentation/uikit/uicollectionlayoutsectionorthogonalscrollingbehavior) 및 각 케이스 페이지 (`none`, `continuous`, `continuousGroupLeadingBoundary`, `paging`, `groupPaging` 개별 문서)

**[표준] (5개 케이스는 이번 세션에서 공식 JSON API로 직접 재확인함).**

`groupPagingCentered`("그룹 단위 페이징, 각 그룹을 중앙 정렬")는 이번
세션에서 발급받은 검색 결과 요약으로만 확인했고, 같은 방식으로 직접
JSON을 재조회하려 했으나 접속 실패가 반복되어 **개별 재검증하지
못했다** — 나머지 5개와 동일한 명명 패턴("~ one at a time" 계열
문장)이라 신뢰도는 높지만, 엄밀히는 **🚧 부분 미확정**으로 표시한다.
— [Apple Developer Documentation, `groupPagingCentered`](https://developer.apple.com/documentation/uikit/uicollectionlayoutsectionorthogonalscrollingbehavior/grouppagingcentered)

**결론**: iOS 플랫폼은 자유 스크롤부터 하드 페이징까지 **스펙트럼을
공식 API로 제공**하고, 어느 걸 쓸지는 콘텐츠 유형에 따라 개발자가
선택하도록 설계돼 있다 — "스냅이 표준"이라거나 "자유 스크롤이 표준"이라고
한쪽으로 단정할 수 없다. 이건 억지로 하나를 고르지 않고 있는 그대로
[표준]으로 진술한다.

### iOS — 1st-party 앱 실제 사례 (Photos)

> "**Swipe left or right on the photo to keep browsing**, or swipe the
> thumbnails below the photo to quickly jump forward or back."
> — [Apple Support, View photos and videos on iPhone](https://support.apple.com/guide/iphone/iph3d267610/ios)

**[관성] (Apple 1st-party 앱 공식 지원 문서, 기기 미확인).** 전체화면 사진 보기는 한 번에 사진
한 장씩 넘어가는 **페이징형**(위 `paging`/`groupPaging`류에 해당) —
콘텐츠가 "한 번에 하나씩 온전히 봐야 하는 것"(사진 감상)일 때 하드
페이징을 쓴다는 실제 사례.

> "Under each collection heading, **swipe left or right to see different
> collections**."
> — [Apple Support, Browse your photo collections on iPhone](https://support.apple.com/guide/iphone/iph4f36c4148/ios)

**[관성] (Apple 1st-party 앱 공식 지원 문서, 기기 미확인).** 반면 컬렉션 목록(썸네일 여러 장을
훑어보는 용도)은 이 문서만으로는 스냅 여부를 명시하지 않는다 — "swipe
left or right to see"라는 표현은 스냅/자유 스크롤 어느 쪽으로도 읽힐 수
있다. **🚧 미확정**(정성적 사용자 안내문이라 기술적으로 스냅 여부를
구분하지 못함 — `reorderable-list.md`에서 이미 짚은 "소비자 도움말
문구의 한계"와 같은 패턴).

### Android — 공식 컴포넌트 문서: 전략별로 스냅을 "권장"

Material Design의 공식 캐러셀 컴포넌트 문서(GitHub 공식 저장소,
material-components-android)는 4가지 레이아웃 전략을 정의하고, 그중
3개에 대해 명시적으로 스냅을 권장한다:

> "There are four carousel layouts: **Multi-browse**, **Uncontained**,
> **Hero** (Start-aligned / Center-aligned), **Full-screen**." /
> "A start-aligned, **multi-browse strategy is the default strategy**
> for the carousel."
> "With the multi-browse strategy, **it is recommended to use the
> `CarouselSnapHelper` to snap to the nearest item**" (Hero, Full-screen
>섹션에도 동일 문장 반복)
> — [Material Components for Android (공식 GitHub 문서), Carousels](https://github.com/material-components/material-components-android/blob/master/docs/components/Carousel.md)

**[표준] (Google 공식 저장소 문서, material.io의 API 레퍼런스로도
링크됨).** Multi-browse(기본 전략)·Hero·Full-screen 세 전략 모두
`CarouselSnapHelper` 권장 — 즉 **Android의 기본 권장값은 스냅이다.**
단, **Uncontained 전략 섹션에는 `CarouselSnapHelper` 권장 문구가 없다**
— 이건 이 문서에서 실제로 확인된 차이이지 추측이 아니다. 콘텐츠가
"종횡비를 유지해야 하는 이미지"일 때 쓰는 전략(Uncontained)에서는
스냅을 권장하지 않는다는 뜻일 수 있으나, 이 문서가 그 이유를 직접
설명하지는 않는다 — 이유 자체는 **🚧 미확정**.

### 웹 표준(W3C) — 스냅은 3단계 강도로, 저자가 선택

이 프로젝트의 실제 대상(웹)에 가장 직접적으로 적용되는 답은 CSS Scroll
Snap Module의 `scroll-snap-type` 속성이다:

> `none` — "If specified on a scroll container, the scroll container
> must not snap."
> `mandatory` — "If specified on a scroll container, the scroll
> container is required to be snapped to a snap position when there are
> no active scrolling operations."
> `proximity` — "If specified on a scroll container, the scroll
> container may snap to a snap position at the termination of a scroll,
> at the discretion of the UA..."
> — [W3C, CSS Scroll Snap Module Level 1](https://www.w3.org/TR/css-scroll-snap-1/)

**[표준].** 웹 플랫폼도 네이티브와 동일하게 "강제 안 함(none) / UA
재량(proximity) / 강제(mandatory)"라는 스펙트럼을 제공한다 — 콘텐츠
유형별로 저자가 고르라는 설계 철학이 iOS·Android·W3C 세 곳 모두에서
동일하게 반복된다는 것 자체가 이번 조사의 핵심 발견이다.

추가로, 한 번에 몇 개까지 건너뛸 수 있는지(플링으로 여러 카드를 한
번에 넘기는지, 하나씩만 멈추는지)도 W3C 스펙에 명시돼 있다:

> `scroll-snap-stop: normal` — "The scroll container may pass over a
> snap position defined by this element during the execution of a
> scrolling operation." (여러 개 건너뛰기 가능, 초기값)
> `scroll-snap-stop: always` — "The scroll container must not pass over
> a snap position defined by this element... it must instead snap to
> the first of this element's snap positions that it encounters."
> (하나씩만 멈춤)
> — [W3C, CSS Scroll Snap Module Level 1 — `scroll-snap-stop`](https://www.w3.org/TR/css-scroll-snap-1/)

**[표준].**

### 판정

| 판단 | 라벨 | 근거 |
|---|---|---|
| 스냅/자유 스크롤 중 하나가 "표준"이라고 단정할 수 없다 — 세 플랫폼(iOS/Android/W3C) 모두 스펙트럼을 제공하고 콘텐츠 유형별 선택을 전제한다 | [표준] | 6단계 iOS enum, Android 전략별 권장 차등, W3C 3단계 strictness — 세 출처 일치 |
| Android의 기본 권장값은 스냅이다(멀티브라우즈=기본 전략+스냅 권장) | [표준] | 공식 GitHub 문서 |
| "온전히 하나씩 감상"류 콘텐츠(사진 전체화면)는 하드 페이징을 쓴다 | [관성] (iOS 1st-party 앱, 기기 미확인) | Apple Support Photos 문서 |
| "여러 개를 훑어보는" 콘텐츠(컬렉션 목록)가 스냅을 쓰는지 자유 스크롤인지 | **🚧 미확정** | 소비자 도움말 문구만으로는 기술적으로 구분 불가 |
| Uncontained 전략에서 스냅을 권장하지 않는 이유 | **🚧 미확정** | 공식 문서가 이유를 설명하지 않음 |

---

## 2. 캐러셀 카드에 자체 탭 액션이 있을 때 — 탭 vs 가로 스와이프 경계

### iOS — 정확히 이 문제를 위한 전용 API가 있다

> `delaysContentTouches` — "A Boolean value that determines whether the
> scroll view delays the handling of touch-down gestures." "If the value
> of this property is `true`, the scroll view delays handling the
> touch-down gesture until it can determine if scrolling is the intent.
> ... **The default value is `true`.**"
> `canCancelContentTouches` — "A Boolean value that controls whether
> touches in the content view always lead to tracking." "If the value of
> this property is `true` and a view in the content has begun tracking a
> finger touching it, and if the user drags the finger enough to
> initiate a scroll, **the view receives a `touchesCancelled(_:with:)`
> message and the scroll view handles the touch as a scroll**."
> — [Apple Developer Documentation, `UIScrollView.delaysContentTouches`](https://developer.apple.com/documentation/uikit/uiscrollview/delayscontenttouches) / [`canCancelContentTouches`](https://developer.apple.com/documentation/uikit/uiscrollview/cancancelcontenttouches)

**[표준].** 이건 이번 조사의 두 번째 핵심 발견이다. iOS는 "카드 안 버튼
탭"과 "가로 스와이프 시작"의 경합을 **기본값(둘 다 `true`)만으로 이미
해소**해 둔다:

1. 터치가 시작되면 스크롤뷰가 먼저 "이게 스크롤 의도인지" 판단할 때까지
   버튼에 터치를 넘기지 않고 지연시킨다(`delaysContentTouches`).
2. 버튼이 이미 눌림 상태를 시작했더라도, 손가락이 스크롤로 인식될 만큼
   움직이면 버튼은 `touchesCancelled`를 받고 스크롤이 그 터치를 가져간다
   (`canCancelContentTouches`).

이건 `swipe-actions.md`에서 확인한 iOS Pointer Events 계열의
`pointercancel` 모델, 그리고 `research/c10-sources.md`의 W3C
`pointercancel` 실측과 **개념적으로 동일한 패턴**(경합에서 진 쪽이
취소 이벤트를 받는다)이 UIKit 네이티브 위젯 레벨에서도 반복된다는
증거다.

### Android — 일반 터치 디스패치 메커니즘(캐러셀 전용은 아님)

Android에는 캐러셀 전용의 `delaysContentTouches` 대응 API는 검색으로
찾지 못했다. 대신 `ViewGroup`(RecyclerView/ViewPager2가 상속하는 기반
클래스)의 일반 터치 처리 메커니즘이 동일한 문제를 해결한다:

> "The `onInterceptTouchEvent()` method gives a parent the chance to see
> touch events before its children do. If you return `true` from
> `onInterceptTouchEvent()`, **the child view that was previously
> handling touch events receives an `ACTION_CANCEL`**, and the events
> from that point forward are sent to the parent's `onTouchEvent()`
> method... if you drag your finger across a child view horizontally,
> the child view no longer gets touch events, and the parent handles
> touch events by scrolling its contents."
> — [Android Developers, Manage touch events in a ViewGroup](https://developer.android.com/develop/ui/views/touch-and-input/gestures/viewgroup)

**[표준] (일반 플랫폼 메커니즘 확인 — 캐러셀/`RecyclerView` 전용으로
문서화된 것은 아님, 그 상위의 `ViewGroup` 레벨 메커니즘).** 판정 기준이
되는 정확한 이동 거리는 `research/c10-sources.md`에서 이미 확인한
`ViewConfiguration.getScaledTouchSlop()`(기본 8dp)가 그대로 관여할
개연성이 높으나, 이 문서가 캐러셀 맥락에서 그 상수를 명시적으로
언급하지는 않는다 — **🚧 미확정**(연결 개연성은 높지만 캐러셀 코드 경로에
그 상수가 그대로 쓰인다고 문서가 직접 말하지는 않음).

### 판정

| 판단 | 라벨 | 근거 |
|---|---|---|
| iOS는 "카드 탭 vs 캐러셀 스와이프" 경합을 스크롤뷰 기본값만으로 해소하는 전용 API가 있다 | [표준] | `delaysContentTouches`, `canCancelContentTouches` 둘 다 기본값 `true` |
| Android는 같은 문제를 캐러셀 전용이 아닌 `ViewGroup`의 일반 터치 인터셉트 메커니즘으로 해소한다 | [표준] (일반 메커니즘 확인) | `onInterceptTouchEvent` + `ACTION_CANCEL` 공식 문서 |
| 두 메커니즘 모두 "판정 전 지연 → 판정 후 진 쪽에 취소 이벤트"라는 동일한 설계 패턴을 쓴다 | [표준] (구조적 유사성, 두 공식 문서의 직접 귀결) | 위 두 인용의 비교 |

---

## 3~4. 세로 페이지 스크롤·핀치 확대와의 공존 — 새 실측 아님

사용자 지정대로 새로 조사하지 않고 기존 실측을 연결만 한다.

- 세로로 스크롤되는 페이지 안에 가로 캐러셀이 끼어 있을 때의 축 충돌은
  [C9 — Drag ↔ Swipe](/CONFLICTS.md#c9--drag--swipe)의 실측이 그대로
  적용된다.
- 캐러셀 카드 위에서 핀치 확대(예: 이미지 캐러셀에서 두 손가락으로
  확대)가 공존 가능한지는 [C13 — Scroll ↔ Pinch](/CONFLICTS.md#c13--scroll--pinch)의
  실측이 그대로 적용된다.

---

## CONFLICTS.md 연결

| 시나리오 | 연결 | 비고 |
|---|---|---|
| 세로 페이지 스크롤 안의 가로 캐러셀 축 충돌 | [C9 — Drag ↔ Swipe](/CONFLICTS.md#c9--drag--swipe) | 재실측 없음, 연결만 |
| 캐러셀 카드 위 핀치 확대 공존 | [C13 — Scroll ↔ Pinch](/CONFLICTS.md#c13--scroll--pinch) | 재실측 없음, 연결만 |
| 카드 안 탭 액션 vs 캐러셀 스와이프 시작 경계 | 새 영역 — C3(Tap↔Drag)와 유사한 성격이나 C3는 세로 리스트 재정렬 맥락에서 실측된 것이라 캐러셀의 가로축 문제에 그대로 대입할 근거는 약함 | 2번 항목에서 네이티브 플랫폼 메커니즘(iOS delaysContentTouches, Android ACTION_CANCEL)을 확인했으나, 이게 브라우저 `touch-action`/`pointercancel` 실측과 수치까지 일치하는지는 **🚧 미확정** |

---

## 다음 문서와의 접점

이 컴포넌트는 롱프레스를 트리거로 쓰지 않으므로 5/6번(multi-select,
context-menu)의 롱프레스 오염 문제와 겹치지 않는다.
reorderable-list.md/swipe-actions.md와도 식별 신호가 겹치지 않는다 —
가로 스크롤 + 균일 폭 카드라는 신호 자체가 이미 두 문서의 식별 신호
목록에서 "캐러셀일 가능성, 재정렬/스와이프 액션 아닐 수 있음"으로
상호 참조돼 있다.

---

## 출처 전체 목록

- [Apple Developer Documentation — `UICollectionLayoutSectionOrthogonalScrollingBehavior`](https://developer.apple.com/documentation/uikit/uicollectionlayoutsectionorthogonalscrollingbehavior) (및 `none`/`continuous`/`continuousGroupLeadingBoundary`/`paging`/`groupPaging` 개별 페이지, JSON API로 직접 재확인)
- [Apple Developer Documentation — `groupPagingCentered`](https://developer.apple.com/documentation/uikit/uicollectionlayoutsectionorthogonalscrollingbehavior/grouppagingcentered) (검색 결과로만 확인, 재조회 실패 — 🚧 부분 미확정)
- [Apple Developer Documentation — `UIScrollView.delaysContentTouches`](https://developer.apple.com/documentation/uikit/uiscrollview/delayscontenttouches)
- [Apple Developer Documentation — `UIScrollView.canCancelContentTouches`](https://developer.apple.com/documentation/uikit/uiscrollview/cancancelcontenttouches)
- [Apple Support — View photos and videos on iPhone](https://support.apple.com/guide/iphone/iph3d267610/ios)
- [Apple Support — Browse your photo collections on iPhone](https://support.apple.com/guide/iphone/iph4f36c4148/ios)
- [Material Components for Android (공식 GitHub) — Carousels](https://github.com/material-components/material-components-android/blob/master/docs/components/Carousel.md)
- [Android Developers — Manage touch events in a ViewGroup](https://developer.android.com/develop/ui/views/touch-and-input/gestures/viewgroup)
- [W3C — CSS Scroll Snap Module Level 1](https://www.w3.org/TR/css-scroll-snap-1/)
- 확인 시도했으나 못 찾거나 확인 못 한 것: 컬렉션 목록(썸네일 훑어보기)의
  스냅 여부, Uncontained 전략에서 스냅을 권장하지 않는 이유, Android
  캐러셀 코드 경로에서 `ViewConfiguration.getScaledTouchSlop()`이 실제로
  쓰이는지, Material 3 공식 캐러셀 디자인 블로그(`m3.material.io/blog/...`,
  JS 렌더링이라 텍스트 추출 불가) — 전부 **🚧 미확정**으로 본문에 개별
  표시했다.

**방법론 고지**: 이전 문서들과 동일하게, [관성]에 해당하는 확인은 전부
"공식 지원 문서 검색 확인"이며 실기기 직접 관찰이 아니다. 이번 문서는
특히 [표준] 비중이 높다 — 캐러셀은 다른 6개 컴포넌트보다 플랫폼
API/스펙 레벨 문서가 상세하게 갖춰진 영역이기 때문이다.
