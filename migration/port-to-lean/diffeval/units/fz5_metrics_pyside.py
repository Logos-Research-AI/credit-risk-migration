"""Fuzz 2026-11-18 (reviewer of five metrics preconditions). PYTHON SIDE ONLY:
no carrier item exists in the blueprint, so nothing could be sent to eval_decl (see the report).
Runs the real source of steps 01, 02, 04, 06, 07 (cut by marker text, executed with the module globals)
on pooled seeded frames and checks that Python does not raise inside the new preconditions.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz5_metrics_pyside.py
"""
import math, sys, textwrap
from pathlib import Path
import polars as pl
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE))
import kit
import fz_t1_gen as f1
from credit_risk import metrics_calculation as mc

nan, inf = float("nan"), float("inf")
L = Path(mc.__file__).read_text().splitlines(keepends=True)


def cut(a, b, extra=0):
    i = next(k for k, l in enumerate(L) if a in l)
    j = next(k for k in range(i, len(L)) if b in L[k])
    return compile(textwrap.dedent("".join(L[i:j + 1 + extra])), f"mc:{i+1}-{j+1}", "exec")


S01 = cut("roc_stats = sas_compat.roc_association(", ".head(min(auc_pairs.height, 1))", 1)
S02 = cut("logit_scored_valid = logit_scored_valid.sort(", 'KS_Cutoff=sas_compat.sql_min', 1)
S04 = cut("decile_data = logit_scored_valid.with_columns(", "decile_analysis_formats = {", -1)
S06 = cut("train_scores_sorted = ", 'otherwise(pl.lit("Significant change"))', 1)
S07 = cut("calibration_data = logit_scored_valid.with_columns(", '.sort("pred_bin", maintain_order=True)', 1)


def run(code, **env):
    ns = dict(vars(mc)); ns.update(env); exec(code, ns); return ns


NS = [0, 1, 2, 3, 4, 5, 8, 9, 10, 13, 19, 20, 24, 40]
GEN_ = [None, nan, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, -0.0, 2.0, 0.5, inf]
FE = [GEN_, [0.0], [1.0], [0.0, 1.0], [0.0, 1.0], [0.0, 1.0, None]]
FPE = [97, 100, 100, 100, 100, 97]
u = math.nextafter
EDGE = [None, nan, inf, -inf, 0.0, -0.0, 0.5, u(.5, 0), u(.5, 1), .25, .75, 1.0, 1e300, 1e-300, 5e-324, .1, .2, .3, .4, .6, .7,
        u(.3, 0), u(.3, 1), u(.7, 0), u(.7, 1), -1.0, 2.0]
PE = [EDGE, [0.25, 0.5, 0.75, None], EDGE, [0.1, 0.2, 0.3, 0.4]]
PPE = [70, 100, 20, 100]


def frame(s):
    n = NS[kit.hsh(s, 7) % len(NS)]
    fm, pm = kit.hsh(s, 9) % 6, kit.hsh(s, 8) % 4
    return pl.DataFrame({"default_flag": pl.Series(kit.gF(2 * s, n, FPE[fm], 2, FE[fm]), dtype=pl.Float64, nan_to_null=False),
                         "pd_logistic": pl.Series(kit.gF(2 * s + 1, n, PPE[pm], 2, PE[pm]), dtype=pl.Float64, nan_to_null=False)})


def pre_rank(x, k, desc):
    nn = x.len() - x.null_count()
    for r in x.rank("average", descending=desc).to_list():
        if r is not None and not (-2**63 <= math.floor(r * float(k) / float(nn + 1)) < 2**63):
            return False
    return True


T = [None, nan, inf, -inf, 0.0, -0.0, 1e300, 5e-324, 700.0, u(700., inf), u(700., 0), 650.0, 600.0, u(600., 0), u(600., inf), 1.0, 4.0]
SZ = [0, 1, 2, 3, 5, 9, 10, 11, 20, 37]


def col06(s, n, m):
    if m == 0:
        return pl.Series("credit_risk_score", kit.gF(s, n, 60, 3, T), dtype=pl.Float64, nan_to_null=False)
    if m == 1:
        a, b = kit.gI(s, n, 10, 6, 0), kit.gI(s + 1, n, 0, 3, 0)
        return pl.Series("credit_risk_score", [None if x is None else u(float(600 + 10 * x), (0.0, -inf, inf)[y]) if y else float(600 + 10 * x)
                                               for x, y in zip(a, b)], dtype=pl.Float64)
    if m == 2:
        return pl.Series("credit_risk_score", [None if x is None else float(500 + 7 * x) for x in kit.gI(s, n, 5, 40, 0)], dtype=pl.Float64)
    return pl.Series("credit_risk_score", [None] * n, dtype=pl.String)


stats = {}


def tally(k, ok, raised, msg=""):
    d = stats.setdefault(k, dict(gen=0, kept=0, raise_in=[], raise_out=0, empty_kept=0))
    d["gen"] += 1
    if ok:
        d["kept"] += 1
        if raised:
            d["raise_in"].append(msg[:200])
    elif raised:
        d["raise_out"] += 1


N = 3000
for s in range(30000, 30000 + N):
    df = frame(s)
    for k, code, pre in [("01", S01, lambda d: f1.pre_roc(d["default_flag"], d["pd_logistic"])),
                         ("02", S02, lambda d: True),
                         ("04", S04, lambda d: pre_rank(d["pd_logistic"], 10, True)),
                         ("07", S07, lambda d: pre_rank(d["pd_logistic"], 20, False))]:
        ok = pre(df); raised = False; msg = ""
        try:
            run(code, logit_scored_valid=df)
        except Exception as e:  # noqa: BLE001
            raised, msg = True, f"seed {s} n={df.height} {type(e).__name__}: {e}"
        tally(k, ok, raised, msg)
        stats[k]["empty_kept"] += ok and df.height == 0
    nt, nv = SZ[kit.hsh(s, 9001) % 10], SZ[kit.hsh(s, 9002) % 10]
    mt, mv = kit.hsh(s, 9003) % 4, kit.hsh(s, 9004) % 3
    t, v = pl.DataFrame([col06(s, nt, mt)]), pl.DataFrame([col06(s + 500000, nv, mv)])
    ok = nt > 0
    raised, msg = False, ""
    try:
        ns = run(S06, logit_scored_train=t, logit_scored_valid=v)
        if mt == 3 and nt > 0:
            ns2 = run(S06, logit_scored_train=t.with_columns(pl.col("credit_risk_score").cast(pl.Float64)), logit_scored_valid=v)
            same = all(ns[k].equals(ns2[k], null_equal=True) for k in ("psi_calculation", "psi_summary"))
            stats.setdefault("06 strnull==f64null", [0, 0])[0 if same else 1] += 1
    except Exception as e:  # noqa: BLE001
        raised, msg = True, f"seed {s} nt={nt} nv={nv} mt={mt} {type(e).__name__}: {e}"
    tally("06", ok, raised, msg)
    stats["06"]["empty_kept"] += ok and nv == 0
    stats.setdefault("06 strnull cases", 0)
    stats["06 strnull cases"] += ok and mt == 3

for k, d in sorted(stats.items(), key=lambda kv: str(kv[0])):
    print(k, {a: (b if not isinstance(b, list) else len(b)) for a, b in d.items()} if isinstance(d, dict) else d,
          d["raise_in"][:3] if isinstance(d, dict) else "")
