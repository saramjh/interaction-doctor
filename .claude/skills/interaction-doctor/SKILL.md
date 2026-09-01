---
name: interaction-doctor
description: 국제 표준(ISO 9241, W3C) 기반 인간-기기 상호작용(HCI) 3대 축(정확한 입력, 명확한 인지 출력, 3차원 반응 속도)과 사용 환경 다차원 제약(하드웨어/OS/런타임)을 보증하여 인터랙션 결함을 원천 차단하는 에이전틱 코딩 스킬.
---

# Interaction Doctor (상호작용 품질 보증 아키텍트)

## 1. 스킬의 정체성과 궁극적 목적 (First Principle)

LLM은 이미 인류의 모든 프로그래밍 언어, API, 알고리즘, 물리 엔진 지식을 풍부하게 알고 있다.
그러나 **비즈니스 로직, 시각적 UI, 사용 환경(하드웨어/OS/런타임), 반응성 속도** 사이에서 우선순위의 기준을 잃어버릴 때 어텐션 분산과 찐빠가 발생한다.

`interaction-doctor`는 정답 코드를 외워서 치게 만드는 사전이 아니라, **"HCI(인간-컴퓨터 상호작용)의 신체적·물리적 한계 기준과 사용자의 조작 의도를 분석하여, 어떤 언어와 플랫폼에서든 최적의 상호작용 결정을 스스로 도출하도록 이끄는 보편적 의사결정 나침반(Decision Compass)"**이다.

> ⚠️ **[메타 해석 헌장]** 본 헌장에 기재된 괄호 `(...)` 및 세부 항목은 이해를 돕기 위한 대표 예시(Non-exhaustive examples)이며, 에이전트는 특정 언어나 UI 형태에 국한되지 않고 사용자의 모든 상황과 플랫폼에 이 보편 원리를 능동적으로 확장 적용해야 한다.

---

## 2. 3대 상호작용 절대 목적 계약 (Core 3-Axis Contract)

에이전트는 구현 언어(Swift, Kotlin, Flutter, React, Web, Unity 등 환경 일체)에 관계없이 다음 3대 목적을 최우선 기준으로 고정(Anchor)해야 한다:

### 1) 축 1: 정확한 커맨드 입력 (Input Fidelity & Anti-Interference)
* **목적**: 사용자가 내린 조작 명령이 브라우저/OS의 기본 제스처나 인접 UI의 간섭을 받지 않고 100% 온전히 시스템에 전달되어야 한다.
* **4대 입력 양식 전수 클러스터링**:
  1. **연속적 공간 변위 입력 (Continuous Spatial Modality)**: 1D 선형 축 이동(슬라이더/스크러버/스크롤), 2D 평면 벡터 이동(패닝/DnD/스와이프) $\to$ *초기 슬롭(8px) 내 의도 확정 및 직교 축 간섭 격리*
  2. **다점 기하 변환 입력 (Multi-Point Geometric Modality)**: 거리 비례 스케일링(핀치 줌), 각도 비례 회전(다이얼/로테이션) $\to$ *포인터별 독립 식별자 분리, 4대 원시 스칼라 분리 헌장([차수 가드] $\to$ [4대 실수 스칼라 x1,y1,x2,y2 독립 추출] $\to$ [순수 스칼라 대수식 완결]) 준수로 전 언어 런타임 NaN/속성 누락 원천 차단 및 중심점(Centroid) 불변 유지*
  3. **시간 누적 및 압력 임계 입력 (Temporal & Pressure Modality)**: 시간 유지(롱프레스/홀드), 연속 반복 탭(더블탭) $\to$ *생리적 손떨림 보존 및 시간 임계(350ms) 도달 시 상위 스크롤러 권한 즉시 박탈*
  4. **이산적 상태 트리거 입력 (Discrete Event Modality)**: 순간 접촉(단일 탭/클릭/토글/단축키) $\to$ *최소 44dp 물리 히트박스 보장 및 중복 실행 멱등성 락*

### 2) 축 2: 명확한 정보 인지 출력 (Output Visibility & Affordance)
* **목적**: 손가락 가림, 가상 키보드 팝업, 화면 회전 등의 동적 환경에서도 사용자가 "내가 지금 무엇을 바꾸고 있고 어떤 상태인가"를 1밀리초의 모호함도 없이 실시간 인지할 수 있어야 한다.
* **3대 인지 보장 전수 클러스터링**:
  1. **신체 가림 및 환경 침범 방어 (Occlusion & Obstruction Defense)**: 손끝 접촉 면적에 가려지지 않는 오프셋 인디케이터 제공, 가상 키보드/OS 바 침범 시 가용 뷰포트 자동 확보(Keep-in-View).
  2. **상태 전이의 즉시 표명 (State Transparency & Affordance)**: 조작 시작(Active), 경합(Evaluating), 점유(Locked), 완료(Released)의 전 과정을 시각적·촉각적으로 1ms 지연 없이 투명하게 표명.
  3. **물리적 한계 및 경계 피드백 (Boundary & Dynamic Friction Output)**: 컨텐츠 끝 도달 시 고무줄 탄성(Rubber-band), 스냅 안착 시 촉각 틱(Haptic Tick) 등 공간적 한계치를 사용자 감각에 직관 전달.

### 3) 축 3: 상호작용 속도 (3차원 정밀 분리 정의: Velocity & Time)
* **목적**: '속도'의 다차원적 물리 특성을 분리하여, 지연 없는 반응성과 자연스러운 물리 감속을 동시에 달성한다.
  * **[차원 1] 추종 지연 (Tracking Latency) = 0.00ms (Zero-Lag)**: 조작 진행 중(Dragging/Pinching) 손끝과 객체 사이의 간극을 0초로 밀착 (불필요한 CSS transition/이징 지연 0건).
  * **[차원 2] 인지 접수 속도 (Feedback Immediacy) < 50ms**: 브라우저/OS의 300ms 대기 딜레이를 파괴하고 터치 즉시 시각적 압축(Scale 0.96) 및 햅틱 발화.
  * **[차원 3] 동역학적 수렴 시간 (Kinetic Duration) = 자연 물리 감속**: 손을 뗀 후(Release) 관성 스크롤 및 복귀는 직전 100~120ms 평균 속도 벡터 기반의 부드러운 지수 감속 적용.

---

## 3. 국제 표준 기반 사용 환경 다차원 제약 매트릭스 (Context-of-Use Matrix)

국제 표준(ISO 9241-11/210/410, W3C Pointer Events L3, Fitts's Law)에 따라 사용 환경의 하드웨어 및 소프트웨어 제약을 사전에 판별하고 방어한다.

### 1) [하드웨어 계층 제약] 물리적 입력 장치 및 디바이스 특성 (ISO 9241-410)
* **스마트폰 (Mobile Handheld)**: 손가락 접촉 면적 7~10mm, 생리적 손떨림 3~5px $\to$ **8.0px 터치 슬롭** 히스테리시스, 최소 44×44dp 히트박스, GPU 0ms 1:1 하드웨어 가속.
* **태블릿 & 스타일러스 (Tablet & Pen)**: 펜촉 정밀도 0.5~1.0mm, 손바닥 오터치 > 15mm $\to$ `pointerType === 'pen'` 감지 시 슬롭 0.5px 축소, 15mm 초과 광역 접촉 **Palm Rejection 즉시 폐기**.
* **데스크톱 & 랩톱 (Desktop / Laptop)**: 1px 미세 마우스 커서, 창 이탈 위험 $\to$ W3C `setPointerCapture` 필수 결합, 트랙패드 vs 휠 노치 정규화, 텍스트 선택 방어.
* **폴더블 & 가변 기기 (Foldable / Dual)**: 힌지(Hinge) 각도 및 화면 분할 $\to$ 뷰포트 상대 비율($x / W_{\text{viewport}}$) 동적 재동기화.

### 2) [소프트웨어 계층 제약] 운영체제(OS) 및 런타임/엔진 특성
* **Apple iOS / iPadOS**: 좌우 20pt 엣지 스와이프 제스처 선점 $\to$ **20pt 엣지 데드존 확보**, `overscroll-behavior: contain !important`, `-webkit-touch-callout: none`.
* **Google Android**: 24dp 예측 뒤로가기(Predictive Back) $\to$ **24dp 엣지 세이프존**, `contextmenu` 방어, 상단 PTR 선점 방어.
* **WebKit / Blink / Native Runtime**:
  * Web: `100dvh` 및 `VisualViewport API` 바인딩, `touch-action: manipulation`, 비패시브 리스너 명시.
  * Native: React Native `Reanimated Worklet`, Compose `detectTransformGestures`, SwiftUI `SimultaneousGesture` 등 각 런타임 고유 아키텍처 매핑.

---

## 4. 세상의 모든 UX 상호작용: 5대 메가 클러스터 조작 프로토콜

세상의 모든 UX 상호작용은 수학적·물리적 특성에 따라 다음 5대 클러스터로 수렴하며, 에이전트는 해당 클러스터의 불변식(Invariants)을 적용한다.

```
[1. 연속 공간 변위 (Displacement)] ──> 8px 초기 축 잠금 + 1:1 즉각 추종 + 100ms 궤적 관성 감속
[2. 다점 기하 변환 (Multi-Point)]   ──> 좌표 맵 독립 저장 + 4대 원시 스칼라 분리 수식 + N→N-1 앵커 재동기화
[3. 시간 임계 승격 (Temporal)]       ──> 5px 슬롭 내 시간 누적 + 승격 시 스크롤 차단 + 탭 즉시 발화 분기
[4. 가변 뷰포트 침범 (Viewport)]     ──> dvh/VisualViewport 바인딩 + 활성 필드 시야 확보 + Safe-Area 패딩
[5. 이산 피드백 트리거 (Discrete)]   ──> 최소 44dp 히트박스 + 0ms 시각/촉각 피드백 + 비동기 멱등 락
```

---

## 5. LLM 실행 파이프라인 및 하드 스탑 자가 검증 (4-Step Execution Flow)

### 1단계: 사용 환경 및 의도 분석 (Context & Intent Extraction)
* ISO 표준에 따라 기기 환경(모바일/태블릿/데스크톱), OS 특성(iOS/Android/macOS/Win), 런타임을 판별하고 해당 조작이 5대 클러스터 중 어디에 속하는지 식별한다.

### 2단계: 3축 상호작용 계약 수립 (Contract Formulation)
* **입력 축**: 4대 입력 양식 중 무엇이며 어떤 시스템 간섭(엣지 제스처/스크롤러)을 격리할 것인가?
* **출력 축**: 손가락 가림/키보드 침범 시 어떤 시각적/촉각적 피드백과 뷰포트를 확보할 것인가?
* **속도 축**: 조작 중 0ms 1:1 밀착 추종 및 릴리즈 시 감속/스냅을 어떻게 처리할 것인가?

### 3단계: 조작 프로토콜 기반 코드 구현 (Protocol-Driven Implementation)
* [cluster-invariants.md](references/cluster-invariants.md) 및 [platform.md](references/platform.md)를 참조하여 해당 런타임 표준에 맞게 코드를 구현한다.

### 4단계: CoT 하드 스탑 자가 검증 선언 (Self-Correction Reflection)
* **[강제 규칙]** 에이전트는 최종 코드를 출력하기 직전, 내부 사고(CoT)에서 다음 3가지 물리 검증을 거쳐 **`[UX 자가 검증 판정]`** 블록을 반드시 명시해야 한다:
  1. `[4대 원시 스칼라 분리 수식 추적]`: 언어와 관계없이 다점 기하 연산 시 복합 객체/컨테이너를 수식 내에 직접 전달하지 않고, `[가드 -> 4대 실수 스칼라(x1,y1,x2,y2) 선행 바인딩 -> 순수 스칼라 대수식 계산]` 불변식을 준수했는가? (전 언어 런타임 NaN/속성 누락 0% 확인)
  2. `[0ms 물리 반응성 대조]`: 조작 중(Dragging/Pinching) 화면이 손끝에 0ms로 밀착되는가? (불필요한 CSS transition/이징 지연 0건 확인)
  3. `[경계/플랫폼 간섭 방어]`: 롱프레스 시 손떨림(5px) 보존 및 승격 즉시 상위 스크롤러 탈취 차단이 보장되는가?

```markdown
<!-- 코드 출력 직전 강제 실행되는 CoT 선언 블록 -->
[UX 자가 검증 판정]
• 4대 원시 스칼라 분리 및 식별자 격리: PASS (4-Scalar Primitive Binding 준수 및 전 언어 NaN 0% 확인)
• 0ms 실시간 밀착 반응성: PASS (조작 중 지연 0건, rAF 중복 폭주 방어 확인)
• 시스템 간섭 및 경계 방어: PASS (스크롤러 탈취 차단 및 5px 슬롭, Safe-Area 보존 확인)
```

---

## 6. 핵심 참조 헌장 (References)

* [보편적 UX 상호작용 계약 헌장](references/ux-contract.md): 3대 축 철학 & 4대 입력 양식 & 3대 인지 출력 & 3차원 속도 전문
* [5대 클러스터 상태 전이 및 불변식 나침반](references/cluster-invariants.md): 클러스터별 생애주기 다이어그램과 엄격한 불변식
* [복합 중첩 상호작용 충돌 해소 헌장](references/recipes.md): 중첩 제스처 권한 승격 및 핸드오프 법칙
* [국제 표준 기반 플랫폼 & 디바이스 보편 물리 헌장](references/platform.md): ISO 9241, W3C, OS/하드웨어 물리 제약 & 선점 방어 보편 기준
* [상호작용 결함 증상 역추적 진단서](references/symptoms.md): 사용자 체감 증상 기반 결함 진단 룩업
* [36대 결함 해결 인과 보증서](references/guarantee-matrix.md): P01~P36 전수 결함과 물리 불변식의 1:1 결정론적 보증 매트릭스
