# Deviations pending human sanction

Moved into RULEBOOK.md §7 by the human when sanctioned (the rulebook is read-only to agents).

| ID | Date | Deviation | Sanctioned by |
|---|---|---|---|
| DEV-005 | 2026-11-05 | Prompt 02: inventory row 14 (stepwise) was revised a second time instead of being marked UNKNOWN after its one resubmission, because the reviewer's re-check named the single missing sentence (tie-break by MODEL order) and an implementation of the fixed rule (migration/experiments/x02_stepwise_reference.py, re-run independently by the orchestrator) reproduces SAS's 24-step path exactly | user, 2026-11-05 — moved to RULEBOOK.md §7 |
| DEV-006 | 2026-11-05 | Prompt 02 batch 1: the two skeptic reviewers took disjoint halves (rows 1–10, 11–20), so each row had ONE reviewer, not two as the kit requires ("two reviewers per batch ... neither seeing the other's verdict"). Found by the orchestrator at fan-out. Mitigation: the fan-out uses two independent reviewers on the same rows, and the joint audit reads batch 1 again with the full inventory | — (pending) |
