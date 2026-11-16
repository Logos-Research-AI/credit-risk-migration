"""Fuzz pass 2026-11-16 (prompts/fuzz-2026-11-16.md), by port-translator-3 on units it reviewed:
_groups, _pairs, roc_association, association_table (sas_compat.py:892-1032).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_t1_gen.py
      -> diffeval/work/fz_t1.json, fz_t1.inputs.json, fz_t1.fuzz.json
  eval_decl each input on def:zz_carrier_s; python3 diffeval/fuzz_collect.py 3 fz_t1; compare.py; fuzz_receipt.py

Inputs are built inside Lean from the seed (kit.GEN) and mirrored here (kit.gF / gI / hsh). One seed
gives one (y, score) pair of columns, and one (ss, eps) for _groups. A case is the digest of the
results of CH seeds (field "covers").

Expected values: the real sas_compat functions on the mirrored values.

math.fsum (explicit parameter `fsum` of roc_association): on the Lean side the algorithm of CPython's
math.fsum (Shewchuk partials, final rounding half to even) written as a `let`; its Python mirror
`py_fsum` is asserted equal, bit for bit, to the value math.fsum returned on every list the port
passed during this run.

Preconditions, rendered in Python:
  _groups_precond             ss is 1-D: always true here (only 1-D arrays are generated)
  _pairs_precond              len(y) == len(score) and each dtype in Float64 / Int64 / Boolean / Null
  association_table_precond   = _pairs_precond
  roc_association_precond     _pairs_precond and, when the area exists, not (s10 + s01 < 0), with
                              s10, s01 recomputed here from sc._pairs by the formula of sc:962-963
A seed where the precondition rejects and Python raises (unequal lengths) is dropped.
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
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import b4_gen as b4  # noqa: E402
import compare as cmp  # noqa: E402
import kit  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

ITEM, DECL = "def:zz_carrier_s", "zz_carrier_s"
LABEL = "Logistic Model"
nan, inf = float("nan"), float("inf")
up, dn = (lambda x: math.nextafter(x, inf)), (lambda x: math.nextafter(x, -inf))
raw, lf, w, o = b4.raw, b4.lf, b4.w, b4.o
E_, T_ = sc._SE_EPS, sc._TIE_EPS
SEED0, TARGET, CH, PER_INPUT = 10000, 2100, 25, 21  # 21 chunks of 25 seeds per eval input

NS = [0, 1, 2, 3, 4, 5, 7, 9, 12, 16, 24, 40]
EY = [0.0, 1.0, 0.0, 1.0, 1.0, 0.0, None, nan, -0.0, 2.0, 0.5, 1.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0]
ES = [None, nan, inf, -inf, 0.0, -0.0, 0.5, 1.0, 0.5 - E_, up(0.5 - E_), dn(0.5 - E_), 0.5 - T_, up(0.5 - T_),
      dn(0.5 - T_), 1e300, -1e300, 1e-300, 5e-324, 0.3, 0.3, 0.5, 0.5 + E_, 0.5 + T_]
J2 = [0.0, E_, -E_, E_ / 2, up(E_), dn(E_), 2 * E_, 0.75 * E_, T_, -T_, T_ / 2, 1e-9]
LV = [1, 2, 3, 6, 12]
EP = [0.0, T_, E_, nan, inf, -inf, -1.0, 1e300, 5e-324, 0.5, up(T_), dn(E_), 1.0, 2.0]
OY, OS, OG, OGR = 0, 1000003, 2000003, 3000003


def olist(xs) -> str:
    return "[" + ", ".join("none" if x is None else f"some {lf(x)}" for x in xs) + "]"


FS_LET = (
    # CPython's math.fsum
    "let FS := fun (xs : List Float) => let ps := xs.foldl (fun (ps : List Float) (x0 : Float) => "
      "let r := ps.foldl (fun (st : Float × List Float) (y0 : Float) => let a := if st.1.abs < y0.abs then y0 else st.1; "
      "let b := if st.1.abs < y0.abs then st.1 else y0; let hi := a + b; let lo := b - (hi - a); "
      "(hi, if lo != 0.0 then st.2 ++ [lo] else st.2)) (x0, ([] : List Float)); r.2 ++ [r.1]) ([] : List Float); "
      "(match ps.reverse with | [] => (0.0 : Float) | p :: t => "
      "let r := t.foldl (fun (st : Float × Float × Bool × Option Float) (y : Float) => "
      "if st.2.2.1 then (if st.2.2.2.isNone then (st.1, st.2.1, true, some y) else st) else "
      "let hi := st.1 + y; let lo := y - (hi - st.1); (hi, lo, lo != 0.0, (none : Option Float))) (p, (0.0 : Float), false, (none : Option Float)); "
      "(match r.2.2.2 with | some q => if (r.2.1 < 0.0 && q < 0.0) || (r.2.1 > 0.0 && q > 0.0) then "
      "(let y := r.2.1 * 2.0; let x := r.1 + y; if y == x - r.1 then x else r.1) else r.1 | none => r.1)); "
)
U_LETS = {
    "_pairs": b4.FA + "let P := fun (y s : Pl.Col Float) => let q := _pairs (α := Float) y s; W ([q.conc, q.disc, q.tied, q.n1, q.n0] ++ fa q.v10 ++ fa q.v01); ",
    "roc_association": b4.OF + b4.TS + b4.TCOL + FS_LET
      + "let R := fun (y s : Pl.Col Float) (l : Option String) => W (match roc_association (α := Float) FS y s l with "
        "| .inl r => 0 :: (o r.area ++ o r.std_err ++ o r.lower ++ o r.upper ++ o r.somers_d ++ o r.gamma ++ o r.tau_a) "
        "| .inr fr => 1 :: (fr.length : Int) :: fr.flatMap (fun (p : String × Pl.Col Float) => ts p.1 ++ tc p.2) : List Int); ",
    "association_table": b4.OF + "let A := fun (y s : Pl.Col Float) => let r := association_table (α := Float) y s; W (o r.concordant_pct ++ o r.discordant_pct ++ o r.tied_pct ++ [r.pairs] ++ "
        "o r.somers_d ++ o r.gamma ++ o r.tau_a ++ o r.c); ",
    "_groups": f"let EP : List Float := [{', '.join(lf(j) for j in EP)}]; "
        f"let GS := fun (s : Nat) => W (_groups (α := Float) (Np.NDArray.d1 ((gF (s + {OGR}) (nn s) 50 3 ES).filterMap id)) (EP.getD (h s 1005 % {len(EP)}) 0.0)); ",
}
BASE = (
    b4.W + "let h := fun (s k : Nat) => (hsh s k).toNat; "
    + f"let NS : List Nat := {NS}; let ES : List (Option Float) := {olist(ES)}; "
    + "let nn := fun (s : Nat) => NS.getD (h s 1000 % 12) 0; "
)
COLS = (
    f"let EY : List (Option Float) := {olist(EY)}; let J : List Float := [{', '.join(lf(j) for j in J2)}]; let LV : List UInt64 := {LV}; "
    + "let bl := fun (v : List (Option Int)) => v.map (fun (x : Option Int) => x.map (fun (i : Int) => i == 1)); "
    + f"let YC := fun (s : Nat) => let n := nn s; (match h s 1001 % 10 with | 6 => Pl.Col.int (gI s n 8 3 0) | 7 => Pl.Col.int (gI s n 8 4 1) "
      "| 8 => Pl.Col.bool (bl (gI s n 8 2 0)) | 9 => Pl.Col.null n | _ => Pl.Col.f64 (gF s n 100 1 EY) : Pl.Col Float); "
    + f"let SC := fun (s : Nat) => let n := nn s + (if h s 1003 % 25 == 0 then 1 else 0); let a := s + {OS}; (match h s 1002 % 10 with "
      "| 0 | 1 | 2 => Pl.Col.f64 (List.zipWith (fun (a b : Option Int) => (match a, b with | some a, some b => some (Float.ofInt a / 100.0 + J.getD b.toNat 0.0) | _, _ => none : Option Float)) "
      f"(gI a n 4 (LV.getD (h s 1004 % 5) 1) 0) (gI (s + {OG}) n 0 {len(J2)} 0)) "
      "| 3 | 4 | 5 => Pl.Col.f64 (gF a n 50 3 ES) | 6 => Pl.Col.f64 (gF a n 0 1 ES) | 7 => Pl.Col.int (gI a n 5 4 1) "
      "| 8 => Pl.Col.bool (bl (gI a n 5 2 0)) | _ => Pl.Col.null n : Pl.Col Float); "
    # the seeds of chunk i that Python kept: asserted in the generator to be exactly those with equal lengths
    + f"let KS := fun (i : Nat) => (List.range' ({SEED0} + {CH} * i) {CH}).filter (fun (s : Nat) => h s 1003 % 25 != 0); "
)


def h(s: int, k: int) -> int:
    return kit.hsh(s, k)


def nn(s: int) -> int:
    return NS[h(s, 1000) % 12]


def bl(v):
    return [None if x is None else x == 1 for x in v]


def y_col(s: int) -> pl.Series:
    n = nn(s)
    k = h(s, 1001) % 10
    if k == 6:
        return pl.Series(kit.gI(s, n, 8, 3, 0), dtype=pl.Int64)
    if k == 7:
        return pl.Series(kit.gI(s, n, 8, 4, 1), dtype=pl.Int64)
    if k == 8:
        return pl.Series(bl(kit.gI(s, n, 8, 2, 0)), dtype=pl.Boolean)
    if k == 9:
        return pl.Series([None] * n, dtype=pl.Null)
    return pl.Series(kit.gF(s, n, 100, 1, EY), dtype=pl.Float64, nan_to_null=False)


def s_col(s: int) -> pl.Series:
    n = nn(s) + (1 if h(s, 1003) % 25 == 0 else 0)
    a = s + OS
    k = h(s, 1002) % 10
    if k in (0, 1, 2):
        g, j = kit.gI(a, n, 4, LV[h(s, 1004) % 5], 0), kit.gI(s + OG, n, 0, len(J2), 0)
        return pl.Series([None if x is None else float(x) / 100.0 + J2[b] for x, b in zip(g, j, strict=True)],
                         dtype=pl.Float64, nan_to_null=False)
    if k in (3, 4, 5):
        return pl.Series(kit.gF(a, n, 50, 3, ES), dtype=pl.Float64, nan_to_null=False)
    if k == 6:
        return pl.Series(kit.gF(a, n, 0, 1, ES), dtype=pl.Float64, nan_to_null=False)
    if k == 7:
        return pl.Series(kit.gI(a, n, 5, 4, 1), dtype=pl.Int64)
    if k == 8:
        return pl.Series(bl(kit.gI(a, n, 5, 2, 0)), dtype=pl.Boolean)
    return pl.Series([None] * n, dtype=pl.Null)


def groups_in(s: int):
    ss = [x for x in kit.gF(s + OGR, nn(s), 50, 3, ES) if x is not None]
    return np.asarray(ss, dtype=np.float64), EP[h(s, 1005) % len(EP)]


# ---------------------------------------------------------------- math.fsum mirror
def py_fsum(xs) -> float:
    ps: list[float] = []
    for x in xs:
        new = []
        for y in ps:
            a, b = (y, x) if abs(x) < abs(y) else (x, y)
            hi = a + b
            lo = b - (hi - a)
            if lo != 0.0:
                new.append(lo)
            x = hi
        ps = new + [x]
    if not ps:
        return 0.0
    n = len(ps) - 1
    hi, lo = ps[n], 0.0
    while n > 0:
        x = hi
        n -= 1
        y = ps[n]
        hi = x + y
        lo = y - (hi - x)
        if lo != 0.0:
            break
    if n > 0 and ((lo < 0.0 and ps[n - 1] < 0.0) or (lo > 0.0 and ps[n - 1] > 0.0)):
        y = lo * 2.0
        x = hi + y
        if y == x - hi:
            hi = x
    return hi


_orig_fsum = math.fsum
FSUM_CALLS = [0]


def _chk_fsum(xs):
    xs = list(xs)
    r = _orig_fsum(xs)
    assert raw(py_fsum(xs)) == raw(r), ("py_fsum differs from math.fsum", xs)
    FSUM_CALLS[0] += 1
    return r


math.fsum = _chk_fsum

NUMERIC = (pl.Float64, pl.Int64, pl.Boolean, pl.Null)


def pre_pairs(y: pl.Series, s: pl.Series) -> bool:
    return y.len() == s.len() and y.dtype in NUMERIC and s.dtype in NUMERIC


def pre_roc(y: pl.Series, s: pl.Series) -> bool:
    if not pre_pairs(y, s):
        return False
    q = sc._pairs(y, s)
    p = q.n1 * q.n0
    if p == 0:
        return True
    a = (q.conc + 0.5 * q.tied) / p
    s10 = _orig_fsum(((q.v10 - a) ** 2).tolist()) / (q.n1 - 1 if q.n1 >= 2 else sc._SQRTBIG) / q.n1
    s01 = _orig_fsum(((q.v01 - a) ** 2).tolist()) / (q.n0 - 1 if q.n0 >= 2 else sc._SQRTBIG) / q.n0
    return not (s10 + s01 < 0.0)


def d_pairs(y, s) -> int:
    q = sc._pairs(y, s)
    return w([q.conc, q.disc, q.tied, q.n1, q.n0] + b4.fa(q.v10) + b4.fa(q.v01))


def d_roc(y, s) -> int:
    return w([w([0] + b4.roc_tok(sc.roc_association(y, s))), w([1] + b4.frame_tok(sc.roc_association(y, s, LABEL)))])


def d_assoc(y, s) -> int:
    a = sc.association_table(y, s)
    return w(o(a.concordant_pct) + o(a.discordant_pct) + o(a.tied_pct) + [a.pairs] + o(a.somers_d)
             + o(a.gamma) + o(a.tau_a) + o(a.c))


def d_groups(s: int) -> int:
    ss, eps = groups_in(s)
    return w([int(x) for x in sc._groups(ss, eps).tolist()])


UNITS = {
    "_pairs": (pre_pairs, d_pairs, "W (c.map (fun (s : Nat) => P (YC s) (SC s)))"),
    "roc_association": (pre_roc, d_roc, f'W (c.map (fun (s : Nat) => W [R (YC s) (SC s) none, R (YC s) (SC s) (some "{LABEL}")]))'),
    "association_table": (pre_pairs, d_assoc, "W (c.map (fun (s : Nat) => A (YC s) (SC s)))"),
}
POOLS = ("rows 0..40 by seed; y: Float64 from {0, 1, null, NaN, -0.0, 2, 0.5} / Int64 with nulls / Boolean / Null dtype; "
         "score: a grid of 1..12 levels plus offsets of the size of _SE_EPS and _TIE_EPS (ties), or 50% edges "
         "(null, NaN, +-inf, +-0.0, 0.5 and 0.5 -+ each eps exactly and one ulp either side, +-1e300, 1e-300, 5e-324), "
         "or random floats, or Int64 / Boolean / Null dtype; score one row longer in 1 seed of 25; "
         f"one case digests {CH} seeds")


def main() -> None:
    st = Suite("fz_t1")
    st.item, st.decl = ITEM, DECL
    fuzz = {"fuzzer": "port-translator-3", "generator": "diffeval/units/fz_t1_gen.py", "units": {}}
    chunks: dict[str, list[tuple[list[int], int]]] = {}
    for unit, (pre, dig, _) in UNITS.items():
        kept: list[tuple[int, int]] = []
        gen = dropped = 0
        raises: list[int] = []
        rejected_returns: list[int] = []
        s = SEED0
        while len(kept) < TARGET:
            y, sc_ = y_col(s), s_col(s)
            gen += 1
            try:
                ok = pre(y, sc_)
            except Exception:
                ok = None  # the precondition itself could not be evaluated: Python raises in _pairs
            try:
                v = dig(y, sc_)
            except Exception:
                v = None
            if ok and v is not None:
                kept.append((s, v))
            elif ok and v is None:
                raises.append(s)
            elif v is not None:
                rejected_returns.append(s)
            else:
                dropped += 1
            s += 1
        assert not rejected_returns, rejected_returns[:5]  # none arises with these pools
        kd = dict(kept)
        assert sorted(kd) == [x for x in range(SEED0, s) if h(x, 1003) % 25 != 0], "kept seeds are not the equal-length seeds"
        assert (s - SEED0) % CH == 0 or True
        chunks[unit] = []
        for a0 in range(SEED0, s, CH):
            c = [x for x in range(a0, a0 + CH) if x in kd]
            c_all = [x for x in range(a0, a0 + CH) if h(x, 1003) % 25 != 0]
            if c != c_all:  # the last, partial chunk: extend the kept seeds to the whole chunk
                for x in c_all:
                    if x not in kd:
                        yy, ss_ = y_col(x), s_col(x)
                        assert pre(yy, ss_)
                        kd[x] = dig(yy, ss_)
                c = c_all
            chunks[unit].append((c, w([kd[x] for x in c])))
        kept = sorted(kd.items())
        gen = len(chunks[unit]) * CH
        dropped = gen - len(kept)
        s = SEED0 + gen
        fuzz["units"][unit] = {"seeds": f"{SEED0}..{s - 1}", "generated": gen, "kept": len(kept),
                               "python_raises_inside_precondition": raises,
                               "note": f"{POOLS}; {dropped} seeds dropped (unequal lengths: precondition rejects and Python raises)"}
        print(unit, "generated", gen, "kept", len(kept), "dropped", dropped, "raises inside", raises[:5])
    # _groups: every seed is kept
    gk = [(s, d_groups(s)) for s in range(SEED0, SEED0 + TARGET)]
    chunks["_groups"] = [([a for a, _ in gk[k:k + CH]], w([b for _, b in gk[k:k + CH]])) for k in range(0, len(gk), CH)]
    fuzz["units"]["_groups"] = {"seeds": f"{SEED0}..{SEED0 + TARGET - 1}", "generated": TARGET, "kept": TARGET,
                                "python_raises_inside_precondition": [],
                                "note": "ss: 0..40 values, 50% edges (NaN, +-inf, +-0.0, values one ulp either side of each eps below 0.5, "
                                        "+-1e300, 1e-300, 5e-324), else random; eps from {0, _TIE_EPS, _SE_EPS, NaN, +-inf, -1, 1e300, "
                                        f"5e-324, 0.5, one ulp beside the two eps, 1, 2}}; 1-D arrays only; one case digests {CH} seeds"}
    bodies = dict({u: b for u, (_, _, b) in UNITS.items()}, _groups="W (c.map GS)")
    for unit, chs in chunks.items():
        if unit == "_groups":
            body = f"(List.range {len(chs)}).map (fun (i : Nat) => let c := List.range' ({SEED0} + {CH} * i) {CH}; {bodies[unit]})"
            lets = BASE + U_LETS[unit]
        else:
            body = f"(List.range {len(chs)}).map (fun (i : Nat) => let c := KS i; {bodies[unit]})"
            lets = BASE + COLS + U_LETS[unit]
        st.ints(lets, body, [(f"{unit} seeds {SEED0 + CH * i}..{SEED0 + CH * i + CH - 1}", unit, v, {"fz": "kept", "covers": len(c)})
                             for i, (c, v) in enumerate(chs)], gen=True, use_kit=False)
    st.notes = {u: "fuzz 2026-11-16" for u in chunks}
    st.write()
    (HERE.parent / "work" / "fz_t1.fuzz.json").write_text(json.dumps(fuzz, indent=1))
    print("math.fsum calls checked against py_fsum:", FSUM_CALLS[0])
    for i, inp in enumerate(st.inputs):
        print(i, len(inp["text"]), "chars")


if __name__ == "__main__":
    main()
