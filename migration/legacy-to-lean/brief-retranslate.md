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
