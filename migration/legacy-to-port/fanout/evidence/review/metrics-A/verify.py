"""metrics-A independent recomputation of metrics_calculation.sas rows on all 4 input sets."""
import math, sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import numpy as np
import polars as pl

sys.path.insert(0, "/Users/cristophersalvi/GitHub/sas-migration/judge")
from compare import sas_best12  # plain BEST12 (no E-notation; fine for these files)

J = Path("/Users/cristophersalvi/GitHub/sas-migration/judge")
SETS = {
    "real": (J / "reference", J / "reference"),
    "a": (J / "scenarios/edge_metrics_a", J / "reference/scenarios/edge_metrics_a"),
    "b": (J / "scenarios/edge_metrics_b", J / "reference/scenarios/edge_metrics_b"),
    "c": (J / "scenarios/edge_metrics_c", J / "reference/scenarios/edge_metrics_c"),
}


def fixed(x, d):
    if x is None:
        return ""
    q = Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-d), rounding=ROUND_HALF_UP)
    s = f"{q:.{d}f}"
    return "0." + "0" * d if s == "-0." + "0" * d else s


def pct82(x):
    for d in (2, 1, 0):
        s = fixed(100 * x, d) + "%"
        if len(s) <= 6:
            return s
    return s


def best(x):
    return "" if x is None else sas_best12(x)


def d8(x):  # D8. emulation per row 3: decimals = max(4, decimals for 3 sig digits)
    e = math.floor(math.log10(abs(x)))
    dec = max(4, 2 - e)
    return fixed(x, dec)


def read(p):
    return pl.read_csv(p, infer_schema=False).select(
        pl.col("default_flag").cast(pl.Float64), pl.col("pd_logistic").cast(pl.Float64))


def rank_groups(x: np.ndarray, k: int, descending: bool):
    v = -x if descending else x
    order = np.argsort(v, kind="stable")
    sv = v[order]
    ranks = np.empty(len(v))
    i = 0
    n = len(v)
    while i < n:
        j = i
        while j + 1 < n and sv[j + 1] == sv[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return np.floor(ranks * k / (n + 1)).astype(np.int64)


def ref(path):
    return pl.read_csv(path, infer_schema=False).fill_null("")


bad = 0


def check(tag, got, exp):
    global bad
    if got != exp:
        bad += 1
        print(f"  MISMATCH {tag}: got {got!r} ref {exp!r}")


for name, (inp, rdir) in SETS.items():
    print(f"=== {name}")
    v = read(inp / "risk_scores_validation.csv")
    t = read(inp / "risk_scores_train.csv")
    for nm, df in (("valid", v), ("train", t)):
        print(f"  {nm}: rows {df.height} null default {df['default_flag'].null_count()} null pd {df['pd_logistic'].null_count()} "
              f"flag values {sorted(df['default_flag'].unique().to_list())} pd range {df['pd_logistic'].min()}..{df['pd_logistic'].max()}")
    y = v["default_flag"].to_numpy()
    p = v["pd_logistic"].to_numpy()

    # ---------------- ROC (row 3) ----------------
    ev = np.sort(p[y == 1]); ne = np.sort(p[y == 0])
    n1, n0 = len(ev), len(ne)
    below = np.searchsorted(ne, ev, side="left"); le = np.searchsorted(ne, ev, side="right")
    tie_e = le - below
    C = below.sum(); T = tie_e.sum(); P = n1 * n0; D = P - C - T
    area = (C + T / 2) / P
    v10 = (below + 0.5 * tie_e) / n0
    above = n1 - np.searchsorted(ev, ne, side="right"); tie_n = np.searchsorted(ev, ne, side="right") - np.searchsorted(ev, ne, side="left")
    v01 = (above + 0.5 * tie_n) / n1
    se = math.sqrt(np.var(v10, ddof=1) / n1 + np.var(v01, ddof=1) / n0)
    z = 1.959963985
    N = n1 + n0
    rocrow = dict(Area=area, StdErr=se, LowerArea=area - z * se, UpperArea=area + z * se,
                  SomersD=(C - D) / P, Gamma=(C - D) / (C + D), TauA=(C - D) / (N * (N - 1) / 2))
    r = ref(rdir / "printed_roc_metrics.csv").row(0, named=True)
    check("roc ROCModel", "Logistic Model", r["ROCModel"])
    for k, val in rocrow.items():
        txt = d8(val) if k == "StdErr" else fixed(val, 4)
        check(f"roc {k}", txt, r[k])
        dec = len(r[k].split(".")[1])
        dist = abs(val * 10**dec - math.floor(val * 10**dec) - 0.5)
        if dist < 0.02:
            print(f"   roc {k} near rounding boundary: {val!r} ({dist:.4f} du from .5)")
    print(f"  ROC n1={n1} n0={n0} T={T} Area={area:.8f} SE={se:.8f}")
    # Gini
    gini = 2 * area - 1
    vs = ref(rdir / "validation_summary.csv").row(0, named=True)
    check("AUC", fixed(area, 4), vs["AUC"]); check("Gini", fixed(gini, 4), vs["Gini"])

    # ---------------- threshold loop (rows 9-25) ----------------
    vt = ref(rdir / "threshold_analysis.csv")
    rows = []
    for th, suf in ((0.3, "03"), (0.4, "04"), (0.5, "05"), (0.6, "06"), (0.7, "07")):
        conf = (v.with_columns(predicted=(pl.col("pd_logistic") >= th).cast(pl.Int64))
                .group_by(["default_flag", "predicted"], maintain_order=True).agg(COUNT=pl.len())
                .sort(["default_flag", "predicted"], maintain_order=True))
        cnt = conf.select(
            TP=pl.col("COUNT").filter((pl.col("default_flag") == 1) & (pl.col("predicted") == 1)).sum(),
            TN=pl.col("COUNT").filter((pl.col("default_flag") == 0) & (pl.col("predicted") == 0)).sum(),
            FP=pl.col("COUNT").filter((pl.col("default_flag") == 0) & (pl.col("predicted") == 1)).sum(),
            FN=pl.col("COUNT").filter((pl.col("default_flag") == 1) & (pl.col("predicted") == 0)).sum())
        # polars-expression form (rows 14, 16, 18, 20, 22)
        tot = pl.col("TP") + pl.col("TN") + pl.col("FP") + pl.col("FN")
        m = (cnt.with_columns(threshold=pl.lit(th, pl.Float64),
                              accuracy=pl.when(tot > 0).then((pl.col("TP") + pl.col("TN")) / tot).otherwise(None),
                              precision=pl.when((pl.col("TP") + pl.col("FP")) > 0).then(pl.col("TP") / (pl.col("TP") + pl.col("FP"))).otherwise(None),
                              recall=pl.when((pl.col("TP") + pl.col("FN")) > 0).then(pl.col("TP") / (pl.col("TP") + pl.col("FN"))).otherwise(None),
                              specificity=pl.when((pl.col("TN") + pl.col("FP")) > 0).then(pl.col("TN") / (pl.col("TN") + pl.col("FP"))).otherwise(None))
             .with_columns(f1_score=pl.when((pl.col("precision") + pl.col("recall")).fill_null(-1) > 0)
                           .then(2 * (pl.col("precision") * pl.col("recall")) / (pl.col("precision") + pl.col("recall"))).otherwise(None))
             .select("threshold", "accuracy", "precision", "recall", "f1_score", "specificity"))
        rows.append(m)
        tp, tn, fp, fn = cnt.row(0)
        # scalar form (rows 15, 17, 19, 21, 23)
        acc = (tp + tn) / (tp + tn + fp + fn) if tp + tn + fp + fn > 0 else None
        pr = tp / (tp + fp) if tp + fp > 0 else None
        rc = tp / (tp + fn) if tp + fn > 0 else None
        f1 = 2 * (pr * rc) / (pr + rc) if pr is not None and rc is not None and pr + rc > 0 else None
        sp = tn / (tn + fp) if tn + fp > 0 else None
        rr = vt.filter(pl.col("threshold") == best(th)).row(0, named=True)
        mr = m.row(0, named=True)
        for k, sv in (("accuracy", acc), ("precision", pr), ("recall", rc), ("f1_score", f1), ("specificity", sp)):
            check(f"th{suf} {k} scalar", best(sv), rr[k]); check(f"th{suf} {k} polars", best(mr[k]), rr[k])
            if sv is not None and mr[k] is not None and sv != mr[k]:
                print(f"   th{suf} {k}: scalar {sv!r} != polars {mr[k]!r}")
        onth = int((v["pd_logistic"] == th).sum())
        if onth:
            print(f"   th {th}: {onth} rows exactly on threshold; TP+FP={tp+fp} conf rows={conf.height}")
    ta = pl.concat(rows, how="vertical")
    check("threshold header", ",".join(ta.columns), ",".join(vt.columns))

    # ---------------- decile + cumulative lift (rows 27-33) ----------------
    dec = rank_groups(p, 10, True)
    dd = v.with_columns(decile=pl.Series(dec))
    tot_def = float(dd["default_flag"].sum()); rate = tot_def / dd.height
    da = (dd.group_by("decile", maintain_order=True)
          .agg(total_count=pl.len(), defaults=pl.col("default_flag").sum(), avg_pd=pl.col("pd_logistic").mean(),
               min_pd=pl.col("pd_logistic").min(), max_pd=pl.col("pd_logistic").max())
          .sort("decile").with_columns(decile=pl.col("decile") + 1))
    best8 = float(f"{rate:.6f}")
    cl_polars = (da.with_columns(cum_defaults=pl.col("defaults").cum_sum(), cum_count=pl.col("total_count").cum_sum())
                 .with_columns(cum_capture_rate=pl.col("cum_defaults") / tot_def,
                               cum_lift=(pl.col("cum_defaults") / pl.col("cum_count")) / best8,
                               cum_lift_full=(pl.col("cum_defaults") / pl.col("cum_count")) / rate))
    cd = cl_polars["cum_defaults"].to_numpy().astype(float); cc = cl_polars["cum_count"].to_numpy().astype(float)
    ieee_cap = np.divide(cd, tot_def); ieee_lift = np.divide(np.divide(cd, cc), best8)
    ulp_cap = int((cl_polars["cum_capture_rate"].to_numpy() != ieee_cap).sum())
    ulp_lift = int((cl_polars["cum_lift"].to_numpy() != ieee_lift).sum())
    print(f"  cumlift: total_defaults={tot_def:.0f} rate={rate!r} best8={best8!r}; polars col/scalar != IEEE: cap {ulp_cap}/10 lift {ulp_lift}/10;"
          f" last cap polars={cl_polars['cum_capture_rate'][-1]!r}")
    rl = ref(rdir / "printed_cumulative_lift.csv")
    for i, row in enumerate(cl_polars.iter_rows(named=True)):
        rr = rl.filter(pl.col("decile") == str(row["decile"])).row(0, named=True)
        check(f"d{row['decile']} cum_defaults", best(float(row["cum_defaults"])), rr["cum_defaults"])
        check(f"d{row['decile']} cum_count", best(float(row["cum_count"])), rr["cum_count"])
        for src in (row["cum_capture_rate"], ieee_cap[i]):
            check(f"d{row['decile']} cum_capture_rate", pct82(src), rr["cum_capture_rate"])
        for src in (row["cum_lift"], ieee_lift[i], row["cum_lift_full"]):
            check(f"d{row['decile']} cum_lift", fixed(src, 2), rr["cum_lift"])
        x = row["cum_lift"] * 100
        dist = abs(x - math.floor(x) - 0.5)
        if dist < 0.02:
            print(f"   cum_lift d{row['decile']} near boundary {row['cum_lift']!r}")
    check("cumlift header tail", ",".join(rl.columns[-4:]), "cum_defaults,cum_count,cum_capture_rate,cum_lift")

    # ---------------- calibration (rows 35-37) ----------------
    pb = rank_groups(p, 20, False)
    cdat = v.with_columns(pred_bin=pl.Series(pb))
    g = cdat.group_by("pred_bin", maintain_order=True)
    cal1 = (g.agg(sum_pd=pl.col("pd_logistic").sum(), sum_def=pl.col("default_flag").sum(), bin_count=pl.len())
            .sort("pred_bin").with_columns(mean_predicted=pl.col("sum_pd") / pl.col("bin_count"),
                                           mean_actual=pl.col("sum_def") / pl.col("bin_count")))
    cal2 = (g.agg(mean_predicted=pl.col("pd_logistic").mean(), _d=pl.col("default_flag").sum(), bin_count=pl.len())
            .with_columns(mean_actual=pl.col("_d") / pl.col("bin_count")).sort("pred_bin", maintain_order=True))
    rc_ = ref(rdir / "calibration_plot.csv")
    check("calib nrows", rc_.height, cal1.height)
    for c1, c2 in zip(cal1.iter_rows(named=True), cal2.iter_rows(named=True)):
        rr = rc_.filter(pl.col("pred_bin") == str(c1["pred_bin"]))
        if rr.height == 0:
            check("calib bin", c1["pred_bin"], None); continue
        rr = rr.row(0, named=True)
        for c in (c1, c2):
            check(f"cal{c1['pred_bin']} mean_predicted", fixed(c["mean_predicted"], 4), rr["mean_predicted"])
            check(f"cal{c1['pred_bin']} mean_actual", fixed(c["mean_actual"], 4), rr["mean_actual"])
            check(f"cal{c1['pred_bin']} bin_count", str(c["bin_count"]), rr["bin_count"])
        for k in ("mean_predicted", "mean_actual"):
            x = c1[k] * 1e4; dist = abs(x - math.floor(x) - 0.5)
            if dist < 1e-6:
                print(f"   calib bin {c1['pred_bin']} {k} AT a 8.4 boundary: {c1[k]!r} vs in-agg {c2[k]!r}")
    print(f"  calib: first-appearance order {cdat.group_by('pred_bin', maintain_order=True).len()['pred_bin'].to_list()[:5]}")

print("TOTAL MISMATCHES", bad)
