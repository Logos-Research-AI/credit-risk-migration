"""T11 (update after verification, 2026-11-16): def:run_py_py (predict.run) against REAL runs.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t11_gen.py
      -> diffeval/work/t11_run.json (+ .inputs.json); eval on def:zz_carrier_p / zz_carrier_p;
  compare: ... python diffeval/compare.py diffeval/work/t11_run.json diffeval/work/t11_run.out.txt

Python side: the real feature_engineering.run and train.run on the whole legacy/data training file
give income_medians.csv, model.json and model_coefficients.csv; then the real predict.run on a test
file (header and chosen data lines of the named file, verbatim; or the whole file when short).
`sas_compat.write_sas_csv` is replaced by a recorder (the frames handed to it, in call order, are
the expected files); a line tracer copies `test_raw` at line 82 (what lines 42-79 produced: the
import parameter). A run that raises ValueError("Test set scoring stopped...") and leaves no file
is the expected `none`.
Lean side: run_py_py full ib IC CO sb mce cs_test medians with
  cs_test = some (header with kinds, rows) from the traced frame; medians = the table
  proc_import_csv(income_medians.csv) returns, or none; mce = whether model_coefficients.csv exists;
  ib / sb = lookup tables of the real input_best32 (every text of the String columns, as it is and
  stripped of blanks, and every BEST12 text) and of the real sas_best12; IC / CO = model.json.
Result encoding: none -> [0]; some files -> 1 :: one digest per file of (name, column names, table).
"""
from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
import t8_gen as t8  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import predict as pr  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

FILES = ["kaggle_submission.csv", "test_predictions.csv"]
SRC = Path(pr.__file__).read_text().splitlines()
assert SRC[81].startswith("    EXPECTED = (")


def pyrun(test_text: str | None, ind: Path, medians: Path, work: Path) -> dict:
    rec: dict = {"files": [], "raw0": "unset"}
    code = pr.run.__code__
    o_write = sc.write_sas_csv

    def w_write(df, path, formats=None):
        rec["files"].append((Path(path).name, df))

    def local(frame, event, arg):
        if event == "line" and frame.f_lineno == 82:
            rec["raw0"] = frame.f_locals.get("test_raw")
        return local

    dd = work / "data"
    dd.mkdir(parents=True)
    if test_text is not None:
        (dd / "cs-test.csv").write_text(test_text)
    outd = work / "out"
    sc.write_sas_csv = w_write
    sys.settrace(lambda f, e, a: local if f.f_code is code else None)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            pr.run(ind, outd, data_dir=dd, income_medians=medians)
        rec["stopped"] = False
    except ValueError as ex:
        assert str(ex) == "Test set scoring stopped. Nothing is exported.", ex
        rec["stopped"] = True
    finally:
        sys.settrace(None)
        sc.write_sas_csv = o_write
    if rec["stopped"]:
        assert rec["files"] == [] and not any((outd / f).exists() for f in FILES)
    else:
        assert [f for f, _ in rec["files"]] == FILES
    return rec


def file_digest(name: str, df: pl.DataFrame) -> int:
    toks = cmp.tok_str(name) + [len(df.columns)]
    for c in df.columns:
        toks += cmp.tok_str(c)
    return cmp.digest(toks + cmp.tokens(cmp.canon_table(df)))


def lean_cs(raw0) -> tuple[str, str, str]:
    """(cs_test term, ib table, sb table)."""
    if raw0 is None:
        return "none", "[]", "[]"
    assert all(dt in (pl.String, pl.Float64) for dt in raw0.dtypes)
    hdr = "[" + ", ".join(f"({lt.lean_str(n)}, {'true' if raw0.schema[n] == pl.String else 'false'})" for n in raw0.columns) + "]"
    rows = t8.lean_table(raw0) if raw0.height > 0 else "[]"
    texts: list[str] = []
    best: dict[int, str] = {}
    for n in raw0.columns:
        s = raw0.get_column(n)
        if s.dtype == pl.String:
            for v in s.to_list():
                if v is not None:
                    texts += [v, v.strip(" ")]
        elif n.upper() in ("MONTHLYINCOME", "NUMBEROFDEPENDENTS"):   # the only numeric columns step 01 renders
            for v in s.to_list():
                if v is not None:
                    t = sc.sas_best12(v)
                    best[lt.bits(v)] = t
                    texts.append(t)
    texts = list(dict.fromkeys(texts))
    vals = pl.DataFrame({"s": texts}, schema={"s": pl.String}).select(sc.input_best32(pl.col("s"))).to_series().to_list()
    ib = "[" + ", ".join(f"({lt.lean_str(t)}, {'none' if v is None else 'some ' + lt.lean_float(v)})" for t, v in zip(texts, vals)) + "]"
    sb = "[" + ", ".join(f"({b}, {lt.lean_str(t)})" for b, t in best.items()) + "]"
    return f"(some ({hdr}, {rows}))", ib, sb


RUN = (
    "let tL := fun (ns : List String) => ns.length.toUInt64 :: ns.flatMap tS; "
    "let enc := fun (r : Option (List (String × List String × Tabular.Table Float))) => ((match r with | none => [0] | some fs => "
    "1 :: fs.map (fun (f : String × List String × Tabular.Table Float) => dg (tS f.1 ++ tL f.2.1 ++ tA f.2.2))) : List Int); "
)


def main():
    s = Suite("t11_run")
    base = Path(tempfile.mkdtemp(prefix="t11_"))
    out, _ = t8.stages_before(t8.REPO / "legacy" / "data" / "cs-training.csv", base / "before", None)
    model = json.loads((out / "model.json").read_text())
    med_ok = out / "income_medians.csv"
    no_model = base / "no_model"
    no_model.mkdir()
    shutil.copy(out / "model.json", no_model / "model.json")
    real = (t8.REPO / "legacy" / "data" / "cs-test.csv").read_text()
    upper = (t8.SCEN / "fix_round5" / "test_header_age_upper" / "cs-test.csv").read_text().splitlines(keepends=True)
    dup = (t8.SCEN / "fix2" / "test_duplicate_id" / "cs-test.csv").read_text().splitlines(keepends=True)
    ids = [ln.split(",")[0] for ln in dup[1:]]
    dup_lines = [ln for ln in dup[1:] if ids.count(ln.split(",")[0]) > 1]
    assert dup_lines
    header_only = (t8.SCEN / "fix_Q1" / "cs-test.csv").read_text()
    assert len(header_only.splitlines()) == 1
    plan = [
        ("legacy/data cs-test[10 lines]", t8.pick(real, 2, 10), out, med_ok),
        ("fix_Q1 cs-test (header line only)", header_only, out, med_ok),
        ("fix_round5/test_header_age_upper[4 lines]", "".join(upper[:5]), out, med_ok),
        ("stop: income_medians.csv absent", t8.pick(real, 2, 3), out, base / "absent.csv"),
        ("stop: model_coefficients.csv absent", t8.pick(real, 2, 3), no_model, med_ok),
        ("stop: fix2/test_duplicate_id[its repeated ids + 2 lines]", dup[0] + "".join(dup[1:3] + [x for x in dup_lines if x not in dup[1:3]]), out, med_ok),
        ("stop: cs-test.csv absent", None, out, med_ok),
    ]
    mi = sc.proc_import_csv(med_ok)
    co = "[" + ", ".join(f"({lt.lean_str(k)}, {lt.lean_float(float(v))})" for k, v in model["coefficients"].items()) + "]"
    lets = t8.MK + RUN + f"let MT : Tabular.Table Float := {t8.lean_table(mi)}; let CO : List (String × Float) := {co}; "
    lets += ("let go := fun (fl : Bool) (ib : List (String × Option Float)) (sb : List (UInt64 × String)) (mce : Bool) "
             "(C : Option (List (String × Bool) × Tabular.Table Float)) (M : Option (Tabular.Table Float)) => "
             f"enc (run_py_py fl (mkIb ib) {lt.lean_float(float(model['intercept']))} CO (mkSb sb) mce C M); ")
    calls, cases = [], []
    for k, (name, text, ind, med) in enumerate(plan):
        r = pyrun(text, ind, med, base / f"run{k}")
        mce = (ind / "model_coefficients.csv").exists()
        mterm = "(some MT)" if med.exists() else "none"
        if isinstance(r["raw0"], str):   # stopped at :31-37, before the import: any cs_test gives none
            raw0 = sc.proc_import_csv(base / f"run{k}" / "data" / "cs-test.csv", guessingrows=None)
        else:
            raw0 = r["raw0"]
        cs, ib, sb = lean_cs(raw0)
        if isinstance(r["raw0"], str):   # the run stops before any text is read
            ib, sb = "[]", "[]"
        lets += f"let C{k} : Option (List (String × Bool) × Tabular.Table Float) := {cs}; let I{k} : List (String × Option Float) := {ib}; let B{k} : List (UInt64 × String) := {sb}; "
        for fl in ("true", "false"):
            calls.append(f"go {fl} I{k} B{k} {'true' if mce else 'false'} C{k} {mterm}")
            if r["stopped"]:
                cases.append((f"{name} full={fl}: stopped (none)", "run_py_py", 0))
            else:
                cases.append((f"{name} full={fl}: completed (some)", "run_py_py", 1))
                cases += [(f"{name} full={fl}: {f}", "run_py_py", file_digest(f, df)) for f, df in r["files"]]
        print(f"[{name}] stopped={r['stopped']} files={[(f, df.shape, df.columns[:3]) for f, df in r['files']]}")
    s.ints(lets, " ++ ".join("(" + c + ")" for c in calls), cases, table=True)
    for inp in s.inputs:
        inp["item"], inp["decl"] = t8.CARRIER
    s.notes = {"run_py_py": "real feature_engineering.run + train.run on legacy/data, then real predict.run; files captured at write_sas_csv, "
                            "import parameter traced at line 82; stops = ValueError and no file; full = true and false both compared"}
    s.write()
    shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()
