"""Fuzz of def:train_run_10_score_valid (+ def:train_run_10_score_valid_precond), fifth port diff (2026-11-18), by a non-author.
Nothing is changed on the blueprint (blueprint 5365851c-5549-44b7-9207-4bd4c422031d).

  --text B N          Lean term (one eval_decl input, decl zz_carrier on def:zz_carrier): for seeds B..B+N-1 the list
                      [input digest, output digest] per seed
  --expect B N        the same list computed in Python (the real lines 611-635 of train.py, exec'd by fz5_s10_py.py)
  --cmp B N leanfile  compare a Lean output line with --expect (same seeds)
  --show S            the case of seed S in words, and the Python result

Case of seed s (built INSIDE Lean from hsh of diffeval/kit.py, mirrored here, integer arithmetic only; u(k) = hsh(s, k)):
  mode (u1>>8)%9 picks, for the intercept / the coefficients / the cells, a pool (EP eta edges, ZP zeros and specials, ZE the two zeros,
  PP powers of two, HP the 0.5 threshold of pd with ulps, UP all) with an edge percentage and an exponent half-range (rnd);
  rows n from NR (0,1,2,3,.. 10; mode 8: 40..79 rows of moderate eta to compare exp); 1 case in 12 is a frame with no column;
  final some with 3 in 4; intercept none with 1 in 10; 0..4 coefficients (mode 8: 1..2) on distinct names among
  c0..c4, predicted_logit, pd_logistic, pred_logistic; the frame has the coefficient columns (Float64) when final is some,
  every other name with 35% and a dtype among f64/int/str/bool, extra columns i0 s0 f0 b0 with 40%, nulls in cells with pn% (0,0,5,20,100),
  columns rotated by (u60>>8) % count.
Classes: Python returns (kept, sent) / Python raises (an admitted input where the unit has a precondition gap: not sent, listed).
"""
from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import polars as pl  # noqa: E402
import compare as cmp  # noqa: E402
import kit  # noqa: E402
from fz5_s10_py import step10  # noqa: E402

M64 = (1 << 64) - 1
h = kit.hsh
NAN, INF = float("nan"), float("inf")


def bits(x):
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def flt(b):
    return struct.unpack("<d", struct.pack("<Q", b & M64))[0]


def xmax():
    lo_b, hi_b = bits(700.0), bits(720.0)  # largest x with a finite exp
    while hi_b - lo_b > 1:
        mid = (lo_b + hi_b) // 2
        try:
            math.exp(flt(mid))
            lo_b = mid
        except OverflowError:
            hi_b = mid
    return flt(lo_b)


def xzero():  # smallest x with exp(-x) == 0 (underflow)
    lo_b, hi_b = bits(740.0), bits(760.0)
    while hi_b - lo_b > 1:
        mid = (lo_b + hi_b) // 2
        if math.exp(-flt(mid)) == 0.0:
            hi_b = mid
        else:
            lo_b = mid
    return flt(hi_b)


XM, XZ = xmax(), xzero()
EP = []
for v in (XM, XZ, 36.7368005696771, 37.0, 18.714973875118524):
    for k in (-2, -1, 0, 1, 2):
        EP += [flt(bits(v) + k), -flt(bits(v) + k)]
EP += [0.0, -0.0, 1.0, -1.0, 0.5, -0.5, 2.0 ** -52, -(2.0 ** -52), 2.0 ** -53, -(2.0 ** -53), 2.0 ** -54, -(2.0 ** -54),
       5e-324, -5e-324, 1e-17, 700.0, -700.0, 710.0, -710.0, 740.0, -740.0, 745.0, 746.0, -745.0, 800.0, -800.0, 1e3, -1e3,
       1e308, -1e308, 1.7976931348623157e308, -1.7976931348623157e308, NAN, INF, -INF, 36.0, 38.0, 40.0, -40.0, 20.0, -20.0]
ZP = [0.0, -0.0, 1.0, -1.0, 0.5, 2.0, NAN, INF, -INF, 1e-300]
ZE = [0.0, -0.0]
PP = [1.0, 2.0, 0.5, -1.0, 4.0, -2.0, 0.25, 1.0]
HP = []
for v in (2.0 ** -52, 2.0 ** -53, 2.0 ** -54, 2.0 ** -55, 1.1102230246251565e-16, 5e-324, 1e-300, 2.0 ** -1022):
    for k in (-2, -1, 0, 1, 2):
        HP += [flt(bits(v) + k), -flt(bits(v) + k)]
HP += [0.0, -0.0]
if sys.argv[-1] == "hp2" or "hp2" in sys.argv:  # second sweep: eta near -2^-51 .. -2^-49, where pd first falls below 0.5
    sys.argv.remove("hp2")
    HP = []
    for v in (2.0 ** -51, 2.0 ** -50, 2.0 ** -49, 1.5 * 2.0 ** -51, 1.25 * 2.0 ** -51, 1.75 * 2.0 ** -51, 3 * 2.0 ** -52, 2.0 ** -52 * 1.25):
        for k in (-3, -2, -1, 0, 1, 2, 3):
            HP += [flt(bits(v) + k), -flt(bits(v) + k)]
    HP += [0.0, -0.0, 2.0 ** -53, -(2.0 ** -53), 2.0 ** -52, -(2.0 ** -52)]
UP = EP + ZP + HP
POOLS = [EP, ZP, ZE, PP, UP, HP]  # indices 0..5
# per mode: (pool, pe, eh) for the intercept, a coefficient, a cell
MODES = [
    ((0, 100, 8), (1, 100, 8), (1, 100, 8)),
    ((2, 100, 8), (1, 100, 8), (0, 100, 8)),
    ((2, 100, 8), (3, 100, 8), (0, 100, 8)),
    ((0, 20, 6), (1, 20, 6), (0, 20, 6)),
    ((0, 10, 600), (0, 10, 600), (0, 10, 600)),
    ((0, 100, 8), (1, 30, 30), (1, 50, 30)),
    ((4, 60, 100), (4, 60, 100), (4, 60, 100)),
    ((5, 100, 8), (1, 100, 8), (1, 100, 8)),
    ((2, 50, 3), (3, 40, 2), (0, 0, 5)),
]
NR = [0, 0, 1, 1, 1, 2, 2, 3, 4, 5, 7, 10]
PN = [0, 0, 5, 20, 100]
NM = ["c0", "c1", "c2", "c3", "c4", "predicted_logit", "pd_logistic", "pred_logistic", "i0", "s0", "f0", "b0"]
STRS = ["a", "b", "", "zz"]


def fpick(E, u):
    return E[(u >> 20) % len(E)]


def rnd(u, eh):
    b = (u & 0x8000000000000000) | (((1023 - eh + (u >> 52) % (2 * eh + 1)) * 0x10000000000000) & M64) | (u & 0xFFFFFFFFFFFFF)
    return flt(b)


def gen(t, s, k):
    p, pe, eh = t
    u = h(s, k)
    return fpick(POOLS[p], u) if (u >> 8) % 100 < pe else rnd(u, eh)


def build(s):
    u = lambda k: h(s, k)  # noqa: E731
    mode = (u(1) >> 8) % 9
    fin = (u(3) >> 8) % 4 != 0
    n = 40 + (u(2) >> 8) % 40 if mode == 8 else NR[(u(2) >> 8) % 12]
    nocol = mode != 8 and (u(9) >> 8) % 12 == 0
    if nocol:
        n = 0
    pn = PN[(u(7) >> 8) % 5]
    ti, tb, tx = MODES[mode]
    icpt = None if (u(4) >> 8) % 10 == 0 else gen(ti, s, 20)
    nc = 1 + (u(5) >> 8) % 2 if mode == 8 else (u(5) >> 8) % 5
    if nocol and fin:
        nc = 0
    used = []
    for j in range(nc):
        q0 = (u(10 + j) >> 8) % 8
        used.append(next((q0 + d) % 8 for d in range(8) if (q0 + d) % 8 not in used))
    coefs = [(NM[used[j]], gen(tb, s, 30 + j)) for j in range(nc)]
    cols = []
    for q in range(12):
        if nocol:
            continue
        if q < 8:
            if fin and q in used:
                dt = 0
            elif (u(40 + q) >> 8) % 100 < 35:
                dt = (u(40 + q) >> 20) % 4
            else:
                continue
        else:
            if (u(40 + q) >> 8) % 100 >= 40:
                continue
            dt = [1, 2, 0, 3][q - 8]
        vals = []
        for t in range(n):
            key = 100 + q * 128 + t
            if dt == 0:
                vals.append(None if (h(s, key) >> 8) % 100 < pn else gen(tx, s, key + 4000))
            else:
                w = h(s, key + 8000)
                if (w >> 8) % 100 < 15:
                    vals.append(None)
                elif dt == 1:
                    vals.append(((w >> 20) % 7) - 3)
                elif dt == 2:
                    vals.append(STRS[(w >> 20) % 4])
                else:
                    vals.append((w >> 20) % 2 == 0)
        cols.append((NM[q], dt, vals))
    r = (u(60) >> 8) % max(len(cols), 1)
    cols = cols[r:] + cols[:r]
    return dict(seed=s, mode=mode, fin=fin, n=n, icpt=icpt, coefs=coefs, cols=cols)


DT = [pl.Float64, pl.Int64, pl.String, pl.Boolean]


def to_df(c):
    return pl.DataFrame([pl.Series(nm, vals, dtype=DT[dt]) for nm, dt, vals in c["cols"]])


FIN = object()


def run_py(c):
    df = to_df(c)
    return step10(c["icpt"], dict(c["coefs"]), FIN if c["fin"] else None, df), df


def tok_in(c, df):
    t = [1] + ([0] if c["icpt"] is None else [1, cmp.fbits(c["icpt"])]) + [1 if c["fin"] else 0, len(c["coefs"])]
    for nm, b in c["coefs"]:
        t += cmp.tok_str(nm) + [cmp.fbits(b)]
    return t + cmp.tokens(cmp.canon_frame(df))


def expect(B, N):
    out, raised = [], []
    for s in range(B, B + N):
        c = build(s)
        try:
            res, df = run_py(c)
        except Exception as e:  # noqa: BLE001
            raised.append((s, type(e).__name__))
            out += [-1, -1]
            continue
        out += [cmp.digest(tok_in(c, df)), cmp.digest(cmp.tokens(cmp.canon_frame(res)))]
    return out, raised


# ---------------------------------------------------------------- Lean text
def u64(xs):
    return "[" + ", ".join(hex(bits(x)) for x in xs) + "]"


PRE = (
    kit.GEN.split("let gF")[0]
    + kit._BASE
    + kit._TC.format(cell="[5, v.length.toUInt64]")
    + kit._TR
    + "".join(f"let P{i} : List UInt64 := {u64(p)}; " for i, p in enumerate(POOLS) if i != 4)
    + "let P4 : List UInt64 := P0 ++ P1 ++ P5; "
    + "let PT : List (List UInt64) := [" + ", ".join(f"P{i}" for i in range(len(POOLS))) + "]; "
    + "let MT : List (Nat × Nat × Nat) := [" + ", ".join(f"({p}, {pe}, {eh})" for m in MODES for (p, pe, eh) in m) + "]; "
    + "let NR : List Nat := [" + ", ".join(map(str, NR)) + "]; "
    + "let PN : List UInt64 := [" + ", ".join(map(str, PN)) + "]; "
    + "let NM : List String := [" + ", ".join(f'"{x}"' for x in NM) + "]; "
    + "let STRS : List String := [" + ", ".join(f'"{x}"' for x in STRS) + "]; "
    + "let fpick := fun (E : List UInt64) (u : UInt64) => Float.ofBits (E.getD ((u >>> 20) % E.length.toUInt64).toNat 0); "
    + "let rnd := fun (u : UInt64) (eh : UInt64) => let k : UInt64 := u >>> 52; Float.ofBits ((u &&& 0x8000000000000000) ||| ((1023 - eh + k % (2 * eh + 1)) * 0x10000000000000) ||| (u &&& 0xFFFFFFFFFFFFF)); "
    + "let gen := fun (t : Nat × Nat × Nat) (s k : Nat) => let u := hsh s k; if (u >>> 8) % 100 < t.2.1.toUInt64 then fpick (PT.getD t.1 []) u else rnd u t.2.2.toUInt64; "
)

# Copies of the stored Lean of def:_e, _named, sas_exp, lt, ge, flag and the unit (statement text of the revisions in the task),
# alpha := Float, as `let` lambdas: eval_decl has no carrier item that depends on the unit (def:zz_carrier is not in the blueprint),
# and a Pl.Frame has no Repr, so the unit cannot be evaluated on its own item; the only decl that returns a printable value from
# frames is Pl.zipB of def:ExprOrNum, where the unit is not in scope.
COPIES = (
    "let _e := fun (c : ExprOrNum Float) => (match c with | .expr e => e | .float x => Pl.litF x | .int n => Pl.litI n : Pl.Expr Float); "
    "let _named := fun (first : ExprOrNum Float) (out : Pl.Expr Float) => (match (_e first).name with | some s => (if s.isEmpty then out else out.alias s) | none => out : Pl.Expr Float); "
    "let sas_exp := fun (x : ExprOrNum Float) => (let v := (_e x).castF64.exp; _named x (Pl.wto v.isFinite v Pl.litNull) : Pl.Expr Float); "
    "let lt := fun (x c : ExprOrNum Float) => (let xe := _e x; let ce := _e c; "
    "let out := (Pl.wto xe.isNull ce.isNotNull (Pl.wto ce.isNull (Pl.litB false) (xe.lt ce))).fillNull (Pl.litB false); _named x out : Pl.Expr Float); "
    "let ge := fun (x c : ExprOrNum Float) => (_named x ((lt x c).not) : Pl.Expr Float); "
    "let flag := fun (cond : Pl.Expr Float) => (_named (.expr cond) ((cond.fillNull (Pl.litB false)).castI64) : Pl.Expr Float); "
    "let train_run_10_score_valid := fun (intercept : Option Float) (coefficients : List (String × Float)) (final : Option Nat) (mfv : Pl.Frame Float) => ("
    "let eta_valid : Pl.Expr Float := coefficients.foldl (fun (eta : Pl.Expr Float) (cb : String × Float) => eta.add ((Pl.litF cb.2).mul (Pl.col (α := Float) cb.1))) "
    "(match intercept with | some x => Pl.litF x | none => Pl.litNull); "
    "let logit_scored_valid_temp : Option (Pl.Frame Float) := match final with | none => none | some _ => some (mfv.withColumns [(\"predicted_logit\", eta_valid)]); "
    "let valid_temp_read : Pl.Frame Float := match logit_scored_valid_temp with | none => [(\"predicted_logit\", Pl.Col.f64 [])] | some fr => fr; "
    "((valid_temp_read.withColumns [(\"pd_logistic\", (Pl.litI 1).div ((Pl.litI 1).add (sas_exp (.expr (Pl.col (α := Float) \"predicted_logit\").neg))))]).withColumns "
    "[(\"pred_logistic\", flag (ge (.expr (Pl.col (α := Float) \"pd_logistic\")) (.float (0.5 : Float))))]).drop [\"predicted_logit\"] : Pl.Frame Float); "
)

CASE = (
    "let mode := (((hsh s 1) >>> 8) % 9).toNat; "
    "let fin := ((hsh s 3) >>> 8) % 4 != 0; "
    "let n0 := if mode == 8 then 40 + (((hsh s 2) >>> 8) % 40).toNat else NR.getD ((((hsh s 2) >>> 8) % 12).toNat) 0; "
    "let nocol := mode != 8 && ((hsh s 9) >>> 8) % 12 == 0; "
    "let n := if nocol then 0 else n0; "
    "let pn := PN.getD ((((hsh s 7) >>> 8) % 5).toNat) 0; "
    "let ti := MT.getD (mode * 3) (0, 0, 0); let tb := MT.getD (mode * 3 + 1) (0, 0, 0); let tx := MT.getD (mode * 3 + 2) (0, 0, 0); "
    "let icpt : Option Float := if ((hsh s 4) >>> 8) % 10 == 0 then none else some (gen ti s 20); "
    "let nc0 := if mode == 8 then 1 + (((hsh s 5) >>> 8) % 2).toNat else (((hsh s 5) >>> 8) % 5).toNat; "
    "let nc := if nocol && fin then 0 else nc0; "
    "let used : List Nat := (List.range nc).foldl (fun (acc : List Nat) (j : Nat) => "
    "let q0 := ((((hsh s (10 + j)) >>> 8) % 8).toNat); "
    "acc ++ [(((List.range 8).map (fun (d : Nat) => (q0 + d) % 8)).find? (fun (q : Nat) => !(acc.contains q))).getD 0]) []; "
    "let coefs : List (String × Float) := (List.range nc).map (fun (j : Nat) => (NM.getD (used.getD j 0) \"\", gen tb s (30 + j))); "
    "let colF := fun (q : Nat) => Pl.Col.f64 ((List.range n).map (fun (t : Nat) => let key := 100 + q * 128 + t; "
    "if ((hsh s key) >>> 8) % 100 < pn then (none : Option Float) else some (gen tx s (key + 4000)))); "
    "let colI := fun (q : Nat) => Pl.Col.int ((List.range n).map (fun (t : Nat) => let w := hsh s (100 + q * 128 + t + 8000); "
    "if (w >>> 8) % 100 < 15 then (none : Option Int) else some ((((w >>> 20) % 7).toNat : Int) - 3))); "
    "let colS := fun (q : Nat) => Pl.Col.str ((List.range n).map (fun (t : Nat) => let w := hsh s (100 + q * 128 + t + 8000); "
    "if (w >>> 8) % 100 < 15 then (none : Option String) else some (STRS.getD (((w >>> 20) % 4).toNat) \"\"))); "
    "let colB := fun (q : Nat) => Pl.Col.bool ((List.range n).map (fun (t : Nat) => let w := hsh s (100 + q * 128 + t + 8000); "
    "if (w >>> 8) % 100 < 15 then (none : Option Bool) else some (((w >>> 20) % 2) == 0))); "
    "let colOf := fun (q : Nat) (dt : Nat) => (if dt == 0 then colF q else if dt == 1 then colI q else if dt == 2 then colS q else colB q : Pl.Col Float); "
    "let cols0 : List (String × Pl.Col Float) := (List.range 12).filterMap (fun (q : Nat) => "
    "if nocol then none else "
    "if q < 8 then (if fin && used.contains q then some (NM.getD q \"\", colOf q 0) "
    "else if ((hsh s (40 + q)) >>> 8) % 100 < 35 then some (NM.getD q \"\", colOf q ((((hsh s (40 + q)) >>> 20) % 4).toNat)) else none) "
    "else (if ((hsh s (40 + q)) >>> 8) % 100 >= 40 then none else some (NM.getD q \"\", colOf q ([1, 2, 0, 3].getD (q - 8) 0)))); "
    "let r := (((hsh s 60) >>> 8) % (max cols0.length 1).toUInt64).toNat; "
    "let frame : List (String × Pl.Col Float) := cols0.drop r ++ cols0.take r; "
    "let finv : Option Nat := if fin then some 0 else none; "
    "let itk : List UInt64 := tF [icpt] ++ [if fin then 1 else 0, coefs.length.toUInt64] ++ coefs.flatMap (fun (p : String × Float) => tS p.1 ++ [p.2.toBits]) ++ tR frame; "
    "let res := train_run_10_score_valid icpt coefs finv frame; "
)


def lean_text(B, N):
    return "(" + PRE + COPIES + f"(fun (i : Nat) (_ : Unit) => let s := {B} + i; " + CASE + f"([dg itk, dg (tR res)] : List Int))) (List.range {N}) [()]"


def lean_chunks(B, C, K, bases=None, P=None):
    P = P or 100 // K
    """C chunks of K seeds from B: per chunk [folded input digest, folded output digest, seeds compared]; the seeds where
    Python raises (intercept none, final some, no coefficient: `skip`) are left out on both sides"""
    body = (
        f"(fun (ci : Nat) (_ : Unit) => ((List.range {K}).foldl (fun (acc : UInt64 \u00d7 UInt64 \u00d7 Nat) (jj : Nat) => " +
        (f"let s := {B} + ci * {K} + jj; " if bases is None else
         f"let s := ([{', '.join(map(str, bases))}] : List Nat).getD (ci / {P}) 0 + (ci % {P}) * {K} + jj; ") + CASE +
        "if icpt.isNone && fin && coefs.isEmpty then acc else (mx acc.1 (dgu itk), mx acc.2.1 (dgu (tR res)), acc.2.2 + 1)) "
        "((0 : UInt64), (0 : UInt64), 0) |> fun (a : UInt64 \u00d7 UInt64 \u00d7 Nat) => ([(a.1.toNat : Int), (a.2.1.toNat : Int), (a.2.2 : Int)] : List Int)))"
)
    return "(" + PRE + "let dgu := fun (t : List UInt64) => t.foldl mx 14695981039346656037; " + COPIES + body + f") (List.range {C}) [()]"


def lean_pd(bases):
    """per seed in bases: the bits of pd_logistic row by row (-1: null)"""
    body = (
        "(fun (ci : Nat) (_ : Unit) => let s := ([" + ", ".join(map(str, bases)) + "] : List Nat).getD ci 0; " + CASE +
        "((res.col \"pd_logistic\").asF64.map (fun (o : Option Float) => match o with | none => (-1 : Int) | some x => (x.toBits.toNat : Int)) : List Int))"
    )
    return "(" + PRE + COPIES + body + f") (List.range {len(bases)}) [()]"


def mx(h_, x):
    g = ((h_ ^ x) * 1099511628211) & M64
    return g ^ (g >> 32)


def chunk_expect(B, C, K, bases=None, P=None):
    P = P or 100 // K
    out, bad = [], []
    for ci in range(C):
        a1 = a2 = 0
        cnt = 0
        for jj in range(K):
            s = B + ci * K + jj if bases is None else bases[ci // P] + (ci % P) * K + jj
            c = build(s)
            skip = c["icpt"] is None and c["fin"] and not c["coefs"]
            try:
                res, df = run_py(c)
            except Exception as e:  # noqa: BLE001
                if not skip:
                    bad.append((s, "raised but not skipped", type(e).__name__))
                continue
            if skip:
                bad.append((s, "skipped but Python returned"))
                continue
            a1 = mx(a1, cmp.digest(tok_in(c, df)))
            a2 = mx(a2, cmp.digest(cmp.tokens(cmp.canon_frame(res))))
            cnt += 1
        out.append([a1, a2, cnt])
    return out, bad


def main():
    mode = sys.argv[1]
    if mode == "--ptext":
        print(lean_pd([int(x) for x in sys.argv[2].split(",")]))
        return
    if mode == "--pexpect":
        for sd in [int(x) for x in sys.argv[2].split(",")]:
            c = build(sd)
            res, df = run_py(c)
            print(sd, json.dumps([None if v is None else bits(v) for v in res.get_column("pd_logistic").to_list()]))
        return
    if mode == "--dtext":  # bases (comma list) K
        bs = [int(x) for x in sys.argv[2].split(",")]
        K = int(sys.argv[3])
        P = int(sys.argv[4]) if len(sys.argv) > 4 else 100 // K
        print(lean_chunks(0, len(bs) * P, K, bs, P))
        return
    if mode == "--dexpect":
        bs = [int(x) for x in sys.argv[2].split(",")]
        K = int(sys.argv[3])
        P = int(sys.argv[4]) if len(sys.argv) > 4 else 100 // K
        o, bad = chunk_expect(0, len(bs) * P, K, bs, P)
        print(json.dumps(o))
        return
    if mode == "--ctext":
        print(lean_chunks(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])))
        return
    if mode == "--cexpect":
        o, bad = chunk_expect(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
        print(json.dumps(o))
        print("bad", bad, file=sys.stderr)
        return
    if mode == "--text":
        print(lean_text(int(sys.argv[2]), int(sys.argv[3])))
    elif mode == "--expect":
        out, raised = expect(int(sys.argv[2]), int(sys.argv[3]))
        print(json.dumps(out))
        print("raised", raised, file=sys.stderr)
    elif mode == "--show":
        c = build(int(sys.argv[2]))
        print(c)
        try:
            res, df = run_py(c)
            print(df)
            print(res)
        except Exception as e:  # noqa: BLE001
            print("RAISES", type(e).__name__, str(e)[:200])
    elif mode == "--cmp":
        B, N = int(sys.argv[2]), int(sys.argv[3])
        got = json.loads(Path(sys.argv[4]).read_text().strip())
        out, raised = expect(B, N)
        rs = {s for s, _ in raised}
        bad_in, bad_out, kept = [], [], 0
        for i in range(N):
            s = B + i
            if s in rs:
                continue
            kept += 1
            if got[2 * i] != out[2 * i]:
                bad_in.append(s)
            elif got[2 * i + 1] != out[2 * i + 1]:
                bad_out.append(s)
        print(f"seeds {N} kept {kept} python-raised {sorted(rs)} input-mirror-mismatch {bad_in} output-differs {bad_out}")


if __name__ == "__main__":
    main()
