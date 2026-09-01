---
name: interaction-doctor
description: 국제 표준(ISO 9241, W3C) 기반 인간-기기 상호작용(HCI) 3대 축(정확한 입력, 명확한 인지 출력, 3차원 반응 속도)과 5대 클러스터 불변식을 보증하여 인터랙션 결함을 원천 차단하는 에이전틱 코딩 스킬.
---

# Interaction Doctor (상호작용 품질 보증 아키텍트)

## 1. 스킬의 정체성과 궁극적 목적 (First Principle)

LLM은 이미 인류의 모든 프로그래밍 언어, API, 알고리즘, 물리 엔진 지식을 풍부하게 알고 있다.
그러나 **비즈니스 로직, 시각적 UI, 사용 환경(하드웨어/OS/런타임), 반응 속도** 사이에서 우선순위의 기준을 잃어버릴 때 어텐션 분산과 결함이 발생한다.

`interaction-doctor`는 정답 코드를 외워서 치게 만드는 사전이 아니라, **"HCI(인간-컴퓨터 상호작용)의 신체적·물리적 한계 기준과 사용자의 조작 의도를 분석하여, 어떤 언어와 플랫폼에서든 최적의 상호작용 결정을 스스로 도출하도록 이끄는 보편적 의사결정 나침반(Decision Compass)"**이다.

---

## 2. 3대 상호작용 축 & 5대 클러스터 나침반 요약

에이전트는 구현 언어(Swift, Kotlin, Flutter, React, Web, Unity 등 환경 일체)에 관계없이 다음 **3대 축과 5대 클러스터 불변식**을 코딩 사고의 절대 기준으로 삼는다.

### 🎯 3대 상호작용 축 (Core 3-Axis)
1. **정확한 커맨드 입력 (Input Fidelity)**: 브라우저/OS 제스처 및 직교 축 간섭 차단 (Axis Lock, 포인터 캡처, 식별자 분리).
2. **명확한 정보 인지 출력 (Cognitive Visibility)**: 신체 가림(7~10mm) 방어, 가상 키보드 뷰포트 확보, 1ms 상태 투명 표명.
3. **상호작용 속도 (Velocity & Time)**: 조작 중 0.00ms 1:1 추종 밀착, 접수 즉시 <50ms 피드백, 릴리즈 시 120ms 모멘텀 큐 자연 감속.

### 🧭 5대 메가 클러스터 조작 프로토콜
```
[1. 연속 공간 변위 (Displacement)] ──> 8px 초기 축 잠금 + 1:1 즉각 추종 + 120ms 궤적 관성 감속
[2. 다점 기하 변환 (Multi-Point)]   ──> 좌표 맵 독립 저장 + 4대 원시 스칼라 분리 수식 + N↔M 앵커 재동기화
[3. 시간 임계 승격 (Temporal)]       ──> 5px 슬롭 내 시간 누적 + 승격 시 스크롤 차단 + 탭 즉시 발화 분기
[4. 가변 뷰포트 침범 (Viewport)]     ──> dvh/VisualViewport 바인딩 + 활성 필드 시야 확보 + Safe-Area 패딩
[5. 이산 피드백 트리거 (Discrete)]   ──> 최소 44dp 히트박스 + 0ms 시각/촉각 피드백 + 비동기 멱등 락
```

---

## 3. 국제 표준 사용 환경 분석 (Context-of-Use Matrix)

국제 표준(ISO 9241-11/210/410, W3C Pointer Events L3)에 따라 하드웨어 및 OS 제약을 사전 판별한다:
* **스마트폰**: 7~10mm 손가락 면적, 3~5px 손떨림 $\to$ **8.0px 터치 슬롭**, 최소 44×44dp 히트박스, GPU 0ms 1:1 가속.
* **태블릿 & 스타일러스**: 0.5~1.0mm 펜촉 vs 15mm 팜 $\to$ 슬롭 0.5px 축소, 15mm 초과 광역 접촉 **Palm Rejection 즉시 폐기**.
* **데스크톱**: 1px 커서 $\to$ W3C `setPointerCapture` 필수 결합, 트랙패드 vs 마우스 휠 노치 틱 정규화, 텍스트 선택 방어.
* **OS 시스템 제스처 방어**: iOS 20pt / Android 24dp 엣지 데드존 확보, `overscroll-behavior: contain !important`.

---

## 4. LLM 실행 파이프라인 및 하드 스탑 자가 검증 (4-Step Execution Flow)

### 1단계: 사용 환경 및 의도 분석 (Context & Intent Extraction)
* 기기 환경(모바일/태블릿/데스크톱), OS 특성(iOS/Android/macOS/Win), 런타임을 판별하고 조작 클러스터를 식별한다.

### 2단계: 3축 상호작용 계약 수립 (Contract Formulation)
* **입력 축**: 어떤 시스템 간섭(엣지 제스처/직교 스크롤러)을 격리할 것인가?
* **출력 축**: 신체 가림/키보드 침범 시 어떤 시각적/촉각적 피드백과 가용 뷰포트를 확보할 것인가?
* **속도 축**: 조작 중 0ms 1:1 밀착 추종 및 릴리즈 시 감속/스냅을 어떻게 처리할 것인가?

### 3단계: 조작 프로토콜 기반 코드 구현 (Protocol-Driven Implementation)
* [cluster-invariants.md](references/cluster-invariants.md), [platform.md](references/platform.md), [recipes.md](references/recipes.md)를 참조하여 코드를 구현한다.

### 4단계: CoT 하드 스탑 자가 검증 선언 (Self-Correction Reflection)
* **[강제 규칙]** 에이전트는 최종 코드를 출력하기 직전, 내부 사고(CoT)에서 다음 3가지 물리 검증을 거쳐 **`[UX 자가 검증 판정]`** 블록을 반드시 명시해야 한다:
  1. `[2계층 분리 수식 추적]`: 언어와 관계없이 다점 기하 연산 시 `arr[i].x` 동시 연쇄를 배제하고, `[Tier 1: 2개 독립 원소(p1, p2) 선행 격리] ➔ [Tier 2: p1, p2로부터 4대 스칼라 추출] ➔ [Tier 3: 순수 스칼라 수식]` 불변식을 준수했는가? (`points.x` 오타, 인덱스 누락, NaN 0% 확인)
  2. `[0ms 물리 반응성 대조]`: 조작 중(Dragging/Pinching) 화면이 손끝에 0ms로 밀착되는가? (불필요한 CSS transition/이징 지연 0건 확인)
  3. `[경계/플랫폼 간섭 방어]`: 롱프레스 시 손떨림(5px) 보존 및 승격 즉시 상위 스크롤러 탈취 차단이 보장되는가?

```markdown
<!-- 코드 출력 직전 강제 실행되는 CoT 선언 블록 -->
[UX 자가 검증 판정]
• 2계층 분리 선언 및 식별자 격리: PASS (Tier 1 [p1, p2] 격리 후 스칼라 추출 준수 및 NaN 0% 확인)
• 0ms 실시간 밀착 반응성: PASS (조작 중 지연 0건, rAF 중복 폭주 방어 확인)
• 시스템 간섭 및 경계 방어: PASS (스크롤러 탈취 차단 및 5px 슬롭, Safe-Area 보존 확인)
```

---

## 5. 핵심 참조 헌장 (References)

* [보편적 UX 상호작용 계약 헌장](references/ux-contract.md): 3대 축 철학 & 4대 입력 양식 & 3대 인지 출력 & 3차원 속도 전문
* [5대 클러스터 상태 전이 및 불변식 나침반](references/cluster-invariants.md): 클러스터별 생애주기 다이어그램과 엄격한 물리 불변식
* [복합 중첩 상호작용 충돌 해소 헌장](references/recipes.md): 중첩 제스처 권한 승격 및 동적 핸드오프 법칙
* [국제 표준 기반 플랫폼 & 디바이스 보편 물리 헌장](references/platform.md): ISO 9241, W3C, Multi-OS/Device 보편 물리 기준
* [보편 환경-물리 불변식 및 결함 인과 보증서](references/guarantee-matrix.md): 체감 증상-근본 물리 원인-수학적 보증 매트릭스

---
---

# [참조 헌장 1] 보편적 UX 상호작용 계약 헌장 (Universal UX Interaction Contract)

# 보편적 UX 상호작용 계약 헌장 (Universal UX Interaction Contract)

## 0. 핵심 철학: 국제 표준 기반 환경 분석과 3대 절대 목적

사용자는 기기와 소통할 때 단순한 텍스트나 그림을 보는 것이 아니라, **자신의 물리적 의도(손끝, 시선, 커서, 키보드)가 시스템과 1:1로 실시간 연결되어 있는가**를 통해 신뢰를 형성한다.

에이전트는 코드를 작성하기 전, 반드시 ISO 9241 및 HCI 인간공학 표준에 따라 다음을 먼저 분석해야 한다:
> **"이 기능은 어떤 하드웨어(모바일/태블릿/데스크톱/폴더블), 어떤 운영체제(iOS/Android/macOS/Windows), 어떤 런타임 환경에서 사용자가 어떤 물리적 의도로 조작하는가?"**

코딩 에이전트가 생성하는 모든 UI/UX 코드는 플랫폼과 언어(Swift, Kotlin, Flutter, React, Web, Unity 등)에 구애받지 않고 다음 **3대 상호작용 축의 절대 목적**을 100% 충족해야 한다.

---

## 1. 3대 상호작용 축 및 전수 클러스터링 (Core 3-Axis System)

### 축 1: 정확한 커맨드 입력 (Input Fidelity & Anti-Interference)
* **목적**: 사용자가 내린 조작 명령이 브라우저/OS의 기본 제스처나 인접 UI 요소의 간섭에 의해 왜곡되거나 가로채이지 않고 **100% 순수하게 시스템에 도달**해야 한다.
* **4대 입력 양식 전수 클러스터링 (Input Modalities)**:
  1. **연속적 공간 변위 입력 (Continuous Spatial Modality)**:
     * *표본*: 1D 선형 축 이동(슬라이더, 룰러, 스크러버, 스크롤), 2D 평면 벡터 이동(캔버스 패닝, 지도 탐색, 드래그앤드롭, 스와이프).
     * *방어 간섭*: 초기 슬롭(5~8px) 내 주 이동 축을 판별하고 확정 즉시 직교 축 스크롤러 개입 차단(Axis Lock).
  2. **다점 기하 변환 입력 (Multi-Point Geometric Modality)**:
     * *표본*: 거리 비례 스케일링(2손가락 핀치 줌), 각도 비례 회전(다이얼, 캔버스 로테이션), 변형 핸들(크롭/리사이즈).
     * *방어 간섭*: 포인터별 독립 식별자(`Map<id, Coord>`) 격리, 중심점(Centroid) 불변 보존, 포인터 수 변경($N \leftrightarrow M$) 시 앵커 즉시 재동기화.
     * *2계층 분리 불변식 (Two-Tier Separation)*: 컨테이너 인덱싱과 속성 조회의 동시 연쇄(`arr[i].prop`)를 엄격히 금지한다. 반드시 [Tier 1: 컨테이너에서 2개 독립 원소 `(p1, p2)` 선행 격리 선언] ➔ [Tier 2: 분리된 `p1, p2`로부터만 4대 실수 스칼라 $(x_1, y_1, x_2, y_2)$ 추출] ➔ [Tier 3: 순수 스칼라 대수식 계산]의 3단계를 준수하여 전 언어 인덱스 누락(`points.x`), 타입 오염, `NaN`을 100% 원천 차단한다.
  3. **시간 누적 및 압력 임계 입력 (Temporal & Pressure Modality)**:
     * *표본*: 시간 유지(롱프레스, 홀드 투 액션), 연속 반복 탭(더블탭, 트리플탭), 압력 센서 터치.
     * *방어 간섭*: 5px 이내 생리적 미세 떨림(Tremor) 보존, 시간 임계(350ms) 도달 즉시 상위 스크롤러 권한 박탈 및 모달 승격.
  4. **이산적 상태 트리거 입력 (Discrete Event Modality)**:
     * *표본*: 순간 접촉(단일 탭, 마우스 클릭, 토글 스위치, 칩 필터, 키보드 단축키).
     * *방어 간섭*: 최소 44×44dp 히트박스 보장, 비동기 멱등성 락(중복 트리거 차단), 300ms 합성 클릭 관통 방어.

---

### 축 2: 명확한 정보 인지 출력 (Output Visibility & Affordance)
* **목적**: 사용자가 조작 중인 순간(손가락 가림), 가상 키보드가 솟아오르는 순간, 화면이 회전하는 순간에도 **"내가 지금 무엇을 바꾸고 있고, 현재 어떤 상태인가?"를 1밀리초의 모호함도 없이 명확히 인지**할 수 있는 실시간 피드백을 제공해야 한다.
* **3대 인지 보장 전수 클러스터링 (Cognitive Visibility)**:
  1. **신체 가림 및 환경 침범 방어 (Occlusion & Obstruction Defense)**:
     * 손가락 접촉 면적(7~10mm)에 UI 수치가 가려지지 않도록 실시간 오프셋 툴팁/인디케이터 제공.
     * 가상 키보드(IME) 및 시스템 Safe Area 침범 시 활성 입력 필드 자동 뷰포트 확보(Keep-in-View).
  2. **상태 전이의 즉시 표명 (State Transparency & Affordance)**:
     * 조작 시작(Active/Press), 경합(Evaluating), 점유(Locked), 완료(Released)의 전 과정을 시각적/촉각적으로 1ms 지연 없이 투명하게 표명.
  3. **물리적 한계 및 경계 피드백 (Boundary & Dynamic Friction Output)**:
     * 컨텐츠 끝에 도달했을 때의 고무줄 탄성(Rubber-band), 스냅 포인트 안착 시의 촉각 틱(Haptic Tick) 등 공간적 한계치를 사용자 감각에 직관 전달.

---

### 축 3: 상호작용 속도 (3차원 정밀 분리 정의: Velocity & Time)
* **목적**: '속도'의 다차원적 물리 특성을 분리하여, 지연 없는 반응성과 자연스러운 물리 감속을 동시에 달성한다.
  * **[차원 1] 추종 지연 (Tracking Latency) = 0.00ms (Zero-Lag)**: 조작 진행 중(Dragging/Pinching) 손끝과 객체 사이의 간극을 0초로 밀착 (불필요한 CSS transition/이징 지연 0건).
  * **[차원 2] 인지 접수 속도 (Feedback Immediacy) < 50ms**: 브라우저/OS의 300ms 대기 딜레이를 파괴하고 터치 즉시 시각적 압축(Scale 0.96) 및 햅틱 발화.
  * **[차원 3] 동역학적 수렴 시간 (Kinetic Duration) = 자연 물리 감속**: 손을 뗀 후(Release) 관성 스크롤 및 복귀는 직전 100~120ms 평균 속도 벡터 기반의 부드러운 지수 감속 적용.

---
---

# [참조 헌장 2] 5대 상호작용 클러스터 상태 전이 및 불변식 나침반 (Cluster Invariants)

# 5대 상호작용 클러스터 상태 전이 및 불변식 나침반 (Cluster Invariants)

## 0. 개요: LLM의 지식 바다를 인도하는 의사결정 기준

LLM은 이미 모든 언어(Swift, Kotlin, Flutter, Web, React Native, Unity 등)의 API와 이벤트 시스템을 알고 있다.
본 문서는 LLM이 코드를 생성할 때 어텐션 분산에 빠지지 않고, **"각 상호작용 원형(클러스터)에서 반드시 지켜야 할 상태 전이 불변식(Invariants)과 7대 런타임 찐빠 방어 헌장"**을 제공하는 사고의 나침반이다.

---

## 1. [클러스터 1] 연속 공간 변위 (Continuous Spatial Displacement)

> **적용 대상**: 스크롤, 1D 슬라이더/페이더, 2D 지도/캔버스 패닝, 캐러셀 스와이프, 당겨서 새로고침(PTR).

### 📐 상태 전이 생애주기
```
[IDLE] ──(터치/포인터 진입)──> [EVALUATING (슬롭 5~8px 구간)]
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
[AXIS LOCKED (주 이동축 확정)]                      [CANCELLED / SUBMITTED]
  • 0ms 1:1 직접 변위 추종                            • 탭 또는 시스템 제스처로 양도
  • 직교 축 간섭 원천 차단
                │
        (포인터 릴리즈)
                ▼
[DECELERATING / SNAPPING]
  • 최근 100~120ms 궤적 평균 속도(v) 기반 관성 감속
  • 경계 도달 시 탄성 저항(Rubber-band) 및 복귀(Restitution)
```

### 🔒 반드시 유지해야 할 불변식 (Invariants)
1. **변위 동기화 불변식**: 드래그 진행 중에는 어떠한 인위적 트랜지션/이징 딜레이도 없어야 하며, 손끝/커서의 $\Delta x, \Delta y$와 뷰의 위치는 $0\text{ms}$로 1:1 일치해야 한다.
2. **축 배타성 불변식**: 주 이동 축이 한 번 확정되면 제스처가 끝날 때까지 수직/직교 축의 스크롤러가 절대 개입하지 못하도록 격리해야 한다.
3. **모멘텀 연속성 불변식**: 손가락을 떼는 순간의 관성 속도는 단일 프레임이 아닌 '최근 이동 궤적의 가중 평균'으로 산출하여 릴리즈 직전 멈춤으로 인한 급정지를 방지해야 한다.
4. **애니메이션 단일 소유권 불변식 (rAF 폭주 방어)**: 새로운 터치(`pointerdown`)가 진입하는 즉시, 실행 중이던 모든 관성/스냅 애니메이션 루프(`requestAnimationFrame`)를 즉시 취소(`cancel`)하고 동결하여 속도 중첩 가속 폭주를 원천 차단해야 한다.
5. **경계 분모 안전성 불변식 (분모 0 Infinity 방어)**: 줌 배율이나 스크롤 퍼센트 연산 시 분모는 항상 `Math.max(1, containerDimension)`을 적용하여 렌더링 초기 $0$ 나누기 에러를 방지해야 한다.

---

## 2. [클러스터 2] 다점 기하 변환 (Multi-Point Geometric Transform)

> **적용 대상**: 2손가락 핀치 줌, 회전 다이얼, 캔버스 프리폼 변형, 이미지 크롭/리사이즈.

### 📐 상태 전이 생애주기
```
[N=1 POINTER (단일 조작)] ──(추가 포인터 진입)──> [N=2 MULTI-GEOMETRY (기하 변환)]
                                                     • 앵커 중심점(Centroid) 계산
                                                     • 유클리드 거리/각도 실시간 차분
                                                     • 식별자 분리 수식 연산
                                                           │
                                                (손가락 하나 릴리즈 N -> 1)
                                                           ▼
                                                [RE-SYNC ANCHOR (앵커 재동기화)]
                                                     • 남은 포인터 위치로 원점 즉시 갱신
                                                     • 화면 튐(Jump Glitch) 원천 차단
```

### 🔒 반드시 유지해야 할 불변식 (Invariants)
1. **2계층 분리 선언 불변식 (Two-Tier Separation Invariant)**:
   * **원칙**: 다점 기하 연산 시 컨테이너 인덱싱과 속성 조회를 단일 라인에서 동시 연쇄(`points[0].x`, `points[1].x`)하는 행위를 엄격히 금지한다. (LLM의 `[1]` 토큰 증발 및 `points.x` 오타 원천 방어). 반드시 아래 3단계를 순차 준수해야 한다:
     1. `[Tier 1: 컨테이너 ➔ 독립 원소 격리 선언]`: 컬렉션/배열에서 2개의 점을 독립 단일 변수(`p1`, `p2`)로 완전히 분리 선언. 이 단계 이후 컨테이너 식별자(`points`, `touches` 등)는 폐기.
     2. `[Tier 2: 독립 원소 ➔ 4대 스칼라 추출]`: 분리된 `p1`, `p2`로부터만 4대 실수 스칼라 좌표($x_1 = p_1.x, y_1 = p_1.y, x_2 = p_2.x, y_2 = p_2.y$)를 안전하게 바인딩.
     3. `[Tier 3: 순수 스칼라 기하 유도]`: 바인딩된 실수 스칼라 변수($x_1, y_1, x_2, y_2$)만으로 거리 $d = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2}$와 중심점 $C = \left(\frac{x_1 + x_2}{2}, \frac{y_1 + y_2}{2}\right)$를 완결하여, 전 언어 런타임에서 속성 누락, `points.x`, `NaN`, `undefined`를 $0\%$로 원천 박멸.
2. **포인터 수 변경 불변식 (N <-> M Anchor Re-sync)**: 포인터 수가 $N \leftrightarrow M$으로 증감하는 순간, 누적 변환 행렬(Transform Matrix)을 동결하고 남은 포인터의 위치를 새로운 기준점(Anchor)으로 즉시 재설정하여 화면 튐(Jump Glitch)을 방어해야 한다.
4. **중심점 불변 보존 불변식 (Centroid Invariant Preservation Contract)**:
   * **수학적 계약**: 단일 포인터(마우스 휠/트랙패드) 또는 2포인터(핀치) 조작 시, 화면 상의 중심 앵커 $C(c_x, c_y)$에 놓인 월드 좌표 $W(w_x, w_y)$는 스케일이 $s_{\text{old}} \to s_{\text{new}}$로 변경된 직후에도 화면 상의 $C(c_x, c_y)$와 $0\text{px}$ 오차로 일치해야 한다.
     $$w_x = \frac{c_x - \text{pan}_x}{s_{\text{old}}}, \quad w_y = \frac{c_y - \text{pan}_y}{s_{\text{old}}}$$
     $$\text{pan}_{x,\text{new}} = c_x - w_x \times s_{\text{new}}, \quad \text{pan}_{y,\text{new}} = c_y - w_y \times s_{\text{new}}$$
   * **좌표계 분리 격리**: 변환 레이어는 반드시 `transform-origin: 0 0`을 고정해야 하며, 기본값(`50% 50%`)과의 불일치로 인한 오프셋 왜곡(Offset Drift)을 원천 금지한다.

---

## 3. [클러스터 3] 시간 임계 승격 (Temporal Threshold & Modal Escalation)

> **적용 대상**: 롱프레스 카드 드래그(DnD), 탭 vs 더블탭 분기, 홀드 녹음, 툴팁 팝오버.

### 📐 상태 전이 생애주기
```
[PRESS DOWN] ──> [TIMING ACCUMULATION (슬롭 5px 이내)]
                         │
         ┌───────────────┴───────────────┐
 (시간 도달 Δt ≥ 350ms)           (시간 전 릴리즈 Δt < 350ms)
         ▼                               ▼
[PROMOTED: MODAL DRAG]               [DISCRETE TAP EXECUTION]
 • 상위 스크롤러 즉시 차단           • 0ms 즉각 명령 실행
 • 햅틱/시각적 리프트 피드백         • 더블탭 필요 시만 분기 타이머 가동
```

### 🔒 반드시 유지해야 할 불변식 (Invariants)
1. **미세 떨림 보존 불변식**: 5px 이내의 인체 자연 손떨림(Physiological Tremor)으로 인해 롱프레스 타이머가 조기 취소되어서는 안 된다.
2. **권한 동적 확장 불변식**: 시간 임계 도달로 모달/드래그 모드에 진입한 즉시, 시스템 기본 스크롤러의 권한을 박탈하고 해당 제스처가 100% 점유하도록 소유권을 확장해야 한다.
3. **타이머 전이 단일 킬 불변식 (유령 발화 방어)**: 사용자가 시간 도달 전 손을 떼거나(`pointerup`), 시스템 취소(`pointercancel`), 슬롭 초과 이동(`pointermove`) 시 진행 중인 모든 롱프레스 타이머(`clearTimeout`)를 완벽하게 폐기하여 유령 팝업을 차단해야 한다.
4. **자식 상호작용 유예 불변식 (자식 버튼 씹힘 방어)**: 부모 컨테이너는 5~8px 이동 슬롭을 넘어서기 전까지는 포인터 캡처(`setPointerCapture`)를 독점하지 않고 자식 요소의 단일 탭/클릭 권한을 온전히 보존해야 한다.

---

## 4. [클러스터 4] 가변 뷰포트 침범 (Viewport Dynamics & Inset)

> **적용 대상**: 가상 키보드(IME) 팝업, 화면 회전, 폴더블 디스플레이 접힘, 모달 시트 높이 가변.

### 🔒 반드시 유지해야 할 불변식 (Invariants)
1. **시야 보장 불변식**: 사용자가 텍스트를 입력하는 필드는 가상 키보드나 시스템 오버레이 뒤로 가려져서는 안 되며, 항상 가용 뷰포트 중앙~상단에 노출되어야 한다.
2. **시스템 Inset 불변식**: 노치, 다이내믹 아일랜드, 홈 제스처 바 등 기기 고유의 시스템 영역과 주요 액션 버튼이 겹치지 않도록 항상 안전 여백을 확보해야 한다.

---

## 5. [클러스터 5] 이산 피드백 트리거 (Discrete Trigger & Sensory Feedback)

> **적용 대상**: 버튼 탭, 토글 스위치, 칩 필터, 비동기 확인 모달, 즐겨찾기 하트.

### 🔒 반드시 유지해야 할 불변식 (Invariants)
1. **타겟 최소 면적 불변식**: 시각적 디자인 크기와 무관하게, 손가락이 닿는 히트박스는 최소 $44 \times 44\text{dp}$ 이상이어야 한다.
2. **무지연 피드백 불변식**: 사용자가 누르는 순간($0\text{ms}$) 시각적/촉각적 반응이 즉시 나타나 "입력이 정상 접수되었음"을 인지시켜야 한다.
3. **멱등성 락 불변식 (중복 결제 방어)**: 네트워크 요청이나 무거운 비동기 작업이 진행되는 동안 중복 연타로 인한 이중 처리가 일어나지 않도록 즉시 락을 걸어야 한다.
4. **합성 클릭 관통 차단 불변식 (고스트 클릭 방어)**: 모달 닫기나 터치 액션 완료 시 `e.preventDefault()`를 선언하여 300ms 뒤 발사되는 합성 마우스 클릭이 하위 레이어 버튼을 오작동시키는 현상을 방지해야 한다.

---
---

# [참조 헌장 3] 복합 중첩 상호작용 충돌 해소 헌장 (Nested Interaction Resolution)

# 복합 중첩 상호작용 충돌 해소 헌장 (Nested Interaction Resolution)

## 0. 개요: 중첩 상호작용의 의사결정 원칙

실무 UI/UX에서는 단일 컴포넌트가 독립적으로 존재하지 않고, **스크롤 컨테이너 내부의 캐러셀, 리스트 항목 내부의 롱프레스, 바텀시트 내부의 데이터 그리드**처럼 여러 상호작용이 한 공간에 중첩(Nested)된다.

본 문서는 특정 언어의 코드가 아닌, **"복합 제스처가 경합할 때 시스템이 어떤 순서와 기준으로 권한을 승격하고 인계해야 하는가"**에 대한 보편적 아키텍처 법칙이다.

---

## 1. 3대 중첩 상호작용 충돌 해소 법칙

### 1) 시간 확전 및 이동 분기 법칙 (Temporal Escalation & Motion Preemption)
> **상황**: 하나의 리스트 항목에 [단일 탭(상세 이동)], [이동(스크롤/재정렬)], [롱프레스(컨텍스트 메뉴/다중선택)]이 모두 걸려 있을 때.

* **해소 원칙**:
  1. **1단계 (이동 선점, $\Delta d > 8\text{px}$)**: 손가락이 8px 이상 이동하면 시간 타이머를 즉시 폐기하고 **스크롤/재정렬 제스처가 100% 우선권**을 갖는다.
  2. **2단계 (슬롭 내 시간 확전, $\Delta d \le 8\text{px}$)**:
     * $\Delta t < 350\text{ms}$: 단일 탭 대기 (릴리즈 시 즉시 실행)
     * $350\text{ms} \le \Delta t < 700\text{ms}$: 1차 모달 승격 (컨텍스트 메뉴 / 미리보기)
     * $\Delta t \ge 700\text{ms}$: 2차 권한 확전 (다중 선택 모드 / 자유 재정렬 잠금 해제)
  3. **3단계 (촉각 동기화)**: 각 승격 단계에 진입하는 정확한 순간에 단계별 햅틱 피드백을 발화하여 사용자가 '현재 어떤 모드로 승격되었는지'를 인지시킨다.

---

### 2) 동적 스크롤 핸드오프 법칙 (Dynamic Boundary Hand-off)
> **상황**: 위아래로 끌어당길 수 있는 모달 바텀시트 내부에, 세로 스크롤 리스트가 포함되어 있을 때.

* **해소 원칙**:
  1. **내부 스크롤 우선권 (In-Bounds Content)**: 내부 리스트의 스크롤 위치가 최상단이 아닐 때($\text{scrollTop} > 0$), 사용자의 아래로 당기는 제스처는 **오직 내부 리스트의 스크롤에만 소비**되어야 하며 바텀시트가 내려가서는 안 된다.
  2. **경계 도달 시 소유권 인계 (Boundary Hand-off)**: 내부 리스트가 최상단($\text{scrollTop} \le 0$)에 도달한 상태에서 추가로 아래로 당길 때만, 제스처 소유권이 **'바텀시트 접기/닫기 제스처'로 자연스럽게 전이(Hand-off)**된다.
  3. **역방향 방어**: 바텀시트를 위로 끌어올리는 제스처는 바텀시트가 최대 높이에 완전히 도달(Expanded)하기 전까지 내부 리스트의 스크롤을 락(Lock)한다.

---

### 3) 직교 축 선점 및 복귀 법칙 (Orthogonal Axis Preemption)
> **상황**: 세로로 스크롤되는 피드 본문 안에 가로로 스와이프되는 이미지 캐러셀/카드 덱이 존재할 때.

* **해소 원칙**:
  1. **초기 8px 벡터 판별**: 터치 시작 후 8px 이동하는 동안의 각도 벡터($\theta$)를 측정한다.
     * $|\Delta x| > |\Delta y|$ (수평 성분 우세) ➔ **캐러셀이 100% 점유**, 세로 본문 스크롤러 차단.
     * $|\Delta y| \ge |\Delta x|$ (수직 성분 우세) ➔ **본문 스크롤러가 100% 점유**, 캐러셀 스와이프 차단.
  2. **경계 탄성 및 상위 전이**: 캐러셀이 첫 장이나 마지막 장에 도달했을 때의 추가 스와이프는 저항 계수($0.3$)를 적용한 고무줄 탄성을 보여주되, 부모 스크롤 컨테이너의 위치를 강제로 흔들지 않아야 한다.

---

### 4) 다중 인스턴스 스코프 및 이벤트 격리 법칙 (Multi-Instance Scope & Event Isolation)
> **상황**: 단일 화면에 비슷한 제스처 로직을 가진 컴포넌트가 복수 개 배치되어 있을 때 (예: 복수 캔버스/미니맵, 복수 캐러셀, 리스트 내 수십 개의 드래그 카드).

* **해소 원칙**:
  1. **인스턴스 단위 상태 캡슐화 (Zero Global Variables)**: `pointerMap`, `timer`, `velocityQueue`, `rafId` 등 모든 제스처 상태는 전역 변수가 아닌 **개별 컴포넌트 인스턴스(Class, Hook, Closure Factory, StateObject)** 내부에 100% 독립 격리하여 상태 덮어쓰기를 차단한다.
  2. **이벤트 경계 차단 (`e.stopPropagation()` & Target Capture)**: 자식 컴포넌트 조작 시작 즉시 상위 전파를 차단(`stopPropagation()`)하고 해당 요소에 포인터를 독점 캡처(`setPointerCapture`)하여 상위 캔버스/스크롤러와의 동시 발화를 원천 차단한다.
  3. **독립 관성 애니메이션 루프**: 인스턴스마다 고유한 `rafId` 채널을 관리하여 한 컴포넌트의 터치 진입이나 애니메이션 취소가 다른 컴포넌트의 관성 감속 루프를 멈추지 않도록 보증한다.

---
---

# [참조 헌장 4] 국제 표준 기반 플랫폼 & 디바이스 보편 물리 헌장 (Omni-Platform & Device Invariant Charter)

# 국제 표준 기반 플랫폼 & 디바이스 보편 물리 헌장 (Omni-Platform & Device Invariant Charter)

## 0. 개요: 국제 표준 및 인간공학(HCI) 기초

인간의 신체적 특성(손가락 면적, 미세 떨림, 반응 시간)과 입력 하드웨어(터치스크린, 스타일러스 펜, 트랙패드, 마우스)는 소프트웨어 스택과 무관한 **수학적·물리적 절대 법칙**을 형성한다.

본 헌장은 다음 국제 표준 및 인간공학 연구 자료를 기반으로 제정되었다:
* **ISO 9241-11 & ISO 9241-210**: *Ergonomics of human-system interaction — Usability & Context of Use* (사용 환경 맥락 규정)
* **ISO 9241-410 & ISO 9241-420**: *Physical input devices — Ergonomic requirements and testing methods* (입력 장치 물리적 정확도 및 슬롭 기준)
* **W3C Pointer Events Level 3 & Touch Events Extension**: 플랫폼 간 상이한 입력 장치의 통합 정규화 규약
* **Fitts's Law (피츠의 법칙, ISO 9241-9)**: 타깃 거리와 크기($W$)에 따른 인간 손가락 도달 시간 및 오발동 확률 수식 모델 ($T = a + b \log_2(2D/W)$)

`interaction-doctor`는 특정 브라우저나 자바스크립트에 국한되지 않고, **Web, React Native, Flutter, Swift/SwiftUI, Kotlin/Jetpack Compose, Electron, Unity** 등 모든 환경에서 동일하게 적용되는 포괄적 물리 계약을 제공한다.

---

## 1. 멀티 디바이스 하드웨어 특성 및 물리 제약 (Multi-Device Matrix)

### 1) 스마트폰 터치스크린 (60Hz / 90Hz / 120Hz ProMotion)
* **물리 특성 (ISO 9241-410)**: 정전식 터치 센서의 접촉 면적은 직경 7~10mm(44~48dp)에 달하며, 접촉 초기 약 3~5px의 인체 생리적 손떨림(Physiological Tremor)이 무조건 발생한다.
* **120Hz 고주사율 특성**: 8.3ms 주기로 이벤트가 쏟아지며, UI 스레드에서 메인 루프 연산이 8ms를 초과하면 즉시 프레임 드롭(Micro-stutter)이 발생한다.
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

---
---

# [참조 헌장 5] 보편 환경-물리 불변식 및 결함 인과 보증서 (Universal Invariant & Defect Guarantee Matrix)

# 보편 환경-물리 불변식 및 결함 인과 보증서 (Universal Invariant & Defect Guarantee Matrix)

## 0. 개요: 환경 기반 결정론적 인과 보증 (Deterministic Guarantee)

소프트웨어와 하드웨어의 상호작용 결함은 특정 UI 컴포넌트의 문제가 아니라, **[하드웨어 입력 해상도] × [OS 시스템 제스처 선점] × [HCI 3대 축]**의 교차점에서 발생하는 **물리적 상태 전이 실패(Failure Modes)**이다.

`interaction-doctor`는 특정 프로그래밍 언어나 변수명에 종속되지 않고, **수학적 불변식(Invariants)과 상태 전이 제약조건을 AI의 의사결정 루프에 강제 주입**함으로써, 아래의 모든 복합 결함 모드가 코드 생성 단계에서 **수학적·구조적으로 100% 원천 차단**됨을 보증한다.

---

## 1. 5대 사용 환경별 물리 실패 모드 & 보편 불변식 매트릭스

### 📱 [환경군 A] 정전식 터치 & 인체 손떨림 충돌군 (Mobile Touch Modality)
* **환경 변수**: 7~10mm 손가락 접촉 면적, 3~5px 인체 생리적 손떨림(Tremor), 60~120Hz 가변 주사율.

| ID | 사용자 체감 결함 (Failure Mode) | 근본 물리 원인 | 보편 불변식 처방 (Universal Invariants) | 수학적 / 구조적 보증 메커니즘 |
|:---:|:---|:---|:---|:---|
| **M01** | 드래그 릴리즈 시 오클릭 발화 | 8px 이하 미세 이동을 드래그로 판정 후 클릭 플래그 미폐기 | **터치 슬롭 히스테리시스 (HCI 표준)** | 포인터 변위 $\Delta d > 8.0\text{px}$ 초과 즉시 클릭/탭 이벤트를 영구 억제하여 릴리즈 오발동 차단. |
| **M02** | 롱프레스 조작 시 조기 취소 | 손가락의 1~3px 자연 손떨림을 '이동'으로 오판단 | **미세 떨림 보존 불변식 (클러스터 3)** | 변위 $\Delta d \le 5.0\text{px}$ 이내의 움직임은 시간 누적($\Delta t$)을 100% 유지하여 350ms 도달 보장. |
| **M03** | 릴리즈 후 지연된 유령 팝업 | 릴리즈/취소 시 백그라운드 타이머 미폐기 | **타이머 전이 단일 킬 (클러스터 3)** | 포인터 해제, 시스템 취소, 슬롭 초과 즉시 실행 중인 모든 롱프레스 타이머를 0ms 동기 폐기. |
| **M04** | 대각선 이동 시 축 떨림 및 덜컹거림 | 초기 이동 방향을 확정하지 않고 양방향 동시 연산 | **직교 축 선점 및 잠금 (클러스터 1)** | 초기 8px 이동 벡터 각도($|\Delta x| > |\Delta y|$)로 주 이동 축을 100% 독점 잠금하여 직교 축 간섭 차단. |
| **M05** | 고속 플릭 시 갑작스러운 급정지 | 릴리즈 직전 손가락 멈춤 순간 단일 프레임 속도 참조 | **모멘텀 궤적 큐 감속 (클러스터 1)** | 릴리즈 직전 100~120ms 동안의 이동 궤적 가중 평균 속도 벡터($\vec{v}$)를 산출하여 자연스러운 지수 감속 적용. |
| **M06** | 터치 중 재터치 시 가속 폭주 | 새 터치 진입 시 이전 애니메이션 프레임 루프 미취소 | **애니메이션 단일 소유권 (클러스터 1)** | `pointerdown` 진입 즉시 실행 중이던 모든 관성 rAF 루프를 즉시 취소(`cancelAnimationFrame`) 동결. |
| **M07** | 렌더링 직후 스크롤 시 화면 뻗음 | 컨테이너 크기 미확정 상태에서 0 나누기 발생 | **경계 분모 안전 가드 (클러스터 1)** | 모든 나눗셈 연산의 분모에 `Math.max(1, dimension)` 가드를 적용하여 `Infinity`/`NaN` 원천 방어. |
| **M08** | 모바일 브라우저 300ms 탭 굼뜸 | 더블탭 화면 확대를 대기하는 시스템 지연 | **무지연 피드백 규약 (클러스터 5)** | 조작 요소에 더블탭 줌을 비활성화하고 0ms 즉각 시각/촉각 상태 압축(Scale 0.96) 동시 발화. |
| **M09** | 좁은 타깃으로 인한 터치 씹힘 | 시각적 크기(<44dp) 그대로 히트박스 적용 | **최소 물리 타깃 보증 (ISO 9241-410)** | 시각적 렌더링 크기와 무관하게 투명 히트박스를 최소 $44 \times 44\text{dp}$ 이상으로 확장. |

---

### 🍎 [환경군 B] 시스템 제스처 & OS 윈도우 선점 충돌군 (OS & System Modality)
* **환경 변수**: iOS 20pt / Android 24dp 엣지 스와이프 제스처, macOS 트랙패드 내비게이션, 창 이탈.

| ID | 사용자 체감 결함 (Failure Mode) | 근본 물리 원인 | 보편 불변식 처방 (Universal Invariants) | 수학적 / 구조적 보증 메커니즘 |
|:---:|:---|:---|:---|:---|
| **S01** | 사이드 제스처 시 OS 뒤로가기 탈취 | 화면 가장자리 스와이프가 OS 시스템에 선점됨 | **OS 엣지 데드존 격리 (플랫폼 헌장)** | 화면 가장자리 $0 \sim 20\text{pt}$ (Android $24\text{dp}$) 영역은 시스템 제스처 영역으로 비워두고 이후부터 감지. |
| **S02** | 트랙 이탈 시 드래그 멈춤/끊김 | 포인터가 UI 바운딩 박스를 벗어났을 때 추적 상실 | **포인터 단일 소유권 구속 (클러스터 1)** | 조작 개시 즉시 이벤트 스트림을 해당 객체에 강제 바인딩(Capture)하여 창 밖 이탈 후에도 1:1 추종. |
| **S03** | 가로 스와이프 끝에서 브라우저 이탈 | 끝 도달 후 스와이프 에너지가 상위 OS로 누수 | **오버스크롤 경계 격리 (플랫폼 헌장)** | 컨테이너 경계 도달 시 수평 스크롤 체이닝을 차단하고 탄성 계수($0.3$) 고무줄 저항 적용. |
| **S04** | 드래그 조작 중 텍스트 파란색 선택 | 플랫폼 텍스트 선택/컨텍스트 메뉴 시스템 개입 | **선택 시스템 선점 억제 (플랫폼 헌장)** | 조작 진행 중 텍스트 블록 선택, 돋보기 콜아웃, 시스템 컨텍스트 메뉴 트리거를 전역 비활성화. |
| **S05** | 중첩 스크롤 시 부모 뷰 붕괴 | 자식 리스트 조작 중 부모 모달/바텀시트 동시 이동 | **동적 경계 핸드오프 법칙 (클러스터 1)** | 내부 컨텐츠가 경계($\text{offset} \le 0$)에 도달하기 전까지 부모 이동량을 $0\text{px}$로 완전 격리. |
| **S06** | 닫힌 팝업 뒷자리 요소 오클릭 | 터치 완료 후 지연 발사되는 합성 마우스 클릭 관통 | **합성 클릭 관통 차단 (클러스터 5)** | 제스처 완료 시 후속 합성 마우스 이벤트 생성을 즉시 차단하여 하위 레이어 오동작 방지. |
| **S07** | 결제/저장 버튼 중복 연타 처리 | 비동기 요청 진행 중 멱등성 락 미적용 | **비동기 멱등성 락 (클러스터 5)** | 첫 터치 릴리즈 즉시 버튼 비활성화 및 락(Debounce)을 걸어 중복 트리거 원천 차단. |

---

### 📐 [환경군 C] 가변 뷰포트 & 시스템 오버레이 침범군 (Dynamic Viewport & Insets)
* **환경 변수**: 모바일 가상 키보드(IME) 높이 급변($\Delta H$), 기기 Safe-Area Inset.

| ID | 사용자 체감 결함 (Failure Mode) | 근본 물리 원인 | 보편 불변식 처방 (Universal Invariants) | 수학적 / 구조적 보증 메커니즘 |
|:---:|:---|:---|:---|:---|
| **V01** | 가상 키보드 팝업 시 입력창 가림 | 고정 뷰포트 기준 레이아웃으로 키보드 뒤에 은폐 | **가용 뷰포트 수축 동기화 (클러스터 4)** | OS 키보드 가용 높이 감소량($\Delta H_{\text{inset}}$)을 실시간 추종하여 활성 입력 필드 하단 인셋 0ms 동기 확장. |
| **V02** | 장문 타이핑 중 커서 은폐 | 텍스트 영역 내부에서 현재 포커스 커서가 가려짐 | **활성 필드 자동 시야 확보 (클러스터 4)** | 뷰포트 수축 시 현재 캐럿(Caret) 및 활성 포커스 요소 위치를 가용 뷰포트 중앙 안전 영역으로 자동 스크롤. |
| **V03** | 노치 및 홈 제스처 바 버튼 겹침 | 기기 고유의 물리적 시스템 인셋 미반영 | **시스템 Safe Inset 보존 (클러스터 4)** | 상단 노치/다이내믹 아일랜드 및 하단 홈 바 영역에 최소 안전 패딩을 독립 뷰포트 레이어로 확보. |
| **V04** | 상단 컨텐츠 추가 시 스크롤 위치 튐 | 상단 데이터 추가로 전체 높이가 늘어나며 시선 이탈 | **스크롤 앵커 불변식 (클러스터 1)** | 추가된 컨텐츠 높이 변위($\Delta H$)를 스크롤 오프셋에 동기 가산하여 사용자의 물리적 시선 기준점 0px 보존. |

---

### 🎯 [환경군 D] 다점 기하 & 좌표 공간 변환군 (Multi-Point Geometry)
* **환경 변수**: 2손가락 핀치 줌/회전, $N \leftrightarrow M$ 포인터 수 급변, 월드-스크린 변환.

| ID | 사용자 체감 결함 (Failure Mode) | 근본 물리 원인 | 보편 불변식 처방 (Universal Invariants) | 수학적 / 구조적 보증 메커니즘 |
|:---:|:---|:---|:---|:---|
| **G01** | 핀치 줌 시 타깃 핀 화면 밖 이탈 | 고정 원점(0,0) 기준 스케일링으로 초점 위치 왜곡 | **중심점 불변 보존 수식 (클러스터 2)** | 줌 전후 화면 초점 $C(cx, cy)$ 아래의 월드 좌표 $W(wx, wy)$를 $0.000\text{px}$ 오차로 고정 역보정. |
| **G02** | 손가락 하나 뗄 때 화면 위치 팍 튐 | 포인터 수 변경($N \to 1$) 시 델타 급변 및 NaN 유입 | **포인터 수 변경 앵커 재동기화 (클러스터 2)** | 포인터 수 증감 즉시 변환 행렬을 동결하고, 남은 포인터들의 현재 위치를 새로운 기준 앵커로 즉시 재설정. |
| **G03** | 다점 거리 계산 중 화면 멈춤/에러 | 수식 내 컨테이너 인덱싱과 속성 동시 연쇄(`points[0].x`)로 인한 인덱스 증발(`points.x`) | **2계층 분리 선언 (클러스터 2)** | 컨테이너에서 2개 독립 원소(`p1, p2`)를 먼저 격리 선언 후 `p1.x, p2.x`로 스칼라를 추출하여 인덱스 누락 원천 박멸. |
| **G04** | 줌 릴리즈 시 사진이 시야 밖으로 날아감 | 과도한 관성 가속으로 가용 캔버스 영역 이탈 | **경계 탄성 및 스냅 복귀 (클러스터 2)** | 릴리즈 관성 속도에 마찰 감쇠 계수($\mu = 0.92$)를 적용하고 경계선 도달 시 탄성 복귀 바운드 제한. |

---

### 🖥️ [환경군 E] 고정밀 포인터 & 다차원 입력 기기군 (Stylus & Desktop Modality)
* **환경 변수**: 0.5mm 펜촉 vs 15mm 팜 접촉, 마우스 휠 노치 틱 vs 연속 스크롤.

| ID | 사용자 체감 결함 (Failure Mode) | 근본 물리 원인 | 보편 불변식 처방 (Universal Invariants) | 수학적 / 구조적 보증 메커니즘 |
|:---:|:---|:---|:---|:---|
| **P01** | 펜 필기 중 손바닥 오터치 선 그어짐 | 손바닥 광역 접촉을 스타일러스 드로잉으로 오인 | **Palm Rejection 15mm 폐기 (플랫폼 헌장)** | 스타일러스 활성 중 접촉 직경 $> 15\text{mm}$ 광역 터치는 손바닥으로 판정하여 즉시 드랍 폐기. |
| **P02** | 캔버스 휠 조작 시 브라우저 창 줌 | 트랙패드 2손가락 제스처와 휠 노치 미분기 | **입력 장치 식별 격리 (플랫폼 헌장)** | 핀치 줌 메타 키 신호와 일반 휠 델타를 명시적으로 분기하고 브라우저 기본 스케일링 전파 차단. |
| **P03** | 휠 노치당 스크롤 속도 제각각 | 플랫폼/OS별 라인 단위와 픽셀 단위 델타 불일치 | **델타 픽셀 정규화 (플랫폼 헌장)** | 라인/픽셀 델타 모드를 판별하여 1틱당 이동량을 물리적 픽셀($16 \sim 24\text{px}$)로 표준 정규화. |

---
---
