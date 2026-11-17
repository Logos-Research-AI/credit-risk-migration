"""Update 2026-11-17, task T-D (port-translator-5): differential tests of
  def:train_run_13_roc                credit_risk/train.py:702-718
  def:train_run_14_final_and_summary  credit_risk/train.py:725-819
  def:train_run_15_printed_roc        credit_risk/train.py:823-842
on blueprint 5365851c-5549-44b7-9207-4bd4c422031d, carrier def:zz_carrier_t / zz_carrier_t.

  cd migration/port-to-lean
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/td_gen.py   -> diffeval/work/td_steps.*
  (eval_decl every input of work/td_steps.inputs.json; ... python diffeval/fuzz_collect.py 5 td_steps)
  PYTHONPATH=../../port uv run --project ../../port python diffeval/compare.py diffeval/work/td_steps.json diffeval/work/td_steps.out.txt

Each unit is evaluated DIRECTLY on its inputs (the other train steps may be cleared).

Python side: the code of the package only.
  real   the REAL train.run under a line tracer that copies the locals of `run` when it reaches
         the first line of a slice and when it has left its last line, with sas_compat.write_sas_csv
         recording (name, frame) of every export. Runs (feature files of a real feature-engineering
         run on legacy/data, made here if absent):
           full   the two real feature files, whole;
           both   60 training rows (every 1250th) and 25 validation rows, 20 non-defaulters and 5 defaulters;
           one0   the same training rows and 12 validation rows that are all non-defaulters;
           one1   the same training rows and 12 validation rows that are all defaulters.
  slice  the source lines of the slice executed verbatim with the module's globals:
         (1) on the inputs of a real run restricted to what must be typed (step 13: the columns
         default_flag and pd_logistic; step 14: one row of the two scored sets, with six of their
         columns except the training set of the run `full`, which keeps every column; interest_rate
         is among the six because the export names it in `formats`); what the slice gives on them is asserted equal to the
         real run (step 13 and step 15: everything; step 14: model_summary.csv and
         model_coefficients.csv; the three scored exports are pass-through of the restricted rows);
         (2) on hand-made validation sets (step 13), and steps 14 / 15 on what step 13 gave there.
  NOT evaluated in Lean: step 13 on the run `full` (105,000 and 45,000 rows cannot be typed).

Lean side: frames from short codes (FZ, FB, IZ, text literals); the digest of the inputs of every
call is compared first. Explicit parameters: `fsum` is a table of what math.fsum returned in the
slice, keyed by the digest of the list it received (a list not in the table gives -7.25);
`sas_d8` a table of the real sas_compat.sas_d8 over the values of the ROC frames; `today` the text
cell "TODAY" (the Python date column is replaced by that text before the comparison).
An exported file is compared as (name, table); a frame with no row is the empty table (D2).
"""
from __future__ import annotations

import contextlib
import io
import math
import sys
import tempfile
import textwrap
import types
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
KIT_DIR = HERE.parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE.parent))

import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_t", "zz_carrier_t")

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

nan, inf = float("nan"), float("inf")
WORK = suite_mod.WORK
FE_OUT = WORK / "td_data" / "fe"
SLICES = {"s13": (702, 718, "roc_valid_created = bool((roc_valid_used == 1).any())"),
          "s14": (725, 819, "model_summary = model_summary.clear().select("),
          "s15": (823, 842, "if roc_valid_created:  # the judge's export")}
U13, U14, U15 = "train_run_13_roc", "train_run_14_final_and_summary", "train_run_15_printed_roc"
SENT = -7.25


# ---------------------------------------------------------------- running the code of the package
def slice_code(key: str):
    a, b, must = SLICES[key]
    src = "".join(Path(train.__file__).read_text().splitlines(keepends=True)[a - 1:b])
    assert must in src, (key, "the slice does not hold the expected line: line numbers moved?")
    return compile(textwrap.dedent(src), f"{train.__file__}:{a}-{b}", "exec")


CODE = {k: slice_code(k) for k in SLICES}


@contextlib.contextmanager
def recording():
    """sas_compat.write_sas_csv records (file name, frame) and still writes; math.fsum (as
    sas_compat sees it) records (list, result)."""
    writes, fsums = [], []
    o_write, o_math = sc.write_sas_csv, sc.math

    def w_write(df, path, formats=None):
        writes.append((Path(path).name, df))
        return o_write(df, path, formats=formats)

    def w_fsum(xs):
        xs = [float(x) for x in xs]
        r = math.fsum(xs)
        fsums.append((xs, r))
        return r

    proxy = types.SimpleNamespace(**{k: getattr(math, k) for k in dir(math) if not k.startswith("__")})
    proxy.fsum = w_fsum
    sc.write_sas_csv, sc.math = w_write, proxy
    try:
        yield writes, fsums
    finally:
        sc.write_sas_csv, sc.math = o_write, o_math


def run_slice(key: str, env: dict):
    ns = dict(vars(train))
    ns.update(env)
    with tempfile.TemporaryDirectory() as d, recording() as (writes, fsums), contextlib.redirect_stdout(io.StringIO()):
        ns["output_dir"] = Path(d)
        exec(CODE[key], ns)  # noqa: S102
    return ns, writes, fsums


def traced(ind: Path):
    snap: dict = {}

    def local(frame, event, arg):
        if event in ("line", "return"):
            for k, (a, b, _) in SLICES.items():
                if (k, "in") not in snap and event == "line" and frame.f_lineno >= a:
                    snap[k, "in"] = dict(frame.f_locals)
                if (k, "in") in snap and (k, "out") not in snap and (event == "return" or frame.f_lineno > b):
                    snap[k, "out"] = dict(frame.f_locals)
        return local

    def glob(frame, event, arg):
        return local if frame.f_code is train.run.__code__ else None

    end = "completed"
    with tempfile.TemporaryDirectory() as out, recording() as (writes, _), contextlib.redirect_stdout(io.StringIO()):
        sys.settrace(glob)
        try:
            train.run(ind, Path(out))
        except Exception as ex:  # noqa: BLE001
            end = f"{type(ex).__name__}: {str(ex)[:80]}"
        finally:
            sys.settrace(None)
    return snap, dict(writes), end, [n for n, _ in writes]


def same(a: pl.DataFrame, b: pl.DataFrame) -> bool:
    return cmp.canon_frame(a) == cmp.canon_frame(b)


# ---------------------------------------------------------------- canonical values, digests
def ftoks(df: pl.DataFrame) -> list[int]:
    return cmp.tokens(cmp.canon_frame(df))


def file_digest(name: str, df: pl.DataFrame) -> int:
    """digest of (name, table): mirrors dg (tS p.1 ++ tA p.2); the Date column becomes the text TODAY"""
    if "training_date" in df.columns:
        df = df.with_columns(training_date=pl.lit("TODAY", dtype=pl.String))
    return cmp.digest(cmp.tok_str(name) + cmp.tokens(cmp.canon_table(df)))


# ---------------------------------------------------------------- frames as short Lean terms
ENC = (
    "let FZ := fun (v : List Int) => (Pl.Col.f64 (v.map (fun (k : Int) => if k < 0 then none else some (Float.ofNat k.toNat))) : Pl.Col Float); "
    "let FB := fun (v : List Nat) => (Pl.Col.f64 (v.map (fun (b : Nat) => if b == 1 then none else some (Float.ofBits b.toUInt64))) : Pl.Col Float); "
    "let IZ := fun (v : List Int) => (Pl.Col.int (v.map (fun (k : Int) => if k == -9 then none else some k)) : Pl.Col Float); "
)


def _ints(vals) -> str:
    return "[" + ", ".join(str(v) if v >= 0 else f"({v})" for v in vals) + "]"


def enc_col(s: pl.Series) -> str:
    v = s.to_list()
    if s.dtype == pl.Float64:
        if all(x is None or (x == x and abs(x) != inf and x == int(x) and 0 <= x < 2**53 and math.copysign(1, x) > 0) for x in v):
            return "(FZ " + _ints([-1 if x is None else int(x) for x in v]) + ")"
        assert all(x is None or cmp.fbits(x) != 1 for x in v)
        return "(FB " + _ints([1 if x is None else cmp.fbits(x) for x in v]) + ")"
    if s.dtype.is_integer():
        assert all(x != -9 for x in v if x is not None)
        return "(IZ " + _ints([-9 if x is None else x for x in v]) + ")"
    return lt.lean_col(s)


def enc_frame(df: pl.DataFrame) -> str:
    return "[" + ", ".join(f"({lt.lean_str(n)}, {enc_col(df[n])})" for n in df.columns) + "]"


def let_frame(name: str, df: pl.DataFrame) -> str:
    return f"let {name} : Pl.Frame Float := {enc_frame(df)}; "


# ---------------------------------------------------------------- data
def feature_files() -> Path:
    if not (FE_OUT / "model_features_train.csv").exists():
        FE_OUT.mkdir(parents=True, exist_ok=True)
        with contextlib.redirect_stdout(io.StringIO()):
            fe.run(REPO / "legacy" / "data", FE_OUT, split_ids=KIT_DIR / "inputs" / "split_ids.csv")
    return FE_OUT


def sample_dirs() -> dict:
    full = feature_files()
    tr = sc.proc_import_csv(full / "model_features_train.csv", guessingrows=None)[2::1250].head(60)
    va = sc.proc_import_csv(full / "model_features_validation.csv", guessingrows=None)
    sub = va[1::97]
    both = pl.concat([sub.filter(pl.col("default_flag") == 0).head(20), sub.filter(pl.col("default_flag") == 1).head(5)]).sort("row_id")
    assert set(both["default_flag"].to_list()) == {0.0, 1.0} and both.height == 25
    dirs = {"full": full}
    for name, v in (("both", both), ("one0", sub.filter(pl.col("default_flag") == 0).head(12)),
                    ("one1", sub.filter(pl.col("default_flag") == 1).head(12))):
        d = WORK / "td_data" / name
        d.mkdir(parents=True, exist_ok=True)
        tr.write_csv(d / "model_features_train.csv")
        v.write_csv(d / "model_features_validation.csv")
        dirs[name] = d
    return dirs


# interest_rate must stay: write_sas_csv raises ValueError on a `formats` key that names no column
RISK_COLS = ["row_id", "default_flag", "pd_logistic", "risk_grade", "interest_rate"]


def build() -> Suite:
    s = Suite("td_steps")
    report = []
    d8_none = sc.sas_d8(None)
    runs = {}
    for name, d in sample_dirs().items():
        snap, writes, end, order = traced(d)
        runs[name] = (snap, writes)
        o13 = snap["s13", "out"]
        report.append(f"{name}: run {end}; validation rows {snap['s13', 'in']['risk_scores_validation'].height}; "
                      f"roc_valid_created={o13['roc_valid_created']}; roc_valid Area={o13['roc_valid']['Area'].to_list()}; "
                      f"model_summary rows={writes['model_summary.csv'].height} columns={writes['model_summary.csv'].columns}; "
                      f"files written: {order}")

    # ================================================================ step 13
    lets13, calls13, cases13, fs_tab = "", [], [], {}

    def add13(cid: str, rst_name: str, rst: pl.DataFrame, rsv: pl.DataFrame, real: dict | None, fz: str = "kept"):
        nonlocal lets13
        ns, _, fsums = run_slice("s13", {"risk_scores_train": rst, "risk_scores_validation": rsv})
        if real is not None:
            assert same(ns["roc_train"], real["roc_train"]) and same(ns["roc_valid"], real["roc_valid"]), cid
            assert ns["roc_valid_created"] == real["roc_valid_created"], cid
        for xs, r in fsums:
            fs_tab[cmp.digest([cmp.fbits(x) for x in xs])] = r
        k = len(calls13)
        lets13 += let_frame(f"v{k}", rsv)
        calls13.append(f"c13 {rst_name} v{k}")
        note = {"note": "outside the precondition (Python returns)"} if fz != "kept" else {}
        cases13.extend([(f"{cid} / inputs", U13 + " (input)", cmp.digest(ftoks(rst) + ftoks(rsv)), note),
                        (f"{cid} / roc_train", U13, cmp.digest(ftoks(ns["roc_train"])), note),
                        (f"{cid} / roc_valid", U13, cmp.digest(ftoks(ns["roc_valid"])), note),
                        (f"{cid} / roc_valid_created = {ns['roc_valid_created']}", U13, int(ns["roc_valid_created"]), note)])
        return ns

    two = ["default_flag", "pd_logistic"]
    rst_s = runs["both"][0]["s13", "in"]["risk_scores_train"].select(two)
    for name in ("both", "one0", "one1"):
        i13, o13 = runs[name][0]["s13", "in"], runs[name][0]["s13", "out"]
        assert same(i13["risk_scores_train"].select(two), rst_s)
        add13(f"real run {name} ({i13['risk_scores_validation'].height} validation rows, columns default_flag, pd_logistic)",
              "RT", rst_s, i13["risk_scores_validation"].select(two), o13)
    rt_small = rst_s.head(6)
    f64 = lambda v: pl.Series(v, dtype=pl.Float64, nan_to_null=False)  # noqa: E731
    hand = [
        ("a NaN outcome is not 1: [1, NaN, 1]", pl.DataFrame({"default_flag": f64([1.0, nan, 1.0]), "pd_logistic": f64([0.2, 0.5, 0.7])}), "kept"),
        ("events only once the null outcome is left out: [1, 1, null]", pl.DataFrame({"default_flag": f64([1.0, 1.0, None]), "pd_logistic": f64([0.3, 0.6, 0.1])}), "kept"),
        ("both classes, the only non-event has no probability", pl.DataFrame({"default_flag": f64([1.0, 0.0, 1.0]), "pd_logistic": f64([0.3, None, 0.9])}), "kept"),
        ("Int64 outcome [0, 1, 1]", pl.DataFrame({"default_flag": pl.Series([0, 1, 1], dtype=pl.Int64), "pd_logistic": f64([0.3, 0.2, 0.9])}), "kept"),
        ("non-events only [0, 0, 0]", pl.DataFrame({"default_flag": f64([0.0, 0.0, 0.0]), "pd_logistic": f64([0.3, 0.2, 0.9])}), "kept"),
        ("1 + one ulp is not 1: [1.0000000000000002, 1]", pl.DataFrame({"default_flag": f64([1.0000000000000002, 1.0]), "pd_logistic": f64([0.3, 0.2])}), "kept"),
        ("validation set with no row", pl.DataFrame({"default_flag": f64([]), "pd_logistic": f64([])}), "kept"),
        ("every outcome null", pl.DataFrame({"default_flag": f64([None, None]), "pd_logistic": f64([0.1, 0.2])}), "kept"),
        ("a NaN probability is not null: [1, 0] with [NaN, 0.4]", pl.DataFrame({"default_flag": f64([1.0, 0.0]), "pd_logistic": f64([nan, 0.4])}), "kept"),
    ]
    hand_out = {}
    for cid, rsv, fz in hand:
        ns = add13("hand: " + cid, "RS", rt_small, rsv, None, fz)
        hand_out[cid] = ns
        report.append(f"   13 hand [{cid}] -> created={ns['roc_valid_created']} roc_valid Area={ns['roc_valid']['Area'].to_list()}")
    tab = "[" + ", ".join(f"({k}, {lt.lean_float(v)})" for k, v in fs_tab.items()) + "]"
    pre13 = (ENC + f"let T : List (Int × Float) := {tab}; "
             f"let fs := fun (xs : List Float) => (match T.lookup (dg (xs.map Float.toBits)) with | some r => r | none => {SENT}); "
             + let_frame("RT", rst_s) + let_frame("RS", rt_small) + lets13 +
             "let c13 := fun (t v : Pl.Frame Float) => (let r := train_run_13_roc fs t v; "
             "[dg (tR t ++ tR v), dg (tR r.1), dg (tR r.2.1), if r.2.2 then 1 else 0]); ")
    s.ints(pre13, " ++ ".join(calls13), cases13, table=True)

    # ================================================================ steps 14 and 15
    class Group:
        """One eval input for a step: the frames are let-bound once each (equal frames share a name)."""

        def __init__(self, unit: str):
            self.unit, self.names, self.lets, self.calls, self.cases, self.d8 = unit, {}, "", [], [], {}

        def fr(self, df: pl.DataFrame) -> str:
            t = enc_frame(df)
            if t not in self.names:
                self.names[t] = f"f{len(self.names)}"
                self.lets += f"let {self.names[t]} : Pl.Frame Float := {t}; "
            return self.names[t]

    g14, g15 = Group(U14), Group(U15)

    def case14(cid: str, env: dict, created: bool, real_writes: dict | None):
        e = dict(env)
        e["roc_valid_created"] = created
        _, writes, _ = run_slice("s14", e)
        if real_writes is not None:
            assert same(dict(writes)["model_summary.csv"], real_writes["model_summary.csv"]), cid
            mc = dict(writes)["model_coefficients.csv"]   # pass-through of the (first rows of the) input
            assert same(mc, real_writes["model_coefficients.csv"].head(mc.height)), cid
        names = ["model_coefficients", "training_metrics", "validation_metrics", "risk_scores_train", "risk_scores_validation",
                 "roc_train", "roc_valid"]
        intoks = []
        for n in names:
            intoks += ftoks(e[n])
        g14.calls.append("c14 " + " ".join(g14.fr(e[n]) for n in names) + f" {str(created).lower()}")
        g14.cases += [(f"{cid} / inputs", U14 + " (input)", cmp.digest(intoks)), (f"{cid} / number of files", U14, len(writes))]
        g14.cases += [(f"{cid} / {n} ({df.height} rows)", U14, file_digest(n, df)) for n, df in writes]
        return writes

    def case15(cid: str, env: dict, created: bool, real_writes: dict | None):
        e = dict(env)
        e["roc_valid_created"] = created
        _, writes, _ = run_slice("s15", e)
        if real_writes is not None:
            for n, df in writes:
                assert same(df, real_writes[n]), (cid, n)
            assert ("printed_roc_validation.csv" in real_writes) == created
        names = ["confusion_matrix_train", "confusion_matrix", "roc_train", "roc_valid"]
        intoks = []
        for n in names:
            intoks += ftoks(e[n])
        for fr in (e["roc_train"], e["roc_valid"]):
            for c in ["Area", "StdErr", "LowerArea", "UpperArea", "SomersD", "Gamma", "TauA"]:
                for v in fr[c].to_list():
                    if v is not None:
                        g15.d8[cmp.fbits(v)] = sc.sas_d8(v)
        g15.calls.append("c15 " + " ".join(g15.fr(e[n]) for n in names) + f" {str(created).lower()}")
        g15.cases += [(f"{cid} / inputs", U15 + " (input)", cmp.digest(intoks)), (f"{cid} / number of files", U15, len(writes))]
        g15.cases += [(f"{cid} / {n} ({df.height} rows)", U15, file_digest(n, df)) for n, df in writes]
        return writes

    def restrict(e14: dict, all_train_columns: bool) -> dict:
        e14 = dict(e14)
        extra = [c for c in e14["risk_scores_train"].columns if c not in RISK_COLS][:1]
        if not all_train_columns:
            e14["risk_scores_train"] = e14["risk_scores_train"].head(1).select(RISK_COLS + extra)
        else:
            e14["risk_scores_train"] = e14["risk_scores_train"].head(1)
            e14["model_coefficients"] = e14["model_coefficients"].head(3)   # 16 rows of text, pass-through
        e14["risk_scores_validation"] = e14["risk_scores_validation"].head(1).select(RISK_COLS + extra)
        return e14

    for name in ("full", "both", "one0"):
        snap, writes = runs[name]
        e14, e15 = restrict(snap["s14", "in"], name == "full"), dict(snap["s15", "in"])
        created = e14["roc_valid_created"]
        w = case14(f"real run {name} (roc_valid_created={created}; one row of the scored sets, "
                   + ("every column of the training one" if name == "full" else "six columns") + ")", e14, created, writes)
        report.append(f"   14 {name}: files {[(n, df.height) for n, df in w]}")
        w = case15(f"real run {name} (roc_valid_created={created})", e15, created, writes)
        report.append(f"   15 {name}: files {[(n, df.height) for n, df in w]}")
    # steps 14 / 15 on what step 13 gave on a hand-made validation set: roc_valid_created true with
    # no Area (other inputs: run `both`)
    snap, _ = runs["both"]
    for cid in ("a NaN outcome is not 1: [1, NaN, 1]",):
        ns = hand_out[cid]
        e14, e15 = restrict(snap["s14", "in"], False), dict(snap["s15", "in"])
        for e in (e14, e15):
            e["roc_valid"] = ns["roc_valid"]
        w = case14(f"hand: step 13 on [{cid}] (roc_valid_created={ns['roc_valid_created']}, Area {ns['roc_valid']['Area'].to_list()})",
                   e14, ns["roc_valid_created"], None)
        report.append(f"   14 hand [{cid}]: files {[(n, df.height) for n, df in w]}")
        w = case15(f"hand: step 13 on [{cid}] (roc_valid_created={ns['roc_valid_created']})", e15, ns["roc_valid_created"], None)
        report.append(f"   15 hand [{cid}]: files {[(n, df.height) for n, df in w]}")
    FILES = "o.map (fun (p : String × Tabular.Table Float) => dg (tS p.1 ++ tA p.2))"
    s.ints(ENC + g14.lets +
           "let c14 := fun (a0 a1 a2 a3 a4 a5 a6 : Pl.Frame Float) (cr : Bool) => (let o := train_run_14_final_and_summary "
           "(Tabular.Cell.str (some \"TODAY\")) a0 a1 a2 a3 a4 a5 a6 cr; "
           f"[dg (tR a0 ++ tR a1 ++ tR a2 ++ tR a3 ++ tR a4 ++ tR a5 ++ tR a6), (o.length : Int)] ++ {FILES}); ",
           " ++ ".join(g14.calls), g14.cases, table=True)
    tabd = "[" + ", ".join(f"({k}, {lt.lean_str(t)})" for k, t in g15.d8.items()) + "]"
    s.ints(ENC + g15.lets + f"let D : List (UInt64 × String) := {tabd}; "
           f"let d8 := fun (o : Option Float) => (match o with | none => {lt.lean_str(d8_none)} | some x => (D.lookup x.toBits).getD \"?MISSING\"); "
           "let c15 := fun (a0 a1 a2 a3 : Pl.Frame Float) (cr : Bool) => (let o := train_run_15_printed_roc d8 a0 a1 a2 a3 cr; "
           f"[dg (tR a0 ++ tR a1 ++ tR a2 ++ tR a3), (o.length : Int)] ++ {FILES}); ",
           " ++ ".join(g15.calls), g15.cases, table=True)

    s.notes = {
        U13: "evaluated directly; real = locals of the real train.run at the slice boundaries (sample runs with both classes, "
             "non-defaulters only, defaulters only in the validation set), columns default_flag and pd_logistic; hand = the slice's "
             "lines on hand-made validation sets; fsum = table of what math.fsum returned; the run on the whole real files is not "
             "evaluated in Lean (too long to type)",
        U14: "evaluated directly on the inputs of the real train.run (whole real files and the sample runs `both` and `one0`) with one row of "
             "the scored sets; model_summary.csv and model_coefficients.csv asserted equal to the real exports",
        U15: "evaluated directly on the inputs of the real train.run (whole real files and the sample runs `both` and `one0`); every export "
             "asserted equal to the real one; sas_d8 = table of the real function",
    }
    s.write()
    (WORK / "td_steps.report.txt").write_text("\n".join(report) + "\n")
    print("\n".join(report))
    print("input chars:", [len(i["text"]) for i in s.inputs])
    return s


if __name__ == "__main__":
    build()
