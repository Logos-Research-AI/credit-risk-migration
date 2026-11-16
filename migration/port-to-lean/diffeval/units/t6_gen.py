"""Update after verification, task T6: differential test of def:run (feature_engineering.run,
credit_risk/feature_engineering.py:19-380), the composition of the input check and the steps.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t6_gen.py
      -> diffeval/work/t6_run (.json + .inputs.json)
  (eval_decl each input of work/t6_run.inputs.json on def:zz_carrier_f / zz_carrier_f; save the
   outputs one per line as work/t6_run.out.txt)
  ... python diffeval/compare.py diffeval/work/t6_run.json diffeval/work/t6_run.out.txt

Python side: the REAL feature_engineering.run, nothing of it copied. Each scenario is a temporary
data directory whose cs-training.csv is the header and chosen data lines of a real file, verbatim
(legacy/data or judge/scenarios); the import is the real sas_compat.proc_import_csv; the split
file is a real CSV with the row ids of the slice that inputs/split_ids.csv holds (the first half
of the slice when it holds none or all of them). sas_compat.write_sas_csv is replaced by a
recorder: the (file name, frame) pairs in call order are the expected result; a run that raises
"Feature engineering stopped" is the expected `none`, and the output directory is checked empty.
The whole legacy/data/cs-training.csv is also run once (it must complete with three files).

Lean side: `run full IB SB (some table) split` for full = true and false (Python cannot choose
`full`: both are compared with the same Python result). The table is `Pl.toTable` of the imported
frame written column by column; its digest and the split table's are compared with Python's
first. IB (input_best32) and SB (sas_best12) are lookup tables generated here from the real
sas_compat functions on exactly the texts / numbers the run hands them.
A result is [0] for `none`, else [number of files, digest(name, table) of each file in order].
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import t2_gen as t2  # noqa: E402  (sets the carrier to def:zz_carrier_f)
import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

UNIT = "run"
REPO, ROOT, SCEN = t2.REPO, t2.ROOT, t2.SCEN
REAL = REPO / "legacy" / "data" / "cs-training.csv"
FILES = ["income_medians.csv", "model_features_train.csv", "model_features_validation.csv"]
REAL_SPLIT = set(pl.read_csv(ROOT / "inputs" / "split_ids.csv", infer_schema=False).get_column("row_id").cast(pl.Int64).to_list())


def stage_run(csv_text: str | None, split_text: str) -> dict:
    rec: dict = {"files": [], "imported": None, "locals": None}
    o_write, o_import = sc.write_sas_csv, sc.proc_import_csv

    def w_import(path, guessingrows=20):
        df = o_import(path, guessingrows=guessingrows)
        rec["imported"] = df
        return df

    def prof(fr, event, arg):
        if event == "return" and fr.f_code is fe.run.__code__:
            rec["locals"] = dict(fr.f_locals)

    stopped = False
    with tempfile.TemporaryDirectory() as d:
        ind, outd = Path(d) / "in", Path(d) / "out"
        ind.mkdir()
        outd.mkdir()
        for f in FILES:  # results of an earlier run: removed first (:28-30)
            (outd / f).write_text("old\n")
        if csv_text is not None:
            (ind / "cs-training.csv").write_text(csv_text)
        (ind / "split.csv").write_text(split_text)
        sc.proc_import_csv = w_import
        sc.write_sas_csv = lambda df, path, formats=None: rec["files"].append((Path(path).name, df))
        sys.setprofile(prof)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                fe.run(ind, outd, split_ids=ind / "split.csv")
        except ValueError as e:
            assert str(e) == "Feature engineering stopped. Nothing is exported.", e
            stopped = True
        finally:
            sys.setprofile(None)
            sc.write_sas_csv, sc.proc_import_csv = o_write, o_import
        assert list(outd.iterdir()) == [], "earlier results were not removed"
    assert stopped == (rec["files"] == [])
    assert stopped or [f for f, _ in rec["files"]] == FILES
    return {"stop": stopped, **rec}


def slice_text(path: Path, lines: list[int]) -> str:
    """Header and the chosen data lines (1-based), verbatim."""
    raw = path.read_text().splitlines(keepends=True)
    return raw[0] + "".join(raw[k] for k in lines)


def split_for(ids: list) -> list[int]:
    ints = [int(v) for v in ids if v is not None and v == v and float(v).is_integer()]
    keep = [i for i in ints if i in REAL_SPLIT]
    if not keep or len(keep) == len(ints):
        keep = ints[: max(1, (len(ints) + 1) // 2)]
    return keep or [1]


def dgt(name: str, df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tok_str(name) + cmp.tokens(cmp.canon_table(df)))


def keys_and_best12(r: dict) -> tuple[set[str], dict[int, str]]:
    """The texts the run hands to input_best32 and the numbers it hands to sas_best12."""
    keys: set[str] = set()
    b12: dict[int, str] = {}
    imp = r["imported"]
    if imp is None:
        return keys, b12
    keys |= t2.best32_keys(imp)                      # the input check: cells stripped of blanks
    cr = r["locals"]["credit_raw"]
    for n in ("MonthlyIncome", "NumberOfDependents"):  # step 01
        if n not in cr.columns:
            continue
        col = cr.get_column(n)
        if col.dtype == pl.String:
            keys |= {v for v in col.to_list() if v is not None}
        else:
            for v in col.to_list():
                if v is not None:
                    text = sc.sas_best12(v)
                    b12[cmp.fbits(v)] = text
                    keys.add(text)
    return keys, b12


def lets(keys: set[str], b12: dict[int, str]) -> str:
    B = "[" + ", ".join(f"({k}, {lt.lean_str(v)})" for k, v in sorted(b12.items())) + "]"
    return t2.lets(t2.best32_table(keys)) + (
        f"let B : List (UInt64 × String) := {B}; "
        'let SB := fun (q : Option Float) => (match q with | some x => (B.lookup x.toBits).getD "?" | none => "." : String); '
        'let SP := fun (L : List Float) => (L.map (fun (x : Float) => [("row_id", Tabular.Cell.num (some x))]) : Tabular.Table Float); '
        "let rn := fun (full : Bool) (t : Option (Tabular.Table Float)) (s : Tabular.Table Float) => "
        "(match run (α := Float) full IB SB t s with | none => [0] | some fs => (fs.length : Int) :: "
        "fs.map (fun (p : String × Tabular.Table Float) => dg (tS p.1 ++ tA p.2)) : List Int); "
        "let sn := fun (f : Pl.Frame Float) (s : Tabular.Table Float) => [dg (tA (Pl.toTable f)), dg (tA s)] ++ "
        "rn true (some (Pl.toTable f)) s ++ rn false (some (Pl.toTable f)) s; "
    )


def expected_result(r: dict, name: str, full: str) -> list[tuple]:
    if r["stop"]:
        return [(f"{name}/{full}/none", UNIT, 0)]
    return [(f"{name}/{full}/files", UNIT, len(r["files"]))] + [
        (f"{name}/{full}/{f}", UNIT, dgt(f, df)) for f, df in r["files"]]


def scenario(name: str, path: Path, lines: list[int]):
    probe = stage_run(slice_text(path, lines), "row_id\n1\n")
    imp = probe["imported"]
    split = split_for(imp.get_column(imp.columns[0]).to_list())
    r = stage_run(slice_text(path, lines), "row_id\n" + "".join(f"{i}\n" for i in split))
    assert r["stop"] == probe["stop"]
    split_df = pl.DataFrame({"row_id": [float(i) for i in split]})
    if not r["stop"]:
        ti = r["locals"]["train_ids"]
        assert ti.dtype == pl.Float64 and ti.to_list() == split_df.get_column("row_id").to_list()
    term = f"sn {t2.frame_term(imp)} (SP [" + ", ".join(str(i) for i in split) + "])"
    cases = [(f"{name}/input table", UNIT, cmp.digest(cmp.tokens(cmp.canon_table(imp)))),
             (f"{name}/split table", UNIT, cmp.digest(cmp.tokens(cmp.canon_table(split_df))))]
    cases += expected_result(r, name, "full=true") + expected_result(r, name, "full=false")
    keys, b12 = keys_and_best12(r)
    lo = r["locals"]
    what = "STOP " + " ".join(f"{c}={lo[c]}" for c in t2.COUNTERS) if r["stop"] else (
        f"train={r['files'][1][1].height} valid={r['files'][2][1].height} medians={r['files'][0][1].rows()}")
    print(f"[{name}] rows={imp.height} income={imp.schema.get('MonthlyIncome', imp.schema.get('MONTHLYINCOME'))} "
          f"dependents={imp.schema.get('NumberOfDependents', imp.schema.get('NUMBEROFDEPENDENTS'))} split={split} {what}")
    return term, cases, keys, b12


def real_lines(pred, k: int) -> list[int]:
    raw = pl.read_csv(REAL, infer_schema=False, n_rows=5000).with_row_index("i", offset=1)
    return raw.filter(pred).get_column("i").head(k).to_list()


def main() -> None:
    whole = stage_run(REAL.read_text(), (ROOT / "inputs" / "split_ids.csv").read_text())
    assert not whole["stop"] and [f for f, _ in whole["files"]] == FILES
    print("whole legacy/data/cs-training.csv with inputs/split_ids.csv: completed,",
          [(f, df.height) for f, df in whole["files"]])

    known = (pl.col("MonthlyIncome") != "NA") & (pl.col("NumberOfDependents") != "NA")
    S = [
        ("real_text", REAL, list(range(1, 21))),
        ("real_numeric", REAL, real_lines(known, 12)),
        ("real_long", REAL, real_lines(known & (pl.col("MonthlyIncome").str.len_chars() >= 6), 5) + real_lines(known, 4)),
        ("fix2/q13_median_width", SCEN / "fix2/q13_median_width/cs-training.csv", list(range(1, 13)) + [20, 29, 31, 32]),
        ("fix_Q14", SCEN / "fix_Q14/cs-training.csv", list(range(1, 15))),
        ("fix_Q1", SCEN / "fix_Q1/cs-training.csv", [1, 2]),
        ("fix_Q9", SCEN / "fix_Q9/cs-training.csv", [1, 2]),
        ("fix_Q7", SCEN / "fix_Q7/cs-training.csv", [1]),
        ("fix_G34/income_zero", SCEN / "fix_G34/income_zero/cs-training.csv", [1, 2, 3, 7, 9, 34]),
        ("fix_round5/train_age_exponent", SCEN / "fix_round5/train_age_exponent/cs-training.csv", [1, 2, 3, 7, 9, 30]),
        ("fix_round5/train_header_all_upper", SCEN / "fix_round5/train_header_all_upper/cs-training.csv", list(range(1, 9))),
        ("edge_predict", SCEN / "edge_predict/cs-training.csv", list(range(1, 11))),
        # one stopping scenario per counter
        ("stop columns_ok: fix2/train_extra_column", SCEN / "fix2/train_extra_column/cs-training.csv", [1, 2, 3, 4]),
        ("stop columns_ok: fix2/train_missing_column", SCEN / "fix2/train_missing_column/cs-training.csv", [1, 2, 3, 4]),
        ("stop bad_rows: fix2/train_outcome_2", SCEN / "fix2/train_outcome_2/cs-training.csv", [1, 2, 3, 30]),
        ("stop duplicate_ids: fix2/train_duplicate_id", SCEN / "fix2/train_duplicate_id/cs-training.csv", [1, 2, 3, 30, 31]),
        ("stop known_incomes: fix2/train_no_known_income", SCEN / "fix2/train_no_known_income/cs-training.csv", [1, 2, 3, 9]),
    ]
    groups: list[list] = [[[], [], set(), {}]]
    for name, path, lines in S:
        term, cases, keys, b12 = scenario(name, path, lines)
        g = groups[-1]
        if g[0] and sum(len(x) for x in g[0]) + len(term) > 6500:
            groups.append([[], [], set(), {}])
            g = groups[-1]
        g[0].append(term)
        g[1].extend(cases)
        g[2] |= keys
        g[3].update(b12)
    s = Suite("t6_run")
    for g in groups:
        s.ints(lets(g[2], g[3]), " ++ ".join(g[0]), g[1], table=True)
    # the import raised (no file), and a file with a header and no data row (Pl.ofTable [] has no column)
    absent = stage_run(None, "row_id\n1\n")
    header = stage_run(slice_text(REAL, []), "row_id\n1\n")
    assert absent["stop"] and absent["imported"] is None and header["stop"] and header["imported"].height == 0
    print("absent file: STOP", [absent["locals"][c] for c in t2.COUNTERS], "| header only: STOP",
          [header["locals"][c] for c in t2.COUNTERS])
    s.ints(lets(set(), {}), "rn true none (SP [1]) ++ rn false none (SP [1]) ++ rn true (some []) (SP [1]) ++ rn false (some []) (SP [1])",
           [("absent file/full=true/none", UNIT, 0), ("absent file/full=false/none", UNIT, 0),
            ("header only/full=true/none", UNIT, 0, {"note": "Python: 12 columns, no row, known_incomes = 0; Lean: the table [] has no column, columns_ok = 0"}),
            ("header only/full=false/none", UNIT, 0)], table=True)
    s.notes = {UNIT: "real run on slices of legacy/data and of the scenario files (the whole legacy file run once in Python); "
                     "full = true and false against the same Python result; stops: one per counter, absent file, header only"}
    s.write()


if __name__ == "__main__":
    main()
