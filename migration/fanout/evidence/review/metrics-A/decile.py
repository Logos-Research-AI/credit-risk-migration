import sys, numpy as np, polars as pl
sys.path.insert(0, "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/review/metrics-A")
from pathlib import Path
exec(open(sys.path[0] + "/verify.py").read().split("bad = 0")[0])
bad = 0
for name, (inp, rdir) in SETS.items():
    v = read(inp / "risk_scores_validation.csv")
    dd = v.with_columns(decile=pl.Series(rank_groups(v["pd_logistic"].to_numpy(), 10, True)))
    tot = dd["default_flag"].sum(); mrate = dd["default_flag"].mean()
    da = (dd.group_by("decile", maintain_order=True)
          .agg(total_count=pl.len(), defaults=pl.col("default_flag").sum(), default_rate=pl.col("default_flag").mean(),
               avg_pd=pl.col("pd_logistic").mean(), min_pd=pl.col("pd_logistic").min(), max_pd=pl.col("pd_logistic").max())
          .sort("decile").with_columns(decile=pl.col("decile") + 1)
          .with_columns(capture_rate=pl.col("defaults") / tot, lift=pl.col("default_rate") / mrate))
    ieee_cap = np.divide(da["defaults"].to_numpy(), tot); ieee_lift = np.divide(da["default_rate"].to_numpy(), mrate)
    ieee_rate = np.divide(da["defaults"].to_numpy(), da["total_count"].to_numpy().astype(float))
    print(name, "ulp diffs cap", int((da["capture_rate"].to_numpy() != ieee_cap).sum()), "lift", int((da["lift"].to_numpy() != ieee_lift).sum()),
          "default_rate in-agg mean vs IEEE", int((da["default_rate"].to_numpy() != ieee_rate).sum()))
    r = pl.read_csv(rdir / "decile_analysis.csv", infer_schema=False)
    for row, rr in zip(da.iter_rows(named=True), r.iter_rows(named=True)):
        got = [str(row["decile"]), str(row["total_count"]), best(float(row["defaults"])), pct82(row["default_rate"]), fixed(row["avg_pd"], 4),
               fixed(row["min_pd"], 4), fixed(row["max_pd"], 4), pct82(row["capture_rate"]), fixed(row["lift"], 2)]
        if got != list(rr.values()):
            bad += 1; print("  MISMATCH", got, list(rr.values()))
print("bad", bad)
