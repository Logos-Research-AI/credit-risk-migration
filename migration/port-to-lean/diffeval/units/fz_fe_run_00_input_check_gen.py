"""Fuzz pass 2026-11-16 (prompts/fuzz-2026-11-16.md): def:fe_run_00_input_check, fuzzed by
port-translator-4 (its reviewer; written by port-translator-3).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_fe_run_00_input_check_gen.py
      -> diffeval/work/fz_fe_run_00_input_check.{json,inputs.json,fuzz.json}

Inputs: one frame per seed, built inside Lean by `mk seed` (kit.GEN) and mirrored here (`mk`). The
first case of every eval input is one digest over all its input frames, so the two sides are
checked to hold the same frames. Modes (q = hash % 10):
  0     hostile: every column String (1 in 3) or Float64; Float64 cells 60 % from the edge list HE
        (null, NaN, +-inf, +-0.0, 0 / 1 and one ulp around 1, 0.5, -1, -5e-324, 5e-324, 1e300, an
        odd integer above 2^52), else random floats; String cells from the pool SP ("", " ", ".",
        NA spellings, numbers with blanks and signs, 1e3, text, 32 and 33 digits, a non-ASCII text)
  1     a valid frame with the names changed: one name in capitals / lower case / replaced by "x",
        a column removed, a thirteenth column, every name in capitals
  2     a valid frame whose `age` column is Int64 (outside the precondition; Python does not raise)
  3-9   a valid frame with ONE cell replaced by an edge value (HE or SP), in a column that is
        Float64 or (1 in 3) String
A valid frame: ids 1..n, outcome 0/1, whole numbers 0..3 elsewhere, MonthlyIncome and
NumberOfDependents missing on 20 % of the rows and String half of the time (missing spelled "",
" ", ".", "NA", "na"). Rows: 0, 1, 1, 2, 2, 3, 4, 6 by the seed.
Expected: lines 43-128 of feature_engineering.py read from the file at run time and executed with
the module's globals on the generated frame (as diffeval/units/t2_gen.py does); result
(stop, credit_raw after the check). `input_best32` is a lookup table made from the REAL
sas_compat.input_best32 over every text the pools can hold (blanks stripped as the unit does).
Precondition in Python (`precond`), clause by clause of def:fe_run_00_input_check_precond:
  names distinct -> len(set(columns)) == len(columns); one common length -> true of a DataFrame;
  every column Float64 or String -> dtype test; ASCII names -> str.isascii; names distinct after
  the case-blind renaming -> the renaming of :69-70 on ASCII upper case; ASCII cells of
  MonthlyIncome / NumberOfDependents when String (after renaming) -> str.isascii on the non-null
  cells; input_best32 gives Float64 of the frame's height -> true of the lookup table.
"""
from __future__ import annotations
import contextlib, io, json, sys, textwrap
from pathlib import Path
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402
from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

UNIT = "fe_run_00_input_check"
SUITE = "fz_fe_run_00_input_check"
nan, inf = float("nan"), float("inf")
N0 = ["VAR1", "SeriousDlqin2yrs", "RevolvingUtilizationOfUnsecuredL", "age", "NumberOfTime30-59DaysPastDueNotW",
      "DebtRatio", "MonthlyIncome", "NumberOfOpenCreditLinesAndLoans", "NumberOfTimes90DaysLate",
      "NumberRealEstateLoansOrLines", "NumberOfTime60-89DaysPastDueNotW", "NumberOfDependents"]
SP = [None, "", " ", ".", "NA", "na", "0", "1", "2", "7", "07", "7.0", " 3 ", "5000", "-1", "1.5", "1e3", "+7", "abc",
      "0.0", "-0", "Na", "1" * 32, "1" * 33, " 1", "ñ"]
HE = [None, nan, inf, -inf, 0.0, -0.0, 1.0, 2.0, 0.5, -1.0, 45.0, 1e300, 5e-324, -5e-324, 0.9999999999999999,
      1.0000000000000002, 4503599627370497.0, 3.0]
ROWS = [0, 1, 1, 2, 2, 3, 4, 6]


def h(s, i, m):
    return kit.hsh(s, i) % m


def mk(s: int) -> pl.DataFrame:
    q, n = h(s, 99, 10), ROWS[h(s, 98, 8)]
    jc, ir = h(s, 301, 12), h(s, 302, max(n, 1))

    def col(j):
        g = kit.gI(s * 16 + j, n, 20 if j in (6, 11) else 0, 2 if j == 1 else 4, 0)
        if j == 0:
            g = [i + 1 for i in range(n)]
        if q == 0:
            is_s = h(s, 200 + j, 3) == 0
        else:
            is_s = (j in (6, 11) and h(s, 200 + j, 2) == 0) or (q >= 3 and j == jc and h(s, 300, 3) == 0)
        if q == 0:
            if is_s:
                return pl.Series([SP[o] for o in kit.gI(s * 16 + j, n, 0, len(SP), 0)], dtype=pl.String)
            return pl.Series(kit.gF(s * 16 + j, n, 60, 3, HE), dtype=pl.Float64)
        if q == 2 and j == 3:
            return pl.Series(g, dtype=pl.Int64)
        if is_s:
            v = [str(x) if x is not None else SP[1 + i % 5] for i, x in enumerate(g)]
            if q >= 3 and j == jc and ir < n:
                v[ir] = SP[h(s, 303, len(SP))]
            return pl.Series(v, dtype=pl.String)
        v = [None if x is None else float(x) for x in g]
        if q >= 3 and j == jc and ir < n:
            v[ir] = HE[h(s, 303, len(HE))]
        return pl.Series(v, dtype=pl.Float64)

    cols = [(N0[j], col(j)) for j in range(12)]
    nv = h(s, 304, 6)
    if q == 1:
        if nv == 3:
            del cols[jc]
        elif nv == 4:
            cols.append(("extra", col(12)))
        else:
            cols = [((nm.upper() if nv == 5 or (j == jc and nv == 0) else nm.lower() if j == jc and nv == 1
                      else "x" if j == jc and nv == 2 else nm), c) for j, (nm, c) in enumerate(cols)]
    return pl.DataFrame([c.alias(nm) for nm, c in cols])


def lean_optf(x):
    return "none" if x is None else f"some {lt.lean_float(x)}"


LETS = (
    "let N0 := [" + ", ".join(lt.lean_str(x) for x in N0) + "]; "
    "let SP : List (Option String) := [" + ", ".join("none" if x is None else "some " + lt.lean_str(x) for x in SP) + "]; "
    "let HE : List (Option Float) := [" + ", ".join(lean_optf(x) for x in HE) + "]; "
    "let h := fun (s i m : Nat) => ((hsh s i) % m.toUInt64).toNat; "
    "let mk := fun (s : Nat) => let q := h s 99 10; let n := [0, 1, 1, 2, 2, 3, 4, 6].getD (h s 98 8) 1; "
    "let jc := h s 301 12; let ir := h s 302 (max n 1); "
    "let col := fun (j : Nat) => "
    "let g := gI (s * 16 + j) n (if j == 6 || j == 11 then 20 else 0) (if j == 1 then 2 else 4) 0; "
    "let g := if j == 0 then (List.range n).map (fun (i : Nat) => some ((i : Int) + 1)) else g; "
    "let isS := if q == 0 then h s (200 + j) 3 == 0 else ((j == 6 || j == 11) && h s (200 + j) 2 == 0) || (q >= 3 && j == jc && h s 300 3 == 0); "
    f"(if q == 0 then (if isS then Pl.Col.str ((gI (s * 16 + j) n 0 {len(SP)} 0).map (fun (o : Option Int) => SP.getD (o.getD 0).toNat none)) "
    "else Pl.Col.f64 (gF (s * 16 + j) n 60 3 HE)) "
    "else if q == 2 && j == 3 then Pl.Col.int g "
    "else if isS then (let v := (List.range n).map (fun (i : Nat) => (match g.getD i none with | some x => some (toString x) | none => SP.getD (1 + i % 5) none : Option String)); "
    f"Pl.Col.str (if q >= 3 && j == jc then v.set ir (SP.getD (h s 303 {len(SP)}) none) else v)) "
    "else (let v := g.map (fun (o : Option Int) => o.map Float.ofInt); "
    f"Pl.Col.f64 (if q >= 3 && j == jc then v.set ir (HE.getD (h s 303 {len(HE)}) none) else v)) : Pl.Col Float); "
    "let fr : Pl.Frame Float := (List.range 12).map (fun (j : Nat) => (N0.getD j \"\", col j)); "
    "let nv := h s 304 6; "
    "(if q != 1 then fr else if nv == 3 then fr.eraseIdx jc else if nv == 4 then fr ++ [(\"extra\", col 12)] else "
    "(List.range 12).map (fun (j : Nat) => let p := fr.getD j (\"\", Pl.Col.f64 []); "
    "((if nv == 5 || (j == jc && nv == 0) then p.1.toUpper else if j == jc && nv == 1 then p.1.toLower else if j == jc && nv == 2 then \"x\" else p.1), p.2)) : Pl.Frame Float); "
)

# ---- the port's lines 43-128, executed (as t2_gen.py)
A, B = 43, 128
src = "".join(Path(fe.__file__).read_text().splitlines(keepends=True)[A - 1:B])
assert src.lstrip().startswith("EXPECTED = (") and src.rstrip().endswith('raise ValueError("Feature engineering stopped. Nothing is exported.")'), "line numbers moved"
CODE = compile(textwrap.dedent(src), f"feature_engineering.py:{A}-{B}", "exec")


def run_slice(credit_raw):
    ns = dict(vars(fe))
    ns["credit_raw"] = credit_raw
    stopped = False
    with contextlib.redirect_stdout(io.StringIO()):
        try:
            exec(CODE, ns)
        except ValueError as e:
            assert str(e) == "Feature engineering stopped. Nothing is exported.", e
            stopped = True
    return stopped, ns["credit_raw"], tuple(int(ns[c]) for c in ("columns_ok", "bad_rows", "duplicate_ids", "known_incomes"))


def precond(df: pl.DataFrame) -> bool:
    names = df.columns
    if len(set(names)) != len(names) or not all(t in (pl.Float64, pl.String) for t in df.dtypes):
        return False
    if not all(nm.isascii() for nm in names):
        return False
    by_upper = {c.upper(): c for c in N0}
    ren = [by_upper.get(nm.upper(), nm) for nm in names]
    if len(set(ren)) != len(ren):
        return False
    for nm, r in zip(names, ren, strict=True):
        if r in ("MonthlyIncome", "NumberOfDependents") and df.schema[nm] == pl.String:
            if not all(v.isascii() for v in df.get_column(nm).to_list() if v is not None):
                return False
    return True


# ---- input_best32 as a lookup table from the real function
texts = sorted({x.strip(" ") for x in SP if x is not None} | {str(i) for i in range(0, 8)})
vals = pl.DataFrame({"t": texts}, schema={"t": pl.String}).select(sc.input_best32(pl.col("t"))).to_series().to_list()
IB = ("let IB := fun (e : Pl.Expr Float) => ({ e with eval := fun (g : Option (List (List Nat))) (fr : Pl.Frame Float) => "
      "(match e.eval g fr with | .str v => Pl.Col.f64 (v.map (fun (o : Option String) => (match o with | some s => (match (["
      + ", ".join(f"({lt.lean_str(t)}, {lean_optf(v)})" for t, v in zip(texts, vals, strict=True))
      + "] : List (String × Option Float)).lookup s with | some r => r | none => some (-987654321.0)) | none => none))) | _ => Pl.Col.int []) } : Pl.Expr Float); ")


def dg_result(stop: bool, frame: pl.DataFrame) -> dict:
    return [1 if stop else 0] + cmp.tokens(cmp.canon_frame(frame))


FIRST, COUNT, PER = 1000, 2700, 450
s = Suite(SUITE)
s.item, s.decl = "def:zz_carrier_f", "zz_carrier_f"
stats = {"generated": 0, "kept": 0, "rejected_sent": 0, "dropped": 0, "raises_inside": [], "stop": 0, "modes": {}}
for base in range(FIRST, FIRST + COUNT, PER):
    seeds, cases, intoks = [], [], []
    for seed in range(base, base + PER):
        stats["generated"] += 1
        df = mk(seed)
        ok = precond(df)
        try:
            stop, out, counters = run_slice(df)
        except Exception as e:  # noqa: BLE001
            if ok:
                stats["raises_inside"].append(seed)
            else:
                stats["dropped"] += 1
            continue
        seeds.append(seed)
        intoks += cmp.tokens(cmp.canon_frame(df))
        stats["kept" if ok else "rejected_sent"] += 1
        stats["stop"] += stop
        q = h(seed, 99, 10)
        stats["modes"][q] = stats["modes"].get(q, 0) + 1
        cases.append((f"seed{seed}", UNIT, {"digest_of": dg_result(stop, out)}, {"fz": "kept" if ok else "rejected"}))
    skipped = [x for x in range(base, base + PER) if x not in seeds]
    sl = f"let SEEDS := ((List.range {PER}).map (fun (i : Nat) => i + {base}))" + (f".filter (fun (x : Nat) => !([{', '.join(map(str, skipped))}].contains x))" if skipped else "") + "; "
    body = ("[dg (SEEDS.flatMap (fun (x : Nat) => tR (mk x)))] ++ SEEDS.map (fun (x : Nat) => "
            "let r := fe_run_00_input_check IB (some (mk x)); dg ((if r.1 then 1 else 0) :: tR r.2))")
    allc = [(f"inputs{base}", UNIT + " (input frames)", cmp.digest(intoks), {"fz": "kept", "covers": 0})] + \
           [(c[0], c[1], cmp.digest(c[2]["digest_of"]), c[3]) for c in cases]
    s.ints(LETS + IB + sl, body, allc, gen=True, table=False)
# None: the import raised
stop, out, _ = run_slice(None)
assert stop and out is None
s.ints(IB, "[(let r := fe_run_00_input_check IB (none : Option (Pl.Frame Float)); dg ((if r.1 then 1 else 0) :: tR r.2))]",
       [("none", UNIT, cmp.digest([1] + cmp.tokens(cmp.canon_frame(pl.DataFrame()))), {"fz": "kept"})], gen=False, table=False)
stats["generated"] += 1
stats["kept"] += 1
s.write()
note = (f"one case = one generated frame (0-6 rows), result (stop, frame); modes hostile / names / Int64 age / one-cell edge = "
        f"{stats['modes']}; stop true on {stats['stop']} of the sent frames; rejected by the precondition and sent: {stats['rejected_sent']}; "
        f"rejected and Python raises (dropped): {stats['dropped']}; pools: HE {len(HE)} float edges, SP {len(SP)} texts")
(HERE.parent / "work" / f"{SUITE}.fuzz.json").write_text(json.dumps({
    "fuzzer": "port-translator-4", "generator": "diffeval/units/fz_fe_run_00_input_check_gen.py",
    "units": {UNIT: {"seeds": f"{FIRST}..{FIRST + COUNT - 1} and None", "generated": stats["generated"], "kept": stats["kept"],
                     "python_raises_inside_precondition": stats["raises_inside"], "note": note}}}))
print(stats)
print([len(i["text"]) for i in s.inputs])
