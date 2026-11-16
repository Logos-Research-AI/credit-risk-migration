"""T8 (update after verification, 2026-11-16): differential test of the three re-translated steps

  def:predict_run_01_clean, def:predict_run_02_medians, def:predict_run_04_imputed

against REAL runs of the port.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t8_gen.py
      -> diffeval/work/t8_steps.json, t8_steps.inputs.json
  (eval_decl each input on def:zz_carrier_p / zz_carrier_p; outputs one per line in
   diffeval/work/t8_steps.out.txt)
  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/compare.py diffeval/work/t8_steps.json diffeval/work/t8_steps.out.txt

Python side, per scenario (a folder with cs-training.csv and cs-test.csv):
  1. the real `feature_engineering.run` on the WHOLE training file (split: inputs/split_ids.csv)
     writes income_medians.csv;
  2. the real `train.run` on its output writes model.json / model_coefficients.csv (where the
     training file cannot be fitted, fix_Q1, the model of the real-data run is copied: steps 01-04
     do not read it);
  3. the real `predict.run` on the test file (whole when small; else the header and chosen data
     lines, verbatim) with that income_medians.csv. A profile hook copies the locals of `run` at
     return: test_raw (after the input check), test_raw_clean, train_income_medians, test_cleaned,
     test_imputed.
Lean side, one eval input per scenario:
  F    the frame test_raw Python had (built from integer codes; its digest is compared first);
  MT   the table `proc_import_csv(income_medians.csv)` returns (digest of Pl.ofTable compared with
       the Python import through the result of step 02);
  ib   test double of sas_compat.input_best32: evaluates its argument, requires a String column and
       maps every text through a table text -> value computed with the REAL input_best32 (a text
       that is not in the table gives -777, a non-String argument a column of length 0);
  sb   test double of sas_compat.sas_best12: a table float bits -> text computed with the REAL
       sas_best12 on the non-null values of the numeric MonthlyIncome / NumberOfDependents columns
       (a value not in the table gives "?");
  s1 = predict_run_01_clean ib sb F; md = predict_run_02_medians MT; s3 = predict_run_03_cleaned s1
  (unchanged accepted item); s4 = predict_run_04_imputed s3 md. Each is compared with the local of
  the real run.
"""
from __future__ import annotations

import contextlib
import io
import shutil
import sys
import tempfile
from decimal import Decimal
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
KIT_ROOT = HERE.parents[1]          # migration/port-to-lean
REPO = KIT_ROOT.parents[1]
sys.path.insert(0, str(HERE.parent))

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import predict as pr  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train as tr  # noqa: E402

CARRIER = ("def:zz_carrier_p", "zz_carrier_p")
SCEN = REPO / "judge" / "scenarios"
STEP_LOCALS = [
    ("test_raw", "input (test_raw)"),
    ("test_raw_clean", "predict_run_01_clean"),
    ("train_income_medians", "predict_run_02_medians"),
    ("test_cleaned", "predict_run_03_cleaned"),
    ("test_imputed", "predict_run_04_imputed"),
]


def quiet(f, *a, **k):
    with contextlib.redirect_stdout(io.StringIO()):
        return f(*a, **k)


def stages_before(train_csv: Path, work: Path, fallback_model: Path | None) -> tuple[Path, str]:
    """feature_engineering.run and train.run on the whole training file -> (output dir, how the model was got)."""
    d = work / "data"
    d.mkdir(parents=True)
    shutil.copy(train_csv, d / "cs-training.csv")
    out = work / "out"
    quiet(fe.run, d, out, split_ids=KIT_ROOT / "inputs" / "split_ids.csv")
    assert (out / "income_medians.csv").exists()
    how = "train.run"
    try:
        quiet(tr.run, out, out)
        assert (out / "model.json").exists() and (out / "model_coefficients.csv").exists()
    except Exception as e:  # noqa: BLE001
        assert fallback_model is not None, e
        for f in ("model.json", "model_coefficients.csv"):
            shutil.copy(fallback_model / f, out / f)
        how = f"model copied from the real-data run (train.run: {type(e).__name__})"
    return out, how


def pyrun(test_text: str, out: Path, work: Path) -> dict:
    rec: dict = {}

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is pr.run.__code__:
            rec["locals"] = dict(frame.f_locals)

    dd = work / "testdata"
    dd.mkdir(parents=True)
    (dd / "cs-test.csv").write_text(test_text)
    sys.setprofile(prof)
    try:
        quiet(pr.run, out, work / "pred", data_dir=dd, income_medians=out / "income_medians.csv")
    finally:
        sys.setprofile(None)
    assert (work / "pred" / "kaggle_submission.csv").exists()
    rec["medians_import"] = sc.proc_import_csv(out / "income_medians.csv")
    rec["medians_text"] = (out / "income_medians.csv").read_text()
    return rec


def pick(text: str, n_head: int, n_total: int) -> str:
    """Header, the first n_head data lines and further lines chosen for their content, verbatim, in file order."""
    lines = text.splitlines(keepends=True)
    head, data = lines[0], lines[1:]
    if len(data) <= n_total:
        return text
    f = [ln.rstrip("\r\n").split(",") for ln in data]
    crit = [
        lambda r: r[6] == "NA" and float(r[3]) < 30,
        lambda r: r[6] == "NA" and 30 <= float(r[3]) < 40,
        lambda r: r[6] == "NA" and 40 <= float(r[3]) < 50,
        lambda r: r[6] == "NA" and 50 <= float(r[3]) < 60,
        lambda r: r[6] == "NA" and float(r[3]) >= 60,
        lambda r: r[11] == "NA",
        lambda r: r[6] not in ("NA", "") and float(r[6]) > 200000,
        lambda r: r[6] == "0",
        lambda r: "E" in r[2] or "E" in r[5],
        lambda r: r[6] not in ("NA", "") and len(r[6]) > 12,
        lambda r: r[11] not in ("NA", "") and float(r[11]) >= 6,
        lambda r: float(r[3]) in (30.0, 40.0, 50.0, 60.0),
    ]
    chosen = set(range(n_head))
    k = 0
    while len(chosen) < n_total and k < 20 * len(crit):
        p = crit[k % len(crit)]
        k += 1
        for i in range(n_head, len(f)):
            if i in chosen:
                continue
            try:
                ok = p(f[i])
            except (ValueError, IndexError):
                ok = False
            if ok:
                chosen.add(i)
                break
    return head + "".join(data[i] for i in sorted(chosen))


def known_income_only(text: str, n: int) -> str:
    """Header and the first n data lines whose MonthlyIncome and NumberOfDependents are stated numbers:
    the import types both columns numeric, so step 01 takes the BEST12 branch for both."""
    lines = text.splitlines(keepends=True)
    keep = [ln for ln in lines[1:] if ln.rstrip("\r\n").split(",")[6] != "NA" and ln.rstrip("\r\n").split(",")[11] != "NA"]
    wide = [ln for ln in keep if len(ln.split(",")[6]) >= 6][:2]
    return lines[0] + "".join(dict.fromkeys(keep[:n] + wide))


# ---------------------------------------------------------------- Lean terms
MK = (
    "let cs := fun (s : String) => ((s.splitOn \",\").map (fun (x : String) => (x.toInt?).getD (-1))).toArray; "
    "let mkT := fun (names : List String) (kinds : List Nat) (strs : String) (codes : String) => "
    "(let C := cs codes; let S := (strs.splitOn \",\").toArray; "
    "((List.range (C.size / names.length)).map (fun (i : Nat) => (List.range names.length).map (fun (j : Nat) => "
    "let v : Int := C.getD (i * names.length + j) (-1); "
    "(names.getD j \"\", (if kinds.getD j 0 == 0 then Tabular.Cell.num (if v < 0 then none else some "
    "(Float.ofScientific (v.toNat / 64) true (v.toNat % 64))) else Tabular.Cell.str (if v < 0 then none else some "
    "(S.getD v.toNat \"\")) : Tabular.Cell Float)))) : Tabular.Table Float)); "
    # ib: the input_best32 double; sb: the sas_best12 double
    "let mkIb := fun (tab : List (String × Option Float)) (e : Pl.Expr Float) => (({ eval := fun (g : Option (List (List Nat))) (fr : Pl.Frame Float) => "
    "(match e.eval g fr with | .str v => Pl.Col.f64 (v.map (fun (o : Option String) => (match o with | none => none | some s => "
    "(match tab.lookup s with | some r => r | none => some (-777.0)) : Option Float))) | _ => Pl.Col.f64 []), "
    "name := e.name, ser := Pl.node [e.ser] }) : Pl.Expr Float); "
    "let mkSb := fun (tab : List (UInt64 × String)) (o : Option Float) => ((match o with | none => \"!none\" | some x => "
    "(match tab.lookup x.toBits with | some s => s | none => \"?\")) : String); "
)
ACC: dict = {"lets": "", "calls": [], "cases": []}
BODY = (
    "let runS := fun (F : Pl.Frame Float) (MT : Tabular.Table Float) (ib : Pl.Expr Float → Pl.Expr Float) (sb : Option Float → String) => ("
    "let s1 := predict_run_01_clean ib sb F; "
    "let md := predict_run_02_medians MT; "
    "let s3 := predict_run_03_cleaned s1; "
    "let s4 := predict_run_04_imputed s3 md; "
    "([dg (tR F), dg (tR s1), dg (tR md), dg (tR s3), dg (tR s4)] : List Int)); "
)


def lean_table(df: pl.DataFrame) -> str:
    """`mkT names kinds strs codes` for a frame of Float64 / String columns with at least one row."""
    assert df.height > 0
    kinds, strs, cols = [], [], []
    for n in df.columns:
        s = df.get_column(n)
        if s.dtype == pl.String:
            kinds.append(1)
            codes = []
            for v in s.to_list():
                if v is None:
                    codes.append(-1)
                else:
                    if v not in strs:
                        strs.append(v)
                    codes.append(strs.index(v))
        else:
            assert s.dtype == pl.Float64, (n, s.dtype)
            kinds.append(0)
            codes = []
            for v in s.to_list():
                if v is None:
                    codes.append(-1)
                    continue
                assert v == v and v >= 0 and abs(v) != float("inf") and lt.bits(v) != lt.bits(-0.0), (n, v)
                sign, digits, exp = Decimal(repr(v)).as_tuple()
                m = int("".join(map(str, digits)))
                if exp > 0:
                    m, exp = m * 10 ** exp, 0
                assert -exp < 64
                assert float(f"{m}e{exp}") == v
                codes.append(m * 64 + (-exp))
        cols.append(codes)
    flat = ",".join(str(c[i]) for i in range(df.height) for c in cols)
    assert all("," not in x and '"' not in x and "\\" not in x for x in strs)
    return (f"(mkT [{', '.join(lt.lean_str(n) for n in df.columns)}] [{', '.join(map(str, kinds))}] "
            f"{lt.lean_str(','.join(strs))} \"{flat}\")")


def lean_empty_frame(df: pl.DataFrame) -> str:
    assert df.height == 0
    cols = []
    for n in df.columns:
        k = {pl.String: "str", pl.Float64: "f64"}[df.schema[n]]
        cols.append(f"({lt.lean_str(n)}, Pl.Col.{k} [])")
    return "[" + ", ".join(cols) + "]"


def doubles(test_raw: pl.DataFrame) -> tuple[str, str, str]:
    """The two lookup tables, from the REAL functions, and a note of what they hold."""
    texts: list[str] = []
    best: list[tuple[float, str]] = []
    for n in ("MonthlyIncome", "NumberOfDependents"):
        s = test_raw.get_column(n)
        if s.dtype == pl.String:
            texts += [v for v in s.to_list() if v is not None]
        else:
            assert s.dtype == pl.Float64
            for v in s.to_list():
                if v is not None:
                    t = sc.sas_best12(v)
                    best.append((v, t))
                    texts.append(t)
    texts = list(dict.fromkeys(texts))
    vals = pl.DataFrame({"s": texts}, schema={"s": pl.String}).select(sc.input_best32(pl.col("s"))).to_series()
    assert vals.dtype == pl.Float64
    ib = "[" + ", ".join(f"({lt.lean_str(t)}, {'none' if v is None else 'some ' + lt.lean_float(v)})"
                         for t, v in zip(texts, vals.to_list())) + "]"
    seen: dict[int, str] = {}
    for v, t in best:
        seen[lt.bits(v)] = t
    sb = "[" + ", ".join(f"({b}, {lt.lean_str(t)})" for b, t in seen.items()) + "]"
    changed = [(v, t) for v, t in best if float(t) != v] if best else []
    note = f"input_best32 table {len(texts)} texts; sas_best12 table {len(seen)} values, {len(set(changed))} changed by BEST12"
    return ib, sb, note


def scenario(s: Suite, name: str, train_csv: Path, test_text: str, work: Path, fallback: Path | None,
             out: Path | None = None) -> Path:
    if out is None:
        out, how = stages_before(train_csv, work / "before", fallback)
    else:
        how = "stages before: shared with the scenario above"
    r = pyrun(test_text, out, work / "run")
    L = r["locals"]
    raw = L["test_raw"]
    mi = r["medians_import"]
    ibt, sbt, note = doubles(raw)
    k = len(ACC["calls"])
    ACC["lets"] += (f"let F{k} : Pl.Frame Float := " + (f"Pl.ofTable {lean_table(raw)}" if raw.height > 0 else lean_empty_frame(raw)) + "; ")
    ACC["lets"] += f"let MT{k} : Tabular.Table Float := {lean_table(mi)}; "
    ACC["calls"].append(f"runS F{k} MT{k} (mkIb {ibt}) (mkSb {sbt})")
    ACC["cases"] += [(f"{name}: {loc}", unit, cmp.digest(cmp.tokens(cmp.canon_frame(L[loc])))) for loc, unit in STEP_LOCALS]
    kinds = {n: str(raw.schema[n]) for n in ("MonthlyIncome", "NumberOfDependents")}
    imp = L["test_imputed"]
    print(f"[{name}] {how}; test rows={raw.height} kinds={kinds}; {note}\n"
          f"    medians file: {r['medians_text']!r}\n"
          f"    medians frame: {L['train_income_medians'].schema} ; imputed rows={imp.height} "
          f"missing income rows={int(imp.get_column('MonthlyIncome_missing').sum() or 0)} null monthly_income={imp.get_column('monthly_income').null_count()}")
    return out


def main(only: set[str] | None):
    s = Suite("t8_steps")
    s.item, s.decl = CARRIER
    for i in s.inputs:
        i["item"], i["decl"] = CARRIER
    base = Path(tempfile.mkdtemp(prefix="t8_"))
    real_train = REPO / "legacy" / "data" / "cs-training.csv"
    real_test = (REPO / "legacy" / "data" / "cs-test.csv").read_text()
    want = lambda n: only is None or any(o in n for o in only)  # noqa: E731
    real_out = None
    # the real-data run comes first: its model is the fallback where a scenario cannot be fitted
    real_out = scenario(s, "legacy/data cs-test[15 lines]", real_train, pick(real_test, 3, 15), base / "real", None)
    scenario(s, "legacy/data cs-test[stated income]", real_train, known_income_only(real_test, 3), base / "real_num", None, out=real_out)
    for name, folder in (("fix_Q13", "fix_Q13"), ("fix_Q14", "fix_Q14"), ("fix_Q1", "fix_Q1"),
                         ("fix2/q13_median_width", "fix2/q13_median_width")):
        if want(name):
            test_text = (SCEN / folder / "cs-test.csv").read_text()
            scenario(s, f"{name} cs-test[{'whole' if len(test_text.splitlines()) <= 25 else '12 lines'}]",
                     SCEN / folder / "cs-training.csv", pick(test_text, 3, 12), base / name.replace("/", "_"), real_out)
    if want("edge_predict"):
        edge_test = (SCEN / "edge_predict" / "cs-test.csv").read_text()
        eo = scenario(s, "edge_predict cs-test[15 lines]", SCEN / "edge_predict" / "cs-training.csv", pick(edge_test, 3, 15), base / "edge", real_out)
        scenario(s, "edge_predict cs-test[stated income]", SCEN / "edge_predict" / "cs-training.csv", known_income_only(edge_test, 3), base / "edge_num", real_out, out=eo)
    # NOT a scenario of the plan: a hand-made test file whose numeric MonthlyIncome needs more than
    # 12 characters, so that BEST12 changes it (no listed scenario reaches that on the predict side)
    if want("handmade"):
        hm = real_test.splitlines(keepends=True)[0] + (
            "1,,0.5,25,0,0.3,1234567890123,4,0,0,0,0\n"
            "2,,0.2,35,1,0.1,0.1234567890123,2,0,1,0,1\n"
            "3,,1.2,61,0,0.7,123456789012,9,2,0,1,2\n")
        scenario(s, "handmade wide numeric income (not a plan scenario)", real_train, hm, base / "hand", None, out=real_out)
    s.ints(MK + BODY + ACC["lets"], " ++ ".join("(" + c + ")" for c in ACC["calls"]), ACC["cases"], table=False)
    for inp in s.inputs:
        inp["item"], inp["decl"] = CARRIER
    s.notes = {u: "real feature_engineering.run + train.run + predict.run; locals of predict.run captured at return; "
                  "input_best32 / sas_best12 doubles are lookup tables of the real functions" for _, u in STEP_LOCALS}
    s.write()
    shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
