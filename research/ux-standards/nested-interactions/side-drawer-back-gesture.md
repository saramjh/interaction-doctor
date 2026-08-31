# Side Drawer vs Browser Chrome — Edge Swipe Physical Collision

오염 방지 유형 **C**: 웹페이지 안의 사이드 드로어(에지 스와이프로 열림)와
모바일 브라우저 자체의 뒤로가기 제스처(에지 스와이프)가 **같은 물리적
화면 영역**을 두고 경합하는 문제. 유형 A/B와 근본적으로 다른 점이
있다는 걸 먼저 밝힌다 — 아래 0번 참조.

`patterns/side-drawer.md` §3이 이 문제를 발견만 해 두고 **답하지
않은 채로 넘겼다** — "구체적으로 남는 질문들... 전부 미확정, 이
문서에서 답하지 않음"이라고 명시돼 있었다. 유형 A/B와 달리 이
문서에서는 **그 남겨진 질문에 대해 실제로 새로 조사한다** — patterns
문서들이 이미 답을 갖고 있지 않았기 때문이다.

---

## 0. 이 문제가 유형 A/B와 근본적으로 다른 이유

유형 A(롱프레스 3자 충돌)와 유형 B(바텀시트 내부 스크롤)는 둘 다
**같은 웹페이지 DOM 안에서 서로 다른 제스처 인식기끼리 경합**하는
문제였다 — `pointerdown`/`pointermove`/`pointerup`이 페이지에 도달하고,
JS가 그 이벤트들을 보고 어느 인식기가 이길지 판정할 수 있었다.

이 문제는 다르다. 모바일 브라우저의 엣지 스와이프 뒤로가기는 **브라우저
크롬(chrome) 레벨의 제스처**일 수 있다 — 페이지의 JavaScript에
`pointerdown` 이벤트가 도달하기도 전에, 혹은 도달하더라도 브라우저가
그 스트림을 가로채 페이지 내비게이션으로 소비해버릴 수 있다. 이건
`research/ux-standards/patterns/ux-standards-architecture.md` §3의 activation_distance/activation_delay/
relations 모델이 애초에 가정하는 상황(동일 레이어의 두 인식기가
경합)과 다르다 — **이 모델을 그대로 적용할 수 없을 가능성이 있다는
걸 미리 밝혀 둔다.** 아래 2번에서 이 모델이 어디까지 적용되고 어디서부터
적용되지 않는지를 명시한다.

---

## 1. 새로 조사한 것 — 1차 출처만

### 1-1. 이 시스템 제스처를 웹에서 억제하는 공식 메커니즘이 존재한다

> `overscroll-behavior` — "The `contain` value disables native browser
> navigation, including the vertical pull-to-refresh gesture and
> **horizontal swipe navigation**."
> — [MDN, `overscroll-behavior`](https://developer.mozilla.org/en-US/docs/Web/CSS/overscroll-behavior)

**[표준] (원문 직접 확인).** MDN이 공식적으로 "수평 스와이프 내비게이션"
(정확히 사이드 드로어와 경합하는 그 제스처)을 이 속성이 억제 대상으로
삼는다고 명시한다.

W3C/CSSWG 초안 스펙(Working Draft, 아직 REC 아님)은 더 구체적인
예시와 형식적 정의를 준다:

> "A page wants to implement their own pull-to-refresh effect and thus
> needs to disable browser native overscroll action. `/* only disable
> pull-to-refresh but allow **swipe navigations** */
> overscroll-behavior-y: contain;` In this case, the author can use
> `contain` on the viewport defining element to prevent overscroll from
> triggering navigation actions."
> "A **non-local boundary default action** interacts with the page, for
> example scroll chaining or **a navigation action**."
> — [CSSWG Drafts, CSS Overscroll Behavior Module](https://drafts.csswg.org/css-overscroll-behavior/) (Editor's Draft — 아직 W3C REC이 아님, `research/c10-sources.md`가 이미 확인한 Pointer Events처럼 완성된 표준이 아니라는 점을 명시)

**[표준] (원문 직접 확인, 단 스펙 성숙도는 Editor's Draft로 낮음 —
`www.w3.org/TR/`에 게시된 버전은 찾지 못했다, 이 자체를 🚧 미확정으로
표시).** 스펙이 "swipe navigations"를 `overscroll-behavior-x`(가로축)로,
"pull-to-refresh"를 `overscroll-behavior-y`(세로축)로 예시에서 명확히
분리한다 — 사이드 드로어가 경합하는 게 정확히 x축 스와이프
내비게이션이므로, `overscroll-behavior-x: contain`(또는 `none`)이
관련 선언이라는 것까지는 문서로 확인된다.

### 1-2. 확인하지 못한 것 — 정직하게 남긴다

**이 CSS 메커니즘이 iOS Safari의 "화면 물리적 가장자리에서 시작하는"
엣지 스와이프 뒤로가기와 정확히 같은 것을 가리키는지는 확인하지
못했다.** `overscroll-behavior`는 스펙상 "스크롤 컨테이너가 경계에
도달했을 때"(overscroll) 발동하는 속성이다 — 반면 iOS의 시스템 뒤로가기
스와이프는 (네이티브 앱의 `UIScreenEdgePanGestureRecognizer`가 그렇듯,
`patterns/side-drawer.md`에서 이미 확인함) 스크롤 경계와 무관하게 **화면
가장자리 자체에서 시작하는 것만으로 인식**될 수 있다 — 즉 스크롤이 아예
없는 페이지에서도 발동할 수 있는 별개의 메커니즘일 가능성이 있다.

- 이 둘이 브라우저 내부에서 같은 구현인지 별개인지는 **🚧 미확정** —
  블로그·이슈 트래커(bugzilla.webkit.org 등) 수준의 논의는 검색으로
  다수 발견했으나, 이 프로젝트의 출처 규칙(1차 공식 문서만)에 맞는
  근거로 확인하지 못했다. 추측으로 채우지 않는다.
- 정확한 엣지 인식 폭(px)이 플랫폼/브라우저별로 얼마인지도 **🚧
  미확정** — 공식 문서에서 수치를 찾지 못했다.
- "왼쪽을 피해 오른쪽에서 여는" 회피책이 실제로 널리 쓰이는 관행인지도
  **🚧 미확정** — 이걸 확인하려면 다수 실제 웹사이트를 관찰하는 조사가
  필요한데, 이번 세션에서는 공식 문서 검색만 수행했으므로 하지 않았다.

---

## 2. 이 프로젝트가 채택하는 접근 — §3 모델이 적용되는 범위와 안 되는 범위

### 2-1. §3 모델이 적용되지 않는 부분

`activation_distance`/`activation_delay`/`relations`(requireFailureOf/
blockedBy/simultaneousWith) 모델은 **"페이지가 이벤트를 실제로 받는다"는
전제** 위에 서 있다. 만약 브라우저가 엣지 영역의 터치를 애초에 페이지에
전달하지 않고 자체 소비한다면, 페이지 쪽에 어떤 인식기를 선언하든
무관하다 — **선언 자체가 무의미해지는 시나리오가 있다는 걸 인정한다.**
이건 이 프로젝트가 만들 수 있는 규칙의 한계이지, 빠뜨린 설계가 아니다.

### 2-2. §3 모델이 적용되는 부분 — 페이지가 이벤트를 받는 경우에 한해

`overscroll-behavior-x`로 시스템 제스처를 억제하는 데 성공했다고
가정하면(그 성공 여부 자체가 위 1-2의 미확정 사항이다), 그 이후
페이지 내부에서 드로어 열기 제스처와 다른 가로 스크롤(예: 그 화면에
같이 있는 캐러셀)이 경합하는 문제는 **새로운 문제가 아니라 이미 이
프로젝트가 가진 도구로 풀리는 문제다**:

- [C9 — Drag ↔ Swipe](/CONFLICTS.md#c9--drag--swipe)의 축 판정 실측이
  그대로 적용된다.
- `carousel.md`가 이미 확인한 iOS `UIScrollView.delaysContentTouches`/
  `canCancelContentTouches` 패턴, 또는 Android의 `ViewGroup`
  `onInterceptTouchEvent`/`ACTION_CANCEL` 패턴과 구조적으로 같은
  "판정 지연 후 진 쪽 취소" 방식을 웹의 `pointercancel`로 구현하면 된다.

**즉 이 문서가 새로 설계해야 할 건 "페이지 안의 경합"이 아니라 "페이지
대 브라우저 크롬의 경합"이고, 후자는 §3 모델로 설계할 수 있는 대상이
아니다** — 웹 표준(CSS 선언)으로 브라우저에 요청하는 것 이상을 페이지
쪽에서 강제할 수단이 없다.

### 2-3. 이 프로젝트가 실제로 제시하는 것 — 선언 + 회피 설계, "해소 규칙"이 아니라 "완화 조치"

유형 A/B처럼 "누가 이기는가"를 판정하는 규칙표를 만들 수 없으므로,
대신 **완화 조치(mitigation)** 목록으로 제시한다. 이건 §3의
recognizer 경합 모델이 아니라 **[이 프로젝트의 설계 판단]**이다 —
공식 문서 어디에도 "사이드 드로어는 이렇게 만들어라"라는 권고는 없다.

```
mitigations:

  1. suppress_system_gesture:
       declaration: "overscroll-behavior-x: contain;"  # 또는 none
       target: "html 또는 뷰포트 정의 요소"
       status: "[표준] 메커니즘 존재 확인됨 (MDN, CSSWG)"
       caveat: "iOS Safari의 화면-가장자리 시작형 뒤로가기 스와이프까지
                억제하는지는 🚧 미확정 — 이 선언만으로 문제가 완전히
                해결된다고 가정하지 않는다."

  2. avoid_left_edge:
       description: "왼쪽 가장자리 대신 오른쪽 가장자리에서 여는
                     드로어를 우선 고려한다."
       status: "[이 프로젝트의 설계 판단] — iOS 뒤로가기 스와이프가
                왼쪽 가장자리에 공식 할당되어 있다는 사실(side-drawer.md,
                interactivePopGestureRecognizer 원문 확인)에서 도출한
                회피책일 뿐, '오른쪽 드로어가 표준'이라는 근거는 아니다.
                오른쪽에서 여는 것도 나름의 트레이드오프(오른손잡이
                한손 사용성 등)가 있으며 이건 이 문서의 조사 범위가
                아니다."

  3. explicit_button_fallback:
       description: "에지 스와이프만이 아니라 항상 탭 가능한 hamburger
                     버튼을 같이 제공해, 스와이프가 시스템에 뺏겨도
                     드로어를 열 수 있는 경로를 남긴다."
       status: "[이 프로젝트의 설계 판단] — 다만 이건 reorderable-list.md/
                multi-select.md에서 이미 확인한 iOS 1st-party 앱들의
                일반적 태도(제스처만 믿지 않고 명시적 버튼을 항상 병행)
                와 일관된다는 정황은 있다. 정황일 뿐 직접 근거는 아니다."
```

---

## 3. 라벨 요약

| 요소 | 라벨 | 근거/사유 |
|---|---|---|
| `overscroll-behavior-x`가 "스와이프 내비게이션"을 공식적으로 대상으로 한다 | [표준] | MDN + CSSWG Editor's Draft 원문 직접 확인 |
| 이 스펙이 아직 W3C REC이 아니라 Editor's Draft라는 점 | [표준]이되 성숙도 낮음 — 별도 명시 | `www.w3.org/TR/`에서 REC 버전을 찾지 못함 |
| 이 CSS 메커니즘이 iOS Safari의 엣지 시작형 뒤로가기까지 억제하는지 | **🚧 미확정** | 공식 문서로 확인 못함, 블로그/이슈트래커만 존재 |
| 정확한 엣지 인식 폭(px) | **🚧 미확정** | 공식 문서에 수치 없음 |
| "오른쪽에서 열기" 회피책 | **[이 프로젝트의 설계 판단]** | side-drawer.md의 확인 사실(왼쪽=시스템 뒤로가기 선점)에서 도출한 추론, 업계 관행 확인은 안 됨 |
| "버튼을 항상 병행 제공하라"는 권고 | **[이 프로젝트의 설계 판단]**, 약한 정황 있음 | reorderable-list.md/multi-select.md의 iOS 관찰과 방향은 일치하나 직접 근거 아님 |
| §3 모델(activation_distance 등)이 이 문제 전체에 적용 가능한가 | **적용 불가 — 구조적 한계로 명시** | 0번 참조. 새 필드 확장으로도 해결 안 되는 범주(유형 A/B와 질적으로 다름) |

---

## 4. 코드/선언 예시 — 자체 점검일 뿐, 런타임 검증 아님

```css
/* interaction-doctor 예시 — side drawer, 시스템 제스처 완화 시도
   상태: 자체 점검만 완료. §5.5 기준 런타임 검증 아님.
   이 선언이 iOS Safari의 엣지 스와이프 뒤로가기를 실제로
   억제하는지는 실기기로 확인된 바 없다. */

html {
	overscroll-behavior-x: contain; /* MDN/CSSWG 확인된 선언 — 효과 범위는 미확정 */
}

.drawer-trigger-zone {
	/* 왼쪽 대신 오른쪽에서 여는 설계 — [이 프로젝트의 설계 판단] */
	right: 0;
	left: auto;
}
```

```html
<!-- 완화 조치 3: 스와이프가 시스템에 뺏기더라도 항상 열 수 있는 경로 -->
<button type="button" aria-label="메뉴 열기" onclick="openDrawer()">☰</button>
```

**이 예시에 대한 정직한 한계 표시**:

- `overscroll-behavior-x: contain`을 선언한 코드가 실제로 iOS
  Safari에서 시스템 뒤로가기 스와이프를 막는지, 아니면 아무 효과가
  없는지 **이 세션은 확인하지 않았다.** 효과가 있다는 것도, 없다는
  것도 주장하지 않는다.
- 오른쪽 배치와 버튼 병행은 코드로 표현 가능하지만, 이게 "충돌을
  해소한다"고 말할 수 없다 — 회피와 대체 경로 제공일 뿐, 유형 A/B처럼
  "어느 인식기가 이기는가"를 판정하는 규칙이 아니다.
- **이건 §5.5 기준 자체 점검조차 완전하지 않다** — 유형 A/B의 코드는
  최소한 "선언과 로직이 논리적으로 맞는가"를 검토할 수 있었지만, 이
  문서의 핵심 질문(브라우저가 이벤트를 페이지에 주는가 마는가)은 코드
  검토만으로는 답이 안 나온다. **실기기에서 실제로 iOS Safari/Android
  Chrome을 열어 확인하는 것 외에 다른 확인 방법이 없다** — 이건 유형
  A/B보다도 더 강하게 런타임 검증이 필요한 항목이다.

---

## 5. 런타임 검증 결과 — 가능한 것과 불가능한 것을 먼저 가른다

`bottom-sheet-scroll-drag.md`, `long-press-triple-conflict.md`와 같은
"§5.5 기준 검증됨으로 승격" 작업이지만, **이 문서는 그 절차를 그대로
적용하기 전에 먼저 "검증이 가능한 질문인가"부터 판정해야 한다** — §0
에서 이미 이 문제가 유형 A/B와 근본적으로 다르다고 밝혀 뒀기 때문이다.
아래는 그 판정을 실제 실험으로 먼저 마친 결과다.

### 5-1. 실험 1 — Playwright가 실제 엣지 스와이프 뒤로가기를 발생시킬 수 있는가

**방법**: 두 개의 정적 페이지(`page1.html` → `page2.html`)로 이동해
브라우저 히스토리를 만든 뒤, iPhone 13 디바이스 프리셋
(`devices["iPhone 13"]`, `hasTouch:true`, `isMobile:true`)으로 연
컨텍스트에서, CDP `Input.dispatchTouchEvent`로 화면 왼쪽 가장자리
(x=1)에서 시작해 오른쪽으로 진행하는 완전한 터치 스트림
(`touchStart`→`touchMove`×27→`touchEnd`)을 주입했다. headless/headed
양쪽 모두, `overscroll-behavior-x: contain` 있는 페이지와 없는
페이지 양쪽 모두 시도했다. 스크립트:
`research/ux-standards/nested-interactions/verification/side-drawer-edge-swipe-probe.js`.

**결과**:

| 조건 | `page.url()`이 실제로 뒤로 이동했는가 |
|---|---|
| headless, `overscroll-behavior-x` 없음 | **아니오** |
| headless, `overscroll-behavior-x: contain` | **아니오** |
| headed, `overscroll-behavior-x` 없음 | **아니오** |
| headed, `overscroll-behavior-x: contain` | **아니오** |

**주입 자체는 정상 작동했다는 것도 별도로 확인함**: 페이지에
`touchstart`/`touchmove`/`touchend` 리스너를 달아 보니, x=1에서
시작해 x≈217까지 진행하는 좌표가 정확히 전부 페이지에 도달했다(예:
`touchstart x=0.9999... y=400`, 이어서 `touchmove x=41...x=217`).
**즉 이건 "주입이 안 먹혔다"가 아니라 "주입은 완벽히 됐는데 그 위의
시스템 제스처가 아예 반응하지 않는다"는 뜻이다.**

**실험 2(보조) — 데스크톱 트랙패드 스타일 스와이프도 시도**: 모바일
에뮬레이션 없이 `page.mouse.wheel(-120, 0)`을 40회 반복해 데스크톱
Chrome의 "두 손가락 스와이프로 뒤로가기" 경로도 시도했다. 결과는
동일 — `overscroll-behavior-x: contain` 유무와 무관하게 내비게이션
없음. 스크립트:
`research/ux-standards/nested-interactions/verification/side-drawer-wheel-swipe-probe.js`.

### 5-2. 판정 — 검증 불가능함을 확인함 (실패가 아니라 도구의 한계)

**작업 지시 3번대로 명확히 기록한다: Playwright로는 이 시스템
제스처를 검증할 수 없다는 것을 실제 실험으로 확인했다.**

이유(추정이 아니라 위 실험이 뒷받침하는 설명): Playwright가 자동화
하는 건 브라우저 **엔진** 프로세스(Chromium/WebKit)이지, iOS의
Mobile Safari 앱이나 그에 준하는 네이티브 브라우저 셸이 아니다.
"화면 가장자리에서 스와이프하면 뒤로가기"라는 동작은 §1에서 이미
확인했듯 그 네이티브 셸 레벨(`UIScreenEdgePanGestureRecognizer`,
Android의 시스템 제스처 내비게이션)에 구현되는 게 정상적인
아키텍처다 — Chromium 자체의 브라우저 프로세스에도 그런 기능이
있는지 데스크톱 트랙패드 경로로 따로 시도했지만, 그 경로로도
재현되지 않았다. 두 실험 다 음성 결과라는 것 자체가 유용한 정보다:
적어도 Playwright가 자동화하는 이 두 경로(모바일 터치 에뮬레이션,
데스크톱 휠 스와이프)로는 이 기능 자체가 트리거되지 않는다.

**이걸 이 문서의 §1-2 미확정 항목과 혼동하지 않는다**: §1-2는
"`overscroll-behavior-x`가 iOS Safari의 엣지 스와이프까지 억제하는지
모른다"는 것이었다 — 이건 **비교할 두 상태(억제됨/안 됨) 중 어느
쪽인지 몰랐다**는 뜻이다. 이번 실험은 그보다 한 단계 앞선 것을
확인했다: **Playwright로는 애초에 비교 자체를 할 수 없다**(기준선이
되는 "억제 안 된 상태의 내비게이션"조차 발생시키지 못했으므로).
따라서 §1-2는 여전히 미확정이고, 이번 실험은 그 미확정을 해소하지
못한다 — 대신 "이 도구로는 절대 해소할 수 없다"는 사실을 추가했다.

**이 발견은 `research/ux-standards/patterns/ux-standards-architecture.md` §6(명시적 한계)에도
새 항목으로 추가했다** — 이건 이 문서 하나의 한계가 아니라, 이
프로젝트가 Playwright를 쓰는 모든 곳에 적용되는 일반적 한계이기
때문이다.

### 5-3. 미티게이션 2 — 오른쪽 배치 (페이지 내부 동작, 검증 가능함)

작업 지시 4번대로, 순수 페이지 내부 동작이라 정상적으로 검증했다.
재현 페이지: `tools/nested/side-drawer-mitigations-verify.html`.

| 항목 | 값 |
|---|---|
| 뷰포트 폭 | 390px (iPhone 13) |
| `.drawer-trigger-zone`의 실제 위치 | `x=370, width=20` |
| 왼쪽 가장자리(x=0)에 닿아 있는가 | **아니오** |
| 오른쪽 가장자리에 닿아 있는가 | **예**(`x+width === viewportWidth`) |
| 닫힌 상태의 `#drawer` 위치 | `x=390`(뷰포트 폭과 동일 — 화면 밖 오른쪽에 완전히 대기) |

**검증됨**: `.drawer-trigger-zone`과 `#drawer` 모두 iOS가
`interactivePopGestureRecognizer`에 공식 할당한 왼쪽 가장자리
영역과 기하학적으로 전혀 겹치지 않는다. 이건 §3-2에서 미리 밝힌 대로
"오른쪽 드로어가 표준"이라는 근거가 아니라, **선언한 대로 배치가
실제로 그렇게 된다는 것**만 검증한 것이다.

### 5-4. 미티게이션 3 — 버튼 병행 (페이지 내부 동작, 검증 가능함)

| 항목 | 클릭 전 | 클릭 후 |
|---|---|---|
| `#drawer`의 `open` 클래스 | 없음 | **있음** |
| `#drawer`의 `aria-hidden` | `"true"` | **`"false"`** |
| `#drawer`의 `x` 좌표 | 390(화면 밖) | **150**(390−240, 완전히 화면 안) |

스크린샷: `research/ux-standards/nested-interactions/verification/side-drawer-before-button-click.png`,
`side-drawer-after-button-click.png`.

**검증됨**: `#hamburger` 버튼 클릭 **하나만으로**(스와이프·드래그
시뮬레이션 전혀 없이) 드로어가 완전히 열린다. 이건 "스와이프가
시스템에 뺏겨도 열 수 있는 경로가 실제로 작동한다"는 것을 확인한
것이다 — 5-1/5-2가 확인 못 한 스와이프 쪽 질문과는 독립적으로, 이
경로 자체는 항상 유효하다.

### 5-5. 종합 — 무엇이 검증됐고 무엇이 여전히 미확정인가

| 항목 | 상태 |
|---|---|
| `overscroll-behavior-x`가 iOS Safari 엣지 스와이프를 억제하는지 | 🚧 미확정(불변) — **그리고 이제 Playwright로는 확인 불가능함까지 확인됨** |
| 정확한 엣지 인식 폭(px) | 🚧 미확정(불변) |
| 오른쪽 배치가 기하학적으로 왼쪽 시스템 영역을 피하는가 | **검증됨**(5-3) |
| 버튼 병행 경로가 항상 작동하는가 | **검증됨**(5-4) |
| §3의 "완화 조치이지 해소 규칙이 아니다"라는 원래 판정 | 바뀌지 않음 — 완화 조치 두 개가 "제대로 선언한 대로 동작한다"는 것만 검증됐지, "충돌이 해소된다"는 게 검증된 게 아니다 |

---

## 오염 방지 3유형 종합 — 이번 작업에서 드러난 것

세 유형을 순서대로 진행하면서 드러난 공통점 하나를 기록해 둔다(이것도
결론이 아니라 관찰이다): 유형 A와 B는 §3 모델(시간/거리 기반 판정)을
확장(각각 `escalatesFrom`, `activation_condition`)해서 표현할 수
있었지만, 유형 C는 확장으로도 안 되는 **구조적으로 다른 층위**의
문제였다. 오염 방지 작업이 "매트릭스에 축 하나만 더 그리면 끝나는
일"이 아니라는 걸 세 유형을 실제로 다 해보고 나서야 확인했다 — 이건
`research/ux-standards/patterns/ux-standards-architecture.md` §6이 이미 "커버리지는 유한하다"고 밝혀둔
것과 같은 방향의 재확인이다.

## 다음 단계

- 유형 A/B/C 세 문서 모두 완료. 런타임 검증도 세 문서 모두 §5에서
  완료됨(이 문서는 "검증 가능한 두 미티게이션은 검증, 검증 불가능한
  시스템 제스처는 불가능하다는 것 자체를 확인"으로 끝맺음).
- §5-2에서 확인한 Playwright의 구조적 한계(네이티브 브라우저 셸
  제스처 자동화 불가)는 `research/ux-standards/patterns/ux-standards-architecture.md` §6에 일반
  한계로 등재됨 — 이 프로젝트가 Playwright를 쓰는 다른 모든 검증에도
  적용된다.
- `overscroll-behavior-x`가 iOS Safari 엣지 스와이프를 실제로
  억제하는지는 여전히 미확정이며, **이 프로젝트의 도구로는 앞으로도
  해소할 수 없다** — 답이 필요하다면 실기기 필드 테스트 외에 방법이
  없다.
