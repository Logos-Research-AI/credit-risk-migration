"""Fuzz of def:_inv_sas (sas_compat.py:801-811), by the fuzzer who did not write it.
  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz5_inv_sas_gen.py sweep LO HI
      -> prints the eval_decl input (item def:_inv_sas, decl _inv_sas) for seeds LO..HI-1, writes
         work/fz5_inv_sas_LO_HI.expected.json (per-case 32-bit digest of the result)
  ... case S   -> the input for one seed with the matrix and the result at 6 decimals; the real Python result on stderr
Library routines (solve, inv, dot) are doubles written once in Lean and once here: Gauss elimination with
partial pivoting; inv by solving the unit columns; dot sequential, (p0+p2)+(p1+p3) for 4 terms (numpy's order
for <= 4 terms; checked against numpy on every call). Python runs the REAL sas_compat._inv_sas with
np.linalg.solve / np.linalg.inv replaced by the doubles. The sweep runs inside Lean: the outer call is
_inv_sas on [[1.0]] (everything kept) whose inv double returns the list of digests of all the cases.
"""
import sys, json, struct
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import kit
from credit_risk import sas_compat as sc

M64 = (1 << 64) - 1
NAN = float("nan"); INF = float("inf")
f64 = np.float64
def fromb(b): return struct.unpack("<d", struct.pack("<Q", b))[0]
def tob(x): return 0x7FF8000000000000 if x != x else struct.unpack("<Q", struct.pack("<d", float(x)))[0]

def solveG(A, b):
    n = len(A)
    M = [[f64(v) for v in A[i]] + [f64(b[i])] for i in range(n)]
    for k in range(n):
        best = k
        for r in range(n):
            if k <= r and abs(M[r][k]) > abs(M[best][k]): best = r
        Ms = [M[best] if r == k else (M[k] if r == best else M[r]) for r in range(n)]
        pr = Ms[k]; out = []
        for r in range(n):
            if k < r:
                row = Ms[r]; f = row[k] / pr[k]
                out.append([row[c] - f * pr[c] for c in range(n + 1)])
            else: out.append(Ms[r])
        M = out
    xs = []
    for t in range(n):
        i = n - 1 - t; row = M[i]; s = f64(0.0)
        for q in range(len(xs)): s = s + row[i + 1 + q] * xs[q]
        xs = [(row[n] - s) / row[i]] + xs
    return xs

def invG(A):
    n = len(A)
    cols = [solveG(A, [1.0 if i == j else 0.0 for i in range(n)]) for j in range(n)]
    return [[cols[j][i] for j in range(n)] for i in range(n)]

def dotG(c, x):
    p = [f64(c[i]) * f64(x[i]) for i in range(len(c))]
    if len(p) == 4: return (p[0] + p[2]) + (p[1] + p[3])
    s = f64(0.0)
    for v in p: s = s + v
    return s

hsh, gF = kit.hsh, kit.gF
def md(s, k, m): return hsh(s, k) % m
E1 = [0.0, -0.0, 1.0, -1.0, NAN, INF, -INF, None, 1e-300, 1e300, 1e-9, 0.5, 2.0]
E2 = [0.0, 1.0, -1.0, 2.0, 0.5, 3.0, -2.0, 4.0]
E3 = [0.0, -0.0, 1.0, -1.0, NAN, INF, -INF, fromb(2020), 1e308, fromb(1), 1e-9, -1e-9]
E4 = [1.0, 2.0, 0.5, 0.0, -1.0, 1e-9, 1e-10, 1e9, NAN, INF, 4.0]
E5 = [1.0, -1.0, 2.0, 0.5, 0.0]
D = [3.0517578125e-05, 6.103515625e-05, 1.52587890625e-05, 1e-4, 1e-5, 4e-5, 3e-5, 2.5e-5, 5e-5, 3.2e-5]
def un(l): return [NAN if v is None else v for v in l]
def rowsof(n, f): return [[f[i * n + j] for j in range(n)] for i in range(n)]
def gram(n, r, X):
    out = []
    for p in range(n):
        row = []
        for q in range(n):
            s = f64(0.0)
            for t in range(r): s = s + f64(X[t][p]) * f64(X[t][q])
            row.append(s)
        out.append(row)
    return out
def genCase(s):
    n = md(s, 1, 6); fam = md(s, 2, 7)
    if n == 0: return []
    if fam == 0: return rowsof(n, un(gF(s, n * n, 30, 6, E1)))
    if fam == 1:
        r = md(s, 3, 6) + 1; flat = un(gF(s, r * n, 35, 3, E2))
        i = md(s, 5, n); j = md(s, 6, n); dup = md(s, 4, 4)
        def cell(t, c):
            if c == j:
                if dup == 0: return flat[t * n + i]
                if dup == 1: return 0.0
                if dup == 2: return 2.0 * flat[t * n + i]
            return flat[t * n + c]
        return gram(n, r, [[cell(t, c) for c in range(n)] for t in range(r)])
    if fam == 6:
        r = md(s, 3, 6) + 2; flat = un(gF(s, r * n, 40, 2, E5))
        i = md(s, 5, n); j = md(s, 6, n); d = D[md(s, 4, len(D))]
        def cell(t, c):
            if c == j: return f64(flat[t * n + i]) + f64(d)
            return flat[t * n + c]
        return gram(n, r, [[cell(t, c) for c in range(n)] for t in range(r)])
    if fam == 2:
        n2 = 2 if n < 2 else n; m = 4503597 + md(s, 3, 5); C = f64(1.0) + f64(float(m)) * f64(2.220446049250313e-16)
        i = md(s, 4, n2); j = (i + 1 + md(s, 5, n2 - 1)) % n2; p = min(i, j); q = max(i, j)
        def c_(a, b):
            if a == p and b == p: return 1.0
            if a == q and b == q: return C
            if (a == p and b == q) or (a == q and b == p): return 1.0
            return 4.0 if a == b else 0.0
        return [[c_(a, b) for b in range(n2)] for a in range(n2)]
    if fam == 3: return [[E3[md(s, 3, len(E3))]]]
    if fam == 4:
        kind = md(s, 3, 5); v = E3[md(s, 4, len(E3))]
        def c_(a, b):
            if kind == 0: return 0.0
            if kind == 1: return 1.0 if a == b else 0.0
            if kind == 2: return 1.0
            if kind == 3: return NAN
            return v
        return [[c_(a, b) for b in range(n)] for a in range(n)]
    def c_(a, b):
        if a == b: return E4[md(s, 20 + a, len(E4))]
        o = md(s, 100 + min(a, b) * 8 + max(a, b), 3)
        return 0.0 if o == 0 else (1.0 if o == 1 else -1.0)
    return [[c_(a, b) for b in range(n)] for a in range(n)]

def dg(toks):
    h = 14695981039346656037
    for x in toks:
        g = ((h ^ x) * 1099511628211) & M64
        h = g ^ (g >> 32)
    return h
def toks(rows): return [len(rows)] + [t for r in rows for t in [len(r)] + [tob(v) for v in r]]

calls = {"dots": 0, "dotbad": 0}
def run_py(rows):
    n = len(rows)
    a = np.array(rows, dtype=np.float64).reshape(n, n) if n else np.zeros((0, 0))
    o_s, o_i = np.linalg.solve, np.linalg.inv
    def ws(A, b):
        A = np.asarray(A); b = np.asarray(b)
        x = solveG(A.tolist(), b.tolist())
        xa = np.array([float(v) for v in x], dtype=np.float64)
        if b.ndim == 1 and len(b) > 0:
            calls["dots"] += 1
            u, v = float(b @ xa), float(dotG(b.tolist(), x))
            if not (tob(u) == tob(v) or (u == 0.0 and v == 0.0)): calls["dotbad"] += 1
        return xa
    def wi(A):
        m = invG(np.asarray(A).tolist()); k = len(m)
        return np.array(m, dtype=np.float64).reshape(k, k)
    np.linalg.solve, np.linalg.inv = ws, wi
    try:
        with np.errstate(all="ignore"):
            res = sc._inv_sas(a)
    finally:
        np.linalg.solve, np.linalg.inv = o_s, o_i
    return res.tolist()

def lit(v):
    if v is None: return "none"
    if v != v: return "nan"
    if v == INF: return "inf"
    if v == -INF: return "(-inf)"
    if v == 0.0: return "(-0.0)" if str(v) == "-0.0" else "0.0"
    if 0 < abs(v) < 2.3e-308: return f"(Float.ofBits {tob(v)})"
    r = repr(abs(v)).replace("e+", "e")
    return r if v > 0 else f"(-{r})"
def lo_(l): return "[" + ", ".join("none" if v is None else f"(some {lit(v)})" for v in l) + "]"
def lf_(l): return "[" + ", ".join(lit(v) for v in l) + "]"

LETS = (
 "let nan : Float := 0.0 / 0.0; let inf : Float := 1.0 / 0.0; "
 + kit.GEN.split("let gI")[0] +
 "let mx := fun (h x : UInt64) => let g := (h ^^^ x) * 1099511628211; g ^^^ (g >>> 32); "
 "let dg := fun (t : List UInt64) => t.foldl mx 14695981039346656037; "
 "let md := fun (s k m : Nat) => ((hsh s k) % m.toUInt64).toNat; "
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
 "let dotG := fun (c x : List Float) => let p := (List.range c.length).map (fun (i : Nat) => c.getD i nan * x.getD i nan); "
 "if p.length == 4 then ((p.getD 0 nan + p.getD 2 nan) + (p.getD 1 nan + p.getD 3 nan)) else p.foldl (fun (s : Float) (v : Float) => s + v) 0.0; "
 f"let E1 : List (Option Float) := {lo_(E1)}; "
 f"let E2 : List (Option Float) := {lo_(E2)}; "
 f"let E3 : List Float := {lf_(E3)}; "
 f"let E4 : List Float := {lf_(E4)}; "
 f"let E5 : List (Option Float) := {lo_(E5)}; "
 f"let D : List Float := {lf_(D)}; "
 "let un := fun (l : List (Option Float)) => l.map (fun (o : Option Float) => o.getD nan); "
 "let rowsof := fun (n : Nat) (f : List Float) => (List.range n).map (fun (i : Nat) => (List.range n).map (fun (j : Nat) => f.getD (i * n + j) nan)); "
 "let gram := fun (n r : Nat) (X : List (List Float)) => (List.range n).map (fun (p : Nat) => (List.range n).map (fun (q : Nat) => "
 "(List.range r).foldl (fun (s : Float) (t : Nat) => s + (X.getD t []).getD p nan * (X.getD t []).getD q nan) 0.0)); "
 "let genCase := fun (s : Nat) => let n := md s 1 6; let fam := md s 2 7; "
 "if n == 0 then ([] : List (List Float)) else "
 "if fam == 0 then rowsof n (un (gF s (n * n) 30 6 E1)) else "
 "if fam == 1 then (let r := md s 3 6 + 1; let flat := un (gF s (r * n) 35 3 E2); let i := md s 5 n; let j := md s 6 n; let dup := md s 4 4; "
 "gram n r ((List.range r).map (fun (t : Nat) => (List.range n).map (fun (c : Nat) => if c == j then (if dup == 0 then flat.getD (t * n + i) nan else if dup == 1 then 0.0 else if dup == 2 then 2.0 * flat.getD (t * n + i) nan else flat.getD (t * n + c) nan) else flat.getD (t * n + c) nan)))) else "
 "if fam == 6 then (let r := md s 3 6 + 2; let flat := un (gF s (r * n) 40 2 E5); let i := md s 5 n; let j := md s 6 n; let d := D.getD (md s 4 D.length) nan; "
 "gram n r ((List.range r).map (fun (t : Nat) => (List.range n).map (fun (c : Nat) => if c == j then flat.getD (t * n + i) nan + d else flat.getD (t * n + c) nan)))) else "
 "if fam == 2 then (let n2 := if n < 2 then 2 else n; let m := 4503597 + md s 3 5; let C := 1.0 + Float.ofNat m * 2.220446049250313e-16; "
 "let i := md s 4 n2; let j := (i + 1 + md s 5 (n2 - 1)) % n2; let p := min i j; let q := max i j; "
 "(List.range n2).map (fun (a : Nat) => (List.range n2).map (fun (b : Nat) => if a == p && b == p then 1.0 else if a == q && b == q then C else if (a == p && b == q) || (a == q && b == p) then 1.0 else if a == b then 4.0 else 0.0))) else "
 "if fam == 3 then [[E3.getD (md s 3 E3.length) nan]] else "
 "if fam == 4 then (let kind := md s 3 5; let v := E3.getD (md s 4 E3.length) nan; "
 "(List.range n).map (fun (a : Nat) => (List.range n).map (fun (b : Nat) => if kind == 0 then 0.0 else if kind == 1 then (if a == b then 1.0 else 0.0) else if kind == 2 then 1.0 else if kind == 3 then nan else v))) else "
 "(List.range n).map (fun (a : Nat) => (List.range n).map (fun (b : Nat) => if a == b then E4.getD (md s (20 + a) E4.length) nan else "
 "(let o := md s (100 + (min a b) * 8 + max a b) 3; if o == 0 then 0.0 else if o == 1 then 1.0 else -1.0))); "
)
TAIL = " (fun (_ : List (List Float)) (b : List Float) => b) (fun (_ _ : List Float) => (0.0 : Float)) (Np.NDArray.d2 [[1.0]])"

def main():
    mode = sys.argv[1]
    if mode == "sweep":
        lo, hi = int(sys.argv[2]), int(sys.argv[3])
        exp = [dg(toks(run_py(genCase(s)))) % (1 << 32) for s in range(lo, hi)]
        (HERE.parent / "work" / f"fz5_inv_sas_{lo}_{hi}.expected.json").write_text(json.dumps(exp))
        print("numpy dot vs double:", calls, file=sys.stderr)
        sweep = (f"(List.range {hi - lo}).map (fun (k : Nat) => [Float.ofNat ((dg (let res := _inv_sas invG solveG dotG (Np.NDArray.d2 (genCase ({lo} + k))); "
                 "res.length.toUInt64 :: res.flatMap (fun (r : List Float) => r.length.toUInt64 :: r.map Float.toBits))).toNat % 4294967296)])")
        print("(fun (_ : List (List Float)) => " + LETS + sweep + ")" + TAIL)
    elif mode == "stats":
        lo, hi = int(sys.argv[2]), int(sys.argv[3]); from collections import Counter
        c = Counter()
        for s in range(lo, hi):
            rows = genCase(s); n = len(rows)
            if n == 0: c["empty"] += 1; continue
            a = np.array(rows, dtype=np.float64)
            o_s = np.linalg.solve
            np.linalg.solve = lambda A, b: np.array([float(v) for v in solveG(np.asarray(A).tolist(), np.asarray(b).tolist())])
            with np.errstate(all="ignore"): k = sc._kept(a)
            np.linalg.solve = o_s
            c["all kept" if len(k) == n else ("none kept" if not k else "partial")] += 1
            c[f"n={n}"] += 1
            c[f"fam{md(s, 2, 7)} " + ("all" if len(k) == n else "left-out")] += 1
        print(sorted(c.items()))
    elif mode == "case":
        s = int(sys.argv[2])
        print("(fun (_ : List (List Float)) => " + LETS + f"genCase {s} ++ _inv_sas invG solveG dotG (Np.NDArray.d2 (genCase {s})))" + TAIL)
        rows = genCase(s); print("rows", rows, file=sys.stderr); print("py", run_py(rows), file=sys.stderr)
main()
