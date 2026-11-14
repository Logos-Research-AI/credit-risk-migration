import polars as pl
R = "/Users/cristophersalvi/GitHub/sas-migration/judge/reference/"
for f in ["model_features_train.csv", "model_features_validation.csv", "kaggle_submission.csv", "test_predictions.csv",
          "scenarios/edge_predict/model_features_train.csv", "scenarios/edge_predict/model_features_validation.csv",
          "scenarios/edge_predict/kaggle_submission.csv", "scenarios/edge_predict/test_predictions.csv"]:
    df = pl.read_csv(R + f, infer_schema=False)
    ecells = []
    empties = {}
    for c in df.columns:
        s = df[c]
        e = df.filter(s.str.contains("E", literal=True) & ~s.str.contains("[A-DF-Za-z]"))
        if c not in ("risk_grade", "recommendation"):
            for row in (e.select("row_id", c).rows() if c != "row_id" else []):
                ecells.append((c, row))
        n = (s.is_null() | (s == "")).sum()
        if n:
            empties[c] = n
    print("==", f, df.height, "E-cells", len(ecells), ecells[:8], "empties", empties)
    if "test_predictions" in f:
        print("  interest_rate values", df["interest_rate"].value_counts().sort("interest_rate").rows())
        miss = df.filter(pl.col("pd_logistic").is_null())
        if miss.height:
            print("  on missing pd:", miss.select("risk_grade", "recommendation", "interest_rate", "pred_logistic").unique().rows(),
                  "monthly_income empty", miss["monthly_income"].is_null().sum(), "score empty", miss["credit_risk_score"].is_null().sum(),
                  "age<30", (miss["age"].cast(pl.Int64) < 30).sum(), "total_risk_flags empty", miss["total_risk_flags"].is_null().sum())
        mi = df.filter(pl.col("monthly_income").is_null())
        print("  monthly_income empty rows", mi.height, "all age<30", (mi["age"].cast(pl.Int64) < 30).all() if mi.height else None,
              "n age<30 total", (df["age"].cast(pl.Int64) < 30).sum())
        print("  row_id sorted?", df["row_id"].cast(pl.Int64).is_sorted())
