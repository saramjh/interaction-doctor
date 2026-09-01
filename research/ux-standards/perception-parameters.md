# perception-parameters.md — 지각 파라미터

## 0. 이 문서가 메우는 간극

지금까지 `research/ux-standards/patterns/*.md`, `nested-interactions/*.md`,
`common-pitfalls.md` §4.5·§7이 검증한 건 전부 **"코드가 물리 법칙/
플랫폼 관행과 일치하는가"**다 — 타이머가 선언한 시간에 정확히
발동하는가, 좌표 계산이 정확한가, 멀티포인터가 격리되는가. **"사람이
실제로 이 상호작용을 편하다고 느끼는가"는 이 프로젝트가 한 번도
측정한 적이 없다.**

사용자 개개인에게 직접 물어볼 수는 없지만(이 프로젝트엔 사용성
테스트 참가자가 없다), "사람이 왜 어떤 상호작용을 편하다/불편하다고
느끼는가"에 대한 **이미 알려진 설명**(HCI 연구, 공식 접근성/디자인
표준)이 있으면, 그 이유를 측정 가능한 파라미터로 바꿀 수 있다. 이
문서는 그 파라미터들을 `ux-standards-architecture.md` §4의 라벨
체계 그대로 조사한다 — 새 방법론을 만들지 않는다.

**구조 — 3축 프레임**: 지각 가능한 문제는 사용자 액션이 시스템에
들어가는 지점(**입력**), 시스템 반응이 사용자에게 보이는 지점
(**출력**), 그 사이의 시간(**속도**) 셋 중 하나에서 생긴다. 이
문서는 이 3축으로 조사를 조직한다. §4는 이 3축에 안 들어가지만
이전 조사 라운드에서 이미 확인된 두 파라미터(기대 일치, 오류 회복)
를 지우지 않고 남겨 둔 부록이다.

**라벨 확장에 대한 정직한 표시**: §4 원문은 [표준]을 "W3C, HIG,
Material 공식 문서"로 좁게 정의한다. 아래에서 WCAG(§2)와 DOM API
(§1)는 W3C 스펙이라 이 정의를 그대로 만족하고, Material Design
3의 duration 토큰(§3)도 Material 공식 문서라 마찬가지다. 반면
Nielsen Norman Group의 응답시간 연구(§3)와 usability heuristics
(§4 부록)는 W3C/HIG/Material 어디에도 속하지 않는다 — 이 항목들은
작업 지시에 따라 [표준]으로 쓰되, §4 원래 범위를 벗어난 확장이라는
사실을 숨기지 않는다. 그 확장을 `ux-standards-architecture.md` §4
원문에 소급 반영하지는 않는다(별도 승인 필요).

---

## 1. 입력 (Input Fidelity)

**원칙**: 사용자의 액션이 의도된 기능에 정확히 전달되는가. 방해
요인(다른 요소가 가로챔, 요소가 안 보여서 클릭 불가, 다른 입력이
상태를 덮어씀)이 있으면 만족도가 급격히 하락한다.

**판정 도구**: `Element.getBoundingClientRect()` + `document.elementFromPoint(x, y)`
— **[표준]**(W3C DOM/CSSOM 스펙, §4 원래 범위 그대로 — 확장
아님). 요소의 시각적 중심 좌표에서 `elementFromPoint`가 실제로
반환하는 요소가 그 요소 자신(또는 자손)과 일치하는지 확인하면,
"사용자가 여기를 눌렀을 때 실제로 어느 요소가 이벤트를 받는가"를
추측이 아니라 코드로 정확히 판정할 수 있다:

```js
function isActuallyHittable(el) {
	const r = el.getBoundingClientRect();
	const cx = r.left + r.width / 2, cy = r.top + r.height / 2;
	const hit = document.elementFromPoint(cx, cy);
	return el === hit || el.contains(hit) || hit.contains(el);
}
```

이건 **가려짐(occlusion)으로 인한 요소 오식별**을 판정하는 도구다
— 아래에서 이 도구가 직접 겨냥하는 문제와, 겨냥하지 않는(다른
종류의) 입력 방해를 구분한다.

### 기존 사례 재해석 — "코드 결함"이 아니라 "입력 방해"였다

`common-pitfalls.md`의 규칙 1·2를 이 프레임으로 다시 읽으면, 둘 다
**"사용자의 실제 의도와 시스템이 해석한 입력이 어긋난 사건"**이라는
같은 뿌리를 갖고 있었다는 게 보인다 — 다만 어긋나는 **경로**가
서로 다르다는 것도 동시에 정직하게 구분해야 한다.

- **규칙 1(pointerdown 미확인)**: `elementFromPoint`가 판정하는
  "어느 요소인가" 문제가 아니다 — 요소 식별 자체는 맞았다. 어긋난
  건 **"액션의 종류"**다: 사용자는 아무것도 누르지 않았는데
  (호버/마우스 통과) 시스템은 "눌림"으로 해석했다. 입력 충실도의
  정의를 정확히 쪼개면 "올바른 요소가 받는가"(elementFromPoint로
  판정)와 "올바른 종류의 액션으로 해석되는가"(pointerdown 여부
  확인)는 서로 다른 하위 질문이다 — 규칙 1은 후자의 위반이다.
- **규칙 2(멀티포인터)**: 마찬가지로 "다른 요소가 가로챔"이 아니라
  **"다른 입력(두 번째 포인터)이 첫 번째 입력의 상태를 덮어써서
  가로챔"**이다 — 원칙문의 "방해 요인" 목록 중 "다른 요소가
  가로챔"의 변형("다른 입력이 가로챔")으로 정확히 해당한다.

**결론**: `elementFromPoint`류 도구는 이 두 규칙이 재현하는 결함을
직접 잡아내지 못한다(요소 식별은 원래도 맞았으므로) — 대신
**"이 요소가 지금 정말 눌려 있는 상태인가"**, **"이 상태가 지금
어느 포인터에 속하는가"**를 판정하는 별도 도구(플래그/변수 대조)
가 필요하고, 그건 이미 `common-pitfalls.md` §4.5·§7이 하고 있던
일이다 — 이 문서가 새로 추가하는 건 "가려짐으로 인한 요소
오식별"이라는, 지금까지 이 원장에 없던 **세 번째 방해 경로**다.

### evals 채점 기준 추가 검토 — "방해 발생 횟수" 기록

**[이 프로젝트의 설계 판단]**: 그레이더에 "간섭(interference)
발생 횟수"를 세는 항목을 추가할 수 있는지 검토한다 — 점수로
환산하지는 않는다(근거 없이 숫자를 만들지 않는다는 §8 원칙 그대로).
후보:

1. 시나리오의 핵심 상호작용 요소(핸들, 스와이프 아이템 등)에 대해
   위 `isActuallyHittable()`을 제스처 전/중/후 여러 시점에 호출해
   `false`가 나오는 횟수를 기록 — 가려짐 발생 횟수.
2. 규칙 1/2류 결함이 실제로 트리거되는 서브테스트가 몇 번
   실패하는지(이미 각 그레이더가 개별 pass/fail로 내고 있는 것)를
   "간섭 발생 횟수"라는 하나의 집계값으로 다시 세는 것 — 새 측정이
   아니라 기존 pass/fail 결과의 **재집계**.

**아직 구현하지 않았다** — "횟수를 기록할 수 있는지 검토"까지가
이번 지시 범위이고, 실제로 그레이더 코드에 추가하는 건 별도 승인
후 진행한다.

---

## 2. 출력 (Output Visibility)

**원칙**: 시스템의 반응이 사용자에게 실제로 보이는가. 레이어에
가려지거나 뷰포트를 벗어나 안 보이면 문제다. 단, **"의도된
오버플로우"**(드래그 중 손가락을 따라 일시적으로 화면 경계를
넘어가는 것 등)는 문제가 아니므로 반드시 구분해야 한다.

### 판정 기준 설계 — "진행 중"과 "정지" 상태를 코드로 구분

**[이 프로젝트의 설계 판단]**(외부 표준이 아니라 이 문서가 만든
운영적 정의): 가시성 판정은 **정지 상태**(제스처가 끝나고
transition/animation이 완전히 끝난 뒤)에서만 한다. 진행 중 상태
(활성 제스처 중, transform 값이 계속 바뀌는 중)는 판정 대상에서
제외한다. 구체적 절차:

1. 이 프로젝트의 코드는 이미 활성 제스처를 클래스로 표시한다
   (`.dragging`, `.lifted` 등, `demo-reorder.html`/`recipes.md`
   전반에서 재사용 중인 관행) — 판정 시점에 이 클래스가 없는지
   먼저 확인한다.
2. `pointerup`/`pointercancel` 이후 `getComputedStyle(el)
   .transitionDuration`(또는 `animationDuration`)만큼 대기해서
   전환이 실제로 끝난 뒤에 가시성을 검사한다 — 전환 도중의 스냅샷을
   "최종 상태"로 오판하지 않는다.
3. 그 시점에 `isActuallyHittable()`(§1) + 요소의
   `getBoundingClientRect()`가 뷰포트(`0 ≤ rect.left`, `rect.right
   ≤ window.innerWidth` 등) 안에 있는지를 같이 확인한다.

### 재점검 — side-drawer / bottom-sheet 코드 직접 확인

`tools/nested/side-drawer-mitigations-verify.html`,
`bottom-sheet-scroll-drag-verify.html`을 이 기준으로 다시 열어
z-index/overflow 선언을 전부 확인했다. **결함을 찾지 못했다** —
정직하게 "확인함, 문제 없음"으로 기록한다: 트리거존(`.drawer-
trigger-zone`, 우측 20px)과 `#drawer`는 둘 다 `z-index`를 명시하지
않지만, `#drawer`가 DOM에서 더 나중에 선언돼 있어 스택 순서상
트리거존 위에 정상적으로 그려진다 — 열린 드로어가 트리거존에
가려질 위험은 없다. `bottom-sheet-scroll-drag-verify.html`도
`z-index` 선언 자체가 없어 겹침 문제가 구조적으로 발생할 수 없다
(레이어가 하나뿐).

### 시각적 대비도 "출력이 보이는가"의 하위 문제다

가려짐/뷰포트 이탈은 **구조적으로 안 보임**이고, 대비 부족은
**구조적으로는 보이는데 지각적으로 구분이 안 됨**이다 — 서로 다른
경로지만 둘 다 "출력이 사용자에게 실제로 도달하는가"라는 같은
질문에 속한다.

**1차 출처**: [WCAG 2.1, SC 1.4.3 Contrast (Minimum)](https://www.w3.org/WAI/WCAG20/Understanding/contrast-minimum)(텍스트 4.5:1), [WCAG 2.1, SC 1.4.11 Non-text Contrast](https://w3c.github.io/wcag21/understanding/non-text-contrast.html)(UI 컴포넌트/그래픽 3:1). **[표준]**(W3C 공식 스펙, 확장 아님).

> "The visual presentation of text and images of text has a contrast
> ratio of at least 4.5:1" — SC 1.4.3

> "The visual presentation of the following have a contrast ratio of
> at least 3:1 against adjacent color(s): User Interface Components...
> Graphical Objects: Parts of graphics required to understand the
> content" — SC 1.4.11

핸들 아이콘은 텍스트가 아니라 그래픽이므로 SC 1.4.11(3:1)이
적용 대상이다.

**실측**(`demo/demo-reorder.html`, CSS 커스텀 프로퍼티가 고정
헥스값이라 WCAG 상대휘도 공식으로 근사 없이 정확히 계산):

| 요소 | 전경색 | 배경색 | 대비 | 기준 | 결과 |
|---|---|---|---|---|---|
| **재정렬 핸들 아이콘**(`.handle`, `var(--line)`) | `#262a33` | `#171a21` | **1.21:1** | 3:1(SC 1.4.11) | **✗ 미달**(필요치의 40%) |
| 아티스트 서브텍스트(`var(--dim)`) | `#7b8290` | `#171a21` | **4.51:1** | 4.5:1(SC 1.4.3) | ✓ 통과(여유 0.01, 아슬아슬) |
| 트랙 제목(`var(--fg)`) | `#e8eaed` | `#171a21` | **14.45:1** | 4.5:1 | ✓ 충분히 통과 |
| 헤더 제목(`var(--fg)`) | `#e8eaed` | `#0b0d12` | **16.12:1** | 4.5:1 | ✓ 충분히 통과 |

**이건 이전에 "핸들이 잘 안 보인다"고 지적됐던 부분과 직접
연결된다** — 정성적 인상이 숫자로 확인됐다: 핸들의 실제 대비는
WCAG 최소 기준의 40%다. [검증됨] 결함으로 기록한다. 수정은 이번
지시 범위 밖(조사까지)이라 기록만 남긴다.

---

## 3. 속도 (Response Latency vs Animation Duration)

**원칙**: "빠를수록 무조건 좋다"가 아니다. 반응이 **시작되는 데
걸리는 시간**(처리 시작 지연)과, 그 반응이 화면에서 **재생되는
길이**(애니메이션 재생 길이)는 서로 다른 기준을 가진 별개의
축이다 — 하나로 뭉뚱그리면 안 된다.

### 3-1. 처리 시작 지연

**1차 출처**: [Nielsen, "Response Times: The 3 Important Limits" (NN/G)](https://www.nngroup.com/articles/response-times-3-important-limits/) — 원 연구는 Miller 1968(*AFIPS Fall Joint Computer Conference* Vol. 33, 267–277)과 Card, Robertson & Mackinlay 1991(*ACM CHI'91*, 181–188)까지 거슬러 올라가며, "30년 넘게 거의 변하지 않았다"고 명시한다. **[표준]**(확장, §0 명시대로).

| 임계값 | 의미 | 원문 |
|---|---|---|
| **0.1초(100ms)** | "즉각 반응한다"고 느끼는 한계 | "the limit for having the user feel that the system is reacting instantaneously" |
| **1.0초(1000ms)** | 지연을 알아채도 사고 흐름은 안 끊기는 한계 | "the limit for the user's flow of thought to stay uninterrupted" |
| **10초** | 작업에 계속 집중할 수 있는 한계 | "the limit for keeping the user's attention focused on the dialogue" |

### 3-2. 애니메이션 재생 길이

**1차 출처**: [Material Design 3, Easing and duration](https://m3.material.io/styles/motion/easing-and-duration) — 구체적 ms 값은 Google이 같은 스펙을 구현한 [Flutter `Durations` 클래스](https://api.flutter.dev/flutter/material/Durations-class.html)로 교차 확인(1차 출처가 JS 렌더링 페이지라 자동 인출이 안 돼서, Google이 동일 스펙을 코드로 구현·공개한 문서로 대체 확인했다는 걸 명시). **[표준]**(Material 공식 문서, 확장 아님).

| 등급 | 토큰 | 값 |
|---|---|---|
| short | short1~4 | 50 / 100 / 150 / 200ms |
| medium | medium1~4 | 250 / 300 / 350 / 400ms |
| long | long1~4 | 450 / 500 / 550 / 600ms |
| extra long | extralong1~4 | 700 / 800 / 900 / 1000ms |

**🚧 미확정**: 어느 등급을 어떤 크기의 전환(작은 아이콘 상태 변화 vs
화면 전체 전환)에 써야 하는지는 이번 조사(자동 텍스트 인출)로는
찾지 못했다 — 4단계로 나눠 놨다는 사실 자체가 "상황에 따라 다른
길이가 맞다"는 걸 시사할 뿐, 정확한 매핑 기준은 확인하지 못했다.

**Apple HIG 대조** — [Apple, Human Interface Guidelines: Motion](https://developer.apple.com/design/human-interface-guidelines/foundations/motion):

> "Animations that combine brevity and precision tend to feel more
> lightweight and less intrusive, and often convey information more
> effectively."

**[표준]**(정성적 원칙만, 확장). Material과 정확히 같은 비대칭이
`reorderable-list.md`가 이미 발견했던 패턴(Android는 API 레벨 수치
공개, iOS/Google 1st-party는 정성적 문구만)과 똑같이 반복된다 —
Apple은 "brevity and precision"이라는 방향만 제시하고 정확한 ms
값을 공개하지 않는다. **구체적 숫자 비교는 여기서 [미확정]으로
남긴다** — "iOS가 Android보다 몇 ms 짧아야 한다" 같은 결론은 근거가
없다.

### 3-3. 기존 값 재분류 — "판정 시간"은 셋 중 어디에도 안 속한다

**핵심 발견**: 이 프로젝트가 이미 쓰는 500ms(롱프레스), 8px(활성화
거리)는 위 두 축(3-1, 3-2) **어느 쪽도 아니다.** NN/G의 세 임계값은
"시스템이 사용자 입력에 반응하는 지연"을 재는 것이고, Material/HIG의
재생 길이는 "전환 애니메이션이 얼마나 오래 재생되는가"를 잰다 — 500ms
대기는 둘 다 아니다. 사용자가 뭔가를 눌러 놓고 **의도적으로 판정
결과를 기다리는 시간**(제스처 확전 타이머)이라, 이 두 프레임워크
어느 것도 이 값이 맞는지 답하지 않는다. 이건 세 번째 범주다 —
그리고 이 프로젝트는 이미 이 범주를 외부 HCI 프레임워크가 아니라
**실기기 측정**(CONFLICTS.md#C6, `research/c10-sources.md`)으로
독자적으로 확보해 뒀다는 것도 재확인된다.

| 값 | 분류 | 근거/판정 |
|---|---|---|
| 500ms 롱프레스 대기 | **제스처 판정 시간**(3-1도 3-2도 아님, 별도 범주) | C6 실기기 실측(Android `contextmenu` 494–513ms) — 이 문서가 새로 다룰 축이 아니라 이미 이 프로젝트 자체 실측이 담당하는 영역 |
| 8px 이동 취소 임계값 | 위와 동일(제스처 판정 거리) | Android touch slop, `research/c10-sources.md` |
| 501.2ms(500ms 판정 직후 콜백 호출) | **처리 시작 지연**(3-1) | NN/G 100ms 기준 통과 — §1(v1 문서)에서 이미 확인 |
| 1003.1ms(1000ms 확전 직후 콜백 호출) | 처리 시작 지연(3-1) | 위와 동일 |
| `.track`/`.toggle` `transition: .18s`~`.2s`(180~200ms) | **애니메이션 재생 길이**(3-2) | M3 short3(150)~short4(200) 구간 — 우연히 토큰 범위 안 |
| 사이드드로어 슬라이드 `transition: transform .2s`(200ms) | 애니메이션 재생 길이(3-2) | M3 short4(200)와 정확히 일치 |
| 캐러셀 스냅 `transition: transform .3s`(300ms) | 애니메이션 재생 길이(3-2) | M3 medium1(250)~medium2(300) 구간 |

**정직하게 밝힌다**: 위 표의 "M3 토큰과 일치/근접"은 **우연**이다 —
이 프로젝트가 이 값들을 만들 때 Material 3 duration 토큰을 참고한
적이 없다(코드 어디에도 그런 인용이 없다). 토큰 범위 안에 들어가
있다는 사실이 "이 값들이 검증됐다"는 뜻은 아니다 — 다만 적어도
"Google이 실무적으로 적절하다고 정의한 범위 밖으로 크게 벗어나지는
않았다"는 정황 정도로만 읽는다.

---

## 4. 부록 — 3축 프레임 밖의 기존 발견 (지우지 않고 보존)

이전 조사 라운드에서 §3(속도)의 "처리 시작 지연"만 3축에 남고,
아래 둘은 입력/출력/속도 어디에도 깔끔히 들어가지 않는다. 삭제하지
않고 별도 절로 보존한다 — 3축 프레임을 확장할지는 별도 결정 사항.

### 4-1. 기대 일치 (Expectation Match)

**1차 출처**: [Nielsen, "10 Usability Heuristics" (NN/G)](https://www.nngroup.com/articles/ten-usability-heuristics/) — "Match between system and the real world", "Recognition rather than recall". **[표준]**(확장).

`patterns/reorderable-list.md`의 핸들 즉시반응 조사(Android [표준]
즉시 드래그, iOS/Google "touch and hold" 문구로 🚧 미확정)가 이미
이 범주의 실제 사례였다 — 재인용만 한다.

새로 확인한 사례: `recipes.md` 레시피 3 완화 2(엣지 스와이프
트리거존을 iOS 시스템 뒤로가기 영역인 왼쪽 대신 오른쪽으로 이동)는
물리 충돌은 피했지만(`side-drawer-back-gesture.md` §5 검증됨), 왼쪽
스와이프=메뉴 열기라는 강한 소비자 관행("Follow real-world
conventions")과는 어긋난다 — 물리적 해법이 지각적 기대를 희생한
트레이드오프였다는 걸 이 문서에서 처음 명시한다.

### 4-2. 오류 회복 용이성

**1차 출처**: [Nielsen, "10 Usability Heuristics" (NN/G)](https://www.nngroup.com/articles/ten-usability-heuristics/) — "User control and freedom". **[표준]**(확장).

> "Users often perform actions by mistake. They need a clearly
> marked 'emergency exit'..."

레시피 3 완화 3(항상 보이는 햄버거 버튼)이 이 원칙의 긍정 사례 —
제스처가 막혀도 대체 경로가 있다(이미 [검증됨]).

**새 발견**: 재정렬 리스트(레시피 4, `demo-reorder.html`, evals
01/09번) 어디에도 실행취소(undo) 경로가 없다 — 손을 떼는 순간
재정렬이 즉시 확정된다. 이건 이전의 어떤 문서(원장 §1, §7-1 포함)
에도 없던 새 발견이다. **[미확정 → 실제 결함 후보로 기록]**, 수정은
이번 범위 밖.

다중선택(evals 05번)은 "취소" 버튼으로 선택 자체는 무를 수 있다 —
다만 "선택 취소"와 "이미 커밋된 동작을 되돌리기"는 다르다는 점을
구분해 둔다.

---

## 5. 종합 — 물리 검증과 지각 검증의 관계

| 축 | 재점검한 대상 | 결과 |
|---|---|---|
| 입력 | 규칙 1·2(재해석) | "요소 오식별"이 아니라 "액션 종류/소유권 오판정" — elementFromPoint 도구가 못 잡는 결함이라는 걸 구분해서 확인 |
| 출력 — 가려짐/뷰포트 | side-drawer/bottom-sheet z-index | 점검함, 결함 없음(정직하게 기록) |
| 출력 — 대비 | `demo-reorder.html` 핸들 아이콘 | **미달**(1.21:1, 필요 3:1) — [검증됨] 결함 |
| 속도 — 처리 시작 지연 | 09번 500/1000ms 확전 콜백 | 통과(1.2ms/3.1ms) — 실기기 렌더링 지연은 🚧 |
| 속도 — 재생 길이 | 기존 transition 값들 | M3 토큰 범위 안(우연), 검증된 건 아님 |
| (부록) 기대 일치 | side-drawer 완화 2 | 물리 충돌 회피, 관행과는 상충 — 트레이드오프로 기록 |
| (부록) 오류 회복 | 재정렬 undo 부재 | **미확정 → 신규 결함 후보** |

**"물리적으로 맞다"와 "사람이 느끼기에 괜찮다"가 자동으로 같이
오지 않는다.** 7개 재점검 중 3개(출력-대비, 부록 2개)에서 물리
정확성만으로는 안 보이던 문제가 지각 기준으로 드러났다. 다음
단계(`common-pitfalls.md` §10)에서 이 둘을 같은 급으로 섞지 않는다는
원칙을 명시한다 — 이번 지시 범위는 여기까지이며, §10 추가는 별도
진행한다.

---

## 출처 전체 목록

- [Nielsen, "Response Times: The 3 Important Limits" (NN/G)](https://www.nngroup.com/articles/response-times-3-important-limits/)
- Miller, R. B. (1968). "Response time in man-computer conversational transactions." *Proc. AFIPS Fall Joint Computer Conference*, Vol. 33, 267–277. (NN/G 경유 간접 인용)
- Card, S. K., Robertson, G. G., & Mackinlay, J. D. (1991). "The information visualizer: An information workspace." *Proc. ACM CHI'91*, 181–188. (위와 동일)
- [W3C, WCAG 2.1 SC 1.4.3 Contrast (Minimum)](https://www.w3.org/WAI/WCAG20/Understanding/contrast-minimum)
- [W3C, WCAG 2.1 SC 1.4.11 Non-text Contrast](https://w3c.github.io/wcag21/understanding/non-text-contrast.html)
- [Nielsen, "10 Usability Heuristics for User Interface Design" (NN/G, 1994/2024)](https://www.nngroup.com/articles/ten-usability-heuristics/)
- [Material Design 3, Easing and duration](https://m3.material.io/styles/motion/easing-and-duration)
- [Flutter `Durations` class (Google, M3 토큰의 코드 구현체로 교차 확인)](https://api.flutter.dev/flutter/material/Durations-class.html)
- [Apple, Human Interface Guidelines — Motion](https://developer.apple.com/design/human-interface-guidelines/foundations/motion)
- MDN, [`Element.getBoundingClientRect()`](https://developer.mozilla.org/en-US/docs/Web/API/Element/getBoundingClientRect), [`Document.elementFromPoint()`](https://developer.mozilla.org/en-US/docs/Web/API/Document/elementFromPoint) (W3C CSSOM View / DOM 스펙의 브라우저 구현체)
