# Evaluation carriers for the fidelity pass, 2026-11-20

Blueprint `5365851c-5549-44b7-9207-4bd4c422031d` (Logos MCP Staging). Harness source:
`diffeval/carrier_fid.py`. The fidelity report itself is closed to this role (hook), so this note
works from the task text: the w29 pass was blocked because the `def:zz_carrier*` items were removed
at the close, and `eval_decl` refuses the units directly (diffeval/eval_decl-errors-2026-11-18.md §1).

## Why

`eval_decl` resolves `decl` only in the evaluated item's own Lean, while input terms see that item's
transitive dependencies. An identity `List Int -> List Int` code item that depends on the units lets
the README's `digest` / `tokens` / `ints` modes run through it (use `item=def:zz_carrier_fid_1`,
`decl=zz_carrier_fid_1` wherever the README says `def:zz_carrier` / `zz_carrier`).

## def:zz_carrier_fid_1

- Lean: `def zz_carrier_fid_1 (xs : List Int) : List Int := xs` (accepted, revision b4d98582).
- Source: `diffeval/carrier_fid.py` (added at 13-14; another writer edited the file afterwards, and
  the function is now at 12-13. The blueprint location still says 13-14).
- Direct dependencies: def:run, def:run_py, def:run_py_py, def:run_py_py_py, def:PyLinks,
  def:PyParams, def:pyPipeline, def:ScoreRun, def:train_run_01_fit_frame,
  def:train_run_02_stepwise_summary, def:train_run_03_fit_global_rsquare,
  def:train_run_04_score_train, def:train_run_08_ctable, def:train_run_11_confusion_valid,
  def:train_run_13_roc, def:train_run_14_final_and_summary, def:train_run_15_printed_roc,
  def:confusion_metrics, def:metrics_run_03_thresholds, def:metrics_run_05_cumulative_lift.
  Through the four `run` items, every unit of the four stages is in scope transitively.
- Reach check (one `eval_decl`, 21 inputs, while it was accepted): `[1, -2, 3]` returned unchanged;
  `(let _u := @<unit>; [k])` returned `[k]` for every unit above and for run, run_py, run_py_py,
  run_py_py_py, PyLinks, PyParams and ScoreRun. `@pyPipeline` resolves but does not run
  (`noncomputable`, Pipeline over the reals): the glue must chain the four `run`s at Float itself.
  A second call ran real code: `run (α := Float) true id (fun _ => "") none []` gives `none` (the
  import failed, so the run stops), and `confusion_metrics (α := Float) 0.5 "" []` gives a metrics
  frame of 0 rows and 6 columns.

## State at the end of this step: the carrier is cleared

After the `def:run` source update below, `def:PyLinks` went to DefinitionUnformalized. Everything
downstream of it was cleared with it: the carrier and 63 items (thm:/lem: contracts). The
blueprint went from 371 items with 370 formalized to 307 formalized, and `verification_approved`
became false. `def:run` and `def:pyPipeline` stayed formalized, so this does not look like a
cascade from `def:run`; a concurrent writer is possible. Minutes later PyLinks was formalized again
(not by this agent), a `def:zz_carrier_fid_2` existed (same units, without PyLinks/PyParams/pyPipeline/
ScoreRun; not added by this agent), and `carrier_fid.py` had been edited. The carrier and the cleared
contracts still need re-submitting; that is for the lead to direct.

## def:run stored source

Stored Python text is the pre-4a757fb `run` (no `_split_draw` / `file_ids` / `n_train`). The
split logic itself is in `def:fe_run_06_split`, refreshed 2026-11-18. `update_item_source` (metadata
only) set the location to `credit_risk/feature_engineering.py` 28-400 (HEAD). get_status before and
after the first call was identical, but it does not change the stored text. `write_code`, the only
way to change the text, clears the Lean of `def:run` and everything that depends on it, so it was
not used: the text is still stale. The status right after the second `update_item_source` call was
the 63-item clearing above.
