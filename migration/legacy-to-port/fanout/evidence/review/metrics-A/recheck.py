import sys, numpy as np, polars as pl
D = "/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/review/metrics-A"
from pathlib import Path
exec(open(D + "/verify.py").read().split("bad = 0")[0])
def div(a, b):
    b = b if isinstance(b, pl.Expr) else pl.lit(float(b))
    return pl.struct(a.cast(pl.Float64).alias("a"), b.cast(pl.Float64).alias("b")).map_batches(
        lambda s: pl.Series(np.divide(s.struct.field("a").to_numpy(), s.struct.field("b").to_numpy())), return_dtype=pl.Float64)
bad = 0
for name, (inp, rdir) in SETS.items():
    v = read(inp / "risk_scores_validation.csv")
    # cumulative lift per revised rows 10-12
    dd = v.with_columns(decile=pl.Series(rank_groups(v["pd_logistic"].to_numpy(), 10, True)))
    s = dd["default_flag"].sum(); tot = float(f"{s:.0f}"); rate = float(f"{s / dd.height:.6f}")
    da = (dd.group_by("decile", maintain_order=True).agg(total_count=pl.len(), defaults=pl.col("default_flag").sum())
          .sort("decile").with_columns(decile=pl.col("decile") + 1))
    cl = (da.sort("decile", maintain_order=True).with_columns(cum_defaults=pl.col("defaults").cum_sum(), cum_count=pl.col("total_count").cum_sum())
          .with_columns(cum_capture_rate=div(pl.col("cum_defaults"), tot), cum_lift=div(pl.col("cum_defaults") / pl.col("cum_count"), rate)))
    cd = cl["cum_defaults"].to_numpy().astype(float); cc = cl["cum_count"].to_numpy().astype(float)
    ieee = int((cl["cum_capture_rate"].to_numpy() != cd / tot).sum()) + int((cl["cum_lift"].to_numpy() != (cd / cc) / rate).sum())
    rl = pl.read_csv(rdir / "printed_cumulative_lift.csv", infer_schema=False)
    for row, rr in zip(cl.iter_rows(named=True), rl.iter_rows(named=True)):
        if pct82(row["cum_capture_rate"]) != rr["cum_capture_rate"] or fixed(row["cum_lift"], 2) != rr["cum_lift"]:
            bad += 1; print("MISMATCH", name, row, rr)
    # PSI per revised rows 13-14, in the layout that broke plain '/'
    fr = {}
    for st, col in (("train", "train_pct"), ("validation", "valid_pct")):
        d = read(inp / f"risk_scores_{st}.csv")
        b = d.with_columns(score_bin=pl.Series(rank_groups(d["pd_logistic"].to_numpy(), 10, False)))
        fr[st] = b.group_by("score_bin", maintain_order=True).agg(cnt=pl.len()).sort("score_bin").with_columns(div(pl.col("cnt"), b.height).alias(col)).drop("cnt")
    j = fr["train"].join(fr["validation"], on="score_bin", how="inner", maintain_order="left").sort("score_bin").with_columns(
        psi_component=(pl.col("train_pct") - pl.col("valid_pct")) * (pl.col("train_pct") / pl.col("valid_pct")).log())
    rp = pl.read_csv(rdir / "printed_psi_calculation.csv", infer_schema=False)
    for row, rr in zip(j.iter_rows(named=True), rp.iter_rows(named=True)):
        for k in ("score_bin", "train_pct", "valid_pct", "psi_component"):
            x = row[k]; ref_ = rr[k]
            ok = (str(x) == ref_) if k == "score_bin" else (abs(x - float(ref_)) <= 1e-9 * max(1, abs(x)) and (x == 0) == (float(ref_) == 0))
            if not ok: bad += 1; print("PSI MISMATCH", name, k, x, ref_)
    print(name, "cumlift non-IEEE cells:", ieee, "| psi rows", j.height, "ref", rp.height, "| PSI", j["psi_component"].sum(),
          "| PSI 8.4", fixed(j["psi_component"].sum(), 4), pl.read_csv(rdir / "validation_summary.csv", infer_schema=False)["PSI"][0])
print("bad", bad)
