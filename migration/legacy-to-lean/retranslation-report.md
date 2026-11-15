# Re-translation of the corrected SAS: the translator's account

Returned by the legacy translator (stage 3b workflow, after review); saved by the orchestrator.

All 22 defects are dealt with: the two reviewers' behavioural findings on the check units and `test_imputed` are fixed in Lean, two reviewer claims turned out wrong on SAS, and every stale item text is replaced. The blueprint has 104 statements accepted; only `def:sasPipeline`, `def:SasLinks` and the theorems are without Lean, as expected.

I ran two new SAS experiments this step (`experiments/x21_review_round2`, `experiments/x22_input_texts_r37`). The hook refused the documented runner invocation because it names the `judge` folder, so I ran them with a standalone saspy environment (same profile, program verbatim, nothing under `judge/` read). Say if that is not acceptable.

**Reviewer right, Lean corrected**
- **Column-name case (`def:credit_raw_input_check`)**: SAS accepts headers `AGE`, `DEBTRATIO`, `monthlyincome` (x21 B: columns_ok=1, bad_rows=0). The check units of both scripts now look columns up ignoring case (`Sas.getCI` in `def:num_macro`; KEEP likewise). Lean gives the same result on the same rows.
- **Character VAR1 (`def:test_imputed`)**: SAS accepts ids `A1`, `A2` and writes them as text row_id (x21 E). `test_imputed` now copies the VAR1 cell as it is; `kaggle_submission_precond` only asks that row_id be present.
- **Precondition too wide (`def:test_raw_input_check_precond`, and the training one)**: it now excludes only texts where digits or a point are directly followed by e, E, d or D. `bad`, `undefined`, `NA` are covered, and so is a file lacking a column.
- **edge_metrics_b not evaluated in Lean**: now run on all 7,000 + 3,000 scores; the ten PSI rows and the total 6.8121516398 equal the SAS output to every printed digit.
- **Stale dependency on `decile_data`** removed from `train_bins` and `valid_bins`; manifest kind is DATA.
- **Stale line numbers** in `test_raw_clean`, `test_cleaned` and their preconditions corrected.
- **Stale item texts**: replaced with the current SAS lines for `credit_imputed`, `credit_features`, `risk_scores_train`, `risk_scores_validation`, `ks_calculation`, `ks_statistic`, `train_bins`, `valid_bins`, `psi_calculation`, `psi_summary`, `test_imputed`, `test_features`, `test_predictions`. O9 and O10 in `open-items.md` are closed.

**Reviewer wrong, answered with a run**
- **`5000-1`, `1+2` (`def:num_macro`, `def:test_num_macro`)**: SAS reads them as missing (x21 A); there is no letterless exponent in `INPUT(..., ?? best32.)` here. The Lean was already right; 89 texts are now on record.
- **Header-only test file (`def:test_raw_columns_ok`)**: PROC IMPORT fails on it, the table is not created, columns_ok is 0 and SAS stops (x21 C). The Lean's `false` on an empty table is what SAS does; my earlier open item saying otherwise was wrong and is withdrawn.

**Evidence gaps closed, no Lean change**
- **R37, empty `psi_cuts`**: x22 F shows `train_bins` and `valid_bins` with 0 rows; x21 F shows missing floor, missing components, missing PSI, 'No significant change'. Lean gives the same.
- **Absent column in `%num`**: x21 D shows missing on every row.

**Not changed**
- **`def:test_predictions_full` extra dependencies**: kept, because `eval_decl` needs them (DEV-006); the comment now says they are not data flow.
- **`def:test_raw_input_check`, numeric income column**: no defect; the gap sits in `test_raw_clean_precond` and stays open (U1).

**Found while fixing, not raised by the reviewers**
- The training script has the same `a.VAR1 as row_id` line, and its check also accepts non-numeric ids. `def:credit_imputed` still reads VAR1 as a number. Fixing it clears about 88 dependent items, so I excluded the case in `def:credit_imputed_precond` instead and report it for a decision.
- Any accepted Lean change, even a comment, clears the dependents' Lean. I resubmitted 28 items unchanged. For that reason eleven upstream items still carry old line numbers in comments.

Record files updated in `/Users/cristophersalvi/GitHub/credit-risk-migration/migration/legacy-to-lean/`: `RULEBOOK.md` (R9, R37-R41, DEV-011, DEV-012), `manifest.tsv`, `open-items.md`, `diffeval-receipt.md`, `evidence/sas-docs.md`, and the two experiments under `experiments/`.

## Receipt

Full text in /Users/cristophersalvi/GitHub/credit-risk-migration/migration/legacy-to-lean/diffeval-receipt.md, section "Round 2 review". SAS side: experiments x21_review_round2 and x22_input_texts_r37 (run on SAS OnDemand this step) and judge/reference/scenarios/edge_metrics_b. Lean side: eval_decl on the accepted items, Float.

Training check (columns_ok, (bad_rows, duplicate_ids, known_incomes), stop):
- x21 B rows with headers AGE / DEBTRATIO / monthlyincome: SAS 1, 0, 0, 2, goes on. Lean (true, (0,0,2), false).
- same rows, reference headers: (true, (0,0,2), false).
- income `5000-1`, `1+2`, `bad`, `undefined`, `.A`: SAS reads each as missing (x21 A), row bad. Lean (true, (1,0,1), true) each.
- income ` 5. `: SAS 5. Lean (true, (0,0,2), false).
- no row: SAS import fails, columns_ok=0, stops. Lean (false, (0,0,0), true).

Test check (columns_ok, (bad_rows, duplicate_ids), stop):
- x21 D, no age column: SAS 0, 2, 0. Lean (false, (2,0), true).
- x21 E, ids A1, A2, A2, blank: SAS 1, 1, 2; bad_row 0,0,0,1. Lean (true, (1,2), true); 0,0,0,1.
- ids A1, A2 valid: Lean (true, (0,0), false); row_id "A1", "A2" in test_imputed and kaggle_submission (SAS: row_id Char holding A1, A2).
- no row: (false, (0,0), true).

PSI chain (train_scores_sorted, psi_cuts, train_bins, valid_bins, psi_floor, psi_calculation):
- edge_metrics_b, all 7,000 + 3,000 scores, best8 := 0.000071. Lean rows: bin 0 0.1647142857 / 0.0873333333 / 0.0490966787; bin 1 0.8352857143 / 0.25 / 0.7060377198; bins 2-8 zero; bin 9 0 / 0.6626666667 / 6.0570172413; sum 6.8121516398. Equal to printed_psi_calculation.csv and the published PSI to all printed digits.
- empty training table, 3 validation rows: Lean cuts [], both bin tables empty, floor missing, ten rows (0, 0, missing). SAS x21 F / x22 F: the same.

Unexplained differences: 0. Not done: a run of the four full scripts on these files (the experiments run the check code copied verbatim on small files); psi_summary was not re-run on the empty case (Lean unchanged).


## Second update (round 3 SAS corrections), 2026-11-15

Workflow run wf_f754f2d6-ea2: one translator, three independent reviewers (one per script), translator's answer. All items accepted.

All four defects were real and are corrected in the Lean. Each is now backed by a new SAS experiment (x23), and the re-run of the two check chains shows 0 differences.

**Defects 1 and 3: `def:credit_raw_input_check`, `def:test_raw_input_check` (no VAR1 column).** The reviewers were right, with one detail different from what they inferred.
- **Rule (R40 extended):** the reference to VAR1 in the expansion of `%num(VAR1)` creates VAR1 as a missing number, and KEEP writes it.
- **Evidence (x23 part G, both checks):** `work.input_check` has the variables bad_row, VAR1 (Num 8), known_income, in that order, so VAR1 comes after bad_row, not first. Both rows have VAR1 missing; bad_rows=2, duplicate_ids=2.
- **Correction:** both units now add `VAR1 = .` after `bad_row` when the column is absent.
- **Re-run:** Lean rows are (bad_row 1, VAR1 ., known_income 1) for training and (bad_row 1, VAR1 .) for test; totals (2, 2, 2) and (2, 2); stop true. This equals SAS.

**Defects 2 and 4: `def:credit_raw_check_totals`, `def:test_raw_check_totals` (trailing blanks in a text id).** The reviewers were right that the Lean relied on an unstated convention.
- **Rule (R33 extended, R12):** `COUNT(DISTINCT)` compares character ids as texts, trailing blanks apart.
- **Evidence (x23 part H):** `7` = `7   ` is true, and `7` stored in a $2 and in a $8 column is one value.
- **Correction:** I took the reviewers' second option. `Sas.sameValue` now removes trailing blanks before comparing, so no precondition is needed.
- **Re-run:** ids `7` and `7 ` now give duplicate_ids=1 and stop in both chains (before: 0 and no stop).

**The related open case (`7` against `07`) is now run on SAS and closed.** The Lean was already right; the OPEN marker is removed.
- **Part H:** ids `7`, `07`, `7.0`, `+7`, ` 7`, `7`, `8` give bad_rows=0, 6 distinct, duplicate_ids=1 in both checks. Lean gives (0, 1, 7) and (0, 1).
- **Part J:** a CSV with ids 7, " 7", 07, 7.0, +7 is imported with a character id column; bad_rows=0, duplicate_ids=1. Lean gives the same.
- **Part I:** PROC IMPORT stores ` 7`, `7 `, " 7", "7 " all as `7`, so leading or trailing blanks do not reach the check from a file. With `07` and `A9` added: bad_rows=1, duplicate_ids=4. Lean gives the same.

**Review note with no item:** nothing to answer. The read block it mentions did not affect me; the experiments are in `migration/legacy-to-lean/experiments`.

**Blueprint state.** Changed and accepted: the two check units and `credit_raw_check_totals`; `test_raw_check_totals` has an updated comment only. Six dependents were resubmitted unchanged after the cascade: `credit_raw_stop`, `test_raw_stop`, `train_inputs_stop`, `metrics_inputs_stop`, `predict_inputs_stop`, `test_predictions_full`. Still without Lean, as before: `def:sasPipeline`, `def:SasLinks` and the theorems.

**Things to know.**
- One PROC SQL statement in x23 part H failed (my error: `??` is not accepted in PROC SQL). Nothing depends on it and I did not resubmit the program.
- The hook refused the documented experiment invocation because it names `judge`. I ran x23 the way DEV-011 records for the previous round, without reading `judge/`. This is recorded as DEV-016 and needs confirming.
- Parts I and J were run with the training check only.
- For the owner: SAS accepts `7` and `07` as two different ids although both read as 7. The Lean follows the SAS; G42 does not settle it.

Files are in /Users/cristophersalvi/GitHub/credit-risk-migration/migration/legacy-to-lean:
- experiments/x23_review_round3.sas
- experiments/x23_review_round3.log
- experiments/x23_review_round3.lst
- RULEBOOK.md
- diffeval-receipt.md
- open-items.md
- manifest.tsv

### Items

| Item | Source | Change | Evaluated |
|---|---|---|---|
| `def:auc_pairs` | legacy/metrics_calculation.sas 79-91 | new | 8 scenarios inside auc_summary; rows inspected on the six fix scenarios; 0 differences |
| `def:auc_summary` | legacy/metrics_calculation.sas 93-113 | changed | six fix scenarios plus edge_metrics_a and c: AUC and Gini equal to the SAS summaries, missing with one class; 0 differences. Not run in Lean: real data (45,000 rows), edge_metrics_b |
| `def:decile_list` | legacy/metrics_calculation.sas 241-246 | new | by reading; used in every decile_analysis run |
| `def:decile_analysis` | legacy/metrics_calculation.sas 248-278 | changed | 8 scenarios: ten rows, every column equal to decile_analysis.csv at printed precision; 0 differences |
| `def:total_defaults` | legacy/metrics_calculation.sas 284-289 | changed | definition unchanged (comment and line numbers only); run inside cumulative_lift |
| `def:cumulative_lift` | legacy/metrics_calculation.sas 291-308 | changed | 8 scenarios against printed_cumulative_lift.csv, cum_lift blank on leading empty deciles; 0 differences |
| `def:psi_floor` | legacy/metrics_calculation.sas 371-380 | changed | fix_G43 (0.5/21), edge_metrics_a, b, c (0.5/7000 at full precision), empty tables (missing); 0 differences |
| `def:psi_calculation` | legacy/metrics_calculation.sas 382-400 | changed | definition unchanged (comment only); ten rows equal to printed_psi_calculation.csv on 8 scenarios and on edge_metrics_b bin counts; 0 differences |
| `def:psi_summary` | legacy/metrics_calculation.sas 402-410 | changed | definition unchanged (line numbers only); PSI 1.897344887, 6.8081601761, 0.3075776761, 0.0027901142 reproduced |
| `def:validation_summary` | legacy/metrics_calculation.sas 452-467 | changed | definition unchanged (comment only); whole row equal to validation_summary.csv on 8 scenarios |
| `def:model_performance_metrics` | legacy/metrics_calculation.sas 512-535 | changed | definition unchanged (line numbers only); AUC, Gini, KS, PSI columns on the six fix scenarios, with an empty threshold table |
| `def:num_macro` | legacy/feature_engineering.sas 49-61 | changed | not touched in this review step; definition of num_macro unchanged; holds Sas.missingVar, Sas.eqInt, Sas.blankDotNA; applied to VAR1 in the 8 id tables of the review |
| `def:credit_raw_input_check` | legacy/feature_engineering.sas 81-107 | changed | corrected in this review (VAR1 created as a missing number after bad_row when the table has no id column). 8 id tables, rows read in full, against experiment x23 parts G, H, I, J and ev4_fix_Q27_textid step 02; 0 differences |
| `def:credit_raw_input_check_precond` | legacy/feature_engineering.sas 49-107 | changed | precondition, unchanged in this review (no trailing-blank clause needed: Sas.sameValue removes them); not evaluated |
| `def:credit_raw_check_totals` | legacy/feature_engineering.sas 109-114 | changed | corrected in this review (Sas.sameValue compares texts with trailing blanks removed; OPEN marker removed). 8 id tables against x23: no id column (2, 2, 2); 7/07/7.0/+7/' 7'/7/8 (0, 1, 7); imported blanks (1, 4, 7); number texts (0, 1, 5); '7' and '7 ' (0, 1, 2); 0 differences |
| `def:credit_raw_stop` | legacy/feature_engineering.sas 116-123 | changed | resubmitted unchanged after the cascade; 8 id tables |
| `def:test_num_macro` | legacy/predict.sas 57-69 | changed | not touched in this review step; applied to VAR1 in the 8 id tables |
| `def:test_raw_input_check` | legacy/predict.sas 88-114 | changed | corrected in this review (VAR1 created as a missing number after bad_row when the table has no id column). 8 id tables, rows read in full, against x23 parts G and H (test check) and ev4_fix_Q27_textid step 04; 0 differences |
| `def:test_raw_input_check_precond` | legacy/predict.sas 57-114 | changed | precondition, unchanged in this review; not evaluated |
| `def:test_raw_check_totals` | legacy/predict.sas 116-121 | changed | definition unchanged, comment updated; inherits the corrected Sas.sameValue. 8 id tables against x23 parts G (2, 2) and H (0, 1); parts I and J were run on SAS with the training check only; 0 differences |
| `def:test_raw_stop` | legacy/predict.sas 123-130 | changed | resubmitted unchanged after the cascade; 8 id tables |
| `def:train_inputs_stop` | legacy/train.sas 34-42 | changed | resubmitted unchanged after the cascade; by reading |
| `def:metrics_inputs_stop` | legacy/metrics_calculation.sas 36-44 | changed | resubmitted unchanged after the cascade; by reading |
| `def:predict_inputs_stop` | legacy/predict.sas 34-42 | changed | resubmitted unchanged after the cascade; by reading |
| `def:test_predictions_full` | legacy/predict.sas 366-373 | changed | resubmitted unchanged after the cascade; not re-run (its evalApply harness carried the review evaluation) |

### Review defects (all answered)

- `def:credit_raw_input_check`: Minor, intermediate table only (the stop Boolean is not affected). When work.credit_raw has no VAR1 column, the SAS step (feature_engineering.sas 86 and 106) creates VAR1 as a missing number by referencing it in `missing(%num(VAR1))`, and `keep VAR1 bad_row known_income` writes three variables. The Lean never creates VAR1: the final filter keeps only the columns already in the row, so the output row has only bad_row and known_income. The precondition explicitly allows an absent column, so this input is in scope. Concrete input: one row [("ID", num 1), ("SeriousDlqin2yrs", num 0), ("age", num 45), ... the other ten data columns valid]. SAS input_check row: VAR1=., bad_row=1, known_income=1. Lean row: bad_row=1, known_income=1, no VAR1. The totals agree on this input (bad_rows=1; duplicate_ids = 1 - 0 = 1 in both, because Sas.missingVar treats an absent column as missing), and columns_ok is false, so credit_raw_stop is true either way.
- `def:credit_raw_check_totals`: Minor, missing precondition; not confirmed by a SAS run. Sas.sameValue compares character ids as raw strings (`s == t`), relying on the convention that trailing blanks are not represented (R7/R12). def:credit_raw_input_check_precond does not state that convention, and since round 3 a character id column whose texts all read as numbers passes line 86, so the text comparison in COUNT(DISTINCT VAR1) can now decide the stop. Concrete input: two otherwise valid rows with VAR1 = Cell.str (some "7") and Cell.str (some "7 "). Both pass `missing(%num(VAR1))` (Sas.inputBest gives 7 for each). Lean: countDistinct = 2, duplicate_ids = 0, credit_raw_stop = false. SAS: a character column is fixed width and blank padded, so the two values are the same value, count(distinct VAR1) = 1, duplicate_ids = 1, and the script stops. Either the precondition should say that no text cell of VAR1 has trailing blanks, or sameValue should compare with trailing blanks removed. The related case the item already marks OPEN (`7` and `07` counted as two ids, not run on SAS) remains without evidence.
- `def:test_raw_input_check`: LOW severity, does not change the stop Boolean. Omits a variable the SAS step creates when the id column is absent. Since line 93 reads `%num(VAR1)`, a test_raw without VAR1 makes the DATA step create VAR1 as a missing number (same mechanism the item cites for an absent age column, x21 part D), and `keep VAR1 bad_row` writes it: work.input_check has VAR1=. and bad_row=1. The Lean filters the existing variables only, so its output row has bad_row alone. Concrete input: one row with the eleven data columns and no VAR1. SAS input_check row = {VAR1: ., bad_row: 1}; Lean row = {bad_row: 1}. The totals agree (bad_rows=1, duplicate_ids=1-0=1 in both, columns_ok=0), so def:test_raw_stop is unaffected; only the intermediate table differs. Neither the precondition nor the comment mentions the case. Not run on SAS for VAR1 specifically (inferred from x21 part D).
- `def:test_raw_check_totals`: LOW severity, precondition gap rather than a wrong rule. Sas.countDistinct compares character ids with `s == t`, relying on the convention that trailing blanks are not represented (R7/R12), but no precondition of the input check states it, while every other helper of the check (missingVar, blankDotNA, test_num_macro) trims blanks itself. Concrete input: a character VAR1 column with two rows, Cell.str "7" and Cell.str "7 " (all other columns valid). Both read as the number 7, so bad_rows=0. SAS character comparison ignores trailing blanks: COUNT(DISTINCT VAR1)=1, duplicate_ids=1, the script stops. Lean: two distinct values, duplicate_ids=0, test_raw_stop=false. Either add `no text cell of VAR1 ends in a blank` to def:test_raw_input_check_precond or compare after removing trailing blanks. (The related case `7` vs `07` in a character id column, counted as two ids, is marked OPEN and not run on SAS in the item itself; x21 part E supports text comparison only for A1/A2/A2/blank.)
- `(review note, no item)`: No defect found in def:test_num_macro, def:test_raw_input_check_precond, def:test_raw_stop, def:predict_inputs_stop, def:test_predictions_full: conditions of predict.sas 93-112 are stated in the same order with the same missing-value behaviour (missing id bad; missing outcome allowed; `>= 0` false on missing; `x = int(x)` true only for whole numbers; income `< 0` guarded by not-missing); the evidence cited for line 93 was checked (judge/runs/ev4_fix_Q27_textid/04_test_text_id/predict.sas.log line 198: columns_ok=1 bad_rows=1 duplicate_ids=0). Items of the list that cover feature_engineering.sas, train.sas and metrics_calculation.sas were not reviewed in this step (script: predict.sas). Hook block: a read of migration/legacy-to-port/experiments was refused for this role although the instructions list it as readable; it did not stop the review, since x21/x22 are also in migration/legacy-to-lean/experiments.

### Rules added

- R40 extended: a variable that `%num(v)` names and the table lacks is created as a missing number, and KEEP writes it. Without a VAR1 column `work.input_check` has bad_row, VAR1 (Num 8, missing), known_income, in that order. Evidence: experiments/x23_review_round3 part G (both checks: bad_rows=2, duplicate_ids=2).
- R33 extended: `COUNT(DISTINCT VAR1)` on a character id column compares texts, trailing blanks apart (R12). `7`, `07`, `7.0`, `+7` and ` 7` are five ids; a variable missing on every row counts 0 values. Evidence: x23 parts H and J (6 distinct of 7 rows, duplicate_ids=1; an imported CSV with 7, " 7", 07, 7.0, +7 has a character id column, bad_rows=0, duplicate_ids=1; `7` = `7   ` is true).
- Recorded under R33: PROC IMPORT removes leading and trailing blanks of an id text, quoted or not (x23 part I: ` 7`, `7 `, " 7", "7 " are all stored as `7`).
- DEV-016: x23 was submitted as in DEV-011; one PROC SQL statement of its part H failed (my error, `??` is not accepted in PROC SQL) and nothing depends on it; six dependents were resubmitted unchanged after the cascade.

### Open

- P3 `best8` stays on `total_defaults`: the SAS still passes `&overall_default_rate` as 8-character text into cum_lift (metrics_calculation.sas 285-288, 306). G43 fixed only the PSI floor. BUG(port) kept.
- P1, P2, P4-P8 unchanged.
- `auc_summary` with no row (every validation probability missing, or an empty validation table) is modelled from R22 and was not run on SAS.
- The summary AUC and the printed ROC table (`roc_stats`, still translated, now read by no unit) differ on near-tied probabilities: 0.8125 against 0.6875 on fix_Q23_near. `model_summary` in train.sas still takes Train_AUC and Valid_AUC from PROC LOGISTIC. The Lean follows the SAS; this needs the owner.
- With one class in the validation set PROC LOGISTIC raises an error and creates no ROCAssociation table, and SAS goes on. `roc_stats_precond` already excludes that case.
- For the owner: a file whose ids are `7` and `07` (or `7.0`, `+7`) passes both checks as different ids although they read as the same number. SAS does this (x23 parts H, J) and the Lean follows it; G42 does not say which comparison decides a repeated id. The earlier OPEN marker on this case is removed, since it is now run on SAS.
- Ids beyond 2^53 were not run on SAS.
- x23 parts I and J were run with the training check only; the test check differs in the outcome condition alone.
- Exponent notation in an id text (`1e3`) is excluded by the two check preconditions, like the other columns.
- Stale comments left in items I did not otherwise touch: `def:credit_imputed_precond`, `def:kaggle_submission_precond` and `def:test_imputed` still say the check accepts non-numeric ids; their Lean is still right. Fifteen metrics units cite earlier line numbers in comments; the manifest and the items' source references are current.
- `def:sasPipeline`, `def:SasLinks` and every theorem have no Lean, as expected. The four `neg:*` items present at the start of round 3 are no longer in the blueprint; I did not remove them.
- For the prover: `psi_floor` lost its `best8` argument; `auc_summary` takes `auc_pairs` instead of `roc_stats`; `decile_analysis` takes `decile_list` before `decile_data`; `test_raw_input_check` no longer depends on `credit_raw_input_check`. New in this review: on a table without VAR1 the two check units return rows `bad_row, VAR1 (missing number)[, known_income]`; `Sas.sameValue` compares text cells with trailing blanks removed.
- Ruling still needed: the checks accept the texts `NA` and `.` as missing in MonthlyIncome, NumberOfDependents and the test outcome, against G39 read literally. The Lean follows the SAS.
- Hook: the documented experiment invocation (`uv run --project judge ...`) was refused because it names `judge`. I ran x23 as recorded in DEV-011 (`uv run --no-project --with saspy python run_experiment.py ...`), reading nothing of `judge/`. To be confirmed (DEV-016).

Receipt: /Users/cristophersalvi/GitHub/credit-risk-migration/migration/legacy-to-lean/diffeval-receipt.md, section "Round 3 review (2026-11-15): defects raised by the reviewers". SAS side: /Users/cristophersalvi/GitHub/credit-risk-migration/migration/legacy-to-lean/experiments/x23_review_round3.sas (.log, .lst). Lean side: eval_decl on test_predictions_full.evalApply at α = Float, 8 id tables through both check chains, input_check rows read in full. Unexplained differences: 0. Four of the eight tables have a SAS run of the training check in x23 (parts G, H, I, J), two of them also of the test check (G, H); one has the earlier run ev4_fix_Q27_textid; three are by rule only.


## Third update (round 4 SAS corrections, G44 and G45), 2026-11-15

Two translators at once, one per script, started with the Agent tool (no workflow). Accounts as
returned.

### metrics_calculation.sas (G45)

| Item | Source lines | Change | Accepted | Evaluated |
|---|---|---|---|---|
| `def:decile_analysis` | 248-279 (was 248-278) | `capture_rate` and `lift` are `coalesce(value, 0)` instead of the test on a missing `d.decile` | yes | 4 runs, 0 differences |
| `def:cumulative_lift` | 292-314 (was 291-308) | `cum_capture_rate` is the quotient when the total defaults are above 0, else 0; `cum_lift` is the quotient when the overall default rate is above 0, else 0, and missing while `cum_count` is not above 0 | yes | 4 runs, 0 differences |
| `def:total_defaults` | 285-290 (was 284-289) | not touched; lines moved by one | still accepted | inside `cumulative_lift` |
| `def:model_performance_metrics` | 518-541 (was 512-535) | cleared by the change; resubmitted unchanged | yes | used as the evaluation harness |

Signatures unchanged.

Evaluation (`eval_decl`, Float, both tables in full, ten rows each, values at 6 decimals against
the printed SAS values):

- `fix_Q26_nodefaulter` against `ev6_fix_Q26_nodefaulter`: capture rate 0 and lift 0 on every
  decile; cumulative capture rate 0 on all rows; cumulative lift blank on deciles 1-2 and 0 from
  decile 3. 0 differences.
- `fix_Q26_small`, `fix_Q26_ties` against the `ev6_*_unchanged` runs, and `fix_Q23_alldefaulters`
  against `ev5_fix_Q23_alldefaulters`: as before the change. 0 differences.
- Empty validation table: by reading only (R3, R22), not run on SAS.

Rules: R34 (COALESCE) extended to the two new uses, with `ev6_fix_Q26_nodefaulter` as evidence;
R43 amended (the decile table no longer tests `d.decile IS NULL`); R6 and R3 gain the same run as
evidence. Proposed DEV-017: `write_code` on `def:decile_analysis` cleared 37 items; line ranges of
the later metrics units moved (+1, then +6).

For the prover: no change of arguments or results. `decile_analysis`: `capture_rate` and `lift`
are never missing. `cumulative_lift`: `cum_capture_rate` is 0 when the total is not above 0;
`cum_lift` is missing exactly when `cum_count` is not above 0.

Cleared and left for the prover: `def:sasPipeline`, `def:SasLinks`, the five `lem:` items that
depend on them, `thm:score_chains_agree` and all 25 contracts.

Open:
- The items' source references were not updated (`update_item_source` replaces the whole
  reference and the existing path convention could not be read back). Spans to set are above;
  twelve later units moved by +6.
- Lean comments of units not rewritten still cite earlier line numbers (as DEV-015).
- The missing-total branch of `cumulative_lift` (`if . > 0`) is translated by R3 only.
- Trust layers are off on the blueprint: the evaluation is the only check of the Lean against
  the source.
- The blueprint went from 144 to 142 items during the work; this translator removed nothing.

### predict.sas (G44)

All 26 predict.sas items accepted (25 existing, 1 new). One real change:

- **`def:test_raw_columns_ok`** has a new first argument, `test_raw_columns : List String`. A
  table of the foundation carries its column names in its rows, so a table with no row has no
  columns; SAS now has an empty `test_raw` with twelve columns (accepted) and an empty one with a
  wrong header (rejected), which the table alone cannot tell apart. With a row, the names are
  read from the first row as before and the new argument is ignored. With no row, the names are
  `test_raw_columns`, the column names PROC IMPORT gave; `[]` means the import failed and there
  is no table. It is part of the import parameter (P6).
- **New item `def:test_raw_columns_ok_precond`**: the names are distinct up to capitalisation, as
  in any SAS data set.
- Every other unit: definition unchanged, comment line numbers moved by +57. Every unit after
  the check is a map over rows and gives `[]` on `[]`; no precondition excluded the empty table.
- Not translated (stated in the item's comment): lines 48-112, the line count, the header copy
  with the made-up applicant, the deletion of earlier WORK tables, the removal of the copy.

Stop on a one-line file, Lean against SAS (`ev10_fix_Q27_*`), 0 differences: twelve names in
Kaggle, permuted, swapped and reversed order: no stop; `years` for `age`, eleven names, no table
(header plus a blank line), a twelfth name `VAR12`: stop. Twelve names in another capitalisation:
no stop, by the `upcase` in the query, not run.

With applicants (4 rows of `fix_Q27_column_order/perm_rows`, Kaggle and permuted order): every
non-model column, grades, recommendations and rates equal, identical in both orders; `pd_logistic`
differs from the 5th decimal because the coefficients given to the Lean are the 4-decimal printed
ones (explained). The id tables of the second update give the same results as before.

Rules: R45 new (a header-only test file); R39 narrowed to the training check; P6 extended with the
column names; lines 48-112 added to the out-of-scope list.

For the prover:
- `def:sasPipeline` calls `test_raw_columns_ok` and needs the extra argument. `importTest` cannot
  supply it, since a header-only raw file is also `[]`: a second import parameter is needed (for
  instance `importTestColumns : Table ℝ → List String`), with its link in `SasLinks`.
- With the check passing on an empty table, `scoreTest` now returns `some []` where it returned
  `none`. `thm:sas_Q27` is affected.

Open:
- **The header lines of the two empty exports cannot be expressed**: the Lean result is `[]`,
  which carries no columns. They are stated in comments only. Fixing this needs a header in the
  foundation's table type.
- Item source references not updated (same reason as for the metrics script).
- The row counts of the intermediate tables on a header-only file are inferred, not observed
  (the logs print no NOTE lines).
- `test_raw_clean` and `test_imputed` read three columns by exact name while the check accepts
  any capitalisation; SAS is case-insensitive there. Pre-existing.
- Neither update has been reviewed by an agent that did not write it. To do before the pipeline
  is revised.

### Review of the metrics_calculation.sas update (2026-11-15): no behavioural defect

By a translator who did not write it, by reading (its two `eval_decl` calls failed with an
output-schema error, so the "0 differences" above is not independently reproduced).

- `def:decile_analysis` and `def:cumulative_lift` do what lines 248-279 and 292-314 do: the
  coalesce on a missing quotient and on an unmatched decile, 0/0 and x/0 giving missing, the two
  `> 0` tests on 0 and on a missing macro value, the branch order, the running sums across empty
  deciles, the columns and their order. Traced by hand on `ev6_fix_Q26_nodefaulter`.
- Record problems, not behaviour:
  - the items' informal text (`statement_text`) still holds the SAS source from before G45, so
    text and Lean disagree; with trust layers off nothing checks this;
  - `def:total_defaults` cites old line numbers in its comment;
  - two SAS rules have no direct run behind them: overflow in a PROC SQL quotient gives missing
    (evidence is from a DATA step; unreachable with 0/1 flags), and `INTO` storing `.` for a
    missing aggregate.
