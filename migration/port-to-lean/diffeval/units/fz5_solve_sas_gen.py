"""Fuzz of def:_solve_sas (NEW, fifth port diff, 2026-11-18) and def:_solve_sas_precond, by a non-author.
Nothing is changed on the blueprint. Blueprint 5365851c-5549-44b7-9207-4bd4c422031d.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz5_solve_sas_gen.py \
      START COUNT          writes work/fz5_solve_sas_<START>.txt (the eval_decl input) and prints stats
      --one SEED           prints the case of one seed (matrices, kept, both results) for diagnosis
      --one-text SEED      the eval_decl input printing the 6-decimal result of one seed (both solvers)

No carrier item is used: the loop over seeds runs INSIDE the `solve` argument of one call on item def:_solve_sas:
`_solve_sas solve0 dot0 (.d2 [[1.0]]) (.d1 [0.0])` takes the plain path on a 1x1 matrix and calls solve0 once;
solve0 ignores its arguments and, for each seed, builds a matrix and vector from hsh (mirrored here), calls
`_solve_sas` itself (twice: solver A and solver B) and returns, per chunk of 10 seeds, 0.0 when the chunk digest
equals the expected one embedded in the input, else the digest mod 2^52 (a Float of an integer below 2^52 prints
exactly).

Parameters of the Lean (written identically on both sides; numpy patched on the Python side while the REAL
sas_compat._solve_sas and _kept run):
  solver A  Gaussian elimination, partial pivoting, no raise (as fz3_s03_gen.solve_sa)
  solver B  returns [ (mx H j) % 16 as float | j < n ], H the digest of (n, all entries of a, b) as bits: checks that
            the right sub-matrix and sub-vector reach solve, whatever _kept decided
  dot       sequential sum from 0.0 (c @ x is replaced by it on the Python side through an ndarray subclass)
Digest of one result vector: dg(len :: bits) (NaN canonical) mod 2^52; chunk digest = fold of mx over the per-seed
digests (A then B).

Seed s: n = hsh s 0 % 7 (0..6), mode = hsh s 1 % 8, a n x n, g of length n. Precondition (def:_solve_sas_precond:
a square 2-D, g 1-D of length n; singularity unconstrained) holds by construction for every seed: all are kept.
Modes: 0 dense (12% edge pool, else random exponent +-6); 1 Gram of a random B with 15% zero entries; 2 rank one
x x^T; 3 diag d, off-diagonals d*r, r = sqrt(1-1e-9) +- 3 ulp; 4 block [[1,o],[o,o*o/(1-1e-9) +- 3 ulp]] then
positive diagonal (pivot of index 1 at the threshold); 5 diagonal from the edge pool (0, -0, NaN, +-inf, +-1,
+-1e-9 and one ulp either side, 1e-300, 5e-324, 1e300, 2, 0.5); 6 dense, all entries from the edge pool; 7 all
entries equal. g: 35% edge pool, else random exponent +-6.
"""
from __future__ import annotations

import math
import struct
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
from credit_risk import sas_compat as sc  # noqa: E402

M64 = (1 << 64) - 1
NANB = 0x7FF8000000000000
OFF = 14695981039346656037


def b2f(b):
    return struct.unpack("<d", struct.pack("<Q", b & M64))[0]


def f2b(x):
    if x != x:
        return NANB
    return struct.unpack("<Q", struct.pack("<d", float(x)))[0]


def hsh(s, i):
    z = (s * 0x9E3779B97F4A7C15 + i * 0xD1B54A32D192ED03 + 1) & M64
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & M64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & M64
    return z ^ (z >> 31)


def mx(h, x):
    g = ((h ^ x) * 1099511628211) & M64
    return g ^ (g >> 32)


def dgl(toks):
    h = OFF
    for t in toks:
        h = mx(h, t)
    return h


R0 = math.sqrt(1 - 1e-9)


def ulpk(x, k):
    return b2f(f2b(x) + k)


PBITS = [0x0, 0x8000000000000000, NANB, 0x7FF0000000000000, 0xFFF0000000000000, 0x3FF0000000000000, 0xBFF0000000000000,
         f2b(1e-9), f2b(-1e-9), f2b(ulpk(1e-9, 1)), f2b(ulpk(1e-9, -1)), f2b(1e-300), 0x1, f2b(1e300), f2b(2.0), f2b(0.5)]
P = [b2f(b) for b in PBITS]
DDP = [1.0, 1000.0, 0.001, 3.0]


def pf(u):
    return P[(u >> 20) % len(P)]


def rnd(u, eh):
    k = u >> 52
    return b2f((u & 0x8000000000000000) | (((1023 - eh + k % (2 * eh + 1)) * 0x10000000000000) & M64) | (u & 0xFFFFFFFFFFFFF))


def mk(s):
    n = hsh(s, 0) % 7
    m = hsh(s, 1) % 8
    kd = hsh(s, 5) % 7 - 3
    dd = DDP[hsh(s, 7) % 4]

    def X(t):
        u = hsh(s, 400 + t)
        return 0.0 if (u >> 8) % 100 < 10 else rnd(u, 3)

    def B(k, i):
        u = hsh(s, 200 + k * 8 + i)
        return 0.0 if (u >> 8) % 100 < 15 else rnd(u, 3)

    o = abs(rnd(hsh(s, 8), 3))
    cu = hsh(s, 9)
    cc = pf(cu) if cu % 2 == 0 else rnd(cu, 3)

    def entry(i, j):
        if m == 0:
            u = hsh(s, 100 + i * 8 + j)
            return pf(u) if (u >> 8) % 100 < 12 else rnd(u, 6)
        if m == 1:
            acc = 0.0
            for k in range(n):
                acc = acc + B(k, i) * B(k, j)
            return acc
        if m == 2:
            return X(i) * X(j)
        if m == 3:
            return dd if i == j else dd * ulpk(R0, kd)
        if m == 4:
            if i == 0 and j == 0:
                return 1.0
            if (i == 0 and j == 1) or (i == 1 and j == 0):
                return o
            if i == 1 and j == 1:
                return ulpk(o * o / (1.0 - 1e-9), kd)
            if i == j:
                return abs(rnd(hsh(s, 500 + i), 3))
            return 0.0
        if m == 5:
            return pf(hsh(s, 600 + i)) if i == j else 0.0
        if m == 6:
            return pf(hsh(s, 100 + i * 8 + j))
        return cc

    a = [[entry(i, j) for j in range(n)] for i in range(n)]
    g = []
    for i in range(n):
        u = hsh(s, 300 + i)
        g.append(pf(u) if (u >> 8) % 100 < 35 else rnd(u, 6))
    return n, m, a, g


class NA(np.ndarray):
    def __matmul__(self, o):
        a, b = np.asarray(self), np.asarray(o)
        assert a.ndim == 1 and b.ndim == 1
        acc = 0.0
        for k in range(a.shape[0]):
            acc += a[k] * b[k]
        return np.float64(acc)


def na(x):
    return np.asarray(x, dtype=np.float64).view(NA)


def solve_A(a, b):
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


def solve_B(a, b):
    a = np.asarray(a)
    b = np.asarray(b)
    toks = [len(a)] + [f2b(v) for r in a for v in r] + [f2b(v) for v in b]
    H = dgl(toks)
    return na(np.array([float(mx(H, j) % 16) for j in range(len(a))], dtype=np.float64))


def run_real(solver, a, g):
    o = np.linalg.solve
    np.linalg.solve = solver
    try:
        n = len(a)
        A = np.array(a, dtype=np.float64).reshape(n, n).view(NA)
        G = np.array(g, dtype=np.float64).view(NA)
        with np.errstate(all="ignore"):
            return [float(v) for v in sc._solve_sas(A, G)], [int(i) for i in sc._kept(A)]
    finally:
        np.linalg.solve = o


def rd(r):
    return dgl([len(r)] + [f2b(x) for x in r]) % (1 << 52)


def seed_digests(s):
    n, m, a, g = mk(s)
    ra, ka = run_real(solve_A, a, g)
    rb, kb = run_real(solve_B, a, g)
    return [rd(ra), rd(rb)], (n, m, ka, kb, ra, rb)


def chunk_digests(start, count):
    out = []
    for c in range(count // 10):
        h = OFF
        for i in range(10):
            ds, _ = seed_digests(start + c * 10 + i)
            for d in ds:
                h = mx(h, d)
        out.append(h)
    return out


LEAN_BODY = (
    "let hsh := fun (s i : Nat) => let z : UInt64 := s.toUInt64 * 0x9E3779B97F4A7C15 + i.toUInt64 * 0xD1B54A32D192ED03 + 1; "
    "let z := (z ^^^ (z >>> 30)) * 0xBF58476D1CE4E5B9; let z := (z ^^^ (z >>> 27)) * 0x94D049BB133111EB; z ^^^ (z >>> 31); "
    "let mx := fun (h x : UInt64) => let g := (h ^^^ x) * 1099511628211; g ^^^ (g >>> 32); "
    "let P : List UInt64 := [" + ", ".join(hex(b) for b in PBITS) + "]; "
    "let pf := fun (u : UInt64) => Float.ofBits (P.getD ((u >>> 20) % P.length.toUInt64).toNat 0); "
    "let rnd := fun (u eh : UInt64) => let k : UInt64 := u >>> 52; "
    "Float.ofBits ((u &&& 0x8000000000000000) ||| ((1023 - eh + k % (2 * eh + 1)) * 0x10000000000000) ||| (u &&& 0xFFFFFFFFFFFFF)); "
    "let ulpk := fun (x : Float) (k : Int) => Float.ofBits (Int.toNat ((x.toBits.toNat : Int) + k)).toUInt64; "
    "let dot0 := fun (a b : List Float) => (List.range a.length).foldl (fun (acc : Float) (k : Nat) => acc + a.getD k 0.0 * b.getD k 0.0) 0.0; "
    "let solA := fun (a : List (List Float)) (b : List Float) => (let n := a.length; "
    "let M0 : Array (Array Float) := (a.zip b).toArray.map (fun (p : List Float × Float) => p.1.toArray.push p.2); "
    "let M := (List.range n).foldl (fun (M : Array (Array Float)) (k : Nat) => "
    "let pb := (List.range n).foldl (fun (pb : Nat × Float) (i : Nat) => if k < i && ((M[i]!)[k]!).abs > pb.2 then (i, ((M[i]!)[k]!).abs) else pb) (k, ((M[k]!)[k]!).abs); "
    "let Mk := M[k]!; let Mp := M[pb.1]!; let M1 := (M.set! k Mp).set! pb.1 Mk; "
    "(List.range n).foldl (fun (Mm : Array (Array Float)) (i : Nat) => if k < i then "
    "(let f := (Mm[i]!)[k]! / (Mm[k]!)[k]!; Mm.set! i ((Mm[i]!).toList.mapIdx (fun (j : Nat) (x : Float) => if k ≤ j then x - f * (Mm[k]!)[j]! else x)).toArray) else Mm) M1) M0; "
    "((List.range n).reverse.foldl (fun (x : Array Float) (i : Nat) => "
    "let s := (List.range n).foldl (fun (acc : Float) (j : Nat) => if i < j then acc - (M[i]!)[j]! * x[j]! else acc) (M[i]!)[n]!; "
    "x.set! i (s / (M[i]!)[i]!)) (List.replicate n 0.0).toArray).toList : List Float); "
    "let solB := fun (a : List (List Float)) (b : List Float) => "
    "(let H : UInt64 := (a.length.toUInt64 :: ((a.flatten ++ b).map Float.toBits)).foldl mx 14695981039346656037; "
    "(List.range a.length).map (fun (j : Nat) => Float.ofNat ((mx H j.toUInt64).toNat % 16))); "
    "let rd := fun (r : List Float) => (((r.length.toUInt64 :: r.map Float.toBits).foldl mx 14695981039346656037).toNat % 4503599627370496).toUInt64; "
    "let mkA := fun (s : Nat) => "
    "let n := (hsh s 0 % 7).toNat; let m := (hsh s 1 % 8).toNat; let kd : Int := ((hsh s 5 % 7).toNat : Int) - 3; "
    "let dd : Float := [1.0, 1000.0, 0.001, 3.0].getD (hsh s 7 % 4).toNat 1.0; "
    "let X := fun (t : Nat) => let u := hsh s (400 + t); if (u >>> 8) % 100 < 10 then 0.0 else rnd u 3; "
    "let Bm := fun (k i : Nat) => let u := hsh s (200 + k * 8 + i); if (u >>> 8) % 100 < 15 then 0.0 else rnd u 3; "
    "let o : Float := (rnd (hsh s 8) 3).abs; let cu := hsh s 9; let cc : Float := if cu % 2 == 0 then pf cu else rnd cu 3; "
    "let entry := fun (i j : Nat) => "
    "if m == 0 then (let u := hsh s (100 + i * 8 + j); if (u >>> 8) % 100 < 12 then pf u else rnd u 6) "
    "else if m == 1 then (List.range n).foldl (fun (acc : Float) (k : Nat) => acc + Bm k i * Bm k j) 0.0 "
    "else if m == 2 then X i * X j "
    "else if m == 3 then (if i == j then dd else dd * ulpk (Float.ofBits " + hex(f2b(R0)) + ") kd) "
    "else if m == 4 then (if i == 0 && j == 0 then 1.0 else if (i == 0 && j == 1) || (i == 1 && j == 0) then o "
    "else if i == 1 && j == 1 then ulpk (o * o / (1.0 - 1e-9)) kd else if i == j then (rnd (hsh s (500 + i)) 3).abs else 0.0) "
    "else if m == 5 then (if i == j then pf (hsh s (600 + i)) else 0.0) "
    "else if m == 6 then pf (hsh s (100 + i * 8 + j)) else cc; "
    "let a : List (List Float) := (List.range n).map (fun (i : Nat) => (List.range n).map (fun (j : Nat) => entry i j)); "
    "let g : List Float := (List.range n).map (fun (i : Nat) => let u := hsh s (300 + i); if (u >>> 8) % 100 < 35 then pf u else rnd u 6); "
    "(a, g); "
    "let seedR := fun (s : Nat) => let ag := mkA s; "
    "[_solve_sas (α := Float) solA dot0 (Np.NDArray.d2 ag.1) (Np.NDArray.d1 ag.2), "
    "_solve_sas (α := Float) solB dot0 (Np.NDArray.d2 ag.1) (Np.NDArray.d1 ag.2)]; "
    "let seedD := fun (s : Nat) => (seedR s).map rd; "
)


def lean_input(start, count):
    exp = chunk_digests(start, count)
    e = "[" + ", ".join(str(x) for x in exp) + "]"
    body = (
        f"let EXP : List UInt64 := {e}; "
        f"(List.range {count // 10}).map (fun (c : Nat) => "
        f"let h : UInt64 := ((List.range 10).flatMap (fun (i : Nat) => seedD ({start} + c * 10 + i))).foldl mx 14695981039346656037; "
        "if h == EXP.getD c 0 then 0.0 else Float.ofNat (h.toNat % 4503599627370496))"
    )
    return _wrap(body), exp


def _wrap(body):
    solve0 = "(fun (_ : List (List Float)) (_ : List Float) => " + LEAN_BODY + body + ")"
    return "(α := Float) " + solve0 + " (fun (_ _ : List Float) => 0.0) (Np.NDArray.d2 [[1.0]]) (Np.NDArray.d1 [0.0])"


def one_text(s):
    # per-seed: the matrix size, the digests, and the 6-decimal results of A then B, separated by -1.0
    body = (f"(((seedD {s}).map (fun (d : UInt64) => Float.ofNat d.toNat)) ++ [-1.0] ++ ((seedR {s}).flatMap (fun (r : List Float) => r ++ [-2.0])))")
    return _wrap(body)


def stats(start, count):
    st = dict(total=0, plain=0, partial=0, partial_empty=0, n0=0, n1=0, kept_diff_AB=0, nan_or_inf_out=0)
    modes = [0] * 8
    for s in range(start, start + count):
        _, (n, m, ka, kb, ra, rb) = seed_digests(s)
        st["total"] += 1
        modes[m] += 1
        st["n0"] += n == 0
        st["n1"] += n == 1
        if len(ka) == n:
            st["plain"] += 1
        else:
            st["partial"] += 1
            st["partial_empty"] += not ka
        st["kept_diff_AB"] += ka != kb
        st["nan_or_inf_out"] += any(not math.isfinite(x) for x in ra)
    return st, modes


if __name__ == "__main__":
    if sys.argv[1] == "--one":
        s = int(sys.argv[2])
        n, m, a, g = mk(s)
        print("n", n, "mode", m)
        for r in a:
            print([repr(x) for x in r])
        print("g", g)
        _, (n, m, ka, kb, ra, rb) = seed_digests(s)
        print("kept A", ka, "kept B", kb)
        print("A", ra)
        print("B", rb)
        print("digests", seed_digests(s)[0])
    elif sys.argv[1] == "--one-text":
        print(one_text(int(sys.argv[2])))
    else:
        start, count = int(sys.argv[1]), int(sys.argv[2])
        text, exp = lean_input(start, count)
        out = HERE.parent / "work" / f"fz5_solve_sas_{start}.txt"
        out.write_text(text)
        print(len(text), "chars ->", out)
        print(stats(start, count))
