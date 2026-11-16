"""Fuzz pass 2026-11-16 (prompts/fuzz-2026-11-16.md): def:predict_run_00_input_check (+ precond),
fuzzed by port-translator-8 (reviewer of the unit, not its author).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_predict_check_gen.py
      -> diffeval/work/fz_predict_check.json, .inputs.json, .fuzz.json
  eval_decl each input on def:zz_carrier_p / zz_carrier_p (first-hand), then
  python3 diffeval/fuzz_collect.py 8 fz_predict_check ; compare.py ; python3 diffeval/fuzz_receipt.py fz_predict_check

One generated input per seed s, built INSIDE Lean (`mk s`) and mirrored here (`mk(s)`), both from
kit.hsh / gF / gI:
  h = hsh s 999; header variant v = h % 18; rows n = (h >> 8) % 7 (0..6)
  v: 0-7 the twelve imported names; 8 all upper case; 9 AGE; 10 a thirteenth name; 11 eleven names;
     12 a thirteenth name AGE (differs from age only in case); 13 Age and monthlyincome; 14 the
     import failed (none); 15 the names reversed; 16 a non-ASCII name whose Python upper form is an
     expected name (U+017F); 17 a thirteenth, non-ASCII name
  column j is String when hsh s (500 + j) % 3 == 0, else Float64
  Float64 values: gF (s * 50 + j) n 85 3 EF  (85 % from the edge list EF: null, 0, -0.0, 1, 2, 0.5,
     -1, 1e300, NaN, +inf, -inf, 3, 98, 1e-300, 7, 1 again; else a random float of magnitude 1/8..16)
  String values: gI (s * 50 + j) n 10 |SP| 0 as an index into SP (10 % null): "", ".", "NA", "na",
     " NA ", numbers with blanks and signs, a fraction, a negative, text, an exponent, 33 characters,
     a tab, an overflow, non-ASCII text
Expected: lines 82-182 of predict.py executed on that frame (test_raw = the frame, or None);
the result is (stop, test_raw, age_name) after them; one digest per seed.
`input_best32`: on both sides the real sas_compat.input_best32; in Lean as a table over the stripped
pool texts (a text outside the table would give 777).
Precondition def:predict_run_00_input_check_precond rendered in Python:
  none -> True; header names distinct -> len(set(names)) == len(names) (true for every variant);
  every row has the header's names and kinds -> true by construction of the frame;
  header names ASCII -> all(name.isascii()) (false for v = 16, 17: "rejected");
  input_best32 returns a Float64 column of the frame's height on the stripped text columns ->
  checked on the real function for every generated frame.
"""
from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import predict as pr  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

UNIT = "predict_run_00_input_check"
CARRIER = ("def:zz_carrier_p", "zz_carrier_p")
BASE, PER_CALL, CALLS = 10000, 600, 4
nan, inf = float("nan"), float("inf")
NM = ["VAR1", "SeriousDlqin2yrs", "age", "MonthlyIncome", "NumberOfDependents", "RevolvingUtilizationOfUnsecuredL",
      "DebtRatio", "NumberOfTime30-59DaysPastDueNotW", "NumberOfTime60-89DaysPastDueNotW", "NumberOfTimes90DaysLate",
      "NumberOfOpenCreditLinesAndLoans", "NumberRealEstateLoansOrLines"]
SP = ["", ".", "NA", "na", " NA ", "1", " 2 ", "0", "-1", "1.5", "x", "1e3", "0" * 32 + "4", "\tNA", "+3", "-0", "1e400", "ß", "5", "1"]
EF = [None, 0.0, -0.0, 1.0, 2.0, 0.5, -1.0, 1e300, nan, inf, -inf, 3.0, 98.0, 1e-300, 7.0, 1.0]
EF_LEAN = "[none, some 0.0, some (-0.0), some 1.0, some 2.0, some 0.5, some (-1.0), some 1e300, some (0.0 / 0.0), some (1.0 / 0.0), some (-1.0 / 0.0), some 3.0, some 98.0, some 1e-300, some 7.0, some 1.0]"

SRC = Path(pr.__file__).read_text().splitlines()
assert SRC[81].startswith("    EXPECTED = (") and SRC[181].strip().startswith("raise ValueError(")
CHECK = textwrap.dedent("\n".join(SRC[81:182]))


def header(v: int) -> list[str]:
    if v == 8:
        return [x.upper() for x in NM]
    if v == 9:
        return ["AGE" if x == "age" else x for x in NM]
    if v == 10:
        return NM + ["extra"]
    if v == 11:
        return NM[:-1]
    if v == 12:
        return NM + ["AGE"]
    if v == 13:
        return ["Age" if x == "age" else "monthlyincome" if x == "MonthlyIncome" else x for x in NM]
    if v == 15:
        return NM[::-1]
    if v == 16:
        return ["ſeriousDlqin2yrs" if x == "SeriousDlqin2yrs" else x for x in NM]
    if v == 17:
        return NM + ["é"]
    return list(NM)


def mk(s: int):
    h = kit.hsh(s, 999)
    v = h % 18
    if v == 14:
        return None
    n = (h >> 8) % 7
    H = header(v)
    cols, schema = {}, {}
    for j, name in enumerate(H):
        if kit.hsh(s, 500 + j) % 3 == 0:
            cols[name] = [None if i is None else SP[i] for i in kit.gI(s * 50 + j, n, 10, len(SP), 0)]
            schema[name] = pl.String
        else:
            cols[name] = kit.gF(s * 50 + j, n, 85, 3, EF)
            schema[name] = pl.Float64
    return pl.DataFrame(cols, schema=schema)


def python(frame):
    """-> (stop, test_raw, age_name) after lines 82-182."""
    env = {"pl": pl, "sas_compat": sc, "test_raw": frame}
    import contextlib
    import io
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            exec(CHECK, env)
        stop = False
    except ValueError as ex:
        assert str(ex) == "Test set scoring stopped. Nothing is exported.", ex
        stop = True
    return stop, env["test_raw"], env["age_name"]


def precond(frame) -> bool:
    if frame is None:
        return True
    names = frame.columns
    if len(set(names)) != len(names) or not all(n.isascii() for n in names):
        return False
    for n in names:
        if frame.schema[n] == pl.String:
            got = frame.select(sc.input_best32(pl.col(n).str.strip_chars(" ")))
            assert got.dtypes == [pl.Float64] and got.height == frame.height
    return True


def lets() -> str:
    stripped = list(dict.fromkeys(t.strip(" ") for t in SP))
    vals = pl.DataFrame({"s": stripped}, schema={"s": pl.String}).select(sc.input_best32(pl.col("s"))).to_series().to_list()
    ibt = "[" + ", ".join(f"({lt.lean_str(t)}, {'none' if v is None else 'some ' + lt.lean_float(v)})" for t, v in zip(stripped, vals)) + "]"
    L = lt.lean_str
    return (
        f"let NM : List String := [{', '.join(L(x) for x in NM)}]; "
        f"let SP : Array String := #[{', '.join(L(x) for x in SP)}]; "
        f"let EF : List (Option Float) := {EF_LEAN}; "
        f"let IBT : List (String × Option Float) := {ibt}; "
        "let IB := fun (e : Pl.Expr Float) => ({ eval := fun (g : Option (List (List Nat))) (fr : Pl.Frame Float) => (match e.eval g fr with "
        "| .str v => Pl.Col.f64 (v.map (fun (o : Option String) => o.bind (fun (t : String) => (IBT.lookup t).getD (some 777.0)))) | _ => Pl.Col.f64 []), "
        "name := e.name, ser := Pl.node [e.ser] } : Pl.Expr Float); "
        'let rp := fun (a b : String) => NM.map (fun (x : String) => if x == a then b else x); '
        'let hd := fun (v : Nat) => (if v == 8 then NM.map String.toUpper else if v == 9 then rp "age" "AGE" else if v == 10 then NM ++ ["extra"] '
        'else if v == 11 then NM.dropLast else if v == 12 then NM ++ ["AGE"] else if v == 13 then (rp "age" "Age").map (fun (x : String) => if x == "MonthlyIncome" then "monthlyincome" else x) '
        f'else if v == 15 then NM.reverse else if v == 16 then rp "SeriousDlqin2yrs" {L(chr(0x17f) + "eriousDlqin2yrs")} else if v == 17 then NM ++ [{L(chr(0xe9))}] else NM : List String); '
        "let mk := fun (s : Nat) => (let h := hsh s 999; let v := (h % 18).toNat; if v == 14 then none else "
        "let n := ((h >>> 8) % 7).toNat; let H := hd v; "
        "let K := (List.range H.length).map (fun (j : Nat) => (hsh s (500 + j)) % 3 == 0); "
        "let cols := (List.range H.length).map (fun (j : Nat) => (if K.getD j false then "
        "(gI (s * 50 + j) n 10 SP.size.toUInt64 0).map (fun (o : Option Int) => Tabular.Cell.str (o.map (fun (i : Int) => SP.getD i.toNat \"\"))) "
        "else (gF (s * 50 + j) n 85 3 EF).map (fun (x : Option Float) => Tabular.Cell.num x) : List (Tabular.Cell Float))); "
        "some (H.zip K, (List.range n).map (fun (i : Nat) => (List.range H.length).map (fun (j : Nat) => (H.getD j \"\", (cols.getD j []).getD i (Tabular.Cell.num none))))) "
        ": Option (List (String × Bool) × Tabular.Table Float)); "
        f"let ev := fun (s : Nat) => (let u := {UNIT} IB (mk s); dg ((if u.1 then 1 else 0) :: (tR u.2.1 ++ tS u.2.2))); "
    )


def main():
    s = Suite("fz_predict_check")
    L = lets()
    gen = kept = 0
    raises: list[int] = []
    stats = {"none": 0, "stop": 0, "pass": 0, "rows0": 0, "rejected": 0}
    for c in range(CALLS):
        b = BASE + c * PER_CALL
        cases = []
        for seed in range(b, b + PER_CALL):
            gen += 1
            fr = mk(seed)
            ok = precond(fr)
            try:
                stop, out, age = python(fr)
            except Exception as ex:  # noqa: BLE001
                if ok:
                    raises.append(seed)
                    print("PYTHON RAISES inside precondition", seed, type(ex).__name__, str(ex)[:120])
                # the Lean still returns something for this seed: an impossible expected value keeps
                # the list aligned; the case is marked rejected so that it is never counted as kept
                cases.append((f"seed {seed} (python raises)", UNIT, -1, {"fz": "rejected", "expect_diff": True, "note": "Python raises"}))
                continue
            if fr is None:
                out = pl.DataFrame()
                stats["none"] += 1
            elif fr.height == 0:
                stats["rows0"] += 1
            stats["stop" if stop else "pass"] += 1
            exp = cmp.digest([1 if stop else 0] + cmp.tokens(cmp.canon_frame(out)) + cmp.tok_str(age))
            if ok:
                kept += 1
            else:
                stats["rejected"] += 1
            cases.append((f"seed {seed}", UNIT, exp, {"fz": "kept" if ok else "rejected"}))
        s.ints(L, f"(List.range {PER_CALL}).map (fun (k : Nat) => ev ({b} + k))", cases, gen=True, table=False)
    for inp in s.inputs:
        inp["item"], inp["decl"] = CARRIER
    s.write()
    print(stats, "generated", gen, "kept", kept, "input chars", [len(i["text"]) for i in s.inputs])
    (HERE.parent / "work" / "fz_predict_check.fuzz.json").write_text(json.dumps({
        "fuzzer": "port-translator-8", "generator": "diffeval/units/fz_predict_check_gen.py",
        "units": {UNIT: {"seeds": f"{BASE}..{BASE + CALLS * PER_CALL - 1}", "generated": gen, "kept": kept,
                         "python_raises_inside_precondition": raises,
                         "note": f"one case = one generated import (header variant, 0-6 rows, String / Float64 columns from edge pools) through lines 82-182; {stats}"}}}))


if __name__ == "__main__":
    main()
