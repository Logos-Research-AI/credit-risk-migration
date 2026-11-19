"""Fuzz of def:classification_table (+ def:classification_table_precond, read as the filter), fifth port diff
(2026-11-18), by a non-author. Evaluated through the carrier def:zz_carrier_e (decl zz_carrier_e, one input
that is a whole sweep; the printer is dg_frame). Nothing is written on the blueprint by this script.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz5_cte_gen.py text LO N
      -> prints the eval_decl input for seeds LO..LO+N-1 (one input: the digests of N cases, in order)
  ... run LO N      -> work/fz5_cte_LO_N.expected.json: per seed the digest of Python's table, or null when Python raises,
                       and the class of the case (see CLASSES)
  ... cmp LO N file -> compares the Lean output (a JSON list of integers, one per seed) with the expected file
  ... show S        -> the case of seed S (Python side) with its table at 6 decimals

A case is built INSIDE Lean from hsh (kit.GEN) and mirrored here: n rows (0..20), 0..2 variables besides the
intercept (modes: random small integers, duplicate of the previous column, twice it, zeros, one-hot on one row
(leverage 1), scaled by 1e-3 / 1e3 / 1e8, 0/1), y (random, all ones, all zeros, one value 2, alternating, rare
events), one of four call shapes (pd keyword; inventory order (X, y, pd); a fit; a fit and pd), pd from a pool
(0.0 and 1.0 rare, constant pd 1 case in 4), beta from a pool (+-40: weight 0).
Library routines are stand-ins written identically in Lean and here: solve = Gauss elimination with partial pivoting,
inv = solving the unit columns (no raise), every dot / matrix product / einsum a sequential sum from 0.0, log1p x =
log(1 + x). Python runs the REAL sas_compat source (sas_compat.py parsed, every `a @ b` replaced by the sequential
product, np.linalg.solve / inv / einsum / log1p replaced by the stand-ins, np.exp / np.log real). A case on which
Python raises is not compared (Lean returns a value there; the precondition excludes it).
"""
from __future__ import annotations

import ast
import json
import math
import struct
import sys
import types
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[3] / "port"))
import kit  # noqa: E402

M64 = (1 << 64) - 1
hsh = kit.hsh
NAN, INF = float("nan"), float("inf")
f64 = np.float64
WORK = HERE.parent / "work"


def md(s, k, m):
    return hsh(s, k) % m


def bits(x):
    return 0x7FF8000000000000 if x != x else struct.unpack("<Q", struct.pack("<d", float(x)))[0]


def fromb(b):
    return struct.unpack("<d", struct.pack("<Q", b))[0]


# ------------------------------------------------------------------ stand-ins (Python mirror)
def solveG(A, b):
    n = len(A)
    M = [[f64(v) for v in A[i]] + [f64(b[i])] for i in range(n)]
    for k in range(n):
        best = k
        for r in range(n):
            if k <= r and abs(M[r][k]) > abs(M[best][k]):
                best = r
        Ms = [M[best] if r == k else (M[k] if r == best else M[r]) for r in range(n)]
        pr = Ms[k]
        out = []
        for r in range(n):
            if k < r:
                row = Ms[r]
                f = row[k] / pr[k]
                out.append([row[c] - f * pr[c] for c in range(n + 1)])
            else:
                out.append(Ms[r])
        M = out
    xs = []
    for t in range(n):
        i = n - 1 - t
        row = M[i]
        s = f64(0.0)
        for q in range(len(xs)):
            s = s + row[i + 1 + q] * xs[q]
        xs = [(row[n] - s) / row[i]] + xs
    return xs


def invG(A):
    n = len(A)
    cols = [solveG(A, [1.0 if i == j else 0.0 for i in range(n)]) for j in range(n)]
    return [[cols[j][i] for j in range(n)] for i in range(n)]


def dotS(u, v):
    s = f64(0.0)
    for a, b in zip(u, v):
        s = s + f64(a) * f64(b)
    return s


def mm(a, b):
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    if a.ndim == 2 and b.ndim == 2:
        out = np.zeros((a.shape[0], b.shape[1]))
        for i in range(a.shape[0]):
            for j in range(b.shape[1]):
                out[i, j] = dotS(a[i, :], b[:, j])
        return out
    if a.ndim == 2:
        return np.array([dotS(a[i, :], b) for i in range(a.shape[0])], dtype=np.float64)
    return dotS(a, b)


def einsumS(spec, x, v, x2):
    assert spec == "ij,jk,ik->i"
    out = []
    for i in range(x.shape[0]):
        s = f64(0.0)
        for j in range(x.shape[1]):
            inner = f64(0.0)
            for k in range(v.shape[1]):
                inner = inner + v[j, k] * x2[i, k]
            s = s + x[i, j] * inner
        out.append(s)
    return np.array(out, dtype=np.float64)


class NPX:
    def __init__(self):
        def ws(A, b):
            A = np.asarray(A)
            b = np.asarray(b)
            return np.array([float(v) for v in solveG(A.tolist(), b.tolist())], dtype=np.float64)

        def wi(A):
            m = invG(np.asarray(A).tolist())
            k = len(m)
            return np.array(m, dtype=np.float64).reshape(k, k)

        self.linalg = types.SimpleNamespace(solve=ws, inv=wi, LinAlgError=np.linalg.LinAlgError)

    def einsum(self, spec, x, v, x2):
        return einsumS(spec, np.asarray(x), np.asarray(v), np.asarray(x2))

    def log1p(self, x):
        with np.errstate(all="ignore"):
            return np.log(1.0 + np.asarray(x))

    def __getattr__(self, k):
        return getattr(np, k)


class _Mm(ast.NodeTransformer):
    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, ast.MatMult):
            return ast.copy_location(ast.Call(func=ast.Name("_mm", ast.Load()), args=[node.left, node.right], keywords=[]), node)
        return node


CAP = {}


def _cap(d):
    CAP.clear()
    CAP.update({k: v for k, v in d.items() if k in ("p", "eta", "w", "h", "q", "ps", "lone", "v")})


def load_module():
    src = (HERE.parents[3] / "port" / "credit_risk" / "sas_compat.py").read_text()
    tree = ast.parse(src)
    for node in tree.body:  # capture locals of classification_table before its return
        if isinstance(node, ast.FunctionDef) and node.name == "classification_table":
            idx = next(i for i, b in enumerate(node.body) if isinstance(b, ast.FunctionDef) and b.name == "pct")
            node.body.insert(idx, ast.parse("_cap(locals())").body[0])
    tree = ast.fix_missing_locations(_Mm().visit(tree))
    ns = {"__name__": "sc_mm", "__file__": "sas_compat_mm.py", "_mm": mm, "_cap": _cap}
    mod = types.ModuleType("sc_mm"); mod.__dict__.update(ns); sys.modules["sc_mm"] = mod; ns = mod.__dict__
    exec(compile(tree, "sas_compat.py", "exec"), ns)
    ns["np"] = NPX()
    return ns


# ------------------------------------------------------------------ the case (Python mirror of the Lean text)
NS = [0, 1, 2, 3, 4, 5, 6, 8, 12, 20]
VS = [1.0 / 1000.0, 1000.0, 100000000.0]
PDP = [0.5, 0.25, 0.75, 0.3, 0.7, 0.02, 0.98, 0.125, 0.875, 0.999, 0.001, fromb(4607182418800017407)]
BP = [0.0, 1.0, -1.0, 0.5, -0.5, 2.0, 40.0, -40.0, 1.0 / 1000.0, 0.25]


def gen(s):
    n = NS[md(s, 1, 10)]
    nv = md(s, 2, 3)
    ones = [1.0] * n

    def rnd(j):
        return [float(md(s, 100 + j * 32 + i, 7)) - 3.0 for i in range(n)]

    def mk(j, prev):
        m = md(s, 10 + j, 8)
        if m in (0, 1):
            return rnd(j)
        if m == 2:
            return list(prev)
        if m == 3:
            return [2.0 * t for t in prev]
        if m == 4:
            return [0.0] * n
        if m == 5:
            r = md(s, 50, n) if n else 0
            return [1.0 if i == r else 0.0 for i in range(n)]
        if m == 6:
            sc_ = VS[md(s, 60 + j, 3)]
            return [t * sc_ for t in rnd(j)]
        return [float(md(s, 100 + j * 32 + i, 2)) for i in range(n)]

    c1 = mk(1, ones)
    c2 = mk(2, c1)
    cols = [c1, c2][:nv]
    x = [[1.0] + [c[i] for c in cols] for i in range(n)]
    ym = md(s, 3, 6)
    rr = md(s, 51, n) if n else 0
    y = []
    for i in range(n):
        if ym == 0:
            y.append(float(md(s, 200 + i, 2)))
        elif ym == 1:
            y.append(1.0)
        elif ym == 2:
            y.append(0.0)
        elif ym == 3:
            y.append(2.0 if i == rr else float(md(s, 200 + i, 2)))
        elif ym == 4:
            y.append(float(i % 2))
        else:
            y.append(1.0 if md(s, 200 + i, 5) == 0 else 0.0)
    shape = md(s, 4, 4)
    constpd = md(s, 5, 4) == 0
    cp = PDP[md(s, 6, 12)]
    pd = []
    for i in range(n):
        if constpd:
            pd.append(cp)
        elif md(s, 300 + i, 25) == 0:
            pd.append(0.0 if md(s, 350 + i, 2) == 0 else 1.0)
        else:
            pd.append(PDP[md(s, 300 + i, 12)])
    beta = [BP[md(s, 400 + j, 10)] for j in range(nv + 1)]
    return dict(n=n, nv=nv, x=x, y=y, shape=shape, pd=pd, beta=beta)


# ------------------------------------------------------------------ digest (zz_e_tR / zz_e_dg)
def tS(t):
    return [len(t)] + [ord(c) for c in t]


def tokens_of(df):
    out = [len(df.columns)]
    for name in df.columns:
        col = df[name]
        out += tS(name)
        if name in ("CorrectNonevents", "IncorrectNonevents"):  # `.f64` in the Lean (R-F2I)
            out += [1, len(col)] + [t for v in col.to_list() for t in ([0] if v is None else [1, bits(float(v))])]
        elif name in ("CorrectEvents", "IncorrectEvents"):
            out += [2, len(col)] + [t for v in col.to_list() for t in ([1, v] if v >= 0 else [2, -v])]
        else:
            out += [1, len(col)] + [t for v in col.to_list() for t in ([0] if v is None else [1, bits(v)])]
    return out


def dg(toks):
    h = 14695981039346656037
    for x in toks:
        g = ((h ^ x) * 1099511628211) & M64
        h = g ^ (g >> 32)
    return h


MOD = None


def run(s):
    """-> (digest or None, exception name or None, class tag, table)"""
    global MOD
    if MOD is None:
        MOD = load_module()
    sc = MOD
    c = gen(s)
    n, nv = c["n"], c["nv"]
    x = np.array(c["x"], dtype=np.float64).reshape(n, nv + 1)
    y = np.array(c["y"], dtype=np.float64)
    pd = np.array(c["pd"], dtype=np.float64)
    fit = sc["LogisticFit"](["Intercept"] + [f"v{j}" for j in range(nv)], np.array(c["beta"]), np.zeros((nv + 1, nv + 1)), 0.0, 0, True)
    CAP.clear()
    try:
        with np.errstate(all="ignore"):
            sh = c["shape"]
            if sh == 0:
                df = sc["classification_table"](y, x, pd=pd)
            elif sh == 1:
                df = sc["classification_table"](x, y, pd)
            elif sh == 2:
                df = sc["classification_table"](y, x, fit)
            else:
                df = sc["classification_table"](y, x, fit, pd=pd)
    except Exception as ex:  # noqa: BLE001
        return None, type(ex).__name__, "raises", None, c
    tag = classify(c, CAP)
    return dg(tokens_of(df)), None, tag, df, c


def classify(c, cap):
    """Edge classes reached (for the report) and whether the precondition's numeric clauses hold, as far as Python can tell."""
    tags = []
    k = c["nv"] + 1
    if k == 1:
        tags.append("icpt")
    if "h" in cap:
        h = cap["h"]
        if any(float(t) != float(t) for t in h):
            tags.append("h nan")
        if any(1.0 - float(t) <= 1e-8 for t in h):
            tags.append("lone")
        if any(float(t) == 0.0 for t in cap["w"]):
            tags.append("w0")
        if bool(np.any(np.asarray(cap["v"]) == 0.0)) and k > 1 and np.all(np.asarray(cap["v"]) == 0.0):
            tags.append("v zero")
        elif k > 1 and np.any(np.diag(cap["v"]) == 0.0):
            tags.append("left-out")
        ps = cap["ps"]
        if len(ps) and any(float(t) != float(t) for t in ps):
            tags.append("ps nan")
    pd_ok = True
    if "ps" in cap and len(cap["ps"]) and "ps nan" not in tags:  # clause (7) as the Lean text computes it
        ps = [float(t) for t in cap["ps"]]
        tol = 1e-9 if k == 1 else 0.0
        klo = float(math.floor(min(ps) / 0.02 + tol))
        khi = -float(math.floor(-(max(ps) / 0.02 - tol)))
        if not (0.0 <= klo and khi <= 50.0 and klo <= khi):
            tags.append("klo/khi outside 0..50")
            pd_ok = False
    if c["shape"] in (0, 1, 3) and k > 1 and not all(0.0 < t < 1.0 for t in c["pd"]):
        pd_ok = False
        tags.append("pd outside (0,1)")
    s_ = sum(c["y"])
    if s_ != math.floor(s_):
        tags.append("n1 not integral")
    n1 = sum(c["y"])
    if n1 != math.floor(n1):
        pd_ok = False
    return "inside" if pd_ok and "ps nan" not in tags else "outside", tags


# ------------------------------------------------------------------ Lean text
def lit(v):
    if v == 0.0:
        return "(-0.0)" if math.copysign(1, v) < 0 else "0.0"
    r = repr(abs(v))
    if "e" in r or float(r) != abs(v):
        return f"(Float.ofBits {bits(v)})"
    return r if v > 0 else f"(-{r})"


def lf_(l):
    return "[" + ", ".join(lit(v) for v in l) + "]"


LETS = (
    "let nan : Float := 0.0 / 0.0; "
    + kit.GEN.split("let gF")[0]
    + "let md := fun (s k m : Nat) => ((hsh s k) % m.toUInt64).toNat; "
    # stand-ins
    "let solveG := fun (A : List (List Float)) (b : List Float) => "
    "let n := A.length; "
    "let M0 : List (List Float) := (A.zip b).map (fun (p : List Float × Float) => p.1 ++ [p.2]); "
    "let M := (List.range n).foldl (fun (M : List (List Float)) (k : Nat) => "
    "let best := (List.range n).foldl (fun (bp : Nat) (r : Nat) => if k ≤ r then (if Float.abs ((M.getD r []).getD k nan) > Float.abs ((M.getD bp []).getD k nan) then r else bp) else bp) k; "
    "let Ms : List (List Float) := (List.range n).map (fun (r : Nat) => if r == k then M.getD best [] else if r == best then M.getD k [] else M.getD r []); "
    "let pr := Ms.getD k []; "
    "(List.range n).map (fun (r : Nat) => if k < r then (let row := Ms.getD r []; let f := (row.getD k nan) / (pr.getD k nan); "
    "(List.range (n + 1)).map (fun (c : Nat) => row.getD c nan - f * pr.getD c nan)) else Ms.getD r [])) M0; "
    "(List.range n).foldl (fun (xs : List Float) (t : Nat) => let i := n - 1 - t; let row := M.getD i []; "
    "let s := (List.range xs.length).foldl (fun (s : Float) (q : Nat) => s + row.getD (i + 1 + q) nan * xs.getD q nan) 0.0; "
    "((row.getD n nan - s) / row.getD i nan) :: xs) []; "
    "let invG := fun (A : List (List Float)) => let n := A.length; "
    "let cols := (List.range n).map (fun (j : Nat) => solveG A ((List.range n).map (fun (i : Nat) => if i == j then 1.0 else 0.0))); "
    "(List.range n).map (fun (i : Nat) => cols.map (fun (col : List Float) => col.getD i nan)); "
    "let dotS := fun (u v : List Float) => (u.zip v).foldl (fun (s : Float) (p : Float × Float) => s + p.1 * p.2) 0.0; "
    "let mmS := fun (a b : List (List Float)) => a.map (fun (r : List Float) => (List.range (b.headD []).length).map "
    "(fun (j : Nat) => dotS r (b.map (fun (br : List Float) => br.getD j 0.0)))); "
    "let mvS := fun (m : List (List Float)) (v : List Float) => m.map (fun (r : List Float) => dotS r v); "
    "let esS := fun (x v : List (List Float)) => x.map (fun (xr : List Float) => "
    "(List.range xr.length).foldl (fun (s : Float) (j : Nat) => s + xr.getD j 0.0 * "
    "((List.range (v.headD []).length).foldl (fun (t : Float) (k : Nat) => t + (v.getD j []).getD k 0.0 * xr.getD k 0.0) 0.0)) 0.0); "
    "let l1S := fun (x : Float) => Float.log (1.0 + x); "
    # pools
    f"let NS : List Nat := {NS}; "
    f"let VS : List Float := [1.0 / 1000.0, 1000.0, 100000000.0]; "
    f"let PDP : List Float := {lf_(PDP)}; "
    f"let BP : List Float := [0.0, 1.0, -1.0, 0.5, -0.5, 2.0, 40.0, -40.0, 1.0 / 1000.0, 0.25]; "
    "let CT := fun (s : Nat) => "
    "let n := NS.getD (md s 1 10) 0; let nv := md s 2 3; "
    "let rnd := fun (j : Nat) => (List.range n).map (fun (i : Nat) => Float.ofNat (md s (100 + j * 32 + i) 7) - 3.0); "
    "let mk := fun (j : Nat) (prev : List Float) => "
    "(match md s (10 + j) 8 with "
    "| 0 => rnd j | 1 => rnd j | 2 => prev | 3 => prev.map (fun (t : Float) => 2.0 * t) | 4 => (List.replicate n 0.0) "
    "| 5 => (let r := md s 50 n; (List.range n).map (fun (i : Nat) => if i == r then 1.0 else 0.0)) "
    "| 6 => (let c := VS.getD (md s (60 + j) 3) 1.0; (rnd j).map (fun (t : Float) => t * c)) "
    "| _ => (List.range n).map (fun (i : Nat) => Float.ofNat (md s (100 + j * 32 + i) 2)) : List Float); "
    "let c1 := mk 1 (List.replicate n 1.0); let c2 := mk 2 c1; "
    "let cols : List (List Float) := ([c1, c2].take nv); "
    "let xl : List (List Float) := (List.range n).map (fun (i : Nat) => 1.0 :: cols.map (fun (c : List Float) => c.getD i 0.0)); "
    "let ym := md s 3 6; let rr := md s 51 n; "
    "let yl : List Float := (List.range n).map (fun (i : Nat) => "
    "(match ym with | 0 => Float.ofNat (md s (200 + i) 2) | 1 => 1.0 | 2 => 0.0 "
    "| 3 => (if i == rr then 2.0 else Float.ofNat (md s (200 + i) 2)) | 4 => Float.ofNat (i % 2) "
    "| _ => (if md s (200 + i) 5 == 0 then 1.0 else 0.0) : Float)); "
    "let shape := md s 4 4; let constpd := md s 5 4 == 0; let cp := PDP.getD (md s 6 12) 0.5; "
    "let pdl : List Float := (List.range n).map (fun (i : Nat) => "
    "if constpd then cp else if md s (300 + i) 25 == 0 then (if md s (350 + i) 2 == 0 then 0.0 else 1.0) "
    "else PDP.getD (md s (300 + i) 12) 0.5); "
    "let bl : List Float := (List.range (nv + 1)).map (fun (j : Nat) => BP.getD (md s (400 + j) 10) 0.0); "
    'let f : LogisticFit Float := { names := ["Intercept"], beta := Np.NDArray.d1 bl, cov := Np.NDArray.d2 [], loglik := 0.0, n_iter := 0, converged := true }; '
    "(match shape with "
    "| 0 => classification_table (α := Float) invG solveG dotS mmS mvS esS l1S (Np.NDArray.d1 yl) (Np.NDArray.d2 xl) none (some (Np.NDArray.d1 pdl)) "
    "| 1 => classification_table (α := Float) invG solveG dotS mmS mvS esS l1S (Np.NDArray.d2 xl) (Np.NDArray.d1 yl) (some (Sum.inr (Np.NDArray.d1 pdl))) none "
    "| 2 => classification_table (α := Float) invG solveG dotS mmS mvS esS l1S (Np.NDArray.d1 yl) (Np.NDArray.d2 xl) (some (Sum.inl f)) none "
    "| _ => classification_table (α := Float) invG solveG dotS mmS mvS esS l1S (Np.NDArray.d1 yl) (Np.NDArray.d2 xl) (some (Sum.inl f)) (some (Np.NDArray.d1 pdl)) : Pl.Frame Float); "
)


def text(lo, n):
    return f"({LETS}(List.range {n}).flatMap (fun (k : Nat) => dg_frame (CT ({lo} + k))))"


CH = 20


def skips(lo, n):
    out = []
    for sd in range(lo, lo + n):
        r = run(sd)
        if r[1] is not None or r[2][0] == "outside":
            out.append(sd)
    return out


def text_chunks(lo, n):
    """chunk digests: n/CH numbers, each the digest of the per-case digests of the chunk's seeds without the seeds Python raises on"""
    sk = skips(lo, n)
    return (f"({LETS}let SK : List Nat := {sk}; let cd := fun (s : Nat) => ((dg_frame (CT s)).headD 0).toNat.toUInt64; "
            f"(List.range {n // CH}).map (fun (c : Nat) => zz_e_dg ((List.range {CH}).filterMap "
            f"(fun (k : Nat) => let s := {lo} + c * {CH} + k; if SK.contains s then none else some (cd s)))))")


def run_lit(y, x, pd):
    """pd keyword call on literal data -> (digest or None, h list or None, lone flag list)"""
    global MOD
    if MOD is None:
        MOD = load_module()
    CAP.clear()
    try:
        with np.errstate(all="ignore"):
            df = MOD["classification_table"](np.array(y, dtype=np.float64), np.array(x, dtype=np.float64).reshape(len(y), -1), pd=np.array(pd, dtype=np.float64))
    except Exception:  # noqa: BLE001
        return None, None
    return dg(tokens_of(df)), [bool(t) for t in CAP["lone"]], [float(t) for t in CAP["h"]]


def near_cases():
    """Designs [1, e_r, eps * z] (z a small integer column): row r has leverage 1 up to eps; eps is bisected (on the float
    bit pattern) so that 1 - h of row r is on either side of the port's threshold 1e-8, then +-1..3 ulps around the flip."""
    out = []
    pdv = [0.5, 0.25, 0.75, 0.3, 0.7, 0.02, 0.98, 0.125, 0.875]
    for d in range(8):
        n = 4 + d % 5
        r = (d * 3) % n
        z = [float(md(900 + d, 70 + i, 5)) - 2.0 for i in range(n)]
        z[r] = 1.0 if z[r] == 0.0 else z[r]
        u = [float(md(900 + d, 60 + i, 3)) - 1.0 for i in range(n)]
        u[(r + 1) % n] = 1.0
        y = [float(md(900 + d, 80 + i, 2)) for i in range(n)]
        y[0], y[-1] = 1.0, 0.0
        pd = [pdv[md(900 + d, 90 + i, len(pdv))] for i in range(n)]

        def mk(eps):
            return [[1.0, 1.0 if i == r else eps * u[i], z[i]] for i in range(n)]

        def lone_r(eps):
            dgst, lone, h = run_lit(y, mk(eps), pd)
            return None if dgst is None else (lone[r], 1.0 - h[r])
        lo_b, hi_b = bits(1e-7), bits(1e-1)  # eps small -> 1 - h small -> lone
        a = lone_r(fromb(lo_b)); b = lone_r(fromb(hi_b))
        if a is None or b is None or not a[0] or b[0]:
            continue
        while hi_b - lo_b > 1:
            mid = (lo_b + hi_b) // 2
            m = lone_r(fromb(mid))
            if m is None:
                break
            if m[0]:
                lo_b = mid
            else:
                hi_b = mid
        for off in (-1, 0, 1, 2):
            eps = fromb(lo_b + off)
            res = lone_r(eps)
            if res is None:
                continue
            out.append((y, mk(eps), pd, res[0], res[1]))
    return out


def near_text():
    cs = near_cases()
    items = ", ".join(f"({lf_(y)}, {'[' + ', '.join(lf_(r) for r in x) + ']'}, {lf_(pd)})" for y, x, pd, _, _ in cs)
    exp = [run_lit(y, x, pd)[0] for y, x, pd, _, _ in cs]
    (WORK / "fz5_cte_near.expected.json").write_text(json.dumps({"digests": exp, "lone": [c[3] for c in cs], "omh": [c[4] for c in cs]}))
    return (f"({LETS}let NC : List (List Float \u00d7 List (List Float) \u00d7 List Float) := [{items}]; "
            "NC.flatMap (fun (c : List Float \u00d7 List (List Float) \u00d7 List Float) => dg_frame (classification_table (\u03b1 := Float) invG solveG dotS mmS mvS esS l1S "
            "(Np.NDArray.d1 c.1) (Np.NDArray.d2 c.2.1) none (some (Np.NDArray.d1 c.2.2)))))").replace("\\u00d7", "×").replace("\\u03b1", "α").replace("\u00d7", "×").replace("\u03b1", "α")


def main():
    mode = sys.argv[1]
    if mode == "near":
        print(near_text())
        return
    if mode == "text":
        print(text(int(sys.argv[2]), int(sys.argv[3])))
    elif mode == "ctext":
        print(text_chunks(int(sys.argv[2]), int(sys.argv[3])))
    elif mode == "otext":
        lo, n = int(sys.argv[2]), int(sys.argv[3])
        sd = [t for t in range(lo, lo + n) if run(t)[1] is None and run(t)[2][0] == "outside"]
        print(f"({LETS}let SD : List Nat := {sd}; SD.flatMap (fun (s : Nat) => dg_frame (CT s)))")
        (WORK / f"fz5_cte_outside_{lo}_{n}.expected.json").write_text(json.dumps([[t, run(t)[0], run(t)[2][1]] for t in sd]))
    elif mode == "ccmp":
        lo, n = int(sys.argv[2]), int(sys.argv[3])
        got = json.loads(Path(sys.argv[4]).read_text())
        assert len(got) == n // CH, (len(got), n // CH)
        bad = []
        for c in range(n // CH):
            ds = []
            for sd in range(lo + c * CH, lo + (c + 1) * CH):
                r = run(sd)
                if r[1] is None and r[2][0] == "inside":
                    ds.append(r[0])
            if dg(ds) != got[c]:
                bad.append(lo + c * CH)
        print("chunks", n // CH, "differing chunks", len(bad), [f"seeds {b}..{b + CH - 1}" for b in bad])
    elif mode == "run":
        lo, n = int(sys.argv[2]), int(sys.argv[3])
        out = []
        from collections import Counter
        cnt = Counter()
        for s in range(lo, lo + n):
            d, ex, tag, df, c = run(s)
            if ex:
                out.append({"seed": s, "digest": None, "raises": ex})
                cnt["raises " + ex] += 1
            else:
                out.append({"seed": s, "digest": d, "pre": tag[0], "tags": tag[1], "shape": c["shape"], "k": c["nv"] + 1, "rows": len(df)})
                cnt["returns " + tag[0]] += 1
                for t in tag[1]:
                    cnt["tag " + t] += 1
        (WORK / f"fz5_cte_{lo}_{n}.expected.json").write_text(json.dumps(out))
        print(sorted(cnt.items()))
    elif mode == "cmp":
        lo, n = int(sys.argv[2]), int(sys.argv[3])
        exp = json.loads((WORK / f"fz5_cte_{lo}_{n}.expected.json").read_text())
        got = json.loads(Path(sys.argv[4]).read_text())
        assert len(got) == n, (len(got), n)
        bad = cmpd = 0
        for e, g in zip(exp, got):
            if e["digest"] is None:
                continue
            cmpd += 1
            if e["digest"] != g:
                bad += 1
                print("DIFF seed", e["seed"], e["pre"], e["tags"], "shape", e["shape"], "k", e["k"])
        print("compared", cmpd, "differences", bad, "python raises (not compared)", sum(e["digest"] is None for e in exp))
    elif mode == "show":
        s = int(sys.argv[2])
        d, ex, tag, df, c = run(s)
        print(c)
        print(ex, tag)
        if df is not None:
            print(df)
        print(text(s, 1) if "-t" in sys.argv else "")


if __name__ == "__main__":
    main()
