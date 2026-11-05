# Gap inventory fan-out: skeptic reviewer brief

You are a **skeptic reviewer** of gap-inventory rows for a SAS 9.4 → Python 3.13 / polars
port. A second reviewer is checking the same rows independently, and neither of you sees the
other's verdicts. Your job is to break rows, not to approve them. Last time, reviewers found
evidence defects in 9 of 20 rows and refuted 2 outright (`migration/inventory-review-batch1.md`).

## Context (read first)

- `migration/fanout/BRIEF.md`: what the classifiers were told, the row format and the
  classification vocabulary.
- `migration/RULEBOOK.md` (v1.1): the canonical mappings.
- `judge/README.md`: the judge contract and the findings about the original code.
- Sources:
  - SAS programs at the repo root;
  - `data/` (raw inputs);
  - `judge/reference/` (SAS outputs and `listings/*.lst|.log`);
  - `judge/scenarios/` and `judge/reference/scenarios/` (edge-case inputs and SAS's outputs
    on them).

## For every row in your batch

Check that the row is right on all of these:
1. **Lines.** The cited `file.sas:line` ranges say what the row claims. Open them.
2. **Sites.** Every site in `; sites S...` (see `migration/gap-sweep.tsv`) is really
   decided by this row. No site in the batch is left without a row.
3. **Missing values.** A `MISSING_NEVER` claim holds on every input the program can
   receive, edge scenarios included. A `MISSING_NULLABLE` row uses the `sas_compat` helpers.
4. **Translation.** It reproduces SAS. Recompute it with polars against the reference or
   scenario CSVs when the claim is checkable. This is the strongest evidence.
5. **Rulebook.** The translation is consistent with the rulebook. If it isn't, which one is
   wrong?
6. **Completeness.** An implementer could port the site from the row alone, with nothing
   left to choose.

You may run Python:
`cd /Users/cristophersalvi/GitHub/sas-migration/judge && uv run python <script>`
(polars and numpy are available). Keep scratch scripts in your own folder:
`/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/review/<YOUR ID>/`.

Rules:
- Do not run SAS or saspy.
- Do not edit any inventory file. Write only your verdict file and your scratch folder.

## Verdict file: `migration/fanout/review.<YOUR ID>.tsv`

Header, tab-separated:
```
file	symbol	source_construct	verdict	cited_line	reason
```

- The first three fields copy the row's key exactly.
- `verdict` is one of:
  - `CONFIRMED`
  - `EVIDENCE_DEFECT`: the translation is right but the evidence is wrong or incomplete.
  - `REFUTED`: the translation is wrong.
  - `RULEBOOK_CONFLICT`: the row is right and the rulebook would translate the site wrong.
- `cited_line` (required): the `file.sas:line`, or the CSV file and cell, that justifies
  your call.
- `reason`: one or two sentences. A REFUTED or EVIDENCE_DEFECT verdict must say concretely
  what is wrong and what the fix is.

Append verdicts as you go. Give one verdict per row, in any order, and cover every row in
your batch. End with a final report of at most 250 words:
- the verdict counts;
- the REFUTED rows, one line each;
- any site of the batch you found with no row.
