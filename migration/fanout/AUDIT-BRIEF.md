# Joint audit: gap inventory × rulebook (kit prompt 02)

You are an adversarial auditor. Read the **gap inventory** (`migration/inventory.tsv`,
193 rows) and the **rulebook** (`migration/RULEBOOK.md` v1.1) together, and hunt for
contradictions between them:

- **A row the rules would translate wrong.** An implementer who follows the rulebook's
  canonical mapping for a site would write code that differs from the row, or from SAS.
- **A rule no row exercises.** A §2 mapping that no site uses (dead rule), or one that no
  row confirms with evidence.
- **Rows that contradict each other.** Two rows give different translations of the same
  construct: a different helper, a different dtype, a different parameter order or file
  location.

Already known, so don't re-report these unless you find them **wrong**:
- the queued amendments A9–A18 and questions Q1/Q2 in `migration/rulebook-amendments.md`;
- experiments X01–X04 in `migration/experiments/`.

**No contradiction without an example.** Every conflict must name:
1. the rule (section and the row of the §2 table, or the amendment id);
2. the inventory row (file + symbol);
3. the **concrete translation that goes wrong**: the code an implementer would write and the
   wrong output it produces. Where you can, demonstrate it with polars against
   `judge/reference/` (run from `judge/` with `uv run python`).

## Scope

Your half of the inventory is given in your prompt. Read the whole rulebook and the queued
amendments. The batch-1 rows (`status` beginning `confirmed`, 20 rows from
`migration/inventory.batch1.tsv`) had only ONE reviewer each (deviation DEV-006). Give the
batch-1 rows in your half a full skeptic read as well.

## Output: `migration/fanout/audit.<YOUR ID>.tsv`

Header, tab-separated:

```
id	kind	rule	inventory_row	wrong_translation	proposed_fix	fix_side
```

- `kind` is one of `ROW_VS_RULE`, `DEAD_RULE`, `ROW_VS_ROW`, `BATCH1_DEFECT`.
- `fix_side` is one of:
  - `inventory`: the row is wrong;
  - `rulebook`: the rule is wrong or missing;
  - `both`.

Do not edit the inventory or the rulebook. The orchestrator applies confirmed inventory fixes
and queues rulebook changes for the human.

Keep scratch scripts in
`/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/audit/<YOUR ID>/`.
Do not run SAS.

End with a report of at most 250 words: the number of conflicts by kind and fix_side, and
the three most consequential ones.
