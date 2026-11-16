"""Fuzz pass 2026-11-16 (prompts/fuzz-2026-11-16.md): def:fe_run_01_clean, fuzzed by port-translator-5
(its reviewer; the unit was written by port-translator-4).

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_fe_run_01_clean_gen.py
      -> diffeval/work/fz_fe_run_01_clean.{json,inputs.json,fuzz.json}
  (eval_decl every input on def:zz_carrier_f / zz_carrier_f; python3 diffeval/fuzz_collect.py 5 fz_fe_run_01_clean)
  PYTHONPATH=../../port uv run --project ../../port python diffeval/compare.py diffeval/work/fz_fe_run_01_clean.json diffeval/work/fz_fe_run_01_clean.out.txt
  python3 diffeval/fuzz_receipt.py fz_fe_run_01_clean

One generated input = one frame credit_raw, built INSIDE Lean from its seed (`mk sh s`, mirrored here by
`frame(sh, s)` with kit.hsh / kit.gI): the number of rows, the kind of MonthlyIncome and of
NumberOfDependents, the layout (column order, other columns, a pre-existing MonthlyIncome_num or
NumberOfDependents_num) and the share of nulls all come from hsh(s, 77); the values are drawn by
index (kit.gI) from a pool of floats and a pool of strings.
  shaped   (sh = true):  1 to 24 rows, both columns Float64 or String, both present;
  unshaped (sh = false): 0 to 7 rows, the two columns Float64 / String / Int64 / Boolean, one layout
                         without NumberOfDependents.
Expected value: the source lines feature_engineering.py:138-152 read from the file and executed
verbatim on the mirrored frame (as diffeval/units/t3_gen.py takes them from the real run), with the
REAL sas_compat.sas_best12 and sas_compat.input_best32. On the Lean side the two parameters are
lookup tables made from the real functions: sas_best12 over the float pool (which also holds the
values an Int64 or Boolean column can hold), input_best32 over the string pool and every text
sas_best12 returns (a value absent from a table gives a marker that cannot match).

Precondition def:fe_run_01_clean_precond, rendered in Python by `precond(df)`:
  distinct names, common length   true of any pl.DataFrame (the names are checked);
  0 < height                      df.height > 0;
  both columns present, String or Float64      the schema;
  the parameter input_best32 applied to the expression the unit builds evaluates to a Float64
  column of the frame's height    the port's own expression (local input_best32(v) of :138-143,
                                  real functions) evaluated on the frame: dtype Float64, length = height.
Kept = admitted and Python returns. Rejected inputs on which Python returns are sent to Lean too
("fz": "rejected"); those on which it raises are dropped.

Cases: shaped seeds are digested in blocks of 25 consecutive seeds (one digest of the 25 results,
"covers": 25; all 25 are asserted kept); the generated input frames of each block are digested too
(primitive "... (input)") so the mirror is checked. Unshaped seeds are one digest each.
"""
from __future__ import annotations

import json
import sys
import textwrap
from decimal import Decimal
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_f", "zz_carrier_f")

import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

nan, inf = float("nan"), float("inf")
UNIT = "fe_run_01_clean"
SUITE = "fz_fe_run_01_clean"
A, B, MUST = 138, 152, "map_elements(sas_compat.sas_best12, return_dtype=pl.String)"

# float pool: the keys of the sas_best12 table. -2..5 are also what an Int64 / Boolean column holds.
FP = [-2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0, 5.0,
      nan, inf, -inf, -0.0, 5e-324, 1e300, -1e-300,
      1234567890123.0, 0.1234567890123, 99999999999.96, 999999999999.5, 123456789012.0, 1e15, 1e20,
      2.0 ** 53, 5400.0, -0.5, 0.000001234567891, 0.1 + 0.2, 99999999999.5]
# string pool
SP = ["", ".", "NA", " 3 ", "+5", "-0", "1e2", "1E400", "0x10", "12abc", " ", "5400", "1234567890123", ".5", "5.",
      "-", "1e", "inf", "nan", "000000000000000000000000000000001234", "1 2", "  -2.50  ", "na", "9" * 32 + "9"]
NF, NS = len(FP), len(SP)
N_SH, N_UN = [1, 1, 2, 3, 5, 9, 24], [0, 0, 1, 2, 3, 7]


# ---------------------------------------------------------------- the generated frame, Python mirror
def col(k: int, s: int, n: int, pn: int) -> pl.Series:
    if k < 2:
        return pl.Series([None if i is None else FP[i] for i in kit.gI(s, n, pn, NF, 0)], dtype=pl.Float64, nan_to_null=False)
    if k < 4:
        return pl.Series([None if i is None else SP[i] for i in kit.gI(s, n, pn, NS, 0)], dtype=pl.String)
    if k == 4:
        return pl.Series(kit.gI(s, n, pn, 8, 2), dtype=pl.Int64)
    return pl.Series([None if i is None else i == 1 for i in kit.gI(s, n, pn, 2, 0)], dtype=pl.Boolean)


def frame(sh: bool, s: int) -> pl.DataFrame:
    u = kit.hsh(s, 77)
    n = N_SH[u % 7] if sh else N_UN[u % 6]
    km = (u // 8) % (4 if sh else 6)
    kd = (u // 64) % (4 if sh else 6)
    lay = (u // 512) % 5
    pn = 100 if (u // 4096) % 8 == 0 else 25
    m = ("MonthlyIncome", col(km, 4 * s + 1, n, pn))
    d = ("NumberOfDependents", col(kd, 4 * s + 2, n, pn))
    v = ("VAR1", col(0, 4 * s + 3, n, 25))
    if lay == 0:
        cols = [v, m, ("age", col(0, 4 * s, n, 25)), d]
    elif lay == 1:
        cols = [d, v, m]
    elif lay == 2:
        cols = [m, ("MonthlyIncome_num", col(2, 4 * s, n, 25)), d, v]
    elif lay == 3:
        cols = [v, ("NumberOfDependents_num", col(0, 4 * s, n, 25)), d, m]
    else:
        cols = [m, d] if sh else [v, m]
    return pl.DataFrame({name: c for name, c in cols})


MK = (
    "let cF := fun (s n : Nat) (pn : UInt64) => (Pl.Col.f64 ((gI s n pn {nf} 0).map (fun (o : Option Int) => o.map (fun (i : Int) => FP.getD i.toNat 0.0))) : Pl.Col Float); "
    "let cK := fun (k s n : Nat) (pn : UInt64) => (if k < 2 then cF s n pn else if k < 4 then "
    "Pl.Col.str ((gI s n pn {ns} 0).map (fun (o : Option Int) => o.map (fun (i : Int) => SP.getD i.toNat \"\"))) else if k == 4 then Pl.Col.int (gI s n pn 8 2) "
    "else Pl.Col.bool ((gI s n pn 2 0).map (fun (o : Option Int) => o.map (fun (i : Int) => i == 1))) : Pl.Col Float); "
    "let mk := fun (sh : Bool) (s : Nat) => (let u := (hsh s 77).toNat; let n := if sh then [1, 1, 2, 3, 5, 9, 24].getD (u % 7) 1 else [0, 0, 1, 2, 3, 7].getD (u % 6) 0; "
    "let q := if sh then 4 else 6; let pn : UInt64 := if (u / 4096) % 8 == 0 then 100 else 25; "
    "let M := (\"MonthlyIncome\", cK ((u / 8) % q) (4 * s + 1) n pn); let D := (\"NumberOfDependents\", cK ((u / 64) % q) (4 * s + 2) n pn); "
    "let V := (\"VAR1\", cF (4 * s + 3) n 25); let l := (u / 512) % 5; "
    "(if l == 0 then [V, M, (\"age\", cF (4 * s) n 25), D] else if l == 1 then [D, V, M] else if l == 2 then [M, (\"MonthlyIncome_num\", cK 2 (4 * s) n 25), D, V] "
    "else if l == 3 then [V, (\"NumberOfDependents_num\", cF (4 * s) n 25), D, M] else if sh then [M, D] else [V, M] : Pl.Frame Float)); "
).replace("{nf}", str(NF)).replace("{ns}", str(NS))


# ---------------------------------------------------------------- the two parameters as lookup tables
def num_code(v):
    if v != v or v in (inf, -inf) or v < 0 or (v == 0 and cmp.fbits(v) != 0):
        return None
    sign, digits, exp = Decimal(repr(v)).as_tuple()
    m = int("".join(map(str, digits)))
    if exp > 0:
        m, exp = m * 10 ** exp, 0
    e = -exp
    if e >= 32 or m >= 2 ** 53 or cmp.fbits(float(f"{m}e-{e}")) != cmp.fbits(v):
        return None
    return m * 32 + e + 1


def lean_optf(v):
    if v is None:
        return "none"
    c = num_code(v)
    return f"d {c}" if c is not None else f"some {lt.lean_float(v)}"


def tables() -> str:
    b12 = [(cmp.fbits(x), sc.sas_best12(x)) for x in FP]
    # an Int64 / Boolean column passes Python ints / bools: the same text as the float of the pool?
    same_int = all(sc.sas_best12(k) == sc.sas_best12(float(k)) for k in range(-2, 6))
    same_bool = sc.sas_best12(True) == sc.sas_best12(1.0) and sc.sas_best12(False) == sc.sas_best12(0.0)
    print(f"sas_best12(int k) == sas_best12(float(k)) for k in -2..5: {same_int}; for bools: {same_bool}")
    texts = sorted(set(SP) | {t for _, t in b12})
    vals = pl.DataFrame({"t": texts}, schema={"t": pl.String}).select(sc.input_best32(pl.col("t"))).to_series().to_list()
    changed = [(x, t) for x, (_, t) in zip(FP, b12, strict=True)
               if (lambda r: r is None or cmp.fbits(r) != cmp.fbits(x))(dict(zip(texts, vals, strict=True))[t])]
    print(f"float pool: {NF} values, {len(changed)} changed or lost by the BEST12 round trip; string pool: {NS}; input_best32 table: {len(texts)} texts")
    bt = "[" + ", ".join(f"({k}, {lt.lean_str(t)})" for k, t in b12) + "]"
    it = "[" + ", ".join(f"({lt.lean_str(t)}, {lean_optf(v)})" for t, v in zip(texts, vals, strict=True)) + "]"
    sp = "[" + ", ".join(lt.lean_str(t) for t in SP) + "]"
    return (
        "let d := fun (c : Nat) => (some (Float.ofScientific ((c - 1) / 32) true ((c - 1) % 32)) : Option Float); "
        f"let BT : List (UInt64 × String) := {bt}; let IT : List (String × Option Float) := {it}; "
        f"let SP : List String := {sp}; let FP : List Float := BT.map (fun (p : UInt64 × String) => Float.ofBits p.1); "
        "let pB := fun (o : Option Float) => (match o with | some x => (BT.lookup x.toBits).getD \"?MISSING\" | none => \"?NONE\"); "
        "let pI := fun (e : Pl.Expr Float) => ({ e with eval := fun (g : Option (List (List Nat))) (fr : Pl.Frame Float) => "
        "(match e.eval g fr with | .str v => Pl.Col.f64 (v.map (fun (o : Option String) => (match o with | some s => (match IT.lookup s with | some r => r | none => some (-987654321.0)) | none => none))) "
        "| _ => Pl.Col.int []) } : Pl.Expr Float); "
    )


# ---------------------------------------------------------------- the port's code, the precondition
def slice_source() -> str:
    src = "".join(Path(fe.__file__).read_text().splitlines(keepends=True)[A - 1:B])
    assert MUST in src, "the slice does not hold the expected line: line numbers moved?"
    return textwrap.dedent(src)


SRC = compile(slice_source(), f"{fe.__file__}:{A}-{B}", "exec")


def python(df: pl.DataFrame):
    """-> (credit_raw_clean, None) or (None, exception)"""
    ns = dict(vars(fe))
    ns["credit_raw"] = df
    try:
        exec(SRC, ns)  # noqa: S102
        return ns["credit_raw_clean"], None
    except Exception as ex:  # noqa: BLE001
        return None, ex


def precond(df: pl.DataFrame) -> bool:
    if len(set(df.columns)) != len(df.columns) or df.height <= 0:
        return False
    for n in ("MonthlyIncome", "NumberOfDependents"):
        if n not in df.columns or df.schema[n] not in (pl.String, pl.Float64):
            return False
        e = (sc.input_best32(pl.col(n).map_elements(sc.sas_best12, return_dtype=pl.String)) if df.schema[n] != pl.String
             else sc.input_best32(pl.col(n)))
        r = df.select(e).to_series()
        if r.dtype != pl.Float64 or r.len() != df.height:
            return False
    return True


def toks(df: pl.DataFrame) -> list[int]:
    return cmp.tokens(cmp.canon_frame(df))


def build(sh0: int = 20000, blocks: int = 92, k: int = 25, un0: int = 50000, n_un: int = 320):
    s = Suite(SUITE)
    pre = tables() + MK + "let U := fun (sh : Bool) (s : Nat) => tR (fe_run_01_clean pI pB (mk sh s)); "
    stats = {"generated": 0, "kept": 0, "rejected_returns": 0, "dropped": 0, "raises_inside": []}
    kinds: dict = {}
    # ---- shaped: blocks of k seeds
    res_cases, in_cases = [], []
    for b in range(blocks):
        rt, it = [], []
        for j in range(k):
            seed = sh0 + b * k + j
            df = frame(True, seed)
            out, ex = python(df)
            stats["generated"] += 1
            assert precond(df) and ex is None, (seed, ex)   # a shaped input is inside the precondition
            stats["kept"] += 1
            kk = (str(df.schema["MonthlyIncome"]), str(df.schema["NumberOfDependents"]), min(df.height, 3))
            kinds[kk] = kinds.get(kk, 0) + 1
            rt += toks(out)
            it += toks(df)
        res_cases.append((f"shaped seeds {sh0 + b * k}..{sh0 + b * k + k - 1}", UNIT, cmp.digest(rt), {"fz": "kept", "covers": k}))
        in_cases.append((f"shaped seeds {sh0 + b * k}..{sh0 + b * k + k - 1} / generated frames", UNIT + " (input)", cmp.digest(it),
                         {"fz": "kept", "covers": k}))
    body1 = (f"(List.range {blocks}).map (fun (b : Nat) => dg ((List.range {k}).flatMap (fun (j : Nat) => U true ({sh0} + b * {k} + j)))) ++ "
             f"(List.range {blocks}).map (fun (b : Nat) => dg ((List.range {k}).flatMap (fun (j : Nat) => tR (mk true ({sh0} + b * {k} + j)))))")
    # ---- unshaped: one digest per seed that Python accepts
    seeds, cases, why = [], [], {}
    for seed in range(un0, un0 + n_un):
        df = frame(False, seed)
        out, ex = python(df)
        ok = precond(df)
        stats["generated"] += 1
        if ex is not None:
            if ok:
                stats["raises_inside"].append(seed)
            else:
                stats["dropped"] += 1
            continue
        if ok:
            stats["kept"] += 1
        else:
            stats["rejected_returns"] += 1
            reason = ("no row" if df.height == 0 else "") + "".join(
                f" {n}:{df.schema[n]}" for n in ("MonthlyIncome", "NumberOfDependents") if df.schema[n] not in (pl.String, pl.Float64))
            why[reason.strip()] = why.get(reason.strip(), 0) + 1
        seeds.append(seed)
        cases.append((f"unshaped seed {seed} ({df.height} rows, {df.schema['MonthlyIncome']}/{df.schema['NumberOfDependents']})", UNIT,
                      cmp.digest(toks(out)), {"fz": "kept" if ok else "rejected"}))
    # the seeds Python accepts are exactly those whose layout is not 4 (the layout without
    # NumberOfDependents, on which Python raises KeyError): Lean filters them by the same test
    assert seeds == [x for x in range(un0, un0 + n_un) if (kit.hsh(x, 77) // 512) % 5 != 4]
    body2 = (f"(((List.range {n_un}).map (fun (i : Nat) => {un0} + i)).filter (fun (s : Nat) => ((hsh s 77).toNat / 512) % 5 != 4)).map "
             "(fun (s : Nat) => dg (U false s))")
    # one eval input (the preamble is most of the text): shaped results, shaped generated frames, unshaped results
    s.ints(pre, f"({body1} ++ {body2})", res_cases + in_cases + cases, gen=True, table=False)
    s.notes = {UNIT: "seeded fuzz: frames generated inside Lean; sas_best12 / input_best32 = lookup tables from the real functions"}
    s.write()
    fz = {"fuzzer": "port-translator-5", "generator": "diffeval/units/fz_fe_run_01_clean_gen.py",
          "units": {UNIT: {"seeds": f"{sh0}..{sh0 + blocks * k - 1} (shaped), {un0}..{un0 + n_un - 1} (unshaped)",
                           "generated": stats["generated"], "kept": stats["kept"],
                           "python_raises_inside_precondition": stats["raises_inside"],
                           "note": f"one case = one frame credit_raw from a seed (rows, kinds, layout, null share from the seed; values by index "
                                   f"from a pool of {NF} floats and {NS} strings); shaped blocks of {k} seeds are one digest; "
                                   f"rejected inputs on which Python returns: {stats['rejected_returns']} {why}; dropped (Python raises "
                                   f"outside the precondition): {stats['dropped']}"}}}
    (suite_mod.WORK / f"{SUITE}.fuzz.json").write_text(json.dumps(fz, indent=1))
    print(stats, why)
    print("shaped kinds (MonthlyIncome, NumberOfDependents, min(rows, 3)):", sorted(kinds.items()))
    for i in s.inputs:
        print("input chars:", len(i["text"]))


if __name__ == "__main__":
    build()
