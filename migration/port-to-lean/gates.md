# Gates — what a sign-off would have reviewed

Gates are run through without stopping (PROMPT.md); each entry records the evidence a sign-off
would have looked at.

## Gate 0 — foundation visible, blueprint created (2026-11-10)
- `grep Tabular.RealLike` from `py-credit-risk-port` finds `Tabular.RealLike`, `.abs`, `.eqb`
  (17 `Tabular.*` declarations visible). Blueprint id b41b22d4-720d-4290-b593-39ceab961986,
  language python, trust layers default (Judging).
- `index_codebase` on `credit_risk/`: 6 files, 83 items, 0 cycles, 0 parse errors.
- `add_code_targets` created 36 items; `FloatArray` clashes with Lean's built-in `FloatArray`
  and was added by hand as `def:FloatArray_` with its 7 dependents and `_into_float`.

## Gate 1 — map and rules (2026-11-10)
- Dependency map: the blueprint graph (index_codebase); manifest `migration/manifest.tsv`.
- Rulebook `migration/RULEBOOK.md`; library rules backed by experiments
  `migration/experiments/e01..e06` and the polars py-2.1.0 / numpy v2.5.4 source.
- Design decisions a sign-off would review:
  1. The server's judge rejected a "value at one row" model of `pl.Expr` (the union
     `ExprOrNum` must keep its three alternatives). Expressions are therefore a Lean type
     `Pl.Expr` (evaluation on a frame, with or without groups; output name; serialization
     skeleton), and polars/numpy semantics are stated once in two preludes housed in
     `def:ExprOrNum` and `def:FloatArray_` (DEV-005).
  2. R-F2I: the foundation has no `α → Int`, so floats converted to integers stay in `α`
     (DEV-004). Affects proc_rank_groups, proc_rank_apply_groups, _hl_groups, hosmer_lemeshow,
     classification_table.
  3. Float summation orders are encoded, not abstracted: select-context sum (block pairwise),
     group-context sum/mean (Kahan), numpy pairwise. The only thread-dependent behaviour found
     (`sum_horizontal` with 5 operands) is the explicit Boolean parameter `full`.

## Gate 1b — judge and inventory (2026-11-10)
- Judge = differential evaluation harness `migration/diffeval/` (README). Comparer validated on
  44 planted pairs, 0 wrong verdicts (`receipts/comparer_validation.tsv`).
- Prelude attack: 567 case-primitive pairs (`receipts/prelude.tsv`): summation orders, Kahan
  group sums, median formula, rank, sort / join / group semantics, rayon shapes all bit-exact;
  11 difference classes D1–D11, each resolved in amendment batch 1 (fixed: D2, D3, D10; recorded
  limits: D1, D7, D11; scope restrictions: D4–D6, D8, D9).
- Inventory `migration/inventory.tsv`: 1383 rows over 1376 swept sites
  (`inventory.sites.txt`), 11 UNKNOWN rows (7 questions), all answered by amendments A7–A12.
  Deviation: the two-skeptic review of inventory rows was not run (DEV-006).

## Gate 2 — stress test (2026-11-10)
- Selection: `lt`/`gt`/`flag` (null logic, naming), `sas_round` (dtype casts, horizontal max,
  sign, `+ 0.0`), `confusion_metrics` (frames, group/sort order, Int vs Float64, null guards).
- Pilot (production pipeline, rulebook v1): 9 units accepted; adherence finding: the implementer
  followed the rulebook where it was wrong (`+ 0.0`), and reported it instead of patching.
- Bakeoff: native translator B (no rulebook) vs pilot A; diff report
  `migration/stress-test/bakeoff_diff.md`.
- Amendment queue: `migration/amendments.md` batch 1 (A1–A14), applied by the orchestrator in
  place of the human gate (DEV-003). The re-round is folded into the production run of bundle
  B1 under rulebook v2 (same units re-submitted), DEV-007.

## Gate 3 — translation (2026-11-10)
- Queue: `migration/manifest.tsv`, 90 code items (B0 3, B1 14, B2 10, B3 4, B4 7, B5 6, B6 12,
  B7 7, B8 9, B9 18), all `DefinitionFormalized`; 55 precondition items; `get_status`: 146/146.
- Pipeline per bundle: implementer -> adversarial reviewers (separate contexts, read-only) ->
  orchestrator verdict (`reviews/verdicts.md`) -> fixer on confirmed findings only
  (`reviews/*_confirmed.md`). Reports: `reviews/B1_r1.md` … `B9_r2.md`, `RUNS_r2.md`.
- What the reviews bought: no defect in any unit's code on inputs inside its precondition after
  fixes; 1 defect class fixed by precondition (negative k in `proc_rank_apply_groups`, found
  independently by both B3 reviewers), precondition gaps fixed in B3, B5, B7, B8, B9
  (unbounded sums kept in α, join suffix clash, text `median_income`, shapes of the fits).
- Rulebook: v1 -> v4 in three amendment batches (`amendments.md`, 14 + 14 + 3 items); recurring
  failures moved upstream each time (scalar-zero addition, Null dtype, R-DIV0, pow2, precondition
  wording). Preludes amended once (batch 1) and frozen after B2.
- Deviations: RULEBOOK §7 (DEV-001 … DEV-012).

## Gate 4 — differential evaluation (2026-11-10)
- Receipts: `diffeval/receipts/comparer_validation.tsv` (74 planted pairs, 0 wrong verdicts),
  `receipts/prelude.tsv` (preludes), `receipts/units.tsv` (every unit, implementers' and
  reviewers' suites), generators `diffeval/units/*_gen.py`, raw inputs/outputs `diffeval/work/`.
- Differences found and how each was resolved: see the final report and `reviews/verdicts.md`.
  Unexplained differences: zero.

## Freeze (2026-11-10) — STOP
- `get_status`: 146 items, 146 statements formalized, nothing to write, nothing waiting.
  90 code items (manifest) + 55 preconditions + the harness item `def:zz_carrier` (identity on
  `List Int`, depends on every unit; kept so the receipts can be re-run; removable with one
  `remove_item` call, nothing depends on it).
- Unit receipt `diffeval/receipts/units.tsv`: 111 rows, 7,795 cases, 42 differences, all in
  KNOWN-DIFF rows (30 recorded prelude limits in B2, 3 `_is_scalar`, 1 `merge_one_to_one`,
  8 = one `exp` last-bit value). Prelude receipt `receipts/prelude.tsv`: 154 rows, 774
  case-primitive pairs, 122 PASS, 32 KNOWN-LIMIT. Every manifest unit has a row.
- From here the statements must not change.

## Post-freeze decisions by the user (2026-11-11)

- R-F2I (DEV-004): accepted as it is. No foundation change, nothing flagged in the Python.
- Date cell (`today : Tabular.Cell α`): accepted as it is.
- Zero-row `printed_odds_ratios.csv`: excluded by precondition. `def:run_py_py_py_precond` now
  requires `final_effects ≠ []` (narrowing, commented). No definition changed, no dependent cleared.
- `full`: kept as a parameter.
- `def:zz_carrier`: to be removed (user decision).
- `model.json` as second component of `train.run`, and `medians` before `cs_test` in
  `def:run_py_py` (DEV-011): accepted as they are.
- Reviews: a second adversarial reviewer for B2 is to be run (closes DEV-009); the inventory skeptic
  round stays skipped (DEV-006 accepted).
- Judge: switched off at the user's explicit request (`trust_layers = []`) after all items had been
  accepted with Judging on. Later edits are compiled only.
- Second B2 review (`reviews/B2_r2.md`): unit texts faithful. F1 (sorted-flag group key) and F2
  (1-ulp `exp`/`log` in the evaluator) recorded as limits (RULEBOOK §6, amendments batch 5); F3
  fixed by precondition at the user's decision: `def:sas_sum_precond` now requires at most 8
  operands; F4 waived (DEV-010).
- `def:zz_carrier` removed. To re-run the receipts, re-add it from `diffeval/carrier.py`.

## Final state (2026-11-11)

145 items, 145 statements formalized (90 code items, 55 preconditions), verification approved.
Trust layers: none (judge off at the user's request, after acceptance under Judging).

## Re-translation after commit 7927af7 (2026-11-12)

Connector: Logos MCP Staging (the local server is discontinued). Units re-translated and accepted:
`_TIE_EPS` (exact value), `_ROUND_FUZZ_CAP` (renamed from `_TWO52`), `sas_round`, `merge_one_to_one`
(+ precondition), `_pairs`, fe steps 02/03/05, predict steps 02/03/05, train steps 09/11, metrics
steps 05/06 (+ `metrics_run_06_psi_precond`). 22 cleared dependent `def:` items restored (unchanged
Lean; line comments shifted for train.py). Source ranges updated on 27 items. Receipt:
`diffeval/receipts/units_7927af7.tsv` (809 cases, 35 differences, all outside preconditions).
Rulebook amendments: batch 6. Harness items `def:zz_carrier_p/_f/_t` added and removed.

## Update after the verification round (2026-11-16)

Plan: `update-after-verification.md`. Baseline of the comparison: the Python source stored in each
blueprint item, against `port/credit_risk` on disk (this role reads no commit history).

Decisions by the lead (2026-11-16):
1. A stopped run is `none`; a completed run is `some files` (`Option`).
2. A failed import or an absent file is an `Option` parameter; the stop is inside the function.
3. The foundation is not changed. A test file with a header and no applicant is valid input
   (ruling G44) and is defined: the import parameter of predict delivers the column names and the
   rows separately. Empty training scores in metrics are not valid input: excluded by precondition,
   stated in the item text.
4. The raw-bytes header probe of predict (:42-63) is part of the import parameter; the item text
   says what the parameter stands for.
5. `grep` only on this blueprint's `def:` code and precondition items; no translator opens a theorem.

T0 done 2026-11-16: RULEBOOK v5 (§2.7; batch 7 in `amendments.md`), experiment E07
(`experiments/e07_batch7.py`, output beside it), five carrier items
(`def:zz_carrier_s/_f/_p/_m/_t`) accepted. Open for the lead: DEV-013 (predict result as triples).

T20 done 2026-11-16 (closing check of the update; scripts and outputs under `diffeval/`):
- Stored source against the port, by script (`diffeval/stored_source_check.py`, output
  `diffeval/work/stored_source_check.out.txt`; the stored texts are under `diffeval/work/stored/`):
  30 changed or added code items; 29 are the text of the file line for line (no difference, not even
  in a comment). `def:run_py_py_py` could not be compared: `get_items` refuses its `code` field
  (37,620 bytes, limit 30,720).
- Suites reproducible from the final port (`diffeval/t20_regen.py`, output
  `diffeval/work/t20_regen.out.txt`): every generator of the update run again after the port's last
  change; the expected values and the Lean inputs, with the lookup tables of `sas_best`,
  `sas_best12` and `input_best32` inside them, come out byte for byte the same.
- The four compositions evaluated again on the Lean as accepted at the end, by agents that did not
  write them (`diffeval/work/t20_<suite>.out.txt`): `run` 144/144, `run_py_py_py` 74/74,
  `run_py_py` 26/26, `run_py` 144/144.
- The port run end to end on `legacy/data`, each stage on the files of the stage before, and each
  stage on a folder without its input (`diffeval/t20_e2e.py`, output `diffeval/work/t20_e2e.out.txt`).
- Receipts: `diffeval/receipts/units.tsv` holds the rows that describe the Lean as it now stands; the
  rows of the earlier Lean of changed units are in `diffeval/receipts/units_before_2026-11-16.tsv`.
- Scripts that called removed keywords: retired (`experiments/t20_retire.py`; plan section 4).
- Manifest: state, upstream, precondition and open parameters of the changed and added units
  (`experiments/t20_manifest.py`); `def:proc_rank_apply_groups` is marked removed.
