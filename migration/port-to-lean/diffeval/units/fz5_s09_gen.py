"""Fuzz of def:metrics_run_09_model_performance (+ _precond), Python side ONLY: the Lean side could not be evaluated
(eval_decl on this item and on def:merge_one_to_one returns a response that does not match the tool's schema).
Runs credit_risk/metrics_calculation.py:527-547 verbatim on seeded frames, mirrors the precondition clause by clause, and
reports Python raises inside the precondition.
  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz5_s09_gen.py [N]
"""
import sys, random, textwrap, struct, datetime as dt
from pathlib import Path
import polars as pl
from credit_risk import metrics_calculation as mc, sas_compat

L = Path(mc.__file__).read_text().splitlines()
SRC = textwrap.dedent("\n".join(L[526:547]))
assert SRC.startswith("at_50") and SRC.rstrip().endswith('"ROCModel")')
nan, inf = float("nan"), float("inf")


def ulp(x, k):
    b = struct.unpack("<q", struct.pack("<d", x))[0] + k
    return struct.unpack("<d", struct.pack("<q", b))[0]


THR = [None, nan, 0.5, 0.5, 0.5, ulp(.5, -1), ulp(.5, 1), 0.25, 0.75, 0.0, -0.0, 1.0, inf, -inf, 5e-324]
VAL = [None, nan, 0.0, -0.0, 0.5, 1.0, inf, -inf, 0.1, 5e-324, 1e300]


def col(r, n, pool):
    return pl.Series([r.choice(pool) for _ in range(n)], dtype=pl.Float64)


def gen(seed):
    r = random.Random(seed)
    h = lambda: r.choice([0, 0, 1, 1, 1, 2, 3, 5])
    nt, ns = h(), h()
    names = ["threshold", "accuracy", "precision", "recall", "f1_score", "specificity"]
    cols = {}
    thr_int = r.random() < .12
    for k in names:
        if r.random() < .03 and k != "threshold":
            continue
        if k == "threshold":
            cols[k] = pl.Series([r.choice([0, 1, 5]) for _ in range(nt)], dtype=pl.Int64) if thr_int else col(r, nt, THR)
        else:
            cols[k] = col(r, nt, VAL)
    if r.random() < .05: cols["accuracy_at_50"] = col(r, nt, VAL)
    if r.random() < .05: cols["ROCModel"] = pl.Series([r.choice(["a", None]) for _ in range(nt)], dtype=pl.String)
    if r.random() < .03: del cols["threshold"]
    ta = pl.DataFrame(cols)
    na = h()
    auc = {"ROCModel": pl.Series(["Logistic Model"] * na, dtype=pl.String), "AUC": col(r, na, VAL), "Gini": col(r, na, VAL)}
    if r.random() < .08: del auc["ROCModel"]
    if r.random() < .05: auc["threshold"] = col(r, na, VAL)
    ks = {"KS_Statistic": col(r, ns, VAL), "KS_Cutoff": col(r, ns, VAL)}
    if r.random() < .05: ks["AUC"] = pl.Series([r.choice(["x", None]) for _ in range(ns)], dtype=pl.String)
    npsi = h()
    psi = {"PSI": col(r, npsi, VAL)}
    if r.random() < .05: psi["accuracy_at_50"] = col(r, npsi, VAL)
    return ta, pl.DataFrame(auc), pl.DataFrame(ks), pl.DataFrame(psi), r.random() < .6


def kind(s):
    return {pl.Float64: "f", pl.Int64: "i", pl.String: "s", pl.Date: "d", pl.Null: "n"}.get(s.dtype, "?")


def excl(a, b):
    ka, kb = kind(a), kind(b)
    if ka == "d": return kb not in ("d", "n")
    return ka == "f" and kb == "s"


def merge_pre(frames):
    for f in frames:
        if len(set(f.columns)) != len(f.columns) or any(s.len() != f.height for s in f.iter_columns()): return False
    for f in frames:
        for g in frames:
            for p in f.iter_columns():
                for q in g.iter_columns():
                    if p.name == q.name and excl(p, q): return False
    return True


def precond(ta, auc, ks, psi, valid):
    if len(set(ta.columns)) != len(ta.columns): return False
    if "threshold" not in ta.columns or ta.schema["threshold"] not in (pl.Float64, pl.Int64): return False
    new = ["accuracy", "precision", "recall", "f1_score", "specificity"]
    if any(n not in ta.columns for n in new): return False
    ren = {n: n + "_at_50" for n in new}
    nm = [ren.get(c, c) for c in ta.columns]
    if len(set(nm)) != len(nm): return False
    for f in (auc, ks, psi):
        if len(set(f.columns)) != len(f.columns): return False
    at50 = ta.filter(pl.col("threshold") == 0.5).rename(ren)
    fr = [auc, ks, psi, at50] if valid else [auc, psi, at50]
    if not merge_pre(fr): return False
    names = {c for f in fr for c in f.columns}
    return "threshold" in names and "ROCModel" in names


def py(ta, auc, ks, psi, valid):
    ns = {"pl": pl, "dt": dt, "sas_compat": sas_compat, "threshold_analysis": ta, "auc_summary": auc, "ks_statistic": ks,
          "psi_summary": psi, "valid_exists": valid}
    exec(compile(SRC, "metrics_calculation.py:527-547", "exec"), ns)  # noqa: S102
    return ns["model_performance_metrics"]


N = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
kept = gen_ = rej_raise = 0
raises = []
stats = {"valid_false": 0, "rows_nonzero": 0, "int_thr": 0}
for seed in range(N):
    inp = gen(seed); gen_ += 1
    ok = precond(*inp)
    try:
        out = py(*inp)
    except Exception as e:  # noqa: BLE001
        if ok: raises.append((seed, type(e).__name__, str(e)[:100]))
        else: rej_raise += 1
        continue
    if not ok: continue
    kept += 1
    stats["valid_false"] += not inp[4]
    stats["rows_nonzero"] += out.height > 0
    stats["int_thr"] += inp[0].schema["threshold"] == pl.Int64
    if not inp[4]:
        assert out.height == 0 and "KS_Statistic" not in out.columns
print("generated", gen_, "kept", kept, "python raises inside precondition", len(raises), raises[:5], "raises outside", rej_raise, stats)
