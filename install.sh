#!/usr/bin/env bash
# interaction-doctor 원클릭 원격 자동 설치 스크립트
# 사용법: curl -fsSL https://raw.githubusercontent.com/saramjh/interaction-doctor/main/install.sh | bash

set -e

REPO_RAW="https://raw.githubusercontent.com/saramjh/interaction-doctor/main"
SKILL_DIR=".agents/skills/interaction-doctor"
CURSOR_DIR=".cursor/rules"
WINDSURF_DIR=".windsurf/rules"
GITHUB_DIR=".github"
CLAUDE_DIR=".claude/skills/interaction-doctor"

echo "============================================================"
echo "  🩺 Interaction Doctor — 원클릭 IDE 스킬 설치기"
echo "============================================================"

# 1. Antigravity & Claude Code 스킬 디렉토리 생성 및 다운로드
mkdir -p "$SKILL_DIR/references"
echo "📦 스킬 핵심 물리 헌장 다운로드 중..."

curl -sSf "$REPO_RAW/skills/interaction-doctor/SKILL.md" -o "$SKILL_DIR/SKILL.md"
curl -sSf "$REPO_RAW/skills/interaction-doctor/STANDALONE.md" -o "$SKILL_DIR/STANDALONE.md"
curl -sSf "$REPO_RAW/skills/interaction-doctor/references/core-law.md" -o "$SKILL_DIR/references/core-law.md"
curl -sSf "$REPO_RAW/skills/interaction-doctor/references/cluster-invariants.md" -o "$SKILL_DIR/references/cluster-invariants.md"
curl -sSf "$REPO_RAW/skills/interaction-doctor/references/platform.md" -o "$SKILL_DIR/references/platform.md"
curl -sSf "$REPO_RAW/skills/interaction-doctor/references/recipes.md" -o "$SKILL_DIR/references/recipes.md"
curl -sSf "$REPO_RAW/skills/interaction-doctor/references/review-checklist.md" -o "$SKILL_DIR/references/review-checklist.md"
curl -sSf "$REPO_RAW/skills/interaction-doctor/references/diagnostic-tree.md" -o "$SKILL_DIR/references/diagnostic-tree.md"

# 2. Claude Code 연동
mkdir -p .claude/skills
ln -sf "../../$SKILL_DIR" "$CLAUDE_DIR" 2>/dev/null || cp -r "$SKILL_DIR" .claude/skills/

# 3. Cursor (.cursor/rules/interaction-doctor.mdc) 연동
mkdir -p "$CURSOR_DIR"
cp "$SKILL_DIR/STANDALONE.md" "$CURSOR_DIR/interaction-doctor.mdc"

# 4. Windsurf (.windsurf/rules/interaction-doctor.md) 연동
mkdir -p "$WINDSURF_DIR"
cp "$SKILL_DIR/STANDALONE.md" "$WINDSURF_DIR/interaction-doctor.md"

# 5. GitHub Copilot (.github/copilot-instructions.md) 연동
mkdir -p "$GITHUB_DIR"
cp "$SKILL_DIR/STANDALONE.md" "$GITHUB_DIR/copilot-instructions.md"

echo "============================================================"
echo "  ✅ 설치 완료!"
echo "  - Google Antigravity: .agents/skills/interaction-doctor"
echo "  - Claude Code:        .claude/skills/interaction-doctor"
echo "  - Cursor:             .cursor/rules/interaction-doctor.mdc"
echo "  - Windsurf:           .windsurf/rules/interaction-doctor.md"
echo "  - GitHub Copilot:     .github/copilot-instructions.md"
echo "============================================================"
