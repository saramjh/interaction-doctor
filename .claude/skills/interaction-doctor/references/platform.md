# 플랫폼 & 디바이스 보편 물리 헌장 (Omni-Platform & Device Invariant Charter)

## 0. 개요: 하드웨어, OS, 소프트웨어 런타임을 관통하는 보편 물리 계층

인간의 신체적 특성(손가락 면적, 미세 떨림, 반응 시간)과 입력 하드웨어(터치스크린, 스타일러스 펜, 트랙패드, 마우스)는 소프트웨어 스택과 무관한 **수학적·물리적 절대 법칙**을 형성한다.
`interaction-doctor`는 특정 브라우저나 자바스크립트에 국한되지 않고, **Web, React Native, Flutter, Swift/SwiftUI, Kotlin/Jetpack Compose, Electron, Unity** 등 모든 환경에서 동일하게 적용되는 포괄적 물리 계약을 제공한다.

---

## 1. 멀티 디바이스 하드웨어 특성 및 물리 제약 (Multi-Device Matrix)

### 1) 스마트폰 터치스크린 (60Hz / 90Hz / 120Hz ProMotion)
* **물리 특성**: 정전식 터치 센서의 접촉 면적은 직경 7~10mm에 달하며, 접촉 초기 약 3~5px의 인체 자연 떨림(Physiological Tremor)이 무조건 발생한다.
* **120Hz 고주사율 특성**: 8.3ms 주기로 이벤트가 쏟아지며, 자바스크립트/UI 스레드에서 메인 루프 연산이 8ms를 초과하면 즉시 프레임 드롭(Micro-stutter)이 발생한다.
* **보편 방어 규칙**:
  * **8.0px 터치 슬롭(Touch Slop)**: 초기 8px 이동 전까지는 스크롤/드래그 상태 전이를 유예하고 탭 판정을 보존한다.
  * **0ms GPU 가속 불변식**: 레이아웃 리플로우(Reflow)를 유발하는 속성(`top`, `left`, `width`, `height`)의 실시간 변경을 금지하고, 컴포지터 레이어(`transform3d`, `Matrix4`, `GraphicsLayer`)만으로 렌더링한다.

### 2) 태블릿 & 스타일러스 펜 (Apple Pencil, S-Pen, Wacom)
* **물리 특성**: 펜촉 접촉 면적은 0.5~1.0mm로 극도로 정밀하며, 화면에 손바닥을 기댄 채 필기하는 **팜 리젝션(Palm Rejection)** 요구가 발생한다.
* **보편 방어 규칙**:
  * **포인터 타입 식별 격리 (`pointerType === 'pen' | 'touch' | 'mouse'`)**: 펜 입력 시에는 8px 슬롭을 0.5px로 축소하여 즉각 반응하도록 하고, 스타일러스 활성 중 유입되는 광역 터치(`contact area > 15mm`)는 손바닥으로 판정하여 무조건 폐기한다.
  * **압력(Pressure) 및 틸트(Tilt) 데이터 독립 채널화**: 변위($\Delta x, \Delta y$) 계산과 압력 수치를 결합하지 않고 직교 상태로 보존한다.

### 3) 데스크톱 & 노트북 (정밀 트랙패드, 마우스 휠, 3버튼)
* **물리 특성**:
  * **고해상도 트랙패드**: 2손가락 핀치 줌과 2손가락 스크롤이 동일한 입력 축에서 발생하며, 운영체제의 가속 곡선(Inertial Smoothing)이 개입한다.
  * **마우스 휠**: 노치 단위 틱(Tick: 100~120 delta)과 픽셀 단위 연속 스크롤(트랙패드)이 혼재한다.
* **보편 방어 규칙**:
  * **Wheel vs Pinch 식별 불변식**: Web 환경에서는 `e.ctrlKey === true`를 핀치 줌으로 분기하고, 네이티브 환경에서는 제스처 인식기(`MagnificationGesture` / `ScaleGestureDetector`)를 휠 스크롤러와 명시적으로 격리한다.
  * **델타 단위 정규화 (Delta Normalization)**: 라인 단위(DOM_DELTA_LINE)와 픽셀 단위(DOM_DELTA_PIXEL)를 감지하여 1틱당 이동 거리를 물리적 픽셀(16~24px)로 정규화한다.

### 4) 폴더블 & 듀얼 스크린 (Foldable Displays)
* **물리 특성**: 힌지(Hinge) 영역의 불연속 접힘 각도 및 가변 화면비(Aspect Ratio) 전환.
* **보편 방어 규칙**:
  * 드래그 도중 화면 회전/접힘 이벤트 발생 시, 현재 제스처 좌표계를 리셋하지 않고 뷰포트 상대 비율($x / W_{\text{viewport}}$)로 앵커를 보정한다.

---

## 2. 멀티 운영체제(OS) 시스템 제스처 선점 방어 (Multi-OS Invariants)

| 운영체제 (OS) | 시스템 침범 메커니즘 | 물리적 위험 증상 | 보편 아키텍처 방어 규칙 |
|:---|:---|:---|:---|
| **Apple iOS / iPadOS** | • 엣지 스와이프 (`UIScreenEdgePan`)<br>• 바운스 오버스크롤<br>• 텍스트 선택 돋보기 콜아웃 | • 사이드 드로어 스와이프 중 브라우저 뒤로가기 탈취<br>• 리스트 끝 도달 시 전체 페이지 덜컹거림<br>• 롱프레스 시 텍스트 파란색 선택 글리치 | • 좌측 20pt 엣지 데드존(Deadzone) 확보<br>• `overscroll-behavior: contain !important`<br>• `user-select: none`, `-webkit-touch-callout: none` 전역 격리 |
| **Google Android** | • 예측 뒤로가기 제스처 (Predictive Back)<br>• 시스템 `contextmenu` 강제 발화<br>• 시스템 Pull-to-Refresh | • 화면 좌우 24dp 스와이프 시 앱이 닫힘<br>• 터치 조작 중 크롬 브라우저 팝업 메뉴 침범<br>• 캔버스 조작 중 상단 새로고침 탈취 | • `OnBackPressedCallback` / 엣지 24dp 여백 확보<br>• `contextmenu` 취소(`preventDefault()`)<br>• `overscroll-behavior-y: contain` 격리 |
| **macOS** | • 트랙패드 2손가락 좌우 스와이프 뒤로가기<br>• 관성 스크롤 체이닝 (Scroll Chaining) | • 내부 캐러셀 넘기다 브라우저 이전 페이지로 날아감<br>• 모달 내부 스크롤 끝나면 부모 창이 스크롤됨 | • 가로 스와이퍼에 `overscroll-behavior-x: contain`<br>• 마우스/휠 진입 시 상위 윈도우 전파 중단(`stopPropagation()`) |
| **Microsoft Windows** | • DirectManipulation 합성기<br>• 윈도우 스냅 제스처<br>• 마우스 우클릭 합성 딜레이 | • 드래그 요소가 윈도우 제스처에 씹힘<br>• 300ms 클릭 합성 지연 발생 | • `touch-action: none` / `pointerdown` 캡처<br>• W3C Pointer Events 표준 API 일원화 |

---

## 3. 멀티 소프트웨어 프레임워크 구현 매핑 (Universal Invariant Binding Table)

상호작용 물리 헌장은 모든 프레임워크의 네이티브 API에 1:1로 정확히 대응된다:

### 1) W3C Web (Vanilla DOM, React, Vue, Svelte)
```typescript
// 1. 단일 소유권 포인터 캡처
element.addEventListener('pointerdown', (e) => {
  element.setPointerCapture(e.pointerId);
});

// 2. 중심점 불변 보존 (Centroid Invariant)
// transform-origin: 0 0 고정 필수
const worldX = (cursorX - panX) / scale;
const worldY = (cursorY - panY) / scale;
panX = cursorX - worldX * newScale;
panY = cursorY - worldY * newScale;
```

### 2) React Native & Expo (`react-native-gesture-handler` + `Reanimated`)
```typescript
// 8px 직교 축 잠금 및 350ms 시간 승격
const panGesture = Gesture.Pan()
  .activeOffsetX([-8, 8])   // 8px X축 잠금
  .failOffsetY([-8, 8])     // 수직 이동 시 즉시 포기하고 스크롤러에 양보
  .simultaneousWithExternalGesture(scrollRef);

const longPressGesture = Gesture.LongPress()
  .minDuration(350)         // 350ms 시간 임계 승격
  .onStart(() => { 'worklet'; runOnJS(triggerHaptic)(); });
```

### 3) Flutter (`InteractiveViewer` & `RawGestureDetector`)
```dart
// FocalPoint 기반 Centroid Invariant (Matrix4 보존)
void _handleScaleUpdate(ScaleUpdateDetails details) {
  final Offset focalPoint = details.localFocalPoint;
  // Flutter Matrix4: 포커스 포인트 기준 줌 변환
  final Matrix4 newTransform = Matrix4.identity()
    ..translate(focalPoint.dx, focalPoint.dy)
    ..scale(details.scale)
    ..translate(-focalPoint.dx, -focalPoint.dy);
}
```

### 4) Native iOS (Swift & SwiftUI)
```swift
// Simultaneous Gesture & Hit Target Extension (44pt)
var body: some View {
    CanvasView()
        .gesture(
            SimultaneousGesture(
                MagnificationGesture().onChanged { value in
                    // Centroid invariant preservation via anchorPoint
                },
                DragGesture(minimumDistance: 8) // 8pt Slop Gate
            )
        )
        .frame(minWidth: 44, minHeight: 44) // Apple HIG 44pt Hit Target
}
```

### 5) Native Android (Kotlin & Jetpack Compose)
```kotlin
// PointerInput 기반 Centroid & Pan 분리
Modifier.pointerInput(Unit) {
    detectTransformGestures(panZoomLock = true) { centroid, pan, zoom, rotation ->
        // centroid: 중심점 불변식 좌표
        // 0ms 그래픽스 레이어 갱신
        graphicsLayer {
            scaleX *= zoom
            scaleY *= zoom
            translationX += pan.x
            translationY += pan.y
        }
    }
}
```

---

## 4. 에이전트 준수 규약 (Agent Implementation Contract)

어떤 플랫폼/언어 환경이 주어지더라도 에이전트는 다음 4대 물리 원칙을 코드로 반드시 증명해야 한다:
1. **타겟 플랫폼의 최소 물리 크기 보장**: iOS `44×44pt`, Android `48×48dp`, Web `44×44px` (터치 타깃 확장).
2. **슬롭 게이트 통과 전까지 상위 제스처 점유 금지**: 8px/8dp 슬롭 이전의 조기 제스처 가로채기 원천 차단.
3. **가변 뷰포트 높이 0ms 적응**: 모바일 가상 키보드(IME) 출현 시 화면 가림 방지 (`VisualViewport` / `WindowInsetsAnimation`).
4. **다점 기하 중심축 불변식 보존**: 줌/회전 시 초점 좌표가 화면 상에서 $0\text{px}$ 오차로 고정되는 월드-스크린 변환 역보정 수식 강제.
