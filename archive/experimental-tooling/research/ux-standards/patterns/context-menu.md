# Component: Context Menu via Long Press (롱프레스로 여는 컨텍스트 메뉴)

절차는 앞선 다섯 문서와 동일: `ux-standards-architecture.md` §1(우선순위)
→ §2(식별 신호) → §4(라벨) 순서를 따른다. 검증 방법도 동일하게 **검색을
통한 1차 문서 확인**이며, 실기기 직접 관찰이 아니다.

**이 문서도 §3-2(오염 방지)와 직결된다.** 롱프레스는 이 컴포넌트뿐
아니라 reorderable-list.md("핸들 없음")와 multi-select.md(Android 소비자
앱)에서도 진입 트리거로 쓰인다. 세 문서 모두 같은 트리거를 공유할 수
있다는 점을 아래 별도 섹션에서 **표시만 하고 해소하지 않는다.**

---

## 식별 신호 (§2)

```
- 항목을 길게 누르면 항목이 살짝 확대/블러 배경과 함께 미리보기되고
  그 아래/옆에 액션 목록(공유, 복사, 삭제 등)이 뜨는 디자인 →
  컨텍스트 메뉴
- 메뉴가 뜨는 동안 배경의 다른 항목들이 흐려지거나 어두워짐 →
  iOS Context Menu API(UIContextMenuInteraction)의 전형적 시각 신호
- 길게 눌렀을 때 항목 자체가 손가락을 따라 움직이기 시작하면 →
  컨텍스트 메뉴가 아니라 reorderable-list.md 쪽. 두 반응이 헷갈리게
  섞여 있으면(짧게 누르면 메뉴, 길게 누르면 흔들리며 재배치 모드) →
  아래 "겹침" 섹션의 iOS 홈 화면 사례와 동일한 패턴일 가능성
- 길게 눌렀을 때 화면 상단에 "N개 선택됨"이 뜨면 → 컨텍스트 메뉴가
  아니라 multi-select.md 쪽
```

---

## 1. iOS — Context Menu API의 공식 트리거

> `UIContextMenuInteraction` — "Use a `UIContextMenuInteraction` object to
> focus the user's attention on a specific portion of your content, and
> to provide actions for the user to perform on that content. **A
> context menu interaction object tracks Force Touch gestures on devices
> that support 3D Touch, and long-press gestures on devices that don't
> support it.** When the appropriate gesture occurs, this object
> animates your content to a new interface and displays the contextual
> menu that you supplied."
> — [Apple Developer Documentation, `UIContextMenuInteraction`](https://developer.apple.com/documentation/uikit/uicontextmenuinteraction)

**[표준] (원문 직접 확인).** iOS의 공식 컨텍스트 메뉴 트리거는 롱프레스다
(3D Touch 지원 기기에서는 Force Touch도 대체 트리거였으나, 3D Touch는
단종된 기능이라 사실상 롱프레스가 유일한 실질 트리거).

1st-party 앱 실사례(Photos, Mail)도 동일하게 확인된다:

> "In Photos, **touch and hold** an image to preview it and see a list of
> options. In Mail, **touch and hold** a message in a mailbox to preview
> the message contents and see a list of options."
> — [Apple Support, Perform quick actions on iPhone](https://support.apple.com/guide/iphone/perform-quick-actions-iphcc8f419db/ios)

**[관성] (Apple 1st-party 앱 공식 지원 문서, 기기 미확인).**

---

## 2. Android — 컨텍스트 메뉴의 공식 트리거

> "There are two ways to provide contextual actions: In a **floating
> context menu**. A menu appears as a floating list of menu items,
> similar to a dialog, when the user performs a **touch & hold**..."
> "Register the View the context menu is associated with by calling
> `registerForContextMenu()`... Implement the `onCreateContextMenu()`
> method... **When the registered view receives a touch & hold event,
> the system calls your `onCreateContextMenu()` method.**"
> — [Android Developers, Menus — Create a contextual menu](https://developer.android.com/guide/topics/ui/menus)

**[표준] (원문 직접 확인).** Android 공식 API 문서도 "touch & hold"(롱
프레스)를 플로팅 컨텍스트 메뉴의 트리거로 명문화한다 — iOS와 동일한
트리거를 쓴다는 점에서 두 플랫폼이 일치한다.

---

## 3. 네이티브 브라우저 컨텍스트 메뉴와의 충돌 — 새 실측 아님

사용자 지정대로 새로 조사하지 않는다. Android Chrome에서 롱프레스가
네이티브 `contextmenu` 이벤트를 발생시키는 정확한 타이밍은 이미
CONFLICTS.md에 실기기로 측정되어 있다:

> [C6 — LongPress ↔ Drag](/CONFLICTS.md#c6--longpress--drag)의 실측:
> Android Chrome은 **494–513ms**에서 `contextmenu`를 발생시킨다(Verified
> on 섹션 실측치).

이 문서가 다루는 "앱이 자체 구현한 컨텍스트 메뉴"(예: React로 만든 롱
프레스 메뉴)가 네이티브 브라우저 컨텍스트 메뉴와 같은 타이밍대에서
경합한다는 사실 자체는 C6이 이미 답한 문제이므로 **연결만 하고 재측정
하지 않는다.**

---

## 겹침 — reorderable-list.md, multi-select.md와 롱프레스 트리거 공유 가능성 (해소하지 않음)

`ux-standards-architecture.md` §3(오염 방지)가 지정한 대로, 여기서도
**문제를 표시만 하고 우선순위를 정하지 않는다.**

- reorderable-list.md의 "핸들 없음"(3-B): 행 전체를 롱프레스하면
  재정렬 모드.
- multi-select.md의 Android 소비자 앱 사례: 항목을 롱프레스하면 다중
  선택 모드.
- 이 문서: 항목을 롱프레스하면 컨텍스트 메뉴.

**같은 항목에 이 세 기능이 동시에 요구되면, 같은 롱프레스가 셋 중
무엇을 열어야 하는지는 이 문서도 답하지 않는다.** 8개 문서가 끝난 뒤
오염 방지 섹션에서 다룬다.

### 사실로 기록해 두는 것 — 실제로 존재하는 두 개의 해소 사례 (일반화하지 않음)

이번 조사에서 우연히, **정확히 이 종류의 충돌을 플랫폼이 실제로 이미
겪고 해소해 둔 사례 두 개**를 발견했다. 이건 "이렇게 하면 된다"는
제안이 아니라 **관찰된 사실**이며, 8번(오염 방지) 작업 시 검토할
후보로만 남긴다 — 일반화하거나 채택을 권하지 않는다.

**사례 A — iOS 홈 화면: 시간 기반 확전(escalation) + 타겟 분리**

> "Touch and hold apps to open Quick Actions menus... **If you touch and
> hold an app for too long before choosing a quick action, all of the
> apps begin to jiggle.** Tap Done ... or press the Home button ..., then
> try again."
> — [Apple Support, Perform quick actions on iPhone](https://support.apple.com/guide/iphone/perform-quick-actions-iphcc8f419db/ios)
>
> "**Touch and hold the Home Screen background** until the items begin
> to jiggle."
> — [Apple Support, Move apps and widgets on the iPhone Home Screen](https://support.apple.com/guide/iphone/move-apps-and-widgets-on-the-home-screen-iphd2fc8ce30/ios)

관찰된 사실: 아이콘 위 롱프레스는 먼저 컨텍스트 메뉴(Quick Actions)를
연다. 사용자가 메뉴에서 아무것도 고르지 않고 계속 누르고 있으면, **그
누름이 지속된 시간이 임계값을 넘는 순간 전체 아이콘이 흔들리는
재배치(jiggle) 모드로 확전**된다 — 시간을 두 번째 판정축으로 쓴다.
동시에, 아이콘이 아니라 **빈 배경**을 롱프레스하면 메뉴 단계 없이
곧바로 재배치 모드로 들어간다 — 터치 타겟 자체를 분리하는 두 번째
전략도 같이 쓴다.

**[표준] (Apple 자사 지원 문서, 원문 직접 확인 — 단, "임계값"의 정확한
ms 수치는 이 문서에 없다, 🚧 미확정).**

**사례 B — Android Pixel 런처: 이동 여부 기반 분기**

> "Add a shortcut — **Touch and hold the app, then lift your finger. If
> the app has shortcuts, you'll get a list.**" / "Add an app — ...
> **Touch and drag the app.** You'll find images of each Home screen."
> — [Pixel Phone Help, Home screen](https://support.google.com/pixelphone/answer/2781850?hl=en)

관찰된 사실: 같은 롱프레스라도 **손가락을 뗄 때까지 움직이지 않았으면
바로가기 메뉴**, **떼기 전에 이동(드래그)했으면 앱을 옮기는 동작**으로
갈린다 — 시간이 아니라 **이동 여부/거리**를 판정축으로 쓴다. 이건 이
프로젝트가 C6/C9에서 이미 쓰고 있는 "활성화 거리(activation_distance)"
모델과 구조적으로 동일한 접근이다.

**[표준] (Google 자사 지원 문서, 원문 직접 확인 — 정확한 이동 거리
임계값은 이 문서에 없다, 🚧 미확정).**

**두 사례를 나란히 놓았을 때 드러나는 사실**: 같은 문제(롱프레스 트리거
공유)를 iOS는 **시간**으로, Android는 **이동 거리**로 푼 서로 다른
전례가 실제로 존재한다. 이 프로젝트의 매트릭스가 이미 두 축(activation_delay,
activation_distance)을 다 갖고 있다는 것과 무관하지 않은 대칭이다 — 다만
이 결론도 8번 섹션에 넘기는 정보일 뿐, 이 문서에서 어느 쪽을 채택할지
정하지 않는다.

---

## CONFLICTS.md 연결

| 시나리오 | 연결 | 비고 |
|---|---|---|
| 컨텍스트 메뉴 트리거(롱프레스) 자체의 타이밍, 네이티브 브라우저 `contextmenu`와의 경합 | [C6 — LongPress ↔ Drag](/CONFLICTS.md#c6--longpress--drag) | 재실측 없음, Android 494–513ms 실측 그대로 연결 |
| 컨텍스트 메뉴 진입 후 배경 스크롤과의 경합(메뉴가 떠 있는 동안 스크롤 가능한지) | 연결 없음 — 🚧 미확정 | C6/C10 어디에도 "메뉴가 열린 상태에서의 배경 스크롤"은 실측되어 있지 않음. 새 조합 후보 |
| 재정렬·다중 선택·컨텍스트 메뉴의 롱프레스 트리거 공유 | 연결 없음 — 오염방지(§3) 후보, 위 "겹침" 섹션 | 해소하지 않음 |

---

## 출처 전체 목록

- [Apple Developer Documentation — `UIContextMenuInteraction`](https://developer.apple.com/documentation/uikit/uicontextmenuinteraction)
- [Apple Support — Perform quick actions on iPhone](https://support.apple.com/guide/iphone/perform-quick-actions-iphcc8f419db/ios)
- [Apple Support — Move apps and widgets on the iPhone Home Screen](https://support.apple.com/guide/iphone/move-apps-and-widgets-on-the-home-screen-iphd2fc8ce30/ios)
- [Android Developers — Menus (Create a contextual menu / floating context menu)](https://developer.android.com/guide/topics/ui/menus)
- [Pixel Phone Help — Home screen (Add a shortcut / Add an app)](https://support.google.com/pixelphone/answer/2781850?hl=en)
- [C6 — LongPress ↔ Drag](/CONFLICTS.md#c6--longpress--drag) (재사용, 재실측 아님)
- 확인 시도했으나 못 찾은 것: iOS 홈 화면 확전의 정확한 ms 임계값,
  Android Pixel 런처 분기의 정확한 이동 거리 임계값, 컨텍스트 메뉴가
  열린 상태에서 배경 스크롤이 가능한지 — 전부 **🚧 미확정**으로 본문에
  개별 표시했다.

**방법론 고지**: 이전 문서들과 동일하게, [관성] 라벨은 "공식 지원 문서
검색 확인"이며 실기기 직접 관찰이 아니다. 이번 문서의 "겹침" 섹션에
인용한 두 사례(iOS 홈 화면, Android Pixel 런처)는 모두 이번 세션에서
원문 HTML을 직접 재확인했다.
