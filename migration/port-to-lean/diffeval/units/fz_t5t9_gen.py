"""Fuzz pass 2026-11-16, port-translator-7: def:fe_run_05_features (feature_engineering.py:234-336)
and def:predict_run_05_features (predict.py:277-372), units I reviewed and did not write.

  from migration/port-to-lean:
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_t5t9_gen.py
      -> diffeval/work/fz_fe05.json, fz_pr05.json, their .inputs.json, .fuzz.json, .in<k>.txt
  eval_decl each input on def:zz_carrier_f / def:zz_carrier_p (text exactly as in work/<suite>.inputs.json)
  python3 diffeval/fuzz_collect.py 7 <suite>; compare.py; python3 diffeval/fuzz_receipt.py <suite>

One generated input = one seed s: a frame and the flag `full`, built INSIDE Lean from s with kit.GEN
and mirrored here with kit.gF / kit.gI / kit.hsh:
  rows     SZ[hsh(s, 9001) % 10], SZ = 0, 1, 2, 3, 4, 5, 7, 12, 24, 40
  full     hsh(s, 9002) % 2 == 0
  columns  the nine columns the step reads, in the order of the precondition; column j is
           gF(16 s + j, rows, pe, 8, E): with hsh(s, 9010 + j) % 10 = m, m = 0 gives an all-null
           column, else pe = 40 + 10 (m % 4) per cent of the values come from the edge pool E and
           the others are random floats of either sign with exponent in [-8, 8].
  E0       null (twice), NaN, +-inf, +-0.0, +-1e300, 1e-300, +-5e-324, -1 one ulp either side, -2,
           0.5, -0.5, 98, and every threshold of the step (25, 30, 35, 43, 50, 60, 65, 75, 100, 200,
           500, 2500, 2, 3, 1) exactly and one ulp either side
  E1       E0 and -1 exactly (log(x + 1) of -1; a late-payment count of -1)
           every column draws from E1, except num_dependents, which draws from E0 unless
           hsh(s, 9003) % 8 == 0 (then E1: a value -1, which the precondition excludes)
  dtype    hsh(s, 9004) % 16 == 0: num_late_30_59 is an Int64 column (values -2..3, 10 % nulls),
           which the precondition excludes
  extras   hsh(s, 9005) % 4 == 0: two columns the step creates are already present with another
           dtype (has_delinquency as text, age_category as Float64) before the nine, and an Int64
           column `zz` the step does not touch after them
Expected: the source lines of the step executed verbatim on the frame (as rv_t5t9_gen.slice_run).
One generated input gives two integers: the digest of the result without the four columns that hold
a logarithm (the last bit of log is outside the model, RULEBOOK 6), and a fold of those four
columns with the low 20 bits of every value dropped (null, NaN, infinities, zeros, sign, exponent
and the upper 32 mantissa bits are compared). A block of seeds returns five integers, each the
fold W of one of these over the seeds of one class, in seed order (the class is computed in Lean
from the same hashes and from the generated num_dependents column):
  kept       the precondition admits the input                              (fz "kept")
  minus one  rejected only by "no value of num_dependents equals -1"        (fz "rejected")
  dtype      rejected by "num_late_30_59 is Float64"                        (fz "rejected")
  kept logs / minus-one logs: the log fold of the first two classes ("covers" 0: the same inputs).
The precondition rendered in Python (`admits`): distinct names and equal column lengths hold for
every pl.DataFrame; "present and Float64" is `schema.get(c) == pl.Float64` for the nine names; the
last clause is `not (x + 1.0 == 0.0)` for every non-null x of num_dependents (IEEE ==, so NaN and
the infinities pass, as with RealLike.eqb on Float).
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import b4_gen as b4  # noqa: E402
import compare as cmp  # noqa: E402
import kit  # noqa: E402
import rv_t5t9_gen as rv  # noqa: E402
from suite import Suite  # noqa: E402

WORK = HERE.parent / "work"
BLOCK, NBLOCK = 750, 4
SZ = [0, 1, 2, 3, 4, 5, 7, 12, 24, 40]
NINE = ["age", "monthly_income", "num_dependents", "num_late_30_59", "num_late_60_89", "num_late_90_plus",
        "credit_utilization", "debt_ratio", "num_credit_lines"]
LOGS = rv.LOGS
nan, inf = float("nan"), float("inf")


def fb(bits: int) -> float:
    return struct.unpack("<d", struct.pack("<Q", bits))[0]


SPECIAL = [None, None, nan, inf, -inf, 0.0, -0.0, 1e300, -1e300, 1e-300, 5e-324, -5e-324,
           fb(b4.raw(-1.0) + 1), fb(b4.raw(-1.0) - 1), -2.0, 0.5, -0.5, 98.0]
T = [25.0, 30.0, 35.0, 43.0, 50.0, 60.0, 65.0, 75.0, 100.0, 200.0, 500.0, 2500.0, 2.0, 3.0, 1.0]
E0 = SPECIAL + [y for t in T for y in (t, fb(b4.raw(t) + 1), fb(b4.raw(t) - 1))]
E1 = E0 + [-1.0]
SUITES = [  # suite, first seed, then the row of rv.UNITS
    ("fz_fe05", 70000, rv.UNITS[0]),
    ("fz_pr05", 75000, rv.UNITS[1]),
]


def frame(s: int):
    n = SZ[kit.hsh(s, 9001) % 10]
    full = kit.hsh(s, 9002) % 2 == 0
    dm = kit.hsh(s, 9003) % 8 == 0
    im = kit.hsh(s, 9004) % 16 == 0
    xm = kit.hsh(s, 9005) % 4 == 0

    def C(j, E):
        m = kit.hsh(s, 9010 + j) % 10
        return kit.gF(s * 16 + j, n, 100, 0, [None]) if m == 0 else kit.gF(s * 16 + j, n, 40 + 10 * (m % 4), 8, E)

    def K(name, j, E=E1):
        return pl.Series(name, C(j, E), dtype=pl.Float64, nan_to_null=False)

    cols = []
    if xm:
        cols += [pl.Series("has_delinquency", ["x"] * n, dtype=pl.Utf8), K("age_category", 9)]
    for j, name in enumerate(NINE):
        if j == 2:
            cols.append(K(name, j, E1 if dm else E0))
        elif j == 3 and im:
            cols.append(pl.Series(name, kit.gI(s * 16 + 3, n, 10, 6, 2), dtype=pl.Int64))
        else:
            cols.append(K(name, j))
    if xm:
        cols.append(pl.Series("zz", kit.gI(s * 16 + 10, n, 20, 5, 0), dtype=pl.Int64))
    return pl.DataFrame(cols), full, im


def admits(df: pl.DataFrame) -> tuple[bool, bool]:
    """def:<unit>_precond, clause by clause: (the nine columns are Float64, no num_dependents + 1 == 0)."""
    assert len(set(df.columns)) == len(df.columns) and all(len(df[c]) == df.height for c in df.columns)
    f64 = all(df.schema.get(c) == pl.Float64 for c in NINE)
    div = all(x is None or not (x + 1.0 == 0.0) for x in df["num_dependents"].to_list())
    return f64, div


def logfold(r: pl.DataFrame) -> int:
    t = []
    for c in LOGS:
        if c not in r.columns or r.schema[c] != pl.Float64:
            t.append(-1)
            continue
        v = r[c].to_list()
        t.append(len(v))
        t += [0 if x is None else 1 if x != x else (b4.raw(x) >> 20) + 2 for x in v]
    return b4.w(t)


def one(unit_row, s: int):
    """(class, main digest, log fold) or (class, None, message) when Python raises."""
    _, _, mod, a, b, inp, out = unit_row
    df, _full, im = frame(s)
    f64, div = admits(df)
    cls = 2 if not f64 else (0 if div else 1)
    assert f64 == (not im)
    try:
        r = rv.slice_run(mod, a, b, inp, out, df)  # `full` is an argument of the Lean unit only
    except Exception as ex:  # noqa: BLE001
        return cls, None, f"{type(ex).__name__}: {ex}"
    return cls, cmp.digest(cmp.tokens(cmp.canon_frame(r.drop(LOGS)))), logfold(r)


def lets(unit: str) -> str:
    sp = "[" + ", ".join("none" if x is None else f"some {b4.lf(x)}" for x in SPECIAL) + "]"
    tl = "[" + ", ".join(str(int(t)) for t in T) + "]"
    lg = "[" + ", ".join(f'"{c}"' for c in LOGS) + "]"
    return (
        b4.W
        + f"let SZ : List Nat := {SZ}; let LOGS : List String := {lg}; "
        + f"let E0 : List (Option Float) := {sp} ++ ({tl} : List Float).flatMap (fun (t : Float) => [some t, some (Float.ofBits (t.toBits + 1)), some (Float.ofBits (t.toBits - 1))]); "
        + "let E1 : List (Option Float) := E0 ++ [some (-1.0)]; "
        + "let LG := fun (r : Pl.Frame Float) => LOGS.flatMap (fun (c : String) => (match r.lookup c with "
          "| some (.f64 v) => (v.length : Int) :: v.map (fun (o : Option Float) => (match o with | none => 0 | some x => if x.isNaN then 1 else ((x.toBits >>> 20).toNat : Int) + 2 : Int)) "
          "| _ => [-1] : List Int)); "
        + "let ONE := fun (s : Nat) => let n := SZ.getD ((hsh s 9001).toNat % 10) 0; let full := (hsh s 9002).toNat % 2 == 0; "
          "let dm := (hsh s 9003).toNat % 8 == 0; let im := (hsh s 9004).toNat % 16 == 0; let xm := (hsh s 9005).toNat % 4 == 0; "
          "let C := fun (j : Nat) (E : List (Option Float)) => let m := (hsh s (9010 + j)).toNat % 10; "
          "(if m == 0 then gF (s * 16 + j) n 100 0 [none] else gF (s * 16 + j) n (40 + 10 * (m % 4)).toUInt64 8 E : List (Option Float)); "
          "let dep := C 2 (if dm then E1 else E0); let K := fun (j : Nat) => (Pl.Col.f64 (C j E1) : Pl.Col Float); "
          "let fr : Pl.Frame Float := (if xm then [(\"has_delinquency\", (Pl.Col.str (List.replicate n (some \"x\")) : Pl.Col Float)), (\"age_category\", K 9)] else []) "
          "++ [(\"age\", K 0), (\"monthly_income\", K 1), (\"num_dependents\", Pl.Col.f64 dep), "
          "(\"num_late_30_59\", if im then Pl.Col.int (gI (s * 16 + 3) n 10 6 2) else K 3), (\"num_late_60_89\", K 4), (\"num_late_90_plus\", K 5), "
          "(\"credit_utilization\", K 6), (\"debt_ratio\", K 7), (\"num_credit_lines\", K 8)] "
          "++ (if xm then [(\"zz\", (Pl.Col.int (gI (s * 16 + 10) n 20 5 0) : Pl.Col Float))] else []); "
          f"let r := {unit} full fr; "
          "((if im then 2 else if dep.any (fun (o : Option Float) => (match o with | some x => x + 1.0 == 0.0 | none => false : Bool)) then 1 else 0 : Nat), dg (tR (r.drop LOGS)), W (LG r)); "
    )


def main():
    for suite, S0, row in SUITES:
        unit, carrier = row[0], row[1]
        st = Suite(suite)
        st.item, st.decl, st.carrier = f"def:{carrier}", carrier, "identity"
        gen = kept = 0
        raises_inside, dropped, rej = [], [], [0, 0]
        L = lets(unit)
        for b in range(NBLOCK):
            s0 = S0 + b * BLOCK
            dig = {0: [], 1: [], 2: []}
            lg = {0: [], 1: [], 2: []}
            for s in range(s0, s0 + BLOCK):
                cls, d, x = one(row, s)
                gen += 1
                if d is None:
                    (raises_inside if cls == 0 else dropped).append((s, x))
                    continue
                dig[cls].append(d)
                lg[cls].append(x)
            # a seed on which Python raises would have to be left out of the Lean range
            assert not raises_inside and not dropped, (raises_inside[:3], dropped[:3])
            kept += len(dig[0])
            rej[0] += len(dig[1])
            rej[1] += len(dig[2])
            body = (f"(let RS := (List.range {BLOCK}).map (fun (i : Nat) => ONE ({s0} + i)); "
                    "let M := fun (c : Nat) => W ((RS.filter (fun (p : Nat × Int × Int) => p.1 == c)).map (fun (p : Nat × Int × Int) => p.2.1)); "
                    "let G := fun (c : Nat) => W ((RS.filter (fun (p : Nat × Int × Int) => p.1 == c)).map (fun (p : Nat × Int × Int) => p.2.2)); "
                    "[M 0, M 1, M 2, G 0, G 1])")
            rng = f"seeds {s0}..{s0 + BLOCK - 1}"
            st.ints(L, body, [
                (f"{rng}: kept ({len(dig[0])} inputs)", unit, b4.w(dig[0]), {"fz": "kept", "covers": len(dig[0])}),
                (f"{rng}: rejected, num_dependents holds -1 ({len(dig[1])} inputs)", unit, b4.w(dig[1]), {"fz": "rejected", "covers": len(dig[1])}),
                (f"{rng}: rejected, num_late_30_59 is Int64 ({len(dig[2])} inputs)", unit, b4.w(dig[2]), {"fz": "rejected", "covers": len(dig[2])}),
                (f"{rng}: kept, the four log columns without their low 20 bits", unit, b4.w(lg[0]), {"fz": "kept", "covers": 0}),
                (f"{rng}: rejected (-1), the four log columns without their low 20 bits", unit, b4.w(lg[1]), {"fz": "rejected", "covers": 0}),
            ], gen=True)
        st.write()
        for i, inp in enumerate(st.inputs):
            (WORK / f"{suite}.in{i}.txt").write_text(inp["text"])
        (WORK / f"{suite}.fuzz.json").write_text(json.dumps({
            "fuzzer": "port-translator-7", "generator": "diffeval/units/fz_t5t9_gen.py",
            "units": {unit: {"seeds": f"{S0}..{S0 + NBLOCK * BLOCK - 1}", "generated": gen, "kept": kept,
                             "python_raises_inside_precondition": [s for s, _ in raises_inside],
                             "note": (f"one case = the fold over the seeds of one class in a block of {BLOCK} seeds of the digest of the result without "
                                      "the four log columns (and, as a second case, of the log columns without their low 20 bits); pools: 0-40 rows; "
                                      "per column 40-70 % from the edge pool (null, NaN, +-inf, +-0.0, +-1e300, 1e-300, +-5e-324, -1 and one ulp either side, "
                                      "every threshold 25 30 35 43 50 60 65 75 100 200 500 2500 2 3 1 exactly and one ulp either side), all-null columns, "
                                      "full true and false, created columns already present with another dtype; "
                                      f"rejected inputs on which Python returns: {rej[0]} with -1 in num_dependents, {rej[1]} with an Int64 num_late_30_59")}}}))
        print(f"{suite}: generated {gen}, kept {kept} ({kept / gen:.3f}); rejected -1: {rej[0]}, Int64: {rej[1]}; "
              f"input sizes {[len(i['text']) for i in st.inputs]}")


if __name__ == "__main__":
    main()
