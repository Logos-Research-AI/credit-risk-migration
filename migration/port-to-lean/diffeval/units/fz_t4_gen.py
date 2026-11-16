"""Fuzz pass 2026-11-16 (prompts/fuzz-2026-11-16.md), by port-translator-6 (reviewer of T4), on
  def:fe_run_02b_medians_all (+_precond)   credit_risk/feature_engineering.py:179-186
  def:fe_run_04_imputed      (+_precond)   credit_risk/feature_engineering.py:208-229

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_t4_gen.py
      -> diffeval/work/fz_t4_02b, fz_t4_04 (.json, .inputs.json, .fuzz.json)
  eval_decl each input on def:zz_carrier_f / zz_carrier_f; python3 diffeval/fuzz_collect.py 6 fz_t4_02b fz_t4_04;
  compare.py on each; python3 diffeval/fuzz_receipt.py fz_t4_02b fz_t4_04

Inputs are built inside Lean from the seed with kit.GEN (gF, gI, hsh) and mirrored here with
kit.gF / kit.gI / kit.hsh; nothing is typed. Expected values: the source lines of the package,
read from the file at run time and executed verbatim (experiments/rev_t4_probe.py: py02b, py04).
The seeds go in blocks of 64. One case is the digest of the results of the seeds of a block that
the precondition admits (56 of them, "kept") or rejects (8, "rejected"), concatenated in seed
order; a third integer per block is the digest of all 64 generated inputs (primitive "input": it
shows that the Python mirror builds the frames Lean builds).

The seed's shape number is s % 8; shape 7 is built to fall outside the precondition.

def:fe_run_02b_medians_all, per seed s:
  income_medians: 0..7 rows; age_group Int32 from gI (10 % null, values -1..6: duplicates, a null
    key, keys outside 1..5, absent groups); median_income Float64 from gF (50 % from the edge pool);
    shape 5: a Float64 column overall_median_income in front (replaced in place by the step).
  credit_raw_clean: MonthlyIncome with 0, 1, 2, 3, 4, 5, 8, 13 or 30 rows, Float64 from gF (60 % from
    the edge pool, exponents -30..30); shape 7: an Int64 column (the median exists in Python; the
    precondition asks for Float64).
  Precondition as rendered (pre02b): names of each frame distinct; all columns of one length
    (true of any polars frame); income_medians has an integer age_group; credit_raw_clean has a
    Float64 MonthlyIncome.
def:fe_run_04_imputed, per seed s:
  credit_cleaned: 1, 2, 3, 5, 9 or 20 rows; the 12 Float64 columns from gF (60 % edge pool,
    exponents -12..12); age_group Int32 from gI (10 % null, -1..6); MonthlyIncome_missing and
    Dependents_missing Int64 from gI (10 % null, 0..2); shape 6: a Float64 column median_income
    of its own (the right one becomes median_income_right). Shape 7: no row (s % 16 == 7), or
    MonthlyIncome_missing as a Float64 column (s % 16 == 15).
  income_medians_all: 0..6 rows; age_group Int32 from gI (10 % null, 0..6: duplicates, 0 and 6
    match nothing useful, groups absent); median_income and overall_median_income Float64 from gF
    (50 % edge pool); shape 4: columns in the order overall, median, key; shape 5: an extra Float64
    column MonthlyIncome (renamed MonthlyIncome_right by the join).
  Precondition as rendered (pre04): names distinct in each frame; 0 < height of credit_cleaned;
    integer age_group on both sides; for each right column other than the key that is also a left
    column, `<name>_right` is in neither frame; median_income and overall_median_income Float64
    after the join and in income_medians_all; MonthlyIncome Float64; the two flags integer; the two
    `* 100` columns and the nine columns selected as they are Float64.
Edge pool E (both units): null (twice), NaN, +inf, -inf, +0.0, -0.0, 1e300, 1e-300, 5e-324, 1.0
(twice), 2.0, 3.0, 5000.0 (twice), 5400.5, 1016.85, 7098.24, -1.0, 0.01, 1.0 +- one ulp.
"""
from __future__ import annotations

import json
import math
import struct
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[1] / "experiments"))

import compare as cmp  # noqa: E402
import kit  # noqa: E402
import rev_t4_probe as rp  # noqa: E402  (py02b, py04: the source lines executed verbatim)
from suite import WORK, Suite  # noqa: E402

nan, inf = float("nan"), float("inf")
CARRIER = ("def:zz_carrier_f", "zz_carrier_f")
BLOCK = 64
E = [None, None, nan, inf, -inf, 0.0, -0.0, 1e300, 1e-300, 5e-324, 1.0, 1.0, 2.0, 3.0, 5000.0, 5000.0, 5400.5, 1016.85,
     7098.24, -1.0, 0.01, math.nextafter(1.0, 2.0), math.nextafter(1.0, 0.0)]
FN = ["VAR1", "SeriousDlqin2yrs", "age", "RevolvingUtilizationOfUnsecuredL", "NumberOfTime30-59DaysPastDueNotW", "DebtRatio",
      "NumberOfOpenCreditLinesAndLoans", "NumberOfTimes90DaysLate", "NumberRealEstateLoansOrLines",
      "NumberOfTime60-89DaysPastDueNotW", "MonthlyIncome", "NumberOfDependents"]
NS2, NS4 = [0, 1, 2, 3, 4, 5, 8, 13, 30], [1, 2, 3, 5, 9, 20]


def fb(x: float) -> int:
    return struct.unpack("<Q", struct.pack("<d", x))[0]


E_LEAN = "[" + ", ".join("none" if x is None else "some (0.0 / 0.0)" if x != x else f"some (Float.ofBits {fb(x)})" for x in E) + "]"
COMMON = (f"let E : List (Option Float) := {E_LEAN}; "
          "let nr := fun (s k m : Nat) => (hsh s k % m.toUInt64).toNat; let EX : List Nat := EXCL; "
          "let F := fun (s n : Nat) (pe eh : UInt64) => (Pl.Col.f64 (gF s n pe eh E) : Pl.Col Float); "
          "let J := fun (s n : Nat) (m : UInt64) (off : Int) => (Pl.Col.int (gI s n 10 m off) : Pl.Col Float); "
          "let sd := fun (a : Nat) (kept : Bool) => ((List.range 64).map (fun (i : Nat) => a + i)).filter (fun (s : Nat) => ((s % 8 != 7) == kept) && !(EX.contains s)); ")


def nr(s: int, k: int, m: int) -> int:
    return kit.hsh(s, k) % m


def F(s, n, pe, eh):
    return pl.Series(kit.gF(s, n, pe, eh, E), dtype=pl.Float64)


def J(s, n, m, off, dtype=pl.Int32):
    return pl.Series(kit.gI(s, n, 10, m, off), dtype=dtype)


def kind(df: pl.DataFrame, n: str) -> str | None:
    if n not in df.columns:
        return None
    t = df.schema[n]
    return "f64" if t == pl.Float64 else "int" if t in (pl.Int32, pl.Int64) else "other"


# ---------------------------------------------------------------- 02b
L02 = (
    'let mkI := fun (s : Nat) => (let n := nr s 900 8; let b : Pl.Frame Float := [("age_group", J (3 * s) n 8 1), ("median_income", F (3 * s + 1) n 50 20)]; '
    'if s % 8 == 5 then ("overall_median_income", F (3 * s + 1) n 30 5) :: b else b : Pl.Frame Float); '
    'let mkC := fun (s : Nat) => (let n := [0, 1, 2, 3, 4, 5, 8, 13, 30].getD (nr s 901 9) 0; '
    '[("MonthlyIncome", (if s % 8 == 7 then Pl.Col.int (gI (3 * s + 2) n 20 9 2) else F (3 * s + 2) n 60 30 : Pl.Col Float))] : Pl.Frame Float); '
    "let run := fun (s : Nat) => fe_run_02b_medians_all (mkI s) (mkC s); let inp := fun (s : Nat) => tR (mkI s) ++ tR (mkC s); "
)


def mk02(s: int) -> tuple[pl.DataFrame, pl.DataFrame]:
    n = nr(s, 900, 8)
    cols = {"age_group": J(3 * s, n, 8, 1), "median_income": F(3 * s + 1, n, 50, 20)}
    if s % 8 == 5:
        cols = {"overall_median_income": F(3 * s + 1, n, 30, 5)} | cols
    m = NS2[nr(s, 901, 9)]
    mi = pl.Series(kit.gI(3 * s + 2, m, 20, 9, 2), dtype=pl.Int64) if s % 8 == 7 else F(3 * s + 2, m, 60, 30)
    return pl.DataFrame(cols), pl.DataFrame({"MonthlyIncome": mi})


def pre02b(im: pl.DataFrame, crc: pl.DataFrame) -> bool:
    return (len(set(im.columns)) == len(im.columns) and len(set(crc.columns)) == len(crc.columns)
            and kind(im, "age_group") == "int" and kind(crc, "MonthlyIncome") == "f64")


# ---------------------------------------------------------------- 04
L04 = (
    "let FN : List String := [" + ", ".join(f'"{n}"' for n in FN) + "]; "
    "let mkL := fun (s : Nat) => (let n := if s % 16 == 7 then 0 else [1, 2, 3, 5, 9, 20].getD (nr s 900 6) 1; "
    "let fl : Pl.Col Float := if s % 16 == 15 then Pl.Col.f64 ((gI (32 * s + 21) n 10 3 0).map (fun (o : Option Int) => o.map Float.ofInt)) else J (32 * s + 21) n 3 0; "
    'let b : Pl.Frame Float := (List.range 12).map (fun (j : Nat) => (FN.getD j "", F (32 * s + j) n 60 12)) ++ '
    '[("age_group", J (32 * s + 20) n 8 1), ("MonthlyIncome_missing", fl), ("Dependents_missing", J (32 * s + 22) n 3 0)]; '
    'if s % 8 == 6 then b ++ [("median_income", F (32 * s + 23) n 60 12)] else b : Pl.Frame Float); '
    'let mkR := fun (s : Nat) => (let k := nr s 901 7; let a : String × Pl.Col Float := ("age_group", J (32 * s + 24) k 7 0); '
    'let m : String × Pl.Col Float := ("median_income", F (32 * s + 25) k 50 12); let o : String × Pl.Col Float := ("overall_median_income", F (32 * s + 26) k 50 12); '
    'if s % 8 == 4 then [o, m, a] else if s % 8 == 5 then [a, ("MonthlyIncome", F (32 * s + 27) k 50 12), m, o] else [a, m, o] : Pl.Frame Float); '
    "let run := fun (s : Nat) => fe_run_04_imputed (mkL s) (mkR s); let inp := fun (s : Nat) => tR (mkL s) ++ tR (mkR s); "
)


def mk04(s: int) -> tuple[pl.DataFrame, pl.DataFrame]:
    n = 0 if s % 16 == 7 else NS4[nr(s, 900, 6)]
    cols = {FN[j]: F(32 * s + j, n, 60, 12) for j in range(12)}
    cols["age_group"] = J(32 * s + 20, n, 8, 1)
    fl = J(32 * s + 21, n, 3, 0, pl.Int64)
    cols["MonthlyIncome_missing"] = fl.cast(pl.Float64) if s % 16 == 15 else fl
    cols["Dependents_missing"] = J(32 * s + 22, n, 3, 0, pl.Int64)
    if s % 8 == 6:
        cols["median_income"] = F(32 * s + 23, n, 60, 12)
    k = nr(s, 901, 7)
    a, m, o = J(32 * s + 24, k, 7, 0), F(32 * s + 25, k, 50, 12), F(32 * s + 26, k, 50, 12)
    if s % 8 == 4:
        r = {"overall_median_income": o, "median_income": m, "age_group": a}
    elif s % 8 == 5:
        r = {"age_group": a, "MonthlyIncome": F(32 * s + 27, k, 50, 12), "median_income": m, "overall_median_income": o}
    else:
        r = {"age_group": a, "median_income": m, "overall_median_income": o}
    return pl.DataFrame(cols), pl.DataFrame(r)


def pre04(cc: pl.DataFrame, ima: pl.DataFrame) -> bool:
    if len(set(cc.columns)) != len(cc.columns) or len(set(ima.columns)) != len(ima.columns) or cc.height == 0:
        return False
    if kind(cc, "age_group") != "int" or kind(ima, "age_group") != "int":
        return False
    for n in ima.columns:
        if n != "age_group" and n in cc.columns and (n + "_right" in cc.columns or n + "_right" in ima.columns):
            return False
    # the column read after the join under a name: the left one when the left frame has it
    after = lambda n: kind(cc, n) if n in cc.columns else kind(ima, n)  # noqa: E731
    if after("median_income") != "f64" or after("overall_median_income") != "f64":
        return False
    if kind(ima, "median_income") != "f64" or kind(ima, "overall_median_income") != "f64" or kind(cc, "MonthlyIncome") != "f64":
        return False
    if kind(cc, "MonthlyIncome_missing") != "int" or kind(cc, "Dependents_missing") != "int":
        return False
    return all(kind(cc, n) == "f64" for n in FN)


# ---------------------------------------------------------------- suites
def toks(df: pl.DataFrame) -> list[int]:
    return cmp.tokens(cmp.canon_frame(df))


def build(name: str, unit: str, lets: str, mk, py, pre, s0: int, blocks: int, per_call: int, note: str, limit: str | None = None):
    s = Suite(name)
    s.item, s.decl = CARRIER
    gen, kept_n, raises_in, dropped = 0, 0, [], 0
    res: dict[int, list[int] | None] = {}
    admit: dict[int, bool] = {}
    inp: dict[int, list[int]] = {}
    for seed in range(s0, s0 + BLOCK * blocks):
        a, b = mk(seed)
        gen += 1
        admit[seed] = pre(a, b)
        assert admit[seed] == (seed % 8 != 7), (name, seed, "shape 7 is the only one built outside the precondition")
        inp[seed] = toks(a) + toks(b)
        try:
            res[seed] = toks(py(a, b))
        except Exception as e:  # noqa: BLE001
            res[seed] = None
            if admit[seed]:
                raises_in.append(seed)
                print(f"[{name}] seed {seed}: Python raises inside the precondition: {type(e).__name__}: {str(e)[:120]}")
            else:
                dropped += 1
        if admit[seed] and res[seed] is not None:
            kept_n += 1
    excl = sorted(sd for sd, r in res.items() if r is None)
    common = COMMON.replace("EXCL", "[" + ", ".join(map(str, excl)) + "]")
    for c0 in range(0, blocks, per_call):
        cs = list(range(c0, min(c0 + per_call, blocks)))
        cases = []
        for bk in cs:
            a = s0 + BLOCK * bk
            seeds = [x for x in range(a, a + BLOCK) if res[x] is not None]
            k = [x for x in seeds if admit[x]]
            r = [x for x in seeds if not admit[x]]
            cases.append((f"seeds {a}..{a + BLOCK - 1} kept", unit, cmp.digest([t for x in k for t in res[x]]), {"fz": "kept", "covers": len(k)}))
            cases.append((f"seeds {a}..{a + BLOCK - 1} rejected", unit, cmp.digest([t for x in r for t in res[x]]), {"fz": "rejected", "covers": len(r)}))
            cases.append((f"seeds {a}..{a + BLOCK - 1} inputs", "input", cmp.digest([t for x in range(a, a + BLOCK) for t in inp[x]]), {"fz": "rejected", "covers": 0}))
        body = (f"((List.range {len(cs)}).flatMap (fun (b : Nat) => let a := {s0 + BLOCK * c0} + 64 * b; "
                "[dg ((sd a true).flatMap (fun (s : Nat) => tR (run s))), dg ((sd a false).flatMap (fun (s : Nat) => tR (run s))), "
                "dg (((List.range 64).map (fun (i : Nat) => a + i)).flatMap inp)]))")
        s.ints(common + lets, body, cases, gen=True)
    s.write()
    fz = {"fuzzer": "port-translator-6", "generator": "diffeval/units/fz_t4_gen.py",
          "units": {unit: {"seeds": f"{s0}..{s0 + BLOCK * blocks - 1}", "generated": gen, "kept": kept_n,
                           "python_raises_inside_precondition": raises_in, "note": note}}}
    if limit:
        fz["units"][unit]["all_differences_are_recorded_limit"] = limit
    (WORK / f"{name}.fuzz.json").write_text(json.dumps(fz, indent=1))
    print(f"[{name}] generated {gen}, kept {kept_n} ({kept_n / gen:.3f}), Python raises inside {len(raises_in)}, rejected and raising (dropped) {dropped}")
    print("   input sizes", [len(i["text"]) for i in s.inputs])


if __name__ == "__main__":
    build("fz_t4_02b", "fe_run_02b_medians_all", L02, mk02, rp.py02b, pre02b, 10000, 40, 20,
          "one case = one block of 64 seeds (56 inside the precondition, 8 outside: Int64 MonthlyIncome); income_medians 0..7 rows, "
          "keys -1..6 with nulls and duplicates, an existing overall_median_income column (shape 5); MonthlyIncome 0..30 rows; "
          "edge pool: null, NaN, +-inf, +-0.0, 1e300, 1e-300, 5e-324, ties (1.0, 5000.0), 1.0 +- 1 ulp; source lines executed verbatim",
          limit="the sign of a zero in the median (RULEBOOK section 6): seeds 11164 and 11214, the only two of block 11152..11215 "
                "that differ when the block is evaluated seed by seed; overall_median_income is 0.0 in Python and -0.0 in Lean, or the "
                "reverse; minimal input of 17 known incomes [0.0, -1.0 x7, 1.0, -0.0, 1.0 x7] (experiments/fz_t4_zero_median_min.py)")
    build("fz_t4_04", "fe_run_04_imputed", L04, mk04, rp.py04, pre04, 20000, 40, 10,
          "one case = one block of 64 seeds (56 inside the precondition, 8 outside: no row, or a Float64 MonthlyIncome_missing); "
          "credit_cleaned 1..20 rows, keys -1..6 with nulls, flags 0..2 with nulls, its own median_income column (shape 6); "
          "income_medians_all 0..6 rows, keys 0..6 with nulls and duplicates, other column order (shape 4), an extra MonthlyIncome "
          "column (shape 5); edge pool: null, NaN, +-inf, +-0.0, 1e300, 1e-300, 5e-324, ties, 1.0 +- 1 ulp; source lines executed verbatim")
