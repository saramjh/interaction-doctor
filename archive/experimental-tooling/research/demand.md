# research/demand.md — W0 V1: 공개 수요 지표

**조사일**: 2026-08-29
**조사자 계정**: saramjh@gmail.com
**목적**: "모바일 웹에서 드래그·스크롤·롱프레스 제스처가 충돌한다"는 이 프로젝트의 전제가 실제로 얼마나 자주 보고되는 문제인지, 상상이 아닌 공개 데이터로 확인한다.

## 방법론

- 데이터 소스: GitHub REST Search API(`api.github.com/search/issues`), 비인증 호출.
- 각 쿼리는 `repo:<owner>/<repo> <쿼리어> is:issue` 형태로 실행. `is:issue`로 PR을 제외하고 이슈만 집계.
- 여러 단어로 된 쿼리(`scroll conflict`, `mobile drag`, `drag not working mobile`)는 **따옴표 없이** 검색 — GitHub 검색창에 그대로 타이핑했을 때와 동일하게, 각 단어를 모두 포함하는 이슈를 찾는 AND 매칭이며 구문(phrase) 일치가 아니다. (`"scroll conflict"`로 구문 검색하면 dnd-kit 기준 0건, AND 매칭으로는 2건 — 실제로 확인함.)
- "최근 1년" = `created:>=2025-08-29` (기준일 2026-08-29로부터 정확히 1년 전).
- 대표 이슈 3개는 저장소별로 각 쿼리 결과를 종합해 실제로 "터치/스크롤/드래그 제스처 충돌"을 설명하는 이슈 중 사람이 직접 골랐다(참여도 — 댓글·리액션 수를 참고). 기계적 최상위 랭킹이 아님을 밝혀둔다.

## 1. 저장소 × 쿼리별 히트 수

### clauderic/dnd-kit

| 쿼리                    | 히트(전체 기간) | 최근 1년      |
| ----------------------- | --------------- | ------------- |
| touch-action            | 10              | 1             |
| scroll conflict         | 2               | 0             |
| mobile drag             | 27              | 4             |
| pointercancel           | 0               | 0             |
| drag not working mobile | 10              | 0             |
| **소계**                | **49**          | **5 (10.2%)** |

### motiondivision/motion

| 쿼리                    | 히트(전체 기간) | 최근 1년     |
| ----------------------- | --------------- | ------------ |
| touch-action            | 13              | 0            |
| scroll conflict         | 1               | 0            |
| mobile drag             | 26              | 0            |
| pointercancel           | 2               | 0            |
| drag not working mobile | 11              | 0            |
| **소계**                | **53**          | **0 (0.0%)** |

### davidjerleke/embla-carousel

| 쿼리                    | 히트(전체 기간) | 최근 1년     |
| ----------------------- | --------------- | ------------ |
| touch-action            | 7               | 0            |
| scroll conflict         | 4               | 1            |
| mobile drag             | 21              | 0            |
| pointercancel           | 0               | 0            |
| drag not working mobile | 11              | 0            |
| **소계**                | **43**          | **1 (2.3%)** |

### emilkowalski/vaul

| 쿼리                    | 히트(전체 기간) | 최근 1년     |
| ----------------------- | --------------- | ------------ |
| touch-action            | 4               | 1            |
| scroll conflict         | 0               | 0            |
| mobile drag             | 13              | 0            |
| pointercancel           | 2               | 0            |
| drag not working mobile | 4               | 0            |
| **소계**                | **23**          | **1 (4.3%)** |

## 2. 총 히트 수

|                     | 전체 기간 | 최근 1년     |
| ------------------- | --------- | ------------ |
| **4개 저장소 합계** | **168**   | **7 (4.2%)** |

쿼리별 합계(4개 저장소):

| 쿼리                    | 전체 기간 | 최근 1년 |
| ----------------------- | --------- | -------- |
| touch-action            | 34        | 2        |
| scroll conflict         | 7         | 1        |
| mobile drag             | 87        | 4        |
| pointercancel           | 4         | 0        |
| drag not working mobile | 36        | 0        |

**판정 (playbook 기준: ≥200 실재/진행, 50~200 진행하되 주니어 타겟으로 좁힘, <50 중단)**: 168건 → **50~200 구간. 진행하되 타겟을 좁혀야 함.** 다만 최근 1년 비중이 4.2%로 매우 낮다는 점은 아래 3번 한계 항목에서 반드시 감안할 것.

## 3. 저장소별 대표 이슈 3개 (원문 인용)

증상을 사용자가 실제로 어떤 언어로 표현했는지 원문(영문) 그대로 인용. `symptoms.md` 작성 시 이 표현을 그대로 재사용할 것.

### clauderic/dnd-kit

1. **[Draggable Touch Events only working on Long Press](https://github.com/clauderic/dnd-kit/issues/1398)** (#1398)

   > "my Draggable elements are only activating on Long Press. Any idea why this is? I would like the Drag event to fire with as minimal delay as possible and be highly sensitive."

2. **[Dragging doesn't work on touch devices with delay activation constraint and touch action auto](https://github.com/clauderic/dnd-kit/issues/453)** (#453)

   > "when I touch and hold a draggable, it gets "stuck" and cannot move anymore... If I have touch action set to none, then I am able to drag the draggable around, but the list doesn't scroll normally anymore... It's impossible to scroll the actual container on a touch device. You can only drag and drop the items."

3. **[Drag interaction does not work on some Android devices (works on iOS)](https://github.com/clauderic/dnd-kit/issues/1955)** (#1955)
   > "On affected Android devices users cannot initiate dragging at all — touch gestures are ignored or interpreted as scroll. This makes sortable lists unusable on part of the mobile audience."

### motiondivision/motion

1. **[[BUG] Stop scrolling from interfering with dragging](https://github.com/motiondivision/motion/issues/185)** (#185)

   > "If you render a list of `drag=\"x\"` components and try to scroll down on a touch device, a small amount of horizontal drag happens on each element that your finger touches."

2. **[[BUG] Reorder on mobile doesn't differentiate scroll from drag](https://github.com/motiondivision/motion/issues/1506)** (#1506)

   > "it interprets my finger's _scroll input_ with a _drag input_... The expected behaviour is that I'm able to scroll down. Instead, I initiate an item drag... it would be great if the interface understood the natural difference between a drag and a scroll"

3. **[Support e.preventDefault() and e.stopPropagation() in tap/drag events](https://github.com/motiondivision/motion/issues/363)** (#363)
   > "In my app I have `<Link>` elements inside a draggable `<motion.div>` element. When the user clicks those, I don't want the drag/`whileTap` styles to activate... the `onMouseDown` event is never fired at all on any of the childs of the draggable element."

### davidjerleke/embla-carousel

1. **[Passive event listeners](https://github.com/davidjerleke/embla-carousel/issues/62)** (#62)

   > "I'm getting some jank on mobile with a slider (3 full width image slides + some HTML)... I have a client that is adamant about the Google Lighthouse scores... This is the only thing I'm getting dinged for in best practices category."

2. **[Prevent click event on child element when dragging](https://github.com/davidjerleke/embla-carousel/issues/24)** (#24)

   > "I created a carousel and added my custom clickable elements inside. The problem is when I drag the carousel and then I mouseup, click event is triggered which is not the desired action."

3. **[[Feat]: Ability to lock scroll if all slides in view](https://github.com/davidjerleke/embla-carousel/issues/320)** (#320)
   > "Is it possible to lock scroll or check if all slides shown completely?" / 이후 명확화: "An option that disables the carousel entirely if all scroll snaps/slides are in view (aren't enough to fill the viewport)."

### emilkowalski/vaul

1. **[Allowing scroll within the drawer introduces unreliable dragging on mobile](https://github.com/emilkowalski/vaul/issues/358)** (#358)

   > "frantic and/or diagonal movements will start dragging the drawer, but only for a small bit, without moving back to it's proper position after letting go of the touch... A similar issue can be experienced on vertical drawers, by simply swiping up and down."

2. **[iOS: Drag to close does not work after scrolling back up in overflowing content](https://github.com/emilkowalski/vaul/issues/153)** (#153)

   > "when you try to drag close on iOS after you scroll down and back up to the top of an overflowing content container it does not close. Most of the time a second drag is working, sometimes it gets completely stuck"

3. **[Pointer cancel event is not handled on iOS when opening the system's dock over the drawer](https://github.com/emilkowalski/vaul/issues/555)** (#555)
   > "it will begin dragging, but suddenly stop when the dock opens and the `pointercancel` event is called, at which point the drawer remains "stuck" in between snap points."

## 4. 한계 및 주의사항 (추정 아님, 관찰된 사실만)

- **AND 매칭의 노이즈**: `mobile drag`, `drag not working mobile`처럼 흔한 단어 조합은 무관한 이슈까지 다수 포함한다. 예를 들어 `mobile drag` 쿼리 결과 상위 샘플 중 dnd-kit의 "Resize - is it possible?"(#1127), embla-carousel의 "Create an option to block excessive scrolling"(#42) 같은 항목은 제스처 충돌과 직접 관련이 없었다(실제로 결과 목록을 열어 확인함). 즉 위 히트 수는 "관련 있을 가능성이 있는 이슈"의 상한선이지, 정확히 필터링된 수치가 아니다.
- **최근 1년 비중이 낮은 이유는 확인 불가**: 4개 저장소 합계 기준 최근 1년 비중은 4.2%(168건 중 7건)로 매우 낮다. 이것이 (a) 문제가 실제로 줄었기 때문인지, (b) 라이브러리가 성숙해 issue tracker보다 Discord/Discussions로 이동했기 때문인지, (c) 최근 이슈들이 이번 조사에 쓴 5개 쿼리어와 다른 표현을 쓰기 때문인지는 이번 조사로는 판단할 수 없다. 확인 불가로 남긴다.
- **Stack Overflow 등 다른 소스는 조사하지 않음**: 이번 조사 범위는 사용자가 지정한 GitHub Issues 4개 저장소로 한정했다. playbook에 언급된 Stack Overflow 질문 수는 이 문서에 포함하지 않았다 — 확인 불가.
- **대표 이슈 선정은 완전 자동 랭킹이 아님**: GitHub 검색 API의 best-match 정렬 결과 중 사람이 주제 적합성과 참여도(댓글·리액션)를 보고 선택했다. 다른 사람이 고르면 다른 3개가 나올 수 있다.
- **모집단 한계**: 이 조사는 성숙한 라이브러리의 이슈 트래커를
  측정했다. 이 프로젝트의 대상은 라이브러리를 쓰지 않고
  에이전트가 직접 짠 코드를 쓰는 사용자이며, 그들은 공개된
  흔적을 남기지 않는다. 168건은 문제의 난이도를 보여주는
  증거이지, 대상 사용자 수요의 직접 측정이 아니다.
