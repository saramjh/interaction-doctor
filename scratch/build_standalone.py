import os

base_dir = '.claude/skills/interaction-doctor'

# 1. Read SKILL.md
with open(os.path.join(base_dir, 'SKILL.md'), 'r', encoding='utf-8') as f:
    skill_content = f.read().strip()

# 2. Refactored Reference files in order (Single Source of Truth)
ref_files = [
    ('1', '보편적 UX 상호작용 계약 헌장 (Universal UX Interaction Contract)', 'references/ux-contract.md'),
    ('2', '5대 상호작용 클러스터 상태 전이 및 불변식 나침반 (Cluster Invariants)', 'references/cluster-invariants.md'),
    ('3', '복합 중첩 상호작용 충돌 해소 헌장 (Nested Interaction Resolution)', 'references/recipes.md'),
    ('4', '국제 표준 기반 플랫폼 & 디바이스 보편 물리 헌장 (Omni-Platform & Device Invariant Charter)', 'references/platform.md'),
    ('5', '보편 환경-물리 불변식 및 결함 인과 보증서 (Universal Invariant & Defect Guarantee Matrix)', 'references/guarantee-matrix.md')
]

standalone_parts = [skill_content, "\n\n---\n---\n"]

for num, title, rel_path in ref_files:
    full_path = os.path.join(base_dir, rel_path)
    if os.path.exists(full_path):
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        standalone_parts.append(f"\n# [참조 헌장 {num}] {title}\n\n{content}\n\n---\n---\n")

full_standalone = "".join(standalone_parts)

out_path = os.path.join(base_dir, 'STANDALONE.md')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(full_standalone)

print(f"Successfully compiled STANDALONE.md (Total Length: {len(full_standalone)} chars)")
