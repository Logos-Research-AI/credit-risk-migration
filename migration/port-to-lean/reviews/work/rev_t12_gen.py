"""Review of T12 (port-translator-2) by port-translator-3: edge frames for def:metrics_run_01_roc_auc.
Python: lines 114-152 of metrics_calculation.py executed verbatim with the module's globals.
fsum in Lean is a left fold; a case is kept only when Python agrees with math.fsum replaced by one."""
import sys, math, json, textwrap
from pathlib import Path
import polars as pl
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "diffeval"))
import leanterm as lt, compare as cmp, kit
from credit_risk import metrics_calculation as mc

src = "".join(Path(mc.__file__).read_text().splitlines(keepends=True)[113:152])
assert src.lstrip().startswith("roc_stats = sas_compat.roc_association(") and ".head(min(auc_pairs.height, 1))" in src
CODE = compile(textwrap.dedent(src), "mc:114-152", "exec")
nan, inf = float("nan"), float("inf")

def py(df):
    ns = dict(vars(mc)); ns["logit_scored_valid"] = df
    exec(CODE, ns)
    return ns["roc_stats"], ns["auc_summary"], ns["auc_pairs"]

def dg(df): return cmp.digest(cmp.tokens(cmp.canon_frame(df)))

C = [
    ("plain", [1, 0, 1, 0, 0], [0.9, 0.1, 0.4, 0.4, 0.7]),
    ("all_null_pd", [1, 0], [None, None]),
    ("nan_pd", [1, 0, 1, 0], [nan, 0.2, 0.7, nan]),
    ("zeros", [1, 0, 0, 1], [0.0, -0.0, 0.5, -0.0]),
    ("odd_flags", [1, 0, 2, nan, None, 1, 0], [0.3, 0.6, 0.1, 0.2, 0.5, None, 0.25]),
    ("single_class", [1, 1, 1], [0.1, 0.2, 0.2]),
    ("no_class", [2, 3], [0.1, 0.2]),
    ("one_row", [0], [0.5]),
    ("close", [1, 0, 1, 0], [0.5, 0.5 + 5e-9, 0.5 + 5e-9, 0.25]),
    ("inf", [1, 0, 1, 0], [inf, -inf, inf, 1.0]),
    ("unsorted_ties", [0, 1, 1, 0, 1, 0, 0, 1], [0.7, 0.2, 0.7, 0.2, 0.9, 0.1, 0.7, 0.1]),
]
terms, exp, names = [], [], []
for name, y, s in C:
    df = pl.DataFrame({"default_flag": pl.Series(y, dtype=pl.Float64), "pd_logistic": pl.Series(s, dtype=pl.Float64)})
    r, a, p = py(df)
    o = math.fsum
    try:
        math.fsum = lambda xs: sum(xs, 0.0)
        r2, a2, _ = py(df)
    finally:
        math.fsum = o
    same = dg(r) == dg(r2)
    print(f"{name:14s} fold==fsum:{same} roc={r.rows()} auc={a.rows()} schema={dict(a.schema)} pairs={p.rows()}")
    if not same: continue
    names.append(name); exp += [dg(df), dg(r), dg(a)]
    def cell(v):
        if v is None: return "n"
        if v != v or v in (inf, -inf) or repr(v) not in ("0.0","1.0","2.0","3.0","0.5","0.25","0.1","0.2","0.3","0.4","0.6","0.7","0.9"): return "o " + lt.lean_float(v)
        return "o " + repr(v)
    terms.append("one (fr [" + ", ".join(cell(v) for v in df["default_flag"].to_list()) + "] [" + ", ".join(cell(v) for v in df["pd_logistic"].to_list()) + "])")
body = ("(" + kit.KIT_NOTABLE + "let fs := fun (l : List Float) => l.foldl (fun (a x : Float) => a + x) 0.0; "
        "let o := fun (x : Float) => (some x : Option Float); let n : Option Float := none; let fr := fun (y s : List (Option Float)) => ([(\"default_flag\", Pl.Col.f64 y), (\"pd_logistic\", Pl.Col.f64 s)] : Pl.Frame Float); let one := fun (f : Pl.Frame Float) => let r := metrics_run_01_roc_auc fs f; [dg (tR f), dg (tR r.1), dg (tR r.2)]; "
        + " ++ ".join(terms) + ")")
json.dump({"names": names, "expected": exp}, open(HERE / "rev_t12.json", "w"))
print(len(body)); print(body[len(kit.KIT_NOTABLE) + 1:])
