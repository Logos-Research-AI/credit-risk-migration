"""Independent recomputation of FE and predict features from raw CSVs (reviewer fe-predict-A)."""
import polars as pl
R = "/Users/cristophersalvi/GitHub/sas-migration/"
REF = R + "judge/reference/"


def lt_sas(x, c):  # SAS: missing smaller than every number
    return pl.when(x.is_null()).then(True).otherwise(x < c)


def load(path, trunc_income):
    df = pl.read_csv(path, infer_schema=False)
    df = df.rename({"": "VAR1"}) if "" in df.columns else df
    inc = pl.col("MonthlyIncome")
    if trunc_income:
        inc = inc.str.slice(0, 5)
    num = lambda c: pl.col(c).cast(pl.Float64, strict=False)
    df = df.with_columns(
        MonthlyIncome=inc.cast(pl.Float64, strict=False),
        NumberOfDependents=num("NumberOfDependents"),
        **{c: num(c) for c in df.columns if c not in ("MonthlyIncome", "NumberOfDependents", "SeriousDlqin2yrs")},
    )
    if "SeriousDlqin2yrs" in df.columns and not trunc_income:
        pass
    else:
        df = df.with_columns(SeriousDlqin2yrs=num("SeriousDlqin2yrs"))
    return df


def agegrp(c):
    return pl.when(c < 30).then(1).when(c < 40).then(2).when(c < 50).then(3).when(c < 60).then(4).otherwise(5)


def features(df, train):
    med = (df.filter(pl.col("MonthlyIncome").is_not_null())
           .with_columns(age_group=agegrp(pl.col("age")))
           .group_by("age_group", maintain_order=True).agg(median_income=pl.col("MonthlyIncome").median()))
    print("medians", sorted(med.rows()))
    cl = df.with_columns(age_group=agegrp(pl.col("age")),
                         MonthlyIncome_missing=pl.col("MonthlyIncome").is_null().cast(pl.Int64),
                         Dependents_missing=pl.col("NumberOfDependents").is_null().cast(pl.Int64),
                         NumberOfDependents=pl.col("NumberOfDependents").fill_null(0.0))
    j = cl.join(med, on="age_group", how="left", maintain_order="left")
    sel = [pl.col("VAR1").alias("row_id")]
    if train:
        sel.append(pl.col("SeriousDlqin2yrs").alias("default_flag"))
    sel += [pl.col("age"),
            pl.when(pl.col("MonthlyIncome_missing") == 1).then(pl.col("median_income")).otherwise(pl.col("MonthlyIncome")).alias("monthly_income"),
            pl.col("MonthlyIncome_missing"), pl.col("NumberOfDependents").alias("num_dependents"), pl.col("Dependents_missing"),
            pl.col("age_group"),
            pl.col("NumberOfTime30-59DaysPastDueNotWorse").alias("num_late_30_59"),
            pl.col("NumberOfTime60-89DaysPastDueNotWorse").alias("num_late_60_89"),
            pl.col("NumberOfTimes90DaysLate").alias("num_late_90_plus"),
            (pl.col("RevolvingUtilizationOfUnsecuredLines") * 100).alias("credit_utilization"),
            (pl.col("DebtRatio") * 100).alias("debt_ratio"),
            pl.col("NumberOfOpenCreditLinesAndLoans").alias("num_credit_lines"),
            pl.col("NumberRealEstateLoansOrLines").alias("num_real_estate_loans")]
    f = j.select(sel)
    c = pl.col
    f = f.with_columns(total_late_payments=pl.sum_horizontal("num_late_30_59", "num_late_60_89", "num_late_90_plus"))
    f = f.with_columns(has_delinquency=(c("total_late_payments") > 0).cast(pl.Int64),
                       has_serious_delinquency=(c("num_late_90_plus") > 0).cast(pl.Int64),
                       credit_util_category=pl.when(c("credit_utilization") < 30).then(1).when(c("credit_utilization") < 50).then(2).when(c("credit_utilization") < 75).then(3).otherwise(4),
                       debt_category=pl.when(c("debt_ratio") < 30).then(1).when(c("debt_ratio") < 43).then(2).when(c("debt_ratio") < 60).then(3).otherwise(4),
                       income_per_dependent=pl.when(c("num_dependents") > 0).then(c("monthly_income") / (c("num_dependents") + 1)).otherwise(c("monthly_income")),
                       credit_lines_per_person=c("num_credit_lines") / (c("num_dependents") + 1),
                       age_category=pl.when(c("age") < 25).then(1).when(c("age") < 35).then(2).when(c("age") < 50).then(3).when(c("age") < 65).then(4).otherwise(5),
                       flag_high_utilization=(c("credit_utilization") > 75).cast(pl.Int64),
                       flag_very_high_utilization=(c("credit_utilization") > 100).cast(pl.Int64),
                       flag_high_debt_ratio=(c("debt_ratio") > 43).cast(pl.Int64),
                       flag_very_high_debt_ratio=(c("debt_ratio") > 60).cast(pl.Int64),
                       flag_recent_late_payments=(c("num_late_30_59") > 0).cast(pl.Int64),
                       flag_serious_delinquency=(c("num_late_90_plus") > 0).cast(pl.Int64),
                       flag_multiple_delinquencies=(c("total_late_payments") >= 3).cast(pl.Int64),
                       flag_low_income=lt_sas(c("monthly_income"), 2500).cast(pl.Int64),
                       flag_many_dependents=(c("num_dependents") >= 3).cast(pl.Int64),
                       flag_few_credit_lines=(c("num_credit_lines") <= 2).cast(pl.Int64))
    f = f.with_columns(total_risk_flags=pl.sum_horizontal("flag_high_utilization", "flag_high_debt_ratio", "flag_serious_delinquency", "flag_multiple_delinquencies", "flag_low_income"))
    fh = (100 - pl.when(c("credit_utilization") > 30).then(15).otherwise(0) - pl.when(c("credit_utilization") > 75).then(15).otherwise(0)
          - pl.when(c("debt_ratio") > 43).then(20).otherwise(0) - pl.when(c("has_delinquency") != 0).then(20).otherwise(0)
          - pl.when(c("num_late_90_plus") > 0).then(30).otherwise(0))
    f = f.with_columns(fh_pre=fh)
    f = f.with_columns(financial_health=pl.max_horizontal(pl.lit(0), c("fh_pre")))
    def slog(x):
        return pl.when(x > 0).then(x.log()).otherwise(None)
    f = f.with_columns(log_monthly_income=slog(c("monthly_income") + 1), log_num_credit_lines=slog(c("num_credit_lines") + 1),
                       log_total_late_payments=slog(c("total_late_payments") + 1))
    f = f.with_columns(age_income_interaction=c("age") * c("log_monthly_income"),
                       utilization_debt_interaction=c("credit_utilization") * c("debt_ratio") / 100,
                       credit_utilization_capped=pl.min_horizontal("credit_utilization", pl.lit(200.0)),
                       debt_ratio_capped=pl.min_horizontal("debt_ratio", pl.lit(500.0)))
    return f


import sys
sys.path.insert(0, R + "judge")
from compare import sas_best12


def compare(mine, ref, cols, label):
    m = ref.join(mine, on="row_id", how="left", suffix="_m")
    assert m.height == ref.height
    for col in cols:
        rt = m[col].to_list()
        xs = m[col + "_m"].to_list()
        bad = 0; ex = []
        for r, x in zip(rt, xs):
            if r is None or r == "":
                ok = x is None
            elif x is None:
                ok = False
            elif "E" in r:
                ok = abs(float(r) - x) <= 1e-6 * abs(float(r))
            else:
                ok = sas_best12(float(x)) == r
            if not ok:
                bad += 1
                if len(ex) < 3: ex.append((r, x))
        print(f"  {label} {col}: best12-mismatches={bad} ref_empty={sum(1 for r in rt if r in (None, ''))} mine_null={sum(1 for x in xs if x is None)} ex={ex}")


fe_raw = load(R + "data/cs-training.csv", True)
fe = features(fe_raw, True)
print("FE fh_pre min", fe["fh_pre"].min(), "count0", (fe["fh_pre"] == 0).sum())
ref = pl.concat([pl.read_csv(REF + "model_features_train.csv", infer_schema=False), pl.read_csv(REF + "model_features_validation.csv", infer_schema=False)])
ref = ref.with_columns(pl.col("row_id").cast(pl.Float64))
cols = [c for c in ref.columns if c != "row_id"]
compare(fe, ref, cols, "FE")
print("FE header order == mine:", [c for c in fe.columns if c != "fh_pre"] == ref.columns)

for name, path, refp in [("ref", "data/cs-test.csv", REF), ("edge", "judge/scenarios/edge_predict/cs-test.csv", REF + "scenarios/edge_predict/")]:
    raw = load(R + path, False)
    p = features(raw, False)
    print(name, "fh_pre min", p["fh_pre"].min(), "nulls per col:", {k: v for k, v in zip(p.columns, p.null_count().row(0)) if v})
    tp = pl.read_csv(refp + "test_predictions.csv", infer_schema=False).with_columns(pl.col("row_id").cast(pl.Float64))
    compare(p, tp, ["age", "monthly_income", "credit_utilization", "debt_ratio", "num_credit_lines", "total_late_payments", "total_risk_flags", "financial_health"], name)
    print(name, "count cu==100", (p["credit_utilization"] == 100).sum(), "dr==60", (p["debt_ratio"] == 60).sum(), "dr==43", (p["debt_ratio"] == 43).sum(),
          "cu==75", (p["credit_utilization"] == 75).sum(), "cu==30", (p["credit_utilization"] == 30).sum())
    p.write_parquet(f"/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/review/fe-predict-A/pred_{name}.parquet")
fe.write_parquet("/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/review/fe-predict-A/fe.parquet")
print("FE boundaries: cu==100", (fe["credit_utilization"] == 100).sum(), "dr==30", (fe["debt_ratio"] == 30).sum(), "age==25/35/50/65",
      [(fe["age"] == a).sum() for a in (25, 35, 50, 65)], "tlp==3", (fe["total_late_payments"] == 3).sum(), "nd==3", (fe["num_dependents"] == 3).sum(),
      "tlp==0", (fe["total_late_payments"] == 0).sum(), "age==0", (fe["age"] == 0).sum())
