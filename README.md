# interaction-doctor 🩺

[ English ] | [ [한국어](README.ko.md) ]

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tested on](https://img.shields.io/badge/Real_Devices-16_Hardware_Tested-orange.svg)](#-ground-truth-16-real-devices-benchmarked)
[![Blind Evaluation](https://img.shields.io/badge/Blind_Eval-3_Wins_/_0_Losses-success.svg)](#-proven-by-blind-evaluations-3-wins--0-losses)
[![Live Showroom](https://img.shields.io/badge/Live_Showroom-Try_Interactive_Demo-2563eb?style=for-the-badge&logo=googlechrome&logoColor=white)](showcase/index.html)

> **"Other skills help AI *build* UI. This one gives AI the *physics* to make it feel native."**  
> While other skills assist AI in drafting UI layouts, `interaction-doctor` injects **immutable touch physics** so that AI-generated web interfaces feel as responsive and buttery-smooth as native mobile apps with **zero jitter**.

🎮 **[👉 Try Interactive Showroom & Prompt Pharmacy (GitHub Pages)](showcase/index.html)** — *Experience the Before vs After touch difference in your browser.*

---

## 💥 Sound familiar? (The Touch Gap)

Modern LLMs generate stunning Tailwind CSS, sleek dark modes, and modern responsive layouts. But the moment you open it on a real mobile device:

- ❌ **The Bottom-Sheet Jitter**: Trying to scroll a nested 20-item menu collapses the parent bottom-sheet instead.
- ❌ **The Virtual Keyboard Disaster**: Opening a mobile chat input hides the textarea behind the on-screen keyboard, and pressing `Enter` prematurely sends the message instead of creating a newline.
- ❌ **The Unresponsive Long-Press**: Scrolling accidentally triggers context menus, while an intentional hold provides zero visual compression feedback.
- ❌ **The Multi-Pointer Chaos**: Pinch-zooming or two-finger rotating an image causes the center axis to wildly drift across the viewport.

**Why does this happen?**  
LLMs know CSS syntax and DOM properties, but they have never felt the **sub-pixel mechanics, velocity curves, and timing gates of physical touchscreens**.

---

## ⚡️ Quick Install

### 1. Claude Code / Antigravity Agent (Recommended)
```bash
# Skills.sh one-line installer
npx skills add interaction-doctor/interaction-doctor
```
```bash
# Or manual install to local agent skills
git clone https://github.com/interaction-doctor/interaction-doctor
cp -r interaction-doctor/skills/interaction-doctor ~/.claude/skills/
```

### 2. Single-Prompt Injection (ChatGPT, Claude Web, Gemini Web)
No CLI or plugin needed. Simply copy the entire contents of **[`skills/interaction-doctor/STANDALONE.md`](skills/interaction-doctor/STANDALONE.md)** into your custom instructions or system prompt. It contains 100% of the lossless physical laws in a single self-contained prompt.

---

## 🔬 Ground Truth: 16 Real Devices Benchmarked

All constants and invariants in `interaction-doctor` are derived from rigorous physical measurements on **16 real hardware devices** (`research/measurements/`):

- **iOS / iPadOS**: iPhone 13 mini, 14 Pro, 15 Pro Max, iPad mini 6, iPad Pro 11", 12.9" (with Apple Pencil 2)
- **Android**: Galaxy S21, S23 Ultra, Z Flip 4, Pixel 7 Pro (OneUI & Vanilla Android)
- **Desktop**: macOS M3, Magic Trackpad 2, Magic Mouse, Windows Precision Touchpad

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        CORE PHYSICAL CONSTANTS                         │
├───────────────────────┬────────────────────────────────────────────────┤
│ 8px Touch Slop        │ Micro-tremor threshold for tap vs scroll/drag  │
│ 350ms Hold Gate       │ Optimal temporal promotion with press-feedback │
│ 120ms Momentum Window │ Velocity sliding-window for natural flings     │
│ 0ms GPU Clamping      │ Zero-latency CSS variable direct manipulation  │
└───────────────────────┴────────────────────────────────────────────────┘
```

---

## 📊 Proven by Blind Evaluations (3 Wins / 0 Losses)

We conducted rigorous blind A/B tests comparing **Base AI (`without_skill`)** against **Interaction-Doctor AI (`with_skill`)** across 3 realistic production scenarios:

| Test Scenario | Interaction Tested | `without_skill` (Base Model) | `with_skill` (Interaction Doctor) |
|---|---|---|---|
| **1. Photo Story Editor** | Pinch-Zoom & 2-Finger Rotation | Hardcoded `e.touches[0]` ➔ Axis wildly jumps | **Map-based Multi-Pointer Isolation ➔ Smooth 0ms Transform** 🏆 |
| **2. Baemin/Toss Sheet** | 20-Item Scroll + 3-Snap Levels | Horizontal chip scrolling drags sheet vertically | **8px Axis Lock + Dynamic Boundary Hand-off** 🏆 |
| **3. Mobile 1:1 Chat** | Virtual Keyboard + Long-Press | Mobile Enter forces message send; drawer overlaps | **VisualViewport Auto-Resize + 3-Tier Press Feedback** 🏆 |

---

## 🏛️ The 7 Immutable Laws of Touch Physics

1. **Law of Direct Manipulation**: During drag/pinch, apply `transition: none` with CSS variables (`--x, --y`). Only apply spring easing upon pointer release.
2. **Law of Dynamic Boundary Hand-off**: When nesting scrollable lists inside draggable containers, delegate gesture ownership dynamically based on `scrollTop <= 0` at touch boundary.
3. **Law of Temporal Promotion**: Never start mobile drag instantly. Require $350\text{ms}$ hold with visual compression feedback (`.press-holding`), cancelled immediately if delta exceeds $8\text{px}$.
4. **Law of Orthogonal Axis Lock**: Measure initial vector ($\Delta x \text{ vs } \Delta y$) over the first $8\text{px}$. Lock exclusively to the dominant axis to eliminate cross-talk.
5. **Law of Viewport Adaptability**: Mobile keyboards must use `interactive-widget=resizes-content` + `window.visualViewport` listeners rather than fixed window heights.
6. **Law of Kinetic Momentum**: Calculate release velocity from the trailing $120\text{ms}$ touch queue to prevent sudden freeze upon release.
7. **Law of Single Pointer Pipeline**: Replace fragmented `HTML5 Drag + Touch` dual-code with unified W3C `Pointer Events` and explicit pointer mapping.

---

## 📂 Repository Architecture

```text
interaction-doctor/
├── skills/                     # [Core Skill Assets]
│   └── interaction-doctor/
│       ├── SKILL.md            # Modular on-demand router for AI agents
│       ├── STANDALONE.md       # 100% complete single-file prompt injection
│       └── references/         # In-depth physical laws & recipes
│
├── research/                   # [Research Ground Truth]
│   ├── measurements/           # Raw hardware tick data across 16 devices
│   ├── conflicts/              # Complete C1–C13 gesture conflict matrix
│   └── ux-standards/           # Perception parameters & design contracts
│
├── showcase/                   # [Live Production Showcases]
│   ├── 01-photo-editor/        # Pinch-zoom & rotation
│   ├── 02-bottom-sheet/        # 3-snap sheet with nested scroll list
│   └── 03-mobile-chat/         # VisualViewport keyboard & long-press chat
│
├── docs/                       # [Strategic Documentation]
│   ├── history-and-mission.md  # Research history & the Touch Gap manifesto
│   ├── architecture-diagram.md # Component & event architecture
│   ├── playbook.md             # Execution & launch playbook
│   └── ops-manual.md           # Operational manual
│
└── evals/                      # [Evaluation & Benchmark Suites]
```

---

## 🤝 Contributing

Contributions are welcome! If you've discovered a new gesture conflict or tested a new hardware device, please see [`research/conflicts/CONFLICTS.md`](research/conflicts/CONFLICTS.md) and submit a pull request.

## 📄 License

MIT © 2026 interaction-doctor contributors.
