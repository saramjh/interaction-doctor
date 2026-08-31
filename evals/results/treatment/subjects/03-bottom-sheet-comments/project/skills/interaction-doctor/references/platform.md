# platform.md

`research/ux-standards/patterns/` 8개 문서와
`research/ux-standards/nested-interactions/` 3개 문서에 등장한 모든
구체적 수치(ms, px, dp, % 등)를 모은다. 값은 각 문서에서 그대로
복사했다 — 다시 타이핑해서 옮기지 않았다. 같은 값이 여러 문서에서
재사용된 경우 한 행으로 합치고 출처를 전부 나열했다 — 독립적으로
여러 번 실측된 것처럼 중복 행을 만들지 않는다.

**제외한 것**: 버전 번호(iOS 15, iOS 13 등), 날짜, URL에 포함된
숫자, 그리고 실제 상수가 아니라 설명을 위한 예시 숫자(예:
`bottom-sheet.md`의 식별 신호 섹션에 있는 "화면의 30%/60%/100%"는
디텐트가 여러 단계일 수 있다는 걸 보여주는 예시일 뿐 인용된 스펙
수치가 아니다 — 표에 넣지 않았다). Playwright 테스트 스크립트가
임의로 고른 드래그 거리(200px, 300px 등 테스트 좌표)도 제외했다 —
그건 상수가 아니라 테스트 설계값이다. `multi-select.md`,
`tab-swipe.md`는 전수 확인했으나 해당 문서 범위에서 추출할 만한
구체적 수치 자체가 없었다 — 두 문서 다 이런 종류의 상수를 다루지
않는다는 뜻이지, 조사를 안 해서 빠진 게 아니다.

---

## 확인된 값

| 값 | 의미 | 플랫폼 | 라벨 | 출처 문서#섹션 |
|---|---|---|---|---|
| **494–513ms** | Android Chrome이 롱프레스 시 `contextmenu` 이벤트를 발생시키는 실측 타이밍(n=73) | Android | 이 프로젝트 자체 실기기 실측(CONFLICTS.md#C6 원 출처) | CONFLICTS.md#C6(원 출처); 인용: `context-menu.md` §3, `derivative-products-plan.md` §2.4 |
| **500ms** | 위 실측에 맞춰 이 프로젝트가 채택한 롱프레스/컨텍스트메뉴 타이머 값 | 없음 — 플랫폼 값 아니라 이 프로젝트가 실측에 맞춰 정한 값 | 이 프로젝트 자체 실측(C6) 재사용 — 4라벨 체계 밖 | `long-press-triple-conflict.md` §2-1(`CONTEXT_MENU_DELAY_MS`); `reorderable-list.md` §3-B 판정; `ux-standards-architecture.md` §3 예시 |
| **8px** | 이동 임계값 — 이 값을 넘으면 롱프레스 타이머 취소/드래그로 전환, 또는 스크롤 콘텐츠에서 시트 소유권으로 전환 | 없음 — Android 8dp를 재사용한 이 프로젝트의 값 | 이 프로젝트 자체 실측(C6) 재사용 — 4라벨 체계 밖 | `long-press-triple-conflict.md` §2-2(`MOVE_THRESHOLD_PX`); `bottom-sheet-scroll-drag.md` §2-2(`COLLAPSE_ACTIVATION_PX`); `ux-standards-architecture.md` §3 예시 |
| **8dp** (`TOUCH_SLOP`) | `ViewConfiguration.getScaledTouchSlop()` 공식 기본값 — 사용자가 스크롤을 시작한다고 판단하기 전까지 허용되는 이동 거리 | Android | [표준] | `carousel.md` §2(인용, 원 출처 `research/c10-sources.md`) |
| **.5f**(문서 표현대로, 곧 50%) | `ItemTouchHelper.getSwipeThreshold()` 기본값 — "to swipe a View, user must move the View at least half of RecyclerView's width or height" | Android | [표준] | `swipe-actions.md` §1 |
| **250**(ms) | `ItemTouchHelper.DEFAULT_SWIPE_ANIMATION_DURATION` — 스와이프 확정/취소 애니메이션 길이 | Android | [표준] | `swipe-actions.md` §5 |
| **280dp / 320dp** | Material 내비게이션 드로어 최대 폭(모바일/태블릿) — "The maximum width of the nav drawer is 280dp on mobile and 320dp on tablet" | Android/Material | [표준] | `side-drawer.md` §2 |
| **56dp / 64dp** | 위 폭 계산에 쓰이는 "standard increment"(모바일/태블릿) | Android/Material | [표준] | `side-drawer.md` §2 |
| **16dp** | Material 내비게이션 드로어 "Resting elevation" | Android/Material | [표준] | `side-drawer.md` §2 |
| **1000ms** | 컨텍스트 메뉴 → 다중 선택 확전 간격(500ms + 500ms) | 없음 — 플랫폼 값 아님 | **[이 프로젝트의 설계 판단]**, 🚧 실기기 미검증 | `long-press-triple-conflict.md` §2-1(`ESCALATE_DELAY_MS`); §5-2가 런타임에서 1003.1ms 발동을 확인했지만, 이건 "타이머가 그 값대로 도는가"의 검증이지 "그 값이 맞는가"의 검증이 아니다(§5-6) |

---

## 🚧 값 없음, 존재만 확인됨

**표에서 빠졌다고 조사 안 한 게 아니다** — 아래는 전부 "이 메커니즘이
존재한다"는 것까지는 공식 문서로 확인했지만, 정확한 수치는 그 문서
자체가 공개하지 않아서 못 찾은 것들이다.

- **iOS 홈 화면 아이콘의 확전(컨텍스트 메뉴 → 재배치 모드) 임계
  시간**: "touch and hold ... too long" 확전이 일어난다는 것 자체는
  Apple Support로 확인됐지만 정확한 ms 값은 공개돼 있지 않다. —
  `context-menu.md`
- **Android Pixel 런처의 이동 거리 분기 임계값**(바로가기 메뉴 vs
  이동): "lift your finger"로 갈린다는 것 자체는 확인됐지만 정확한
  px/dp는 공개돼 있지 않다. — `context-menu.md`
- **iOS 시스템 뒤로가기(`UIScreenEdgePanGestureRecognizer`)의 정확한
  엣지 인식 폭(pt)**: "near an edge"라고만 서술, 수치 없음. —
  `side-drawer.md`
- **Android 시스템 제스처 내비게이션의 정확한 엣지 인식 폭(dp)**:
  `DrawerLayout`이 "takes into account the size of any gesture
  navigation insets"라고만 서술, 수치 없음. — `side-drawer.md`
- **iOS 스와이프 액션의 정확한 커밋 거리(px/%)**:
  `performsFirstActionWithFullSwipe`는 "완전 스와이프냐 아니냐"라는
  불리언만 제공, 거리 수치 없음. — `swipe-actions.md`
- **iOS 스와이프가 속도만으로 완주 전에 조기 확정되는지**: 거리(완주)
  기준 스위치는 확인됐지만 속도(fling) 기반 조기 확정 여부/수치는
  확인 못함. — `swipe-actions.md`
- **Android `BottomSheetBehavior`의 `hideFriction`/
  `significantVelocityThreshold` 기본값**: 필드/메서드 존재는
  확인됐지만 기본 수치는 문서 본문에서 확인 못함. — `bottom-sheet.md`
- **Android `ViewConfiguration.getLongPressTimeout()`의 정확한
  기본값**: `isLongPressDragEnabled()` 기본값이 `true`(롱프레스
  기반)라는 것까지는 확인됐지만, 그 타이머의 정확한 ms 값은
  `TOUCH_SLOP`(8dp)과 별개 상수라 이 조사 범위에서 확인 안 됨. —
  `reorderable-list.md`
- **재정렬 핸들의 정확한 활성화 지연**: "핸들=지연 0ms"라는 가설은
  검증된 적이 없다 — 오히려 iOS Mail·Google Keep의 1st-party 앱
  도움말이 핸들이 있어도 "touch and hold"라는 표현을 써서 반증처럼
  보인다. — `reorderable-list.md`
- **캐러셀 코드 경로에서 8dp(터치 슬롭)가 실제로 쓰이는지**: 관여할
  개연성은 높다고 서술했지만 캐러셀 맥락에서 그 상수를 명시적으로
  언급하는 문서는 찾지 못했다. — `carousel.md`
