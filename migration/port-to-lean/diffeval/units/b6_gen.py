"""Bundle B6 differential tests: metrics_calculation._into_float, the ten step items
def:metrics_run_01 .. _10 and def:run_py (metrics_calculation.run).

  uv run python migration/diffeval/units/b6_gen.py
      -> work/b6_into, b6_run (.json + .inputs.json)
  (eval_decl each work/b6_*.inputs.json on def:zz_carrier / zz_carrier, save work/b6_*.out.txt)
  uv run python migration/diffeval/compare.py migration/diffeval/work/b6_<suite>.json migration/diffeval/work/b6_<suite>.out.txt
  uv run python migration/diffeval/receipts.py units b6

Python side: the REAL `metrics_calculation.run` is called on a temporary input directory that
holds the two CSV files (for the scenario slices: the first lines of the scenario files, verbatim;
for the hand-made tables: a CSV whose import is asserted to be the intended frame). Nothing of
`run` is copied here. The run is instrumented from outside:
  - `sas_compat.write_sas_csv` is replaced by a recorder: the frames Python hands to it, in call
    order, are the expected output tables of `run_py`;
  - a profile hook copies the local variables of `run` when it returns: they are the expected
    results of the step items (roc_stats, auc_summary, the sorted logit_scored_valid, ...);
  - `sas_compat.sas_best` / `sas_d8` are wrapped by recorders: the (argument -> text) pairs that
    occur become the finite lookup tables passed to the Lean as `sas_best`, `parse_float`
    (text -> float(text)) and `sas_d8`; `today` is the cell `Cell.str (some <ISO date of the run>)`.
  - where Python raises (the ValueError of :277 with fix_psi_bins), the expected value is what the
    code gives when it continues: the same real `run` with the module global `abs` shadowed by a
    function returning 0.0, which only disables the test of :276. Such cases carry a note.

Lean side, two eval inputs (the three scenario slices; the hand-made tables), each the
concatenation of one `runS V T SB PF D8` per scenario: the two tables are built inside Lean from short integer
codes (pd_logistic = k / 1000 through Float.ofScientific, default_flag = 0 / 1, row_id = base + i;
the digests of the two tables are compared first, so the inputs are the same bit for bit); the
steps are chained (each step reads what the previous Lean steps produced; every intermediate is
compared with Python's, so a step is tested on the inputs Python had) and `run_py` is evaluated
on the two tables, for fix_psi_bins false and true.

Conventions: Int64 columns that the Lean keeps as Float64 under R-F2I (decile, score_bin,
pred_bin) are cast to Float64 on the Python side before the comparison; the Date column
validation_date is the `.cell` column of the `today` cell (a String cell in the output table).
"""
from __future__ import annotations

# RETIRED 2026-11-16: this script is a record of the port before the update of 2026-11-16 and no longer
# runs: it calls fix_psi_bins; see t12_gen.py to t16_gen.py.
# Its recorded outputs describe the port as it was then.
import sys as _sys

_sys.exit("RETIRED 2026-11-16: " + __file__ + " calls keywords the port no longer has; see the note at its top")


import contextlib
import io
import sys
import tempfile
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(ROOT))

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import metrics_calculation as mc  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

nan, inf = float("nan"), float("inf")
NV, NT = 300, 700  # rows of the scenario slices (validation, training)
F2I = {"decile", "score_bin", "pred_bin"}
FILES = ["validation_summary.csv", "decile_analysis.csv", "threshold_analysis.csv", "ks_statistic.csv",
         "calibration_plot.csv", "model_performance_metrics.csv", "printed_roc_metrics.csv",
         "printed_cumulative_lift.csv", "printed_psi_calculation.csv"]


# ---------------------------------------------------------------- the instrumented real run
def pyrun(vtext: str, ttext: str, fix: bool, no_raise: bool = False) -> dict:
    """Call the real mc.run on a temp directory holding the two CSV texts."""
    rec: dict = {"files": [], "locals": None, "best": {}, "d8": {}, "raised": None}
    o_write, o_best, o_d8 = sc.write_sas_csv, sc.sas_best, sc.sas_d8

    def key(x):
        return None if x is None else cmp.fbits(float(x))

    def w_best(x, w):
        r = o_best(x, w)
        assert w == 8
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

    with tempfile.TemporaryDirectory() as d:
        ind, outd = Path(d) / "in", Path(d) / "out"
        ind.mkdir()
        (ind / "risk_scores_validation.csv").write_text(vtext)
        (ind / "risk_scores_train.csv").write_text(ttext)
        rec["valid"] = sc.proc_import_csv(ind / "risk_scores_validation.csv", guessingrows=20)
        rec["train"] = sc.proc_import_csv(ind / "risk_scores_train.csv", guessingrows=20)
        sc.write_sas_csv, sc.sas_best, sc.sas_d8 = w_write, w_best, w_d8
        if no_raise:
            mc.abs = lambda x: 0.0  # shadows the builtin in `run` only: disables the test of :276
        sys.setprofile(prof)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                mc.run(ind, outd, fix_psi_bins=fix)
        except ValueError as e:
            rec["raised"] = str(e)
        finally:
            sys.setprofile(None)
            sc.write_sas_csv, sc.sas_best, sc.sas_d8 = o_write, o_best, o_d8
            if no_raise:
                del mc.abs
    return rec


# ---------------------------------------------------------------- canonical forms
def canon_frame(df: pl.DataFrame) -> dict:
    cols = []
    for n in df.columns:
        s = df.get_column(n)
        if n in F2I:
            assert s.dtype == pl.Int64, (n, s.dtype)
            s = s.cast(pl.Float64)
        if s.dtype == pl.Date:
            cols.append([n, {"type": "col", "kind": "cell",
                             "values": [["num", None] if v is None else ["str", v.isoformat()] for v in s.to_list()]}])
        else:
            cols.append([n, cmp.canon_series(s)])
    return {"type": "frame", "cols": cols}


def canon_table(df: pl.DataFrame) -> dict:
    df = df.with_columns([pl.col(n).cast(pl.String) for n in df.columns if df.schema[n] == pl.Date])
    return cmp.canon_table(df)


def dgf(df) -> int:
    return cmp.digest(cmp.tokens(canon_frame(df)))


def dgt(name, df) -> int:
    return cmp.digest(cmp.tok_str(name) + cmp.tokens(canon_table(df)))


# ---------------------------------------------------------------- tables as short Lean terms
MK = ("let cell := fun (o : Option Float) => (Tabular.Cell.num o : Tabular.Cell Float); "
      "let mkT := fun (base : Nat) (C : List (Option Nat × Option Nat)) => (((List.range C.length).map (fun (i : Nat) => "
      "let p := C.getD i (none, none); "
      '[("row_id", cell (some (Float.ofNat (base + i)))), ("default_flag", cell (p.1.map Float.ofNat)), '
      '("pd_logistic", cell (p.2.map (fun (k : Nat) => Float.ofScientific k true 3)))])) : Tabular.Table Float); '
      "let mkN := fun (base : Nat) (C : Array Nat) => mkT base (C.toList.map (fun (m : Nat) => (some (m % 2), some (m / 2)))); ")


def codes(df: pl.DataFrame) -> tuple[int, list[tuple]]:
    """(base, [(flag, k)]) with row_id = base + i, default_flag = flag, pd_logistic = float(f'{k}e-3')."""
    assert df.columns == ["row_id", "default_flag", "pd_logistic"] and all(t == pl.Float64 for t in df.dtypes)
    rid = df.get_column("row_id").to_list()
    base = int(rid[0])
    out = []
    for i, (r, f, p) in enumerate(df.iter_rows()):
        assert r == base + i
        assert f is None or f in (0.0, 1.0)
        k = None if p is None else round(p * 1000)
        assert p is None or cmp.fbits(float(f"{k}e-3")) == cmp.fbits(p), p
        out.append((None if f is None else int(f), k))
    return base, out


def lean_tab(df: pl.DataFrame) -> str:
    base, cs = codes(df)
    if all(f is not None and k is not None for f, k in cs):
        return f"(mkN {base} #[" + ", ".join(str(k * 2 + f) for f, k in cs) + "])"
    opt = lambda v: "none" if v is None else f"some {v}"  # noqa: E731
    return f"(mkT {base} [" + ", ".join(f"({opt(f)}, {opt(k)})" for f, k in cs) + "])"


def _key(k) -> str:
    return "none" if k is None else f"some {k}"


def lean_tables(best: dict, d8: dict | None) -> str:
    """The lookup tables SB (sas_best), PF (parse_float) and D8 (sas_d8) as list terms."""
    sb = ", ".join(f"({_key(k)}, {lt.lean_str(v)})" for k, v in best.items())
    pf = ", ".join(f"({lt.lean_str(v)}, {cmp.fbits(float(v))})" for v in sorted({v for v in best.values() if v}))
    out = f"[{sb}] [{pf}]"
    if d8 is not None:
        out += " [" + ", ".join(f"({_key(k)}, {lt.lean_str(v)})" for k, v in d8.items()) + "]"
    return out


# the formatters as lookups in the tables (an argument that Python never passed gives "?" / 5e-324)
SBPF = ('let sb := fun (x : Option Float) (_ : Int) => (match SB.lookup (x.map Float.toBits) with | some s => s | none => "?"); '
        "let pf := fun (s : String) => Float.ofBits ((PF.lookup s).getD 1); ")

# runS V T SB PF D8 : List Int -- the digests of one scenario: 12 that do not depend on
# fix_psi_bins, then 13 for fix_psi_bins = false and 13 for true
RUNS = (
    "let runS := fun (V T : Tabular.Table Float) (SB : List (Option UInt64 × String)) (PF : List (String × UInt64)) "
    "(D8 : List (Option UInt64 × String)) => (" + SBPF +
    'let d8 := fun (x : Option Float) => (match D8.lookup (x.map Float.toBits) with | some s => s | none => "?"); '
    "let v0 := Pl.ofTable V; let t0 := Pl.ofTable T; "
    "let s1 := metrics_run_01_roc_auc v0; "
    "let s2 := metrics_run_02_ks sb pf v0; "
    "let s3 := metrics_run_03_thresholds s2.1; "
    "let s4 := metrics_run_04_deciles s2.1; "
    "let s5 := metrics_run_05_cumulative_lift sb pf s4.1 s4.2; "
    "let s7 := metrics_run_07_calibration s2.1; "
    "let s10 := metrics_run_10_printed_roc d8 s1.1; "
    "let per := fun (fx : Bool) => (let s6 := metrics_run_06_psi t0 s2.1 fx; "
    "let s8 := metrics_run_08_validation_summary s1.2 s2.2 s6.2; "
    "let s9 := metrics_run_09_model_performance today s3 s1.2 s2.2 s6.2; "
    "[dg (tR s6.1), dg (tR s6.2), dg (tR s8), dg (tR s9)] ++ "
    "(run_py sb pf d8 today V T fx).map (fun (p : String × Tabular.Table Float) => dg (tS p.1 ++ tA p.2))); "
    "([dg (tA V), dg (tA T), dg (tR s1.1), dg (tR s1.2), dg (tR s2.1), dg (tR s2.2), dg (tR s3), dg (tR s4.1), "
    "dg (tR s4.2), dg (tR s5), dg (tR s7), dg (tR s10)] ++ per false ++ per true : List Int)); "
)


def scenario(name: str, vtext: str, ttext: str, notes: list, want_valid=None, want_train=None) -> tuple[str, list, str]:
    """-> (the Lean call `runS V T SB PF D8`, the cases in the order of its digests, the run's date)."""
    runs = {}
    raised = {}
    for fix in (False, True):
        r = pyrun(vtext, ttext, fix)
        if r["raised"] is not None:
            raised[fix] = r["raised"]
            r = pyrun(vtext, ttext, fix, no_raise=True)
            assert r["raised"] is None
        runs[fix] = r
    r0 = runs[False]
    if want_valid is not None:  # the hand-made CSV imports as the intended frame
        assert cmp.canon_frame(r0["valid"]) == cmp.canon_frame(want_valid), name
        assert cmp.canon_frame(r0["train"]) == cmp.canon_frame(want_train), name
    best = {**runs[False]["best"], **runs[True]["best"]}
    d8 = {**runs[False]["d8"], **runs[True]["d8"]}
    L0 = r0["locals"]
    today = L0["model_performance_metrics"].get_column("validation_date").to_list()[0].isoformat()
    call = f"runS {lean_tab(r0['valid'])} {lean_tab(r0['train'])} {lean_tables(best, d8)}"
    c = lambda cid, prim, val, **kw: (f"{name}: {cid}", prim, val, kw)  # noqa: E731
    cases = [
        c("input table risk_scores_validation", "run_py", cmp.digest(cmp.tokens(cmp.canon_table(r0["valid"])))),
        c("input table risk_scores_train", "run_py", cmp.digest(cmp.tokens(cmp.canon_table(r0["train"])))),
        c("roc_stats", "metrics_run_01_roc_auc", dgf(L0["roc_stats"])),
        c("auc_summary", "metrics_run_01_roc_auc", dgf(L0["auc_summary"])),
        c("logit_scored_valid sorted", "metrics_run_02_ks", dgf(L0["logit_scored_valid"])),
        c("ks_statistic", "metrics_run_02_ks", dgf(L0["ks_statistic"])),
        c("threshold_analysis", "metrics_run_03_thresholds", dgf(L0["threshold_analysis"])),
        c("decile_data", "metrics_run_04_deciles", dgf(L0["decile_data"])),
        c("decile_analysis", "metrics_run_04_deciles", dgf(L0["decile_analysis"])),
        c("cumulative_lift", "metrics_run_05_cumulative_lift", dgf(L0["cumulative_lift"])),
        c("calibration_plot", "metrics_run_07_calibration", dgf(L0["calibration_plot"])),
        c("printed_roc_metrics", "metrics_run_10_printed_roc", dgf(L0["printed_roc_metrics"])),
    ]
    info = []
    for fix in (False, True):
        r, L = runs[fix], runs[fix]["locals"]
        tag = f"fix_psi_bins={fix}"
        if fix in raised:
            tag += " (Python raises ValueError at :277; expected = continuation with the test of :276 disabled)"
            notes.append(f"{name} fix_psi_bins=True: Python raises ValueError (:277), outside the precondition; expected = the value of the continued code path")
        for k in ("roc_stats", "auc_summary", "logit_scored_valid", "ks_statistic", "threshold_analysis", "decile_data",
                  "decile_analysis", "cumulative_lift", "calibration_plot", "printed_roc_metrics"):
            assert dgf(L[k]) == dgf(L0[k])  # the steps before / beside PSI do not depend on the flag
        cases += [
            c(f"psi_calculation {tag}", "metrics_run_06_psi", dgf(L["psi_calculation"])),
            c(f"psi_summary {tag}", "metrics_run_06_psi", dgf(L["psi_summary"])),
            c(f"validation_summary {tag}", "metrics_run_08_validation_summary", dgf(L["validation_summary"])),
            c(f"model_performance_metrics {tag}", "metrics_run_09_model_performance", dgf(L["model_performance_metrics"])),
        ]
        assert [f for f, _ in r["files"]] == FILES
        cases += [c(f"{f} {tag}", "run_py", dgt(f, df)) for f, df in r["files"]]
        info.append(f"{tag}: ks rows={L['ks_statistic'].height} psi rows={L['psi_calculation'].height} "
                    f"PSI={L['psi_summary'].item(0, 'PSI')} status={L['validation_summary'].get_column('status').to_list()[:2]}")
    print(f"[{name}] valid={r0['valid'].height} train={r0['train'].height} raised={raised}\n   " + "\n   ".join(info))
    return call, cases, today


# ---------------------------------------------------------------- hand-made tables
def frame(base: int, rows: list[tuple]) -> pl.DataFrame:
    return pl.DataFrame({"row_id": [float(base + i) for i in range(len(rows))],
                         "default_flag": [None if f is None else float(f) for f, _ in rows],
                         "pd_logistic": [None if k is None else float(f"{k}e-3") for _, k in rows]},
                        schema={"row_id": pl.Float64, "default_flag": pl.Float64, "pd_logistic": pl.Float64})


def csv_text(df: pl.DataFrame) -> str:
    out = ["row_id,default_flag,pd_logistic"]
    for r, f, p in df.iter_rows():
        out.append(f"{int(r)},{'' if f is None else int(f)},{'' if p is None else repr(p)}")
    return "\n".join(out) + "\n"


T30 = [(i % 2, 100 + 25 * i) for i in range(30)]
T30N = [(f, None if i in (7, 19) else k) for i, (f, k) in enumerate(T30)]
V24 = [(0, 50), (1, 120), (0, 300), (1, 300), (None, 410), (0, 90), (1, None), (0, 640), (1, 555), (0, 20),
       (0, 333), (1, 480), (None, None), (0, 480), (1, 480), (0, 700), (1, 810), (0, None), (0, 150), (1, 150),
       (None, 905), (0, 260), (1, 60), (0, 999)]
HAND = {
    # one class only: total_bad_count = 0 -> every cum_pct_bad null -> every ks_value null -> all rows kept
    "one_class": ([(0, k) for k in (50, 120, 300, 300, 410, 90, 770, 640, 555, 20, 333, 480)], T30),
    # null pd and null default_flag in validation, null pd in training too (the null bins match)
    "nulls_both": (V24, T30N),
    # null pd in validation only: with fix_psi_bins the validation shares do not sum to 1 (raise)
    "nulls_valid_only": (V24, T30),
    # ties: two rows reach the maximum ks_value; tied pd
    "ks_ties": ([(0, 100), (0, 100), (1, 200), (1, 200), (0, 300), (0, 300), (1, 400), (1, 400)], T30),
    # the two rows of the top decile have a null default_flag: defaults / default_rate null in that group
    "null_decile_group": ([(None if i >= 18 else (i * 7) % 3 % 2, 40 + 45 * i) for i in range(20)], T30),
    # 4 validation rows: bins 2, 4, 6, 8 only -> training bins without a validation row
    "empty_train_bins": ([(0, 210), (1, 480), (0, 330), (1, 700)], T30),
    # degenerate sizes
    "two_rows": ([(0, 300), (1, 600)], [(0, 100), (1, 500), (0, 900)]),
    "one_row": ([(1, 500)], [(0, 100), (1, 500), (0, 900)]),
}


def suite_run(names=None) -> Suite:
    s = Suite("b6_run")
    notes: list[str] = []

    def lets(today: str) -> str:
        return MK + f"let today : Tabular.Cell Float := Tabular.Cell.str (some {lt.lean_str(today)}); " + RUNS

    # the three scenario slices: one eval input
    calls, cases, today = [], [], ""
    for sc_ in "abc":
        d = ROOT / "inputs" / "scenarios" / f"edge_metrics_{sc_}"
        vt = "".join((d / "risk_scores_validation.csv").read_text().splitlines(keepends=True)[:NV + 1])
        tt = "".join((d / "risk_scores_train.csv").read_text().splitlines(keepends=True)[:NT + 1])
        if names is None or f"edge_metrics_{sc_}" in names:
            call, cs, today = scenario(f"edge_metrics_{sc_}[{NV}/{NT}]", vt, tt, notes)
            calls.append(call)
            cases += cs
    if calls:
        s.ints(lets(today), " ++ ".join(calls), cases, table=True)
    # the hand-made tables: one eval input for all of them
    calls, cases, today = [], [], ""
    for name, (v, t) in HAND.items():
        if names is None or name in names:
            fv, ft = frame(100001, v), frame(1, t)
            call, cs, today = scenario(name, csv_text(fv), csv_text(ft), notes, fv, ft)
            calls.append(call)
            cases += cs
    if calls:
        s.ints(lets(today), " ++ ".join(calls), cases, table=True)
    f2i = "Int64 columns decile / score_bin / pred_bin compared as Float64 (R-F2I, TODO(port) of the unit)"
    chain = "steps chained inside Lean on the Lean results of the earlier steps, each compared with the locals of the real run"
    s.notes = {
        "metrics_run_04_deciles": f2i + "; " + chain,
        "metrics_run_05_cumulative_lift": f2i + "; " + chain,
        "metrics_run_06_psi": f2i + "; " + chain + ("; " + "; ".join(notes) if notes else ""),
        "metrics_run_07_calibration": f2i + "; " + chain,
        "run_py": "real run on temp CSVs, frames captured at write_sas_csv; sas_best / parse_float / sas_d8 = lookup tables "
                  "of the values that occur, today = the run's date as a String cell; " + f2i
                  + ("; " + "; ".join(notes) if notes else ""),
    }
    for u in ("metrics_run_01_roc_auc", "metrics_run_02_ks", "metrics_run_03_thresholds", "metrics_run_08_validation_summary",
              "metrics_run_09_model_performance", "metrics_run_10_printed_roc"):
        s.notes[u] = chain
    return s


# ---------------------------------------------------------------- _into_float
def _into_lets(best: dict) -> str:
    sb, pf = lean_tables(best, None).split("] [")
    return f"let SB : List (Option UInt64 × String) := {sb}]; let PF : List (String × UInt64) := [{pf}; " + SBPF


def suite_into() -> Suite:
    s = Suite("b6_into")
    X = [None, 0, 2811, 0.066712345678, 123456789, nan, inf, -inf, -0.0, 0.0, 1e-7, 0.5, -2.25, 1 / 3, 99999999.4, 7]
    best = {}
    cases = []
    for x in X:
        k = None if x is None else cmp.fbits(float(x))
        best[k] = sc.sas_best(x, 8)
        r = mc._into_float(x)
        cases.append((f"_into_float({x!r}) -> {r!r} (text {best[k]!r})", "_into_float", -1 if r is None else cmp.fbits(r)))
    lets = _into_lets(best) + "let X : List (Option Float) := [" + ", ".join(
        "none" if x is None else f"some {lt.lean_float(float(x))}" for x in X) + "]; "
    s.ints(lets, "(X.map (fun (x : Option Float) => (match _into_float (α := Float) sb pf x with | none => (-1 : Int) | some q => (q.toBits.toNat : Int))))",
           cases, use_kit=False)
    # the truthiness of the text, with constant formatters: "" -> None, "0" (a non-empty text) -> float("0")
    s.ints("", '[(match _into_float (α := Float) (fun (_ : Option Float) (_ : Int) => "") (fun (_ : String) => 5.0) (some 1.0) with | none => (-1 : Int) | some q => (q.toBits.toNat : Int)), '
               '(match _into_float (α := Float) (fun (_ : Option Float) (w : Int) => toString w) (fun (t : String) => if t == "8" then 3.0 else 4.0) none with | none => (-1 : Int) | some q => (q.toBits.toNat : Int))]',
           [("empty text -> None", "_into_float", -1), ("width 8 is passed; non-empty text -> float(text)", "_into_float", cmp.fbits(3.0))],
           use_kit=False)
    s.notes = {"_into_float": "sas_best / parse_float = lookup tables of the real sas_best(x, 8) and float(text) on the inputs listed"}
    return s


if __name__ == "__main__":
    names = set(sys.argv[1:]) or None
    suite_into().write()
    suite_run(names).write()
