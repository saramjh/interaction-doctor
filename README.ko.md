# interaction-doctor 🩺

[ [English](README.md) ] | [ 한국어 ]

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tested on](https://img.shields.io/badge/실기기_검증-16대_하드웨어-orange.svg)](#-신뢰의-해자-16대-실기기-하드웨어-실측)
[![Blind Evaluation](https://img.shields.io/badge/블라인드_평가-3전_3승_전승-success.svg)](#-블라인드-테스트-실증-3전-전승)
[![Live Showroom](https://img.shields.io/badge/라이브_쇼룸-인터랙티브_체험하기-2563eb?style=for-the-badge&logo=googlechrome&logoColor=white)](showcase/index.html)

> **"다른 스킬은 AI가 UI를 *그리는* 것을 돕습니다. 이건 AI가 만든 UI가 사용자의 손끝에서 *네이티브 앱처럼 작동하도록* 물리 법칙을 주입합니다."**

🎮 **[👉 브라우저에서 직접 만져보는 인터랙티브 전람관 & 프롬프트 약국 (GitHub Pages)](showcase/index.html)** — *고장난 UI와 치유된 손맛을 직접 비교하고 프롬프트를 복사하세요.*

---

## 💥 혹시 이런 경험 있으신가요? (The Touch Gap)

최신 AI는 화려한 Tailwind CSS, 다크 모드, 세련된 반응형 웹을 놀라운 속도로 찍어냅니다. 하지만 **실제 스마트폰을 꺼내 손가락으로 화면을 터치하는 순간**:

- ❌ **바텀시트 덜컹거림**: 바텀시트 안의 메뉴 목록을 스크롤하려는데 바텀시트 전체가 접혀버림.
- ❌ **모바일 가상 키보드 참사**: 모바일 채팅 입력창을 터치하면 키보드가 입력창을 가려버리고, `Enter`를 누르면 줄바꿈 대신 메시지가 강제 전송됨.
- ❌ **롱프레스 오작동**: 스크롤하려는데 뜬금없이 컨텍스트 메뉴가 튀어나오고, 정작 꾹 누르고 있을 때는 아무런 반응이 없어 먹통처럼 보임.
- ❌ **멀티터치 축 요동**: 사진을 두 손가락으로 핀치 줌하거나 회전할 때 중심축이 화면 밖으로 요동침.

**왜 이런 일이 생길까요?**  
AI 모델은 CSS 문법과 DOM 속성은 잘 알지만, **실제 터치스크린의 서브픽셀 물리역학, 속도 곡선, 시간 게이트**를 한 번도 경험해보지 못했기 때문입니다.

---

## ⚡️ 초간단 설치 방법

### 1. Claude Code / Antigravity 에이전트 스킬 (권장)
```bash
# Skills.sh 원클릭 설치
npx skills add saramjh/interaction-doctor
```
```bash
# 또는 로컬 에이전트 스킬 폴더에 직접 복사
git clone https://github.com/saramjh/interaction-doctor
cp -r interaction-doctor/skills/interaction-doctor ~/.claude/skills/
```

### 2. 단일 프롬프트 주입 (ChatGPT, Claude Web, Gemini Web 등)
별도 설치나 플러그인 없이, **[`skills/interaction-doctor/STANDALONE.md`](skills/interaction-doctor/STANDALONE.md)** 파일의 내용을 통째로 복사해서 Custom Instructions(시스템 프롬프트)에 붙여넣기만 하면 100% 무손실로 물리 헌장이 활성화됩니다.

---

## 🔬 신뢰의 해자: 16대 실기기 하드웨어 실측

`interaction-doctor`의 모든 상수와 불변식은 **16대의 실제 하드웨어 기기에서 직접 측정한 원천 데이터(`research/measurements/`)**를 기반으로 설계되었습니다:

- **iOS / iPadOS**: iPhone 13 mini, 14 Pro, 15 Pro Max, iPad mini 6, iPad Pro 11", 12.9" (Apple Pencil 2 연동)
- **Android**: Galaxy S21, S23 Ultra, Z Flip 4, Pixel 7 Pro (OneUI 및 순정 Android)
- **데스크톱**: MacBook Air M3, Magic Trackpad 2, Magic Mouse, Windows 정밀 터치패드

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          핵심 물리 상수 실측치                          │
├───────────────────────┬────────────────────────────────────────────────┤
│ 8px 터치 슬롭          │ 손떨림 미세 이동과 실제 드래그/스크롤을 가르는 한계선  │
│ 350ms 시간 승격 딜레이  │ 누름 시각 피드백 후 롱프레스 모드로 승격되는 최적 타이밍 │
│ 120ms 모멘텀 윈도우     │ 손을 뗄 때 자연스러운 관성 던지기를 보장하는 속도 큐  │
│ 0ms GPU 밀착 추종      │ CSS 변수(--x, --y)를 활용한 0ms 다이렉트 트랜스폼      │
└───────────────────────┴────────────────────────────────────────────────┘
```

---

## 📊 블라인드 테스트 실증 (3전 전승)

동일한 프롬프트로 **기본 AI 세션(`without_skill`)**과 **Interaction Doctor 주입 세션(`with_skill`)**의 상호작용 품질을 블라인드 A/B 테스트로 검증했습니다:

| 테스트 시나리오 | 검증된 인터랙션 | `without_skill` (기본 세션) | `with_skill` (스킬 주입 세션) |
|---|---|---|---|
| **1. 포토 스토리 에디터** | 핀치 줌 & 2핑거 회전 | `e.touches[0]` 하드코딩 ➔ 회전 중심축 요동 | **포인터 맵 분리 & 중심점 보존으로 0ms 회전** 🏆 |
| **2. 토스/배민 바텀시트** | 20개 메뉴 스크롤 & 3단계 스냅 | 가로 카테고리 넘길 때 세로 시트가 덜컹거림 | **8px 직교 축 잠금 + 동적 경계 핸드오프** 🏆 |
| **3. 당근마켓 1:1 채팅** | 가상 키보드 & 롱프레스 | 모바일 엔터 시 강제 전송, 키보드와 서랍장 겹침 | **VisualViewport 가변 + 3단계 누름 피드백** 🏆 |

---

## 🏛️ 7대 상호작용 물리 법칙

1. **직접 조작의 법칙 (Direct Manipulation)**: 드래그/핀치 조작 중에는 `transition: none`과 CSS 변수를 써서 0ms로 손가락을 추종하고, 손을 뗐을 때만 스프링 애니메이션을 적용한다.
2. **동적 경계 핸드오프의 법칙 (Dynamic Boundary Hand-off)**: 바텀시트 내부 스크롤 시트에서는 터치 시작 시점의 `scrollTop <= 0` 여부에 따라 제스처 소유권을 동적으로 인계한다.
3. **시간 승격의 법칙 (Temporal Promotion)**: 모바일 드래그/컨텍스트 메뉴는 350ms 대기 및 누름 인지 애니메이션(`.press-holding`)을 거쳐야 하며, 8px 초과 이동 시 즉시 취소한다.
4. **직교 축 잠금의 법칙 (Orthogonal Axis Lock)**: 제스처 시작 후 최초 8px 동안 $\Delta x$와 $\Delta y$를 비교하여 우세한 축으로 즉시 잠그고 반대 축 간섭을 100% 차단한다.
5. **뷰포트 적응의 법칙 (Viewport Adaptability)**: 모바일 키보드 대응 시 고정 높이가 아닌 `interactive-widget=resizes-content` 메타태그와 `window.visualViewport` 리사이즈 이벤트를 사용한다.
6. **운동량 보존의 법칙 (Kinetic Momentum)**: 손가락을 뗄 때 직전 120ms 동안의 이동 궤적에서 속도를 계산하여 관성 스냅/던지기를 구현한다.
7. **단일 포인터 파이프라인의 법칙 (Single Pointer Pipeline)**: 마우스/터치로 코드를 이원화하지 않고 W3C 표준 `Pointer Events` 하나로 통합 처리한다.

---

## 📂 디렉토리 아키텍처

```text
interaction-doctor/
├── skills/                     # [핵심 배포 스킬 자산]
│   └── interaction-doctor/
│       ├── SKILL.md            # AI 에이전트용 점진적 로드 진입점
│       ├── STANDALONE.md       # 웹 챗봇용 1개짜리 완전체 프롬프트
│       └── references/         # 6대 세부 불변식 레퍼런스
│
├── research/                   # [원천 연구 & 신뢰의 해자]
│   ├── measurements/           # 16대 기기 하드웨어 틱 실측 원천 데이터
│   ├── conflicts/              # C1~C13 제스처 충돌 매트릭스 백과사전
│   └── ux-standards/           # 지각 파라미터 및 물리 설계 계약
│
├── showcase/                   # [실전 쇼케이스 데모]
│   ├── 01-photo-editor/        # 핀치 줌 & 로테이션
│   ├── 02-bottom-sheet/        # 3단계 스냅 & 내부 스크롤 핸드오프
│   └── 03-mobile-chat/         # 가상 키보드 대응 & 롱프레스 채팅
│
├── docs/                       # [전략 문서 및 개발 서사]
│   ├── history-and-mission.md  # 연구 히스토리 & The Touch Gap 선언문
│   ├── architecture-diagram.md # 아키텍처 구조도
│   ├── playbook.md             # 런칭 실행 플레이북
│   └── ops-manual.md           # 운용 매뉴얼
│
└── evals/                      # [평가 및 벤치마크 스위트]
```

---

## 🤝 기여하기

새로운 제스처 충돌 사례나 새로운 하드웨어 실측 데이터를 제보해 주실 분은 [`research/conflicts/CONFLICTS.md`](research/conflicts/CONFLICTS.md)를 확인하시고 언제든지 Pull Request를 열어주세요!

## 📄 라이선스

MIT © 2026 interaction-doctor contributors.
