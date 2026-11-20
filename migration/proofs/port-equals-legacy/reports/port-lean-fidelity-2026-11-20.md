# How the port's Lean was checked against the Python (2026-11-20)

Read-only audit for the public write-up. Blueprint `py-credit-risk-port`
`5365851c-5549-44b7-9207-4bd4c422031d` (Logos MCP Staging), read with `open_blueprint`, `get_status`,
`get_items`, `grep` only. Repository at `b3cab28`, port/ working tree clean.

Question: for each Lean definition that models Python code, (a) was it judged at acceptance,
(b) was its CURRENT Lean differentially evaluated or fuzzed against the CURRENT Python, (c) if not,
what checked it.

## Summary

**Server state today.** `open_blueprint`: `trust_layers: []` ("Lean you write for code is accepted
once it compiles, neither judged nor fuzzed against the source"). `get_status`: 370 items, 369
formalized, nothing to write or prove, `verification_approved: true`.

**When the judge was on.** Records give this timeline:
- 2026-11-10: the first 145 items were accepted on `b41b22d4` with the server's Judging layer on
  (`migration/port-to-lean/gates.md` Gate 0, Freeze).
- 2026-11-11: the judge was switched off at the owner's request (gates.md, "Post-freeze decisions").
- 2026-11-12 to 2026-11-16: the judge was on again on `b41b22d4`. `prompts/common.md` (UPDATE
  2026-11-12) says "Judging is on", `reports/report-round2.md` to `report-round5.md` say "trust
  layer Judging on", and `update-after-verification.md` section 5 (2026-11-16) says "Trust layers:
  Judging". gates.md does not record the switch back on. Its line "Later edits are compiled only"
  is out of date.
- 2026-11-16: the owner re-based the blueprint to `5365851c` with trust layers off, and the lead's
  decision D7 kept them off (`plan-after-verification.md` 0.1; `informal-spec.md` lines 96-101).
  So any Lean accepted on `5365851c` after the re-base was only compiled, not judged.

**The current port equals what the evaluations ran against.**
- `git log -- port/` ends at `4a757fb` (2026-11-19 09:56 GMT), and the working tree is clean.
- The last differential evaluation is fz9 (`fe_run_06_split`). It ran 2026-11-19 10:13-10:17 GMT
  against `4a757fb`. Its work files are `diffeval/work/fz9_*`, and the receipts are
  `fuzz_2026-11-19.tsv` and the last row of `units.tsv`.
- `port-changes-2026-11-19-split.diff` is byte-identical to `git show 4a757fb -- port/credit_risk
  port/tests`.
- `port-changes-2026-11-18-fifth.diff` is byte-identical to `git diff b9883c8 3272e9d -- port/`.
  It is also identical from `5784fc8`, so no port commit falls between the fourth and the fifth
  diff.
- Every evaluation after the fifth diff (fz5/fz6/fz7/fz8m from 19:37 GMT, x27 from 22:51 GMT on
  2026-11-18) started after `3272e9d` (17:01 GMT).
- `3272e9d` and HEAD differ only in `feature_engineering.py` (`_split_draw`, lines 20-25 and
  352-370). Outside the fe stage, the Python those evaluations ran is the Python at HEAD.
- Not established: I could not match the four earlier recorded diffs (`2026-11-16`,
  `-17-second`, `-third`, `-fourth`) byte for byte to git ranges. That matters only for
  provenance: every unit those diffs touched was changed again or re-evaluated later.

**Counts** (100 code units in the manifest less the removed `proc_rank_apply_groups`, plus 5 glue
definitions written by the provers):

| Class | Units | Judged at acceptance | Current Lean evaluated against current Python |
|---|---|---|---|
| A. Lean from before the re-base; the unit's Python unchanged since its evaluation | 67 | yes (`b41b22d4`, copied at the re-base) | yes, unit-level receipts; the Python of the unit is the same at HEAD |
| B. Lean rewritten on `5365851c`; unit-level evaluation of the current Lean | 11 | **no** | yes, fuzz or real-data receipts after the last change |
| B'. Compositions rewritten on `5365851c`, evaluated as wholes | 2 (`run_py`, `run_py_py_py`) | **no** | yes, but on 2 scenarios each plus the stops (x27, 2026-11-18) |
| C. Lean rewritten on `5365851c`; current version reached only inside a composition (x27) or an unreceipted fuzz | 18 | **no** | only indirectly; no unit-level receipt after the last change |
| D. Compositions not re-evaluated after one of their units changed | 2 (`run`, `run_py_py`) | yes (Lean from 11-16, unchanged) | **no**; last whole-stage evaluation 2026-11-16, before the fourth diff and the split change |
| E. Glue: `pyPipeline`, `PyLinks`, `Paired`, `PyParams`, `ScoreRun` | 5 | **no** (written on `5365851c`) | **never evaluated**; review only, and the latest `PyLinks` changes (C-j, C-k) have no recorded review |

In short, 78 of the 100 code units have a unit-level differential receipt on their current Lean
against the current Python (A + B). 20 more are covered only by whole-stage runs, on few scenarios
or on old compositions (B', C, D). The glue that links the port to the contracts (E) has never
been run against Python.

**What "evaluated" means here** (`diffeval/README.md`; `prompts/fuzz-2026-11-16.md`):
- The harness runs `eval_decl` of the Lean on the same inputs as the real Python and compares
  results bit for bit.
- The library routines (fit, numpy `inv`/`solve`/..., `chi2`, `pow2`, the formatters, `today`) are
  parameters. They appear as tables of the real results or as stand-ins, so a wrong routine does
  not show.
- Preconditions are propositions. They were read, not evaluated, except where a receipt row
  evaluates one as a Boolean (step 14, step 15).
- Every difference in a receipt is a recorded prelude limit (RULEBOOK section 6): the sign of a
  zero, or the last bit of `exp`/`log`.

## Gaps for the write-up

1. **Not judged after the re-base.** 36 code units (B, B', C, and `hosmer_lemeshow`) and all 5
   glue definitions were accepted on `5365851c` with trust layers off. Whether their Lean says
   what their text says rests on fuzz (B), whole-stage runs (B', C) or review (E).
2. **The train stage after the fifth diff is fuzzed only in part.** Steps 01, 02, 03, 04, 08, 11,
   13, 14, 15 and the five new helpers (`_kept`, `_solve_sas`, `_inv_sas`, `_left_out`,
   `classification_is_made`) were checked on their current Lean only through `run_py_py_py`, on
   two inputs: x27 C60 (no fit, 89 values) and the T18 sample (6 steps, 258 values).
   - Generators exist for `_kept`, `_solve_sas`, `_inv_sas`, `_left_out`, steps 09 and 14, step 08
     and `fz6_td15`, but no Lean output was kept and no receipt was written
     (`update-2026-11-18.md` 3.5).
   - The X28 path (a singular X'X in step 03, `3272e9d`) has no recorded Lean evaluation.
3. **Two compositions are stale.**
   - `def:run`: its Lean is unchanged since 2026-11-16, and the whole stage was last evaluated
     2026-11-16 (t6 144, fuzz 2411, one re-base input `rb_t6`). The split unit has changed twice
     since. Its stored `code` today is the version from after the fourth diff and before the
     split (no `_split_draw`; checked with `get_items`).
   - `def:run_py_py`: last evaluated as a whole 2026-11-16 (t11 26, fuzz 2314). Step 08 changed in
     the fourth diff. Its stored code lacks `keep_sas_names`: `grep` finds it in step 08, train 14
     and `run_py_py_py`, not in `run_py_py`.
   - Both compositions call the unit items, so the risk is in the wiring, not in the arithmetic.
4. **The glue was never run.** `pyPipeline`, `PyLinks`, `Paired`, `PyParams` and `ScoreRun` were
   never evaluated: no `diffeval/` script names them.
   - What checks them: a non-author review recorded for C-g to C-i (`definitions-v3.md`, "each
     reviewed by a prover who did not write it"; `PyParams`: author prover-1, reviewer prover-9);
     `PyLinks` line citations checked against `port/` at `3272e9d` (C-h); and the T0 proof that
     `PyLinks`, `Paired` and `SasLinks` can hold together.
   - The T0 proof shows the assumptions are consistent, not that they are faithful.
   - No review is recorded for C-j (`PyLinks` 5, the split) or C-k (`PyLinks` 14). C-k says "The
     lead may want them reviewed".
5. **One fuzz has no receipt.** fz7_m (`units/fz7_metrics_gen.py`, `work/fz7_m.result.json`,
   2026-11-18 22:11 GMT): metrics steps 01, 02 and 04-10 composed as `run` composes them, 800
   seeds, 800 PASS. It has no row in `receipts/`. It is the only post-fifth-diff evidence for
   `metrics_run_05` and for steps 01, 02, 04 on the widened preconditions (a validation table with
   no row).
6. **The records disagree in places.**
   - The manifest marks `hosmer_lemeshow` "unchanged" on 2026-11-17. The Python changed that day
     (`a8ab250`: clamp to [1e-6, 0.999999]), and the current Lean contains the clamp
     (`get_items statement_lean`, "sc:1454"). So it was rewritten after the re-base, not judged,
     and the change is not recorded. It is evaluated: fz3_hl 2400 and fz6_hl 2441 through step 07.
   - The `fuzz_2026-11-17.tsv` row for `train_run_03` says "fuzz of 2026-11-18", but its artifacts
     are dated 2026-11-17 14:25-14:45 GMT. Either way it is before the fifth diff.
   - gates.md says the judge stayed off after 2026-11-11, while later records say it was on (see
     the timeline in the summary).
   - On `5365851c`, with `trust_layers: []`, two records report a judge verdict on items without
     code: "the judge rejected the Lean over clause 4" on `PyLinks` (C-f), and "judge approved" on
     `thm:G2_train_coverage` (C-m). The server may judge such statements whatever the trust
     layers. This audit cannot settle that.
7. **Stored code is stale in comments only.** On 11 items the stored code differs from `port/`
   only in `.sas` line numbers inside comments (DEV-014, `update-2026-11-17.md` section 6). Lean
   header line ranges are also out of date (for example `hosmer_lemeshow` cites 1399-1482; it now
   stands at 1408-1493).

## Table per unit

Abbreviations:
- J: judged at acceptance (yes = Lean accepted on `b41b22d4` under Judging and copied unchanged at
  the re-base; no = accepted on `5365851c`).
- Receipts: `R/` = `migration/port-to-lean/diffeval/receipts/`.
- Dates: 2026-11.
- "Py unchanged" means the unit's Python lines are not touched by any commit after the evaluation
  (git `0f7fc64..4a757fb` touches only: fe `run` split lines; metrics `confusion_metrics` and
  `run`; predict `run` lines 442-469; sas_compat `LogisticFit`, `StepwiseResult` (field added and
  removed again), `fit_logistic`, `stepwise_logistic`, `hosmer_lemeshow`, `classification_table`,
  the new helpers and `keep_sas_names`/`drop_sas_names` (let-inlined in units); train `run`).

### Feature engineering

| Unit | Last Lean change | J | Current Lean vs current Python | Other check |
|---|---|---|---|---|
| def:fe_run_00_input_check | 16 (T2) | yes | `R/units.tsv` 784 + fuzz_2026-11-16 2390 kept, 0 diff; Py unchanged | review T2 |
| def:fe_run_01_clean | 16 (T3) | yes | units 8; fuzz 16: 2376 kept, 0 diff | |
| def:fe_run_02_income_medians | ≤12 | yes | units 8; fuzz 16: 2121 + 250 (14 KNOWN-LIMIT sign of zero) | |
| def:fe_run_02b_medians_all | 16 (T4) | yes | units 15/8; fuzz 16: 2240, 1 KNOWN-LIMIT | |
| def:fe_run_03_cleaned | ≤12 | yes | units 8 | |
| def:fe_run_04_imputed | 16 (T4) | yes | units 9/5; fuzz 16: 2240, 0 | |
| def:fe_run_05_features | 16 (T5) | yes | units 234/11; fuzz 16: 2776, 0 | |
| def:fe_run_06_split | 19 (rev b0fadb19, split) | **no** | fz9 19: 800 compared, 0 diff (`R/fuzz_2026-11-19.tsv`); real data 3 of 3 (`R/units.tsv` last row), port `4a757fb` | |
| def:_into_float | ≤12 | yes | units 18 | |
| def:run (fe composition) | 16 (T6), restored unchanged 19 (rev 9d90c71b) | yes | **not since the 4th diff / split**: units t6 144 (16), fuzz 16 2411, re-base input `work/rb_t6` | stored code stale (pre-split) |

### Predict

| Unit | Last Lean change | J | Current Lean vs current Python | Other check |
|---|---|---|---|---|
| def:predict_run_00_input_check | 16 (T7) | yes | units 467/607; fuzz 16: 2135, 0 | |
| def:predict_run_01_clean | 16 (T8) | yes | units 9/8; fuzz 16: 2188, 0 | review T8 |
| def:predict_run_02_medians | 16 (T8) | yes | units 14; fuzz 16: 2560, 0 | |
| def:predict_run_03_cleaned | ≤12 | yes | units 13/9 | |
| def:predict_run_04_imputed | 16 (T8) | yes | units 14/12; fuzz 16: 2071, 0 | |
| def:predict_run_05_features | 16 (T9) | yes | units 195/11; fuzz 16: 2788, 0 | |
| def:predict_run_06_score | ≤12 | yes | units 13 | |
| def:predict_run_07_predictions | 16 (T10) | yes | units 26; fuzz 16: 2400, 0 | |
| def:predict_run_08_outputs | 17 (4th diff) | **no** | `R/fuzz_2026-11-17.tsv` fz3_p08 2100, 0 (after the 4th diff; Py unchanged since) | |
| def:run_py_py (predict composition) | 16 (T11) | yes | **not since step 08 changed**: units t11 26 (16), fuzz 16 2314 (3 KNOWN-LIMIT exp), `rb_t11` | stored code stale (no `keep_sas_names`) |

### Metrics

| Unit | Last Lean change | J | Current Lean vs current Python | Other check |
|---|---|---|---|---|
| def:confusion_metrics | 18 (5th diff, `head`) | **no** | in compositions only: x27 `run_py` 20/20 (`R/units.tsv`, 18); fz7_m builds it in Lean (unreceipted) | |
| def:metrics_run_01_roc_auc | 16 (T12); precond 18 | yes (unit) / no (precond) | units 48, fuzz 16 2166 (before the widened precond); fz7_m 800 PASS (unreceipted) | |
| def:metrics_run_02_ks | 16 (T13); precond 18 | yes / no | units 72, fuzz 16 2229; fz7_m (unreceipted) | |
| def:metrics_run_03_thresholds | 18 (rewritten, rev 8f76df27; Py unchanged) | **no** | x27 `run_py` only (20 values, 2 scenarios) | |
| def:metrics_run_04_deciles | 16 (T14); precond 18 | yes / no | units 48 (1 KNOWN-DIFF), fuzz 16 2244 (6 KNOWN-LIMIT); fz7_m (unreceipted) | |
| def:metrics_run_05_cumulative_lift | 18 (5th diff, `valid_exists`) | **no** | fz7_m 800 PASS (unreceipted); x27 `run_py` | fuzz 16 was before the change |
| def:metrics_run_06_psi | 16 (T15); precond 18 | yes / no | `R/fuzz_2026-11-18.tsv` 2683 compared, 2 DIFF (marked expect_diff, text-null case) | owner lifted precond clause (77 inputs equal) |
| def:metrics_run_07_calibration | ≤12; precond 18 | yes / no | fuzz 18: 3000, 0 | |
| def:metrics_run_08_validation_summary | 18 (5th diff) | **no** | fuzz 18 fz8m: 2400, 0 | |
| def:metrics_run_09_model_performance | 18 (5th diff) | **no** | fuzz 18 fz8m: 2400, 0 | |
| def:metrics_run_10_printed_roc | ≤12 | yes | units 11; fuzz 18 fz8m: 2400, 0 | |
| def:run_py (metrics composition) | 18 (rev bbeffd7a) | **no** | x27 2 scenarios: C60 (no validation row) and real_metrics 200/300, 20/20 values (`units/x27_run_py_gen.py`) | fuzz 16 2092 (before the change) |

### Train and sas_compat

| Unit | Last Lean change | J | Current Lean vs current Python | Other check |
|---|---|---|---|---|
| def:train_run_01_fit_frame | 18 (5th diff, rev 638e76c6) | **no** | x27 `run_py_py_py` only | code refreshed 18 (Lean unchanged) |
| def:train_run_02_stepwise_summary | 18 (5th diff) | **no** | x27 only | fz3_s02 2400 (17, before) |
| def:train_run_03_fit_global_rsquare | 18 (5th diff: `_kept`, `_solve_sas`, `_left_out`, X28) | **no** | x27 only; X28 path not exercised on record | fz 17: 2250 + 2280 (1 exp) before |
| def:train_run_04_score_train | 18 (5th diff) | **no** | x27 only | |
| def:train_run_05_association | 18 (5th diff) | **no** | fuzz_2026-11-17.tsv fifth-diff row: 2507, 0 | |
| def:train_run_06_coefficients_odds | 18 (5th diff) | **no** | fz5_s06 2169, 12 explained (6 exp, 6 pow2 stand-in) | owner: `0 ≤ idx` narrowing |
| def:train_run_07_hl | 17 (d), resubmitted 18 | **no** | fz6_hl 2441, 0 | |
| def:train_run_08_ctable | 18 (5th diff, rev d6d7492b); precond 19 (C-m) | **no** | x27 only | fz 17: 2143, 0 (before); fz5_ctable generator, no output |
| def:train_run_09_confusion_train | ≤12 | yes | units 55/220 (T18 chain) | |
| def:train_run_10_score_valid | 18 (5th diff, rev e605d60f) | **no** | fz5_s10 2049 + 886, 7 exp last bit | |
| def:train_run_11_confusion_valid | 18 (5th diff, rev 3c9c47d1) | **no** | x27 only | |
| def:train_run_12_risk_scores | 16 (T17) | yes | units 32/104; fuzz 18 2257, 0 (through the fifth-diff carrier) | |
| def:train_run_13_roc | 18 (5th diff, rev 575b2fe5) | **no** | x27 only | fz 17 2144 (before) |
| def:train_run_14_final_and_summary | 18 (5th diff) | **no** | x27 only | fz4_t14 2919 (17, before); fz5_t14 inputs, no output |
| def:train_run_15_printed_roc | 18 (5th diff) | **no** | x27 only | fz 17 2045 (before); fz6_td15 inputs, no output |
| def:run_py_py_py (train composition) | 18 (rev feb71d76) | **no** | x27: C60 89 values, T18 sample 258 values, three stops | u18b 771 (17, before) |
| def:LogisticFit | 17 (field `separation`) | **no** | structure; only inside u18b / x27 | |
| def:StepwiseStep, def:StepwiseResult | ≤12, resubmitted unchanged 17 | yes | units 6/15 and 3/12 | Python field added and removed again 17 (`45a5b78`) |
| def:classification_table | 18 (5th diff) | **no** | fz5_cte 2051 + 32 near-threshold literals, 0 diff | |
| def:classification_is_made, def:_kept, def:_solve_sas, def:_inv_sas, def:_left_out | 18 (new) | **no** | x27 only (T18 sample) | generators `fz5_*_gen.py`; no Lean output kept, no receipt |
| def:hosmer_lemeshow | rewritten after the re-base (Lean has the 17 clamp; not in the manifest), resubmitted 18 (54061d92) | **no** | fz3_hl 2400 kept, 105 rejected (R-F2I); through step 07 fz6 2441 | |
| def:_hl_groups | 18 (rev 2864ca0a, n / g) | **no** | author re-run: 2000 + 2699 + 162, 0 diff (`R/fuzz_2026-11-18.tsv`) | non-author fuzz found the bug before the fix |
| def:_pairs, def:roc_association, def:association_table | 16 (T1) | yes | units 96/192/96; fuzz 16 2112 each | |
| def:_groups, def:_SE_EPS, def:_SQRTBIG | 16 (T1) | yes | units; fuzz 16 `_groups` 2100 | |
| def:merge_one_to_one, def:sas_round, def:_TIE_EPS, def:_ROUND_FUZZ_CAP | 12 (7927af7) | yes | `R/units_7927af7.tsv` (809 cases) and units | |
| def:lt, le, gt, ge, eq, flag, div, sas_sum, sas_min, sas_max, sas_log, sas_exp, sql_sum, sql_mean, sql_min, sql_max, proc_rank_groups, _expit, _ratio, _ROUND_FUZZ, _e, _named, _has_bare_column, _is_scalar, chi2_sf, Z975, RocAssociation, _Pairs, AssociationTable | 10-12 | yes | `R/units.tsv` rows (Gate 4, 11-10/12); Py unchanged | |
| def:ExprOrNum, def:FloatArray_ (preludes) | 10-11, frozen | yes | `R/prelude.tsv` 154 rows, 774 pairs; 32 KNOWN-LIMIT | |

### Glue written by the provers (not code items)

| Item | Last change | J | Evaluated against Python | What checked it |
|---|---|---|---|---|
| def:pyPipeline | 19 (text only C-h; restored f3d96a77) | **no** | never | non-author review (C-g "Order"; C-h/C-i review findings); "wiring only" |
| def:PyLinks | 19 (C-j clause 5 split, C-k clause 14; restored f20bd80e) | **no** (one record of a judge rejection, C-f) | never | review to C-i; citations checked against `3272e9d` (C-h); **C-j/C-k not reviewed on record**; T0 witness = consistent, not faithful |
| def:Paired | 19 (C-h `Paired` 5) | **no** | never | review; T0 witness |
| def:PyParams | C-g era | **no** | never | author prover-1, reviewer prover-9 |
| def:ScoreRun | 19 (C-i text only) | **no** | never | review |

Not in scope: the 28 `def:wf_*` (prover-written domains), `def:sasPipelineOf`, `def:SasLinksOf`,
`def:SasParams` (the SAS side), the preconditions (domains, read rather than evaluated, except
where noted).

## Sources

`migration/port-to-lean/gates.md`, `manifest.tsv` (columns `update_2026_11_16` to
`update_2026_11_19_split`), `update-after-verification.md`, `update-2026-11-17.md` section 5,
`update-2026-11-18.md` sections 3-7, `prompts/common.md`, `diffeval/README.md`, `diffeval/receipts/*.tsv`,
`diffeval/work/` (file times), `migration/proofs/port-equals-legacy/definitions-v3.md`,
`plan-after-verification.md` 0.1, `informal-spec.md` 96-101, `reports/2026-11-19-final-report.md`
148-151, git log of `port/`.

## Fidelity pass, 2026-11-20 (w29)

Appended record. The text above stays as written on 2026-11-20. This section records the
workflow pass w29, which tried to close the gaps listed above. Eight agents ran: seven test agents
(`train-a`, `train-b`, `train-c`, `train-d`, `metrics`, `compositions`, `stale-compositions`)
plus a glue end-to-end agent (`glue-end-to-end`), and one non-author review of the glue
(`PyLinks`, `Paired`, `ScoreRun`, `pyPipeline`). Every test agent reported `ok: false`. Blueprint
`5365851c-5549-44b7-9207-4bd4c422031d`. Agents were allowed only `eval_decl` and reads on it.
Nothing was written to the blueprint.

**The common block.** No evaluation carrier is left on the blueprint. `def:zz_carrier_t`,
`def:zz_carrier_e`, `def:zz_carrier_m` and `def:zz_carrier` return ResourceNotFound, and
`open_blueprint` lists no `zz_carrier*` item. On every input, `eval_decl` refuses the train step
items, the compositions, `def:pyPipeline`, `def:PyLinks` and most metrics items with the schema
error recorded in `diffeval/eval_decl-errors-2026-11-18.md` rows 1-6 (the server's own message is
lost). Control calls worked: `def:FloatArray_` / `Np.cumsumInt` gave [1, 3, 6], and
`def:_hl_groups` gave [12, 6]. The pass rules said a needed carrier is reported, not added. So
every unit that can be reached only through a refused item has **0 Lean cases** in this pass.
In those rows, "0 differences" is not a pass.

**Hook block.** Every test agent was refused a read of this report by the role's isolation hook, so
none of them saw the gap list above. They worked from their task text.

### Per gap

**Gap 1 (not judged after the re-base).** No change: the pass did not judge anything. It adds
fuzz evidence for 5 of the 36 units (gap 2 below).

**Gap 2 (train stage after the fifth diff).**

| Unit | Lean cases compared | Differences | KNOWN-LIMIT | Receipt | Status |
|---|---|---|---|---|---|
| def:_kept | 2425 | 0 | 0 | `R/fuzz_2026-11-20-train-b.tsv` | PASS (2400 seeded + 24 hand edge + 1 real-data; evaluated through `def:_solve_sas`'s solve argument) |
| def:_solve_sas | 2001 | 0 | 0 | same | PASS (2000 seeds × 2 solvers, 1182 partial, 211 nothing kept; + 1 real-data step 19) |
| def:_inv_sas | 2101 | 0 | 0 | same | PASS (2100 seeds + 1 real-data 16×16 information matrix) |
| def:_left_out | 2001 | 0 | 0 | same | PASS (2000 seeds + 1 real fit) |
| def:classification_is_made | 2601 | 0 | 0 | `R/fuzz_2026-11-20-train-c.tsv` | PASS (2600 seeds 2000000..2002599, 4 blocks of 650; planted bit-flip detected; + 1 real-data call, rows = [] with an exact Gram-matrix matmul) |
| def:train_run_01_fit_frame | 0 | - | - | `R/fuzz_2026-11-20-train-a.tsv` (NOT-RUN row) | not run; stored code matches train.py:55-111 at HEAD by reading |
| def:train_run_02_stepwise_summary | 0 | - | - | same | not run; stored code matches train.py:117-157 by reading |
| def:train_run_03_fit_global_rsquare | 0 | - | - | `R/fuzz_2026-11-20-train-b.tsv` (NOT-RUN row) | not run; Python side with X28 ready (`units/fz10_train_run_03_gen.py`, `work/fz10_train_run_03.py.json`) |
| def:train_run_04_score_train | 0 | - | - | `R/fuzz_2026-11-20-train-a.tsv` | not run; stored code matches train.py:294-324 by reading |
| def:train_run_08_ctable | 0 | - | - | `R/fuzz_2026-11-20-train-c.tsv` | not run; stored code matches train.py:479-535 |
| def:train_run_11_confusion_valid | 0 | - | - | same | not run; stored code matches train.py:640-700 |
| def:train_run_13_roc | 0 | - | - | `R/fuzz_2026-11-20-train-d.tsv` | not run |
| def:train_run_14_final_and_summary | 0 | - | - | same | not run; suite fz5_t14 ready (2907 kept, 5 inputs), targets the removed `def:zz_carrier_t` |
| def:train_run_15_printed_roc | 0 | - | - | same | not run; suite fz6_td15 ready (2247 kept, 8 inputs), same target |

(`R/` = `migration/port-to-lean/diffeval/receipts/`.) In total, 11,129 cases were compared on the
five helpers, with 0 differences. The X28 path still has no Lean evaluation on record, and the real
stepwise run on `legacy/data` never reaches it.

Still not covered, and why: the nine train steps above have no current-Lean unit receipt. No
carrier exists, and `eval_decl` refuses the units and every computable item that depends on them
(`run_py_py_py`, `pyPipeline`, `PyLinks`). `train_run_11` needs a carrier with a digest printer
even after the refusal is lifted, because Floats print with 6 decimals.

**Gap 3 (stale compositions).**

| Item | Lean cases compared | Receipt | Status |
|---|---|---|---|
| def:run, fuzz | 0 of 2,301 kept | `R/fuzz_2026-11-20-stale-compositions.tsv` | not compared; suite ready (`work/fz10_run.*`, seeds 1000000..1002399 + 2 edge) |
| def:run, real data | 0 | same | not compared; expected digests in `work/fz10_real.expected.json` |
| def:run_py_py, fuzz | 0 of 2,300 kept | same | not compared; suite ready (`work/fz10_run_py_py.*`, seeds 2000000..2002599) |
| def:run_py_py, real data | 0 | same | not compared |
| def:run_py (metrics composition) | 0 | `R/fuzz_2026-11-20-compositions.tsv` | blocked |
| def:run_py_py_py (train composition) | 0 | same | blocked |

Stored source against port HEAD (by reading):
- `def:run`: OUT OF DATE. It confirms gap 3. It lacks HEAD feature_engineering.py:352-367 (the
  fit test and the `_split_draw` fallback), :20-25 and `import random`. Its citations (19-380, and
  :343-350 etc. inside the Lean) are shifted, because the function now runs 28-400. The Lean logic
  is not stale, since it delegates to `def:fe_run_06_split`.
- `def:run_py_py`: UP TO DATE. It matches predict.py:17-491 line for line, "including the fourth
  diff's keep_sas_names lines". **This disagrees with gap 3 above**, which says the stored code
  lacks `keep_sas_names` (from a `grep`). The disagreement is not resolved here.

No input inside the rendered precondition made the current Python raise (0 of 2,301 for run, 0 of
2,300 for run_py_py).

**Gap 4 (glue never run).** The Lean side was still not evaluated: `pyPipeline` is noncomputable
over the reals, and every computable host item is refused. For the first time, the Python wiring
was checked end to end. All four stages ran on the real port (HEAD `4a757fb`), each reading the
files the stage before wrote, on 750 seeded inputs and on `legacy/data` (150,000 rows, with
`inputs/split_ids.csv`). Receipt `R/fuzz_2026-11-20-glue-end-to-end.tsv`, rows marked "PY-ONLY ...
(no Lean)".

| Glue check | Python runs compared | Differences |
|---|---|---|
| G1 features: files exactly when fe completes; split ids from the imported VAR1 cells | 703 | 0 |
| G2 fit: model.json iff both feature files and a final fit; float intercept; coefficients CSV iff model.json | 703 | 0 |
| G3 ScoreRun no-fit: S2 = [] | 53 | 0 |
| G4 ScoreRun fitted: S1 = validation chain on F1 against risk_scores_train.csv | 520 | 0 (10 more outside `def:train_run_04_score_train_precond`, all differ; counted as rejected) |
| G5 medians flag | 703 | 0 |
| G6 metrics lookups | 583 | 0 |

48 seeded runs where a stage raised were left out (39 OverflowError in
`sas_compat._entry_score_chisq`, 9 polars ComputeError on 1-3 row inputs). Whether they fall
inside a stage precondition was not rendered.

The review of C-j and C-k (owed in gap 4) is now on record: both are checked, with no finding. The
review found two high findings on other clauses (F1, PyLinks 10; F2, Paired 2). See the verdicts
and findings below.

**Gap 5 (fz7_m without receipt).** Still no receipt. The suite targets `def:zz_carrier_e`, which no
longer exists, so it was not re-run. The `metrics` agent wrote no receipt on purpose: "a zero-row
receipt (fuzz_2026-11-20-metrics.tsv) would misstate coverage". The metrics units were not compared
either:

| Unit | Lean cases | Status |
|---|---|---|
| def:confusion_metrics | 0 | refused (schema error) |
| def:metrics_run_03_thresholds | 0 | accepted, but every input notRun ("no Repr for the result"; `Pl.Frame` has no Repr) |
| def:metrics_run_05_cumulative_lift | 0 | refused; its dependent `def:run_py` is refused too |
| fz7_m re-run (01/02/04 composition) | 0 | blocked, carrier gone |

**Gaps 6 and 7 (records, stale comments).** Not addressed by this pass, except the `def:run`
citation shift and the `def:run_py_py` disagreement noted under gap 3.

### PyLinks review verdicts

| Clause | Verdict | Lines |
|---|---|---|
| PyParams (all fields; split comment 'table of selected ids', fit 'for the training feature table as read') | OK: fields only; the split and fit descriptions match pyPipeline and the code | feature_engineering.py:349-370; train.py:98-103 |
| PyLinks 1 input_best32 on digit texts / missing forms | OK at R (32-char cut, strip, _NUM_RE, finite) | sas_compat.py:235-243 |
| PyLinks 2 12-char round trip | OK as ruled (H9, G54); restricted to decimal12 | sas_compat.py:235-243, 426-428 |
| PyLinks 3 training import on TrainOK | OK (guessingrows=None; numeric iff every value parses; empty header gives VAR1) | sas_compat.py:557-592; feature_engineering.py:41-47 |
| PyLinks 4 test import on TestOK | OK as described (rules H1-H3, H7, H12, H13d); not re-run | sas_compat.py:557-592 |
| PyLinks 5 split (C-j) | OK: text and Lean agree, and both code branches meet it on every argument and any fixed file; the cited lines match HEAD | feature_engineering.py:20-25, 349-366 (unit 367-370) |
| PyLinks 6 fit (distinct candidate effects; both outcomes give final and intercept-only fits; one outcome gives StepwiseResult()) | OK; the 'returns a fit' part is trusted base B4.1 (the code may raise RuntimeError) | train.py:98-103, 298; sas_compat.py:1068-1072, 1080-1093, 1120, 1208 |
| PyLinks 6b fitted result facts | OK at R (m2ll0 > 0 with both outcomes; cov is an inverse of an information matrix or _inv_sas) | sas_compat.py:745-750, 945-966 |
| PyLinks 7 / 7b existence flags | OK: matches the stop when either feature file is missing and the no-fit write; no circularity with pyPipeline | train.py:35-41; sas_compat.py:1069-1072 |
| PyLinks 8, 8b, 8c, 16 read-backs | OK as rules H4-H6, H15, G55 (not re-run) | sas_compat.py:557-592 |
| PyLinks 9 model file | OK (H11) | train.py:537-539 |
| PyLinks 10 counts as text (for all n : N) | FINDING F1: false of the code for n >= 10^8 (sas_best(123456789, 8) = '1.2346E8' parses to 123460000) | sas_compat.py:391-423; metrics_calculation.py:18-21 |
| PyLinks 11 date | OK | metrics_calculation.py:545; train.py:888; sas_compat.py:275 |
| PyLinks 12 fsum >= 0 | OK | sas_compat.py:1319-1320 |
| PyLinks 13 einsum_q/matmul/matvec shapes | OK ('whenever it returns', B4.2) | numpy semantics |
| PyLinks 14 final fit's first name (C-k) | OK: true on every argument; citations verified | sas_compat.py:16, 672, 750, 952, 964, 1043, 1072, 1084, 1090, 1120, 1208 |
| Paired 1 SAS imports | OK (restates SasLinks 1/2/2b; SAS side not re-run) | legacy/feature_engineering.sas:41-123 |
| Paired 2 split | FINDING F2: assumes SAS SURVEYSELECT selects the port's ids, which holds only for the real data; consistent with PyLinks 5 in the Lean | legacy/feature_engineering.sas:326-331; feature_engineering.py:20-25, 349-366 |
| Paired 3 fit | OK as trusted base B4.1 (G58), disclosed | train.py:294-310 |
| Paired 4 shared read-backs | OK (G55) | - |
| Paired 5 SAS existence flags | OK against the SAS train stop; the 'word for word' match with SasLinks (8) was not re-diffed | legacy train.sas:34-42 (as cited by train.py:34) |
| Paired 6 agg sum/mean, arrange identity | OK at R | - |
| Paired 7 date | OK, consistent with PyLinks 11 | - |
| ScoreRun (fitted / without a model) | OK: the fitted S1 = Q.score m F1 is what the training chain writes (thm:E5_train_scores, TheoremProved); the no-model case matches PyLinks 7b's chain; the C-i caveat is stated | train.py:294-318, 610-633, 705-851 |
| pyPipeline.features | OK: py.split at the cleaned VAR1, run, then the two feature files | feature_engineering.py:349-400 |
| pyPipeline.fit | OK: both flags tested; none when step 04 extracts no intercept | train.py:35-41, 294-310 |
| pyPipeline.score | OK: validation chain (steps 10, 12, 14) on the model's intercept and terms; fillers idle (lem:py_score_fillers_idle) | train.py:610-633, 751-851 |
| pyPipeline.scoreTest | OK as wiring (medians from steps 02/02b, gated by the medians flag) | feature_engineering.py:380-391 |
| pyPipeline.metrics | OK; the one default (a file not written is the table with no row) is disclosed | metrics_calculation.py:117 |

### Findings, verbatim

**train-a**
- BLOCKER (no evaluation route): the evaluation carriers def:zz_carrier_t, def:zz_carrier_e and def:zz_carrier are not in blueprint 5365851c-5549-44b7-9207-4bd4c422031d (get_items returns ResourceNotFoundException for each). eval_decl refuses at the item level, every time and with any input, on def:train_run_01_fit_frame (decl train_run_01_fit_frame), def:train_run_02_stepwise_summary (decl train_run_02_stepwise_summary), def:run_py_py_py (decl omitted and decl run_py_py_py) and def:pyPipeline. The error is 'Structured content does not match the tool's output schema: data must have required property item_id ... data/success must be equal to constant'. This is the same refusal path recorded in migration/port-to-lean/diffeval/eval_decl-errors-2026-11-18.md. Control: eval_decl on def:FloatArray_ / Np.cumsumInt with input [1, 2, 3] returns [1, 3, 6], so the server is up. That prelude item does not depend on the units, so it cannot reach them.
- NEEDED, not added (the pass rules say a needed carrier is reported, not added): a code item with decl `zz_carrier_t (xs : List Int) : List Int := xs` (source migration/port-to-lean/diffeval/carrier.py) that depends on def:train_run_01_fit_frame, def:train_run_02_stepwise_summary and def:train_run_04_score_train. Once it exists, the earlier generators (diffeval/units/fz3_step02_gen.py, fz3_train_run_gen.py, t18_gen.py) show the setup to reuse for the fz10 generators.
- HOOK BLOCK: the role's guard hook refused my read of migration/proofs/port-equals-legacy/reports/port-lean-fidelity-2026-11-20.md, so I could not see which gaps the report lists for these three items.
- No generator was written to diffeval/units/fz10_*: without a Lean side it could not be checked. No outputs were written to diffeval/work/. Nothing was written to the blueprint. The only blueprint calls were the refused eval_decl probes and one control eval_decl on def:FloatArray_.

**train-b**
- No Lean/Python difference found in _kept, _solve_sas, _inv_sas or _left_out: 8528 cases compared bit-exact (fuzz plus real data), 0 differences, 0 KNOWN-LIMIT.
- train_run_03_fit_global_rsquare (including X28) could not be compared in Lean. eval_decl cannot print a result of type List (String x Tabular.Table Float), and no evaluation carrier exists on blueprint 5365851c. The claim for this item rests on earlier receipts (fuzz 2026-11-17/18, which predate the X28 code of the fifth port diff) until a carrier item is added. The X28 inputs and Python expectations are ready in diffeval/units/fz10_train_run_03_gen.py.
- Blocks by the hook or permissions: (1) reading the gap report migration/proofs/port-equals-legacy/reports/port-lean-fidelity-2026-11-20.md is refused to this role, so the pass did not use its list of gaps; (2) reading the session record is refused, so fuzz_collect.py could not take outputs by script. Outputs were transcribed from the eval_decl results instead. Every verdict was computed inside Lean against expected digests embedded in the input, and the outputs are all-zero flags or lists of 'x' of the expected counts, so a transcription or typing error can only produce a false difference, never a false pass.
- Method note for the reader of the receipts: _kept, _solve_sas and _inv_sas take solve/inv/dot as explicit parameters (RULEBOOK 3). The fuzz uses identical stand-ins on both sides. The real-data cases instead feed the Lean lookup tables of what real numpy returned, so they compare against the real Python bit for bit.
- The real stepwise run on legacy/data never reaches X28: every step keeps all its parameters. The X28 path is only reached by the synthetic inputs.

**train-c**
- Two of my three items were not compared at all, so the pass is incomplete. eval_decl on blueprint 5365851c refuses def:train_run_08_ctable and def:train_run_11_confusion_valid on every input, including "1": it returns the schema error, the same as diffeval/eval_decl-errors-2026-11-18.md rows 1-6. The 2026-11-18 workaround carrier def:zz_carrier_e has been removed from the blueprint, and the dependents I tried (def:run_py_py_py, def:run, def:pyPipeline) are refused too. To finish this, either Logos fixes the refusal, or the lead or owner restores a carrier. That carrier is a def: item that depends on both units and declares List Int printers (token or digest), as zz_carrier_e did. It is needed for train_run_11 in any case, because a Float prints with 6 decimals. I did not add it, per the task rules.
- def:classification_is_made: no difference in 2,600 kept fuzz cases or the 1 real-data case. A planted mismatch was detected as false, as it should be.
- Hook block: my role may not read migration/proofs/port-equals-legacy/reports/port-lean-fidelity-2026-11-20.md, which the task said to read first. I worked without the gap list it contains.
- Real-data note for train_run_08: on legacy/data the real train.run calls classification_is_made once (it returns true) and writes printed_classification.csv. So step 08 is reached on real data, but it cannot be evaluated in Lean until a carrier exists.

**train-d**
- BLOCKER (not a Lean/Python difference): I could not evaluate any of the three items, so none of them has a fidelity receipt. eval_decl on blueprint 5365851c fails for def:train_run_13_roc, def:train_run_14_final_and_summary and def:train_run_15_printed_roc (input "1", with and without decl). It also fails for every other item that can see them: def:run_py_py_py (sees all three), def:pyPipeline and def:PyLinks (see step 14). def:Z975 fails too. The error is always the same schema error, so the server's own message is lost. It is the same fault recorded in diffeval/eval_decl-errors-2026-11-18.md (rows 1-6). The tool itself works: def:FloatArray_ / Np.cumsumInt returns [1,3,6], and an input that does not elaborate comes back cleanly as notRun.
- The documented workaround, a carrier item that depends on the units, no longer exists: def:zz_carrier_t and def:zz_carrier_e are not in the item list. The brief forbids adding one, so this is reported. Needed: a carrier depending on def:train_run_13_roc, def:train_run_14_final_and_summary and def:train_run_15_printed_roc (identity zz_carrier_t : List Int -> List Int, as before), or a Logos fix for the refusal.
- Python side is ready. train.py and sas_compat.py were last changed 2026-11-18 16:58. The fz5_t14 and fz6_td15 suites were generated after that (19:44 and 19:45). Their slices still match current train.py: 836-941 for step 14, 945-969 for step 15. Step 13's header (801-830) matches the current lines. Once a carrier named def:zz_carrier_t exists, the existing inputs.json can be run unchanged.
- A block stopped part of my job: the hook refused to let this role read migration/proofs/port-equals-legacy/reports/port-lean-fidelity-2026-11-20.md (the gap report named in the task). I did not try to get round it.
- fuzz_collect.py reads only session records named agent-aport-translator-<n>-*.jsonl. A workflow agent like this one may need another collector, or that pattern extended, to collect outputs by script.

**metrics**
- BLOCKER (no evaluation carrier): every Logos carrier has been removed from blueprint 5365851c. get_items returns ResourceNotFound for def:zz_carrier_e, def:zz_carrier_m and def:zz_carrier (diffeval/carrier_e.py: 'removed at the close'). The brief says a needed carrier is reported, not added, so nothing was added and no Lean value was compared. To unblock, the lead must restore the identity carrier zz_carrier_e (diffeval/carrier_e.py:13-14, RULEBOOK G20) with its printer helpers. It needs dependencies on def:confusion_metrics, def:metrics_run_03_thresholds, def:metrics_run_05_cumulative_lift and def:metrics_run_01..10, so that the fz7_m inputs and new fz10 inputs elaborate.
- Evidence, eval_decl refused with the schema error: def:confusion_metrics, def:metrics_run_05_cumulative_lift, def:run_py and def:pyPipeline, each on input '1'. def:run_py was also refused on a well-typed input: lookup lambdas, a Tabular.Cell.str 'today', and none none. This is the failure documented in diffeval/eval_decl-errors-2026-11-18.md: the server's error text is lost.
- Evidence, evaluable but unreadable: def:metrics_run_03_thresholds accepts eval_decl, but every input is notRun with 'no Repr for the result', including a well-typed 3-row Float frame and the empty frame. Pl.Frame has no Repr, and a Float would print with only 6 decimals anyway, so no bit-exact read-back is possible from any current item.
- Tried and failed: using def:run_py as a read-only carrier by passing the digest list through its free 'today' cell parameter (it reaches the validation_date column of model_performance_metrics). The server refuses eval_decl on def:run_py, so this does not work.
- Isolation hook block: reading migration/proofs/port-equals-legacy/reports/port-lean-fidelity-2026-11-20.md was refused ('Blocked by the isolation rule for port-translator'). The brief told me to read it first; I did not see the gap list it holds.
- Nothing was written to the blueprint. The only eval_decl calls were probes: 1 on def:_into_float (succeeded, used as a control), 2 on def:run_py, 1 on def:pyPipeline, 1 on def:metrics_run_05_cumulative_lift, 1 on def:confusion_metrics, 3 on def:metrics_run_03_thresholds. No generator, work file or receipt was written: a zero-row receipt (fuzz_2026-11-20-metrics.tsv) would misstate coverage.

**compositions**
- BLOCKER (not a port finding): neither composition can be evaluated on blueprint 5365851c. A direct eval_decl on def:run_py and on def:run_py_py_py is refused with 'Structured content does not match the tool's output schema ... data/success must be equal to constant' on every call. This is the refusal recorded on 2026-11-18 for the step items in diffeval/eval_decl-errors-2026-11-18.md. Eval works in general: def:_hl_groups returned [12, 6] in the same session.
- No evaluation carrier is on the blueprint. def:zz_carrier_e was removed on 2026-11-19 (update-2026-11-18.md, section 'removal of def:zz_carrier_e'), and open_blueprint lists no zz_carrier* item. The other item that depends on def:run_py, def:pyPipeline, is noncomputable at the real numbers. The remaining dependents are thm:/lem:/wf_ items, which this role may not open. So the only route is an identity carrier on List Int that depends on def:run_py and def:run_py_py_py. Per the brief I am reporting this, not adding it. Even if a direct eval ran, the result would print Floats with 6 decimals, so a bit-exact comparison needs that carrier anyway.
- What is needed to run this pass: the lead (or owner) re-adds a carrier, for example from diffeval/carrier.py or diffeval/carrier_e.py, connected to def:run_py and def:run_py_py_py. Once that exists, these existing generators already build seeded KIT-digest inputs for exactly these compositions and only need the carrier name and today's lookup tables: diffeval/units/fz_run_py_gen.py (metrics, seeded, 2,092 kept on the old id), diffeval/units/x27_run_py_gen.py (real_metrics and C60), diffeval/units/fz2_train_run_gen.py and diffeval/units/x27_train_gen.py (train, with routine tables).
- Second block: the hook refused my read of migration/proofs/port-equals-legacy/reports/port-lean-fidelity-2026-11-20.md (isolation rule for port-translator). I could not see the gaps that report lists. This did not change the outcome, because the evaluation block stops the pass before the gaps would matter.
- No fz10_* generator was written. Its Lean input terms could not be checked to elaborate against any item. Nothing was written to the blueprint: the only calls were 3 refused eval_decl calls and 1 control eval_decl. No Lean item was changed.

**stale-compositions**
- BLOCKER (Lean side not run): I compared 0 of 4,601 kept fuzz cases and 0 of 2 real-data inputs, so the claim 'current Lean computes what current Python computes' is not shown for def:run or def:run_py_py. Each eval_decl call comes back with the opaque schema error ('Structured content does not match the tool's output schema ... data/success must be equal to constant') before any case runs. Items refused: def:run (with decl run, with decl omitted, with decl Pl.zipB, and with the bare input `1`, which an accepted item returns as a notRun case), def:run_py_py, def:fe_run_06_split and def:predict_run_08_outputs. The control def:_hl_groups ['(α := Float) [3, 4, 5, 6] 18 2'] returns [12, 6] in the same session, so the service works. This matches rows 1-6 of migration/port-to-lean/diffeval/eval_decl-errors-2026-11-18.md. The blueprint also has no zz_carrier_* item, and the brief forbids adding one. A carrier is needed: a computable item that depends on def:run and def:run_py_py and declares `List Int -> List Int` (as zz_carrier_f / zz_carrier_p did), and Logos must lift the refusal. Once that exists, eval the inputs in work/fz10_run.inputs.json and work/fz10_run_py_py.inputs.json (rename the carrier in them if its name differs), then run fuzz_collect / compare.py.
- STALE STORED SOURCE: the code stored in def:run predates port commit 4a757fb. It lacks HEAD feature_engineering.py:352-367 (the split-file fit test and the fallback to _split_draw), plus the helper :20-25 and `import random`. Its line citations (19-380 in the Lean header, in def:run_precond and in manifest.tsv; :343-350 and the following ones inside the Lean) are shifted against HEAD, where the function runs 28-400. The Lean logic is not stale on that account, because def:run delegates the split to def:fe_run_06_split, which is current. The code stored in def:run_py_py is identical to HEAD predict.py:17-491.
- ACCESS BLOCK: the hook denied the read of migration/proofs/port-equals-legacy/reports/port-lean-fidelity-2026-11-20.md (isolation rule for port-translator). So I worked without the gap report the task said to read first.
- NO PYTHON-SIDE DEFECTS: in either suite, no input the rendered precondition accepts made the current Python raise (0 of 2,301 for run, 0 of 2,300 for run_py_py).

**glue-end-to-end**
- BLOCKER (not a defect of the Lean or the port): the Lean side of the glue could not be checked at all. pyPipeline is noncomputable over the reals. eval_decl refuses every computable item whose dependencies include a pipeline field, with the same schema error recorded on 2026-11-18. The carriers that used to work around this were removed and this pass may not add them. So there are 0 Lean cases, and the 200+ seeded and real-data Lean comparisons asked for were not done. To unblock: restore an identity carrier item that depends on run, run_py_py_py, run_py_py, run_py, train_run_01/04/10/12/14 and fe_run_00/01/02/02b, or have Logos fix the eval_decl refusal. Then a Float copy of the pyPipeline wiring can be evaluated as an eval input.
- Narrowing, outside the precondition, so not counted as a FINDING (rule: def:train_run_04_score_train_precond, last clause, RULEBOOK Convention 1, 'exp(-eta) finite on every training row'). ScoreRun takes S1 = pyPipeline.score m F1, which is the validation chain (step 10 uses sas_exp). The port writes risk_scores_train.csv from the training chain (train.py:315-320 uses an unguarded polars exp). The two differ only when exp(-eta) overflows on a training row. Smallest input: migration/port-to-lean/diffeval/work/fz10_glue_G4_min/cs-training.csv, 18 rows. Its last row is '18,0,1e200,40,0,1e200,5000,1e80,0,1,0,1', and split.csv puts id 18 in the training part. That row's utilization_debt_interaction is read back as missing, so the fit leaves the row out. The fitted model is intercept 5.4733 with num_credit_lines -0.56582, so eta is about -5.7e79. Port's risk_scores_train.csv for row_id 18: pd_logistic 0.0, credit_risk_score 850.0, risk_grade A, recommendation Approve, interest_rate 0.05. Glue (validation chain on F1): pd_logistic null, credit_risk_score null, risk_grade F, recommendation Decline, interest_rate 0.2. Responsible lines: port train.py:312-320 against train.py:626-631 and sas_compat.py:176-179; Lean def:pyPipeline score field calls train_run_10_score_valid, and def:ScoreRun's fitted disjunct uses it for S1. Reproduced on 10 of the 100 seeds 11000..11099. Whether the contracts' boundary carries this precondition clause I could not check: the gap report and the boundary are not readable by this role.
- Also not a finding: def:PyLinks pins its parameters by properties, not as exact functions. The port instantiates them consistently in every compared run. split is the file-or-seeded-draw, and its ids come from the VAR1 column the glue names. fit is the port's stepwise. The read-backs are the CSV round trip. The flags are file existence. modelFile is model.json. 48 seeded runs raised inside the port and were not compared: 39 OverflowError in sas_compat._entry_score_chisq on 1e150-class values, 9 polars ComputeError on 1-3 row inputs. Which of these fall inside a stage precondition was not rendered.
- A hook blocked one read: migration/proofs/port-equals-legacy/reports/port-lean-fidelity-2026-11-20.md (the gaps file I was told to read first) is denied to this role. I worked without it.

**review (PyLinks, Paired, ScoreRun, pyPipeline)**
- F1 (high; PyLinks 10, Lean conjuncts 'parse_float (sas_best (some n) 8) = n' for all n : N): the clause is false of the real port. sas_compat.sas_best (port/credit_risk/sas_compat.py:391-423) switches to E-notation when the integer part does not fit in 8 characters, and metrics_calculation._into_float (port/credit_risk/metrics_calculation.py:18-21) parses that text. Run at HEAD (port unchanged since 4a757fb): sas_best(123456789.0, 8) = '1.2346E8' -> 123460000.0, and sas_best(1e8, 8) = '1E8'. So the port's real (sas_best, parse_float) pair does not meet PyLinks, and no contract of the form 'for all py with PyLinks py' formally covers the real port. It covers only ports whose formatter is exact on every count. informal-spec.md:647-653 (B3 rewording of G56) says valid input bounds the counts below 10^8 and that the round trip is exact there, but the clause was never restricted to that range. Fix: restate clause 10 to 'for every whole number n < 10^8'. Every proof that uses it must then discharge the bound from InputOK. The bound is already proved for total_good_bad (B3), so this is a re-proof, not a new hypothesis. Until then, T1/T0 show joint satisfiability only by a witness whose formatter is not the port's.
- F2 (high for a PUBLIC claim; Paired 2): the clause assumes that the legacy SAS split selects exactly the ids the port's split lists. The SAS program does not do that. legacy/feature_engineering.sas:326-331 runs PROC SURVEYSELECT samprate=0.7 seed=42 outall, SAS's own PRNG over the rows in row order. The port (port/credit_risk/feature_engineering.py:349-366) uses the fixed split_ids file when it fits, and otherwise random.Random(42).sample over the sorted distinct ids (lines 20-25). The two selections agree only where the file is SAS's own draw (the 150,000 real rows, definitions-v3.md:888-890). On any other valid input the real programs train on different rows and write different files. B1 (informal-spec.md:9-17) says 'on every valid input, the port writes the same compared files as the corrected SAS program' and does not state this pairing. Paired 2 is a legitimate modelling of the split as an input (A27), but the public claim must say 'with the SAS split taken to be the port's selection'. Otherwise the claim is about a SAS program with a different sampler. The Lean is not wrong; the boundary text is missing a hypothesis that is in force.
- F3 (low, records; informal-spec.md:52): the 2026-11-20 note says that on valid input the split file fits, so the draw is never reached. That holds only in the model, where py.split already is the port's selection (C-j). In the real code, _split_draw (feature_engineering.py:365-366) runs on every valid input whose ids are not exactly the fixed file's. lem:py_split_fits says py.split's table fits the unit's test; it says nothing about the real file. The NaN conclusion of the note still holds, but for a different reason: lem:py_split_ids_finite and InputOK. The note should be reworded so that a reader does not take it to mean the port's random draw is dead code.
- F4 (low, records): definitions-v3.md C-k (lines 1157-1182) says lem:py_split_ids_rowids and lem:py_split_fits are 'stated, not proved' and connected to no consumer. On the blueprint both are TheoremProved, and lem:fe_run_06_split_reached cites the pipeline's split. The 2026-11-20 note in informal-spec.md records them as proved; definitions-v3.md has no matching note. The change-note header lists C-m as the latest correction and needs a line for this.
- Checked, no finding. C-j (PyLinks 5): the text and the Lean say the same thing. Both branches of the code meet it on every argument, at the real numbers and for any fixed file. File branch (feature_engineering.py:365): n_train entries, n_train distinct, all in input_ids; the minimum is n_train. Draw branch (lines 24-25): sample of min(n_train, |pool|) distinct members of the sorted distinct present ids. n_train = (7*height+9)//10 at line 364; the formula equals ceil(0.7n) in Python floats for every n <= 300000 (checked). The idempotence argument (the unit given py.split's table selects the same rows) is sound, and the condition C-j left owed is now proved (lem:py_split_ids_rowids, lem:py_split_fits). Paired 2 and PyLinks 5 line up because both sides receive the raw VAR1 list (lem:py_split_input_ids, lem:sas_split_input_ids). The cited lines 20-25 and 352-366 match HEAD.
- Checked, no finding. C-k (PyLinks 14): true of the code on every argument. names[0]='Intercept' (sas_compat.py:16, 672, 1043); fits are built with ['Intercept'] (1084) or ['Intercept', *cols] (1090); fit_logistic and _fit_as_sas return LogisticFit(list(names), ...) (750, 952, 964); the final fit is always cur (1120, 1208); StepwiseResult() at 1072 has no final fit. All citations verified.
- Joint satisfiability: thm:T1 (TheoremProved) gives some py with PyLinks py, and thm:T0 (TheoremProved) gives, for every such py, a sas with Paired py sas. pyPipeline and sasPipelineOf are the actual unit definitions, and PyLinks clauses 7/7b refer to pyPipeline py without circularity: the flags are defined from features, fit and score, which read no flag except fit/score's guarded tests. So PyLinks and Paired are jointly satisfiable over the actual units. They are not satisfied by the real port's own parameters, because of F1 (clause 10). Clause 6 (both outcomes give a fit; stepwise_logistic can raise RuntimeError at sas_compat.py:1086-1093) rests on the disclosed trusted base B4.1 and is not a finding.

### Counts after w29

The earlier summary table stands as written. The table below applies this pass to it. Class C
earlier held 18 units: `confusion_metrics`, `metrics_run_03`, `metrics_run_05`, train steps 01, 02,
03, 04, 08, 11, 13, 14, 15, `LogisticFit` and the five helpers. The five helpers now have
unit-level receipts on their current Lean, so they move from C to B. Nothing else moved.

| Class | Units (before w29) | Units (after w29) | Change in w29 |
|---|---|---|---|
| A. Lean from before the re-base; Python unchanged since its evaluation | 67 | 67 | none |
| B. Lean rewritten on `5365851c`; unit-level evaluation of the current Lean | 11 | **16** | + `_kept`, `_solve_sas`, `_inv_sas`, `_left_out`, `classification_is_made` (11,129 cases, 0 diff; `R/fuzz_2026-11-20-train-b.tsv`, `-train-c.tsv`) |
| B'. Compositions rewritten on `5365851c`, evaluated as wholes | 2 | 2 | not re-run (blocked; `R/fuzz_2026-11-20-compositions.tsv` BLOCKED rows) |
| C. Current Lean reached only inside a composition or an unreceipted fuzz | 18 | **13** | train steps 01, 02, 03, 04, 08, 11, 13, 14, 15, `confusion_metrics`, `metrics_run_03`, `metrics_run_05`, `LogisticFit` remain; 0 Lean cases (no carrier, eval_decl refused) |
| D. Compositions not re-evaluated after a unit changed | 2 | 2 | not compared (0 of 4,601 kept fuzz cases, 0 of 2 real-data); `def:run` stored source confirmed stale; `def:run_py_py` stored source found current (disagrees with gap 3) |
| E. Glue | 5 | 5 | Lean still never evaluated; Python wiring checked G1-G6 on 703 runs + real data, 0 diff in precondition; non-author review recorded incl. C-j/C-k (no finding there), findings F1 (PyLinks 10) and F2 (Paired 2) high, F3/F4 low |

In short, after w29, 83 of the 100 code units have a unit-level differential receipt on their
current Lean against the current Python (A + B). Before w29 the count was 78. 17 units are still
covered only by whole-stage runs on few scenarios, or on old compositions (B', C, D). The glue's
Lean has still never been run against Python. Its Python wiring is now checked end to end, and its
review has two open high findings, F1 and F2. The fz7_m fuzz still has no receipt.

What w29 left open, and why:
- No evaluation carrier is on `5365851c`, and `eval_decl` refuses the step items, the
  compositions and the glue hosts with the schema error. The pass rules did not allow adding a
  carrier. The needed carrier is an identity `List Int -> List Int` item that depends on the
  units, with digest printers. Ready suites wait for it: fz5_t14, fz6_td15,
  fz10_train_run_03 (X28), fz10_run, fz10_run_py_py, fz7_m, and fz_run_py / x27.
- The isolation hook kept every test agent from reading this report.
- Review findings F1 to F4 are open. F1 concerns a contract clause (PyLinks 10) and F2 concerns
  the boundary text of the public claim.

## Fidelity pass, second attempt (w30), 2026-11-20

Appended record. The text above stays as written. This section records workflow pass w30, which
was allowed to add evaluation carriers, and what followed from it: the restatement of `def:PyLinks`
clause 10 (finding F1), the re-proofs, amendment 3 (findings F2 to F4) and a read-only audit.
Blueprint `5365851c-5549-44b7-9207-4bd4c422031d` (Logos MCP Staging). Everything below is taken
from the agents' returned results; the writer of this section made no Logos or git call.

### What was tested

**Cases, differences, receipts: none in w30.** The test step returned `ok: false` with no
per-unit result. Its only finding is that the carrier step did not finish (below). So w30 compared
**0 Lean cases** against Python, found 0 differences (which is not a pass), and wrote no new
receipt. The receipts dated 2026-11-20 in `migration/port-to-lean/diffeval/receipts/`
(`fuzz_2026-11-20-train-a` to `-train-d`, `-compositions`, `-stale-compositions`,
`-glue-end-to-end`) are the w29 receipts described above. The table "Counts after w29" stands
unchanged: 83 of 100 code units have a unit-level receipt on their current Lean (A + B), 17 do not
(B', C, D), and the glue's Lean has still never been run against Python.

**The carrier step (`ok: false`).**
- `def:zz_carrier_fid_1` was added: Lean `def zz_carrier_fid_1 (xs : List Int) : List Int := xs`,
  source `migration/port-to-lean/diffeval/carrier_fid.py`, accepted at revision `b4d98582`. It
  depends directly on `run`, `run_py`, `run_py_py`, `run_py_py_py`, `PyLinks`, `PyParams`,
  `pyPipeline`, `ScoreRun` and the twelve listed units. Units reached: `train_run_01`, `02`, `03`,
  `04`, `08`, `11`, `13`, `14`, `15`, `confusion_metrics`, `metrics_run_03_thresholds`,
  `metrics_run_05_cumulative_lift`, `run`, `run_py`, `run_py_py`, `run_py_py_py`, `PyLinks`,
  `PyParams`, `ScoreRun`.
- Through it, one `eval_decl` with 21 inputs returned for every target unit and for `PyLinks`,
  `PyParams` and `ScoreRun`, so the schema refusal of w29 is worked around. A second call ran real
  code: `run (α := Float)` on a failed import gives `none`, and `confusion_metrics` on an empty
  frame gives 0 rows and 6 columns. These are probes, not a receipted comparison.
- `pyPipeline` is in scope but cannot run: it is noncomputable (a `Pipeline` over the reals). A
  glue test has to chain the four run items at `Float` itself.
- Then the blueprint changed under the step. After a second `update_item_source` on `def:run`
  (same lines, relative path), `def:PyLinks` read unformalized, and 63 items downstream were
  cleared, the carrier among them (307 formalized, `verification_approved` false). Minutes later
  `PyLinks` was formalized again, `def:zz_carrier_fid_2` appeared (same units, without the PyLinks
  group) and `carrier_fid.py` had been edited, none of it by the carrier step. The carrier step
  could not rule out its own call or a concurrent writer and stopped writing.
- Reading of the two records together: the restatement step (below) reports that its own edit of
  `PyLinks` clause 10, done in the same window, cleared exactly this set (`PyLinks` text then Lean,
  369/370 before, 308/372 after). That fits the clearing seen by the carrier step. Neither step
  claims `def:zz_carrier_fid_2`; who added it is not on record.
- `def:run` stored source: `update_item_source` moved its location to
  `credit_risk/feature_engineering.py` 28-400 (HEAD) but does not change the stored text, which is
  still the version before `4a757fb` (no `_split_draw`, no split-file fit test). Refreshing it needs
  `write_code`, which clears `def:run` and everything that depends on it, so it was left and
  reported. The split logic itself is in `def:fe_run_06_split`, refreshed 2026-11-18.
- Records written by that step: `migration/port-to-lean/update-2026-11-20-carriers.md`; a carrier
  row in `migration/port-to-lean/manifest.tsv` and `run`'s lines changed from 19-380 to 28-400.
  The blueprint location of `fid_1` still says lines 13-14; after the other writer's edit the
  function is at 12-13.

### What is still not covered, and why

- Every unit of class B', C, D and E above. The carrier now exists and `eval_decl` returns through
  it, but no comparison was run in w30: the clearing stopped the carrier step, and the test step
  ran with no carrier result to use. The ready suites (fz5_t14, fz6_td15, fz10_train_run_03 for X28,
  fz10_run, fz10_run_py_py, fz7_m, fz_run_py / x27) still wait. `train_run_11` still needs a digest
  printer, since `Float` prints with 6 decimals.
- The glue's Lean: `pyPipeline` cannot be evaluated; a composed test of the four run items at
  `Float` has not been written.
- `def:run`'s stored Python text stays stale until someone accepts the cost of `write_code`.
- `def:zz_carrier_fid_1` (DefinitionUnformalized after the clearing) and `def:zz_carrier_fid_2`
  are still on the blueprint. The audit found no consumer of either. Both must be removed before
  any close.
- The isolation hook again kept the carrier step from reading this report.

### PyLinks clause 10 restated (finding F1)

- Where the unbounded statement was: `def:PyLinks` clause 10, and one hypothesis of the same shape,
  `hcount` of `lem:metrics_ks_table`
  (`∀ n : Nat, parse_float (sas_best (some n) 8) = n ∧ sas_best (some n) 8 ≠ ""`). The count round
  trip is used only through `lem:metrics_ks_table`, whose consumers are `thm:E8_validation_summary`,
  `thm:E9_ks` and `thm:G4_metrics_coverage` (the counts `total_good`, `total_bad` of
  `metrics_run_02_ks`). Step 05 (`total_defaults`, `overall_default_rate` through `_into_float`)
  feeds only the printed cumulative lift file; no contract uses clause 10 for it. The SAS side and
  `Paired` have no such statement (`SasLinks` has no BEST8 or count clause; the SAS count bound is
  the first clause of `total_good_bad_precond`, fewer than 10^8 rows). Greps for `forall n : Nat`,
  `sas_best (some` and `best8` found nothing else.
- New clause 10: `∀ n : Nat, n < 10 ^ 8 → parse_float (sas_best (some n) 8) = n ∧ sas_best (some n) 8 ≠ ""`,
  with `sas_best none 8 = ""` unchanged. The text was edited first (`edit_text`), then the Lean
  (`edit_statement`); both compiled and the judge accepted. The text cites F1 and the example
  `sas_best(123456789, 8)` = `1.2346E8`. Nothing else in `PyLinks` changed (the audit checked this
  clause by clause, not byte for byte: no copy of the earlier revision `f20bd80e` was at hand).
  The clause is weaker than before and no stronger than the code.
- `lem:metrics_ks_table` (a lemma, not a contract): `hcount` is restated as
  `∀ n : Nat, n ≤ V.length → ...` and moved after `f` and `V`. The number of hypotheses did not
  change. **Choice for review:** the bound is `n ≤ V.length`, not `n < 10^8` plus a new
  `V.length < 10^8` hypothesis, so the lemma gains no hypothesis. It is the one place that goes
  beyond the literal wording "n < 10^8".
- No contract got a new hypothesis.
- Discharging the bound: on valid input the sorted validation score table V has fewer than 10^8
  rows, because it has at most as many rows as the raw training table and `InputOK` (G56) bounds
  that. So n ≤ V.length < 10^8 and clause 10 gives `hcount`. Nothing went to the owner.
- The edit cleared 62 items (statement and proof) plus the proof of `lem:metrics_ks_table` and of
  `lem:ex_port_train_outcomes`; `verification_approved` became false.

### The re-proofs

Cleared items were restored from their stored drafts. Only these proofs changed:
- `lem:metrics_ks_table`: helpers `zinto`, `zgood`, `zkc_facts` take the bounded `hcount` plus one
  inequality each; a helper `zcnt_le` (`zcnt y D ≤ D.length`) was added inside the proof file.
  Accepted first time. Statement untouched.
- `thm:E8_validation_summary`: the fitted-run call of `lem:metrics_ks_table` now gets
  `fun n hn => hCnt n (lt_of_le_of_lt hn hVlt)`, with the row bound from a new in-file helper
  `E8R.read_len` (PyLinks 8 read-backs keep rows; the SAS score chain keeps rows; `Paired` 2 with
  `lem:sas_split_input_ids`; the validation export is a filter of the split; G56 via
  `hOK.1.2.2.2.2`). Readability helpers copied unchanged from `lem:sas_reached_scores_read_shape`.
  Two proof-dependency edges added with `connect`: `lem:sas_reached_feature_shape`,
  `lem:sas_split_input_ids`.
- `thm:E9_ks`: the same argument in an in-file helper `e9_valid_len`; no edge added.
- `thm:G4_metrics_coverage`: `g4_fit_core` takes clause 10 in its new form and
  `xv.length < 10^8`; new in-file helpers `g4_valid_len`, `g4_F2_len`; one edge added,
  G4 → `lem:sas_split_input_ids` (`connect` reported nothing cleared).
- `thm:T1`, `lem:ex_G4_run`, `lem:ex_reached_features_predict`: the clause-10 case of the PyLinks
  witness changed from `intro n` to `intro n _`. Their witnesses round-trip every n, so the bound
  is taken and not used.

Every other item was resubmitted unchanged (statement and proof), because its proof never used
clause 10; positional destructuring of `PyLinks` still matches, as the number and order of
clauses did not change. In the no-model branches of E8, E9 and G4 nothing changed. Several
agents, to unblock their own item, resubmitted unchanged statement drafts of other cleared items
(among them T0, T1, E4, G1, R, `py_scores_valid_empty`, `sas_reached_feature_shape`,
`py_split_input_ids`, `py_split_ids_rowids`, `pr01_clean_frame`, `py_input_check_no_stop`,
`fe_run_06_split_S6a`, `ex_reached_features_predict`); none was reworded.

Not re-proved when the step ended (`ok: false`), each refused only for a dependency then
unformalized, with the stored proof needing no change by the agents' reading:
`lem:ex_port_train_outcomes` (proof edge to S6a), `lem:ex_A3_predict`, `lem:ex_E3_fit`,
`lem:ex_E5_train_scores`, `lem:ex_E7_F2_predict`, `lem:ex_G2_run`, `lem:ex_P0_predict_no_model`,
`thm:fe_run_06_split_S6a` (refused for S6b, which was proved later in the same run, so S6a's stored
draft `01d404e5` can now be resubmitted). Removing the unused proof edge S6a → S6b, or
`ex_port_train_outcomes` → S6a, would change existing items and was not done.

### Amendment 3 (findings F2 to F4)

- `informal-spec.md`: new section "Amendment 3 (2026-11-20, owner): B7, the training split". The
  split is a shared random draw: SAS draws it with PROC SURVEYSELECT (samprate=0.7, seed 42,
  outall, `legacy/feature_engineering.sas:323-327`) with SAS's own generator; the port reads that
  draw from the split_ids file (`feature_engineering.py:352-366`) and otherwise draws with Python's
  `random` (`_split_draw`, :20-25). The claim is equality given that both sides train on the same
  ids, which is `Paired` clause 2, unchanged. The pairing holds on the real 150,000-row file and is
  not claimed elsewhere. B7 is part of the boundary like B4; B1's "on every valid input" is read
  with B7. B1-B6 stand; no item or code changed. This answers F2.
- F3: the 2026-11-20 NaN note in `informal-spec.md` is reworded in place (the draw is reached in
  the real code on every valid input but the one the fixed file fits; `lem:py_split_fits` speaks
  only of the model's `py.split`; the NaN conclusion rests on `lem:py_split_ids_finite` and
  `InputOK`; NaN stays outside the real-number model, B4.4). The first wording is kept, marked
  superseded.
- F4: `definitions-v3.md` has a new top note: `lem:py_split_ids_rowids` and `lem:py_split_fits` are
  `TheoremProved` (checked by `get_items`), against C-k's "stated, not proved"; the C-m heading no
  longer says "latest".
- F1 is answered by the restatement above, not by the amendment.

### The audit (read-only, after the re-proofs; `ok: false`)

- Counts: 372 items, 371 statements formalized, `verification_approved` false. 30 of 30 contracts
  are `TheoremProved` by state, but **18 of them rest transitively on `thm:fe_run_06_split_S6a`,
  which is `TheoremStated`** (no proof submitted since it was cleared). Directly E1, E2; through
  them E3, E5, E6, E7, E8, E9, E10, E11, F2, F3, F4, F6, G2, G4, P0, R. Not resting on it: E4, F1,
  F5, G1, G3, A1, A2, A3, A4, T0, T1, T2. So "every contract proved" does not hold at the time of
  the audit. Fix: prove S6a against the restated `PyLinks`, then re-read the states.
- Not proved or formalized (9): `TheoremStated` S6a, `lem:ex_A3_predict`, `lem:ex_E3_fit`,
  `lem:ex_E5_train_scores`, `lem:ex_E7_F2_predict`, `lem:ex_G2_run`, `lem:ex_P0_predict_no_model`,
  `lem:ex_port_train_outcomes`; `DefinitionUnformalized` `def:zz_carrier_fid_1`. The proved
  `lem:ex_G4_run` and `lem:ex_reached_features_predict` rest on S6a and on
  `lem:ex_port_train_outcomes`, so the existence witnesses for A1, A2, A4, E5, F1 and G4 rest on
  unproved items too.
- Hypotheses (all 30 statements read): each assumes only `PyLinks`, `Paired`, `InputOK` and
  reached-equations or run facts, except E4 (terms of m among the 36 candidates, the spec's own
  wording), A3 and T1 (none), T0 (`PyLinks` only) and T2 (`SasLinks`, `InputOK`,
  `CreditRisk.Fitted`, as its SAS-only scope allows). A public sentence "each contract assumes only
  PyLinks, Paired, InputOK and reached-equations" is not literally true of T2.
- Clause 10 restatement confirmed in the Lean and the text; every other `PyLinks` and `Paired`
  clause matches the verdict table of w29.
- Stale records: `definitions-v3.md:215` (clause 10 "For every whole number n"),
  `definitions-v3.md:239` ("Counts are taken as exact on both sides (clause 10), no bound is
  added"), the new top note of `definitions-v3.md` ("no text or Lean of pyPipeline, PyLinks or
  Paired changed"), and the Lean header comment of `def:PyLinks` (corrections up to C-k only). No
  `.md` record has a C-n / F1 correction entry.
- Trust layers are still off on this blueprint: whether the Lean matches the text rests on reviews,
  not the judge.
- No Logos call of the audit was blocked.

## Fidelity pass, third attempt and close (w31), 2026-11-20

Appended record. The text above stays as written. This section records workflow pass w31: the
re-proofs left open by w30, the unit and composition comparisons run through the evaluation
carrier, the records fix for C-n, and a read-only audit. Blueprint
`5365851c-5549-44b7-9207-4bd4c422031d` (Logos MCP Staging). Everything below is taken from the
agents' returned results; the writer of this section made no Logos or git call.

### The re-proofs (all `ok: true`)

Every item w30 left unproved was resubmitted from its stored draft, unchanged, and accepted with 0
errors. No Lean, statement or hypothesis was changed in any of them, and no hook blocked a call.

| Item | Draft revision | Note |
|---|---|---|
| `thm:fe_run_06_split_S6a` | `01d404e58da74f55894b01761c4decaf` (554 lines) | Dependencies S6b, `lem:py_features_wf`, `lem:py_split_fits`, `lem:py_split_ids_rowids` proved first; `def:PyLinks` `DefinitionFormalized`. Server warning: the proof does not use the declared dependency `lem:py_split_ids_rowids` (stale edge, not acted on). |
| `lem:ex_port_train_outcomes` | `8d7d43b9bfd54d8d999f2e944965548b` (799 lines) | Dependencies `lem:fe05_features_rows`, S6a already formalized. |
| `def:zz_carrier_fid_1` | `b4d98582db0445aaa525d43337b08203` | `DefinitionFormalized` again; accepted `statement_lean` equals the stored text (`def zz_carrier_fid_1 (xs : List Int) : List Int := xs`, comment line citing `carrier_fid.py:13-14`, "harness only; remove at the close"). |
| `lem:ex_A3_predict` | `f0300663d16749d88996e4c6ae32603c` | Depends only on `lem:ex_reached_features_predict` (`TheoremProved`). Tool note: `read_scratch` refused every line range, even 1-40 on a 22-line draft; it returned the draft only without a range. |
| `lem:ex_E3_fit` | `92e77f41` (302 lines) | Dependencies `lem:ex_metrics_run`, T1, T0 proved; `SasLinksOf`, `PyLinks`, `Paired`, `sasPipelineOf`, `PyParams`, `SasParams` formalized. Its training example has 4 rows, so clause 10 (n < 10^8) does not touch it. |
| `lem:ex_E5_train_scores` | `d9419bbf3b9c4c4ba65519e4712343e8` (35 lines) | Used dependencies `lem:ex_reached_features_predict`, E1, E3, `lem:ex_E3_fit` proved. Server warning (pre-existing): unused declared dependencies `lem:ex_metrics_run`, `lem:ex_G4_run`, T0, `lem:sas_features_some_paired`. |
| `lem:ex_E7_F2_predict` | `03f791109a33402283358cb7571bf09e` | Depends only on `lem:ex_reached_features_predict`; accepted first try. |
| `lem:ex_G2_run` | `2921c6d74a2e4eae9c4bb0690ed433c8` | Uses only `lem:ex_G4_run` (both conjuncts, score equations dropped). Server warning: unused declared dependencies T1, T0, E1, `lem:sas_features_some_paired`, `lem:ex_A1_run`. |
| `lem:ex_P0_predict_no_model` | `1c5c7f31` (13 lines) | Only dependency `lem:ex_metrics_run` proved. |

The unused-dependency warnings are about the dependency lists only; removing those edges would
change existing items and was not done.

### What was tested (per unit)

All evaluation ran through `def:zz_carrier_fid_2` with `eval_decl`, Lean against the port at HEAD
`4a757fb`. "Compared" counts kept (in-precondition) cases; "known limit" counts differences each
shown to be wholly explained by a cited RULEBOOK section 6 limit.

| Test | Item | Compared | Differences | Known limit | Verdict |
|---|---|---:|---:|---:|---|
| train-a | `def:train_run_01_fit_frame` | 2473 | 461 | 0 | **FINDING** (m2ll0 NaN vs 0.0) |
| train-a | `def:train_run_02_stepwise_summary` | 2400 | 0 | 0 | PASS |
| train-a | `def:train_run_04_score_train` | 2424 | 2 | 2 | KNOWN-LIMIT (last bit of exp) |
| train-b | `def:train_run_03_fit_global_rsquare` | 2285 | 0 | 3 | PASS with 3 known-limit cases (last bit of exp); as returned, "diff 0, knownLimit 3" |
| train-c | `def:train_run_08_ctable` | 2950 | 0 | 0 | PASS |
| train-c | `def:train_run_11_confusion_valid` | 2018 | 0 | 0 | PASS |
| train-d | `def:train_run_13_roc` | 2068 | 0 | 0 | PASS |
| train-d | `def:train_run_14_final_and_summary` | 2907 | 0 | 0 | PASS |
| train-d | `def:train_run_15_printed_roc` | 2247 | 0 | 0 | PASS |
| metrics | `def:confusion_metrics` | 2356 | 0 | 0 | PASS |
| metrics | `def:metrics_run_03_thresholds` | 2326 | 0 | 0 | PASS |
| metrics | `def:metrics_run_05_cumulative_lift` | 2408 | 13 | 13 | KNOWN-LIMIT (running sum from -0.0) |
| metrics | composition fz7_m re-run (metrics_run_01/02/04 widened, 03/05-10 chained) | 2000 | 0 | 0 | PASS |
| compositions | `def:run_py` (metrics_calculation.run, whole) | 2099 | 76 | 76 | KNOWN-LIMIT (signed zeros, min/max) |
| compositions | `def:run_py_py_py` (train.run, whole) | 2113 | 4 | 4 | KNOWN-LIMIT (last bit of exp) |
| stale-compositions | `def:run` (fz10_run) | 2322 | 0 | 0 | PASS |
| stale-compositions | `def:run`, four log columns at full bits | 2314 | 0 | 0 | PASS |
| stale-compositions | `def:run_py_py` (fz10_run_py_py) | 2300 | 1 | 1 | KNOWN-LIMIT (last bit of exp) |
| stale-compositions | `def:run` on real data | 6 | 0 | 0 | PASS |
| stale-compositions | `def:run_py_py` on real data | 1 | 0 | 0 | PASS |
| glue | fe: `def:run` (pyPipeline.features), all 3 files | 807 | 0 | 0 | PASS |
| glue | train: `def:run_py_py_py` (pyPipeline.fit), every file | 588 | 0 | 0 | PASS |
| glue | model.json (intercept, coefficients) | 588 | 0 | 0 | PASS |
| glue | predict: `def:run_py_py` (pyPipeline.scoreTest), every file | 588 | 0 | 0 | PASS |
| glue | metrics: `def:run_py` (pyPipeline.metrics), every file | 588 | 0 | 0 | PASS |
| glue | ScoreRun S1 vs `risk_scores_train.csv` | 588 | 0 | 0 | PASS |
| glue | ScoreRun S2 vs `risk_scores_validation.csv` | 588 | 0 | 0 | PASS |
| glue | real-data sample (`legacy/data`) | 7 | 0 | 0 | PASS |

Totals as returned: 46,359 compared cases; 557 differences, of which 96 are known-limit (plus the 3
known-limit cases train-b counts outside its differences, 99 in all) and **461 are unexplained, all
in `def:train_run_01_fit_frame`**. Test steps: train-a `ok: false`; train-b, train-c, train-d,
metrics, compositions, stale-compositions, glue-end-to-end `ok: true`.

Per-unit notes, as returned:
- `train_run_01_fit_frame`: all 461 differences are one value, m2ll0, when `intercept_only` is
  None (no fit, which the precondition allows): Python NaN, Lean 0.0. Everything else matches on
  all 2473 kept inputs; all 727 rejected inputs also match (narrowings). Real data: 3 windows of the
  real feature file with the real stepwise result match. Python is `train.py:55-111`, executed.
- `train_run_02_stepwise_summary`: 2400 of 2400 kept (no precondition item); covers 0-6 steps,
  names cut at 20 characters (accent, emoji), None/NaN wald, None final (470), empty tables (260).
  Formatters are injective stand-ins, the same on both sides. Real data: the 19 real steps (2
  removals) with the real final model match. `train.py:117-157`.
- `train_run_04_score_train`: of 4000 generated, 2424 kept, 876 rejected, 700 dropped (Python
  raises outside the precondition), 0 raise inside it. Seeds 102291 and 103385 differ: Lean's
  `Float.exp` of -eta is one ulp below polars'. Python recomputed with Lean's exp equals the Lean
  digest. At least 234 rejected inputs match (narrowings). Real data: 3 windows with the real
  16-parameter final model match. `train.py:297-324`.
- `train_run_03_fit_global_rsquare`: seeds 0..2999; 2284 kept, 1 linalg, 533 dropped, 182 rejected.
  2281 kept seeds and linalg seed 1792 equal; seeds 136, 1493, 1846 differ only in
  `printed_rsquare.csv` (cox_snell / nagelkerke), one ulp of exp. X28 singular path reached by 1001
  kept cases (998 equal plus the 3 known-limit cases). Real data NOT-RUN (105,000 x 16 fit frame).
- `train_run_08_ctable`: suite fz10c_ct (2308 kept, stand-ins FMT, INV, SOLVE, DOT, MATMUL, MATVEC,
  EINSUM, LOG1P identical on both sides; 15 rejected inputs match; 277 dropped); fz10c_ctw (640
  kept, exact routines, wide designs of 2-5 predictors, no zero pivots); real fz10c_ctr rows 0..39
  and 104960..104999, exact routines, PASS. `train.py:479-535`.
- `train_run_11_confusion_valid`: fz10c_cv 2006 kept, 0 differences, 394 rejected match; real
  fz10c_cv_real: all 45,000 real rows of `logit_scored_valid` in 4 consecutive windows, 12 digests,
  PASS. `train.py:640-700`.
- `train_run_13_roc`: suite fz10_td13, 145 cases (25 seeds each), PASS; new suite for the 4-value
  return, adds the x27 no-`default_flag` validation case (139 kept); 1557 seeds outside the
  precondition counted, not compared. Real: first 80 rows of each scored set. `train.py:803-830`.
- `train_run_14_final_and_summary`: fz10_td14_m (fz5_t14 inputs, expected values recomputed and
  identical to 2026-11-18), 10 cases, 2907 kept plus 93 rejected that return, all equal. Real: real
  coefficients, metrics, ROC frames and flags, scored sets cut to their first row.
- `train_run_15_printed_roc`: fz10_td15 (regenerated, identical to 2026-11-18), 8 chunk folds, PASS;
  553 seeds outside the label-null narrowing not compared. Real: exact real inputs.
- `confusion_metrics` / `metrics_run_03_thresholds`: fz10c_cm and fz10c_th, 54 of 54 block cases
  each, 79 rejected (Boolean `default_flag`) equal; real 5 windows of 60 rows x 7 thresholds (35 of
  35) and 5 of 5 windows.
- `metrics_run_05_cumulative_lift`: fz10c_lift, 78 block cases, 65 equal; the 13 differing cases
  are exactly the 13 "zeros" family cases (325 seeds with -0.0 in the defaults pool); fz10c_lift_nz
  (same seeds, -0.0 cleared on both sides) 13 of 13 equal. Real: the WHOLE real decile_data (45,000
  rows) and decile_analysis, valid_exists true and false, 2 of 2 equal.
- fz7_m composition: fz10c_m, seeds 8200000..8201999, 80 of 80 block cases; 155 seeds with an empty
  validation frame, 220 with an empty training frame (06 rejected, compared, equal).
- `run_py`: 2,063 kept seeded runs plus 36 real cases; 1,987 seeded runs bit-exact; 76 differ only
  in `decile_analysis.csv` and `printed_cumulative_lift.csv`, equal when zeros compare unsigned
  (smallest: seed 7000137, decile row 7 max_pd, Python 0.0, Lean -0.0). Real: 36/36.
- `run_py_py_py`: 2,089 kept seeded runs plus 24 real; 2,085 equal; seeds 3000515, 3000862, 3001524,
  3002004 differ only in pd_logistic of `risk_scores_train.csv` and `final_model_output.csv` at
  eta = -3.625 (polars exp(3.625) not correctly rounded); Python with a correctly rounded exp gives
  the Lean digest on all 4. Real: 3 windows, 8 stepwise stand-ins each, 24/24.
- `run` (stale): 2307 kept cases plus 15 rejected (narrowings) all PASS; draw branch reached by 647
  kept completed seeds (555 non-identity). Log columns at full bits: 2314/2314 over 29,888 values.
  Real: 6/6 (mixed, complete, edge slices, each with the restricted and the fitting split file).
- `run_py_py` (stale): 103/104 blocks; seed 2002107, `Float.exp(59.8997662095086)` one ulp from
  polars (predict.py:393), recomputation gives the Lean digest 5069487142773800831. Real: 1/1.
- Glue: 804 seeded small inputs, 2 fitted mkB seeds, 1 real sample (seed 90000000, rows 1-30 of
  `cs-training.csv`, 1-20 of `cs-test.csv`); 588 chained runs (495 stops, 80 no-fit, 10
  intercept-only, 3 with variables); 219 seeds where Python train raises excluded from the chained
  rows (outside the train precondition), their fe files compared. Because `def:pyPipeline` is
  noncomputable, the eval term rebuilds the `PyLinks` wiring from the `def:train_run_*` items.

### Receipts

- train-a: `migration/port-to-lean/diffeval/receipts/fuzz_2026-11-20c-train-a.tsv`; generators
  `diffeval/units/fz10c_train_a_gen.py`, `fz10c_train_a_real.py`; work
  `diffeval/work/fz10c_ta01|02|04|_real.{json,inputs.json,out.txt}`, `fz10c_ta04.loc.inputs.json`,
  `fz10c_ta04.exp.inputs.json`.
- train-b: `receipts/fuzz_2026-11-20c-train-b.tsv`; `units/fz10c_train_run_03_gen.py`,
  `fz10c_train_run_03_explain.py`; `work/fz10c_train_run_03.sweep_0_3000.out.txt`,
  `fz10c_train_run_03.per_120_1470_1830.out.txt`.
- train-c: `receipts/fuzz_2026-11-20c-train-c.tsv` (by `units/fz10c_train_c_receipt.py`;
  generators `fz10c_train_gen.py`, `fz10c_ctw_gen.py`, `fz10c_real11_gen.py`,
  `fz10c_real_capture.py`).
- train-d: `receipts/fuzz_2026-11-20c-train-d.tsv` (generator `units/fz10_traind_gen.py`; work
  `fz10_td13.*`, `fz10_td14_m.*`, `fz10_td15_c.*`, `fz10_td_real.*`).
- metrics: `receipts/fuzz_2026-11-20c-metrics.tsv` (18 rows, by `units/fz10c_receipt.py`;
  generators `fz10c_metrics_gen.py`, `fz10c_m_gen.py`; compare.py: cm 54/54, th 54/54, lift 65 PASS
  + 13 FAIL (zeros family), lift_nz 13/13, real 48/48, m 81/81).
- compositions: `receipts/fuzz_2026-11-20c-compositions.tsv` (generators `fz10c_run_py_gen.py`,
  `fz10c_train_run_gen.py`, `fz10c_common.py`, `fz10c_collect.py`, `fz10c_train_run_exp_check.py`;
  results `work/fz10c_run_py*.result.json`, `fz10c_train_run_{a,b,c,real,diag}.json/.out.txt`,
  `fz10c_train_run_exp_check.out.txt`).
- stale-compositions: `receipts/fuzz_2026-11-20c-stale-compositions.tsv` (by
  `units/fz10c_stale_receipt.py`; suites fz10_run, fz10_run_py_py, fz10c_run_logbits,
  fz10c_stale_narrow, fz10c_stale_real_run, fz10c_stale_real_pp; scripts `fz10c_stale_collect.py`,
  `fz10c_run_logbits_gen.py`, `fz10c_stale_narrow_gen.py`, `fz10c_stale_explain.py`,
  `fz10c_stale_drawcount.py`, `fz10c_stale_real_gen.py`).
- glue: `receipts/fuzz_2026-11-20c-glue-end-to-end.tsv` (generator `units/fz10c_glue_gen.py`; work
  `fz10c_glue_{A,B,C,R}.*`).

### What is still not covered, and why

- `def:train_run_01_fit_frame` does not equal the port on the no-fit case (finding below); nothing
  was fixed.
- Real data at full size is not reached for any unit whose real input is the 105,000- or
  150,000-row frame (`train_run_03` NOT-RUN; `train_run_01`, `04`, `08`, `13`, `14`, `run`,
  `run_py_py`, glue on windows or slices), because one `eval_decl` input is one literal term.
  `train_run_11` (45,000 rows) and `metrics_run_05` (45,000 rows) got every real row; `confusion_metrics`
  and step 03 got 5 real windows of 60 rows. `train_run_11` times out on 45,000 rows in one call
  (superlinear under `eval_decl`).
- Seeds generated and not sent: glue 53 NOTHELD, 421 pickled seeds (327 intercept-only, 60 no-fit,
  34 fitted big) and 5 real seeds; stale 9 larger real slices (6 `run`, 3 `run_py_py`); compositions
  37 + 9 not held, 2 pow2 mismatches.
- Generated pools of step 14 stop at 1e22 and do not approach its 1e76 precondition bound.
- Library preconditions not rendered by `def:run_py_py_py_precond` (association_table,
  hosmer_lemeshow, classification_table, roc_association, merge_one_to_one) are taken as holding
  whenever Python returns.
- `def:run`'s stored Python text is still the pre-`4a757fb` version; the tests ran against the
  current Python and its Lean calls the refreshed `def:fe_run_06_split`.
- No test step covered the units of class B', C, D and E other than those in the table; the counts
  table "Counts after w29" is not recomputed here.

### Findings, verbatim

train-a:
1. FINDING def:train_run_01_fit_frame: m2ll0 differs when intercept_only is None. That case is inside def:train_run_01_fit_frame_precond (no step, no fit). Python train.py:110 gives math.nan, bits 9221120237041090560. The Lean returns 0.0, bits 0; its comment says 'placeholder, lead's decision'. No RULEBOOK rule covers this: R-NULLNAN maps such a NaN to Option, and the item does not. It affects all 461 kept no-fit seeds. Smallest input: StepwiseResult() and a frame with the 36 candidates plus default_flag, one row, all 0.0. Lean returns n_obs, m2ll0 bits, ybar bits = [1, 0, 0]; Python gives n_obs 1, m2ll0 nan, ybar 0.0. Nothing was fixed.
2. KNOWN-LIMIT def:train_run_04_score_train, RULEBOOK section 6 'the last bit of exp', 2 of 2424 kept inputs. Seed 102291: exp of bits 4617753861988428212 (5.389327705032361) is ...692 in Lean and ...693 in polars. Seed 103385: exp of bits 4620133209533684866 is ...903 in Lean and ...904 in polars. The Python result recomputed with Lean's exp equals the Lean digest on both seeds (that check also ran in Lean and returned []).
3. Method change from the README: outputs could not be collected from the session record by script. Searching the session's records was denied by the permission classifier. So every verdict is computed inside Lean: the input carries the Python digests per block of seeds, and Lean returns only counts and the indices of differing blocks or seeds. Those short outputs (for example [2400, 0, -1, -2, -3]) were copied into work/fz10c_ta0*.out.txt by hand. Large outputs were never typed.
4. Real data comes from the port's feature file in work/fz10_trainb_real/model_features_train.csv (105,000 rows, written from legacy/data at HEAD by the train-b generator), with a REAL stepwise run (cached in work/fz10c_ta_real.pkl). The full frame does not fit in an eval input, so units 01 and 04 were checked on 3 windows of 10 real rows in total, chosen as the first rows plus the rows with the largest and smallest |eta|. The real data has no null rows, so fit_mask is true everywhere on it.
5. No Lean item, statement or proof was changed or written. Every eval used def:zz_carrier_fid_2 (it was DefinitionFormalized during the run) on blueprint 5365851c-5549-44b7-9207-4bd4c422031d.

train-b:
1. No unexplained difference: the current Lean of def:train_run_03_fit_global_rsquare computes what the current train.py:163-292 computes on 2282 of 2285 compared cases (2281 kept and 1 linalg), bit for bit.
2. KNOWN-LIMIT (RULEBOOK.md, Known limits of the model, 'Outside the model altogether: the last bit of exp and log' and the 'last bit of exp' bullet): seeds 136, 1493 and 1846. Lean Float.exp and CPython math.exp differ by one ulp on 104.60714285714286 (already recorded for seed 136), 690.125 and 3.625. The Lean value is the correctly rounded one each time. Substituting the Lean exp into the Python reproduces the Lean digests exactly. Smallest case: seed 1846 (n_obs 1, exp argument 3.625).
3. Two of the three exp arguments (690.125 and 3.625) are new examples for the RULEBOOK's exp last-bit bullet. It records only seed 136 for this unit. Updating the bullet is for the lead; nothing on the blueprint was written.
4. Real data not reached: the unit builds x_k from fit_frame itself, so no parameter can stand in for it, and the real frame is 105,000 rows by 15 fit columns, about 1.6 million floats. That is far too large for one eval_decl input. Its sub-units' real-data calls (_kept, _solve_sas, _left_out at the last real stepwise step) are already PASS in diffeval/receipts/fuzz_2026-11-20-train-b.tsv.
5. No hook block stopped the work. One shell heredoc edit was refused by the isolation hook ('may not read migration'); the same edit was then made with the Edit tool. No Lean item, statement or proof was written.

train-c:
1. No FINDING: every Lean output equalled the Python output bit for bit, with no KNOWN-LIMIT cases, in all 5 suites (fz10c_cv, fz10c_ct, fz10c_ctw, fz10c_cv_real, fz10c_ctr).
2. Not reached: train_run_11_confusion_valid on the whole real 45000-row frame in one eval_decl call. The call timed out because the unit's Lean is superlinear in rows under eval_decl (measured: 2000 rows 0.4 s, 12000 rows 2.8 s, 24000 rows 31 s). Every real row was still evaluated, in 4 consecutive real windows, all PASS.
3. Not reached: train_run_08_ctable on its real input. The real fit_frame is 105000 x 16 columns, about 1.7M floats, far beyond what an eval_decl input can carry, and step 11 already times out at 45000 x 2. Two real 40-row windows (rows 0..39 and 104960..104999) were evaluated with the exact routines, both PASS. In them the fit covariance was reduced to its diagonal; the generator asserts the Python result is identical with the full covariance.
4. The step 08 suites fz10c_ct and fz10c_ctr use explicit-parameter stand-ins (RULEBOOK section 3) that are identical on both sides. So fz10c_ct checks the step's own logic, not numpy's numerics. fz10c_ctw and fz10c_ctr use the exact model routines.
5. Hook: one Bash call was blocked because it lacked the required cd prefix. I re-ran it with the prefix. The block did not stop any work.

train-d:
1. No FINDING. The current Lean of all three items matches the current Python (port/ HEAD) bit for bit on every compared case: 7222 seeded inputs plus 3 real-data cases.
2. Nothing blocked me. Every evaluation ran through def:zz_carrier_fid_2. No Lean item, statement or proof was written.
3. Harness note for other agents: on this blueprint, dot notation on a value of type Pl.Frame now resolves `.filter` and `.drop` to Pl.Frame methods (row filter by expression, drop columns by name), not to the List ones. Old suite texts that use `frame.drop n` or `frame.filter (fun p => ...)` on a Pl.Frame fail with 'did not elaborate'. Use `List.drop` / `List.filter` explicitly. This is why fz6_td15 needed the fix.
4. Real-data limit for train_run_13_roc: the step's real inputs are the whole scored sets (105000 and 45000 rows). As Lean literals they are several MB, too large for one eval_decl input, so the real check covers an 80-row prefix of each set (5 and 2 events). For step 14 the scored sets were cut to their first row; the unit only drops and keeps columns there, so the rows are independent. Step 15 ran on its exact real inputs.
5. Generated inputs reach the 0-row edge, NaN, +-inf, -0.0, subnormals and 1-ulp neighbours. They do not reach the 1e76 magnitude bound in step 14's precondition (pools stop at 1e22).

metrics:
1. No unexplained difference. The CURRENT Lean of def:confusion_metrics, def:metrics_run_03_thresholds and def:metrics_run_05_cumulative_lift, and of the fz7_m composition, computes bit for bit what port/ at HEAD 4a757fb computes. All evaluation went through def:zz_carrier_fid_2. The only exception is 13 KNOWN-LIMIT cases of step 05, the RULEBOOK section 6 running-sum-from--0.0 limit; suite fz10c_lift_nz shows it accounts for the whole difference (13/13 equal once -0.0 is cleared).
2. Narrowings, reported and not errors. confusion_metrics_precond and metrics_run_03_thresholds_precond reject a Boolean default_flag, but Python returns on it and Lean equals Python (79 of 79). metrics_run_05_cumulative_lift_precond rejects a Float64 total_count, but Python returns and Lean equals Python (194 seeds). metrics_run_06_psi rejects an empty training frame inside the composition, and Lean equals Python (220 seeds).
3. Not reached, and why. confusion_metrics and step 03 did not get the whole 45,000-row real validation frame: pd_logistic is 41,277 distinct full-precision doubles, about 0.7 MB of input text, and every input is typed by hand into eval_decl. They got 5 real windows of 60 rows each instead (import order, end of the sorted frame, and windows around pd 0.3/0.5/0.7). Step 05 got the whole real input.
4. Process: a block by the hook. fuzz_collect.py and fz10_collect.py need the session record, which this role may not read. So I transcribed outputs from my own eval_decl results into work/<suite>.out.txt. Every case digests its input frames, and the real-data and table inputs carry input-check digests, so a typo shows up as a failure, never as a false pass. One mistyped 9,000-character flag string did fail its check; I re-encoded that input more compactly and the re-run passed its check.
5. No Lean item, statement or proof was changed, and nothing was written to the blueprint. The only writes are under migration/port-to-lean/diffeval: generators, work files and the receipt.

compositions:
1. The current Lean and current Python (HEAD 4a757fb) match for def:run_py and def:run_py_py_py. No difference outside a cited RULEBOOK 6 limit: 80 differences in all (76 signed-zero min/max, 4 last bit of exp). Each was localised to a file and column and reproduced. No Lean item, statement or proof was changed or written.
2. Side effect to disclose: early in this pass, importing diffeval/units/t16_gen.py ran its main() and regenerated /Users/cristophersalvi/GitHub/credit-risk-migration/migration/port-to-lean/diffeval/work/t16_run.json, t16_run.inputs.json and t16_run.in0-3.txt, which now carry today's date. Those files changed only because of this. Afterwards the needed pieces were copied into diffeval/units/fz10c_common.py.
3. Not covered by this label: the glue (pyPipeline is noncomputable, so the glue chains the four compositions at Float). It is not one of this label's two items, and this pass did not run it.
4. Eval quirk, not a fidelity issue: one diag input that defined both `one` and `oneL` did not elaborate. The same input without the unused `one` ran. The two seeds were localised with that version.
5. The hook blocked one Bash command (a heredoc edit combined with `time`, message 'may not read migration'). I redid the edit with the Edit tool. The block did not stop any work.
6. Coverage limits: library preconditions that def:run_py_py_py_precond does not render (association_table, hosmer_lemeshow, classification_table, roc_association, merge_one_to_one) are taken as holding whenever Python returns. The rendered precondition rejected no seed, so there is no data on narrowing.

stale-compositions:
1. No unexplained difference. def:run matches the current Python bit for bit on all 2322 generated cases, on the four log columns at full bits (2314 seeds, 29,888 values) and on 6 real-data cases, including 647 kept seeds and 3 real slices that go through the seeded draw of the refreshed def:fe_run_06_split.
2. def:run_py_py: 2299 of 2300 kept seeds and the real-data slice match. The one difference is seed 2002107, where Float.exp(59.8997662095086) differs from polars by 1 ulp. That ulp is shown to account for the whole digest difference. KNOWN-LIMIT under RULEBOOK section 6 (last bit of exp, outside the model).
3. The fz10 suites were regenerated from port/ at HEAD 4a757fb in this pass and are byte-identical to the stored ones, so the expected values are the current Python's. def:run's stored Python text is still the pre-4a757fb version (write_code would clear the Lean); its Lean calls the refreshed def:fe_run_06_split, and the tests run against the current Python.
4. Not reached: 9 real-slice cases (the larger slices: 6 for run, 3 for run_py_py) are generated but were not evaluated, to keep the hand-transcribed eval_decl inputs within this agent's budget. The whole real files (150,000 / 101,503 rows) are too large for one eval_decl input.
5. Harness collision: another agent overwrote diffeval/units/fz10c_collect.py, which I had created, with a different interface. I left their version in place and used my own diffeval/units/fz10c_stale_collect.py. No hook block stopped the work. Nothing was written to the blueprint.

glue-end-to-end:
1. No FINDING. Every compared value is bit-exact: 807 seeds and 4,335 digested values (A 3,684, B 630, C 14, R 7). No KNOWN-LIMIT from RULEBOOK §6 was needed.
2. Two harness defects were found and fixed on the comparison side; neither is in the port's Lean. (1) The Lean read-back RB treated a number written as empty text (+-inf under BEST12.) as a non-empty text cell. The asserted Python mirror drops such a value from the window like a missing value. Because of this, the first call B had 4 of 5 chunks differing (seeds 3000006, 3000012, 3000047, 3000056, 3000077, 3000091, among others). After the fix, B matches in all 5 chunks. (2) The out-of-scope SB/IB tables (sas_best12 / input_best32) only covered the fz_run_gen pools. For the real-data seed they were extended with the real sas_best12 text and its input_best32 value; the first R run differed, the second is 7 of 7 equal.
3. Seeds not compared: 53 seeds whose frame the CSV cannot hold (NOTHELD). Also 421 pickled seeds that were never sent (327 intercept-only, 60 no-fit, 34 fitted big seeds) and 5 further real-data seeds, because of eval input size and context budget. Their Python pickles and generator are ready: run fz10c_glue_gen.py lean <name> <seeds>.
4. The full real data could not be run in Lean (150,000 rows; eval_decl takes one literal term). The largest sample used is 30 training rows and 20 test rows.
5. No hook block stopped the work. Nothing was written to the blueprint; the only Logos call used was eval_decl.

### Records (C-n), `ok: true`

Records only, no Logos write, no git, no block. In `definitions-v3.md`: clause 10 of `PyLinks` ("For
every whole number n, zero or more", "taken as exact", "InputOK gets no row bound") struck through
and marked superseded by C-n ("below 10^8"; matches the real port, H14/E17, e.g.
`sas_best(123456789, 8) = 1.2346E8`; the bound comes from `InputOK`, G56 made formal, B2/B3); the
G56/D4 note ("Counts are taken as exact ... no bound is added") struck through and superseded; the
2026-11-20 F4 top note's "no text or Lean of pyPipeline, PyLinks or Paired changed" struck through
and headed "before C-n"; a new top change note naming C-n as latest; C-m heading now "before C-n";
a new section "C-n, 2026-11-20 (latest; fidelity finding F1)" (why, what changed incl. the
`lem:metrics_ks_table` `hcount` bound `n <= V.length` left for review, where the bound is
discharged in E8, E9, G4, and a post-audit state paragraph). In `informal-spec.md`: one change note
"2026-11-20 (correction C-n of definitions-v3.md; fidelity finding F1)" before amendment 2's note.
Two things the step flagged: (1) the bound is proved by in-file helpers (`E8R.read_len`,
`e9_valid_len`, `g4_valid_len` / `g4_F2_len`), not by a blueprint lem item, and C-n names them; (2)
the Lean header comment of `def:PyLinks` still lists corrections up to C-k only, which needs a
Logos write this step excluded. The step took its facts from this report and did not re-read the
blueprint, so its "post-audit state" paragraph (18 contracts resting on a `TheoremStated` S6a)
describes the state before the w31 re-proofs.

### The audit (read-only, after the re-proofs; `ok: true`)

Counts, as returned: Blueprint 5365851c (py-credit-risk-port), read only on Logos MCP Staging, nothing written. get_status: 372 items, 372 statements formalized, statements_to_write=[], proofs_to_write=[], waiting=[], verification_approved=true. Per-item state from get_items over all 372 ids: 203 DefinitionFormalized and 169 TheoremProved (76 thm: + 93 lem:). 0 items in any other state. Contracts: 30 of 30 present and TheoremProved (E1-E11, F1-F6, G1-G4, A1-A4, T0-T2, P0, R). Consumers of def:zz_carrier_fid_1 and _2: 0 statement consumers and 0 proof consumers each (both are roots).

Findings, verbatim:
1. (1) PASS. No item is in a state other than TheoremProved or DefinitionFormalized. Every one of the 372 states was read item by item, not taken from the get_status totals.
2. (2) PASS within this blueprint. All 30 contracts are TheoremProved. get_graph parents_of the 30 shows their statement and proof dependencies (for example E7 -> R -> {A1, A3, T0, E1, E2, E3, E5, G1-G4, ...}). Every item in this blueprint is TheoremProved or DefinitionFormalized, so the transitive closure inside 5365851c holds no unproved item. LIMIT: get_graph does not show declarations that come through the profile from sas-credit-risk-spec 3f5df696 and credit-risk-requirements 006ff04c (sasPipeline, SasLinks, CreditRisk.InputOK, CreditRisk.Fitted, the SAS units). Their state was not checked here because this task was scoped to the port blueprint. A public claim should cite the sign-off state of those two blueprints separately.
3. (3) PASS, with notes. Each contract assumes only PyLinks, Paired, InputOK and reached-equations. Several assume fewer: G1-G4, A1, A2 and R have no Paired; T0 and T1 have no input; A3 has no hypothesis at all (any m, test, train). T2 assumes SasLinks + InputOK + CreditRisk.Fitted + hFt (Ft written as sasPipeline builds it), which spec section 6 allows. A1 and A2 take as reached-equations that the stage returned (run = some files, run_py_py_py = some (files, mj)). E8-E11, F5, F6, A4 and G4 take the run hypothesis ScoreRun with hF. P0 takes hF + hfit = none. E4 has one more premise: 'every term of m names one of the 36 candidates'. It is quantified over every such m, so the statement is wider than reached m, not narrower, and it is the restated E4 text of spec section 2 (B1), but it is not literally a reached-equation. No contract has a unit precondition, a wf_ domain or a SasLinks clause.
4. (4) PASS. def:zz_carrier_fid_1 and def:zz_carrier_fid_2 have no statement or proof consumers. But both are still in the blueprint, and their own Lean comment says 'harness only; remove at the close' (identity functions on List Int, statement_text is Python from migration/port-to-lean/diffeval/carrier_fid.py). For a public announcement of a closed blueprint they should be removed, or explained in the announcement.
5. FINDING (substantive, wording): the port's training score table without a model is written three different ways, and no item in the blueprint proves the three are equal. (a) PyLinks clause 7b's noFitTrain and A4's hRun: train_run_12_risk_scores s09.1 s09.1, the final fit of step 01, and the risk frame in all seven step-14 places. (b) G4's hRun and R's no-model branch: train_run_12_risk_scores s09.1 [], with none and [] fillers at step 14. (c) E5, A2(3) and F3: the chain at py.fit (py.readFeatures F1), the real fit result, not {} : StepwiseResult. G4's own comment admits that independence from the fillers 'is a fact about steps 12 and 14, not given by lem:py_score_fillers_idle'. E5 quantifies over every filler, but at py.fit (...), not at {}. PyLinks 6 gives steps=[], final=none and intercept_only=none on one outcome; it does not give py.fit (...) = {}. Consequence: on the run without a model, R and G4 speak of the S1 spelled as (b), A4 of the S1 spelled as (a), and the real train stage writes the table of (c). That all three are the same table is plausible but not proved in the blueprint. A public text should say this, or a lemma should close the gap.
6. CAVEAT for the public text: open_blueprint reports trust_layers=[] ('Every trust layer is off: Lean you write for code is accepted once it compiles, neither judged nor fuzzed against the source'). That the Lean of the port units and definitions matches the Python and SAS sources therefore rests on the project's own reviews and the local diffeval fuzz receipts, not on Logos. Spec D7 says the same ('Judging stays off on 5365851c').
7. CAVEAT for the public text: the claim is conditional on the boundary B1-B7. Under B7 (amendment 3, 2026-11-20), the equality holds only given that both sides train on the same split ids (Paired clause 2). On valid inputs other than the real 150,000-row file, the real programs may train on different rows. Also, informal-spec.md (which carries amendment 3) and the 2026-11-19 final report are modified in the working tree and not committed (git status at session start).

### State at the close of w31

- Proofs: all 30 contracts `TheoremProved`, all 372 items formalized, `verification_approved` true
  (audit). The w30 audit's blocker (18 contracts on an unproved S6a, seven `ex_` lemmas) is gone.
- Fidelity: one open FINDING, `def:train_run_01_fit_frame` m2ll0 (Lean 0.0 where the port gives NaN
  on the no-fit case, 461 of 2473 kept inputs, no RULEBOOK rule covers it; the Lean comment calls
  it a "placeholder, lead's decision"). Every other compared case is equal or wholly explained by a
  RULEBOOK section 6 limit.
- Open for the lead and the owner: the train_run_01 finding; the three spellings of the no-model
  training score table (audit finding 5); removal or disclosure of `def:zz_carrier_fid_1` and
  `_2`; the stale `def:PyLinks` Lean header comment; the stale `def:run` stored Python text; the
  stale unused-dependency edges (S6a → `lem:py_split_ids_rowids` and those listed above); new exp
  examples (690.125, 3.625) for the RULEBOOK bullet; the SAS-side blueprints' sign-off state for a
  public claim; the t16 work files regenerated as a side effect; committing the working tree.

### w31 restart: second audit, 2026-11-20 (appended)

Appended record. The w31 workflow was restarted after an interruption. On the restart the
re-proof, test and records steps returned the same results as recorded above in this section (same
draft revisions, same counts, same findings, same receipts), so nothing above is repeated or
changed. The audit step ran again (read-only, after the re-proofs, `ok: true`) and returned a
different scope and different findings; its result is recorded here verbatim. Where it disagrees
with the first audit above, both stay on record and neither is resolved here.

Counts, as returned: Port blueprint 5365851c: 372 items, 372 statements formalized, nothing left to prove. Per-item state was read for all 372 with get_items: every item is TheoremProved or DefinitionFormalized, so there is no item in any other state to list. All 30 contracts are TheoremProved. The dependency closure of each contract stays inside an all-proved set. The profile blueprints are also complete: SAS spec 3f5df696 151/151, requirements 006ff04c 60/60, foundation 02011d57 17/17, each with nothing left to write or prove. def:zz_carrier_fid_1 and def:zz_carrier_fid_2 each have 0 statement consumers and 0 proof consumers. Nothing was written.

Findings, verbatim:
1. (1) get_status: total_items 372, statements_formalized 372, no statements or proofs left to write, nothing waiting. Per-item states read for all 372 items: every item is TheoremProved or DefinitionFormalized. No item is in another state, so there is nothing to list.
2. (2) All 30 contracts are TheoremProved: E1-E11, F1-F6, G1-G4, A1-A4, T0, T1, T2, P0 and R. I read the direct statement and proof dependencies of all 30 with get_graph parents_of. Every item they name is in the port blueprint, and all 372 of those are proved or formalized, so no contract rests, even transitively, on an item that is not TheoremProved or DefinitionFormalized. T2 lists no dependencies in the port graph because everything it uses comes through the profile. The profile blueprints are complete: SAS 151/151, requirements 60/60, foundation 17/17, each with nothing left to prove. Limit: get_graph cannot trace edges into profile items, so for T2 I relied on whole-blueprint completeness, not an item-by-item closure.
3. (3) Hypotheses, read from statement_lean for all 30 contracts. E1-E3, E5, E6 and E7: PyLinks, Paired, InputOK, plus the reached-equations S.features and S.fit (E7 also states run_py_py returning files as an existence in its conclusion, as the spec allows). E4 also restricts m to models whose terms name the 36 candidates; spec section 2 states this in E4's own wording, so it is not an added hypothesis. E8-E11, F5 and F6: the same, plus hF and the ScoreRun run hypothesis on the SAS side (section 2a counts this as a reached-fact). F1-F4: PyLinks, Paired, InputOK, hF. P0: PyLinks, Paired, InputOK, hF, hfit. A1 and A2: PyLinks, InputOK and reached-equations. A3: no hypothesis at all. A4: PyLinks, Paired, InputOK, hF, ScoreRun. G1 and R: PyLinks and InputOK only. G2 and G3: those plus the reached-equations. G4: those plus ScoreRun on the port side. T0: PyLinks. T1: none. No contract carries a wf_ domain, an hpre or a numeric bound.
4. FINDING (wording, matters for a public text): T2 assumes SasLinks (the SAS trusted base), CreditRisk.InputOK, the reached-fact CreditRisk.Fitted and a defining equation hFt. It does not assume PyLinks or Paired. Spec section 6 allows this ('for the SAS pipeline on valid input', [D8]). But the summary sentence of informal-spec section 7 ('each assuming only PyLinks, Paired, InputOK and reached-equations') does not cover SasLinks, and its list of exceptions names only 'R and G1 to G4 have no Paired, T0 and T1 no input'. A public claim should say that T2 rests on SasLinks, and that A3 assumes nothing, which the exception list also omits.
5. FINDING (stale comment): T2's Lean comment still says 'Feature shape of E4 (section 2, wording not yet fixed by E4's reviewer)'. The spec marked that wording superseded on 2026-11-20: E4 no longer uses feature shape and T2 keeps its own wording. The text is cosmetic, but it is visible to readers.
6. NIT (spelling inconsistency, no unsoundness found): the port-side training score table without a model is written two ways. A4's ScoreRun calls train_run_12_risk_scores with s09.1 twice, then step 14 with s01.2.2.2.1 and the frame `risk` in every filler place. G4 and R call step 12 with s09.1 and [], then step 14 with none and [] fillers. E5 proves that risk_scores_train.csv does not depend on these idle arguments (it quantifies over every value of them), so the two spellings denote the same table. A reader comparing A4, G4 and R will still see different text for the same run.
7. (4) def:zz_carrier_fid_1 and def:zz_carrier_fid_2 have no consumers: empty statement_consumers and proof_consumers, and both are roots. Each is the identity on list[int]; they exist only to carry dependency edges. FINDING (process): brief-prover.md says 'Remove every zz_… item before you finish' and asks the report to confirm that none remains, yet both are still in the published blueprint. They affect no proof, but they should be removed or explained before the announcement.
8. No write was made and no hook blocked anything. The spec contract list (section 7) names the 30 items exactly, one item each, all present on 5365851c.

Where the two audits differ, as recorded (no judgement made here):
- Scope: the first audit left the SAS-side blueprints unchecked (its LIMIT in finding 2); the second
  read their status as complete (SAS 3f5df696 151/151, requirements 006ff04c 60/60, foundation
  02011d57 17/17), with whole-blueprint completeness standing in for an item-by-item closure of T2.
- The no-model training score table: the first audit (its finding 5) counts three spellings (PyLinks
  7b / A4, G4 / R, E5 / A2 / F3) and says no item proves them equal, because E5 is stated at
  `py.fit (...)`, not at `{}`; the second (its finding 6) counts two (A4 vs G4 / R), calls it a NIT,
  and takes E5's quantification over the idle arguments as showing they denote the same table. The
  second does not discuss the `py.fit (...)` vs `{}` point. This stays open for the lead.
- New in the second audit: the T2 / SasLinks and A3 wording finding against informal-spec section 7's
  summary sentence, and the stale "Feature shape of E4" comment in T2's Lean.
- Both audits: `def:zz_carrier_fid_1` and `_2` remain, with no consumers; the second cites
  brief-prover.md's "Remove every zz_… item before you finish".

Open list at the close of w31, updated: the items of "State at the close of w31" above, plus the T2
/ SasLinks / A3 wording of informal-spec section 7 and the stale T2 Lean comment. The SAS-side
sign-off item is narrowed to the second audit's limit (no item-by-item closure for T2).
