"""Fidelity pass 2026-11-20, third attempt (label stale-compositions): def:run and def:run_py_py on REAL data,
against the CURRENT Python (port HEAD 4a757fb).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_stale_real_gen.py
      -> diffeval/work/fz10c_stale_real_run.{json,inputs.json}, diffeval/work/fz10c_stale_real_pp.{json,inputs.json}

A whole file (150,000 / 101,503 rows) is far beyond one eval_decl input, so the real data goes in as slices: data
lines of legacy/data/cs-training.csv and legacy/data/cs-test.csv, copied byte for byte under the real header into a
small file, on which the REAL run is called.

def:run (suite fz10c_stale_real_run). Slices (seeded, random.Random(20261120)): RUN_SLICES, each (kind, rows):
  "mixed"     random data lines of the whole file (MonthlyIncome / NumberOfDependents usually hold NA: String columns)
  "complete"  random data lines whose MonthlyIncome and NumberOfDependents are both numbers (Float64 columns: the
              sas_best12 -> input_best32 path of feature_engineering.py:147-152)
  "edge"      lines with age < 22 or > 100, utilization > 10, DebtRatio > 5000, a 90-day count >= 90, dependents
              >= 8, income 0 or >= 100000, plus random lines
  Each slice runs with two split files:
    "restricted"  inputs/split_ids.csv restricted to the slice's ids, file order kept: almost never (7n+9)//10
                  distinct present ids, so the run DRAWS (feature_engineering._split_draw, seed 42)
    "fits"        the first (7n+9)//10 ids of the restricted list, completed with the slice's other ids in file
                  order: the file fits and is used as given
  full = true for "restricted", false for "fits" (both reduction shapes of the 8-operand sum, RULEBOOK 3).
  Lean: run (α := Float) full IB SB (some T) SP, T the table proc_import_csv returned (built cell by cell), SP the
  split table; IB = input_best32 as a lookup from every text the slice's String columns hold (raw and stripped of
  blanks) and every BEST12. text of the run, to the REAL sas_compat.input_best32 of it (texts it maps to null left
  out: the lookup gives none); SB = sas_best12 as a lookup from every value the run passed to the REAL
  sas_compat.sas_best12 (recorded by a wrapper) to its text. One integer per case: dg of [dg T, dg SP, then 0 when
  the run stops or the number of files and dg (name ++ table) of each file, ALL columns at full bits].

def:run_py_py (suite fz10c_stale_real_pp). The model is the REAL one: model.json and income_medians.csv of the real
pipeline on legacy/data at HEAD (work/fz10_glue_real_out, written by the glue-end-to-end agent; its intercept and 15
coefficients are asserted equal to work/fz10_real.expected.json of the stale-compositions pass). Slices of
cs-test.csv: "random" lines and "complete" lines (both income and dependents numbers). Python: the REAL predict.run
on the written slice, the real medians file and model files. Lean: run_py_py (α := Float) full ib intercept coefs sb
true (some (H, T)) (some M), H the header of test_raw with its kinds, T its rows, M the imported medians table.
One integer per case: W [1, dg (name ++ names ++ table) of each file] as fz_run_py_py_gen (0 when the run stops).
"""
from __future__ import annotations

import contextlib
import io
import json
import random
import sys
import tempfile
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import fz10_run_gen  # noqa: E402,F401
import fz_run_gen as gr  # noqa: E402
import fz10_run_py_py_gen  # noqa: E402,F401
import b4_gen as b4  # noqa: E402
import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_fid_2", "zz_carrier_fid_2")
from suite import Suite  # noqa: E402
from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import predict as pr  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

gp = sys.modules["fz10_run_py_py_impl"]
ROOT = HERE.parents[3]
TRAIN, TEST = ROOT / "legacy" / "data" / "cs-training.csv", ROOT / "legacy" / "data" / "cs-test.csv"
SPLIT = HERE.parents[1] / "inputs" / "split_ids.csv"
REAL = HERE.parent / "work" / "fz10_glue_real_out"
RUN_SLICES = [("mixed", 20), ("mixed", 30), ("complete", 20), ("complete", 30), ("edge", 24), ("edge", 30)]
PP_SLICES = [("random", 25), ("random", 40), ("complete", 25), ("complete", 40)]
FILES_FE = ["income_medians.csv", "model_features_train.csv", "model_features_validation.csv"]

rng = random.Random(20261120)
B12: dict[int, str] = {}
_o_b12 = sc.sas_best12


def rec_b12(x):
    t = _o_b12(x)
    if x is not None:
        B12[lt.bits(x)] = t
    return t


sc.sas_best12 = rec_b12


# ---------------------------------------------------------------- Lean rendering of tables
def cell(kind: str, v) -> str:
    if kind == "str":
        return "Z2" if v is None else f"(S {lt.lean_str(v)})"
    if v is None:
        return "Z"
    x = float(v)
    if x == int(x) and 0 <= x < 2 ** 53 and lt.bits(x) != lt.bits(-0.0):
        return f"(I {int(x)})"
    return f"(B {lt.bits(x)})"


def lean_table(df: pl.DataFrame) -> str:
    """Tabular.Table Float built column by column: (names, kinds) and one list of cells per column."""
    kinds = [lt.col_kind(df.schema[n]) for n in df.columns]
    cols = "[" + ", ".join("[" + ", ".join(cell(k, v) for v in df.get_column(n).to_list()) + "]"
                           for n, k in zip(df.columns, kinds)) + "]"
    names = "[" + ", ".join(lt.lean_str(n) for n in df.columns) + "]"
    return f"(TB {df.height} {names} {cols})"


HELP = ("let I := fun (n : Nat) => Tabular.Cell.num (some (Float.ofNat n)); "
        "let B := fun (n : UInt64) => Tabular.Cell.num (some (Float.ofBits n)); "
        "let S := fun (t : String) => (Tabular.Cell.str (some t) : Tabular.Cell Float); "
        "let Z : Tabular.Cell Float := Tabular.Cell.num none; let Z2 : Tabular.Cell Float := Tabular.Cell.str none; "
        "let TB := fun (n : Nat) (ns : List String) (cs : List (List (Tabular.Cell Float))) => "
        "((List.range n).map (fun (i : Nat) => (ns.zip cs).map (fun (p : String × List (Tabular.Cell Float)) => (p.1, p.2.getD i Z))) : Tabular.Table Float); "
        "let u := fun (i : Int) => i.toNat.toUInt64; ")


def lookups(texts: set[str]) -> str:
    keys = sorted(texts | {t.strip(" ") for t in texts} | set(B12.values()))
    vals = pl.DataFrame({"t": keys}, schema={"t": pl.String}).select(sc.input_best32(pl.col("t"))).to_series().to_list()
    T = "[" + ", ".join(f"({lt.lean_str(t)}, {lt.lean_float(v)})" for t, v in zip(keys, vals) if v is not None) + "]"
    SBT = "[" + ", ".join(f"({b}, {lt.lean_str(t)})" for b, t in sorted(B12.items())) + "]"
    return (f"let T : List (String × Float) := {T}; "
            "let IB := fun (e : Pl.Expr Float) => ({ e with eval := fun (g : Option (List (List Nat))) (fr : Pl.Frame Float) => "
            "(match e.eval g fr with | .str v => Pl.Col.f64 (v.map (fun (q : Option String) => q.bind (fun (s : String) => T.lookup s))) | c => c) } : Pl.Expr Float); "
            f"let SBT : List (UInt64 × String) := {SBT}; "
            "let SB := fun (o : Option Float) => ((match o with | none => \"!none\" | some x => (SBT.lookup x.toBits).getD \"?\") : String); ")


def str_texts(df: pl.DataFrame) -> set[str]:
    return {v for n in df.columns if df.schema[n] == pl.String for v in df.get_column(n).to_list() if v is not None}


# ---------------------------------------------------------------- slices
def lines(path: Path) -> tuple[str, list[str]]:
    t = path.read_text().splitlines()
    return t[0], t[1:]


def fields(line: str) -> list[str]:
    return line.split(",")


def num(s: str):
    try:
        return float(s)
    except ValueError:
        return None


def pick_train(kind: str, n: int, data: list[str]) -> list[str]:
    if kind == "mixed":
        return [data[i] for i in sorted(rng.sample(range(len(data)), n))]
    if kind == "complete":
        pool = [i for i in range(len(data)) if num(fields(data[i])[6]) is not None and num(fields(data[i])[11]) is not None]
        return [data[i] for i in sorted(rng.sample(pool, n))]
    def edge(f):
        a, u, d, l90, dep, inc = num(f[3]), num(f[2]), num(f[5]), num(f[8]), num(f[11]), num(f[6])
        return ((a is not None and (a < 22 or a > 100)) or (u is not None and u > 10) or (d is not None and d > 5000)
                or (l90 is not None and l90 >= 90) or (dep is not None and dep >= 8) or (inc is not None and (inc == 0 or inc >= 100000)))
    pool = [i for i in range(len(data)) if edge(fields(data[i]))]
    k = (2 * n) // 3
    picked = set(rng.sample(pool, k)) | set(rng.sample(range(len(data)), n - k))
    return [data[i] for i in sorted(picked)]


def fe_run(header: str, body: list[str], split_ids: list[str]) -> dict:
    rec: dict = {"files": [], "imported": None, "stop": False}
    o_w, o_i = sc.write_sas_csv, sc.proc_import_csv

    def w_import(path, guessingrows=20):
        df = o_i(path, guessingrows=guessingrows)
        rec["imported"] = df
        return df

    with tempfile.TemporaryDirectory() as d:
        ind, outd = Path(d) / "in", Path(d) / "out"
        ind.mkdir()
        (ind / "cs-training.csv").write_text(header + "\n" + "\n".join(body) + "\n")
        (ind / "split.csv").write_text("row_id\n" + "".join(x + "\n" for x in split_ids))
        sc.proc_import_csv = w_import
        sc.write_sas_csv = lambda df, path, formats=None: rec["files"].append((Path(path).name, df))
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                fe.run(ind, outd, split_ids=ind / "split.csv")
        except ValueError as e:
            assert str(e) == "Feature engineering stopped. Nothing is exported.", e
            rec["stop"] = True
        finally:
            sc.write_sas_csv, sc.proc_import_csv = o_w, o_i
    return rec


def tdig(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_table(df)))


def main() -> None:
    hdr, data = lines(TRAIN)
    split_all = SPLIT.read_text().splitlines()[1:]
    st = Suite("fz10c_stale_real_run", generator="port-to-lean/diffeval/units/fz10c_stale_real_gen.py")
    stats = []
    draws_total = 0
    _o_draw = fe._split_draw
    for kind, n in RUN_SLICES:
        body = pick_train(kind, n, data)
        ids = [fields(x)[0] for x in body]
        idset = set(ids)
        restricted = [x for x in split_all if x in idset]
        nt = (7 * n + 9) // 10
        fits = (restricted[:nt] + [x for x in ids if x not in set(restricted[:nt])])[:nt]
        B12.clear()
        cases, terms, texts = [], [], set()
        tab = None
        for variant, sp, full in (("restricted", restricted, True), ("fits", fits, False)):
            drew = []
            fe._split_draw = lambda a, b, seed=42, _d=drew: (_d.append((len(a), b)), _o_draw(a, b, seed))[1]
            try:
                r = fe_run(hdr, body, sp)
            finally:
                fe._split_draw = _o_draw
            imp = r["imported"]
            assert all(imp.schema[c] in (pl.Float64, pl.String) for c in imp.columns), imp.schema
            ok = gr.precond(imp, r["stop"], [float(x) for x in sp])
            assert ok, (kind, n, variant)
            sp_df = pl.DataFrame({"row_id": [float(x) for x in sp]}, schema={"row_id": pl.Float64})
            res = [0] if r["stop"] else [len(r["files"])] + [cmp.digest(cmp.tok_str(f) + cmp.tokens(cmp.canon_table(x))) for f, x in r["files"]]
            if not r["stop"]:
                assert [f for f, _ in r["files"]] == FILES_FE
            exp = cmp.digest([tdig(imp), tdig(sp_df)] + res)
            texts |= str_texts(imp)
            tab = lean_table(imp)
            what = "stops" if r["stop"] else f"{r['files'][1][1].height} train / {r['files'][2][1].height} validation"
            draws_total += bool(drew)
            cases.append((f"real {kind} slice of {n} lines, split {variant} ({len(sp)} ids, {'draws' if drew else 'used as given'}): {what}",
                          "run", exp, {"fz": "kept"}))
            spl = "[" + ", ".join(f"[(\"row_id\", Tabular.Cell.num (some (Float.ofNat {int(x)})))]" for x in sp) + "]"
            terms.append(f"(let sp : Tabular.Table Float := {spl}; dg ([u (dg (tA t)), u (dg (tA sp))] ++ "
                         f"(match run (α := Float) {'true' if full else 'false'} IB SB (some t) sp with | none => [0] | some fs => "
                         "fs.length.toUInt64 :: fs.map (fun (p : String × Tabular.Table Float) => u (dg (tS p.1 ++ tA p.2))))))")
            stats.append((kind, n, variant, len(sp), bool(drew), what))
        lets = gr.MINI + HELP + lookups(texts) + f"let t : Tabular.Table Float := {tab}; "
        st.ints(lets, "[" + ", ".join(terms) + "]", cases, gen=False, use_kit=False)
    st.write()
    for s in stats:
        print("run", s)
    print("run slices that draw:", draws_total, "of", 2 * len(RUN_SLICES))

    # ------------------------------------------------------------ predict
    model = json.loads((REAL / "model.json").read_text())
    ref = json.loads((HERE.parent / "work" / "fz10_real.expected.json").read_text())["model"]
    assert model["intercept"] == ref["intercept"] and list(model["coefficients"]) == ref["names"]
    med_tab = sc.proc_import_csv(REAL / "income_medians.csv")
    th, tdata = lines(TEST)
    sp2 = Suite("fz10c_stale_real_pp", generator="port-to-lean/diffeval/units/fz10c_stale_real_gen.py")
    for kind, n in PP_SLICES:
        if kind == "random":
            body = [tdata[i] for i in sorted(rng.sample(range(len(tdata)), n))]
        else:
            pool = [i for i in range(len(tdata)) if num(fields(tdata[i])[6]) is not None and num(fields(tdata[i])[11]) is not None]
            body = [tdata[i] for i in sorted(rng.sample(pool, n))]
        B12.clear()
        rec = {"files": []}
        o_w = sc.write_sas_csv
        with tempfile.TemporaryDirectory() as d:
            dd, ind, outd = Path(d) / "data", Path(d) / "in", Path(d) / "out"
            dd.mkdir(); ind.mkdir()
            (dd / "cs-test.csv").write_text(th + "\n" + "\n".join(body) + "\n")
            (ind / "model.json").write_text((REAL / "model.json").read_text())
            (ind / "model_coefficients.csv").write_text((REAL / "model_coefficients.csv").read_text())
            raw = sc.proc_import_csv(dd / "cs-test.csv", guessingrows=None)
            sc.write_sas_csv = lambda df, path, formats=None: rec["files"].append((Path(path).name, df))
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    pr.run(ind, outd, data_dir=dd, income_medians=REAL / "income_medians.csv")
                outcome = "files"
            except ValueError as e:
                assert str(e) == "Test set scoring stopped. Nothing is exported.", e
                outcome = "stop"
            finally:
                sc.write_sas_csv = o_w
        assert all(raw.schema[c] in (pl.Float64, pl.String) for c in raw.columns)
        exp = b4.w([0] if outcome == "stop" else [1] + [gp.file_digest(f, df) for f, df in rec["files"]])
        H = "[" + ", ".join(f"({lt.lean_str(c)}, {'true' if raw.schema[c] == pl.String else 'false'})" for c in raw.columns) + "]"
        co = "[" + ", ".join(f"({lt.lean_str(k)}, {lt.lean_float(v)})" for k, v in model["coefficients"].items()) + "]"
        texts = str_texts(raw) | str_texts(med_tab)
        lets = (gr.MINI + b4.W + HELP + lookups(texts) + "let tL := fun (ns : List String) => ns.length.toUInt64 :: ns.flatMap tS; "
                f"let t : Tabular.Table Float := {lean_table(raw)}; let M : Tabular.Table Float := {lean_table(med_tab)}; ")
        body_l = (f"[W (match run_py_py (α := Float) true IB {lt.lean_float(model['intercept'])} {co} SB true (some ({H}, t)) (some M) with "
                  "| none => [0] | some fs => 1 :: fs.map (fun (f : String × List String × Tabular.Table Float) => dg (tS f.1 ++ tL f.2.1 ++ tA f.2.2)))]")
        what = outcome if outcome == "stop" else ", ".join(f"{f} {df.height} rows" for f, df in rec["files"])
        sp2.ints(lets, body_l, [(f"real cs-test {kind} slice of {n} lines: {what}", "run_py_py", exp, {"fz": "kept"})], gen=False, use_kit=False)
        print("run_py_py", kind, n, what, "| String columns:", [c for c in raw.columns if raw.schema[c] == pl.String])
    sp2.write()


if __name__ == "__main__":
    main()
