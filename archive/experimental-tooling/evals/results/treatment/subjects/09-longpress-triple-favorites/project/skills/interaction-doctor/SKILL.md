---
name: interaction-doctor
description: >
  모바일 웹에서 터치·포인터 인터랙션이 의도대로 동작하지 않을 때 진단하고
  수정한다. 실제로 조사·검증한 증상 언어로 트리거한다 — 드래그가 스크롤과
  충돌한다(세로 리스트를 스크롤하려는데 항목이 끌려온다, 가로 캐러셀 안에
  세로 페이지 스크롤이 같이 있다), 롱프레스가 플랫폼마다 다르게 동작한다
  (iOS Reminders는 롱프레스로 바로 재정렬되는데 iOS Photos/Files의 다중
  선택은 버튼으로만 들어가고, Android는 둘 다 롱프레스라 같은 항목에서
  재정렬·다중선택·컨텍스트메뉴 중 뭐가 열려야 할지 겹친다), 스와이프
  삭제/보관이 iOS는 끝까지 밀면 즉시 실행되고 Android는 항목 폭의 50%를
  넘겨야 확정되는 등 판정 기준이 다르다, 바텀시트 안의 스크롤 가능한
  리스트를 아래로 당기면 리스트가 아니라 시트 전체가 닫힌다, 캐러셀이
  스냅되어야 하는지 자유 스크롤이어야 하는지 헷갈린다(정답은 콘텐츠
  유형에 달렸다 — iOS/Android/CSS 스펙 모두 스펙트럼으로 지원), 탭
  전환에 좌우 스와이프를 기대했는데 iOS 표준 탭 바는 이를 지원하지 않고
  Android는 반대로 표준 패턴이다, 사이드 드로어의 엣지 스와이프가 iOS
  시스템 뒤로가기 제스처와 같은 화면 영역을 두고 겹친다. 이런 증상이
  나오거나, 위 컴포넌트(재정렬 리스트/스와이프 액션/바텀시트/캐러셀/
  다중선택/컨텍스트메뉴/탭 전환/사이드 드로어)의 모바일 터치·포인터
  기반 구현을 처음부터 새로 만들 때 사용한다. 데스크톱 마우스 우클릭
  컨텍스트 메뉴, 키보드 단축키처럼 터치/포인터 충돌이 애초에 존재하지
  않는 데스크톱 전용 구현은 이 스킬의 대상이 아니다.
---

# interaction-doctor

모바일 웹 터치·포인터 인터랙션 진단·구현 스킬. **이 스킬이 내놓는 모든
판단은 `research/ux-standards/patterns/ux-standards-architecture.md`
§1~§5.5(우선순위 5단계 → 식별 신호 → 오염 방지 → 확신도 라벨 → 자체
점검/런타임 검증 구분)와
`research/ux-standards/common-pitfalls.md`(§4.5 게이트)를 그대로
따른다.** 이 문서는 그 절차를 요약하지 않는다 — 원본 절차 문서를 직접
참조한다.

## 언제 이 스킬을 쓰는가

`description`에 적힌 증상 언어와 일치할 때. 증상 언어는 추측이 아니라
`research/ux-standards/patterns/*.md` 8개 문서와
`research/ux-standards/nested-interactions/*.md` 3개 문서의 실제
조사·검증 결과에서 그대로 가져왔다 — CONFLICTS.md의 C1~C13(터치 제스처
2자 충돌)까지 포함해 이 스킬의 진단 대상이다.

**단, C1~C13은 전부 터치/포인터 입력을 전제한다는 것을 명시한다.**
C6(LongPress ↔ Drag)이 다루는 "커스텀 메뉴와 브라우저 기본
`contextmenu`의 충돌"은 모바일 롱프레스가 `contextmenu`를 유발하는
상황(Android Chrome 494–513ms 실측, `context-menu.md` 참조)에
한정된다:

> "Desktop browsers have no long-press concept whatsoever; holding
> the mouse button for two seconds produces an ordinary `click` on
> release."
> — CONFLICTS.md#C6

이 문장이 근거다 — C6/context-menu.md가 실측하고 해소하는 건 롱프레스
타이밍(494–513ms), 경합하는 다른 제스처(드래그·재정렬·다중선택),
`touch-action`처럼 **모바일 롱프레스에만 존재하는 것들**이다. 데스크톱
우클릭에는 이 중 어느 것도 없다는 걸 C6 원문이 스스로 확인해 준다.
그래서 이 스킬은 C6/context-menu.md의 범위를 모바일 롱프레스로
한정한다 — **데스크톱 마우스 우클릭으로 여는 커스텀 컨텍스트 메뉴는
이 스킬의 대상이 아니다.** `contextmenu` 이벤트 이름은 같아도 경합할
타이밍·제스처·`touch-action` 자체가 없는 별개의(그리고 이미 사소한)
문제이기 때문이다.

## 무엇을 참조하는가

```
skills/interaction-doctor/
├── SKILL.md                 이 파일
└── references/
    ├── symptoms.md           증상 → 원인 → 수정, 확신도 라벨 포함
    ├── recipes.md            오염 방지 3유형의 실제 검증된(런타임 통과) 해소 규칙
    └── platform.md           플랫폼 상수 표 (500ms, 8px, 280dp 등) + 출처
```

증상이 `references/symptoms.md`에서 매칭되면 그 항목의 확신도 라벨을
그대로 노출한다. 라벨이 [미확정]이거나 항목 자체가 없으면 "이 부분은
아직 확신 있게 답할 수 없다"고 명시한다 — 추측으로 채우지 않는다
(architecture.md §1의 5순위, §4의 라벨 규율).

같은 항목에 여러 제스처가 겹칠 수 있는 컴포넌트(재정렬 리스트, 다중
선택, 컨텍스트 메뉴 — 전부 롱프레스 트리거를 공유할 수 있음)를 다룰
때는 `references/symptoms.md`의 상호 참조를 반드시 같이 노출한다.
하나만 답하고 나머지 겹침 정보를 누락하지 않는다.

코드 예시를 새로 작성할 때는 `references/recipes.md`에 있는, 이미
런타임 검증을 통과한 형태를 우선 재사용한다. 새 코드를 처음부터
작성해야 한다면 `common-pitfalls.md`의 §4.5 체크리스트(pointerdown
미확인, 멀티 포인터 미처리)를 통과시키기 전에는 "자체 점검 완료"라고
표시하지 않는다.

## 이 스킬이 답하지 못하는 것

- `references/symptoms.md`에 없는 컴포넌트나 조합 — 추측 대신 미조사
  상태임을 밝힌다.
- 미확정 비중이 높은 컴포넌트(예: 사이드 드로어)는 symptoms.md 본표에서
  제외돼 있다 — 별도 "🚧 조사 중" 목록을 참조하고, 확신 있게 답할 수
  없다는 걸 먼저 말한다.
- 브라우저 크롬(시스템 뒤로가기 제스처 등) 레벨의 동작은 이 스킬이
  가진 도구(Playwright)로 검증할 수 없다는 게 이미 확인돼 있다 —
  `nested-interactions/side-drawer-back-gesture.md` §5 참조.
