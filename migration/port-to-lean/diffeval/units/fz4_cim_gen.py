"""Fuzz of def:classification_is_made (revision 2e1c913f...) and def:classification_is_made_precond (9292c39f...),
by a non-author, blueprint 5365851c-....

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz4_cim_gen.py [N] [real]

Input of seed s is built INSIDE Lean (one term, no local Lean file) and mirrored here with integer hashing (kit.hsh):
  k = ncols in 0..5, n rows in {0,1,2,3,4,6,8}; design mode hsh(s,3)%8:
    0 every cell from the edge pool (null-free: NaN, +-inf, +-0, 1, 1 +- ulp, 1e-300, 5e-324, 0.5, 1e300, 98)
    1 random floats (30% edge pool)         2 columns that are exact multiples (1, 2, -3, 0.5) of one base column (ties, duplicates, zero rows)
    3 col0 = 1, col j = 1 + d*(+-1 by row parity), d near sqrt(1e-9) (the pivot threshold, +-1..3 ulp), 0, 1e-8, 1e-5, 1e-4, 2^-52
    4 zero columns / small ints               5 col0 = 1, small ints in [-2, 2]
    6 as 3 with col j >= 1 multiplied by 1000 (7) random floats of exponent +-40 with 20% edge pool
  fit: names "Intercept", "x1", ...; len(names) = k + {0,0,0,0,1,1,2,-1} (longer or shorter than ncols), a duplicate name "x1"
  at the last position in 1/6 of the seeds with >= 3 names; cov square of side len(names) (+1 in 1/5), diagonal 0 / 1 by one of
  six patterns (none, random subset, last only, all slopes, intercept only, pool 0.0 -0.0 NaN 1e-300 5e-324 1 -1 inf).
Routines (standing in for numpy, both sides): solve = Gaussian elimination with partial pivoting (first strict max of |.|),
matmul / dot = sequential sums from 0.0 in index order. A seed on which the stand-in solve meets an exactly zero pivot
(real np.linalg.solve raises LinAlgError: outside the model, RULEBOOK 3) is REJECTED and not sent to Lean.
Expected: the real sas_compat.classification_is_made with np.linalg.solve replaced by the stand-in and x.T @ x by the
sequential product. A second run (arg 'real') uses real numpy, to report where the stand-in and numpy disagree.
Lean side: ONE Bool per input: classification_is_made is evaluated on a dummy whose result is `ncols = 1`; ncols is the term
`if all seeds agree with the packed expected bits then 1 else 0` (the dummy's result is true iff ncols = 1).
"""
from __future__ import annotations

import json
import math
import struct
import sys
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[3] / "port"))
import kit  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

nx = math.nextafter
nan, inf = float("nan"), float("inf")
M64 = (1 << 64) - 1
hsh = kit.hsh


def fb(x):
    return 0x7FF8000000000000 if x != x else struct.unpack("<Q", struct.pack("<d", x))[0]


def bf(b):
    return struct.unpack("<d", struct.pack("<Q", b))[0]


R = math.sqrt(1e-9)
EX = [nan, inf, -inf, 0.0, -0.0, 1.0, nx(1.0, 2), nx(1.0, 0), 1e-300, 5e-324, 0.5, 1e300, 98.0, -1.0]
DL = [0.0, 1e-8, 1e-5, 1e-4, 2.0**-52, R, nx(R, 1), nx(R, 0), nx(nx(R, 1), 1), nx(nx(R, 0), 0),
      nx(nx(nx(R, 1), 1), 1), nx(nx(nx(R, 0), 0), 0), 5e-5, 3.2e-5, 3.1e-5]
CD = [0.0, -0.0, nan, 1e-300, 5e-324, 1.0, 0.0, -1.0, inf]
SC = [1.0, 2.0, -3.0, 0.5]


def pick(L, u):
    return L[(u >> 20) % len(L)]


def rnd(u, eh):
    b = (u & 0x8000000000000000) | (((1023 - eh + (u >> 52) % (2 * eh + 1)) << 52) & M64) | (u & 0xFFFFFFFFFFFFF)
    return bf(b)


def entry(s, mode, i, j):
    u = hsh(s, 1000 + i * 8 + j)
    sgn = 1.0 if i % 2 == 0 else -1.0
    if mode == 0:
        return pick(EX, u)
    if mode == 1:
        return pick(EX, u) if (u >> 8) % 100 < 30 else rnd(u, 3)
    if mode == 2:
        b = hsh(s, 500 + i)
        bv = 0.0 if b % 4 == 0 else float(((b >> 20) % 5) + 1)
        return SC[hsh(s, 600 + j) % 4] * bv
    if mode == 3:
        return 1.0 if j == 0 else 1.0 + pick(DL, hsh(s, 700 + j)) * sgn
    if mode == 4:
        return 0.0 if hsh(s, 800 + j) % 3 == 0 else float((u >> 20) % 4)
    if mode == 5:
        return 1.0 if j == 0 else float(((u >> 20) % 5) - 2)
    if mode == 6:
        return 1.0 if j == 0 else 1000.0 * (1.0 + pick(DL, hsh(s, 700 + j)) * sgn)
    return pick(EX, u) if (u >> 8) % 100 < 20 else rnd(u, 40)


def seed_input(s):
    k = [0, 1, 2, 3, 4, 5][hsh(s, 1) % 6]
    n = [0, 1, 2, 3, 4, 6, 8][hsh(s, 2) % 7]
    mode = hsh(s, 3) % 8
    rows = [[entry(s, mode, i, j) for j in range(k)] for i in range(n)]
    dn = [0, 0, 0, 0, 1, 1, 2, -1][hsh(s, 4) % 8]
    nn = max(0, k + dn)
    dup = hsh(s, 5) % 6 == 0 and nn >= 3
    names = ["Intercept" if j == 0 else "x1" if (dup and j == nn - 1) else f"x{j}" for j in range(nn)]
    cs = nn + (1 if hsh(s, 6) % 5 == 0 else 0)
    zm = hsh(s, 20) % 6

    def dv(i):
        if i >= nn:
            return 1.0
        if zm == 0:
            return 1.0
        if zm == 1:
            return 0.0 if hsh(s, 30 + i) % 2 == 0 else 1.0
        if zm == 2:
            return 0.0 if i + 1 == nn else 1.0
        if zm == 3:
            return 0.0 if i >= 1 else 1.0
        if zm == 4:
            return 0.0 if i == 0 else 1.0
        return pick(CD, hsh(s, 40 + i))

    cov = [[dv(i) if i == j else 0.5 for j in range(cs)] for i in range(cs)]
    return k, n, mode, rows, names, cov, zm


# ---- stand-in routines
FLAG = {"zero_pivot": False}


class NA(np.ndarray):
    def __matmul__(self, o):
        a, b = np.asarray(self), np.asarray(o)
        if a.ndim == 2 and b.ndim == 2:
            r = np.zeros((a.shape[0], b.shape[1]))
            for i in range(a.shape[0]):
                for j in range(b.shape[1]):
                    acc = 0.0
                    for k in range(a.shape[1]):
                        acc += a[i, k] * b[k, j]
                    r[i, j] = acc
            return r.view(NA)
        assert a.ndim == 1 and b.ndim == 1
        acc = 0.0
        for k in range(a.shape[0]):
            acc += a[k] * b[k]
        return np.float64(acc)


def na(a):
    return np.asarray(a, dtype=np.float64).view(NA)


def solve_sa(a, b):
    a = [[float(v) for v in r] for r in np.asarray(a)]
    n = len(a)
    b = [float(v) for v in np.asarray(b)]
    M = [a[i] + [b[i]] for i in range(n)]
    with np.errstate(all="ignore"):
        for k in range(n):
            p, best = k, abs(M[k][k])
            for i in range(k + 1, n):
                if abs(M[i][k]) > best:
                    p, best = i, abs(M[i][k])
            M[k], M[p] = M[p], M[k]
            if M[k][k] == 0.0:
                FLAG["zero_pivot"] = True
            for i in range(k + 1, n):
                f = np.float64(M[i][k]) / np.float64(M[k][k])
                for j in range(k, n + 1):
                    M[i][j] = float(np.float64(M[i][j]) - f * np.float64(M[k][j]))
        x = [0.0] * n
        for i in range(n - 1, -1, -1):
            s = M[i][n]
            for j in range(i + 1, n):
                s = float(np.float64(s) - np.float64(M[i][j]) * np.float64(x[j]))
            x[i] = float(np.float64(s) / np.float64(M[i][i]))
    return na(np.array(x, dtype=np.float64))


def run(inp, real):
    k, n, mode, rows, names, cov, zm = inp
    x = np.array(rows, dtype=np.float64).reshape(n, k)
    fit = sc.LogisticFit(names=names, beta=np.zeros(0), cov=np.array(cov, dtype=np.float64).reshape(len(cov), len(cov)),
                         loglik=0.0, n_iter=0, converged=True)
    if real:
        try:
            with np.errstate(all="ignore"):
                return bool(sc.classification_is_made(fit, x)), None
        except Exception as e:  # noqa: BLE001
            return None, f"{type(e).__name__}: {e}"
    FLAG["zero_pivot"] = False
    o = np.linalg.solve
    np.linalg.solve = solve_sa
    try:
        with np.errstate(all="ignore"):
            r = bool(sc.classification_is_made(fit, na(x)))
    except Exception as e:  # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"
    finally:
        np.linalg.solve = o
    if FLAG["zero_pivot"]:
        return None, "zero pivot (LinAlgError of real numpy)"
    return r, None


def u64(xs):
    return "[" + ", ".join(hex(fb(x)) for x in xs) + "]"


LEAN = (
    kit.GEN.split("let gF")[0]
    + f"let EXB : List UInt64 := {u64(EX)}; let DLB : List UInt64 := {u64(DL)}; let CDB : List UInt64 := {u64(CD)}; let SCB : List UInt64 := {u64(SC)}; "
    "let pick := fun (L : List UInt64) (u : UInt64) => Float.ofBits (L.getD ((u >>> 20) % L.length.toUInt64).toNat 0); "
    "let rnd := fun (u : UInt64) (eh : UInt64) => let k : UInt64 := u >>> 52; Float.ofBits ((u &&& 0x8000000000000000) ||| ((1023 - eh + k % (2 * eh + 1)) * 0x10000000000000) ||| (u &&& 0xFFFFFFFFFFFFF)); "
    "let entry := fun (s mode i j : Nat) => let u := hsh s (1000 + i * 8 + j); let sgn : Float := if i % 2 == 0 then 1.0 else -1.0; "
    "if mode = 0 then pick EXB u "
    "else if mode = 1 then (if (u >>> 8) % 100 < 30 then pick EXB u else rnd u 3) "
    "else if mode = 2 then (let b := hsh s (500 + i); let bv : Float := if b % 4 == 0 then 0.0 else Float.ofNat (((b >>> 20) % 5).toNat + 1); Float.ofBits (SCB.getD ((hsh s (600 + j) % 4).toNat) 0) * bv) "
    "else if mode = 3 then (if j = 0 then 1.0 else 1.0 + pick DLB (hsh s (700 + j)) * sgn) "
    "else if mode = 4 then (if hsh s (800 + j) % 3 == 0 then 0.0 else Float.ofNat (((u >>> 20) % 4).toNat)) "
    "else if mode = 5 then (if j = 0 then 1.0 else Float.ofInt ((((u >>> 20) % 5).toNat : Int) - 2)) "
    "else if mode = 6 then (if j = 0 then 1.0 else 1000.0 * (1.0 + pick DLB (hsh s (700 + j)) * sgn)) "
    "else (if (u >>> 8) % 100 < 20 then pick EXB u else rnd u 40); "
    # stand-in routines
    "let solve := fun (a : List (List Float)) (b : List Float) => (let n := a.length; "
    "let M0 : Array (Array Float) := (a.zip b).toArray.map (fun (p : List Float × Float) => p.1.toArray.push p.2); "
    "let M := (List.range n).foldl (fun (M : Array (Array Float)) (k : Nat) => "
    "let pb := (List.range n).foldl (fun (pb : Nat × Float) (i : Nat) => if k < i && ((M[i]!)[k]!).abs > pb.2 then (i, ((M[i]!)[k]!).abs) else pb) (k, ((M[k]!)[k]!).abs); "
    "let Mk := M[k]!; let Mp := M[pb.1]!; let M1 := (M.set! k Mp).set! pb.1 Mk; "
    "(List.range n).foldl (fun (Mm : Array (Array Float)) (i : Nat) => if k < i then "
    "(let f := (Mm[i]!)[k]! / (Mm[k]!)[k]!; Mm.set! i ((Mm[i]!).toList.mapIdx (fun (j : Nat) (x : Float) => if k ≤ j then x - f * (Mm[k]!)[j]! else x)).toArray) else Mm) M1) M0; "
    "((List.range n).reverse.foldl (fun (x : Array Float) (i : Nat) => "
    "let s := (List.range n).foldl (fun (acc : Float) (j : Nat) => if i < j then acc - (M[i]!)[j]! * x[j]! else acc) (M[i]!)[n]!; "
    "x.set! i (s / (M[i]!)[i]!)) (List.replicate n 0.0).toArray).toList : List Float); "
    "let dot := fun (a b : List Float) => (List.range a.length).foldl (fun (acc : Float) (k : Nat) => acc + a.getD k 0.0 * b.getD k 0.0) 0.0; "
    "let matmul := fun (a b : List (List Float)) => a.map (fun (r : List Float) => (List.range a.length).map (fun (j : Nat) => "
    "(List.range r.length).foldl (fun (acc : Float) (k : Nat) => acc + r.getD k 0.0 * (b.getD k []).getD j 0.0) 0.0)); "
    "let one := fun (s : Nat) => ("
    "let k : Nat := [0, 1, 2, 3, 4, 5].getD ((hsh s 1 % 6).toNat) 0; "
    "let n : Nat := [0, 1, 2, 3, 4, 6, 8].getD ((hsh s 2 % 7).toNat) 0; "
    "let mode : Nat := (hsh s 3 % 8).toNat; "
    "let rows : List (List Float) := (List.range n).map (fun (i : Nat) => (List.range k).map (fun (j : Nat) => entry s mode i j)); "
    "let dn : Int := [0, 0, 0, 0, 1, 1, 2, -1].getD ((hsh s 4 % 8).toNat) 0; "
    "let nn : Nat := ((k : Int) + dn).toNat; "
    "let dup : Bool := hsh s 5 % 6 == 0 && decide (3 ≤ nn); "
    "let names : List String := (List.range nn).map (fun (j : Nat) => if j == 0 then \"Intercept\" else if dup && j + 1 == nn then \"x1\" else \"x\" ++ toString j); "
    "let cs : Nat := nn + (if hsh s 6 % 5 == 0 then 1 else 0); "
    "let zm : Nat := (hsh s 20 % 6).toNat; "
    "let dv := fun (i : Nat) => if i ≥ nn then (1.0 : Float) else if zm = 0 then 1.0 "
    "else if zm = 1 then (if hsh s (30 + i) % 2 == 0 then 0.0 else 1.0) "
    "else if zm = 2 then (if i + 1 == nn then 0.0 else 1.0) "
    "else if zm = 3 then (if i ≥ 1 then 0.0 else 1.0) "
    "else if zm = 4 then (if i == 0 then 0.0 else 1.0) else pick CDB (hsh s (40 + i)); "
    "let cov : List (List Float) := (List.range cs).map (fun (i : Nat) => (List.range cs).map (fun (j : Nat) => if i == j then dv i else 0.5)); "
    "classification_is_made solve matmul dot "
    "({ names := names, beta := Np.NDArray.d1 [], cov := Np.NDArray.d2 cov, loglik := 0.0, n_iter := 0, converged := true } : LogisticFit Float) "
    "(Np.NDArray.d2 rows) (k : Int)); "
)

DUMMY = ("(fun (a : List (List Float)) (b : List Float) => ([] : List Float)) "
         "(fun (a b : List (List Float)) => a.map (fun (r : List Float) => (List.range a.length).map (fun (_ : Nat) => (0.0 : Float)))) "
         "(fun (a b : List Float) => (0.0 : Float)) "
         "({ names := [\"Intercept\"], beta := Np.NDArray.d1 [], cov := Np.NDArray.d2 [[0.0]], loglik := 0.0, n_iter := 0, converged := true } : LogisticFit Float) "
         "(Np.NDArray.d2 [])")


def term(lo, hi, bits, rej, flip=None):
    """lo..hi: seeds; bits: dict seed -> bool expected."""
    E = 0
    for s in range(lo, hi):
        if bits.get(s):
            E |= 1 << (s - lo)
    if flip is not None:
        E ^= 1 << (flip - lo)
    rj = "[" + ", ".join(str(s) for s in rej if lo <= s < hi) + "]"
    return (DUMMY + " (" + LEAN.rstrip() +
            f" let E : Nat := {hex(E)}; let REJ : List Nat := {rj}; "
            f"if (List.range {hi - lo}).all (fun (t : Nat) => REJ.contains (t + {lo}) || (one (t + {lo}) == Nat.testBit E t)) then (1 : Int) else 0)")


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 2300
    real = "real" in sys.argv
    exp, rej, cov, why = {}, [], Counter(), Counter()
    for s in range(N):
        inp = seed_input(s)
        r, err = run(inp, real)
        if err:
            rej.append(s)
            why[err.split(":")[0]] += 1
            continue
        exp[s] = r
        k, n, mode, rows, names, cv, zm = inp
        cov["true"] += r
        cov["false"] += not r
        cov[f"mode{mode}/{r}"] += 1
        cov[f"zm{zm}/{r}"] += 1
        cov["n0"] += n == 0
        cov["n1"] += n == 1
        cov["k0"] += k == 0
        cov["names_gt_ncols"] += len(names) > k
        cov["names_lt_ncols"] += len(names) < k
        cov["dup_name"] += len(set(names)) < len(names)
        cov["cov_bigger"] += len(cv) > len(names)
        cov["nan_in_x"] += any(v != v for r_ in rows for v in r_)
        cov["inf_in_x"] += any(abs(v) == inf for r_ in rows for v in r_)
    out = {"N": N, "kept": len(exp), "rejected": rej, "why": dict(why), "coverage": dict(cov), "real": real,
           "true_seeds": [s for s, v in exp.items() if v]}
    tag = "real" if real else "standin"
    (HERE.parent / "work" / f"fz4_cim_{tag}.json").write_text(json.dumps(out))
    print(json.dumps({k: v for k, v in out.items() if k not in ("rejected", "true_seeds")}, indent=1, sort_keys=True))
    print("rejected", rej[:40], len(rej))
    if not real:
        (HERE.parent / "work" / "fz4_cim_term_all.txt").write_text(term(0, N, exp, rej))
        (HERE.parent / "work" / "fz4_cim_term_flip.txt").write_text(term(0, N, exp, rej, flip=min(exp)))
        print("term len", len(term(0, N, exp, rej)))


if __name__ == "__main__":
    main()
