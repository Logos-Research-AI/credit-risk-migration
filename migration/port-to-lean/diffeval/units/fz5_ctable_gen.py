"""Fuzz of def:train_run_08_ctable + def:train_run_08_ctable_precond (revision d6d7492b / 53a554a5), fifth round.
  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz5_ctable_gen.py [N]
-> diffeval/work/fz5_ctable.cases.json: for each case the eval_decl input (the 14 arguments of the unit, as the tool
   takes them: one case per input; no operator can follow the arguments, so no shared lets) and the Python result.
The Python is train.py:477-535 EXECUTED AS IT STANDS (lines sliced from the file), with sas_compat.np replaced by a proxy
(np.linalg.solve / np.linalg.inv / np.log1p = the stand-ins below, which are the Lean's explicit parameters) and
sas_compat.fmt_wd / write_sas_csv replaced by the stand-in formatter and a capture.
"""
from __future__ import annotations
import json, math, struct, sys, types, random, textwrap
from pathlib import Path
import numpy as np, polars as pl
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from credit_risk import sas_compat as sc, train

nan = float("nan")
def bits(x): return struct.unpack("<Q", struct.pack("<d", float(x)))[0]
def lf(x):
    x = float(x)
    if x != x: return "(0.0/0.0)"
    if x == math.inf: return "(1.0/0.0)"
    if x == -math.inf: return "(-1.0/0.0)"
    if math.copysign(1, x) < 0: return f"(-{abs(x)!r})" if x != 0 else "(-0.0)"
    return repr(x)
def lo(x): return "none" if x is None else (f"some {lf(x)}" if not lf(x).startswith("(") or lf(x).startswith("(-") else f"some {lf(x)}")
def lst(vals, f):
    """a list literal; a run of one repeated value of length >= 4 is List.replicate"""
    if len(vals) >= 4 and all(v == vals[0] and (v is None) == (vals[0] is None) and (bits(v) == bits(vals[0]) if isinstance(v, float) and v == v else True) for v in vals):
        return f"(List.replicate {len(vals)} {f(vals[0])})" if not f(vals[0]).startswith("some") else f"(List.replicate {len(vals)} ({f(vals[0])}))"
    return "[" + ", ".join(f(v) for v in vals) + "]"
def lb(b): return "true" if b else "false"

# ---- stand-ins (Lean text, Python mirror)
FMT = '(fun (v : Option Float) w d => match v with | none => "N" | some x => toString (x.toBits.toNat % 9973))'
SOLVE = ('(fun m b => match m, b with | [[a]], [x] => [x / a] | [[a, p], [c, d]], [x, y] => '
         '[(x * d - p * y) / (a * d - p * c), (a * y - c * x) / (a * d - p * c)] | _, _ => b)')
DOT = '(fun u v => (u.zip v).foldl (fun s p => s + p.1 * p.2) 0.0)'
MATMUL = '(fun a b => a.map fun r => (List.range (b.headD []).length).map fun j => (r.zip (b.map (·.getD j 0.0))).foldl (fun s p => s + p.1 * p.2) 0.0)'
MATVEC = '(fun _ _ => [])'
EINSUM = '(fun x v => x.map fun _ => (v.headD []).headD 0.0)'
LOG1P = '(fun x => Float.log (1.0 + x))'
def inv_lean(a): return f'(fun m => m.mapIdx fun i r => r.mapIdx fun j _ => if i + j == 0 then {lf(a)} else 0.0)'

def fmt_py(v, w, d):
    if v is None or (isinstance(v, float) and v != v and False): return "N"
    b = 0x7FF8000000000000 if float(v) != float(v) else bits(v)
    return str(b % 9973)
def solve_py(m, b):
    m = np.asarray(m, dtype=np.float64); b = np.asarray(b, dtype=np.float64)
    with np.errstate(all="ignore"):
        if m.shape == (1, 1): return np.array([b[0] / m[0, 0]])
        a, p, c, d = m[0, 0], m[0, 1], m[1, 0], m[1, 1]; x, y = b[0], b[1]
        det = a * d - p * c
        return np.array([(x * d - p * y) / det, (a * y - c * x) / det])
class NPX:
    def __init__(self, a):
        def inv(m):
            k = m.shape[0]; o = np.zeros((k, k))
            if k: o[0, 0] = a
            return o
        self.linalg = types.SimpleNamespace(solve=solve_py, inv=inv)
    def log1p(self, x):
        with np.errstate(all="ignore"): return np.log(1.0 + x)
    def __getattr__(self, k): return getattr(np, k)

def slice_src():
    src = Path(train.__file__).read_text().splitlines()
    first = next(i for i, l in enumerate(src) if l.strip() == "x_final = np.column_stack(")
    last = next(i for i, l in enumerate(src) if 'output_dir / "printed_classification.csv"' in l)
    return textwrap.dedent("\n".join(src[first:last + 2])), first + 1, last + 2
SLICE, L0, L1 = slice_src()

def run_py(c):
    """c: dict; returns (result, exception)."""
    writes = []
    proxy = types.SimpleNamespace(classification_table=sc.classification_table, classification_is_made=sc.classification_is_made,
                                  fmt_wd=fmt_py, write_sas_csv=lambda df, path, formats=None: writes.append((Path(path).name, df.clone())))
    ff = pl.DataFrame({k: pl.Series(v, dtype=pl.Float64) for k, v in c["cols"].items()})
    sd = pl.DataFrame({"pd_logistic": pl.Series(c["pd"], dtype=pl.Float64)})
    fin = None
    if c["final"] is not None:
        n = len(c["names"]); cov = np.zeros((n, n))
        for i, v in enumerate(c["final"]): cov[i, i] = v
        fin = sc.LogisticFit(list(c["names"]), np.zeros(n), cov, 0.0, 0, True)
    ns = {"np": np, "pl": pl, "sas_compat": proxy, "fit_frame": ff, "n_obs": c["n"], "y_train": np.array(c["y"], dtype=np.float64),
          "final": fin, "final_names": list(c["names"]), "logit_scored_train": sd, "fit_mask": np.array(c["mask"], dtype=bool),
          "output_dir": Path("out")}
    old = sc.np
    try:
        sc.np = NPX(c["a"])
        with np.errstate(all="ignore"):
            exec(compile(SLICE, "train.py", "exec"), ns)
        res = []
        for nm, df in writes:
            res.append([nm, [[str(v) for v in df.get_column(k).to_list()] for k in df.columns], df.columns])
        run_py.ns = ns
        return res, None
    except Exception as ex:  # noqa
        run_py.ns = ns
        return None, ex
    finally:
        sc.np = old

def lean_input(c):
    cols = ", ".join(f'("{k}", Pl.Col.f64 {lst(vs, lo)})' for k, vs in c["cols"].items())
    fin = "none"
    if c["final"] is not None:
        n = len(c["names"])
        cov = "[" + ", ".join("[" + ", ".join(lf(c["final"][i]) if i == j else "0.0" for j in range(n)) + "]" for i in range(n)) + "]"
        nm = "[" + ", ".join(f'"{s}"' for s in c["names"]) + "]"
        fin = f"(some {{ names := {nm}, beta := Np.NDArray.d1 [], cov := Np.NDArray.d2 {cov}, loglik := 0.0, n_iter := 0, converged := true }})"
    names = "[" + ", ".join(f'"{s}"' for s in c["names"]) + "]"
    return " ".join([FMT, inv_lean(c["a"]), SOLVE, DOT, MATMUL, MATVEC, EINSUM, LOG1P,
                     lst(c["mask"], lb), f"[{cols}]", fin, names, str(c["n"]),
                     lst(c["y"], lf), f'[("pd_logistic", Pl.Col.f64 {lst(c["pd"], lo)})]'])


# ------------------------------------------------------------------ cases
SHORT = FMT + " (fun m => m) (fun _ b => b) (fun _ _ => 0.0) (fun _ _ => []) (fun _ _ => []) (fun _ _ => []) (fun x => x) "
FULL_PRE_LEN = lambda c: len(" ".join([FMT, inv_lean(c["a"]), SOLVE, DOT, MATMUL, MATVEC, EINSUM, LOG1P]) + " ")
def lean_input2(c):
    s = lean_input(c)
    if c["final"] is None:  # no library routine is reached: short stand-ins
        s = SHORT + s[FULL_PRE_LEN(c):]
    return s

PBASE = [0.5, 0.25, 0.75, 0.3, 0.7, 0.02, 0.98, 0.125, 0.875]
def gen_case(rng):
    n = rng.choice([0, 1, 1, 2, 2, 3, 4, 5, 6, 9, 11, 26])
    nv = rng.choice([0, 0, 1, 1, 2])
    has_fin = rng.random() > 0.2
    names, cols = ["Intercept"], {}
    for k in range(nv):
        mode = rng.choice(["rand", "rand", "dupname", "const1", "zero", "double", "negzero"]) if k else rng.choice(["rand", "rand", "rand", "const1", "zero", "negzero"])
        if mode == "dupname":
            names.append(names[-1]); continue
        nm = f"x{k + 1}"
        if mode == "const1": v = [1.0] * n
        elif mode == "zero": v = [0.0] * n
        elif mode == "negzero": v = [rng.choice([0.0, -0.0, 1.0]) for _ in range(n)]
        elif mode == "double" and k: v = [2.0 * t for t in cols["x1"]]
        else: v = [float(rng.randint(-3, 3)) for _ in range(n)]
        cols[nm] = v; names.append(nm)
    if rng.random() < 0.3: cols["extra"] = [float(rng.randint(0, 4)) for _ in range(n)]
    extra = rng.choice([0, 0, 1, 2])
    pos = set(rng.sample(range(n + extra), n)) if n + extra else set()
    mask = [i in pos for i in range(n + extra)]
    if len(names) == 1 and n >= 2:
        pr = rng.choice([0.0, 0.1, 0.5, 0.9, 1.0])
        y = [1.0 if rng.random() < pr else 0.0 for _ in range(n)]
    else:
        y = [float(rng.randint(0, 1)) for _ in range(n)]
    pb, spread = rng.choice(PBASE), rng.choice([0.0, 0.0, 0.005, 0.01])
    pd = [min(0.999, max(0.001, pb + rng.choice([-1, 0, 0, 1]) * spread)) if mask[i] else rng.choice([None, 0.5, 2.0, nan]) for i in range(n + extra)]
    if rng.random() < 0.04 and n: pd[mask.index(True)] = None  # null pd_logistic on a complete case: outside the precondition
    final = [rng.choice([1.0, 1.0, 1.0, 0.0, -0.0, 2.5, nan, 0.0]) for _ in names] if has_fin else None
    return dict(n=n, names=names, cols=cols, final=final, mask=mask, pd=pd, y=y, a=rng.choice([0.0, 0.0, 0.25, 1.0, 4.0]))

def judge(c):
    """-> (result, exception, precondition holds, ctable_made)."""
    res, ex = run_py(c)
    ns = run_py.ns
    n, names, mask = c["n"], c["names"], c["mask"]
    if any(v is None for k in names[1:] for v in c["cols"][k]): return res, ex, False, None
    if any(mask[i] and c["pd"][i] is None for i in range(len(mask))): return res, ex, False, ns.get("ctable_made")
    if c["final"] is None: return res, ex, ex is None, False
    if n == 0: return res, ex, False, ns.get("ctable_made")   # x.T @ x of no row is not the square product the routine returns; ps is empty
    if ex is not None: return res, ex, False, ns.get("ctable_made")
    made = bool(ns["ctable_made"])
    if not made: return res, ex, True, made
    if sum(mask) != n or len(c["y"]) != n: return res, ex, False, made
    pdt = [c["pd"][i] for i in range(len(mask)) if mask[i]]
    if len(names) > 1 and not all(0.0 < t < 1.0 for t in pdt): return res, ex, False, made
    if len(names) == 1 and n - 1.0 == 0.0: return res, ex, False, made
    n1 = float(np.sum(c["y"]))
    if not (math.isfinite(n1) and math.floor(n1) == n1): return res, ex, False, made
    lv = ns["ctable"].get_column("ProbLevel").to_list()
    if not (lv and lv[0] >= 0.0 and lv[-1] <= 1.0): return res, ex, False, made
    return res, ex, True, made

def rows_of(res):
    if not res: return None
    name, cols, names = res[0]
    return [name, [list(r) for r in zip(*cols)] if cols and cols[0] else []]

if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    seed0 = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    out, stats = [], {"generated": 0, "kept": 0, "raises_inside": 0, "raises_outside": 0, "rejected_returns": 0, "too_wide": 0, "made": 0, "not_made_some": 0, "none": 0}
    wide_left = 10
    for sd in range(seed0, seed0 + N):
        rng = random.Random(sd)
        c = gen_case(rng)
        res, ex, pre, made = judge(c)
        stats["generated"] += 1
        if ex is not None:
            stats["raises_inside" if pre else "raises_outside"] += 1; continue
        if not pre:
            stats["rejected_returns"] += 1; continue
        nr = len(res[0][1][0]) if res else 0
        if nr > 4:
            if wide_left <= 0 or nr > 14: stats["too_wide"] += 1; continue
            wide_left -= 1
        stats["kept"] += 1
        stats["none" if c["final"] is None else ("made" if made else "not_made_some")] += 1
        out.append({"seed": sd, "input": lean_input2(c), "expected": rows_of(res), "rows": nr, "case": {k: v for k, v in c.items() if k != "a"} | {"a": c["a"]}})
    (HERE.parent / "work" / "fz5_ctable.cases.json").write_text(json.dumps(out, default=lambda x: None if x != x else x))
    print(stats, "chars", sum(len(o["input"]) for o in out))
