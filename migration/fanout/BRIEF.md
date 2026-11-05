# Gap inventory fan-out: classifier brief

You are one of five parallel classifiers building the **gap inventory**
(`migration/inventory.tsv`) for a SAS 9.4 → Python 3.13 / polars port. The inventory is the
flat table that implementers grep before they translate a site. It records every place where
SAS semantics differ from what Python/polars would do by default: missing-value ordering,
SAS functions on missing or invalid input, type guessing, printed formats, PROC defaults,
output order. It is complete when every site in `migration/gap-sweep.tsv` has a row. Two
skeptic reviewers will attack every row you write, so write rows that survive them.

## Read first

1. `migration/RULEBOOK.md` (v1.1, signed off). Its canonical mappings are authoritative.
   Where a site needs something the rulebook gets wrong, write the row from the evidence
   anyway, and report the clash as a RULEBOOK CONFLICT (format below). Never edit the rulebook.
2. `migration/inventory.batch1.tsv`: 20 reviewed rows. They set the style and the evidence
   standard. Their sites are already decided. Point to them; don't re-decide them.
3. `migration/inventory-review-batch1.md`: what reviewers refuted last time. The most
   common defects were wrong line ranges and "never missing" claims proven on one input only.
4. `judge/README.md`: the judge contract (output files, columns, formats) and the findings
   about the original code.
5. Your assignment: `migration/fanout/<SHARD>.sites.tsv`.

## Sources (read-only)

- SAS programs, at the repo root: `feature_engineering.sas`, `train.sas`,
  `metrics_calculation.sas`, `predict.sas`.
- Raw inputs: `data/cs-training.csv`, `data/cs-test.csv`.
- SAS outputs of the reference run: `judge/reference/*.csv`, with the listings and logs in
  `judge/reference/listings/*.sas.{lst,log}`.
- Edge-case scenarios. Their inputs are in `judge/scenarios/<name>/` and SAS's outputs on
  them are in `judge/reference/scenarios/<name>/`:
  - `edge_predict`: MonthlyIncome = NA for test applicants under 30.
  - `edge_metrics_a`, `edge_metrics_b`, `edge_metrics_c`: synthetic risk scores with ties
    and non-zero PSI.
  - See `judge/make_scenarios.py`.
- Experiments: `migration/experiments/` (X01 one-to-one merge, X02 stepwise reference).

A program can receive the reference inputs and every edge scenario. A claim that a value is
"never missing" (`MISSING_NEVER`) must hold for **every** input the program can receive,
not only the reference run. Prove it by counting empties in the relevant CSVs, or by tracing
the code to show the value cannot be missing.

## What to do for each assigned site

Trace how the value actually flows through the code:
- where it is created;
- where it changes;
- where it escapes (into a later step, an exported CSV or a printed table).

Then decide the classification and the **exact** Python translation: a polars expression,
or the `sas_compat.*` helper the rulebook names. Cite the lines that prove it.

- One row can cover several sites when they share **one** symbol and **one** decision, such
  as a whole `if / else if` chain assigning one variable. Don't build giant rows: split by
  symbol.
- Classification is one or more of the following tokens, joined by `;`:
  - `TYPE_GUESS`
  - `MISSING_SOURCE`: missing values are created here.
  - `MISSING_NULLABLE`: an operand can be missing, so the `sas_compat` comparison helpers are
    mandatory (RULEBOOK A2).
  - `MISSING_NEVER`: never missing on every input, so plain polars comparisons are required.
  - `ROUNDING`
  - `FORMAT`
  - `ORDER`
  - `PROC_SEMANTICS`
  - `MODEL_STAT`
  - `SESSION_STATE`
  - `BUG`: reproduce the original code's defect bug-for-bug, as a `BUG(port):` item.
  - `NO_GAP`: SAS and the rulebook's default translation agree. A row is still required;
    keep it short.
  - `LISTING_ONLY`: a site inside a construct the rulebook does not port (PROC MEANS, PROC
    FREQ printed tables, PROC PRINT, PROC CONTENTS, PROC SGPLOT, `title`).
  - `UNKNOWN`
- Comparisons yield a Boolean (RULEBOOK A1). A 0/1 numeric is made only with
  `sas_compat.flag(...)`. Proportions are divided after aggregation (A7).
- SAS truthiness: `if x then` is true when x is not missing and not 0. The rule for
  division by zero is RULEBOOK §2 (`sas_compat.div`); state whether the divisor can be 0.
- **UNKNOWN rows** (you cannot decide from the evidence): status `unknown`. The translation
  must still be deterministic: the most conservative representation, then
  `TODO(port): <what is open> q: <the question the human must answer>`.

## Row format: append to `migration/inventory.<SHARD>.tsv`

The first line is exactly this header, tab-separated:

```
file	symbol	source_construct	classification	target_translation	evidence	status
```

- One row per line, 7 tab-separated fields. No tabs or newlines inside a field.
- `file`: one of the four `.sas` names.
- The evidence cites `file.sas:line` (ranges allowed: `:183-205`). It **ends with**
  `; sites S###,S###` listing the sweep sites the row decides, all in the same file as the row.
- `status`: `proposed`, or `unknown`.
- The merge deduplicates on (file, symbol, source_construct), and the last write wins. If
  you rewrite a row, append the corrected version with the same three key fields.

**Write incrementally.** Append each row as soon as it is done. The orchestrator polls your
shard's row count, and a shard that does not grow for 3 minutes is treated as stalled. Write
the rows you can decide quickly first, and do the long investigations after.

**Check often:**
`python3 migration/scripts/inventory_fanout.py check <SHARD>`. When you finish,
`... check <SHARD> --final` must report 0 errors, which means every assigned site is covered.

## Rules

- You may run Python against the data:
  `cd /Users/cristophersalvi/GitHub/sas-migration/judge && uv run python <script>`
  (polars and numpy are available). Use absolute paths. Keep scratch scripts in
  `/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/fan/<SHARD>/`.
- **Do not run SAS or saspy.** The ODA session is shared. If only a SAS experiment can settle
  a claim, write the row as `unknown`, and put an `EXPERIMENT NEEDED` item in your report.
- Write to nothing except your shard file, your `.done` marker and your scratch folder. No
  git commands that change state.
- When finished, create an empty `migration/fanout/<SHARD>.done`.

## Final report (at most 300 words, returned to the orchestrator)

1. The output of `check <SHARD> --final`.
2. The UNKNOWN rows, each with its question.
3. Each `RULEBOOK CONFLICT`: the rule (section and row), the inventory row, and the concrete
   translation that goes wrong if an implementer follows the rule.
4. Each `EXPERIMENT NEEDED`: a minimal SAS snippet, and what it decides.
5. Anything in another shard's territory that you noticed and believe is wrong.
