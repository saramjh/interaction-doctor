# interaction-doctor — History & Mission

> **"AI generates great-looking UI, until a real user touches it."**  
> *"Other skills help AI build UI. This one gives AI the physics to make it feel native."*

---

## 1. Problem: The Touch Gap

Large Language Models (LLMs) have achieved mastery over modern CSS, responsive Flexbox/Grid layouts, and dynamic theme switching. Visually, AI-generated web interfaces look ready for production.  
However, the moment a user **touches the screen with a physical finger**, the illusion crumbles:

- **The Bottom-Sheet Jitter**: Trying to scroll a nested list collapses the parent sheet.
- **The Virtual Keyboard Breakdown**: Focusing a mobile chat input hides the textarea behind the on-screen keyboard, while pressing `Enter` prematurely sends the message.
- **The Long-Press Ghosting**: Scrolling triggers unwanted context menus, while an intentional hold gives zero visual feedback.
- **Dual-Code Fragmentation**: Developers and LLMs maintain separate `HTML5 Drag` and `Touch` event handlers, resulting in lost events and bloated codebases.

Every existing AI frontend tool focuses exclusively on **"How to generate prettier UI (Visual Creation)"**.  
Until now, no tool provided the **"Physical Laws of Direct Manipulation (Touch Physics)"** that allow AI to craft interfaces that feel truly native.

`interaction-doctor` was created to permanently bridge this **Touch Gap**.

---

## 2. Real-Device Ground Truth (16 Hardware Devices Benchmarked)

Every constant, timing threshold, and gesture invariant in `interaction-doctor` is grounded in **raw hardware tick data collected from 16 real devices (`research/measurements/`)**, not desktop simulators:

```text
[Benchmarked Hardware Pool]
- iOS: iPhone 13 mini, iPhone 14 Pro, iPhone 15 Pro Max (iOS 16, 17, 18)
- iPadOS: iPad mini 6, iPad Pro 11", iPad Pro 12.9" (with Apple Pencil 2)
- Android: Galaxy S21, S23 Ultra, Z Flip 4, Pixel 7 Pro (OneUI & Vanilla Android)
- macOS: MacBook Air M3, Magic Trackpad 2, Magic Mouse
```

### 🔬 Key Measured Physical Invariants:
1. **8px Touch Slop**: The empirical ceiling of human involuntary micro-tremor before intentional drag or scroll begins.
2. **350ms Temporal Hold Gate**: The sweet spot for visual compression feedback before promoting a touch to a long-press/drag mode.
3. **120ms Momentum Queue**: The velocity sliding window needed to ensure natural inertia release without sudden deceleration freezing.
4. **Orthogonal Axis Lock**: Initial trajectory filtering that completely prevents cross-axis interference between horizontal carousels and vertical containers.

---

## 3. The 13 Gesture Conflict Matrix (C1 – C13)

When composite gestures coexist within a single viewport, they trigger 13 fundamental conflict states, fully documented in [`research/conflicts/CONFLICTS.md`](../research/conflicts/CONFLICTS.md):

| Conflict ID | Competing Gestures | Primary Symptom | Prescribed Physical Invariant |
|:---:|:---|:---|:---|
| **C1** | Tap ↔ DoubleTap | iOS 300ms delay & missed double-tap | Adaptive delay window branch |
| **C2** | Tap ↔ LongPress | Tapping triggers unwanted context menu | 350ms timer + 8px slop cancel |
| **C3** | Tap ↔ Drag | Instant drag leaves residual ghost states | 3px/8px slop hysteresis |
| **C6** | LongPress ↔ Drag | Mobile Kanban D&D vs page scroll | Hold-to-drag temporal promotion |
| **C10** | Drag ↔ Scroll | Nested list scroll vs sheet collapse | Dynamic boundary hand-off (`scrollTop <= 0`) |
| **C11** | Drag ↔ Pinch | Multi-touch rotation causes axis jump | Bound-safe identifier isolation |

---

## 4. Empirical Blind A/B Evaluations

We benchmarked frontier LLMs across **Base AI (`without_skill`)** and **Interaction-Doctor AI (`with_skill`)** sessions using identical natural-language prompts:

### 📊 Blind Evaluation Results (3 Wins / 0 Losses)

| Test Scenario | Interaction Tested | `without_skill` (Base Model) | `with_skill` (Interaction Doctor) |
|---|---|---|---|
| **1. Photo Story Editor** | Pinch-Zoom & 2-Finger Rotation | Hardcoded `e.touches[0]` ➔ Center axis violently jumps | **Pointer Map Isolation ➔ Butter-smooth 0ms Rotation** 🏆 |
| **2. Baemin/Toss Sheet** | 20-Item Scroll + 3-Snap Levels | Horizontal category swipe triggers vertical drag | **8px Axis Lock + Dynamic Boundary Hand-off** 🏆 |
| **3. Mobile 1:1 Chat** | Virtual Keyboard + Long-Press | Mobile Enter forces message send; drawer overlaps | **VisualViewport Auto-Resize + 3-Tier Press Feedback** 🏆 |

---

## 5. Our Mission

> **"Eliminate the tactile gap between web and native applications."**

We empower AI coding agents to generate web interfaces that feel completely frictionless, responsive, and native under the user's fingers across any hardware platform.
