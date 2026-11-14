# Stress test (kit prompt 03), round 1 report

Selection: train.sas, metrics_calculation.sas and predict.sas, scored from the inventory
(`selection.md`). feature_engineering.sas is held back.

## What ran

| Role | Model | Output |
|---|---|---|
| sas_compat implementer | Sonnet | `credit_risk/sas_compat.py` (ships), plus `sas_compat_checks.py` |
| sas_compat reviewers A and B | Opus | `review.sas_compat.{A,B}.tsv`: 19 + 15 findings, 0 wrong-output |
| Translator B (native, never saw the rulebook) | Sonnet | 3 modules in an isolated scratch folder |
| Pilot implementer ×3 (= translator A, DEV-008) | Sonnet | train/metrics/predict in the throwaway worktree `stress-pilot` |
| Pilot reviewers, 2 per file | Opus | 39 findings, **0 wrong-output** |
| Arbiter (single-reviewer findings) | orchestrator | rulings recorded in `amendment-queue.md` |
| Pilot fixers ×3 | Sonnet | all confirmed findings applied; referee clean |
| Diff inspector | Opus | `bakeoff-diff.tsv`: 24 differences |

## Adherence findings (did the implementers obey the rulebook?)

| File | Reviewer A (latent / rule-violation / nit) | Reviewer B | Rule violations |
|---|---|---|---|
| predict | 2 / 0 / 2 | 1 / 0 / 3 | none |
| metrics | 1 / 0 / 4 | 1 / 1 / 5 | a private merge helper (second mapping of §2 merge) |
| train | 1 / 3 / 5 | 1 / 6 / 3 | merged two DATA steps into shared functions (§0); a hand-made D12.3 renderer (§2); wider-than-stored format widths; `# pyright: ignore` (§3); altered %put text |

No reviewer found a translation that was right *because* it ignored a rule. Every violation
was a structural or second-mapping deviation, and each produced the same output today.

## Bakeoff (rulebook vs native)

24 meaningful differences: **13 rulebook-right, 10 both-defensible, 1 native-right, 0 both-wrong**.

The native port fell into exactly the traps the inventory documents:
- stepwise entry by smallest p (wrong from step 1);
- rebuilding the model from the printed D8. coefficients (pd drifts by up to 1.75e-2);
- BEST12 rounding from the binary value (424 vs 39 mismatches);
- `100.00%`;
- PSI `1.54E-33`;
- a carry-forward merge;
- missing HL / ctable / 16 judged files.

The one native-right item (SQL `sum` over an empty join is missing) became S10, confirmed on
SAS by X05.

## Pilot parity (orchestrator, outside every loop)

With the reviewed sas_compat, the fixed pilot translations were run on the judge contract's
staged inputs and judged in port mode:
- run 2 train **18/18**;
- run 3 metrics **9/9**; runs 6–8 edge_metrics a/b/c **9/9 each**;
- run 4 predict **2/2**; run 5 edge_predict **2/2**.

Total runtime 12 s. Translations written strictly from the rulebook and inventory pass on
first execution.

## Amendment queue → rulebook v1.3 (applied under the user's standing instruction)

S1–S12 and the X05 rules (`amendment-queue.md`, `migration/experiments/x05_findings.md`). They cover:
- `sas_exp` overflow;
- `input_best32` on numeric input;
- the literal trailer format;
- the helper return conventions;
- `merge_one_to_one`;
- the stored ODS widths;
- intercept-only stepwise;
- "two DATA steps stay two blocks";
- SQL aggregates over zero rows;
- `run()` creating `output_dir`;
- ROUND fuzz;
- signed negative zero;
- PERCENT negatives in parentheses;
- width-aware BEST E-notation;
- w.d overflow falling back to BEST.

Inventory fixes from the pilot:
- the decile divisors are full-precision subqueries (the pilot implementer caught an audit-fix error);
- S6 (one D12.3 helper);
- S11 (PSI nullable).

No section was amended twice.

## Re-round

Folded into Step 3 (DEV-009). Only one fresh file remains (feature_engineering.sas). Step 3
runs the full production pipeline on all four files under v1.3 with the judge as exit
condition, which covers what a re-round would.

## Workspaces

Deleted after this report, confirmed in DECISIONS.md:
- the translator A / pilot worktree (`stress-pilot`, never merged);
- translator B's scratch folder.

## Estimate for Step 3 (translation fan-out)

The manifest has 4 units. Measured pilot timings per file:
- implementer 1.5–3 min;
- reviewers 4–7.5 min, in parallel;
- arbitration about 1 min;
- fixer 0.5–1 min;
- staged judge runs 12 s.

Running all 4 files in parallel: **about 15–25 min wall-clock**, plus about 10 min of judge
iteration if anything fails. **0 min of user attention** under the standing instruction;
otherwise about 10 min to read the burndown.
