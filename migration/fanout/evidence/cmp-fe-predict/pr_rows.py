from rows_common import *
P="predict.sas"
def chain(col,cuts):
    s=f"pl.when(pl.col('{col}') < {cuts[0]}).then(1)"
    for i,c in enumerate(cuts[1:],2): s+=f".when(pl.col('{col}') < {c}).then({i})"
    return s+f".otherwise({len(cuts)+1})"
NOTEDGE=("predict's only nullable feature is monthly_income (edge_predict: 5,881 rows, batch1 rows 11-12); this operand does not derive from it")
KEEP="test_predictions.csv keeps only row_id, pd, scores, age, monthly_income, credit_utilization, debt_ratio, total_late_payments, num_credit_lines, financial_health, total_risk_flags (predict.sas:275-280)"
R=[]
R.append([P,"age_group (test_income_medians)","PROC SQL CASE WHEN age < 30 / 40 / 50 / 60 THEN 1..4 ELSE 5 + WHERE MonthlyIncome is not missing, group by calculated age_group","MISSING_NEVER;PROC_SEMANTICS;BUG",
 f"test_income_medians = test_raw_clean.filter(pl.col('MonthlyIncome').is_not_null()).with_columns(age_group={chain('age',[30,40,50,60])}).group_by('age_group', maintain_order=True).agg(median_income=pl.col('MonthlyIncome').median()): CASE = one when-chain, first match wins (<30, <40, <50, <60, else 5); plain comparisons (age never missing); `is not missing` = is_not_null() applied BEFORE grouping, so an age group with no non-missing income produces NO row (never a row with a null median). BUG(port): medians come from the TEST set (judge README findings), reproduced as is",
 "predict.sas:59-73 (CASE :62-68, WHERE :71); "+PR_IN.format(cols="age")+"; edge_predict sets MonthlyIncome = NA for every age < 30 row, so group 1 has no non-missing income and gets no median row: recomputation gives medians {2: 4667, 3: 6000, 4: 6260.5, 5: 5395} on edge vs {1: 2516, ...} on the reference, and the resulting missing / imputed monthly_income matches both test_predictions.csv files exactly (5,881 empty on edge, 0 on reference; scratchpad/fan/cmp-fe-predict/verify.py); same construct as FE batch1 row 7; sites S362,S363,S364,S365,S366"])
R.append([P,"age_group","if/else-if chain age < 30 / 40 / 50 / 60 -> 1..4, else 5 (data step test_cleaned)","MISSING_NEVER",
 f"age_group = {chain('age',[30,40,50,60])}: first match wins in source order; plain comparisons (age never missing; a missing age would give 1 in SAS, unreachable). Must equal the test_income_medians CASE because it is the join key",
 "predict.sas:78-83; "+PR_IN.format(cols="age")+"; age 21-104; escapes only as the left-join key to work.test_income_medians (:116-118), not exported ("+KEEP+"); on edge_predict every age_group 1 row joins to no median (row monthly_income (test_imputed)); recomputed age_group drives an imputed monthly_income equal to both test_predictions.csv files (0 mismatches, scratchpad/fan/cmp-fe-predict/verify.py); sites S370,S371,S372,S373"])
R.append([P,"monthly_income (test_imputed)","PROC SQL left join ON a.age_group = b.age_group + CASE WHEN a.MonthlyIncome_missing = 1 THEN b.median_income ELSE a.MonthlyIncome","MISSING_NEVER;MISSING_SOURCE;BUG",
 "test_cleaned.join(test_income_medians, on='age_group', how='left', maintain_order='left'); monthly_income = pl.when(pl.col('MonthlyIncome_missing') == 1).then(pl.col('median_income')).otherwise(pl.col('MonthlyIncome')): both comparisons plain (operands never missing). MISSING_SOURCE: when a test age group has no median row the left join leaves median_income null, so monthly_income is NULL (SAS missing) and must stay null (no fill): downstream comparisons on it use sas_compat helpers (batch1 rows 11-12). BUG(port): imputes from TEST-set medians",
 "predict.sas:86-87,96-118 (CASE :102-104, ON :118); MonthlyIncome_missing is assigned 1/0 by if/else on every row (:86-87), never missing; a.age_group always assigned by the chain :79-83 and b.age_group by the CASE with ELSE 5 (:62-68), so SAS SQL's missing = missing join match (which polars' default join does not do) is unreachable; age never missing on both test inputs (row age_group); judge/reference/scenarios/edge_predict/test_predictions.csv has 5,881 empty monthly_income, exactly the age < 30 rows (age_group 1), and the reference file 0; recomputation matches both files value-for-value (scratchpad/fan/cmp-fe-predict/verify.py); sites S379,S380"])
R.append([P,"has_delinquency","flag = (total_late_payments > 0)","MISSING_NEVER",
 "has_delinquency = sas_compat.flag(pl.col('total_late_payments') > 0): plain comparison; Int64 0/1; computed before financial_health (:185 reads it)",
 "predict.sas:129,132; total_late_payments = sum() (:129) of three counts, each "+PR_IN.format(cols="NumberOfTime30-59DaysPastDueNotWorse, NumberOfTime60-89DaysPastDueNotWorse, NumberOfTimes90DaysLate")+"; "+NOTEDGE+"; escapes as model variable into PROC PLM (:208, model_coefficients.csv) and financial_health (:185); "+PR_VER.format(what="total_late_payments and financial_health (which uses this flag)")+"; sites S383"])
R.append([P,"has_serious_delinquency","flag = (num_late_90_plus > 0)","MISSING_NEVER",
 "has_serious_delinquency = sas_compat.flag(pl.col('num_late_90_plus') > 0): plain comparison; Int64 0/1",
 "predict.sas:111,135; "+PR_IN.format(cols="NumberOfTimes90DaysLate")+"; "+NOTEDGE+"; escapes only as model variable into PROC PLM (:208; model_coefficients.csv has_serious_delinque), not exported; same comparison as FE row has_serious_delinquency, which matches the reference on 150,000 rows; sites S384"])
R.append([P,"credit_util_category","if/else-if chain credit_utilization < 30 / 50 / 75 -> 1..3, else 4","MISSING_NEVER",
 f"credit_util_category = {chain('credit_utilization',[30,50,75])}: first match wins in source order; plain comparisons (a missing value would give 1 in SAS, unreachable)",
 "predict.sas:112,137-141; credit_utilization = RevolvingUtilizationOfUnsecuredL * 100 (:112); "+PR_IN.format(cols="RevolvingUtilizationOfUnsecuredLines")+"; no product equals 30/50/75 exactly; "+NOTEDGE+"; escapes only as model variable into PROC PLM (:208), not exported; identical code to FE row credit_util_category (0 mismatches on 150,000 rows); sites S385,S386,S387"])
R.append([P,"debt_category","if/else-if chain debt_ratio < 30 / 43 / 60 -> 1..3, else 4","MISSING_NEVER",
 f"debt_category = {chain('debt_ratio',[30,43,60])}: first match wins in source order; plain comparisons (a missing value would give 1 in SAS, unreachable). Translated for structure only: the value is dead in predict",
 "predict.sas:113,143-147; debt_ratio = DebtRatio * 100 (:113); "+PR_IN.format(cols="DebtRatio")+"; "+NOTEDGE+"; DEAD in predict: not a model variable (model_coefficients.csv) and not exported ("+KEEP+"), so unjudged; identical code to FE row debt_category (0 mismatches on 150,000 rows); sites S388,S389,S390"])
R.append([P,"age_category","if/else-if chain age < 25 / 35 / 50 / 65 -> 1..4, else 5","MISSING_NEVER",
 f"age_category = {chain('age',[25,35,50,65])}: first match wins in source order; plain comparisons (a missing age would give 1 in SAS, unreachable). Translated for structure only: the value is dead in predict",
 "predict.sas:156-161; "+PR_IN.format(cols="age")+"; DEAD in predict: not a model variable and not exported ("+KEEP+"), so unjudged; identical code to FE row age_category (0 mismatches on 150,000 rows); sites S394,S395,S396,S397"])
FL=[("flag_high_utilization","credit_utilization > 75",164,"credit_utilization","RevolvingUtilizationOfUnsecuredLines","S398","model variable into PROC PLM and total_risk_flags (:176, exported)",True),
    ("flag_very_high_utilization","credit_utilization > 100",165,"credit_utilization","RevolvingUtilizationOfUnsecuredLines","S399","model variable into PROC PLM only, not exported (12 rows exactly 100.0 -> 0; FE row matches SAS on the same boundary)",False),
    ("flag_high_debt_ratio","debt_ratio > 43",166,"debt_ratio","DebtRatio","S400","total_risk_flags (:176, exported); not a model variable",True),
    ("flag_very_high_debt_ratio","debt_ratio > 60",167,"debt_ratio","DebtRatio","S401","model variable into PROC PLM only, not exported (one reference row has debt_ratio exactly 60.0 -> 0, strict >)",False),
    ("flag_recent_late_payments","num_late_30_59 > 0",168,"num_late_30_59","NumberOfTime30-59DaysPastDueNotWorse","S402","model variable into PROC PLM only, not exported",False),
    ("flag_serious_delinquency","num_late_90_plus > 0",169,"num_late_90_plus","NumberOfTimes90DaysLate","S403","total_risk_flags (:176, exported); not a model variable",True),
    ("flag_multiple_delinquencies","total_late_payments >= 3",170,"total_late_payments","NumberOfTime30-59DaysPastDueNotWorse, NumberOfTime60-89DaysPastDueNotWorse, NumberOfTimes90DaysLate","S404","model variable into PROC PLM and total_risk_flags (:176, exported)",True),
    ("flag_many_dependents","num_dependents >= 3",172,"num_dependents",None,"S406","DEAD in predict: not a model variable and not exported, so unjudged",False),
    ("flag_few_credit_lines","num_credit_lines <= 2",173,"num_credit_lines","NumberOfOpenCreditLinesAndLoans","S407","model variable into PROC PLM only, not exported (a missing value would give 1 in SAS since . <= 2 is true; unreachable)",False),
]
for sym,cond,ln,col,raw,site,esc,in_trf in FL:
    op=cond.split()[1]; c=cond.split()[2]
    if col=="num_dependents":
        proof=("num_dependents: raw NumberOfDependents is missing only for 2,626 'NA' values in both test inputs, which :89-90 resets to 0 (Dependents_missing = 1); "
               "every other value is numeric (0 non-numeric in data/cs-training.csv... cs-test.csv and judge/scenarios/edge_predict/cs-test.csv), so never missing; unlike monthly_income (not reset, nullable on edge_predict)").replace("data/cs-training.csv... ","")
    elif col=="total_late_payments":
        proof="total_late_payments = sum() (:129) of three counts, each "+PR_IN.format(cols=raw)
    else:
        proof=PR_IN.format(cols=raw)
    ver = PR_VER.format(what="total_risk_flags (this flag summed with the others, flag_low_income per sas_compat.lt)") if in_trf else f"identical code to FE row {sym} (0 mismatches on 150,000 rows)"
    R.append([P,sym,f"flag = ({cond})","MISSING_NEVER",
     f"{sym} = sas_compat.flag(pl.col('{col}') {op} {c}): plain comparison ({col} never missing on any predict input, edge_predict included); Int64 0/1",
     f"predict.sas:{ln}; {proof}; {NOTEDGE}; escapes: {esc}; {ver}; sites {site}"])
R.append([P,"financial_health","five independent if-then deductions from 100 (cu > 30, cu > 75, debt_ratio > 43, truthy has_delinquency, num_late_90_plus > 0)","MISSING_NEVER",
 "financial_health = 100 - pl.when(pl.col('credit_utilization') > 30).then(15).otherwise(0) - pl.when(pl.col('credit_utilization') > 75).then(15).otherwise(0) - pl.when(pl.col('debt_ratio') > 43).then(20).otherwise(0) - pl.when(pl.col('has_delinquency') != 0).then(20).otherwise(0) - pl.when(pl.col('num_late_90_plus') > 0).then(30).otherwise(0), then max(0, .) per S419 (arith shard). Independent ifs, not an else-if chain; `if has_delinquency` (SAS truthiness: not missing and not 0) -> `!= 0`, plain because has_delinquency is a non-null 0/1 flag computed in an earlier with_columns. No operand derives from monthly_income, so the value is NOT missing on the 5,881 edge_predict rows either",
 "predict.sas:180-187; credit_utilization (:112), debt_ratio (:113), num_late_90_plus (:111): "+PR_IN.format(cols="RevolvingUtilizationOfUnsecuredLines, DebtRatio, NumberOfTimes90DaysLate")+"; has_delinquency from :132 (row has_delinquency); deductions total at most 100, never below 0 before max(0, .); escapes as exported column (:275-280) and model variable; "+PR_VER.format(what="financial_health (0 empty in both files, including the 5,881 rows with empty monthly_income)")+"; sites S410,S412,S414,S416,S418"])
append(R); print(len(R))
