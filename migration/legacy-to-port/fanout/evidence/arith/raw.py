import polars as pl
for f in ["/Users/cristophersalvi/GitHub/sas-migration/data/cs-training.csv","/Users/cristophersalvi/GitHub/sas-migration/data/cs-test.csv","/Users/cristophersalvi/GitHub/sas-migration/judge/scenarios/edge_predict/cs-test.csv","/Users/cristophersalvi/GitHub/sas-migration/judge/scenarios/edge_predict/cs-training.csv"]:
    df = pl.read_csv(f, infer_schema=False)
    print(f, df.height)
    for c in df.columns:
        s = df[c]
        nul = s.is_null().sum(); na=(s=="NA").sum()
        num = s.cast(pl.Float64, strict=False)
        bad = (num.is_null() & s.is_not_null()).sum()
        print(f"  {c[:40]:40s} null={nul} NA={na} nonnum={bad} min={num.min()} max={num.max()} neg={(num<0).sum()}")
