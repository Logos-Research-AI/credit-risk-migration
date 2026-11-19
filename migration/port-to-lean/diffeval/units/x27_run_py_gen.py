"""x27 evaluation (2026-11-18, after the fifth port diff): def:run_py (metrics_calculation.py:82-609)
on def:zz_carrier_e, against the REAL metrics_calculation.run. Built from t16_gen.py (helpers copied, its
main() not run). Scenarios: port/tests/data/x27_one_class/C60 (a header-only risk_scores_validation.csv:
valid_exists False; training scores with every credit_risk_score blank, imported as a String column of
nulls, cut to that column); judge/scenarios/real_metrics first 200 / 300 lines cut to the columns read
(a fitted sample, valid_exists True). Expected: digests of the two input tables, the number of files,
one digest per (file name, table), in write order.

  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/x27_run_py_gen.py
  -> work/x27_run_py.json, .inputs.json; eval each input on def:zz_carrier_e / zz_carrier_e;
     outputs one per line in work/x27_run_py.out.txt; python3 diffeval/compare.py work/x27_run_py.json work/x27_run_py.out.txt
"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_e", "zz_carrier_e")

import t1_gen as t1  # noqa: E402  (wraps math.fsum and records its calls in t1.FSUM)
import b6_gen as b6  # noqa: E402  (table digests, lookup tables)
import compare as cmp  # noqa: E402
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import metrics_calculation as mc  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

SCEN = ROOT / "judge" / "scenarios"
U = "run_py"
SIX = ["validation_summary.csv", "decile_analysis.csv", "threshold_analysis.csv", "ks_statistic.csv",
       "calibration_plot.csv", "model_performance_metrics.csv"]
PRINTED = ["printed_roc_metrics.csv", "printed_cumulative_lift.csv", "printed_psi_calculation.csv"]


def key(x):
    return None if x is None else cmp.fbits(float(x))


def pyrun(vtext: str | None, ttext: str | None) -> dict:
    """the real mc.run on a temp directory holding the given files (None: the file is absent)"""
    rec: dict = {"files": [], "best": {}, "d8": {}, "raised": None, "locals": None}
    o_write, o_best, o_d8 = sc.write_sas_csv, sc.sas_best, sc.sas_d8

    def w_best(x, width):
        r = o_best(x, width)
        if width == 8 and sys._getframe(1).f_code is mc._into_float.__code__:
            assert rec["best"].setdefault(key(x), r) == r
        return r

    def w_d8(x):
        r = o_d8(x)
        assert rec["d8"].setdefault(key(x), r) == r
        return r

    def w_write(df, path, formats=None):
        rec["files"].append((Path(path).name, df))

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is mc.run.__code__:
            rec["locals"] = dict(frame.f_locals)

    t1.FSUM.clear()
    with tempfile.TemporaryDirectory() as d:
        ind, outd = Path(d) / "in", Path(d) / "out"
        ind.mkdir()
        outd.mkdir()
        for n in SIX + PRINTED:  # results of an earlier run
            (outd / n).write_text("earlier run\n")
        if vtext is not None:
            (ind / "risk_scores_validation.csv").write_text(vtext)
            rec["valid"] = sc.proc_import_csv(ind / "risk_scores_validation.csv", guessingrows=20)
        if ttext is not None:
            (ind / "risk_scores_train.csv").write_text(ttext)
            rec["train"] = sc.proc_import_csv(ind / "risk_scores_train.csv", guessingrows=20)
        sc.write_sas_csv, sc.sas_best, sc.sas_d8 = w_write, w_best, w_d8
        sys.setprofile(prof)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                mc.run(ind, outd)
        except ValueError as e:
            rec["raised"] = str(e)
        finally:
            sys.setprofile(None)
            sc.write_sas_csv, sc.sas_best, sc.sas_d8 = o_write, o_best, o_d8
        rec["left"] = sorted(p.name for p in outd.iterdir())
    rec["fsum"] = dict(t1.FSUM)
    return rec


# ---------------------------------------------------------------- tables as short Lean terms
# value codes of a flat list: mkV base d ds [c, s, c, s, ...]: row i has row_id = base + i,
# default_flag = c % 2, pd_logistic = (c / 2) * 10^-d, credit_risk_score = s * 10^-ds;
# mkR: the same without row_id; mkC ds [s, ...]: the single column credit_risk_score
MK = ("let cell := fun (x : Float) => (Tabular.Cell.num (some x) : Tabular.Cell Float); "
      "let pairs := fun (L : Array Nat) => (List.range (L.size / 2)).map (fun (i : Nat) => (L[2 * i]!, L[2 * i + 1]!)); "
      "let mkR := fun (d ds : Nat) (L : Array Nat) => ((pairs L).map (fun (p : Nat × Nat) => "
      '[("default_flag", cell (Float.ofNat (p.1 % 2))), ("pd_logistic", cell (Float.ofScientific (p.1 / 2) true d)), '
      '("credit_risk_score", cell (Float.ofScientific p.2 true ds))]) : Tabular.Table Float); '
      "let mkV := fun (base d ds : Nat) (L : Array Nat) => ((List.zip (List.range (L.size / 2)) (mkR d ds L)).map "
      '(fun (q : Nat × Tabular.Row Float) => ("row_id", cell (Float.ofNat (base + q.1))) :: q.2) : Tabular.Table Float); '
      'let mkC := fun (ds : Nat) (L : List Nat) => (L.map (fun (s : Nat) => [("credit_risk_score", cell (Float.ofScientific s true ds))]) : Tabular.Table Float); ')
SBPF = b6.SBPF + 'let d8 := fun (x : Option Float) => (match D8.lookup (x.map Float.toBits) with | some s => s | none => "?"); '
# RUN V T : List Int = [digest V, digest T, number of files or -1 when stopped, digest of each (name, table)]
RUN = ("let files := fun (r : Option (List (String × Tabular.Table Float))) => (match r with | none => [(-1 : Int)] "
       "| some fs => (fs.length : Int) :: fs.map (fun (p : String × Tabular.Table Float) => dg (tS p.1 ++ tA p.2)) : List Int); "
       "let RUN := fun (V T : Tabular.Table Float) => [dg (tA V), dg (tA T)] ++ files (run_py sb pf d8 today FS (some V) (some T)); ")


def dec(vals: list[float], cap: int = 13) -> int:
    for d in range(cap + 1):
        if all(cmp.fbits(float(f"{round(x * 10**d)}e-{d}")) == cmp.fbits(x) for x in vals):
            return d
    raise AssertionError("no decimal scale")


def vcodes(df: pl.DataFrame, d: int, ds: int) -> str:
    out = []
    for f, p, s in df.select("default_flag", "pd_logistic", "credit_risk_score").iter_rows():
        assert f in (0.0, 1.0) and p is not None and s is not None and p >= 0 and s >= 0
        out += [round(p * 10**d) * 2 + int(f), round(s * 10**ds)]
    return "#[" + ", ".join(map(str, out)) + "]"


def table_term(df: pl.DataFrame) -> str:
    if df.height == 0:
        return "([] : Tabular.Table Float)"
    if df.columns == ["credit_risk_score"] and df.schema["credit_risk_score"] == pl.String:
        assert df.get_column("credit_risk_score").null_count() == df.height
        return f'(List.replicate {df.height} [("credit_risk_score", (Tabular.Cell.str none : Tabular.Cell Float))])'
    assert all(t == pl.Float64 for t in df.dtypes), df.schema
    if df.columns == ["credit_risk_score"]:
        s = df.get_column("credit_risk_score").to_list()
        ds = dec(s)
        return f"(mkC {ds} [" + ", ".join(str(round(x * 10**ds)) for x in s) + "])"
    d, ds = dec(df.get_column("pd_logistic").to_list()), dec(df.get_column("credit_risk_score").to_list())
    if df.columns == ["default_flag", "pd_logistic", "credit_risk_score"]:
        return f"(mkR {d} {ds} {vcodes(df, d, ds)})"
    assert df.columns == ["row_id", "default_flag", "pd_logistic", "credit_risk_score"], df.columns
    rid = df.get_column("row_id").to_list()
    base = int(rid[0])
    assert all(r == base + i for i, r in enumerate(rid))
    return f"(mkV {base} {d} {ds} {vcodes(df, d, ds)})"


def dgt_in(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_table(df)))


class Acc:
    """one eval input: several scenarios sharing the lookup tables"""

    def __init__(self):
        self.best, self.d8, self.fsum, self.today = {}, {}, {}, None
        self.terms, self.cases = [], []

    def take(self, r: dict):
        for a, b in ((self.best, r["best"]), (self.d8, r["d8"]), (self.fsum, r["fsum"])):
            for k, v in b.items():
                assert a.setdefault(k, v) == v
        if r["locals"] is not None and "model_performance_metrics" in r["locals"] and r["locals"]["model_performance_metrics"].height:
            t = r["locals"]["model_performance_metrics"].get_column("validation_date").to_list()[0].isoformat()
            assert self.today in (None, t)
            self.today = t

    def scenario(self, name: str, r: dict):
        assert r["raised"] is None, (name, r["raised"])
        self.take(r)
        names = [n for n, _ in r["files"]]
        area = r["locals"]["roc_stats"].item(0, "Area")
        print(f"[{name}] files written: {names}")
        # a completed run that does not write printed_roc_metrics.csv leaves the earlier one in place
        assert r["left"] == sorted(PRINTED), r["left"]  # the recorder writes nothing: the six were removed
        print(f"[{name}] valid={r['valid'].height} train={r['train'].height} files={len(names)} Area={area} "
              f"ks={r['locals']['ks_statistic'].rows()} valid_exists={r['locals']['valid_exists']}")
        self.terms.append(f"RUN {table_term(r['valid'])} {table_term(r['train'])}")
        c = lambda cid, v: (f"{name}: {cid}", U, v)  # noqa: E731
        self.cases += [c("input table risk_scores_validation", dgt_in(r["valid"])), c("input table risk_scores_train", dgt_in(r["train"])),
                       c(f"number of files ({'with' if area is not None else 'without'} printed_roc_metrics.csv)", len(names))]
        self.cases += [c(n, b6.dgt(n, df)) for n, df in r["files"]]

    def lets(self) -> str:
        t1.FSUM.clear()
        t1.FSUM.update(self.fsum)
        sb, rest = b6.lean_tables(self.best, self.d8).split("] [", 1)
        pf, d8 = rest.split("] [", 1)
        return (t1.fs_let(set(self.fsum))
                + f"let SB : List (Option UInt64 × String) := {sb}]; let PF : List (String × UInt64) := [{pf}]; "
                + f"let D8 : List (Option UInt64 × String) := [{d8}; " + SBPF
                + f"let today : Tabular.Cell Float := Tabular.Cell.str (some {lt.lean_str(self.today or '2000-01-01')}); " + MK + RUN)

    def flush(self, s: Suite, extra_terms: list[str] | None = None, extra_cases: list | None = None):
        body = "(" + " ++ ".join(self.terms + (extra_terms or [])) + ")"
        s.ints(self.lets(), body, self.cases + (extra_cases or []), table=True)


def head_lines(p: Path, n: int | None) -> str:
    ls = p.read_text().splitlines(keepends=True)
    return "".join(ls if n is None else ls[:n + 1])


def cut_columns(text: str, cols: list[str]) -> str:
    """the same lines with only the named columns (cell text verbatim)"""
    ls = text.splitlines()
    hdr = ls[0].split(",")
    ix = [hdr.index(c) for c in cols]
    out = []
    for ln in ls:
        cells = ln.split(",")
        assert len(cells) == len(hdr) and '"' not in ln
        out.append(",".join(cells[i] for i in ix))
    return "\n".join(out) + "\n"



def main() -> None:
    s = Suite("x27_run_py")
    # C60: header-only validation scores, training scores with blank credit_risk_score
    d = ROOT / "port" / "tests" / "data" / "x27_one_class" / "C60"
    vfull, tfull = head_lines(d / "risk_scores_validation.csv", None), head_lines(d / "risk_scores_train.csv", None)
    rfull = pyrun(vfull, tfull)
    tcut = cut_columns(tfull, ["credit_risk_score"])
    r = pyrun(vfull, tcut)
    assert [n for n, _ in r["files"]] == [n for n, _ in rfull["files"]]
    for (n, x), (_, y) in zip(r["files"], rfull["files"], strict=True):
        assert b6.dgt(n, x) == b6.dgt(n, y), n
    print("[C60] valid", r["valid"].schema, "train", r["train"].schema, r["train"].height)
    a = Acc()
    a.scenario("x27_one_class/C60 [training scores cut to credit_risk_score]", r)
    a.flush(s)
    # fitted sample
    d = SCEN / "real_metrics"
    vfull, tfull = head_lines(d / "risk_scores_validation.csv", 200), head_lines(d / "risk_scores_train.csv", 300)
    rfull = pyrun(vfull, tfull)
    r = pyrun(cut_columns(vfull, ["default_flag", "pd_logistic", "credit_risk_score"]), cut_columns(tfull, ["credit_risk_score"]))
    assert [n for n, _ in r["files"]] == [n for n, _ in rfull["files"]]
    for (n, x), (_, y) in zip(r["files"], rfull["files"], strict=True):
        assert b6.dgt(n, x) == b6.dgt(n, y), n
    a = Acc()
    a.scenario("real_metrics [first 200 validation / 300 training lines, the columns the run reads]", r)
    a.flush(s)
    s.notes = {U: "x27 (fifth diff): real mc.run at HEAD, frames captured at write_sas_csv; C60 (valid_exists False) and real_metrics 200/300 (fitted sample)"}
    s.write()
    for i, inp in enumerate(s.inputs):
        (suite_mod.WORK / f"x27_run_py.in{i}.txt").write_text(inp["text"])
        print(i, len(inp["text"]), "chars;", sum(1 for c in s.cases if c["input"] == i), "cases")


def sc_frame(text: str) -> pl.DataFrame:
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.csv"
        p.write_text(text)
        return sc.proc_import_csv(p, guessingrows=20)


main()
