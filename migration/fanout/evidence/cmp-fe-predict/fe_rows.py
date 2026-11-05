from rows_common import *
F="feature_engineering.sas"
def chain(col,cuts):
    s=f"pl.when(pl.col('{col}') < {cuts[0]}).then(1)"
    for i,c in enumerate(cuts[1:],2): s+=f".when(pl.col('{col}') < {c}).then({i})"
    return s+f".otherwise({len(cuts)+1})"
rows=[]
ROWS=[]
# 1 age_group
ROWS.append([F,"age_group","if/else-if chain age < 30 / 40 / 50 / 60 -> 1..4, else 5 (data step credit_cleaned)","MISSING_NEVER",
 f"age_group = {chain('age',[30,40,50,60])}: one when-chain, first match wins in source order (<30, <40, <50, <60, else 5); plain comparisons because age is never missing. (Were age missing, SAS would give 1 since . < 30 is true; unreachable.) Must stay identical to the income_medians CASE (batch1 row 7) because it is the join key",
 "feature_engineering.sas:78-83; "+FE_IN.format(cols="age")+"; age min 0 (one row -> group 1) max 109; escapes as the left-join key to work.income_medians (:117-119) and as column age_group of model_features_*.csv; "+FE_VER.format(what="age_group")+"; sites S018,S019,S020,S021"])
# 2 has_delinquency
ROWS.append([F,"has_delinquency","flag = (total_late_payments > 0)","MISSING_NEVER",
 "has_delinquency = sas_compat.flag(pl.col('total_late_payments') > 0): plain comparison (total_late_payments never missing); Int64 0/1. Computed in a with_columns AFTER total_late_payments (:130) and BEFORE financial_health (:186 reads it)",
 "feature_engineering.sas:130,133; total_late_payments = sum() (:130, S030) of num_late_30_59 / num_late_60_89 / num_late_90_plus, each "+FE_IN.format(cols="NumberOfTime30-59DaysPastDueNotWorse, NumberOfTime60-89DaysPastDueNotWorse, NumberOfTimes90DaysLate")+" and passed through credit_imputed unchanged (:110-112), so the sum is never missing (min 0, 119,637 rows exactly 0 -> 0); escapes as model_features column, train model variable (judge/reference/model_coefficients.csv) and financial_health (:186); "+FE_VER.format(what="has_delinquency")+"; sites S031"])
# 3 has_serious_delinquency
ROWS.append([F,"has_serious_delinquency","flag = (num_late_90_plus > 0)","MISSING_NEVER",
 "has_serious_delinquency = sas_compat.flag(pl.col('num_late_90_plus') > 0): plain comparison; Int64 0/1 (bitwise equal to flag_serious_delinquency, :170)",
 "feature_engineering.sas:112,136; num_late_90_plus = NumberOfTimes90DaysLate; "+FE_IN.format(cols="NumberOfTimes90DaysLate")+"; escapes as model_features column and train model variable (model_coefficients.csv has_serious_delinque); "+FE_VER.format(what="has_serious_delinquency")+"; sites S032"])
# 4 credit_util_category
ROWS.append([F,"credit_util_category","if/else-if chain credit_utilization < 30 / 50 / 75 -> 1..3, else 4","MISSING_NEVER",
 f"credit_util_category = {chain('credit_utilization',[30,50,75])}: first match wins in source order; plain comparisons (credit_utilization never missing; a missing value would give 1 in SAS, unreachable)",
 "feature_engineering.sas:113,138-142; credit_utilization = RevolvingUtilizationOfUnsecuredL * 100 (:113); "+FE_IN.format(cols="RevolvingUtilizationOfUnsecuredLines")+"; no product equals 30, 50 or 75 exactly, and the IEEE product is the same in SAS and polars (recomputation below); escapes as model_features column and train model variable; "+FE_VER.format(what="credit_util_category")+"; sites S033,S034,S035"])
# 5 debt_category
ROWS.append([F,"debt_category","if/else-if chain debt_ratio < 30 / 43 / 60 -> 1..3, else 4","MISSING_NEVER",
 f"debt_category = {chain('debt_ratio',[30,43,60])}: first match wins in source order; plain comparisons (debt_ratio never missing; a missing value would give 1 in SAS, unreachable)",
 "feature_engineering.sas:114,144-148; debt_ratio = DebtRatio * 100 (:114); "+FE_IN.format(cols="DebtRatio")+"; one row has debt_ratio exactly 30.0 (-> 2, strict <) and SAS agrees; escapes as model_features column (not selected by the model); "+FE_VER.format(what="debt_category")+"; sites S036,S037,S038"])
# 6 income_per_dependent branch
ROWS.append([F,"income_per_dependent","if num_dependents > 0 then ... else ... (branch condition)","MISSING_NEVER",
 "income_per_dependent = pl.when(pl.col('num_dependents') > 0).then(pl.col('monthly_income') / (pl.col('num_dependents') + 1)).otherwise(pl.col('monthly_income')): plain comparison because num_dependents is never missing (a missing value would take the else branch in SAS, . > 0 false; unreachable). The divisor in the then-branch is >= 2, never 0 (division itself: S040, arith shard)",
 "feature_engineering.sas:89-93,107,150-152; NumberOfDependents is missing only for the 3,924 raw 'NA' values (input(...,best32.), :50; batch1 row 3) and :89-90 resets every missing value to 0; all other raw values are numeric 0-20 in data/cs-training.csv and its byte-identical edge_predict copy, so num_dependents is never missing; monthly_income is never missing in FE (batch1 row 10); escapes as model_features column and train model variable; recomputation with this branch matches judge/reference/model_features_*.csv within 2e-10 relative (BEST12 printing) on all 150,000 rows (scratchpad/fan/cmp-fe-predict/verify.py); sites S039"])
# 7 age_category
ROWS.append([F,"age_category","if/else-if chain age < 25 / 35 / 50 / 65 -> 1..4, else 5","MISSING_NEVER",
 f"age_category = {chain('age',[25,35,50,65])}: first match wins in source order; plain comparisons (age never missing; a missing age would give 1 in SAS, unreachable)",
 "feature_engineering.sas:157-162; "+FE_IN.format(cols="age")+"; integer ages, boundaries 25/35/50/65 hit exactly by 953/2,246/3,753/2,594 rows (strict < puts them in the next category), SAS agrees; escapes as model_features column (not selected by the model); "+FE_VER.format(what="age_category")+"; sites S042,S043,S044,S045"])
# flags
FL=[("flag_high_utilization","credit_utilization > 75",165,"credit_utilization","RevolvingUtilizationOfUnsecuredLines","S046","model variable and total_risk_flags (:177)"," (0 rows exactly 75)"),
    ("flag_very_high_utilization","credit_utilization > 100",166,"credit_utilization","RevolvingUtilizationOfUnsecuredLines","S047","model variable"," (17 rows exactly 100.0 = raw 1 * 100 -> 0, strict >; SAS agrees)"),
    ("flag_high_debt_ratio","debt_ratio > 43",167,"debt_ratio","DebtRatio","S048","total_risk_flags (:177); not selected by the model"," (0 rows exactly 43)"),
    ("flag_very_high_debt_ratio","debt_ratio > 60",168,"debt_ratio","DebtRatio","S049","model variable"," (0 rows exactly 60)"),
    ("flag_recent_late_payments","num_late_30_59 > 0",169,"num_late_30_59","NumberOfTime30-59DaysPastDueNotWorse","S050","model variable",""),
    ("flag_serious_delinquency","num_late_90_plus > 0",170,"num_late_90_plus","NumberOfTimes90DaysLate","S051","total_risk_flags (:177); bitwise equal to has_serious_delinquency, so stepwise skips it as aliased (batch1 row 15)",""),
    ("flag_multiple_delinquencies","total_late_payments >= 3",171,"total_late_payments","NumberOfTime30-59DaysPastDueNotWorse, NumberOfTime60-89DaysPastDueNotWorse, NumberOfTimes90DaysLate (summed at :130)","S052","model variable and total_risk_flags (:177)"," (2,884 rows exactly 3 -> 1)"),
    ("flag_many_dependents","num_dependents >= 3",173,"num_dependents","NumberOfDependents after :89-90 resets missing to 0","S054","not selected by the model"," (9,483 rows exactly 3 -> 1)"),
    ("flag_few_credit_lines","num_credit_lines <= 2",174,"num_credit_lines","NumberOfOpenCreditLinesAndLoans","S055","model variable"," (a missing value would give 1 in SAS since . <= 2 is true; unreachable)"),
]
for sym,cond,ln,col,raw,site,esc,note in FL:
    op = cond.split()[1]; c=cond.split()[2]
    if col=="num_dependents":
        proof = "num_dependents: raw NumberOfDependents is missing only for 3,924 'NA' values, which :89-90 resets to 0; every other value is numeric (0 non-numeric in data/cs-training.csv and its byte-identical edge_predict copy), so never missing"
    elif col=="total_late_payments":
        proof = "total_late_payments = sum() (:130) of three counts, each "+FE_IN.format(cols=raw.split(' (')[0])
    else:
        proof = FE_IN.format(cols=raw)
    ROWS.append([F,sym,f"flag = ({cond})","MISSING_NEVER",
     f"{sym} = sas_compat.flag(pl.col('{col}') {op} {c}): plain comparison ({col} never missing); Int64 0/1",
     f"feature_engineering.sas:{ln}; {proof}{note}; escapes as model_features column; {esc}; "+FE_VER.format(what=sym)+f"; sites {site}"])
# financial health
ROWS.append([F,"financial_health","five independent if-then deductions from 100 (cu > 30, cu > 75, debt_ratio > 43, truthy has_delinquency, num_late_90_plus > 0)","MISSING_NEVER",
 "financial_health = 100 - pl.when(pl.col('credit_utilization') > 30).then(15).otherwise(0) - pl.when(pl.col('credit_utilization') > 75).then(15).otherwise(0) - pl.when(pl.col('debt_ratio') > 43).then(20).otherwise(0) - pl.when(pl.col('has_delinquency') != 0).then(20).otherwise(0) - pl.when(pl.col('num_late_90_plus') > 0).then(30).otherwise(0), then max(0, .) per S067 (arith shard). The five ifs are NOT an else-if chain: every true condition deducts (cu > 75 deducts 30 in total). SAS truthiness `if has_delinquency` = not missing and not 0 -> `!= 0`, plain because has_delinquency is a non-null 0/1 flag. has_delinquency must exist in an earlier with_columns. All operands never missing, so plain comparisons",
 "feature_engineering.sas:181-188; credit_utilization (:113), debt_ratio (:114), num_late_90_plus (:112): "+FE_IN.format(cols="RevolvingUtilizationOfUnsecuredLines, DebtRatio, NumberOfTimes90DaysLate")+"; has_delinquency = flag(...) from :133, never missing (row has_delinquency); the deductions sum to at most 100, so the value is never below 0 before max(0, .); escapes as model_features column and train model variable; "+FE_VER.format(what="financial_health")+"; also total_risk_flags (:177-179) recomputed, 0 mismatches; sites S058,S060,S062,S064,S066"])
append(ROWS)
print(len(ROWS))
