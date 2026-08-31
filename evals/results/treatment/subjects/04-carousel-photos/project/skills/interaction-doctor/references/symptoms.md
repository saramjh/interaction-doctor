# symptoms.md

CONFLICTS.md의 압축 규칙(원인 한 줄, 수정 한 줄, 나머지는 링크)을
그대로 쓴다. UX 표준 계층(`research/ux-standards/patterns/*.md`)에서
나온 항목은 여기에 두 가지를 추가한다: **확신도 라벨**(그 항목의
판단들 중 가장 약한 것을 대표값으로 — 낙관적으로 포장하지 않는다)과,
롱프레스 트리거를 공유할 수 있는 컴포넌트끼리의 **상호 참조**.

## 이 문서에 포함되지 않은 것 — 제외 기준

각 patterns 문서의 라벨 밀도를 실측했다(표준/관성/관행 개수 대비
🚧 개수):

| 문서 | 🚧 비율 |
|---|---|
| reorderable-list.md | 21.4% |
| swipe-actions.md | 32.0% |
| carousel.md | 34.6% |
| multi-select.md | 34.6% |
| tab-swipe.md | 35.7% |
| bottom-sheet.md | 37.9% |
| context-menu.md | 40.0% |
| **side-drawer.md** | **40.0%** |

**정직하게 밝힌다**: 기계적 카운트로는 어느 문서도 정확히 50%를
넘지 않았다. `side-drawer.md`를 제외한 기준은 숫자가 아니라 질적
판단이다 — 그 문서는 (a) iOS 쪽에 대응하는 HIG 전용 페이지 자체를
찾지 못했고, (b) 이 컴포넌트의 핵심 질문("`overscroll-behavior-x`가
실제로 iOS 시스템 제스처를 막는가")이 미확정일 뿐 아니라 **이
프로젝트의 도구(Playwright)로는 앞으로도 검증이 불가능하다는 것까지
실험으로 확인**됐다(`nested-interactions/side-drawer-back-gesture.md`
§5). 라벨 밀도가 아니라 "핵심 질문 자체가 영구 미확정"이라는 게
제외 사유다 — 아래 "🚧 조사 중" 목록으로 뺀다. 다른 7개는 라벨 밀도가
비슷하게 높아도(context-menu 40%까지) 핵심 메커니즘 자체는 [표준]으로
확인되어 있어 포함한다.

---

## "재정렬 리스트에서 항목을 얼마나 눌러야 드래그가 시작되는지 모르겠다"

**확신도** 🚧 미확정 (구조적 결론은 [표준], 정확한 활성화 지연은 미확정)

**원인** 핸들(별도 아이콘)이 있으면 탭↔드래그 충돌 자체가 구조적으로
사라진다 — Android `ItemTouchHelper.startDrag()`가 지연 없이 즉시
드래그를 시작하도록 공식 문서화되어 있다. 핸들이 없으면 행 전체가
탭/롱프레스/드래그를 공유하는 게 원인이고, Android 공식 기본값은
`isLongPressDragEnabled()=true`(롱프레스 기반).
**수정** 핸들이 있으면 별도의 작은 히트 타겟으로 분리하고 그 위에는
다른 탭 액션을 두지 않는다. 핸들이 없으면 500ms/8px(C6 재사용)
롱프레스로 재정렬 모드에 진입시킨다.
**주의** "핸들=즉시 드래그(지연 0ms)"라는 가정은 iOS Mail·Google
Keep의 1st-party 앱 도움말이 핸들이 있어도 "touch and hold"라는
표현을 쓴다는 점에서 반증처럼 보인다 — 정확한 지연 값은 네이티브 앱
계측이 필요하고 이 프로젝트 범위 밖이다.
**관련** [multi-select](#다중-선택-모드에-진입하려고-길게-눌렀는데-플랫폼마다-다르게-동작한다),
[context-menu](#길게-눌렀는데-컨텍스트-메뉴가-아니라-다른-게-뜬다),
[롱프레스 3중 충돌](#같은-리스트-항목에-재정렬다중선택컨텍스트메뉴가-전부-필요하면-뭐가-열려야-하는가) — 이 셋은 같은 롱프레스 트리거를 공유할 수 있다.
C2, C6, C10.
**상세** `research/ux-standards/patterns/reorderable-list.md`

---

## "다중 선택 모드에 진입하려고 길게 눌렀는데 플랫폼마다 다르게 동작한다"

**확신도** [관성] (1st-party 앱 공식 도움말 문서 기준, 기기 직접 관찰 아님)

**원인** iOS의 Photos·Files 앱은 다중 선택 진입에 롱프레스를 아예
쓰지 않는다 — 명시적 "Select" 버튼으로 진입한다. Android의 Google
Photos·Files by Google은 반대로 진입 자체가 touch-and-hold(롱프레스)다.
**수정** iOS 스타일(항상 보이는 "Select"/편집 버튼으로 진입)을 기본으로
채택하면 이 문서 자체가 불필요해진다 — 이게 가장 확실한 회피책이다.
롱프레스 진입을 그대로 쓴다면 드래그로 연쇄 선택("slide your finger
across")까지 같이 구현한다 — iOS(`slide your finger`)·Android
공식 API(`SelectionTracker`의 "gesture selection")가 대칭적으로 지원한다.
**관련** [reorderable-list](#재정렬-리스트에서-항목을-얼마나-눌러야-드래그가-시작되는지-모르겠다),
[context-menu](#길게-눌렀는데-컨텍스트-메뉴가-아니라-다른-게-뜬다),
[롱프레스 3중 충돌](#같은-리스트-항목에-재정렬다중선택컨텍스트메뉴가-전부-필요하면-뭐가-열려야-하는가). C2, C6.
**상세** `research/ux-standards/patterns/multi-select.md`

---

## "길게 눌렀는데 컨텍스트 메뉴가 아니라 다른 게 뜬다"

**확신도** [표준] (트리거 자체는 양쪽 플랫폼 공식 API 문서로 확인)

**원인** iOS `UIContextMenuInteraction`, Android
`registerForContextMenu`/`onCreateContextMenu` 둘 다 롱프레스를
공식 트리거로 문서화한다 — 트리거 자체는 확실하다. 문제는 같은
항목에 재정렬이나 다중 선택도 롱프레스로 열리게 만들면 셋이 경합한다는
것.
**수정** 하나의 요소에 컨텍스트 메뉴만 필요하면 C6의 500ms 타이머
(Android `contextmenu` 494–513ms 실측)를 그대로 쓰고 네이티브
`contextmenu`는 `preventDefault()`로 막는다. 셋 이상이 겹치면 아래
"롱프레스 3중 충돌" 레시피를 쓴다.
**관련** [reorderable-list](#재정렬-리스트에서-항목을-얼마나-눌러야-드래그가-시작되는지-모르겠다),
[multi-select](#다중-선택-모드에-진입하려고-길게-눌렀는데-플랫폼마다-다르게-동작한다),
[롱프레스 3중 충돌](#같은-리스트-항목에-재정렬다중선택컨텍스트메뉴가-전부-필요하면-뭐가-열려야-하는가). C6.
**상세** `research/ux-standards/patterns/context-menu.md`

---

## "같은 리스트 항목에 재정렬·다중선택·컨텍스트메뉴가 전부 필요하면 뭐가 열려야 하는가"

**확신도** 규칙의 축 선택은 [표준](상속), 정확한 수치(1000ms 확전
간격)와 3자 조합 자체는 **[이 프로젝트의 설계 판단]**, 실기기 미검증

**원인** 이 정확한 3자 조합을 실증하는 1st-party 앱 사례는 어느
플랫폼에도 없다. iOS는 애초에 다중 선택을 버튼으로 분리해서 이 충돌이
발생하지 않는다 — 이 충돌은 **Android 쪽에서 더 실재한다.**
**수정** `references/recipes.md`의 "롱프레스 3중 충돌" 레시피 —
1단계(8px 이동 여부)로 재정렬을 먼저 가르고, 2단계(500ms/1000ms 시간
확전)로 컨텍스트 메뉴/다중 선택을 가른다. **런타임 검증 통과 —
자세한 수치는 recipes.md 참조.**
**관련** [reorderable-list](#재정렬-리스트에서-항목을-얼마나-눌러야-드래그가-시작되는지-모르겠다),
[multi-select](#다중-선택-모드에-진입하려고-길게-눌렀는데-플랫폼마다-다르게-동작한다),
[context-menu](#길게-눌렀는데-컨텍스트-메뉴가-아니라-다른-게-뜬다). C2, C6.
**상세** `research/ux-standards/nested-interactions/long-press-triple-conflict.md`,
`references/recipes.md`

---

## "스와이프로 삭제/보관했는데 확정되는 기준이 플랫폼마다 다르다"

**확신도** [표준] (양쪽 플랫폼 공식 API 문서로 수치 확인)

**원인** iOS `UISwipeActionsConfiguration.performsFirstActionWithFullSwipe`
(기본값 `true`)는 끝까지 밀면 첫 액션을 즉시 실행한다. Android
`ItemTouchHelper.getSwipeThreshold()`(기본값 `.5f`)는 항목 크기의
50%를 넘겨야 확정된다 — 둘 다 정확한 수치가 공식 문서에 있다.
**수정** 웹 구현에서는 두 기준(완주 여부, 50% 거리)과 속도 기반
조기 확정(`getSwipeEscapeVelocity`)을 함께 쓴다 — 어느 하나도 못
넘기면 원위치로 스냅.
**관련** C9, C12(축 판정은 재사용, 재실측 없음).
**상세** `research/ux-standards/patterns/swipe-actions.md`

---

## "바텀시트 안에서 위로 스크롤했는데 리스트가 아니라 시트가 커진다/안 커진다"

**확신도** [표준] (iOS 공식 API로 확인 — 단, 이건 확장 방향만)

**원인** iOS `UISheetPresentationController.prefersScrollingExpandsWhenScrolledToEdge`
(기본값 `true`)가 "시트가 최대 디텐트가 아니면 위로 스크롤은 콘텐츠가
아니라 시트를 확장시킨다"를 공식 규정한다. Android `BottomSheetBehavior.
setDraggableOnNestedScroll()`은 이 문제를 다루는 전용 토글이
존재한다는 것만 확인되고 기본 동작은 미확정.
**수정** 시트가 최대 디텐트가 아니고 위로 스크롤 중이면 시트를
확장시키고, 최대 디텐트에 도달한 뒤에만 콘텐츠 스크롤을 허용한다.
**관련** [바텀시트 내부 스크롤 vs 닫기](#바텀시트-안-리스트를-아래로-당겼는데-리스트가-아니라-시트-전체가-닫힌다)(반대 방향, 별도 레시피).
**상세** `research/ux-standards/patterns/bottom-sheet.md`

---

## "바텀시트 안 리스트를 아래로 당겼는데 리스트가 아니라 시트 전체가 닫힌다"

**확신도** **[이 프로젝트의 설계 판단]**(대칭 가정) — 코드로서는
런타임 검증 통과, iOS/Android 공식 문서로 이 방향 자체가 확인된 건
아님

**원인** iOS 공식 문서는 위로 스크롤(확장) 방향만 다룬다 — 콘텐츠가
맨 위(`scrollTop===0`)에서 계속 아래로 당길 때 시트가 축소/닫혀야
하는지는 어느 플랫폼 공식 문서에도 없다.
**수정** `references/recipes.md`의 "바텀시트 내부 스크롤" 레시피 —
`scrollTop>0`이면 무조건 콘텐츠 스크롤 우선, `scrollTop===0`이고
아래로 8px 넘게 이동하면 그때부터 시트 소유권으로 전환. **이 정확한
경계 조건 로직이 실제 브라우저에서 그대로 동작하는지는 Playwright로
검증됨** — 다만 이게 iOS/Android 네이티브 동작과 일치한다는 보장은
아니다.
**관련** [바텀시트 확장 방향](#바텀시트-안에서-위로-스크롤했는데-리스트가-아니라-시트가-커진다안-커진다)(반대 방향).
**상세** `research/ux-standards/nested-interactions/bottom-sheet-scroll-drag.md`,
`references/recipes.md`

---

## "캐러셀이 스냅되어야 하는지 자유 스크롤이어야 하는지 모르겠다"

**확신도** [표준] (iOS API, Android 공식 문서, W3C 스펙 세 출처 일치)

**원인** 정답이 하나가 아니다 — iOS `UICollectionLayoutSectionOrthogonalScrollingBehavior`
(6단계), Android Material `CarouselSnapHelper`(전략별 권장), W3C
`scroll-snap-type`(none/proximity/mandatory) 세 플랫폼 모두 스펙트럼을
제공하고 콘텐츠 유형별 선택을 전제한다.
**수정** "한 번에 하나씩 온전히 감상"류(사진 전체화면)는
`scroll-snap-type: mandatory` + `scroll-snap-stop: always`. "여러 개
훑어보기"류는 `proximity`나 `none`. Android 기본 권장은 스냅
(멀티브라우즈+`CarouselSnapHelper`).
**관련** C9(세로 페이지 안 가로 캐러셀), C13(핀치 확대 공존) — 재실측
없음, 연결만.
**상세** `research/ux-standards/patterns/carousel.md`

---

## "탭 전환에 좌우 스와이프를 기대했는데 안 되거나(또는 의도치 않게 된다)"

**확신도** [표준] (양쪽 플랫폼 공식 API 문서/가이드로 확인, 정반대
결과)

**원인** iOS `UITabBarController` 공식 클래스 레퍼런스는 탭 전환을
"User taps"로만 서술한다 — 스와이프 관련 언급은 문서 전체에 tvOS
포커스 이동 1곳뿐이고 "In iOS, the tab bar always remains in
focus"라고 명시한다. Android는 정반대로 `ViewPager2`+`TabLayout`
스와이프 전환이 공식 가이드 제목에 그대로 등장하는 1급 권장 패턴이다.
**수정** iOS 스타일 하단 탭 바를 구현한다면 스와이프 전환을 넣지
않는 게 플랫폼 표준과 일치한다. Android 스타일(또는 웹 전용 탭
스트립)이라면 `ViewPager2`+`TabLayoutMediator`에 대응하는 스와이프
전환을 구현한다.
**관련** C9(탭 콘텐츠 내부 세로 스크롤과의 축 충돌) — 재실측 없음.
**상세** `research/ux-standards/patterns/tab-swipe.md`

---

## 🚧 조사 중 — 아직 확신 있게 답할 수 없음

이 컴포넌트는 위 "제외 기준"에 따라 본표에서 뺐다. 질문이 들어오면
"조사는 했지만 핵심 질문 자체가 아직 확신 있게 답할 수 없다"고
먼저 말한다 — 표준화된 것처럼 포장하지 않는다.

### 사이드 드로어(에지 스와이프로 열리는)

- iOS HIG에 전용 가이드 페이지를 찾지 못했다.
- 왼쪽 엣지는 iOS 시스템 뒤로가기(`interactivePopGestureRecognizer`)가
  이미 공식 선점하고 있다.
- `overscroll-behavior-x: contain`이 실제로 iOS 시스템 제스처를
  억제하는지는 미확정이며, **이 프로젝트의 도구(Playwright)로는
  검증 자체가 불가능하다는 것까지 실험으로 확인**됐다(CDP 터치 주입,
  트랙패드 휠 시뮬레이션 둘 다 시도, 둘 다 시스템 내비게이션을
  발생시키지 못함).
- 확인 가능했던 건 완화 조치(오른쪽 배치, 버튼 병행)가 "선언한 대로
  동작한다"는 것뿐이다 — 충돌이 해소된다는 뜻은 아니다.
- **상세**: `research/ux-standards/patterns/side-drawer.md`,
  `research/ux-standards/nested-interactions/side-drawer-back-gesture.md`
