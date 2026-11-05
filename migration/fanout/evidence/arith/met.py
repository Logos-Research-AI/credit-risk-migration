import sys, math
sys.path.insert(0, "/Users/cristophersalvi/GitHub/sas-migration/judge")
import polars as pl, numpy as np
from compare import sas_best12
J = "/Users/cristophersalvi/GitHub/sas-migration/judge"
sets = {"real": (f"{J}/scenarios/real_metrics", f"{J}/reference"),
        "a": (f"{J}/scenarios/edge_metrics_a", f"{J}/reference/scenarios/edge_metrics_a"),
        "b": (f"{J}/scenarios/edge_metrics_b", f"{J}/reference/scenarios/edge_metrics_b"),
        "c": (f"{J}/scenarios/edge_metrics_c", f"{J}/reference/scenarios/edge_metrics_c")}
def b12(v): return "" if v is None else sas_best12(v)
def f(v, d): return "" if v is None else f"{v:.{d}f}"
def pct82(v):  # percent8.2 approx: value*100 with 2 decimals then %; width 8 may drop decimals for 100%
    s = f"{v*100:.2f}%"
    return s if len(s) <= 8 else f"{v*100:.1f}%"
def best8(x):
    # BEST8: fit in 8 chars
    if x == 0: return "0"
    ilen = len(str(int(abs(x))))
    s = f"{x:.{max(0, 8-1-ilen)}f}"
    if "." in s: s = s.rstrip("0").rstrip(".")
    if float(s) == 0 or len(s) > 8:
        s = f"{x:.2E}"
    return s
def metrics(tp, tn, fp, fn):
    acc = (tp+tn)/(tp+tn+fp+fn) if (tp+tn+fp+fn) > 0 else None
    pr = tp/(tp+fp) if (tp+fp) > 0 else None
    rc = tp/(tp+fn) if (tp+fn) > 0 else None
    f1 = 2*(pr*rc)/(pr+rc) if (pr is not None and rc is not None and pr+rc > 0) else None
    sp = tn/(tn+fp) if (tn+fp) > 0 else None
    return acc, pr, rc, f1, sp
def proc_rank_groups(pd_, k, desc):
    x = -pd_ if desc else pd_
    r = x.rank("average")
    n = len(x)
    return (r * k / (n + 1)).floor().cast(pl.Int64)
for name, (inp, ref) in sets.items():
    v = pl.read_csv(f"{inp}/risk_scores_validation.csv", infer_schema=False).select(y=pl.col("default_flag").cast(pl.Float64), p=pl.col("pd_logistic").cast(pl.Float64))
    ta = pl.read_csv(f"{ref}/threshold_analysis.csv", infer_schema=False).fill_null("")
    bad = 0
    for t, row in zip([0.3,0.4,0.5,0.6,0.7], ta.iter_rows(named=True)):
        pred = v["p"] >= t; y = v["y"]
        tp = int(((y==1)&pred).sum()); tn=int(((y==0)&~pred).sum()); fp=int(((y==0)&pred).sum()); fn=int(((y==1)&~pred).sum())
        m = metrics(tp,tn,fp,fn)
        mine = [b12(x) for x in m]; refs = [row[c] for c in ["accuracy","precision","recall","f1_score","specificity"]]
        if mine != refs: bad += 1; print("  MISMATCH", name, t, mine, refs)
    print(name, "threshold_analysis rows mismatching:", bad)
    # cumulative lift
    cl = pl.read_csv(f"{ref}/printed_cumulative_lift.csv", infer_schema=False)
    tot = float(v["y"].sum()); rate = v["y"].mean(); rate8 = float(best8(rate))
    cd = np.cumsum(cl["defaults"].cast(pl.Float64).to_numpy()); cc = np.cumsum(cl["total_count"].cast(pl.Float64).to_numpy())
    bc = bl = bl8 = 0; marg = []
    for i in range(len(cd)):
        cap = cd[i]/tot; lift = (cd[i]/cc[i])/rate; lift8 = (cd[i]/cc[i])/rate8
        if pct82(cap) != cl["cum_capture_rate"][i]: bc += 1; print("   cap", pct82(cap), cl["cum_capture_rate"][i])
        if f(lift,2) != cl["cum_lift"][i]: bl += 1
        if f(lift8,2) != cl["cum_lift"][i]: bl8 += 1
        marg.append(abs(lift*100 - math.floor(lift*100) - 0.5))
    print(f"  cum: total_defaults {tot} rate {rate!r} best8 {best8(rate)}; cap mismatches {bc}, lift(full) mismatches {bl}, lift(best8) mismatches {bl8}, min distance of lift*100 to .5 boundary {min(marg):.2e}")
    # calibration
    cal = pl.read_csv(f"{ref}/calibration_plot.csv", infer_schema=False)
    d = v.with_columns(pred_bin=proc_rank_groups(v["p"], 20, False))
    g1 = d.group_by("pred_bin", maintain_order=True).agg(mp=pl.col("p").mean(), ma=pl.col("y").mean(), n=pl.len()).sort("pred_bin")
    g2 = d.group_by("pred_bin", maintain_order=True).agg(sp=pl.col("p").sum(), sy=pl.col("y").sum(), n=pl.len()).sort("pred_bin")
    mism = 0
    for r, a, b in zip(cal.iter_rows(named=True), g1.iter_rows(named=True), g2.iter_rows(named=True)):
        mine = [str(a["pred_bin"]), f(a["mp"],4), f(a["ma"],4), str(a["n"])]
        mine2 = [str(b["pred_bin"]), f(b["sp"]/b["n"],4), f(b["sy"]/b["n"],4), str(b["n"])]
        refr = [r["pred_bin"], r["mean_predicted"], r["mean_actual"], r["bin_count"]]
        if mine != refr or mine2 != refr: mism += 1; print("   cal", mine, mine2, refr)
    print(f"  calibration rows {cal.height}, mismatching {mism}")
    # gini
    mp = pl.read_csv(f"{ref}/model_performance_metrics.csv", infer_schema=False)
    print("  AUC/Gini ref", mp["AUC"][0], mp["Gini"][0])
