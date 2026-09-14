This file intentionally contains no additional instruction text.

Arm A (baseline) receives ONLY the per-case task description (see
`cases/<case-id>/task.md`) as the prompt. Nothing from this file is injected.
It exists so the harness has a symmetrical `prompts/<arm>.md` slot for all
three arms and so the "no generic/doctor instruction was added" fact is
auditable by diffing what each arm's launcher actually concatenates.
