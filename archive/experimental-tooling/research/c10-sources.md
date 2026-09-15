# research/c10-sources.md — C10 (Drag ↔ Scroll) Primary Sources

Scope: primary sources only (W3C, WHATWG, MDN, Chrome/Apple/Android official docs).
No conclusions, no recommendations — source excerpts only. Findings not located are marked "미발견".

---

## 1. CSS `touch-action` — W3C Pointer Events spec

### touch-action: auto
URL: https://www.w3.org/TR/pointerevents3/ (Pointer Events Level 3, W3C Recommendation — "The touch-action CSS property" section; editor's draft mirror: https://w3c.github.io/pointerevents/#the-touch-action-css-property)
원문 요약: `auto` 값은 해당 요소에서 시작되는 다이렉트 조작(direct manipulation) 중 패닝·줌과 관련해 허용되는 모든 동작을 브라우저가 고려할 수 있게 한다.
직접 관련된 원문 구절: "The user agent MAY consider any permitted direct manipulation behaviors related to panning and zooming of the viewport that begin on the element."

### touch-action: none
URL: https://www.w3.org/TR/pointerevents3/ (같은 섹션)
원문 요약: `none` 값은 해당 요소에서 시작되는 다이렉트 조작 상호작용이 뷰포트 패닝·줌과 관련된 어떤 동작도 트리거해서는 안 된다고 규정한다.
직접 관련된 원문 구절: "Direct manipulation interactions that begin on the element MUST NOT trigger behaviors related to viewport panning and zooming."

### touch-action: pan-x / pan-y
URL: https://www.w3.org/TR/pointerevents3/ (같은 섹션)
원문 요약: 스펙은 `pan-x`와 `pan-y`(및 `pan-left`/`pan-right`/`pan-up`/`pan-down`)를 하나의 정의 문장으로 함께 규정한다 — 나열된 값들이 지정하는 방향으로 시작하는 패닝만 브라우저가 처리하도록 허용한다는 내용이며, 값 자체에 축이 하나로 제한되면(pan-x 또는 pan-y 단독) 패닝이 시작된 후에는 그 축을 바꿀 수 없다고 명시한다.
직접 관련된 원문 구절: "The user agent MAY consider direct manipulation interactions that begin on the element only for the purposes of panning that starts in any of the directions specified by all of the listed values. Once panning has started, the direction may be reversed by the user even if panning that starts in the reversed direction is disallowed. In contrast, when panning is restricted to a single axis (for instance, with pan-x or pan-y), the axis cannot be changed during panning."
추가 원문(예시, 같은 섹션): "For example, an image carousel may use pan-y to ensure it receives pointer events for any horizontal pan operations without interfering with vertical panning of the document."
비고: 스펙은 pan-x와 pan-y를 별개의 문장으로 정의하지 않고 공유 정의를 쓴다. pan-x/pan-y 각각을 독립적으로 정의한 별도 문장은 W3C 스펙에서 미발견 — 대신 아래 MDN 항목에서 개별 문장을 확인함.

### touch-action: pan-x / pan-y — 개별 정의 (MDN)
URL: https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action
원문 요약: MDN은 W3C 스펙과 달리 pan-x와 pan-y를 각각 별도 문장으로 설명한다.
직접 관련된 원문 구절:
- pan-x: "Enable single-finger horizontal panning gestures. May be combined with pan-y, pan-up, pan-down and/or pinch-zoom."
- pan-y: "Enable single-finger vertical panning gestures. May be combined with pan-x, pan-left, pan-right and/or pinch-zoom."

### touch-action: manipulation
URL: https://www.w3.org/TR/pointerevents3/ ("The touch-action CSS property" section)
원문 요약: `manipulation`은 패닝과 연속 줌(핀치 줌 등)만 허용하고, 더블탭 줌처럼 일정 시간 내 여러 활성화가 필요한 다른 관련 동작은 트리거하지 않도록 규정한다.
직접 관련된 원문 구절: "The user agent MAY consider direct manipulation interactions that begin on the element only for the purposes of panning and continuous zooming (such as pinch-zoom), but MUST NOT trigger other related behaviors that rely on multiple activations that must happen within a set period of time (such as double-tap to zoom, or double-tap and hold for a synthetic double-click)."

---

## 2. touch-action 적용 시점 / preventDefault가 늦는 이유

### 제스처 시작 시점에 touch-action이 고정됨 (MDN)
URL: https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action
원문 요약: 브라우저는 제스처가 시작될 때 터치된 요소와 그 조상 요소들의 touch-action 값을 교차 적용해 판정하며, 일단 제스처가 시작된 후에는 touch-action 변경이 현재 진행 중인 제스처에 영향을 주지 않는다.
직접 관련된 원문 구절: "When a gesture is started, the browser intersects the touch-action values of the touched element and its ancestors, up to the one that implements the gesture (in other words, the first containing scrolling element)." / "After a gesture starts, changes to touch-action will not have any impact on the behavior of the current gesture."

### preventDefault가 늦는 이유 — touch-action을 먼저 선언해야 하는 이유 (MDN)
URL: https://developer.mozilla.org/en-US/docs/Web/CSS/touch-action
원문 요약: Touch Events를 쓰는 애플리케이션은 preventDefault()로 브라우저의 제스처 처리를 막지만, 이벤트 리스너가 호출되기도 전에 브라우저가 애플리케이션의 의도를 알 수 있도록 touch-action도 함께 사용해야 한다고 명시한다. Pointer Events를 쓰는 애플리케이션은 브라우저가 터치 제스처 처리를 시작하면 pointercancel 이벤트를 받는다.
직접 관련된 원문 구절: "By default, panning (scrolling) and pinching gestures are handled exclusively by the browser. An application using Pointer events will receive a pointercancel event when the browser starts handling a touch gesture." / "Applications using Touch events disable the browser handling of gestures by calling preventDefault(), but should also use touch-action to ensure the browser knows the intent of the application before any event listeners have been invoked."

### 브라우저가 non-passive 리스너의 완료를 기다려야 하는 이유 (Chrome Developers)
URL: https://developer.chrome.com/blog/scrolling-intervention
원문 요약: touchstart 또는 첫 touchmove 이벤트에서 preventDefault()를 호출하면 스크롤이 막히는데, 실제로는 대부분의 리스너가 preventDefault()를 호출하지 않음에도 브라우저는 그 여부를 확인하기 위해 이벤트 처리가 끝날 때까지 기다려야 한다고 설명한다.
직접 관련된 원문 구절: "If you call preventDefault() in the touchstart or first touchmove events then you will prevent scrolling. The problem is that most often listeners will not call preventDefault(), but the browser needs to wait for the event to finish to be sure of that."

### 컴포지터 스레드가 메인 스레드와 독립적으로 처리하는 조건 (Chrome Developers)
URL: https://developer.chrome.com/blog/inside-browser-part4 ("Inside look at modern web browser (part 4)")
원문 요약: 페이지에 입력 이벤트 리스너가 붙어 있지 않으면 컴포지터 스레드는 메인 스레드와 완전히 독립적으로 새 컴포지트 프레임을 생성할 수 있고, 입력 이벤트가 리스너가 없는(non-fast scrollable) 영역 밖에서 발생하면 메인 스레드를 기다리지 않고 계속 컴포지팅한다.
직접 관련된 원문 구절: "If no input event listeners are attached to the page, Compositor thread can create a new composite frame completely independent of the main thread." / "If input event comes from outside of this region, then the compositor thread carries on compositing new frame without waiting for the main thread." / "Alternatively, you may use CSS rule like touch-action to completely eliminate the event handler."

---

## 3. Pointer Events 취소 동작

### pointercancel이 발생하는 조건 (W3C 스펙 원문)
URL: https://www.w3.org/TR/pointerevents3/ ("Suppressing a pointer event stream" section)
원문 요약: 브라우저는 특정 pointerId를 가진 포인터에 대해 더 이상 이벤트를 받을 가능성이 낮다고 판단하면 포인터 이벤트 스트림을 억제해야(MUST) 하며, 그 조건 중 하나로 "포인터가 이후 뷰포트 조작(패닝·줌)에 사용되는 경우"를 명시한다. 이 억제 처리 절차의 첫 단계가 pointercancel 이벤트 발생이다.
직접 관련된 원문 구절: "The user agent MUST suppress a pointer event stream when it detects that the web page is unlikely to continue to receive pointer events with a specific pointerId. Any of the following scenarios satisfy this condition (there MAY be additional scenarios): ... The pointer is subsequently used by the user agent to manipulate the page viewport (e.g. panning or zooming). See the section on touch-action CSS property for details." / "The user agent MUST run the following steps to suppress a pointer event stream: Fire a pointercancel event. Fire a pointerout event. Fire a pointerleave event. Implicitly release the pointer capture if the pointer is currently captured."
관련 이벤트 정의 원문: "The user agent MUST fire a pointer event named pointercancel when it detects a scenario to suppress a pointer event stream." (Bubbles: Yes, Cancelable: No, Composed: Yes)

### setPointerCapture() 정의
URL: https://www.w3.org/TR/pointerevents3/ ("Pointer Capture" section)
원문 요약: 인자로 받은 pointerId에 대해, 이 메서드를 호출한 요소로 포인터 캡처를 설정한다. 이후 해당 포인터의 이벤트는 일반적인 히트 테스트 결과 대신 항상 이 캡처 대상 요소로 타겟팅된다.
직접 관련된 원문 구절: "Set pointer capture for the pointer identified by the argument pointerId to the element on which this method is invoked. For subsequent events of the pointer, the capturing target will substitute the normal hit testing result as if the pointer is always over the capturing target, and they MUST always be targeted at this element until capture is released. The pointer MUST be in its active buttons state for this method to be effective, otherwise it fails silently."

### releasePointerCapture() 정의
URL: https://www.w3.org/TR/pointerevents3/ ("Pointer Capture" section)
원문 요약: 인자로 받은 pointerId에 대해, 이 메서드를 호출한 요소로부터 포인터 캡처를 해제한다. 이후 해당 포인터의 이벤트는 일반적인 히트 테스트 방식을 따른다.
직접 관련된 원문 구절: "Release pointer capture for the pointer identified by the argument pointerId from the element on which this method is invoked. Subsequent events for the pointer follow normal hit testing mechanisms (out of scope for this specification) for determining the event target."

---

## 4. Passive event listener

### touchstart/touchmove의 passive 기본값 (WHATWG DOM 스펙 원문)
URL: https://dom.spec.whatwg.org/#the-default-passive-value ("The default passive value" algorithm; general anchor https://dom.spec.whatwg.org/#dom-eventlisteneroptions-passive)
원문 요약: WHATWG DOM 표준은 addEventListener() 호출 시 리스너의 passive 옵션이 명시되지 않은 경우 기본값을 결정하는 알고리즘("default passive value")을 정의하며, 이벤트 타입이 touchstart/touchmove/wheel/mousewheel이고 대상이 Window·해당 노드의 document·documentElement·body 중 하나이면 true를 반환하도록 규정한다.
직접 관련된 원문 구절: "The default passive value, given an event type type and an EventTarget eventTarget, is determined as follows: Return true if all of the following are true: type is one of \"touchstart\", \"touchmove\", \"wheel\", or \"mousewheel\". ... eventTarget is a Window object, or is a node whose node document is eventTarget, or is a node whose node document's document element is eventTarget, or is a node whose node document's body element is eventTarget. ... Return false."
관련 정의(같은 스펙, passive 옵션 자체): "When set to true, options's passive indicates that the callback will not cancel the event by invoking preventDefault()."

### 동일 동작에 대한 Chrome 측 설명 (Chrome Developers)
URL: https://developer.chrome.com/blog/scrolling-intervention
원문 요약: touchstart 또는 touchmove 리스너의 대상이 window, document, body인 경우 Chrome은 passive를 true로 기본 설정하는 인터벤션을 도입했다고 설명한다.
직접 관련된 원문 구절: "if the target of a touchstart or touchmove listener is the window, document or body we default passive to true."

---

## 5. 플랫폼 이동 임계값 (touch slop)

### Android — ViewConfiguration.getScaledTouchSlop() 및 관련 상수
URL (공식 API 레퍼런스): https://developer.android.com/reference/android/view/ViewConfiguration
URL (AOSP 원본 소스): https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/core/java/android/view/ViewConfiguration.java
원문 요약: getScaledTouchSlop()은 "사용자가 스크롤을 시작한다고 판단하기 전까지 터치가 이동할 수 있는 거리(픽셀)"를 반환한다. AOSP 소스 기준 기본 TOUCH_SLOP 상수는 8dp이며, PAGING_TOUCH_SLOP(페이지 스크롤 판정)은 TOUCH_SLOP의 2배(16dp), DOUBLE_TAP_TOUCH_SLOP은 TOUCH_SLOP과 동일(8dp), DOUBLE_TAP_SLOP(더블탭 두 터치 간 거리)은 100dp, WINDOW_TOUCH_SLOP은 16dp이다. 이 값들은 config_viewConfigurationTouchSlop 리소스로 기기별 오버레이가 가능하다고 명시되어 있다.
직접 관련된 원문 구절 (developer.android.com, getScaledTouchSlop 반환값 설명): "Distance in pixels a touch can wander before we think the user is scrolling"
직접 관련된 원문 구절 (AOSP 소스 주석, TOUCH_SLOP 상수): "Distance a touch can wander before we think the user is scrolling in dips. Note that this value defined here is only used as a fallback by legacy/misbehaving applications that do not provide a Context for determining density/configuration-dependent values. To alter this value, see the configuration resource config_viewConfigurationTouchSlop in frameworks/base/core/res/res/values/config.xml or the appropriate device resource overlay."
직접 관련된 원문 구절 (AOSP 소스, 상수 값): `private static final int TOUCH_SLOP = 8;` / `private static final int PAGING_TOUCH_SLOP = TOUCH_SLOP * 2;` / `private static final int DOUBLE_TAP_TOUCH_SLOP = TOUCH_SLOP;` / `private static final int DOUBLE_TAP_SLOP = 100;` / `private static final int WINDOW_TOUCH_SLOP = 16;`

### iOS/Apple — 공개된 OS 차원의 touch slop 상수
URL: 미발견 (UIKit UIGestureRecognizer / UIPanGestureRecognizer 공식 문서에는 Android ViewConfiguration에 대응하는 시스템 차원의 공개 "touch slop" 픽셀/포인트 상수가 없음)
원문 요약: 조사 범위 내에서 iOS 쪽에 Android의 getScaledTouchSlop()에 정확히 대응하는, OS 레벨에서 공개 문서화된 이동 임계값 상수는 확인하지 못했다. 대신 SwiftUI DragGesture의 초기화 메서드에 프레임워크 차원의 기본값이 공개되어 있다.
직접 관련된 원문 구절 (SwiftUI DragGesture 이니셜라이저 시그니처, 공식 문서 데이터 — https://developer.apple.com/documentation/swiftui/draggesture/init(minimumdistance:coordinatespace:)):
`init(minimumDistance: CGFloat = 10, coordinateSpace: CoordinateSpace = .local)`
비고: 이 값(10포인트)은 SwiftUI DragGesture 하나의 기본 매개변수일 뿐, Android ViewConfiguration처럼 시스템 전역에 적용되는 공식 상수가 아니다. UIKit 레벨(UIPanGestureRecognizer 등)의 대응 공개 수치는 미발견.
