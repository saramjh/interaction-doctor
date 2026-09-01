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
