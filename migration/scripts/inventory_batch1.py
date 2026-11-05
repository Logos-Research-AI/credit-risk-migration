#!/usr/bin/env python3
"""Inventory batch 1 (prompt 02, first 20 rows, complex cases first).

Writes migration/inventory.batch1.tsv. Every row's evidence ends with the gap-sweep
site ids it covers; ids() asserts each cited (file, line) is a real sweep site, so a
wrong line citation fails loudly. Rows are proposals until the skeptic reviewers rule.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITES = list(csv.DictReader(open(ROOT / "migration/gap-sweep.tsv"), delimiter="\t"))
L = "judge/reference/listings"


def ids(file, lines, cats=None):
    out = [s["site_id"] for s in SITES if s["file"] == file and int(s["line"]) in lines
           and (cats is None or s["category"] in cats)]
    assert out, (file, lines, cats)
    return ",".join(out)


ROWS = [
 ("feature_engineering.sas", "work.credit_raw (all columns)", "PROC IMPORT csv, default guessingrows=20", "TYPE_GUESS;BUG",
  "sas_compat.proc_import_csv(data_dir/'cs-training.csv', guessingrows=20): MonthlyIncome -> text, width 5 (values longer than 5 chars TRUNCATED: BUG(port)); NumberOfDependents -> text, width 2; all other columns numeric; empty header -> VAR1; names cut to 32 chars, hyphens kept",
  f"feature_engineering.sas:28-33; informats {L}/feature_engineering.sas.log (MonthlyIncome $5., NumberOfDependents $2., rest best32.); 77 raw incomes >= 100000 truncated (row_id 36716: 159791 -> 15979 in judge/reference/model_features_*.csv); judge mutation fe_import_guessingrows CAUGHT; sites " + ids("feature_engineering.sas", [28], ["PROC"])),
 ("feature_engineering.sas", "MonthlyIncome_num", "input(MonthlyIncome, best32.) on $5. text", "MISSING_SOURCE;BUG",
  "sas_compat.input_best32(col) on the TRUNCATED text: 'NA' -> missing, '15979' (from 159791) -> 15979.0; then drop the text columns and rename the numeric ones to MonthlyIncome / NumberOfDependents",
  f"feature_engineering.sas:49,53-55; 'NA' -> missing with _ERROR_=1 data-line dumps ({L}/feature_engineering.sas.log:81-83 'MonthlyIncome=NA ... MonthlyIncome_num=. _ERROR_=1') then 'WARNING: Limit set by ERRORS= option reached' (log:180); 29,731 NA in raw column 7. drop/rename at :53-55 only rename columns; their position in credit_raw_clean is irrelevant because credit_imputed selects columns explicitly (:99-116); sites " + ids("feature_engineering.sas", [49, 53, 54])),
 ("feature_engineering.sas", "NumberOfDependents_num", "input(NumberOfDependents, best32.) on $2. text", "MISSING_SOURCE",
  "sas_compat.input_best32(col): 'NA' -> missing; no truncation possible (longest raw value is 2 chars)",
  "feature_engineering.sas:50; raw column 12 max length 2 (146,069 len-1, 3,931 len-2 incl. 'NA'); sites " + ids("feature_engineering.sas", [50], ["FUNC"])),
 ("predict.sas", "work.test_raw (all columns)", "PROC IMPORT csv, guessingrows=max", "TYPE_GUESS",
  "sas_compat.proc_import_csv(data_dir/'cs-test.csv', guessingrows=None): MonthlyIncome -> text width 7 (no truncation), NumberOfDependents -> text width 2, SeriousDlqin2yrs -> text width 1 (empty in the test file; never used), rest numeric",
  f"predict.sas:27-33; informats {L}/predict.sas.log (MonthlyIncome $7., NumberOfDependents $2., SeriousDlqin2yrs $1.); sites " + ids("predict.sas", [27], ["PROC"])),
 ("metrics_calculation.sas", "work.logit_scored_valid / logit_scored_train", "PROC IMPORT csv (risk_scores_*), default guessingrows=20", "TYPE_GUESS",
  "sas_compat.proc_import_csv(input_dir/'risk_scores_validation.csv', guessingrows=20) and the same for risk_scores_train.csv (input_dir = the folder holding train's outputs, RULEBOOK §4) (RULEBOOK's one canonical import); metrics uses only default_flag and pd_logistic, which import as numeric. SAS reads interest_rate as $5., truncating '12.00%' to '12.00' (39 train / 17 validation rows): unused by metrics, reproduced by the helper anyway",
  f"metrics_calculation.sas:28,36; informats {L}/metrics_calculation.sas.log (risk_grade $1., recommendation $7., interest_rate $5.); only default_flag and pd_logistic are referenced (metrics_calculation.sas:49-311); both numeric and non-null in every risk_scores input (reference, edge scenarios, real_metrics); sites " + ids("metrics_calculation.sas", [28, 36], ["PROC"])),
 ("feature_engineering.sas", "work.income_medians", "PROC SQL median(MonthlyIncome) where not missing group by calculated age_group", "PROC_SEMANTICS",
  "filter MonthlyIncome not null; age_group = when(age<30)1 .when(age<40)2 .when(age<50)3 .when(age<60)4 .otherwise(5); group_by('age_group', maintain_order=True).agg(median_income = MonthlyIncome.median()); age is never missing, so plain comparisons (MISSING_NEVER, RULEBOOK §2 A2)",
  "feature_engineering.sas:59-73; median of non-missing values, even counts average the middle two (SAS = polars); age has 0 missing and 0 non-numeric values in cs-training.csv; polars medians on the truncated incomes per group (2557/4666/6000/6333/5313) equal the imputed values in judge/reference/model_features_*.csv (review 1); sites " + ids("feature_engineering.sas", [60])),
 ("feature_engineering.sas", "work.credit_imputed", "PROC SQL left join on age_group + CASE imputation + renames + *100", "PROC_SEMANTICS;ORDER",
  "credit_cleaned.join(income_medians, on='age_group', how='left', maintain_order='left'); monthly_income = when(MonthlyIncome_missing == 1).then(median_income).otherwise(MonthlyIncome); select in the SQL's column order with its names (VAR1 -> row_id, ...); credit_utilization = RevolvingUtilizationOfUnsecuredL * 100, debt_ratio = DebtRatio * 100. Row order is not reproduced (SAS's join order is unspecified; the split is an input)",
  "feature_engineering.sas:97-120 (ON clause :119); output column order = select order (judge/reference/model_features_train.csv header); row order is free because the judge matches rows by key (judge/README.md comparison policy); SAS's own output happens to be sorted by age_group (sort-merge join); MonthlyIncome_missing is never missing, so plain == 1; sites " + ids("feature_engineering.sas", [98])),
 ("feature_engineering.sas", "work.credit_split / credit_train / credit_validation", "PROC SURVEYSELECT samprate=0.7 seed=42 outall + split data step", "BUG",
  "NOT reproduced: run(data_dir, output_dir, *, split_ids: Path) takes the reference training row_ids as an external INPUT (split_ids = a CSV with a row_id column, keyword-only; audit FP-04, queued A27), marks selected = row_id in split_ids, splits into credit_train / credit_validation, then drops `selected` (no Selected/SelectionProb/SamplingWeight columns reach the output); BUG(port): SAS split depends on unguaranteed SQL row order",
  "feature_engineering.sas:209-221; judge/README.md (16/17 SAS runs reproduce the split, 1 drifted); sites " + ids("feature_engineering.sas", [209, 216, 218, 220])),
 ("feature_engineering.sas", "flag_low_income", "flag = (monthly_income < 2500)", "MISSING_NEVER",
  "sas_compat.flag(pl.col('monthly_income') < 2500): plain comparison because monthly_income is never missing in feature_engineering",
  "feature_engineering.sas:172; proof for ALL inputs this program receives: its only input is cs-training.csv (scenarios/edge_predict/cs-training.csv is a byte copy, make_scenarios.py), age is never missing, and every age group has non-missing incomes (7,379 / 20,060 / 29,109 / 28,502 / 35,219), so the imputed monthly_income (:103-105) is never missing; also 0 empty in judge/reference/model_features_*.csv; judge mutation fe_low_income_boundary CAUGHT; sites " + ids("feature_engineering.sas", [172], ["CMP"])),
 ("predict.sas", "flag_low_income", "flag = (monthly_income < 2500)", "MISSING_NULLABLE",
  "sas_compat.flag(sas_compat.lt(pl.col('monthly_income'), 2500)): missing < 2500 is 1 in SAS. NEVER the polars default (null -> false)",
  "predict.sas:171; monthly_income is missing when a test age group has no non-missing income (predict imputes from TEST medians, predict.sas:59-73): judge/reference/scenarios/edge_predict/test_predictions.csv has 5,881 rows with empty monthly_income whose total_risk_flags count this flag as 1; judge mutation predict_null_compare_false CAUGHT; sites " + ids("predict.sas", [171], ["CMP"])),
 ("predict.sas", "log_monthly_income / age_income_interaction / income_per_dependent", "log(monthly_income + 1), age * log(...), monthly_income / (num_dependents + 1) with missing income", "MISSING_NULLABLE",
  "sas_compat.sas_log(monthly_income + 1) -> missing when income missing; products and divisions propagate missing (plain polars arithmetic: null propagates, as SAS); num_dependents is never missing (set to 0 at predict.sas:89-90), so `num_dependents > 0` (:150) is a plain comparison",
  "predict.sas:150,190,195; same edge_predict rows; sites " + ids("predict.sas", [150, 190, 195])),
 ("predict.sas", "work.test_scored (pd_logistic)", "PROC PLM restore=work.logit_model score predicted= ; pd = 1/(1+exp(-predicted_logit))", "SESSION_STATE;MISSING_NULLABLE",
  "read input_dir/model.json written by train (predict's input_dir = train's output folder, RULEBOOK §4 run(input_dir, output_dir, ...)); eta = intercept + sum(b_i * x_i), null if ANY model variable is null; pd = 1/(1+exp(-eta)) (null stays null)",
  "predict.sas:208-221 <- train.sas:90 (store); edge_predict: pd empty on the 5,881 rows whose income is missing (log_monthly_income, income_per_dependent, age_income_interaction are model variables, judge/reference/model_coefficients.csv); sites " + ids("predict.sas", [208, 219, 221])),
 ("predict.sas", "credit_risk_score / risk_grade / recommendation / interest_rate / pred_logistic", "round(600+250*(1-pd)) and grade chain when pd is missing", "MISSING_NULLABLE;ROUNDING",
  "credit_risk_score = sas_compat.sas_round(...) (null stays null); grade chain with sas_compat.ge: sas_compat.ge(score, t) is false for a missing score at every threshold, so otherwise('F'); recommendation 'Decline'; interest_rate = base_rate + 0.15 = 0.20, exported with percent8.2 -> '20.00%'; pred_logistic = sas_compat.flag(sas_compat.ge(pd, 0.5)) = 0",
  "predict.sas:229-259; edge_predict reference: 5,881 rows with empty pd and score, risk_grade F, Decline, 20.00%, pred_logistic 0; judge mutation predict_rate_f CAUGHT; sites " + ids("predict.sas", list(range(229, 262)))),
 ("train.sas", "work.logit_scored_train / model_coefficients / stepwise path", "PROC LOGISTIC descending, selection=stepwise slentry=0.05 slstay=0.05", "PROC_SEMANTICS;MODEL_STAT",
  "sas_compat.stepwise_logistic over the 36 candidates in MODEL statement order (train.sas:51-80): (1) intercept-only start; after every step, test REMOVAL first, then ENTRY. (2) REMOVAL: Wald chi-square for each effect in the model; remove the one with the SMALLEST chi-square if its p > 0.05 (ties: first in MODEL order), one per step. (3) ENTRY: for each candidate not in the model, in MODEL order, skip it if it is aliased with the CURRENT model (relative residual V / (z'Wz) < 1e-8, where V is its residual variance after projecting on the model's columns in the information metric; decided per step, never by pre-excluding columns: on this data only flag_serious_delinquency, identical to has_serious_delinquency, is skipped, from step 5); else compute the score chi-square U^2/V at the current fit; enter the LARGEST chi-square (DF=1; strict >, so equal chi-squares go to the FIRST in MODEL order; never select by smallest p, which underflows) if its p < 0.05. (4) Stop when nothing enters or the best entry is the effect just removed. Newton to max|step| < 1e-10 at every step. TODO(port): if an effect with an alias outside the model were ever removed, the alias could enter next and the two could alternate; unreachable on this data",
  f"train.sas:48-95; path in judge/reference/stepwise_summary.csv (24 steps; removals at 17, 21, 24); termination NOTE {L}/train.sas.lst:1026 'No (additional) effects met the 0.05 significance level for entry'; VERIFIED by implementation: migration/experiments/x02_stepwise_reference.py (+ .out) reproduces all 24 EffectEntered/EffectRemoved of judge/reference/stepwise_summary.csv, step-1 score 14471.4043 exactly, other chi-squares within 3.4e-5 relative, stop after step 24 (best = num_credit_lines, just removed, p = 0.0512), residual chi-square 53.5194 on 15 DF vs SAS 53.5184 on 15 DF (lst ~1017); tie-break is load-bearing: at step 4 has_serious_delinquency and flag_serious_delinquency have bitwise-equal score 294.625 and SAS enters the first in MODEL order; aliased residual <= 7e-15 relative vs smallest non-aliased 1.3e-3, so any threshold in [1e-12, 1e-4] gives the same path; sites " + ids("train.sas", [48, 93])),
 ("train.sas", "printed_association.csv", "ODS Association table (concordant/discordant/tied, Somers' D, Gamma, Tau-a, c)", "MODEL_STAT",
  "pairwise over all event x non-event pairs on the final model's pd, NO 0.002 binning, with pairs whose |pd_event - pd_nonevent| <= 1e-8 counted as TIED (SAS tie fuzz); c = (C + T/2)/pairs; Somers' D = (C-D)/pairs, Gamma = (C-D)/(C+D), Tau-a = (C-D)/(n(n-1)/2); FILE LAYOUT: columns Label1,cValue1,nValue1,Label2,cValue2,nValue2; 4 rows in order (Percent Concordant | Somers' D), (Percent Discordant | Gamma), (Percent Tied | Tau-a), (Pairs | c); cValue1 = percents with 1 decimal ('85.9', '0.0'), Pairs as an integer; cValue2 = 3 decimals ('0.718'); nValue1/nValue2 rendered by ONE helper sas_compat.sas_d12_3 (the export format is D12.3, train.sas.log:2459,2462), the same helper as printed_rsquare nValue and printed_fit_statistics InterceptOnly. D12.3 as observed on every D12.3 cell of the reference and 17 judge runs (3,000+ cells): |x| >= 1e4 -> 0 decimals ('686727936', '51478'); 1e-4 <= |x| < 100 -> 6 decimals ('85.922064', '0.718442', '0.000123'); 1e-5 <= |x| < 1e-4 -> 9 decimals ('0.000040773'); last digit rounded half up as A18. TODO(port): magnitudes 100 <= |x| < 1e4 and |x| < 1e-5 never observed; verify with an ODA experiment in the Step 2 sas_compat pilot. Percent Tied is judged with an absolute 1e-5 percentage-point tolerance (human decision Q1, 2026-11-05; RULEBOOK v1.1 A8)",
  'judge/reference/printed_association.csv: 280 tied pairs = 0.000040773% of 686,727,936, concordant 85.922064, discordant 14.077895 (lst:1111-1116); exact comparison (no fuzz) gives 226 ties; on the exported 12-digit pd a fuzz of 1.05e-8 reproduces 280 / 85.922064 / 14.077895 exactly, 1e-8 gives 275 (review 2, scratchpad/invB/fuzz.py; orchestrator re-run); 0.002 binning gives 85.504083 (wrong); a table built by this rule from the converged refit (judge/fixtures/converged, 283 ties) PASSES `compare.py --only printed_association.csv` after the Q1 change, and the judge self-test has 4 Percent Tied cases; sites ' + ids("train.sas", [48])),
 ("train.sas", "credit_risk_score (train + validation blocks)", "round(base_score + score_range * (1 - pd_logistic))", "ROUNDING;MISSING_NEVER",
  "sas_compat.sas_round(600 + 250 * (1 - pd)) (half away from zero, never Python round); pd is never missing in train, so the grade chains (:222-227, :255-260) and pred_logistic = flag(pd >= 0.5) (:105, :165) use plain comparisons",
  "train.sas:219,253; 0 empty pd in judge/reference/risk_scores_{train,validation}.csv; judge mutation train_round_floor CAUGHT; exact .5 ties do not occur on the data (judge README); sites " + ids("train.sas", [105, 165, 219, 222, 223, 224, 225, 226, 253, 255, 256, 257, 258, 259])),
 ("metrics_calculation.sas", "work.ks_calculation / ks_statistic", "PROC SORT by pd; retained cumulative counts; SQL remerge max(ks_value)", "ORDER;PROC_SEMANTICS",
  "sort('pd_logistic', maintain_order=True) on the CSV's row order (PROC SORT EQUALS keeps ties in input order); cum_good = cumulative count of default_flag == 0, cum_bad = cumulative count of everything else (:96-97, else branch); cum_pct_good = sas_compat.div(cum_good, total_good_count), cum_pct_bad = sas_compat.div(cum_bad, total_bad_count) (scalar divisors, A13: plain polars col / scalar differs from IEEE on 12,982 of 45,000 reference rows and can change which rows tie at the maximum; total_*_count are the INTO values, BEST8. per A9, exact integers here); ks_value = abs(cum_pct_good - cum_pct_bad); keep EVERY row whose ks_value equals the maximum (remerge), KS_Statistic = max, KS_Cutoff = that row's pd, both exported with 8.4",
  "metrics_calculation.sas:75-111; real validation data: 252 tied pd values covering 581 rows, maximum on an untied row; ORDER EVIDENCE: on edge scenarios a/b/c the maximum falls inside tie runs of 173/24/183 rows, and only the stable CSV-order sort reproduces SAS's 0.1309/0.0800, 0.1884/0.0760, 0.2959/0.0800 (reversing tie order changes all three) (review 2, scratchpad/invB/ks.py); sites " + ids("metrics_calculation.sas", list(range(75, 112)))),
 ("metrics_calculation.sas", "work.decile_data / decile_analysis", "PROC RANK groups=10 descending; SQL select decile + 1 as decile ... group by decile", "PROC_SEMANTICS",
  "sas_compat.proc_rank_groups(pd, 10, descending=True) (ties = mean rank, group = floor(rank*10/(n+1))); group by rank, output decile = rank + 1 (alias vs source column gives an identical partition); aggregate total_count = count, defaults = sum(default_flag), pd_sum = sum(pd), min_pd, max_pd; then, after the aggregation, default_rate = defaults / total_count and avg_pd = pd_sum / total_count (column / column, the same translation of SQL mean() as the calibration rows); capture_rate = sas_compat.div(defaults, total_defaults) and lift = sas_compat.div(default_rate, overall_default_rate) (scalar divisors, A13; plain polars differs from IEEE in 5/3/4 capture_rate and 2/1/2 lift cells on edge a/b/c; total_defaults / overall_default_rate are the INTO values, BEST8. per A9); export formats percent8.2 (default_rate, capture_rate), 8.4 (avg/min/max_pd), 8.2 (lift)",
  "metrics_calculation.sas:183-205; X01b (migration/experiments/x01_merge_and_alias.lst) shows only that the partition is identical either way; the rank rule reproduces SAS decile total_count and defaults on all four input sets (real, a, b, c) and, with 20 groups, calibration bin_count too (review 2, scratchpad/invB/rank.py); judge mutations metrics_decile_groups, metrics_rank_ties CAUGHT; sites " + ids("metrics_calculation.sas", [183, 192])),
 ("metrics_calculation.sas", "work.psi_calculation / psi_summary", "PROC RANK per set + inner join on score_bin + (a-b)*log(a/b)", "BUG;PROC_SEMANTICS",
  "rank each set separately with sas_compat.proc_rank_groups(pd, 10, descending=False); bin share = sas_compat.div(count, n) (element-wise IEEE division, RULEBOOK amendment A13) AFTER the aggregation: plain polars `count / n` is computed as count * (1/n) and gives 0.09999999999999999 for 10500/105000 even after aggregation, making PSI 1.5e-32 instead of 0 (fan-out review metrics-A; fanout/evidence/psi_div.py: plain 1.54e-32, sas_compat.div 0.0); inner join on score_bin (bins missing on either side drop out); psi_component = (train_pct - valid_pct) * log(train_pct / valid_pct); PSI = sum, exported 8.4; PSI_interpretation = case PSI < 0.1 'No significant change', < 0.25 'Some change', else 'Significant change'. BUG(port): always 0 on real data (each set fills its own deciles)",
  "metrics_calculation.sas:250-287; reproduces every reference psi table: real all 0; a 0.0906; b 1.5743 with only bins {4, 8, 9} surviving the join; c 0.1790 over 8 bins (review 2); judge mutation metrics_psi_sign CAUGHT; sites " + ids("metrics_calculation.sas", [250, 257, 266, 280])),
 ("metrics_calculation.sas", "work.validation_summary", "one-to-one MERGE (no BY) of auc_summary, ks_statistic, psi_summary", "PROC_SEMANTICS",
  "one-to-one merge: rows = max rows of the inputs; values from a shorter input are MISSING (not repeated) on the extra rows, written as empty fields (numeric and text); status per row: sas_compat.ge(AUC, 0.7) & sas_compat.ge(KS, 0.3) & sas_compat.lt(PSI, 0.25) -> 'Production Ready', elif sas_compat.ge(AUC, 0.65) -> 'Requires Review', else 'Needs Improvement' (missing AUC -> 'Needs Improvement'). Same construct for model_performance_metrics (:388-410). Only reachable if KS ties at its maximum (every input set has 1 KS row)",
  "metrics_calculation.sas:331-345; migration/experiments/x01_merge_and_alias.lst (X01a: second row has missing auc and psi); sites " + ids("metrics_calculation.sas", [332, 339, 341, 392])),
]

# after skeptic round 1 (reviews: migration/inventory-review-batch1.md)
STATUS = [  # after skeptic round 1 (inventory-review-batch1.md), the fan-out review and the joint audit
    "confirmed", "confirmed (evidence revised)", "confirmed", "confirmed",
    "confirmed (revised); audit fix TM-09: input_dir",                       # 5 metrics import
    "confirmed (revised); audit fix FP-14: wording",                         # 6 income_medians
    "confirmed (evidence revised)", "confirmed (evidence revised); audit fix FP-04: signature", "confirmed (evidence revised)",
    "confirmed", "confirmed",
    "confirmed (revised at fan-out: input_dir)",                             # 12 PLM
    "confirmed; audit fix FP-14: wording",                                   # 13 predict score/grade
    "confirmed (2nd revision, verified by implementation; DEV-005)",          # 14 stepwise
    "confirmed (resolved by Q1); audit fix TM-02: file layout + D12.3",      # 15 Association
    "confirmed",
    "confirmed (evidence revised); audit fix TM-07: sas_compat.div",         # 17 KS
    "confirmed (evidence revised); audit fix TM-08: sas_compat.div, mean",   # 18 deciles
    "confirmed (revised at fan-out: sas_compat.div, A13)",                    # 19 PSI
    "confirmed",
]


if __name__ == "__main__":
    assert len(ROWS) == 20
    out = ROOT / "migration/inventory.batch1.tsv"
    with open(out, "w") as f:
        f.write("file\tsymbol\tsource_construct\tclassification\ttarget_translation\tevidence\tstatus\n")
        for i, r in enumerate(ROWS):
            f.write("\t".join(r) + "\t" + STATUS[i] + "\n")
    covered = {i for r in ROWS for i in r[5].split("sites ")[-1].split(",")}
    print(f"wrote {out.name}: {len(ROWS)} rows, covering {len(covered)} of {len(SITES)} sweep sites")
