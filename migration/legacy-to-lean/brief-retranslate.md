# Bring the SAS Lean up to date with the corrected SAS program

The SAS program in `legacy/` was corrected where it was proved to violate its documented
requirements (rulings G33 to G38 in `migration/requirements/requirements.md`). Your Lean in
`sas-credit-risk-spec` still describes the program as it was. Bring it up to date, with the same
care and the same rules as the original translation (`migration/legacy-to-lean/brief.md`, your
`RULEBOOK.md`, `manifest.tsv`): the Lean must do what the SAS now does, nothing more.

## What changed

- `migration/legacy-to-lean/corrections.diff`: every change to the four scripts.
- `migration/legacy-to-lean/corrections-account.md`: the coding agent's account, per
  finding, with the SAS runs that show each fix.
- `judge/reference/` and `judge/reference/scenarios/` now hold the outputs of the corrected SAS.
  Further evidence runs are in `judge/runs/` (`final_*`, `ev*_fix_*`) with inputs under
  `judge/scenarios/` (`fix_*`, `fix2/`), and experiments x16 to x20 in
  `migration/legacy-to-lean/experiments/`.

## What to do

1. Work through the diff. For every unit it touches, update the code item so it mirrors the new
   SAS lines; add an item for every new step; keep names and order in line with the source.
   Update `manifest.tsv` (line ranges moved in all four files) and the item texts.
2. New behaviour to model, not skip:
   - **The input check** after each raw PROC IMPORT, and the fact that a script stops and exports
     nothing when it fails. Give each stage a way to say "stopped" (the units were all total
     before). State exactly the conditions the SAS tests, as the SAS tests them.
   - **`income_medians.csv`**: written by `feature_engineering.sas`, read by `predict.sas`.
   - The corrected PSI binning, the single KS row, the KS at ties, the grade ladder on the
     probability, the unrounded score, the eight-flag sum, the two interaction features, the
     median fallback.
   - Each script removing its earlier output files, and stopping when the step before produced
     none: record how you model it (or that it is outside the model, as files are) and why.
3. Rules for a built-in PROC or function not used before need evidence, as always: an existing
   run or experiment, or a new experiment you run on SAS.
4. **Differential evaluation**: run every changed or new unit on real rows and on the fix
   scenarios, against what the corrected SAS produced, to zero unexplained differences. Add to
   `diffeval-receipt.md`.
5. Do not touch `def:sasPipeline`, `def:SasLinks` or any `sas_Q*` / `neg:*` item: they belong to
   the prover, who will redo them. Your edits will clear their acceptance; that is expected.
6. Do not add or prove postconditions.

Return as text: every item changed or added with the SAS lines it covers; how "stopped" is
modelled; rules added to the rulebook with their evidence; the differential-evaluation receipt
for this round; open parameters; anything in the corrected SAS that looks wrong or that you could
not model.

## Second update (round 3 of the corrections)

The SAS was corrected again on four points (rulings G40 to G43): the exact AUC in
`metrics_calculation.sas`, the ten-row decile table, the numeric row-id check in both input
checks, and the PSI floor at full precision. The diff since your last update is
`migration/legacy-to-lean/corrections-round3.diff`; the account is the section "Round 3" of
`corrections-account.md`; the evidence runs are `ev4_*`, `ev5_*` and `final3_*` in `judge/runs/`,
and `judge/reference/` holds the newest outputs. Do the same work as above for these changes
only. Your earlier account is `retranslation-report.md`. While you are editing them anyway,
bring the informal text of each item you touch in line with the current SAS lines.

## Third update (2026-11-15): round 4 corrections

The SAS was corrected again on two findings (rulings G44 and G45 in
`migration/requirements/requirements.md`). The changes to the four scripts since the second
update are in `migration/legacy-to-lean/corrections-round4.diff` (commits a9acbf5, 5913e11,
56e52f7, 697eed5). Bring the Lean of the units those lines touch up to date, and nothing else.

- **`metrics_calculation.sas` (G45).** In the decile table, capture rate and lift are coalesced to
  0 (lines 261-262), so a validation set with no defaulter gives 0 on every decile. The
  cumulative lift table got the same rule (lines 305-312): cumulative capture rate 0 on every
  row; cumulative lift 0 from the first decile that holds an applicant, missing before it.
  Evidence: `judge/runs/ev6_fix_Q26_nodefaulter` (and `ev6_fix_Q26_small_unchanged`,
  `ev6_fix_Q26_ties_unchanged` for the cases that must not change).
- **`predict.sas` (G44).** A test file with its header and no applicant is now scored: the import
  yields an empty `test_raw` with the columns the header names, whatever their order, the input
  check passes, and both prediction tables are empty. What the Lean must capture is the
  behaviour on tables, not the mechanism: the made-up applicant, the temporary copy and the
  deletion of earlier WORK tables are file-system and session effects and are not translated;
  say so in the items' comments. The import itself stays a parameter of the later pass. Check
  every unit of the test chain on the empty table: the checks, the imputation and its join with
  the medians, the features, the scoring, the two exported tables. Evidence:
  `judge/runs/ev10_fix_Q27_emptytest`, `ev10_fix_Q27_fresh_header_only`,
  `ev10_fix_Q27_column_order`, `ev10_fix_Q27_emptytest_badheader`.

Each of you has one script. Edit only items that cover lines of your script. Do not edit the
shared record files (manifest, rulebook, receipt, open items): return what should go into them.
If your work needs a change to an item of another script, do not make it: report it. After a
change, items that depend on it may need resubmitting unchanged; do that for your script's items
and report the others.
