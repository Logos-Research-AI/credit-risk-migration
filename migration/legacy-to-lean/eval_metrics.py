"""Differential evaluation of every unit of metrics_calculation.sas on a staged input, against
the full-precision dump of the same input run through the original SAS script
(migration/run_stage.py). Usage: python3 migration/eval_metrics.py <inputs-dir> <run-id>"""
import csv, sys, math
sys.path.insert(0, "migration")
from diffeval import *

STR = {"risk_grade", "recommendation", "interest_rate"}
SINK, DECL = "def:model_performance_metrics", "model_performance_metrics.evalApply"
NAMES = ["roc_stats", "auc_summary", "logit_scored_valid", "ks_calculation", "ks_statistic", "threshold_analysis",
         "decile_data", "decile_analysis", "cumulative_lift", "train_bins", "valid_bins", "psi_calculation",
         "psi_summary", "calibration_data", "calibration_plot", "validation_summary", "model_performance_metrics"]
# columns whose value passes through the PROC SQL SUM/MEAN parameter (R17) or BEST8. (R19)
AGGCOLS = {"decile_analysis": {"defaults", "default_rate", "avg_pd", "capture_rate", "lift"},
           "cumulative_lift": {"defaults", "default_rate", "avg_pd", "capture_rate", "lift", "cum_defaults", "cum_capture_rate", "cum_lift"},
           "psi_summary": {"PSI"}, "calibration_plot": {"mean_predicted", "mean_actual"},
           "validation_summary": {"PSI"}, "model_performance_metrics": {"PSI"}}
NARROW = {"row_id", "default_flag", "pd_logistic", "risk_grade"}
SKIP = {"interest_rate", "validation_date", "StdErr", "LowerArea", "UpperArea", "SomersD", "Gamma", "TauA"}

def table(path, narrow=NARROW):
    rows = []
    for r in csv.DictReader(open(path)):
        rows.append(lean_row([(k, "s" if k in STR else "n", v) for k, v in r.items() if narrow is None or k in narrow]))
    return lean_table(rows)

def expr(name, valid, train, best8_rate):
    b8 = f"(fun (x : Float) => if x < 1 then {best8_rate} else x)"
    d = {}
    d["rs"] = "(roc_stats V0)"; d["au"] = f"(auc_summary {d['rs']})"; d["V"] = "(logit_scored_valid_sorted V0)"
    d["kc"] = f"(ks_calculation (total_good_bad {d['V']}) {d['V']})"; d["ks"] = f"(ks_statistic {d['kc']})"
    d["ta"] = f"(threshold_analysis {d['V']})"; d["dd"] = f"(decile_data {d['V']})"
    d["da"] = f"(decile_analysis {AGG} {d['dd']})"
    d["cl"] = f"(cumulative_lift (total_defaults {AGG} {b8} {d['dd']}) {d['da']})"
    d["tb"] = "(train_bins T0)"; d["vb"] = f"(valid_bins {d['V']})"; d["pc"] = f"(psi_calculation {d['tb']} {d['vb']})"
    d["ps"] = f"(psi_summary {AGG} {d['pc']})"; d["cd"] = f"(calibration_data {d['V']})"
    d["cp"] = f"(calibration_plot {AGG} {d['cd']})"; d["vs"] = f"(validation_summary {d['au']} {d['ks']} {d['ps']})"
    d["mp"] = f"(model_performance_metrics (none : Option Float) {d['au']} {d['ks']} {d['ps']} {d['ta']})"
    key = dict(zip(NAMES, ["rs", "au", "V", "kc", "ks", "ta", "dd", "da", "cl", "tb", "vb", "pc", "ps", "cd", "cp", "vs", "mp"]))[name]
    body = d[key]
    if "T0" in body and "V0" not in body:
        return f"(fun (T0 : Tabular.Table Float) => {ROWVIEW} {body}) {train}"
    if "T0" in body:
        return f"(fun (V0 T0 : Tabular.Table Float) => {ROWVIEW} {body}) {valid} {train}"
    return f"(fun (V0 : Tabular.Table Float) => {ROWVIEW} {body}) {valid}"

def compare(name, lean, sas, out):
    stats = out.setdefault(name, dict(rows=len(sas), cells=0, exact=0, agg_cells=0, agg_exact=0, agg_close=0, diffs=[]))
    if len(lean) != len(sas): stats["diffs"].append(("ROWCOUNT", len(lean), len(sas))); return
    for i, (lr, sr) in enumerate(zip(lean, sas)):
        ln = [k for k, _ in lr]; sn = [k for k, _ in sr if k not in SKIP or k in ln]
        if [k for k in ln] != [k for k in sn if k in ln] or (not NARROW and (set(sn) - set(ln) - SKIP)):
            stats["diffs"].append(("COLUMNS", ln, sn)); return
        sd = dict(sr)
        for k, v in lr:
            if k in SKIP: continue
            s = sd[k]
            if isinstance(v, str) or isinstance(s, str) and v is None and False:
                stats["cells"] += 1
                if (s or "") == v: stats["exact"] += 1
                else: stats["diffs"].append((i, k, v, s))
                continue
            if isinstance(s, str): s = None if s in (".", "") else float(s)
            if k in AGGCOLS.get(name, ()):
                stats["agg_cells"] += 1
                if v == s: stats["agg_exact"] += 1
                if (v is None) == (s is None) and (v is None or abs(v - s) <= 1e-9 * max(1.0, abs(s))): stats["agg_close"] += 1
                else: stats["diffs"].append((i, k, v, s))
            else:
                stats["cells"] += 1
                if v == s: stats["exact"] += 1
                else: stats["diffs"].append((i, k, v, s))

def main():
    indir, run = sys.argv[1], sys.argv[2]
    dump = read_dump(f"migration/runs/{run}/dump.txt")
    rate = None
    for l in open(f"migration/runs/{run}/dump.txt"):
        if l.startswith("DUMPM"): rate = re.search(r"overall_default_rate=\[\s*([^\]]+)\]", l).group(1)
    mcp = Mcp(); res = {}; ms = 0
    V = table(f"{indir}/risk_scores_validation.csv"); T = table(f"{indir}/risk_scores_train.csv", {"pd_logistic"})
    for name in NAMES:
        try:
            outs, t = run_(mcp, expr(name, V, T, rate)); ms += t or 0
            compare(name, parse_rowview(outs[0]), dump[name], res)
        except Exception as e:
            res[name] = dict(rows=len(dump[name]), cells=0, exact=0, agg_cells=0, agg_exact=0, agg_close=0, diffs=[("NOT EVALUATED", str(e)[:150])])
    tot = 0; totd = 0
    for name in NAMES:
        s = res[name]; tot += s["cells"] + s["agg_cells"]; totd += len(s["diffs"])
        print(f"{name:28s} rows={s['rows']:4d} exact={s['exact']}/{s['cells']}  agg-param: bit-equal {s['agg_exact']}/{s['agg_cells']}, within 1e-9 {s['agg_close']}/{s['agg_cells']}  differences={len(s['diffs'])}")
        for d in s["diffs"][:6]: print("      ", str(d)[:300])
    print("TOTAL cells", tot, "differences", totd, "elapsed_ms", ms)

def run_(mcp, e): return run(mcp, SINK, [e], DECL)

if __name__ == "__main__":
    main()
