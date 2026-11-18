"""Fuzz of def:hosmer_lemeshow / def:hosmer_lemeshow_precond (update 2026-11-17, third diff).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_hl_gen.py [first_seed n_seeds]
      -> diffeval/work/fz_hl.json, fz_hl.inputs.json, fz_hl.fuzz.json, fz_hl.in<k>.txt

Inputs are built INSIDE Lean from a parameter list [s, n, m, off, pe, ky, yp, kp, pp] per case (kit.gF / kit.gI
mirrored in Python, integer arithmetic only):
  y  : ky 0 f64 column drawn from pool YP[yp] ; ky 1 Int64 column gI(s+11,n,8,2,0) ; ky 2 Boolean column of it
  pd : kp 0 structured  a/100 + JJ[b] (ties within 1e-6) with probability pe% replaced by an element of EP0
       kp 1 f64 column drawn from pool PP[pp] ; kp 2 Int64 column gI(s+15,n,10,3,1)
Library parameters of the unit: chi2 is the stub x*3.0+float(df) on both sides (Python: sc.chi2_sf replaced, the
real hosmer_lemeshow run otherwise); pow2 is a lookup of the squares that differ from x*x (libm pow) over the
arguments Python squared in that eval input, x*x elsewhere. So the real Python value is compared bit for bit.

Precondition, rendered in Python from the text of def:hosmer_lemeshow_precond (function `precond`):
  y.len = pd.len, numeric dtypes: true by construction (f64 / int / bool columns of equal length);
  prep = the lines of the unit up to sizes (numpy as in the code); none -> True;
  n <= 2**52; for every group row: size != 0, isfinite(o1), floor(o1) == o1, |o1| <= 2**52,
  isfinite(o1-e1) -> x**2 finite (OverflowError = not finite), same for (size-o1)-e0.
Per case: precond true and Python returns = kept; precond true and Python raises = defect (not sent);
precond false and Python returns = rejected (sent, chunked); precond false and Python raises = dropped.
One compared value per chunk of cases: the digest of the case digests; "covers" = chunk length.
"""
from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2]))
sys.path.insert(0, str(HERE.parents[3] / "port"))

import compare as cmp  # noqa: E402
import kit  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

ITEM, DECL = "def:zz_carrier_t", "zz_carrier_t"
BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"
nan, inf = float("nan"), float("inf")
up, dn = (lambda x: math.nextafter(x, inf)), (lambda x: math.nextafter(x, -inf))
M64 = (1 << 64) - 1


def fb(x: float) -> int:
    return cmp.fbits(float(x))


# ----------------------------------------------------------------------------- pools
JJ = [0.0, 0.0, 3e-7, -4e-7, 1e-6, -1e-6, 1.2e-6, 5e-7, 9.99999e-7, 1.0000001e-6]
EP0 = [None, nan, inf, -inf, 0.0, -0.0, 1.0, 0.999999, up(0.999999), dn(0.999999), 1e-6, up(1e-6), dn(1e-6), 1e300, -1e300,
       1e-300, 5e-324, 0.5, 2.0, -1.0, 1.7976931348623157e308, 1e154, 1.4e154]
YP = [
    [0.0, 1.0, 0.0, 1.0, 0.0, 1.0, 0.0, 1.0, None],                                   # 0 clean with nulls
    [0.0, 1.0],                                                                       # 1 clean
    [0.0, 1.0, None, nan, 2.0, -1.0, 0.5, inf, -0.0, 1.0, 0.0],                        # 2 edges
    [0.0] * 7 + [1.0],                                                                # 3 few events
    [1.0] * 7 + [0.0],                                                                # 4 many events
    [0.0, 1.0, 2.0, 3.0, -1.0, 0.0, 1.0],                                             # 5 integral
    [0.5, 0.5, 1.0, 0.0, 1.5],                                                        # 6 halves
    [0.0],                                                                            # 7 all zero
    [None],                                                                           # 8 all null
    [-0.0, 0.0, 1.0, 1.0],                                                            # 9 signed zeros
]
LOW = [0.0, 1e-6, up(1e-6), dn(1e-6), 5e-7, 2e-6, 3e-6, 1e-7, 1.5e-6, 0.0, 0.0]
HIGH = [1.0, 0.999999, up(0.999999), dn(0.999999), 0.9999995, 0.99999, 1 - 1e-7, 1 - 2e-6, 1.0, 0.9999985]
PP = [
    LOW,                                                                              # 0 low end
    HIGH,                                                                             # 1 high end
    LOW + HIGH + [0.5, 0.3],                                                          # 2 both ends
    [0.25, 0.25 + 1e-6, up(0.25 + 1e-6), dn(0.25 + 1e-6), 0.25 + 2e-6, 0.25 - 1e-6, 0.3, 0.3 + 1e-6, 0.35, 0.35 + 9.99999e-7],  # 3 tie ladder
    [None, nan, inf, -inf, 0.1, 0.2, 0.7, 0.9, 0.5],                                  # 4 non-finite
    [1e300, -1e300, 1e-300, 5e-324, 1.7976931348623157e308, 0.0, 0.5, 1.0, 1e154, 1.4e154, -1.4e154],  # 5 huge, tiny
    [0.5, 0.5, 0.5, 0.25],                                                            # 6 duplicates
    [0.0, -0.0, 0.5, -0.5, 1.0],                                                      # 7 signed zeros
    [i / 20 for i in range(21)],                                                      # 8 grid
]


def lit(v) -> str:
    return "none" if v is None else f"(f {fb(v)})"


def pool_lean(name: str, pools) -> str:
    return f"let {name} : List (List (Option Float)) := [" + ", ".join("[" + ", ".join(lit(v) for v in p) + "]" for p in pools) + "]; "


LEAN_POOLS = ("let f := fun (b : UInt64) => (some (Float.ofBits b) : Option Float); "
              f"let JJ : List Float := [{', '.join(f'(Float.ofBits {fb(j)})' for j in JJ)}]; "
              "let EP0 : List (Option Float) := [" + ", ".join(lit(v) for v in EP0) + "]; "
              + pool_lean("YP", YP) + pool_lean("PP", PP))

# ----------------------------------------------------------------------------- Lean side
W = "let W := fun (t : List Int) => t.foldl (fun (h x : Int) => (h * 1099511628211 + x + 7) % 18446744073709551616) 14695981039346656037; "
OF = "let o := fun (v : Option Float) => (match v with | none => [0] | some x => [1, (x.toBits.toNat : Int)] : List Int); "
TS = "let ts := fun (s : String) => (s.length : Int) :: s.toList.map (fun (c : Char) => (c.toNat : Int)); "
TCOL = ("let tc := fun (c : Pl.Col Float) => (match c with | .f64 v => 1 :: (v.length : Int) :: v.flatMap o "
        "| .int v => 2 :: (v.length : Int) :: v.flatMap (fun (x : Option Int) => (match x with | none => [0] | some n => [1, n] : List Int)) | _ => [99] : List Int); ")
FT = "let ft := fun (fr : Pl.Frame Float) => (fr.length : Int) :: fr.flatMap (fun (p : String × Pl.Col Float) => ts p.1 ++ tc p.2); "
def rep(vals, weights):
    return [v for v, w_ in zip(vals, weights, strict=True) for _ in range(w_)]


NSL = rep([0, 1, 2, 3, 4, 5, 8, 10, 15, 20, 30, 40, 60, 100, 150, 200, 300], [3, 3, 3, 3, 3, 3, 4, 6, 6, 8, 8, 8, 8, 6, 3, 1, 1])
KYL = rep([0, 1, 2], [11, 5, 4])
YPL = rep(range(len(YP)), [10, 14, 3, 6, 6, 3, 2, 4, 1, 4])
KPL = rep([0, 1, 2], [15, 9, 1])
MML = [2, 3, 5, 8, 25, 60, 101]
PEL = [0, 0, 0, 5, 15, 40]
OFL = [5, 200, -150]


def lst(xs) -> str:
    return "[" + ", ".join(f"({x})" if x < 0 else str(x) for x in xs) + "]"


MK = (
    "let pick := fun (L : List Int) (k j : Nat) => L.getD (((hsh k j >>> 20) % L.length.toUInt64).toNat) 0; "
    f"let NSL : List Int := {lst(NSL)}; let KYL : List Int := {lst(KYL)}; let YPL : List Int := {lst(YPL)}; "
    f"let KPL : List Int := {lst(KPL)}; let MML : List Int := {lst(MML)}; let PEL : List Int := {lst(PEL)}; let OFL : List Int := {lst(OFL)}; "
    "let mk := fun (k : Nat) => "
    "let s := k; let n := (pick NSL k 0).toNat; let ky := pick KYL k 1; let yp := (pick YPL k 2).toNat; let kp := pick KPL k 3; "
    "let pp := ((hsh k 4 >>> 20) % 9).toNat; let m := (pick MML k 5).toNat; "
    "let off : Int := (if (hsh k 6 >>> 20) % 10 == 0 then pick OFL k 7 else -(Int.ofNat (((hsh k 8 >>> 20) % (Nat.max 1 (101 - m)).toUInt64).toNat))); "
    "let pe := pick PEL k 9; "
    "let m := m.toUInt64; "
    "let YI := gI (s + 11) n 8 2 0; "
    "let ycol : Pl.Col Float := (if ky == 0 then Pl.Col.f64 (gF (s + 10) n 100 0 (YP.getD yp [none])) "
    "else if ky == 1 then Pl.Col.int YI "
    "else Pl.Col.bool (YI.map (fun (q : Option Int) => q.map (fun (v : Int) => decide (v ≠ 0))))); "
    "let A := gI s n 0 m off; let B := gI (s + 1) n 0 10 0; let C := gI (s + 12) n 0 100 0; let E := gF (s + 13) n 100 0 EP0; "
    "let pcol : Pl.Col Float := (if kp == 1 then Pl.Col.f64 (gF (s + 14) n 100 0 (PP.getD pp [none])) "
    "else if kp == 2 then Pl.Col.int (gI (s + 15) n 10 3 1) "
    "else Pl.Col.f64 ((List.range n).map (fun (i : Nat) => "
    "if ((C.getD i none).getD 0) < pe then E.getD i none else "
    "(match A.getD i none, B.getD i none with | some a, some b => some (Float.ofInt a / 100.0 + JJ.getD b.toNat 0.0) | _, _ => none : Option Float)))); "
    "(ycol, pcol); "
)
CH = "let CH := fun (x : Float) (d : Int) => x * 3.0 + Float.ofInt d; "


def pow_let(pt: dict[int, int]) -> str:
    tab = "[" + ", ".join(f"({a}, {b})" for a, b in pt.items()) + "]"
    return (f"let PT : List (UInt64 × UInt64) := {tab}; "
            "let PW := fun (x : Float) => (match PT.find? (fun (t : UInt64 × UInt64) => t.1 == x.toBits) with "
            "| some t => Float.ofBits t.2 | none => x * x : Float); ")


CASE_D = ("let CD := fun (k : Nat) => let yp := mk k; let r := hosmer_lemeshow (α := Float) CH PW yp.1 yp.2; "
          "W (ft r.1 ++ o r.2.1 ++ [r.2.2.1] ++ o r.2.2.2); ")


def lean_chunks(chunks: list[list[int]]) -> str:
    return "let CS : List (List Nat) := [" + ", ".join("[" + ",".join(str(v) for v in ch) + "]" for ch in chunks) + "]; "


BODY = "CS.map (fun (ch : List Nat) => W (ch.map CD))"
BODY_CASES = "CS.flatMap (fun (ch : List Nat) => ch.map CD)"


# ----------------------------------------------------------------------------- Python side
def build(p: list[int]):
    s, n, m, off, pe, ky, yp, kp, pp = p
    YI = kit.gI(s + 11, n, 8, 2, 0)
    if ky == 0:
        yv = kit.gF(s + 10, n, 100, 0, YP[yp])
        y = pl.Series(yv, dtype=pl.Float64, nan_to_null=False)
    elif ky == 1:
        y = pl.Series(YI, dtype=pl.Int64)
    else:
        y = pl.Series([None if q is None else q != 0 for q in YI], dtype=pl.Boolean)
    if kp == 1:
        pd = pl.Series(kit.gF(s + 14, n, 100, 0, PP[pp]), dtype=pl.Float64, nan_to_null=False)
    elif kp == 2:
        pd = pl.Series(kit.gI(s + 15, n, 10, 3, 1), dtype=pl.Int64)
    else:
        A, B, C, E = kit.gI(s, n, 0, m, off), kit.gI(s + 1, n, 0, 10, 0), kit.gI(s + 12, n, 0, 100, 0), kit.gF(s + 13, n, 100, 0, EP0)
        pv = []
        for i in range(n):
            if C[i] < pe:
                pv.append(E[i])
            else:
                pv.append(float(A[i]) / 100.0 + JJ[B[i]])
        pd = pl.Series(pv, dtype=pl.Float64, nan_to_null=False)
    return y, pd


def precond(y: pl.Series, pd: pl.Series) -> bool:
    d = pl.DataFrame({"y": y.cast(pl.Float64), "p": pd.cast(pl.Float64)}).drop_nulls()
    if d.height == 0:
        return True
    p0 = np.asarray(d.get_column("p").to_numpy(), dtype=np.float64)
    y0 = np.asarray(d.get_column("y").to_numpy(), dtype=np.float64)
    o = np.argsort(p0, kind="stable")
    p, yy = p0[o], y0[o]
    n = len(p)
    if n > 2**52:
        return False
    blocks: list[int] = []
    i = 0
    while i < n:
        j = int(p.searchsorted(float(p[i]) + 1e-6, side="right"))
        blocks.append(j - i)
        i = j
    starts = np.concatenate([[0], np.cumsum(blocks)[:-1]]).astype(np.int64)
    p = np.repeat(p[starts], blocks)
    sizes = sc._hl_groups(blocks, n, 10)
    start = 0
    for size in sizes:
        if size == 0:
            return False
        o1 = float(yy[start:start + size].sum())
        e1 = size * min(max(float(p[start:start + size].sum()) / size, 1e-6), 0.999999)
        start += size
        o0, e0 = size - o1, size - e1
        if not math.isfinite(o1) or math.floor(o1) != o1 or abs(o1) > 4503599627370496.0:
            return False
        for x in (o1 - e1, o0 - e0):
            if math.isfinite(x):
                try:
                    if not math.isfinite(x ** 2):
                        return False
                except OverflowError:
                    return False
    return True


def tsr(s):
    return [len(s)] + [ord(c) for c in s]


def otok(v):
    return [0] if v is None else [1, fb(v)]


def frame_tok(df: pl.DataFrame):
    out = [df.width]
    for name in df.columns:
        c = df.get_column(name)
        out += tsr(name)
        if c.dtype == pl.Float64:
            out += [1, len(c)] + [t for v in c.to_list() for t in otok(v)]
        elif c.dtype == pl.Int64:
            out += [2, len(c)] + [t for v in c.to_list() for t in ([0] if v is None else [1, v])]
        else:
            out += [99]
    return out


def w(t) -> int:
    h = 14695981039346656037
    for x in t:
        h = (h * 1099511628211 + x + 7) % 18446744073709551616
    return h


def stub_chi2(x, df):
    return float(x) * 3.0 + float(df)


def run_py(y, pd):
    """(case digest, pow2 table entries) or raises."""
    sc.chi2_sf = stub_chi2
    table, chisq, dof, pv = sc.hosmer_lemeshow(y, pd)
    pt = {}
    for _, size, o1, e1, o0, e0 in table.iter_rows():
        for x in (float(o1) - e1, float(o0) - e0):
            try:
                sq = x ** 2
            except OverflowError:
                continue
            if fb(sq) != fb(x * x) or (sq != sq) != (x * x != x * x):
                pt[fb(x)] = fb(sq)
    if table.height > 0:
        table = table.with_columns(pl.col("EventsObserved").cast(pl.Float64), pl.col("NoneventsObserved").cast(pl.Float64))
    return w(frame_tok(table) + otok(chisq) + [dof] + otok(pv)), pt


# ----------------------------------------------------------------------------- parameters
def pick(L, k, j):
    return L[(kit.hsh(k, j) >> 20) % len(L)]


def params(k: int) -> list[int]:
    n, ky, yp, kp = pick(NSL, k, 0), pick(KYL, k, 1), pick(YPL, k, 2), pick(KPL, k, 3)
    pp = (kit.hsh(k, 4) >> 20) % 9
    m = pick(MML, k, 5)
    off = pick(OFL, k, 7) if (kit.hsh(k, 6) >> 20) % 10 == 0 else -((kit.hsh(k, 8) >> 20) % max(1, 101 - m))
    pe = pick(PEL, k, 9)
    return [k, n, m, off, pe, ky, yp, kp, pp]


def suite(first: int = 1000, count: int = 4200, chunk: int = 20, rej_chunk: int = 5, per_input: int = 140, max_rej: int = 150):
    kept, rejected, defects, dropped = [], [], [], 0
    for k in range(first, first + count):
        p = params(k)
        y, pd = build(p)
        ok = precond(y, pd)
        try:
            dg, pt = run_py(y, pd)
        except Exception as ex:  # noqa: BLE001
            if ok:
                defects.append((k, f"{type(ex).__name__}: {ex}"))
            else:
                dropped += 1
            continue
        (kept if ok else rejected).append((k, p, dg, pt))
    kept = kept[:2400]
    rejected = rejected[:max_rej]
    st = Suite("fz_hl")
    st.item, st.decl = ITEM, DECL
    # group kept chunks, rejected chunks; pack chunks into eval inputs of about per_input cases
    chunks = [("kept", kept[i:i + chunk]) for i in range(0, len(kept), chunk)] + [("rejected", rejected[i:i + rej_chunk]) for i in range(0, len(rejected), rej_chunk)]
    packs, cur, size = [], [], 0
    for c in chunks:
        if size + len(c[1]) > per_input and cur:
            packs.append(cur)
            cur, size = [], 0
        cur.append(c)
        size += len(c[1])
    if cur:
        packs.append(cur)
    for pack in packs:
        pt = {}
        for _, items in pack:
            for _, _, _, t in items:
                pt.update(t)
        lets = LEAN_POOLS + W + OF + TS + TCOL + FT + MK + CH + pow_let(pt) + CASE_D + lean_chunks([[it[0] for it in items] for _, items in pack])
        cases = []
        for kind, items in pack:
            ks = [it[0] for it in items]
            cases.append((f"{kind} seeds {ks[0]}..{ks[-1]} ({len(ks)})", "hosmer_lemeshow", w([it[2] for it in items]),
                          {"fz": kind, "covers": len(ks), "seeds": ks}))
        st.ints(lets, BODY, cases, gen=True, use_kit=False)
    (HERE.parent / "work").mkdir(exist_ok=True)
    fz = {"fuzzer": "port-translator-hl-fuzz", "generator": "diffeval/units/fz_hl_gen.py", "blueprint": BLUEPRINT,
          "units": {"hosmer_lemeshow": {
              "seeds": f"{first}..{first + count - 1}", "generated": count, "kept": len(kept),
              "python_raises_inside_precondition": [d[0] for d in defects],
              "note": "pools: n 0..300, y f64/int/bool pools (clean, edges, few/many events, integral, halves, all zero/null, signed zeros), "
                      "pd structured a/100+jitter with ties at 1e-6, edge pool, low/high end pools around 1e-6 and 0.999999 +- ulp, "
                      "non-finite, huge/tiny, duplicates, grid; chi2 stub x*3+df, pow2 lookup of squares != x*x; one case = chunk of 20 digests",
              "rejected_sent": len(rejected), "dropped_python_raises_outside_precondition": dropped}}}
    (HERE.parent / "work" / "fz_hl.fuzz.json").write_text(json.dumps(fz, indent=1))
    return st, kept, rejected, defects, dropped, packs


if __name__ == "__main__":
    a = sys.argv[1:]
    st, kept, rejected, defects, dropped, packs = suite(*(int(x) for x in a))
    st.write()
    for i, inp in enumerate(st.inputs):
        (HERE.parent / "work" / f"fz_hl.in{i}.txt").write_text(inp["text"])
    print("kept", len(kept), "rejected sent", len(rejected), "defects", defects[:5], len(defects), "dropped", dropped)
    print("input sizes", [len(i["text"]) for i in st.inputs])
