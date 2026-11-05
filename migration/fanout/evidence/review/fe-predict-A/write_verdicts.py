import csv
R = "/Users/cristophersalvi/GitHub/sas-migration/"
rows = list(csv.reader(open(R + "migration/fanout/review-batch.fe-predict.tsv"), delimiter="\t"))[1:]
assert len(rows) == 81

REC = "independent polars recomputation from the raw CSV (scratchpad/review/fe-predict-A/recompute.py)"
FE_ALL = f"{REC} matches every row of judge/reference/model_features_{{train,validation}}.csv under BEST12 (0 mismatches)"
PR_ALL = f"{REC} matches judge/reference/test_predictions.csv and scenarios/edge_predict/test_predictions.csv on all 101,503 rows each (0 mismatches)"
RAWP = "raw profile: data/cs-test.csv and scenarios/edge_predict/cs-test.csv have 0 empty/NA/non-numeric cells in every used column except MonthlyIncome (20,103 / 25,003 NA) and NumberOfDependents (2,626 NA); on edge_predict only monthly_income, income_per_dependent, log_monthly_income, age_income_interaction come out null (5,881 rows each)"
RAWF = "raw profile: data/cs-training.csv (byte-identical edge copy) has 0 empty/NA/non-numeric cells in every column except MonthlyIncome (29,731 NA) and NumberOfDependents (3,924 NA)"

V = {}
def v(i, verdict, cite, reason):
    V[i] = (verdict, cite, reason)

v(1, "CONFIRMED", "feature_engineering.sas:20-21,28,268,275,281-282", "Lines check out: &data_path is used only at :28, &output_path at :268/:275/:281-282; positional (input dir, output dir) order matches RULEBOOK §4. The %put lines :280/:283/:284 have no macro reference and no sweep site.")
v(2, "CONFIRMED", "feature_engineering.sas:36-38,227-247", "All five PROCs have no out=/ods output and are listing-only per RULEBOOK §2 [DECIDED]. Sites S004 and S082-S085 are all covered.")
v(3, "CONFIRMED", "feature_engineering.sas:59", "This is a pointer row for the PROC SQL statement. Its content is in batch1 row 6 (S010-S017), and the polars medians 2557/4666/6000/6333/5313 on the truncated incomes reproduce the reference imputations.")
v(4, "EVIDENCE_DEFECT", "migration/inventory.batch1.tsv data row 6 (work.income_medians)", f"Translation is right ({FE_ALL}; age 0 empty, min 0 on 1 row). Defect: 'income_medians CASE (batch1 row 7)' points to data row 7 = work.credit_imputed. Batch1 numbering is by data row (inventory-review-batch1.md: row 14 = stepwise), so the fix is 'batch1 row 6'.")
v(5, "CONFIRMED", "feature_engineering.sas:86-87", f"The flag is correct and never missing; 29,731 'NA' and 0 empty in raw column 7. {FE_ALL}.")
v(6, "CONFIRMED", "feature_engineering.sas:89-93", f"Both expressions read the pre-imputation column, which is correct. NA = 3,924 and numeric 0-20; 0 null num_dependents after the step. {FE_ALL}.")
v(7, "CONFIRMED", "feature_engineering.sas:97", "This is a pointer row for the PROC SQL statement. Its content is in batch1 row 7 (S025-S029).")
v(8, "CONFIRMED", "feature_engineering.sas:130", f"{RAWF}. sas_sum equals plain + here and the result is never missing. {FE_ALL}.")
v(9, "CONFIRMED", "feature_engineering.sas:133", f"Plain > 0 is right: 119,637 rows have exactly 0. {FE_ALL}.")
v(10, "CONFIRMED", "feature_engineering.sas:112,136", f"NumberOfTimes90DaysLate has 0 missing on both FE inputs. {FE_ALL}.")
v(11, "CONFIRMED", "feature_engineering.sas:113,139-142", f"No credit_utilization equals 30, 50 or 75 exactly, and 0 are missing. {FE_ALL}.")
v(12, "CONFIRMED", "feature_engineering.sas:114,145-148", f"One row has debt_ratio == 30.0 and gets category 2, matching SAS; 0 missing. {FE_ALL}.")
v(13, "EVIDENCE_DEFECT", "migration/inventory.batch1.tsv data row 10 (predict flag_low_income, says income CAN be missing)", f"Translation is right ({FE_ALL}, 0 BEST12 mismatches). Defect: 'monthly_income is never missing in FE (batch1 row 10)' points to PREDICT's flag_low_income row, which says the opposite. The same evidence uses data-row numbering for 'batch1 row 3', so it is inconsistent. Fix: 'batch1 row 9'.")
v(14, "CONFIRMED", "feature_engineering.sas:151-152", f"The divisor is >= 2 in the then-branch, so plain / is right. {FE_ALL}. Same expression as the S039 row.")
v(15, "CONFIRMED", "feature_engineering.sas:155", f"The divisor is >= 1 and never missing. {FE_ALL}.")
v(16, "CONFIRMED", "feature_engineering.sas:158-162", f"Boundary counts reproduced: 953/2,246/3,753/2,594. {FE_ALL}.")
v(17, "CONFIRMED", "feature_engineering.sas:165", f"0 rows exactly 75, 0 missing. {FE_ALL}.")
v(18, "CONFIRMED", "feature_engineering.sas:166", f"17 rows exactly 100.0 give 0, as in SAS. {FE_ALL}.")
v(19, "CONFIRMED", "feature_engineering.sas:167", f"0 rows exactly 43. It is not a model variable (judge/reference/model_coefficients.csv). {FE_ALL}.")
v(20, "CONFIRMED", "feature_engineering.sas:168", f"0 FE rows exactly 60; it is a model variable (flag_very_high_debt_). {FE_ALL}.")
v(21, "CONFIRMED", "feature_engineering.sas:169", f"{FE_ALL}; it is a model variable (flag_recent_late_pay).")
v(22, "EVIDENCE_DEFECT", "migration/inventory.batch1.tsv data row 14 (stepwise)", f"Translation is right ({FE_ALL}). Defect: 'stepwise skips it as aliased (batch1 row 15)' points to data row 15 = Association table. Fix: 'batch1 row 14' (inventory-review-batch1.md and RULEBOOK DEV-005 call stepwise row 14).")
v(23, "CONFIRMED", "feature_engineering.sas:171", f"2,884 rows exactly 3 give 1. {FE_ALL}.")
v(24, "CONFIRMED", "feature_engineering.sas:173", f"9,483 rows exactly 3; not a model variable. {FE_ALL}.")
v(25, "CONFIRMED", "feature_engineering.sas:174", f"{FE_ALL}.")
v(26, "CONFIRMED", "feature_engineering.sas:177-179", f"Every flag is a non-null 0/1, so the sum is never missing. {FE_ALL}.")
v(27, "CONFIRMED", "feature_engineering.sas:182-188", f"Pre-clamp minimum is 0 on exactly 2,127 rows, never negative. {FE_ALL}. Note: this row and the S058.. row give two equivalent forms (Float 100.0 chain vs Int 100 minus deductions); output is identical under BEST12.")
v(28, "CONFIRMED", "feature_engineering.sas:183-187", f"The ifs are independent, not else-if, and truthiness becomes != 0 on a non-null flag. {FE_ALL}.")
v(29, "CONFIRMED", "feature_engineering.sas:191", f"The argument is >= 1 because monthly_income is never missing in FE and min 0. {FE_ALL}.")
v(30, "CONFIRMED", "feature_engineering.sas:192", f"{FE_ALL}.")
v(31, "CONFIRMED", "feature_engineering.sas:193", f"{FE_ALL}.")
v(32, "CONFIRMED", "feature_engineering.sas:196", f"{FE_ALL}.")
v(33, "CONFIRMED", "judge/reference/model_features_{train,validation}.csv utilization_debt_interaction", "Reproduced exactly: polars `/100` is bitwise equal to multiplying by the reciprocal on all 150,000 rows, and it misses 361 BEST12 cells vs 424 for IEEE (cu*dr)/100. Where the two forms print differently (79 cells) SAS agrees with polars 71 times; every residual is at most 1 unit in the 12th character. Consistent with v1.1 plain arithmetic. The queued A13 (sas_compat.div = IEEE for scalar divisors) would make this site slightly WORSE.")
v(34, "CONFIRMED", "feature_engineering.sas:200", f"{FE_ALL}.")
v(35, "CONFIRMED", "feature_engineering.sas:201", f"{FE_ALL}.")
v(36, "RULEBOOK_CONFLICT", "judge/reference/model_features_train.csv row_id 41700 utilization_debt_interaction = 9.670322E-6", "Row is right: the 42-column order equals the header, there are no CR and no empties, and the stated E rule reproduces all 13 E cells (9 train + 4 validation) from recomputed values. RULEBOOK v1.1 §2 PROC EXPORT names a sas_best12 described by the judge's plain-only helper, so an implementer following it prints 0.0000096703 and fails format_ok. The pending A15 must be applied.")
v(37, "RULEBOOK_CONFLICT", "judge/reference/model_features_validation.csv utilization_debt_interaction (4 E cells, e.g. row_id 16380 6.6978029E-6)", "Row is right: same 42 columns and the 4 E cells reproduced by the stated rule. RULEBOOK v1.1 §2's sas_best12 (plain-only) would print them in plain notation. Needs A15.")
v(38, "EVIDENCE_DEFECT", "migration/RULEBOOK.md §4 'run(input_dir: Path, output_dir: Path, ...)'", "Paths, %put lines and model.json handling are right. Defect: the row cites §4 for run(data_dir, input_dir, output_dir), but §4 fixes the positional order (input_dir, output_dir, ...). The FE twin row keeps (in, out). Fix: run(input_dir, output_dir, data_dir) (or keyword-only data_dir), or queue a §4 amendment.")
v(39, "CONFIRMED", "predict.sas:36-38,302-316", "No out=/ods output; all four are listing-only per RULEBOOK §2. Sites S356 and S459-S461 are covered.")
v(40, "CONFIRMED", "judge/reference/listings/predict.sas.log:62 (informat MonthlyIncome $7.)", "Log lines :62, :122-124 and :180 say what is claimed. NA counts 20,103 / 25,003 and max 7,727,000 reproduced; 0 other non-numeric text.")
v(41, "CONFIRMED", "judge/reference/listings/predict.sas.log:67", "$2. informat; 2,626 NA in both inputs and numeric max 43 reproduced.")
v(42, "CONFIRMED", "predict.sas:45-56,99-115", "Replacing in place is safe: test_imputed selects its columns explicitly and test_income_medians reads only age and MonthlyIncome.")
v(43, "CONFIRMED", "predict.sas:59-73", f"An empty group gets no row (edge_predict medians: only groups 2-5). {PR_ALL}.")
v(44, "EVIDENCE_DEFECT", "migration/inventory.batch1.tsv data row 6 (work.income_medians)", f"Translation is right: edge medians {{2:4667, 3:6000, 4:6260.5, 5:5395}} and reference {{1:2516,...}} reproduced, and both logs :56-67 are the informat lines. Defect: 'same construct as FE batch1 row 7' points to work.credit_imputed. Fix: 'batch1 row 6'.")
v(45, "CONFIRMED", "judge/reference/test_predictions.csv monthly_income (imputed 6260.5 for group 4)", f"Medians 2516/4667/6000/6260.5/5395 reproduced. {PR_ALL}, including the 5,881 empty incomes on edge.")
v(46, "CONFIRMED", "predict.sas:59-73", "Per-group non-missing counts 4900/13502/19809/19220/23969 (edge 0/...) and age min 21 reproduced. Minor: the parenthetical '(same when-chain, Int64)' is wrong, since pl.when(..).then(1) is Int32 in polars 2.1. The operative rule (both sides the same chain, so the same dtype) holds.")
v(47, "CONFIRMED", "predict.sas:79-83", f"Age 21-104, 0 missing on both inputs. age_group is not exported or a model variable. {PR_ALL}.")
v(48, "CONFIRMED", "predict.sas:86-87", "Null exactly on the NA cells (20,103 / 25,003). The flag is never missing.")
v(49, "CONFIRMED", "predict.sas:89-93", "2,626 NA in both inputs, numeric min 0; num_dependents has 0 nulls after the step.")
v(50, "CONFIRMED", "predict.sas:97-119", f"A null median gives a null monthly_income on exactly the 5,881 age<30 rows of edge_predict. {PR_ALL}.")
v(51, "CONFIRMED", "predict.sas:112-113", f"{RAWP}. credit_utilization and debt_ratio match both test_predictions.csv files exactly.")
v(52, "EVIDENCE_DEFECT", "migration/inventory.batch1.tsv data rows 10 (lt) and 13 (ge)", f"Translation is right: MonthlyIncome_missing and both age_group sides are never null, and the null-key join is unreachable. {PR_ALL}. Defect: 'downstream comparisons on it use sas_compat helpers (batch1 rows 11-12)' points to rows 11 (sas_log/arithmetic, plain num_dependents > 0) and 12 (PLM). Fix: cite row 10 (flag_low_income, lt), with rows 11-13 for the consequences.")
v(53, "CONFIRMED", "judge/compare.py:81-82", f"Select order matches, VAR1 is unique in both inputs, the reference is unsorted by row_id, and KEYS are row_id. {PR_ALL}.")
v(54, "CONFIRMED", "predict.sas:129", f"{RAWP}. {PR_ALL}.")
v(55, "CONFIRMED", "predict.sas:132", f"{RAWP}. financial_health (which uses this flag) matches. {PR_ALL}.")
v(56, "CONFIRMED", "predict.sas:135", f"{RAWP}. It is a model variable (has_serious_delinque) and not exported.")
v(57, "CONFIRMED", "predict.sas:138-140", f"{RAWP}. No product equals 30/50/75 exactly on either test input. It is a model variable.")
v(58, "CONFIRMED", "predict.sas:144-146", f"{RAWP}. Dead: not in model_coefficients.csv and not in the keep list (:277-280).")
v(59, "CONFIRMED", "predict.sas:154", f"{RAWP}. 0 nulls, divisor >= 1; it is a model variable.")
v(60, "CONFIRMED", "predict.sas:157-161", f"{RAWP}. Dead: not a model variable and not exported.")
v(61, "CONFIRMED", "predict.sas:164", f"{RAWP}. total_risk_flags matches on both files.")
v(62, "CONFIRMED", "predict.sas:165", f"{RAWP}. 12 test rows have exactly 100.0; it is a model variable and not exported.")
v(63, "CONFIRMED", "predict.sas:166", f"{RAWP}. Not a model variable; total_risk_flags matches on both files.")
v(64, "CONFIRMED", "predict.sas:167", f"{RAWP}. 1 test row has exactly 60.0; it is a model variable.")
v(65, "CONFIRMED", "predict.sas:168", f"{RAWP}. Model variable (flag_recent_late_pay).")
v(66, "CONFIRMED", "predict.sas:169", f"{RAWP}. Not a model variable (aliased); total_risk_flags matches.")
v(67, "CONFIRMED", "predict.sas:170", f"{RAWP}. total_risk_flags matches on both files.")
v(68, "CONFIRMED", "predict.sas:172", f"{RAWP}. Dead: not a model variable and not exported.")
v(69, "CONFIRMED", "predict.sas:173", f"{RAWP}. Model variable (flag_few_credit_line).")
v(70, "CONFIRMED", "judge/reference/scenarios/edge_predict/test_predictions.csv total_risk_flags (0 empty on the 5,881 empty-income rows)", f"flag(lt(null, 2500)) = 1 keeps the sum non-null. {PR_ALL}.")
v(71, "CONFIRMED", "predict.sas:181-187", f"No operand derives from monthly_income; pre-clamp min 0 on both inputs. {PR_ALL}. Same overlap with the S410.. row as in FE (equivalent forms).")
v(72, "CONFIRMED", "predict.sas:182-186", f"Financial_health has 0 empties in both files, including the 5,881 rows with empty income. {PR_ALL}.")
v(73, "CONFIRMED", "predict.sas:191", f"{RAWP}. 0 nulls recomputed.")
v(74, "CONFIRMED", "predict.sas:192", "total_late_payments is never missing on either input, so the argument is >= 1. 0 nulls recomputed.")
v(75, "CONFIRMED", "predict.sas:196", "Same form as the FE row (verified there). Not in model_coefficients.csv and not in test_predictions.csv, so the last bit is unjudged here.")
v(76, "CONFIRMED", "predict.sas:199", f"{RAWP}. Model variable credit_utilization_c.")
v(77, "CONFIRMED", "predict.sas:200", f"{RAWP}. Model variable debt_ratio_capped.")
v(78, "CONFIRMED", "judge/reference/kaggle_submission.csv header", "Header row_id,pd_logistic. Keep order and PDV order coincide; key row_id at judge/compare.py:82.")
v(79, "CONFIRMED", "judge/reference/test_predictions.csv header", "The PDV-filtered order row_id..interest_rate equals the reference and edge headers and differs from the keep-list order. This is consistent with §2's 'preserve SAS column order rules' (and the queued A12).")
v(80, "RULEBOOK_CONFLICT", "judge/reference/kaggle_submission.csv row_id 24163 pd_logistic = 8.406611E-51", "Row is right: 6 E cells at exactly the cited row_ids, the 5,881 empty pd on edge, log :444-445/:455 as cited, and the E rule matches the reference strings. RULEBOOK v1.1 §2's plain sas_best12 prints '0' for this cell and fails format_ok. Needs A15.")
v(81, "RULEBOOK_CONFLICT", "judge/reference/test_predictions.csv pd_logistic E cells (6, same row_ids as kaggle)", "Row is right: header order, interest_rate values {5,7,9,12}% (+20.00% x 5,881 on edge), and on missing-pd rows F/Decline/20.00%/0 with empty income/pd/score, all verified; log :516-530/:553 as cited. The pd E-notation cells need A15, because §2's plain sas_best12 prints them in plain notation.")

assert len(V) == 81, sorted(set(range(1, 82)) - set(V))
out = R + "migration/fanout/review.fe-predict-A.tsv"
with open(out, "w", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, escapechar=None)
    w.writerow(["file", "symbol", "source_construct", "verdict", "cited_line", "reason"])
    for i, r in enumerate(rows, 1):
        verdict, cite, reason = V[i]
        for x in (cite, reason):
            assert "\t" not in x and "\n" not in x
        w.writerow([r[0], r[1], r[2], verdict, cite, reason])
from collections import Counter
print(Counter(x[0] for x in V.values()))
