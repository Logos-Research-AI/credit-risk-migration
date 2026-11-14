import polars as pl
R = "/Users/cristophersalvi/GitHub/sas-migration/"
for f in ["data/cs-training.csv", "data/cs-test.csv", "judge/scenarios/edge_predict/cs-test.csv"]:
    df = pl.read_csv(R + f, infer_schema=False)
    print("==", f, df.height)
    for c in df.columns:
        s = df[c]
        empty = (s.is_null() | (s == "")).sum()
        na = (s == "NA").sum()
        num = s.cast(pl.Float64, strict=False)
        nonnum = (num.is_null() & s.is_not_null() & (s != "") & (s != "NA")).sum()
        ml = s.str.len_chars().max()
        print(f"  {c[:40]:40s} empty={empty} NA={na} nonnum={nonnum} min={num.min()} max={num.max()} maxlen={ml}")
