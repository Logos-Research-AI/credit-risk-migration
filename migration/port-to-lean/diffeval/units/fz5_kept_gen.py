"""Fuzz of def:_kept (and def:_kept_precond), fifth port diff (2026-11-18), a non-author. Carrier:
Np.cumsumInt on item def:_kept (blueprint 5365851c-5549-44b7-9207-4bd4c422031d). Nothing is changed on the
blueprint.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz5_kept_gen.py \
      --text B N            print the Lean input term for seeds B..B+N-1 (one eval_decl input)
      --run B N [outfile]   print/save the Python side for the same seeds (JSON list of per-seed kept lists)
      --cmp B N leanfile    compare: leanfile holds the cumsum output line of the input for B..B+N-1

Case of seed s (built INSIDE Lean from hsh, mirrored here): a square matrix n x n, n = 0..5, in one of 7 modes
  0 symmetric from edge pools (diagonal pool DG with 0, -0, NaN, inf, denormal, 1e-9 ...; off-diagonal pool OF)
  1 X'X of a small integer matrix X (r rows 0..6, columns sometimes duplicates of the previous one)
  2 the same with each column scaled (1000, 1e-3, 1, 1e5, 3)
  3 threshold: diagonal D, entry (0,1) = D * (sqrt(1 - 1e-9) + k ulp), k = -3..3, rest 0 (second pivot at 1e-9 * D)
  4 asymmetric from the same pools
  5 rank one d * u_i * u_j
  6 diagonal d, off-diagonal d * r (r = 1 - k ulp)
NOTE: the inputs actually sent are rendered from the Python mirror (`--inputs B N`) as literal matrices, because
eval_decl takes one case per input and the carrier items of earlier fuzz runs are not on the blueprint (no item may be
added); `--text` (generator inside Lean) is kept but was not used. The stand-in solve of the inputs sent is
x_i = (b_i - rowsum_i) / a_ii (row sum sequential from 0.0), dot = sequential from 0.0; mode 3 is tuned to it:
2nd pivot = D - b (b - D) / D, b = D * (t0 + k ulp), k = -3..3, t0 = (1 + sqrt(5 - 4e-9)) / 2 (pivot = 1e-9 D).
Routines are stand-ins written identically on both sides (same as fz3_s03_gen): solve = Gaussian elimination with
partial pivoting, no raise; dot = sequential sum from 0.0. On the Python side the REAL sas_compat._kept runs with
np.linalg.solve patched and `a` an ndarray subclass whose 1-D @ 1-D is the sequential dot.
Class: zero_pivot = the stand-in solve met an exactly zero pivot (the real np.linalg.solve would raise LinAlgError).
"""
from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import kit  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

M64 = (1 << 64) - 1
hsh = kit.hsh
NAN, INF = float("nan"), float("inf")


def bits(x):
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def flt(b):
    return struct.unpack("<d", struct.pack("<Q", b & M64))[0]


R0 = bits((1.0 + math.sqrt(5.0 - 4e-9)) / 2.0)  # b/D with D - b (b - D)/D = 1e-9 D (the stand-in solve, 1 x 1 block)
DG = [0.0, -0.0, 1.0, -1.0, 1e300, 1e-300, NAN, INF, -INF, 5e-324, 0.5, 1e-9, 2e-9, 1e-10, 1e-8, 1e9, 2.0]
OF = [0.0, -0.0, 1.0, -1.0, 0.5, 1e-8, NAN, 1e300, -1e300, 1e-9, 5e-324, INF, 1e-10]
DP = [1.0, 1000.0, 1e-5, 3.0, 1e150, 1e-150, 1e-9]
SCP = [1000.0, 0.001, 1.0, 100000.0, 3.0]
UP = [1.0, -1.0, 2.0, 0.5, 1e-3, 1e3, 3.0, 0.0]
D4P = [1.0, 2.0, 0.5, 1e-8, 4.0, 1e-5]
DLP = [1.0, 1 - 2.0**-53, 1 - 2.0**-52, 1 - 2.0**-51, 1 - 1e-9, 0.5, -1.0, 1 - 2.0**-50, math.sqrt(1 - 1e-9), 1 - 1e-8]
POOLS = dict(DG=DG, OF=OF, DP=DP, SCP=SCP, UP=UP, D4P=D4P, DLP=DLP)


def u64(xs):
    return "[" + ", ".join(hex(bits(x)) for x in xs) + "]"


def fpick(E, u):
    return E[(u >> 20) % len(E)]


def rnd(u, eh):
    b = (u & 0x8000000000000000) | (((1023 - eh + (u >> 52) % (2 * eh + 1)) * 0x10000000000000) & M64) | (u & 0xFFFFFFFFFFFFF)
    return flt(b)


def gen(E, pe, eh, s, k):
    u = hsh(s, k)
    return fpick(E, u) if (u >> 8) % 100 < pe else rnd(u, eh)


def mk(s):
    n = hsh(s, 0) % 6
    mode = hsh(s, 1) % 7
    r = hsh(s, 2) % 7

    def col(c):
        return c - 1 if c > 0 and hsh(s, 50 + c) % 3 == 0 else c

    def xv(t, c):
        return float(hsh(s, 100 + t * 8 + col(c)) % 5) - 2.0

    def xs(t, c):
        return xv(t, c) * fpick(SCP, hsh(s, 70 + c)) if mode == 2 else xv(t, c)

    def gram(i, j):
        acc = 0.0
        for t in range(r):
            acc = acc + xs(t, i) * xs(t, j)
        return acc

    D = fpick(DP, hsh(s, 3))
    d4 = fpick(D4P, hsh(s, 3))

    def ent(i, j):
        a, b = min(i, j), max(i, j)
        if mode == 0:
            return gen(DG, 60, 8, s, 10 + i) if i == j else gen(OF, 60, 8, s, 30 + a * 8 + b)
        if mode in (1, 2):
            return gram(i, j)
        if mode == 3:
            if i == j:
                return D
            if a == 0 and b == 1:
                return D * flt((R0 - 3 + hsh(s, 4) % 7) & M64)
            return 0.0
        if mode == 4:
            return gen(DG, 60, 8, s, 10 + i) if i == j else gen(OF, 60, 8, s, 200 + i * 8 + j)
        if mode == 5:
            return d4 * fpick(UP, hsh(s, 80 + i)) * fpick(UP, hsh(s, 80 + j))
        return d4 if i == j else d4 * fpick(DLP, hsh(s, 5))

    return [[ent(i, j) for j in range(n)] for i in range(n)]


# ---- Python side: the real sas_compat._kept
FLAG = {"zero_pivot": False}


class NA(np.ndarray):
    def __matmul__(self, o):
        a, b = np.asarray(self), np.asarray(o)
        assert a.ndim == 1 and b.ndim == 1, (a.shape, b.shape)
        acc = 0.0
        for k in range(a.shape[0]):
            acc += a[k] * b[k]
        return np.float64(acc)


def na(a):
    return np.asarray(a, dtype=np.float64).view(NA)


def solve_sa(a, b):
    """stand-in: x_i = (b_i - rowsum_i(a)) / a_ii, the row sum added sequentially from 0.0; no raise"""
    a = [[float(v) for v in r] for r in np.asarray(a)]
    b = [float(v) for v in np.asarray(b)]
    out = []
    with np.errstate(all="ignore"):
        for i in range(len(b)):
            acc = 0.0
            for v in a[i]:
                acc = float(np.float64(acc) + np.float64(v))
            den = np.float64(a[i][i])
            if den == 0.0:
                FLAG["zero_pivot"] = True
            out.append(float((np.float64(b[i]) - np.float64(acc)) / den))
    return na(np.array(out, dtype=np.float64))


def py_kept(s):
    m = mk(s)
    n = len(m)
    arr = np.zeros((n, n), dtype=np.float64)
    for i in range(n):
        for j in range(n):
            arr[i, j] = m[i][j]
    FLAG["zero_pivot"] = False
    o = np.linalg.solve
    np.linalg.solve = solve_sa
    try:
        with np.errstate(all="ignore"):
            k = sc._kept(arr.view(NA))  # pyright: ignore[reportPrivateUsage]
    finally:
        np.linalg.solve = o
    return k, FLAG["zero_pivot"], m


# ---- Lean text
SOLVE = (
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
)
GENL = (
    "let fpick := fun (E : List UInt64) (u : UInt64) => Float.ofBits (E.getD ((u >>> 20) % E.length.toUInt64).toNat 0); "
    "let rnd := fun (u : UInt64) (eh : UInt64) => let k : UInt64 := u >>> 52; Float.ofBits ((u &&& 0x8000000000000000) ||| ((1023 - eh + k % (2 * eh + 1)) * 0x10000000000000) ||| (u &&& 0xFFFFFFFFFFFFF)); "
    "let gen := fun (E : List UInt64) (pe eh : UInt64) (s k : Nat) => let u := hsh s k; if (u >>> 8) % 100 < pe then fpick E u else rnd u eh; "
)
MKL = (
    f"let R0 : UInt64 := {hex(R0)}; "
    "let mk := fun (s : Nat) => (let n := ((hsh s 0) % 6).toNat; let mode := ((hsh s 1) % 7).toNat; let r := ((hsh s 2) % 7).toNat; "
    "let col := fun (c : Nat) => if c > 0 && (hsh s (50 + c)) % 3 == 0 then c - 1 else c; "
    "let xv := fun (t c : Nat) => Float.ofNat ((hsh s (100 + t * 8 + col c)) % 5).toNat - 2.0; "
    "let xs := fun (t c : Nat) => if mode == 2 then xv t c * fpick SCP (hsh s (70 + c)) else xv t c; "
    "let gram := fun (i j : Nat) => (List.range r).foldl (fun (acc : Float) (t : Nat) => acc + xs t i * xs t j) 0.0; "
    "let D := fpick DP (hsh s 3); let d4 := fpick D4P (hsh s 3); "
    "let ent := fun (i j : Nat) => (let a := min i j; let b := max i j; "
    "if mode == 0 then (if i == j then gen DG 60 8 s (10 + i) else gen OF 60 8 s (30 + a * 8 + b)) "
    "else if mode == 1 || mode == 2 then gram i j "
    "else if mode == 3 then (if i == j then D else if a == 0 && b == 1 then D * Float.ofBits (R0 - 3 + (hsh s 4) % 7) else 0.0) "
    "else if mode == 4 then (if i == j then gen DG 60 8 s (10 + i) else gen OF 60 8 s (200 + i * 8 + j)) "
    "else if mode == 5 then d4 * fpick UP (hsh s (80 + i)) * fpick UP (hsh s (80 + j)) "
    "else (if i == j then d4 else d4 * fpick DLP (hsh s 5))); "
    "(List.range n).map (fun (i : Nat) => (List.range n).map (fun (j : Nat) => ent i j))); "
)
PRE = (
    kit.GEN.split("let gF")[0]
    + "".join(f"let {k} : List UInt64 := {u64(v)}; " for k, v in POOLS.items())
    + GENL + SOLVE + MKL
)


def lean_text(B, N):
    return (
        "(" + PRE + f"(List.range {N}).flatMap (fun (i : Nat) => let s := {B} + i; "
        "let k := _kept solve dot (Np.NDArray.d2 (mk s)); (k.length : Int) :: k) : List Int)"
    )


def lit(x):
    if math.isnan(x):
        return "(0.0/0.0)"
    if math.isinf(x):
        return "(1.0/0.0)" if x > 0 else "(-1.0/0.0)"
    if x == 0.0:
        return "0.0" if math.copysign(1.0, x) > 0 else "(-0.0)"
    if abs(x) < 2.3e-308:
        return f"(Float.ofBits {hex(bits(x))})"
    r = repr(x)
    if "e" not in r and "." not in r:
        r += ".0"
    if "e" in r and "." not in r.split("e")[0]:
        m, e = r.split("e")
        r = m + ".0e" + e
    if "e" in r:
        m, e = r.split("e")
        r = m + "e" + str(int(e))
    return f"({r})" if x < 0 else r


S_L = (
    "(fun (x : List (List Float)) (b : List Float) => b.mapIdx fun i v => (v - (x.getD i []).foldl (fun s w => s + w) 0.0) / (x.getD i []).getD i 1.0)"
)
D_L = "(fun (u v : List Float) => (u.zip v).foldl (fun s p => s + p.1 * p.2) 0.0)"


def lean_input(s):
    m = mk(s)
    return S_L + " " + D_L + " (Np.NDArray.d2 [" + ",".join("[" + ",".join(lit(v) for v in r) + "]" for r in m) + "])"


def py_flat(B, N):
    out, per = [], []
    for s in range(B, B + N):
        k, zp, m = py_kept(s)
        per.append((s, k, zp, m))
        out += [len(k)] + k
    return out, per


def main():
    mode, B, N = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    if mode == "--inputs2":
        print("\n".join(lean_input(x) for x in range(B, B + N) if len(mk(x)) >= 2))
    elif mode == "--run2":
        print(json.dumps([py_kept(x)[0] for x in range(B, B + N) if len(mk(x)) >= 2]))
    elif mode == "--inputs":
        print(json.dumps([lean_input(x) for x in range(B, B + N)]))
    elif mode == "--text":
        print(lean_text(B, N))
    elif mode == "--run":
        out, per = py_flat(B, N)
        print(json.dumps(out))
    elif mode == "--cmp":
        line = Path(sys.argv[4]).read_text().strip()
        got = json.loads(line)
        lean, acc = [], 0
        for d in got:
            lean.append(d - acc)
            acc = d
        out, per = py_flat(B, N)
        # split per seed
        i = 0
        diffs = 0
        zp_n = 0
        for s, k, zp, m in per:
            ln = lean[i]
            lk = lean[i + 1 : i + 1 + ln]
            i += 1 + ln
            if zp:
                zp_n += 1
            if lk != k:
                diffs += 1
                print("DIFF seed", s, "py", k, "lean", lk, "zero_pivot", zp, "m", m)
        print(f"seeds {N} diffs {diffs} zero_pivot {zp_n}")


if __name__ == "__main__":
    main()
