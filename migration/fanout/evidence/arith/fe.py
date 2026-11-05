import sys, math
sys.path.insert(0, "/Users/cristophersalvi/GitHub/sas-migration/judge")
import polars as pl
from compare import sas_best12
R = "/Users/cristophersalvi/GitHub/sas-migration"

def num(c): return pl.col(c).cast(pl.Float64, strict=False)

def sas_sum(*cols):
    e = [pl.col(c) if isinstance(c,str) else c for c in cols]
    return pl.when(pl.all_horizontal([x.is_null() for x in e])).then(None).otherwise(pl.sum_horizontal(e))
def sas_log(x): return pl.when(x > 0).then(x.log()).otherwise(None)
def flag(b): return b.cast(pl.Int64)
def lt(x, c): return pl.when(x.is_null()).then(True).otherwise(x < c)
def gt(x, c): return pl.when(x.is_null()).then(False).otherwise(x > c)
def ge(x, c): return pl.when(x.is_null()).then(False).otherwise(x >= c)

def build(path, width):
    raw = pl.read_csv(path, infer_schema=False)
    inc = pl.col("MonthlyIncome")
    if width: inc = inc.str.slice(0, width)
    df = raw.select(
        pl.col("").cast(pl.Int64).alias("row_id"),
        num("age").alias("age"),
        inc.cast(pl.Float64, strict=False).alias("MonthlyIncome"),
        num("NumberOfDependents").alias("NumberOfDependents"),
        num("NumberOfTime30-59DaysPastDueNotWorse").alias("num_late_30_59"),
        num("NumberOfTime60-89DaysPastDueNotWorse").alias("num_late_60_89"),
        num("NumberOfTimes90DaysLate").alias("num_late_90_plus"),
        (num("RevolvingUtilizationOfUnsecuredLines")*100).alias("credit_utilization"),
        (num("DebtRatio")*100).alias("debt_ratio"),
        num("NumberOfOpenCreditLinesAndLoans").alias("num_credit_lines"),
    )
    ag = pl.when(pl.col("age")<30).then(1).when(pl.col("age")<40).then(2).when(pl.col("age")<50).then(3).when(pl.col("age")<60).then(4).otherwise(5)
    df = df.with_columns(age_group=ag)
    med = df.filter(pl.col("MonthlyIncome").is_not_null()).group_by("age_group", maintain_order=True).agg(median_income=pl.col("MonthlyIncome").median())
    df = df.join(med, on="age_group", how="left", maintain_order="left")
    df = df.with_columns(
        monthly_income=pl.when(pl.col("MonthlyIncome").is_null()).then(pl.col("median_income")).otherwise(pl.col("MonthlyIncome")),
        num_dependents=pl.col("NumberOfDependents").fill_null(0.0))
    df = df.with_columns(total_late_payments=sas_sum("num_late_30_59","num_late_60_89","num_late_90_plus"))
    df = df.with_columns(has_delinquency=flag(pl.col("total_late_payments")>0))
    mi = pl.col("monthly_income"); nd = pl.col("num_dependents")
    df = df.with_columns(
        income_per_dependent=pl.when(nd>0).then(mi/(nd+1)).otherwise(mi),
        credit_lines_per_person=pl.col("num_credit_lines")/(nd+1),
        flag_high_utilization=flag(pl.col("credit_utilization")>75),
        flag_high_debt_ratio=flag(pl.col("debt_ratio")>43),
        flag_serious_delinquency=flag(pl.col("num_late_90_plus")>0),
        flag_multiple_delinquencies=flag(pl.col("total_late_payments")>=3),
        flag_low_income=flag(lt(mi,2500)),
    )
    df = df.with_columns(total_risk_flags=sas_sum("flag_high_utilization","flag_high_debt_ratio","flag_serious_delinquency","flag_multiple_delinquencies","flag_low_income"))
    fh = pl.lit(100.0)
    fh = pl.when(pl.col("credit_utilization")>30).then(fh-15).otherwise(fh)
    fh = pl.when(pl.col("credit_utilization")>75).then(fh-15).otherwise(fh)
    fh = pl.when(pl.col("debt_ratio")>43).then(fh-20).otherwise(fh)
    fh = pl.when(pl.col("has_delinquency")!=0).then(fh-20).otherwise(fh)
    fh = pl.when(pl.col("num_late_90_plus")>0).then(fh-30).otherwise(fh)
    df = df.with_columns(fh_pre=fh)
    df = df.with_columns(financial_health=pl.max_horizontal(pl.lit(0.0), pl.col("fh_pre")))
    df = df.with_columns(log_monthly_income=sas_log(mi+1), log_num_credit_lines=sas_log(pl.col("num_credit_lines")+1), log_total_late_payments=sas_log(pl.col("total_late_payments")+1))
    df = df.with_columns(age_income_interaction=pl.col("age")*pl.col("log_monthly_income"),
        utilization_debt_interaction=pl.col("credit_utilization")*pl.col("debt_ratio")/100,
        udi_alt=pl.col("credit_utilization")*(pl.col("debt_ratio")/100),
        credit_utilization_capped=pl.min_horizontal(pl.col("credit_utilization"), pl.lit(200.0)),
        debt_ratio_capped=pl.min_horizontal(pl.col("debt_ratio"), pl.lit(500.0)))
    return df

def cmp(mine, ref, cols, key="row_id", alt=None):
    ref = pl.read_csv(ref, infer_schema=False).with_columns(pl.col(key).cast(pl.Int64))
    j = ref.join(mine, on=key, how="left", suffix="_py")
    print("rows", ref.height, "unmatched", j.filter(pl.col("age_py").is_null()).height if "age_py" in j.columns else "?")
    for c in cols:
        src = alt.get(c, c) if alt else c
        pc = src + "_py" if src in ref.columns else src
        vals = j[pc].to_list(); refs = j[c].to_list()
        bad = 0; ex=None
        for v, r in zip(vals, refs):
            s = "" if v is None else sas_best12(float(v))
            r = r or ""
            if s != r:
                bad += 1
                if ex is None: ex=(s, r)
        print(f"  {c}: mismatches {bad} ex {ex}")

if __name__ == "__main__":
    fe = build(f"{R}/data/cs-training.csv", 5)
    print("fe: fh_pre min", fe["fh_pre"].min(), "nulls", {c: fe[c].null_count() for c in ["total_late_payments","total_risk_flags","financial_health","log_monthly_income","log_num_credit_lines","log_total_late_payments","credit_lines_per_person","income_per_dependent"]})
    print("fe: min divisor nd+1", (fe["num_dependents"]+1).min(), "min income", fe["monthly_income"].min(), "count fh_pre==0", (fe["fh_pre"]==0).sum())
    cols = ["total_late_payments","income_per_dependent","credit_lines_per_person","total_risk_flags","financial_health","log_monthly_income","log_num_credit_lines","log_total_late_payments","age_income_interaction","utilization_debt_interaction","credit_utilization_capped","debt_ratio_capped","credit_utilization","debt_ratio","monthly_income"]
    for part in ["train","validation"]:
        print(part); cmp(fe, f"{R}/judge/reference/model_features_{part}.csv", cols)
    print("alt udi (cu*(dr/100))"); cmp(fe, f"{R}/judge/reference/model_features_validation.csv", ["utilization_debt_interaction"], alt={"utilization_debt_interaction":"udi_alt"})
