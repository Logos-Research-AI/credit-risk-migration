"""Fuzz pass 2026-11-16 by port-translator-9 on the three units it reviewed (written by
port-translator-8): predict_run_01_clean, predict_run_02_medians, predict_run_04_imputed.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_t8_gen.py [per_call]
      -> diffeval/work/fz_p01.json, fz_p02.json, fz_p04.json (+ .inputs.json, .fuzz.json)
  eval on def:zz_carrier_p; python3 diffeval/fuzz_collect.py 9 fz_p01 fz_p02 fz_p04; compare.py; fuzz_receipt.py.
  `--one <unit> <seed>`: prints the generated input of one seed, the Python result and a tokens input.

Inputs are built inside Lean from the seed (kit.GEN: hsh, gF, gI) and mirrored here value for value
(`gen01`, `gen02`, `gen04` next to the Lean text `L01`, `L02`, `L04`). Stream of a seed s: s * 1000 + k.
Expected values: the source lines of predict.py executed (192-206, 211-222, 247-271), as in
t8_edges_gen.py / rv_t8_gen.py. One Lean case digests up to 25 seeds (`covers`): kept seeds in seed
order; rejected seeds (Python returns) grouped by the first precondition clause that fails.

Preconditions rendered in Python (`pre01`, `pre02`, `pre04`), clause by clause from the items:
  01  names distinct and one length: true of any pl.DataFrame; MonthlyIncome / NumberOfDependents
      present and Float64 or String (dtype test); input_best32 returns a Float64 column of the
      frame's height: checked on the real function's result.
  02  table not empty (height > 0); rows of one shape: true of a frame; names distinct: true of a
      frame (a draw with a repeated name cannot be built: counted as "Python raises", dropped);
      names ASCII (every character < 128).
  04  both frames well formed: true of frames; left age_group Int64; right age_group present and
      Float64; no `<name>_right` clash for a right name the left has; median_income and
      overall_median_income of the JOINED frame present and Float64 (the left's own column when it
      has one, else the right's under its joined name); MonthlyIncome_missing Int64; MonthlyIncome,
      RevolvingUtilizationOfUnsecuredL, DebtRatio Float64; the nine only-selected columns present.

Doubles of step 01: sb (sas_best12) = table bits -> text of the real function over the float pool;
ib (input_best32) = table text -> value of the real function over the string pool and sb's texts.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
import rv_t8_gen as rv  # noqa: E402
import t8_edges_gen as e8  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import sas_compat as sc  # noqa: E402

CARRIER = ("def:zz_carrier_p", "zz_carrier_p")
nan, inf = float("nan"), float("inf")
H = kit.hsh
F64, I64, STR = pl.Float64, pl.Int64, pl.String


def lof(xs) -> str:
    return "[" + ", ".join("none" if x is None else f"some {lt.lean_float(x)}" for x in xs) + "]"


def lstrs(xs) -> str:
    return "[" + ", ".join(lt.lean_str(x) for x in xs) + "]"


def fcol(vals):
    return pl.Series(vals, dtype=F64, nan_to_null=False)


def rot(xs, r):
    return xs[r:] + xs[:r]


# ------------------------------------------------------------------ pools
E = [None, nan, inf, -inf, 0.0, -0.0, 1e300, 1e-300, 5e-324, 1.0, 100.0, 0.07, 0.29, 1.7976931348623157e308, -1e306, 3.0]
EK = [None, 1.0, 2.0, 3.0, 4.0, 5.0, 0.0, -0.0, nan, 6.0, 2.5, inf, 1.0, 2.0, 3.0]
S4 = ["", "7", "x", "NA"]

# ------------------------------------------------------------------ unit 04
LN = ["VAR1", "age", "NumberOfDependents", "NumberOfTime30-59DaysPastDueNotW", "NumberOfTime60-89DaysPastDueNotW",
      "NumberOfTimes90DaysLate", "NumberOfOpenCreditLinesAndLoans", "NumberRealEstateLoansOrLines", "MonthlyIncome",
      "RevolvingUtilizationOfUnsecuredL", "DebtRatio"]
XN = ["median_income", "overall_median_income", "x", "t", "y", "age_group_right"]
RN = ["x", "age", "VAR1", "t", "MonthlyIncome", "NumberOfDependents", "age_group_right"]

L04 = (
    f"let E : List (Option Float) := {lof(E)}; let EK : List (Option Float) := {lof(EK)}; "
    f"let S4 : List String := {lstrs(S4)}; let LN : List String := {lstrs(LN)}; let XN : List String := {lstrs(XN)}; "
    f"let RN : List String := {lstrs(RN)}; "
    "let sc := fun (s n : Nat) => (Pl.Col.str ((gI s n 20 4 0).map (fun (o : Option Int) => o.map (fun (k : Int) => S4.getD k.toNat \"\"))) : Pl.Col Float); "
    "let mkL := fun (s : Nat) => (let q := s * 1000; let r := (hsh q 800 % 10).toNat; let n := if r < 2 then r else (hsh q 801 % 12).toNat + 2; "
    "let u := hsh q 802 % 20; "
    "let base : Pl.Frame Float := (List.range 11).map (fun (j : Nat) => (LN.getD j \"\", if u == 3 && j == 8 then sc (q + 140) n else Pl.Col.f64 (gF (q + 100 + j) n 50 3 E))); "
    "let ag : Pl.Col Float := if u == 0 then Pl.Col.f64 (gF (q + 120) n 60 2 EK) else Pl.Col.int (gI (q + 120) n 8 8 1); "
    "let mm : Pl.Col Float := if u == 1 then Pl.Col.f64 (gF (q + 121) n 70 1 EK) else Pl.Col.int (gI (q + 121) n 10 3 0); "
    "let x0 := (hsh q 804 % 5).toNat; "
    "let ex : Pl.Frame Float := (List.range ((hsh q 803 % 4).toNat - 1)).map (fun (j : Nat) => (XN.getD ((x0 + j) % 6) \"\", Pl.Col.f64 (gF (q + 130 + j) n 40 3 E))); "
    "(base ++ [(\"age_group\", ag), (\"MonthlyIncome_missing\", mm), (\"Dependents_missing\", Pl.Col.int (gI (q + 122) n 10 2 0))] ++ ex : Pl.Frame Float)); "
    "let mkR := fun (s : Nat) => (let q := s * 1000; let m := (hsh q 850 % 8).toNat; let v := hsh q 851 % 20; let x0 := (hsh q 853 % 6).toNat; "
    "let cols : Pl.Frame Float := [(\"age_group\", if v == 0 then Pl.Col.int (gI (q + 160) m 10 7 0) else Pl.Col.f64 (gF (q + 160) m 85 2 EK)), "
    "(\"median_income\", if v == 1 then sc (q + 161) m else Pl.Col.f64 (gF (q + 161) m 50 3 E)), "
    "(\"overall_median_income\", if v == 2 then sc (q + 162) m else Pl.Col.f64 (gF (q + 162) m 50 3 E))] ++ "
    "(List.range (hsh q 852 % 3).toNat).map (fun (j : Nat) => (RN.getD ((x0 + j) % 7) \"\", Pl.Col.f64 (gF (q + 170 + j) m 40 3 E))); "
    "let r := (hsh q 854).toNat % cols.length; "
    "(List.filter (fun (p : String × Pl.Col Float) => !((v == 3 && p.1 == \"median_income\") || (v == 4 && p.1 == \"overall_median_income\"))) (List.drop r cols ++ List.take r cols) : Pl.Frame Float)); "
    "let U := fun (s : Nat) => predict_run_04_imputed (mkL s) (mkR s); "
)


def scol(s, n):
    return pl.Series([None if k is None else S4[k] for k in kit.gI(s, n, 20, 4, 0)], dtype=STR)


def gen04(s: int):
    q = s * 1000
    r = H(q, 800) % 10
    n = r if r < 2 else H(q, 801) % 12 + 2
    u = H(q, 802) % 20
    cols = [(LN[j], scol(q + 140, n) if u == 3 and j == 8 else fcol(kit.gF(q + 100 + j, n, 50, 3, E))) for j in range(11)]
    ag = fcol(kit.gF(q + 120, n, 60, 2, EK)) if u == 0 else pl.Series(kit.gI(q + 120, n, 8, 8, 1), dtype=I64)
    mm = fcol(kit.gF(q + 121, n, 70, 1, EK)) if u == 1 else pl.Series(kit.gI(q + 121, n, 10, 3, 0), dtype=I64)
    x0 = H(q, 804) % 5
    ex = [(XN[(x0 + j) % 6], fcol(kit.gF(q + 130 + j, n, 40, 3, E))) for j in range(max(H(q, 803) % 4 - 1, 0))]
    cols += [("age_group", ag), ("MonthlyIncome_missing", mm), ("Dependents_missing", pl.Series(kit.gI(q + 122, n, 10, 2, 0), dtype=I64))] + ex
    left = pl.DataFrame(dict(cols))
    m = H(q, 850) % 8
    v = H(q, 851) % 20
    x0 = H(q, 853) % 6
    rc = [("age_group", pl.Series(kit.gI(q + 160, m, 10, 7, 0), dtype=I64) if v == 0 else fcol(kit.gF(q + 160, m, 85, 2, EK))),
          ("median_income", scol(q + 161, m) if v == 1 else fcol(kit.gF(q + 161, m, 50, 3, E))),
          ("overall_median_income", scol(q + 162, m) if v == 2 else fcol(kit.gF(q + 162, m, 50, 3, E)))]
    rc += [(RN[(x0 + j) % 7], fcol(kit.gF(q + 170 + j, m, 40, 3, E))) for j in range(H(q, 852) % 3)]
    rc = rot(rc, H(q, 854) % len(rc))
    rc = [p for p in rc if not ((v == 3 and p[0] == "median_income") or (v == 4 and p[0] == "overall_median_income"))]
    return left, pl.DataFrame(dict(rc))


def pre04(inp) -> str | None:
    """None when the precondition admits, else the first failing clause."""
    left, right = inp
    ls, rs = left.schema, right.schema
    if ls["age_group"] != I64:
        return "left age_group not integer"
    if rs.get("age_group") != F64:
        return "right age_group absent or not Float64"
    for p in right.columns:
        if p in ls and (p + "_right" in ls or p + "_right" in rs):
            return "_right clash"

    def joined(nm):
        if nm in ls:
            return ls[nm]
        for p in right.columns:
            if (p + "_right" if p in ls else p) == nm:
                return rs[p]
        return None

    if joined("median_income") != F64:
        return "joined median_income absent or not Float64"
    if joined("overall_median_income") != F64:
        return "joined overall_median_income absent or not Float64"
    if ls["MonthlyIncome_missing"] != I64:
        return "MonthlyIncome_missing not integer"
    for c in ("MonthlyIncome", "RevolvingUtilizationOfUnsecuredL", "DebtRatio"):
        if ls[c] != F64:
            return f"{c} not Float64"
    return None


# ------------------------------------------------------------------ unit 02
NP = ["age_group", "AGE_GROUP", "Age_Group", "aGE_GROUP", "median_income", "MEDIAN_INCOME", "Median_Income", "overall_median_income",
      "OVERALL_MEDIAN_INCOME", "Overall_Median_Income", "overall_median_incomE", "x", "X", "age", "VAR1", "median_ıncome", "",
      "age_group ", "AGE_GROUPS", "m", "median_income_right", "Age_group", "MEDIAN_income"]
assert len(NP) == 23 and len(set(NP)) == 23
L02 = (
    f"let E : List (Option Float) := {lof(E)}; let NP : List String := {lstrs(NP)}; "
    "let mkT := fun (s : Nat) => (let q := s * 1000; let nc := (hsh q 900 % 5).toNat + 1; let h := (hsh q 901 % 8).toNat; let nr := if h == 0 then 0 else h % 3 + 1; "
    "let i0 := (hsh q 902 % 23).toNat; let st := if hsh q 905 % 12 == 0 then 0 else (hsh q 903 % 22).toNat + 1; "
    "let names := (List.range nc).map (fun (j : Nat) => NP.getD ((i0 + j * st) % 23) \"\"); "
    "let cells := (List.range nc).map (fun (j : Nat) => (if hsh q (910 + j) % 4 == 0 then "
    "(gI (q + 50 + j) nr 20 23 0).map (fun (o : Option Int) => Tabular.Cell.str (o.map (fun (k : Int) => NP.getD k.toNat \"\"))) else "
    "(gF (q + 70 + j) nr 50 3 E).map (fun (o : Option Float) => Tabular.Cell.num o) : List (Tabular.Cell Float))); "
    "((List.range nr).map (fun (i : Nat) => (List.range nc).map (fun (j : Nat) => (names.getD j \"\", (cells.getD j []).getD i (Tabular.Cell.num none)))) : Tabular.Table Float)); "
    "let U := fun (s : Nat) => predict_run_02_medians (mkT s); "
)


def gen02(s: int):
    q = s * 1000
    nc = H(q, 900) % 5 + 1
    h = H(q, 901) % 8
    nr = 0 if h == 0 else h % 3 + 1
    i0 = H(q, 902) % 23
    st = 0 if H(q, 905) % 12 == 0 else H(q, 903) % 22 + 1
    names = [NP[(i0 + j * st) % 23] for j in range(nc)]
    cols = []
    for j in range(nc):
        if H(q, 910 + j) % 4 == 0:
            cols.append(pl.Series([None if k is None else NP[k] for k in kit.gI(q + 50 + j, nr, 20, 23, 0)], dtype=STR))
        else:
            cols.append(fcol(kit.gF(q + 70 + j, nr, 50, 3, E)))
    if len(set(names)) != len(names):
        raise ValueError("repeated name: not a frame")
    return pl.DataFrame(dict(zip(names, cols, strict=True)))


def pre02(df) -> str | None:
    if df.height == 0:
        return "table with no row"
    if any(ord(c) >= 128 for n in df.columns for c in n):
        return "non-ASCII name"
    return None


# ------------------------------------------------------------------ unit 01
FP = [nan, inf, -inf, 0.0, -0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 1234567890123.0, 0.1, 5400.0, 1e300, 1e-300, 5e-324, -1e-7,
      123456789012.5, 99999999999.95, 1e12, 0.000012345678901234, -1234567.891, 9007199254740992.0, 1e15]
SP = ["", ".", "NA", "na", " ", "5400", " 3 ", "+7", "-2", "1e2", "1E-3", "x", "1,000", "0x10", ".5", "5.", "-", "+", "--1", "1 2",
      "NaN", "inf", "12345678901234567890", "0"]
ON = ["VAR1", "z", "MonthlyIncome_num", "NumberOfDependents_num", "age"]
assert len(FP) == 24 and len(SP) == 24


def doubles01() -> str:
    sb = {lt.bits(x): sc.sas_best12(x) for x in FP}
    texts = list(dict.fromkeys(SP + list(sb.values())))
    vals = pl.DataFrame({"v": texts}, schema={"v": STR}).select(sc.input_best32(pl.col("v")))["v"].to_list()
    ibt = "[" + ", ".join(f"({lt.lean_str(k)}, {'none' if v is None else 'some ' + str(lt.bits(v))})" for k, v in zip(texts, vals, strict=True)) + "]"
    sbt = "[" + ", ".join(f"({k}, {lt.lean_str(v)})" for k, v in sb.items()) + "]"
    return (
        f"let IT : List (String × Option UInt64) := {ibt}; let ST : List (UInt64 × String) := {sbt}; "
        "let ib := fun (e : Pl.Expr Float) => (({ eval := fun (g : Option (List (List Nat))) (fr : Pl.Frame Float) => "
        "(match e.eval g fr with | .str v => Pl.Col.f64 (v.map (fun (o : Option String) => (match o with | none => none | some s => "
        "(match IT.lookup s with | some r => r.map Float.ofBits | none => some (-777.0)) : Option Float))) | _ => Pl.Col.f64 []), "
        "name := e.name, ser := Pl.node [e.ser] }) : Pl.Expr Float); "
        "let sb := fun (o : Option Float) => ((match o with | none => \"!none\" | some x => (match ST.lookup x.toBits with | some s => s | none => \"?\")) : String); "
    )


L01 = (
    f"let FP : List Float := [{', '.join(lt.lean_float(x) for x in FP)}]; let SP : List String := {lstrs(SP)}; let ON : List String := {lstrs(ON)}; "
    + doubles01()
    + "let mkC := fun (s n : Nat) (k pn : UInt64) => (if k == 0 then Pl.Col.f64 ((gI s n pn 24 0).map (fun (o : Option Int) => o.map (fun (i : Int) => FP.getD i.toNat 0.0))) "
    "else if k == 1 then Pl.Col.str ((gI s n pn 24 0).map (fun (o : Option Int) => o.map (fun (i : Int) => SP.getD i.toNat \"\"))) else Pl.Col.int (gI s n pn 6 0) : Pl.Col Float); "
    "let kd := fun (h : UInt64) => (if h % 20 == 0 then 2 else (h >>> 9) % 2 : UInt64); "
    "let mkF := fun (s : Nat) => (let q := s * 1000; let r := (hsh q 700 % 10).toNat; let n := if r < 2 then r else (hsh q 701 % 8).toNat + 2; "
    "let pn : UInt64 := if hsh q 710 % 8 == 0 then 100 else 15; let o0 := (hsh q 702 % 5).toNat; "
    "let cols : Pl.Frame Float := [(\"MonthlyIncome\", mkC (q + 200) n (kd (hsh q 703)) pn), (\"NumberOfDependents\", mkC (q + 201) n (kd (hsh q 704)) 15)] ++ "
    "(List.range (hsh q 706 % 4).toNat).map (fun (j : Nat) => (ON.getD ((o0 + j) % 5) \"\", mkC (q + 210 + j) n ((hsh q (720 + j)) % 2) 15)); "
    "let r := (hsh q 709).toNat % cols.length; (List.drop r cols ++ List.take r cols : Pl.Frame Float)); "
    "let U := fun (s : Nat) => predict_run_01_clean ib sb (mkF s); "
)


def mkc(s, n, k, pn):
    if k == 0:
        return fcol([None if i is None else FP[i] for i in kit.gI(s, n, pn, 24, 0)])
    if k == 1:
        return pl.Series([None if i is None else SP[i] for i in kit.gI(s, n, pn, 24, 0)], dtype=STR)
    return pl.Series(kit.gI(s, n, pn, 6, 0), dtype=I64)


def kd(h):
    return 2 if h % 20 == 0 else (h >> 9) % 2


def gen01(s: int):
    q = s * 1000
    r = H(q, 700) % 10
    n = r if r < 2 else H(q, 701) % 8 + 2
    pn = 100 if H(q, 710) % 8 == 0 else 15
    o0 = H(q, 702) % 5
    cols = [("MonthlyIncome", mkc(q + 200, n, kd(H(q, 703)), pn)), ("NumberOfDependents", mkc(q + 201, n, kd(H(q, 704)), 15))]
    cols += [(ON[(o0 + j) % 5], mkc(q + 210 + j, n, H(q, 720 + j) % 2, 15)) for j in range(H(q, 706) % 4)]
    return pl.DataFrame(dict(rot(cols, H(q, 709) % len(cols))))


def pre01(df) -> str | None:
    for c in ("MonthlyIncome", "NumberOfDependents"):
        if df.schema.get(c) not in (F64, STR):
            return f"{c} absent or not Float64 / String"
    for c in ("MonthlyIncome", "NumberOfDependents"):
        e = pl.col(c) if df.schema[c] == STR else pl.col(c).map_elements(sc.sas_best12, return_dtype=STR)
        out = df.select(sc.input_best32(e))
        if out.dtypes[0] != F64 or out.height != df.height:
            return "input_best32 not Float64 of the height"
    return None


UNITS = {
    "p01": ("predict_run_01_clean", 10000, L01, gen01, pre01, rv.step01,
            "pools: 24 floats (NaN, inf, -inf, 0.0, -0.0, 13-digit, 1e300, 1e-300, subnormal, 2^53, values BEST12 rounds) and 24 texts "
            "('', '.', 'NA', signs, spaces, exponents, '1,000', '--1', 20 digits) by index; 0-9 rows; all-null MonthlyIncome 1 in 8; each of the two "
            "columns Float64 or String (Int64 1 in 20: rejected); 0-3 other columns among VAR1, z, MonthlyIncome_num, NumberOfDependents_num, age; "
            "column order rotated; one case = up to 25 seeds"),
    "p02": ("predict_run_02_medians", 20000, L02, gen02, pre02, e8.step02,
            "pools: 23 names (case variants of the three names, near misses, '', a dotless-i name) drawn at a start and a stride so that they are "
            "distinct (stride 0, 1 in 12: repeated names, not a frame, dropped); 1-5 columns, numeric (edge pool: null, NaN, infinities, zeros, "
            "1e300, 1e-300, subnormal) or text; 0-3 rows (0 rows 1 in 8: rejected); one case = up to 25 seeds"),
    "p04": ("predict_run_04_imputed", 30000, L04, gen04, pre04, lambda i: e8.step04(*i),
            "left: 0-13 rows, the 11 selected columns Float64 from the edge pool (null, NaN, infinities, zeros, 1e300, 1e-300, subnormal, max, "
            "0.07, 0.29), age_group Int64 in -1..6 with nulls, MonthlyIncome_missing Int64 in 0..2 with nulls, 0-2 own columns among "
            "median_income, overall_median_income, x, t, y, age_group_right; right: 0-7 rows, key from {null, 1..6, 0.0, "
            "-0.0, NaN, 2.5, inf} (repeated keys, keys with no member), medians from the edge pool, 0-2 extra columns among x, age, VAR1, t, "
            "MonthlyIncome, NumberOfDependents, age_group_right, column order rotated; unshaped 1 in 20 each: Float64 left key, Float64 "
            "MonthlyIncome_missing, String MonthlyIncome, Int64 right key, String median / overall median, median / overall median absent; "
            "one case = up to 25 seeds"),
}
CH = 25
CHL = ("let ch := fun (c : Nat) (l : List Nat) => (List.range ((l.length + c - 1) / c)).map (fun (k : Nat) => (l.drop (c * k)).take c); "
       "let D := fun (s : Nat) => (dg (tR (U s))).toNat.toUInt64; "
       # dec a "<delta><letter> ...": the seeds that are not kept, each with its class (x: not sent; a, b, ..: the rejecting clause)
       "let dec := fun (a : Nat) (z : String) => (((z.splitOn \" \").filter (fun (t : String) => t != \"\")).foldl (fun (acc : Nat × List (Nat × Char)) (t : String) => "
       "let cs := t.toList; let p := acc.1 + (String.ofList cs.dropLast).toNat!; (p, acc.2 ++ [(p, cs.getLastD 'x')])) (a, ([] : List (Nat × Char)))).2; ")
LETTERS: dict = {}


def run_py(gen, pre, step, s):
    """-> (status, reason, digest): status kept | rejected | raises_inside | dropped."""
    try:
        inp = gen(s)
    except Exception:  # noqa: BLE001  (the draw is not a frame)
        return "dropped", "not a frame", None
    why = pre(inp)
    try:
        d = cmp.digest(cmp.tokens(cmp.canon_frame(step(inp))))
    except Exception as e:  # noqa: BLE001
        return ("raises_inside" if why is None else "dropped"), f"{why}: {type(e).__name__}", None
    return ("kept" if why is None else "rejected"), why, d


def build(key: str, total: int, per_call: int):
    unit, s0, lets, gen, pre, step, note = UNITS[key]
    s = Suite(f"fz_{key}")
    stats = {"kept": 0, "rejected": {}, "dropped": {}, "raises": []}
    for a in range(s0, s0 + total, per_call):
        seeds = range(a, min(a + per_call, s0 + total))
        dig, kept, rej = {}, [], {}
        for x in seeds:
            st, why, d = run_py(gen, pre, step, x)
            if st == "kept":
                kept.append(x)
                dig[x] = d
            elif st == "rejected":
                rej.setdefault(why, []).append(x)
                dig[x] = d
                stats["rejected"][why] = stats["rejected"].get(why, 0) + 1
            elif st == "raises_inside":
                stats["raises"].append(x)
            else:
                stats["dropped"][why] = stats["dropped"].get(why, 0) + 1
        stats["kept"] += len(kept)
        letter = {}
        for why, xs in rej.items():
            LETTERS.setdefault((key, why), "abcdefghijklmnopqrstuvw"[len([k for k in LETTERS if k[0] == key])])
            for x in xs:
                letter[x] = LETTERS[(key, why)]
        toks, prev = [], a
        for x in seeds:
            if x not in dig or x in letter:
                toks.append(f"{x - prev}{letter.get(x, 'x')}")
                prev = x
        cases = []
        for k in range(0, len(kept), CH):
            g = kept[k:k + CH]
            cases.append((f"kept seeds {g[0]}..{g[-1]}", unit, cmp.digest([dig[x] for x in g]), {"fz": "kept", "covers": len(g), "seeds": g}))
        for why, xs in sorted(rej.items(), key=lambda kv: LETTERS[(key, kv[0])]):
            for k in range(0, len(xs), 5):
                g = xs[k:k + 5]
                cases.append((f"rejected ({why}) seeds {g[0]}..{g[-1]}", unit, cmp.digest([dig[x] for x in g]),
                              {"fz": "rejected", "covers": len(g), "seeds": g, "clause": why}))
        zs = " ".join(toks)
        body = (f"let Z := dec {a} \"{zs}\"; "
                f"(ch 25 (List.filter (fun (s : Nat) => !(Z.any (fun (p : Nat × Char) => p.1 == s))) ((List.range {len(seeds)}).map (fun (i : Nat) => i + {a}))) ++ "
                "\"abcdefghijklmnopqrstuvw\".toList.flatMap (fun (c : Char) => ch 5 ((Z.filter (fun (p : Nat × Char) => p.2 == c)).map (fun (p : Nat × Char) => p.1)))).map "
                "(fun (g : List Nat) => dg (g.map D))")
        s.ints(lets + CHL, body, cases, gen=True)
    for inp in s.inputs:
        inp["item"], inp["decl"] = CARRIER
    s.write()
    print(key, "kept", stats["kept"], "of", total, "| rejected", stats["rejected"], "| dropped", stats["dropped"], "| raises inside", stats["raises"][:10],
          "| input sizes", [len(i["text"]) for i in s.inputs])
    return unit, {"seeds": f"{s0}..{s0 + total - 1}", "generated": total, "kept": stats["kept"],
                  "python_raises_inside_precondition": stats["raises"],
                  "note": note + f"; rejected with Python returning: {stats['rejected']}; dropped (Python raises outside the precondition): {stats['dropped']}"}


def one(key: str, seed: int):
    unit, s0, lets, gen, pre, step, note = UNITS[key]
    inp = gen(seed)
    print("input:", inp)
    print("precondition:", pre(inp))
    out = step(inp)
    print("python:", out.schema, out.rows())
    s = Suite(f"fz_{key}_one")
    s.tokens(lets, f"seed {seed}", unit, f"tR (U {seed})", "frame", cmp.canon_frame(out), gen=True)
    for i in s.inputs:
        i["item"], i["decl"] = CARRIER
    s.write()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--one":
        one(sys.argv[2], int(sys.argv[3]))
    else:
        per = int(sys.argv[1]) if len(sys.argv) > 1 else 500
        tot = {"p01": 2400, "p02": 3600, "p04": 3600}
        for key in UNITS:
            unit, row = build(key, tot[key], per)
            (HERE.parent / "work" / f"fz_{key}.fuzz.json").write_text(json.dumps(
                {"fuzzer": "port-translator-9", "generator": "diffeval/units/fz_t8_gen.py", "units": {unit: row}}))
