"""Re-translation after commit 7927af7: differential tests of the four changed step items
  def:train_run_09_confusion_train   credit_risk/train.py:424-483
  def:train_run_11_confusion_valid   credit_risk/train.py:509-559
  def:metrics_run_05_cumulative_lift credit_risk/metrics_calculation.py:216-240
  def:metrics_run_06_psi             credit_risk/metrics_calculation.py:244-303

  uv run python migration/diffeval/units/r3_gen.py            -> work/r3_conf, r3_lift, r3_psi, r3_psibig
  (eval_decl each work/r3_*.inputs.json on def:zz_carrier_t / zz_carrier_t, save work/r3_*.out.txt)
  uv run python migration/diffeval/compare.py migration/diffeval/work/r3_<suite>.json migration/diffeval/work/r3_<suite>.out.txt

Each step item is evaluated DIRECTLY on its inputs (no chaining: other step items may be cleared).

Python side. Two ways, both run the code of the package, never a re-implementation:
  real   the REAL train.run / metrics_calculation.run (through b9_gen.real_run / b6_gen.pyrun) under
         a line tracer (sys.settrace) that copies the locals of `run` when it reaches the first
         line of the slice and when it leaves its last line: the inputs and the results of the
         slice in the real run;
  slice  the source lines of the slice, read from the file at run time (verbatim, dedented) and
         executed with the module's own globals on a given input (`run_slice`). It is used (1) on
         the inputs captured from the real run restricted to the columns the slice reads (the
         Lean input must be typed into an eval_decl call, so it has to be short); the results are
         asserted equal to the real run's results on the full frames, column for column; (2) on
         hand-made frames that the upstream code of `run` cannot produce (a null pred_logistic, a
         null `defaults` in a chosen decile, frames with 0 / 1 / 2 / 5000 / 5001 rows).
  Where the slice raises ValueError (:277, fix_psi_bins) the expected value is the continuation
  with the builtin `abs` shadowed in the slice's globals (as b6_gen does); the case carries a note.

Lean side: frames are built from short integer codes (FZ: non-negative integers as Float64, FB:
float bits, FK: thousandths through Float.ofScientific, FS: the same from a 3-digit string, IZ:
Int64); the digest of every input frame is compared with the digest of the Python frame first, so
the inputs are the same bit for bit. Int64 columns that the Lean keeps as Float64 under R-F2I
(decile, score_bin) are cast to Float64 on the Python side (inputs and results).
"""
from __future__ import annotations

# RETIRED 2026-11-16: this script is a record of the port before the update of 2026-11-16 and no longer
# runs as a script (its helper functions are still imported by later generators): it calls fix_psi_bins in the slice of step 06; see t14_gen.py, t15_gen.py.
# Its recorded outputs describe the port as it was then.
import sys as _sys

if __name__ == "__main__":  # retired as a script; its helpers may still be imported
    _sys.exit("RETIRED 2026-11-16: " + __file__ + " calls keywords the port no longer has; see the note at its top")


import math
import sys
import textwrap
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(ROOT))

import suite as suite_mod  # noqa: E402

suite_mod.CARRIERS["identity"] = ("def:zz_carrier_t", "zz_carrier_t")  # the carrier of this round

import b6_gen as b6  # noqa: E402
import b9_gen as b9  # noqa: E402
import b9_r2_gen as b9r2  # noqa: E402
import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import metrics_calculation as mc  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

nan = float("nan")
SCRATCH = Path("/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration-formal-python/"
               "aa9ba63a-dfbb-4dbd-bc0a-805359ea00aa/scratchpad/r3")
SLICES = {"s09": (train, 424, 483, ".filter(pl.all_horizontal("), "s11": (train, 509, 559, ".filter(pl.all_horizontal("),
          "s05": (mc, 216, 240, ".cum_sum().forward_fill()"), "s06": (mc, 244, 303, "max(train_bins.height, 1)")}
U09, U11, U05, U06 = ("train_run_09_confusion_train", "train_run_11_confusion_valid",
                      "metrics_run_05_cumulative_lift", "metrics_run_06_psi")


# ---------------------------------------------------------------- running the code of the package
def slice_source(key: str) -> str:
    mod, a, b, must = SLICES[key]
    src = "".join(Path(mod.__file__).read_text().splitlines(keepends=True)[a - 1:b])
    assert must in src, (key, "the slice does not hold the changed line: line numbers moved?")
    return textwrap.dedent(src)


def run_slice(key: str, env: dict, shadow: dict | None = None) -> dict:
    """Execute the source lines of the slice (verbatim) with the module's globals plus `env`."""
    mod, a, b, _ = SLICES[key]
    ns = dict(vars(mod))
    ns.update(shadow or {})
    ns.update(env)
    exec(compile(slice_source(key), f"{mod.__file__}:{a}-{b}", "exec"), ns)  # noqa: S102
    return ns


def traced(code, keys: list[str], call):
    """Run `call()`; copy the locals of the frame of `code` at the entry and at the exit of each slice."""
    snap: dict = {}

    def local(frame, event, arg):
        if event in ("line", "return"):
            for k in keys:
                _, a, b, _ = SLICES[k]
                if (k, "in") not in snap and event == "line" and frame.f_lineno >= a:
                    snap[k, "in"] = dict(frame.f_locals)
                if (k, "in") in snap and (k, "out") not in snap and (event == "return" or frame.f_lineno > b):
                    snap[k, "out"] = dict(frame.f_locals)
        return local

    def glob(frame, event, arg):
        return local if frame.f_code is code else None

    sys.settrace(glob)
    try:
        r = call()
    finally:
        sys.settrace(None)
    return r, snap


def same(a: pl.DataFrame, b: pl.DataFrame) -> bool:
    return cmp.canon_frame(a) == cmp.canon_frame(b)


def dgf(df: pl.DataFrame) -> int:
    return b6.dgf(df)  # digest of the frame; decile / score_bin Int64 -> Float64 (R-F2I)


# ---------------------------------------------------------------- frames as short Lean terms
ENC_PARTS = [
    "let FZ := fun (v : List Int) => (Pl.Col.f64 (v.map (fun (k : Int) => if k < 0 then none else some (Float.ofNat k.toNat))) : Pl.Col Float); ",
    "let FB := fun (v : List Nat) => (Pl.Col.f64 (v.map (fun (b : Nat) => if b == 1 then none else some (Float.ofBits b.toUInt64))) : Pl.Col Float); ",
    "let FK := fun (v : List Int) => (Pl.Col.f64 (v.map (fun (k : Int) => if k < 0 then none else if k == 9999 then some (0.0 / 0.0) "
    "else some (Float.ofScientific k.toNat true 3))) : Pl.Col Float); ",
    "let FS := fun (s : String) => (let a := s.toList.toArray; let d := fun (i : Nat) => (a[i]!).toNat - 48; "
    "Pl.Col.f64 ((List.range (a.size / 3)).map (fun (i : Nat) => if a[3 * i]! == 'n' then none else "
    "some (Float.ofScientific (d (3 * i) * 100 + d (3 * i + 1) * 10 + d (3 * i + 2)) true 3))) : Pl.Col Float); ",
    "let IZ := fun (v : List Int) => (Pl.Col.int (v.map (fun (k : Int) => if k == -9 then none else some k)) : Pl.Col Float); ",
]
ENC = "".join(ENC_PARTS)
PSI1 = ("let psi1 := fun (t v : Pl.Frame Float) (fx : Bool) => (let r := metrics_run_06_psi t v fx; "
        "[dg (tR t), dg (tR v), dg (tR r.1), dg (tR r.2)]); ")


def _ints(vals) -> str:
    return "[" + ", ".join(str(v) if v >= 0 else f"({v})" for v in vals) + "]"


def enc_fz(s: pl.Series) -> str:
    v = s.to_list()
    assert s.dtype == pl.Float64 and all(x is None or (x == int(x) and 0 <= x < 2**53 and math.copysign(1, x) > 0) for x in v), s
    return "(FZ " + _ints([-1 if x is None else int(x) for x in v]) + ")"


def enc_fb(s: pl.Series) -> str:
    v = s.to_list()
    assert s.dtype == pl.Float64 and all(x is None or cmp.fbits(x) != 1 for x in v)
    return "(FB " + _ints([1 if x is None else cmp.fbits(x) for x in v]) + ")"


def k3(x) -> int:
    if x is None:
        return -1
    if x != x:
        return 9999
    k = round(x * 1000)
    assert 0 <= k < 9999 and cmp.fbits(float(f"{k}e-3")) == cmp.fbits(x), x
    return k


def enc_fk(s: pl.Series) -> str:
    assert s.dtype == pl.Float64
    return "(FK " + _ints([k3(x) for x in s.to_list()]) + ")"


def enc_fs(s: pl.Series) -> str:
    ks = [k3(x) for x in s.to_list()]
    assert s.dtype == pl.Float64 and all(k < 1000 for k in ks)
    return '(FS "' + "".join("nnn" if k < 0 else f"{k:03d}" for k in ks) + '")'


def enc_iz(s: pl.Series) -> str:
    v = s.to_list()
    assert s.dtype == pl.Int64 and all(x != -9 for x in v if x is not None)
    return "(IZ " + _ints([-9 if x is None else x for x in v]) + ")"


def frame_term(cols: list[tuple[str, str]]) -> str:
    return "[" + ", ".join(f"({lt.lean_str(n)}, {t})" for n, t in cols) + "]"


def f64(vals) -> pl.Series:
    return pl.Series("x", [None if v is None else float(v) for v in vals], dtype=pl.Float64)


def i64(vals) -> pl.Series:
    return pl.Series("x", vals, dtype=pl.Int64)


class Group:
    """One eval input: a list of calls, each returning a list of digests (List Int)."""

    def __init__(self, lets: str):
        self.lets, self.calls, self.cases = lets, [], []

    def add(self, call: str, cases: list[tuple]):
        self.calls.append(call)
        self.cases += cases

    def flush(self, s: Suite):
        if self.calls:
            body = " ++ ".join(self.calls)
            # only the encoders the calls use (the input is typed into the eval_decl call by hand)
            lets = self.lets
            for text in ENC_PARTS + [PSI1]:
                name = text.split(" ")[1]
                if f"{name} " not in body:
                    lets = lets.replace(text, "")
            s.ints(lets, body, self.cases, table=False)
        self.calls, self.cases = [], []


# ---------------------------------------------------------------- confusion matrices (steps 09, 11)
CONF = (ENC +
        "let c9 := fun (fr : Pl.Frame Float) => (let r := train_run_09_confusion_train fr; "
        "[dg (tR fr), dg (tR r.1), dg (tR r.2.1), dg (tR r.2.2)]); "
        "let c11 := fun (fr : Pl.Frame Float) => (let r := train_run_11_confusion_valid fr; "
        "[dg (tR fr), dg (tR r.1), dg (tR r.2)]); ")


def conf9(g: Group, name: str, df: pl.DataFrame, term: str, **kw):
    ns = run_slice("s09", {"logit_scored_train": df})
    g.add(f"c9 {term}", [
        (f"{name}: input logit_scored_train", U09, dgf(df), kw),
        (f"{name}: logit_scored_train + pred_logistic", U09, dgf(ns["logit_scored_train"]), kw),
        (f"{name}: confusion_matrix_train", U09, dgf(ns["confusion_matrix_train"]), kw),
        (f"{name}: training_metrics", U09, dgf(ns["training_metrics"]), kw)])
    return ns


def conf11(g: Group, name: str, df: pl.DataFrame, term: str, **kw):
    ns = run_slice("s11", {"logit_scored_valid": df})
    g.add(f"c11 {term}", [
        (f"{name}: input logit_scored_valid", U11, dgf(df), kw),
        (f"{name}: confusion_matrix", U11, dgf(ns["confusion_matrix"]), kw),
        (f"{name}: validation_metrics", U11, dgf(ns["validation_metrics"]), kw)])
    return ns


def real_train_samples():
    """(name, input directory) of the real train.run samples: the B9 sample and reviewer-2 samples a, c."""
    yield "b9 sample", b9.sample_inputs()
    b9r2.FE_DIR = b9.DATA / "fe_out"
    for smp in ("a", "c"):
        cfg = b9r2.SAMPLES[smp]
        ind = SCRATCH / "b9r2" / smp
        if not (ind / "model_features_validation.csv").exists():
            b9r2.write_sample(cfg, cfg["seed"], ind)
        yield f"b9r2 sample {smp}", ind


# hand-made inputs of step 09: (name, default_flag values, dtype of default_flag, pd_logistic in thousandths)
H09 = [
    ("null default_flag levels, null and NaN pd", [0, 1, None, 0, 1, None, 1, 0, None], "f", [200, 700, 600, 500, 100, 300, None, 9999, 600]),
    ("every default_flag null (N over nothing)", [None, None, None, None], "f", [100, 900, 500, 499]),
    ("single level", [0, 0, 0], "f", [100, 200, 300]),
    ("single level, missing", [None, None], "f", [100, 200]),
    ("one row", [1], "f", [750]),
    ("one row, missing", [None], "f", [750]),
    ("Int64 default_flag with nulls", [0, 1, None, 1, 1, 0, None], "i", [510, 490, 700, 800, 100, 100, 100]),
    ("default_flag levels 2 and NaN", [2, 9999, 1, 0, 2, 9999, None], "k", [100, 600, 700, 200, 800, 300, 900]),
    ("thirds", [0, 0, 1, 1, 1, 0, 1], "f", [100, 600, 700, 200, 800, 300, 900]),
]
# hand-made inputs of step 11: (name, default_flag, dtype, pred_logistic Int64)
H11 = [
    ("null pred_logistic levels", [0, 1, 0, 1, 1, 0], "f", [0, None, 1, 1, None, 0]),
    ("null default_flag levels", [None, 1, 0, None, 1, 0], "f", [0, 1, 1, 1, 0, 0]),
    ("both null, each null, none null", [None, None, 0, 1, None, 0, 1, 1], "f", [None, 0, None, 1, None, 0, 1, 0]),
    ("every row has a missing key (N over nothing)", [None, 0, None, 1], "f", [1, None, None, None]),
    ("every key null", [None, None], "f", [None, None]),
    ("single level", [1, 1, 1], "f", [1, 1, 1]),
    ("single level, missing pred", [1, 1], "f", [None, None]),
    ("one row", [0], "f", [1]),
    ("pred_logistic levels 2 and -1", [0, 1, 0, 1, None, 0, 1], "f", [2, -1, 0, 1, 2, 2, None]),
    ("Int64 default_flag with nulls", [0, 1, None, 1, 1, 0, None], "i", [0, 1, 1, None, 1, 0, 0]),
    ("sevenths", [0, 0, 1, 1, 1, 0, 1], "f", [0, 1, 1, 0, 1, 0, 1]),
]


def dcol(vals, kind) -> tuple[pl.Series, str]:
    if kind == "i":
        s = i64(vals)
        return s, enc_iz(s)
    if kind == "k":  # thousandths (2 -> 2000), 9999 = NaN
        s = f64([None if v is None else (nan if v == 9999 else v) for v in vals])
        return s, enc_fk(s)
    s = f64(vals)
    return s, enc_fz(s)


def suite_conf() -> Suite:
    s = Suite("r3_conf")
    # (a) the real train.run
    g = Group(CONF)
    for name, ind in real_train_samples():
        rec, snap = traced(train.run.__code__, ["s09", "s11"], lambda ind=ind: b9.real_run(ind, encoded=False))
        i9, o9, i11, o11 = snap["s09", "in"], snap["s09", "out"], snap["s11", "in"], snap["s11", "out"]
        full = i9["logit_scored_train"]
        # the slice run on the full frame IS what the real run did
        ns = run_slice("s09", {"logit_scored_train": full})
        for k in ("logit_scored_train", "confusion_matrix_train", "training_metrics"):
            assert same(ns[k], o9[k]), (name, k)
        assert o9["logit_scored_train"].columns == full.columns + ["pred_logistic"] and same(o9["logit_scored_train"].drop("pred_logistic"), full)
        cols = ["default_flag", "pd_logistic"]
        small = full.select(cols)
        term = frame_term([("default_flag", enc_fz(small["default_flag"])), ("pd_logistic", enc_fb(small["pd_logistic"]))])
        ns = conf9(g, f"real train.run, {name} ({small.height} rows, columns {cols})", small, term)
        assert same(ns["confusion_matrix_train"], o9["confusion_matrix_train"]) and same(ns["training_metrics"], o9["training_metrics"])
        assert same(ns["logit_scored_train"], o9["logit_scored_train"].select(cols + ["pred_logistic"]))
        fullv = i11["logit_scored_valid"]
        ns = run_slice("s11", {"logit_scored_valid": fullv})
        for k in ("confusion_matrix", "validation_metrics"):
            assert same(ns[k], o11[k]), (name, k)
        cols = ["default_flag", "pred_logistic"]
        small = fullv.select(cols)
        term = frame_term([("default_flag", enc_fz(small["default_flag"])), ("pred_logistic", enc_iz(small["pred_logistic"]))])
        ns = conf11(g, f"real train.run, {name} ({small.height} rows, columns {cols})", small, term)
        assert same(ns["confusion_matrix"], o11["confusion_matrix"]) and same(ns["validation_metrics"], o11["validation_metrics"])
        print(f"[{name}] cm train {o9['confusion_matrix_train'].rows()} cm valid {o11['confusion_matrix'].rows()}")
    g.flush(s)
    # (b) hand-made frames, the source lines of the slice executed on them
    g = Group(CONF)
    for name, dflt, kind, pd in H09:
        d, dt = dcol(dflt, kind)
        p = pl.Series("x", [None if v is None else (nan if v == 9999 else float(f"{v}e-3")) for v in pd], dtype=pl.Float64)
        df = pl.DataFrame({"default_flag": d, "pd_logistic": p})
        ns = conf9(g, f"hand: {name}", df, frame_term([("default_flag", dt), ("pd_logistic", enc_fk(p))]))
        print(f"[09 {name}] {ns['confusion_matrix_train'].rows()} {ns['training_metrics'].rows()}")
    for name, dflt, kind, pred in H11:
        d, dt = dcol(dflt, kind)
        p = i64(pred)
        df = pl.DataFrame({"default_flag": d, "pred_logistic": p})
        ns = conf11(g, f"hand: {name}", df, frame_term([("default_flag", dt), ("pred_logistic", enc_iz(p))]))
        print(f"[11 {name}] {ns['confusion_matrix'].rows()} {ns['validation_metrics'].rows()}")
    g.flush(s)
    note = ("evaluated directly on its input frame; real = the locals of the real train.run at the slice boundaries (line tracer), "
            "Lean input = the columns the slice reads (results asserted equal to the full-frame run); hand = the slice's source "
            "lines executed verbatim on hand-made frames (null levels cannot all be produced by the upstream code)")
    s.notes = {U09: note, U11: note}
    return s


# ---------------------------------------------------------------- cumulative lift (step 05)
LIFT = (
    "let lift := fun (fl : String) (D : List (Int × Int × Int)) (SB : List (Option UInt64 × String)) (PF : List (String × UInt64)) => ("
    + b6.SBPF +
    "let dd : Pl.Frame Float := [(\"default_flag\", Pl.Col.f64 (fl.toList.map (fun (c : Char) => "
    "if c == '0' then some 0.0 else if c == '1' then some 1.0 else (none : Option Float))))]; "
    "let o := fun (k : Int) => if k < 0 then (none : Option Float) else if k == 999 then some (0.0 / 0.0) else some (Float.ofNat k.toNat); "
    "let da : Pl.Frame Float := [(\"decile\", Pl.Col.f64 (D.map (fun (p : Int × Int × Int) => o p.1))), "
    "(\"total_count\", Pl.Col.int (D.map (fun (p : Int × Int × Int) => if p.2.1 == -9 then none else some p.2.1))), "
    "(\"defaults\", Pl.Col.f64 (D.map (fun (p : Int × Int × Int) => o p.2.2)))]; "
    "[dg (tR dd), dg (tR da), dg (tR (metrics_run_05_cumulative_lift sb pf dd da))]); "
)


def run05(dd: pl.DataFrame, da: pl.DataFrame) -> tuple[pl.DataFrame, dict]:
    best: dict = {}
    o_best = sc.sas_best

    def w_best(x, w):
        r = o_best(x, w)
        assert w == 8
        assert best.setdefault(None if x is None else cmp.fbits(float(x)), r) == r
        return r

    sc.sas_best = w_best
    try:
        ns = run_slice("s05", {"decile_data": dd, "decile_analysis": da})
    finally:
        sc.sas_best = o_best
    return ns["cumulative_lift"], best


def lift_case(g: Group, name: str, dd: pl.DataFrame, da: pl.DataFrame, **kw) -> pl.DataFrame:
    """dd: default_flag (Float64 0 / 1 / null); da: decile Int64, total_count Int64, defaults Float64."""
    assert dd.columns == ["default_flag"] and da.columns == ["decile", "total_count", "defaults"]
    assert da.schema["decile"] == pl.Int64 and da.schema["total_count"] == pl.Int64 and da.schema["defaults"] == pl.Float64
    out, best = run05(dd, da)
    fl = "".join("n" if v is None else {0.0: "0", 1.0: "1"}[v] for v in dd["default_flag"].to_list())

    def code(v, null=-1):
        if v is None:
            return null
        if v != v:
            return 999
        assert v == int(v) and 0 <= v < 999, v
        return int(v)

    D = "[" + ", ".join(f"({code(a)}, {code(b, -9)}, {code(c)})" for a, b, c in da.iter_rows()) + "]"
    g.add(f"lift {lt.lean_str(fl)} {D} {b6.lean_tables(best, None)}", [
        (f"{name}: input decile_data", U05, dgf(dd), kw),
        (f"{name}: input decile_analysis", U05, dgf(da), kw),
        (f"{name}: cumulative_lift", U05, dgf(out), kw)])
    return out


def real_metric_inputs():
    """(name, validation csv text, training csv text): the B6 scenario slices and hand-made tables,
    then tables whose deciles (2 rows each) have a null default_flag in chosen deciles."""
    for sc_, nv, nt in (("a", b6.NV, b6.NT), ("b", 100, 250), ("c", 100, 250)):
        d = ROOT / "inputs" / "scenarios" / f"edge_metrics_{sc_}"
        yield (f"edge_metrics_{sc_}[{nv}/{nt}]",
               "".join((d / "risk_scores_validation.csv").read_text().splitlines(keepends=True)[:nv + 1]),
               "".join((d / "risk_scores_train.csv").read_text().splitlines(keepends=True)[:nt + 1]))
    for name, (v, t) in b6.HAND.items():
        yield name, b6.csv_text(b6.frame(100001, v)), b6.csv_text(b6.frame(1, t))
    for name, nulls in NULL_DECILES.items():
        v = [(None if i // 2 in nulls else (i * 7) % 3 % 2, 40 + 45 * i) for i in range(20)]
        yield f"null deciles {name}", b6.csv_text(b6.frame(100001, v)), b6.csv_text(b6.frame(1, b6.T30))


# deciles (0-based, 2 validation rows each) whose default_flag is null: `defaults` is null there
NULL_DECILES = {"first": {0}, "middle": {4}, "last": {9}, "three in a row": {3, 4, 5}, "first two and last two": {0, 1, 8, 9},
                "alternate": {1, 3, 5, 7, 9}, "all but one": {0, 1, 2, 3, 4, 6, 7, 8, 9}, "all": set(range(10))}
# hand-made (decile, total_count, defaults) rows: 999 = NaN, None = null
HL = [
    ("unsorted deciles, nulls first / middle / last", "0110n1", [(3, 4, None), (1, 5, None), (5, 2, 2), (2, 3, 1), (4, 6, None), (6, 1, None)]),
    ("all defaults null", "nn", [(1, 2, None), (2, 2, None), (3, 1, None)]),
    ("no null", "0101", [(2, 2, 1), (1, 2, 1)]),
    ("NaN defaults is kept, not filled", "011", [(1, 2, 1), (2, 2, 999), (3, 2, None), (4, 2, 3)]),
    ("null decile key sorts first; one row", "1", [(None, 1, 1)]),
    ("total_count 0 first (outside the precondition: divisor 0)", "01", [(1, 0, None), (2, 0, 0), (3, 2, 1), (4, 0, None)]),
    ("every default_flag null (total_defaults missing)", "nnn", [(1, 2, None), (2, 1, None)]),
    ("default_flag all 0 (rate 0: divisor 0 inside div)", "000", [(1, 2, 0), (2, 1, None), (3, 1, 0)]),
]


def suite_lift(cap: dict) -> Suite:
    s = Suite("r3_lift")
    g = Group(LIFT)
    for name, c in cap.items():
        i5, o5 = c["snap"]["s05", "in"], c["snap"]["s05", "out"]
        ddf, daf = i5["decile_data"], i5["decile_analysis"]
        out_full, _ = run05(ddf, daf)
        assert same(out_full, o5["cumulative_lift"]), name  # the slice on the full frames is the real run
        dd, da = ddf.select("default_flag"), daf.select("decile", "total_count", "defaults")
        out = lift_case(g, f"real mc.run, {name}", dd, da)
        new = ["cum_defaults", "cum_count", "cum_capture_rate", "cum_lift"]
        assert same(out.select(new), o5["cumulative_lift"].select(new)), name
        assert same(o5["cumulative_lift"].drop(new), daf.sort("decile", maintain_order=True)), name
        print(f"[05 {name}] defaults {da['defaults'].to_list()} cum_defaults {out['cum_defaults'].to_list()} cum_lift nulls {out['cum_lift'].null_count()}")
    g.flush(s)
    g = Group(LIFT)
    for name, fl, rows in HL:
        dd = pl.DataFrame({"default_flag": f64([None if ch == "n" else int(ch) for ch in fl])})
        da = pl.DataFrame({"decile": i64([r[0] for r in rows]), "total_count": i64([r[1] for r in rows]),
                           "defaults": f64([None if r[2] is None else (nan if r[2] == 999 else r[2]) for r in rows])})
        out = lift_case(g, f"hand: {name}", dd, da)
        print(f"[05 hand {name}] cum_defaults {out['cum_defaults'].to_list()} rate {out['cum_capture_rate'].to_list()} lift {out['cum_lift'].to_list()}")
    g.flush(s)
    s.notes = {U05: "evaluated directly on decile_data / decile_analysis; real = the locals of the real metrics_calculation.run at "
                    "the slice boundaries (line tracer), Lean input = the columns the slice reads (default_flag; decile, total_count, "
                    "defaults), the other columns pass through unchanged (asserted); hand = the slice's source lines executed verbatim; "
                    "decile compared as Float64 (R-F2I); sas_best / parse_float = lookup tables of the values that occur"}
    return s


# ---------------------------------------------------------------- PSI (step 06)
PSI = (ENC +
       "let P := fun (c : Pl.Col Float) => ([(\"pd_logistic\", c)] : Pl.Frame Float); "
       "let psi := fun (t v : Pl.Frame Float) => (let r0 := metrics_run_06_psi t v false; let r1 := metrics_run_06_psi t v true; "
       "[dg (tR t), dg (tR v), dg (tR r0.1), dg (tR r0.2), dg (tR r1.1), dg (tR r1.2)]); "
       )
PSIBIG = (
    "let P := fun (c : Pl.Col Float) => ([(\"pd_logistic\", c)] : Pl.Frame Float); "
    "let G := fun (n a b m : Nat) => P (Pl.Col.f64 ((List.range n).map (fun (i : Nat) => some (Float.ofScientific ((i * a + b) % m) true 4)))); "
    + PSI1)
RAISED: list[str] = []


def run06(t: pl.DataFrame, v: pl.DataFrame, fix: bool, name: str):
    """-> (psi_calculation, psi_summary, note) of the slice; None when Python raises before the end."""
    env = {"logit_scored_train": t, "logit_scored_valid": v, "fix_psi_bins": fix}
    try:
        ns = run_slice("s06", env)
        note = ""
    except ValueError as e:
        assert "--fix-psi-bins" in str(e) and fix
        ns = run_slice("s06", env, shadow={"abs": lambda x: 0.0})  # only disables the test of :276
        note = "Python raises ValueError at :277 (outside the precondition); expected = continuation with the test of :276 disabled"
        RAISED.append(f"{name} fix_psi_bins=True: {note}")
    return ns["psi_calculation"], ns["psi_summary"], note


def psi_cases(name: str, t: pl.DataFrame, v: pl.DataFrame, flags=(False, True), guard=True) -> list[tuple]:
    cases = ([(f"{name}: input logit_scored_train", U06, dgf(t)), (f"{name}: input logit_scored_valid", U06, dgf(v))] if guard else [])
    info = []
    for fix in flags:
        try:
            pc, ps, note = run06(t, v, fix, name)
        except Exception as e:  # noqa: BLE001  Python raises where the Lean returns a value
            note = f"Python raises {type(e).__name__} ({str(e)[:60]}) before the end of the slice: outside the precondition; no expected value"
            RAISED.append(f"{name} fix_psi_bins={fix}: {note}")
            kw = {"expect_diff": True, "note": note}
            cases += [(f"{name}: psi_calculation fix_psi_bins={fix}", U06, -1, kw), (f"{name}: psi_summary fix_psi_bins={fix}", U06, -1, kw)]
            info.append(f"fix={fix}: {type(e).__name__}")
            continue
        kw = {"note": note} if note else {}
        cases += [(f"{name}: psi_calculation fix_psi_bins={fix}", U06, dgf(pc), kw), (f"{name}: psi_summary fix_psi_bins={fix}", U06, dgf(ps), kw)]
        info.append(f"fix={fix}: rows {pc.height} valid_pct zeros {sum(1 for x in pc['valid_pct'].to_list() if x == 0.0)} "
                    f"PSI {ps.item(0, 'PSI')!r}{' RAISE' if note else ''}")
    print(f"[06 {name}] train {t.height} valid {v.height}; " + "; ".join(info))
    return cases


def pdf(vals) -> pl.DataFrame:
    return pl.DataFrame({"pd_logistic": pl.Series("pd_logistic", [None if k is None else float(f"{k}e-3") for k in vals], dtype=pl.Float64)})


# hand-made heights: (name, training pd in thousandths, validation pd in thousandths)
HP = [
    ("heights 1 / 1", [500], [500]),
    ("heights 1 / 1, validation above", [500], [700]),
    ("heights 2 / 1", [200, 800], [100]),
    ("heights 1 / 2", [500], [100, 900]),
    ("heights 2 / 2", [200, 800], [300, 900]),
    ("heights 3 / 0 (validation without rows)", [200, 500, 800], []),
    ("heights 0 / 3 (training without rows)", [], [200, 500, 800]),
    ("heights 0 / 0", [], []),
    ("training bins without validation rows", [50 * i + 10 for i in range(20)], [15, 20, 400, 410, 990]),
    ("null pd on both sides, training bins without validation rows", [None, 100, 200, None, 300, 400, 500, 600, 700, 800, 900, 950], [None, 120, 130, 940]),
    ("one distinct value each", [300, 300, 300, 300], [300, 300]),
    ("all training pd null", [None, None], [100, 200]),
]


def gen_frame(n: int, a: int, b: int, m: int) -> pl.DataFrame:
    return pl.DataFrame({"pd_logistic": pl.Series("pd_logistic", [float(f"{(i * a + b) % m}e-4") for i in range(n)], dtype=pl.Float64)})


def suite_psi(cap: dict) -> Suite:
    s = Suite("r3_psi")
    g = Group(PSI)
    for name, c in cap.items():
        if name.startswith("null deciles"):
            continue
        if not name.startswith("edge_metrics") and g.calls and g.cases[0][0].startswith("real mc.run, edge_metrics"):
            g.flush(s)
        i6 = c["snap"]["s06", "in"]
        tf, vf = i6["logit_scored_train"], i6["logit_scored_valid"]
        t, v = tf.select("pd_logistic"), vf.select("pd_logistic")
        # the slice on the restricted frames gives what the real run gave on the full frames, for both flags
        for fix in (False, True):
            L = c["locals"][fix]
            pc, ps, _ = run06(t, v, fix, f"real mc.run, {name}")
            assert same(pc, L["psi_calculation"]) and same(ps, L["psi_summary"]), (name, fix)
            pc2, ps2, _ = run06(tf, vf, fix, f"real mc.run, {name}")
            assert same(pc2, pc) and same(ps2, ps)
        enc = enc_fs if max(t.height, v.height) > 40 else enc_fk
        g.add(f"psi (P {enc(t['pd_logistic'])}) (P {enc(v['pd_logistic'])})", psi_cases(f"real mc.run, {name}", t, v))
    for name, tk, vk in HP:
        t, v = pdf(tk), pdf(vk)
        g.add(f"psi (P {enc_fk(t['pd_logistic'])}) (P {enc_fk(v['pd_logistic'])})", psi_cases(f"hand: {name}", t, v))
    g.flush(s)
    s.notes = {U06: "evaluated directly on logit_scored_train / logit_scored_valid (column pd_logistic; the other columns are not read: "
                    "asserted on the real run); real = the locals of the real metrics_calculation.run at the slice boundaries; hand = the "
                    "slice's source lines executed verbatim; score_bin compared as Float64 (R-F2I)"
                    + ("; " + "; ".join(dict.fromkeys(RAISED)) if RAISED else "")}
    return s


# frames generated inside Lean (i -> ((i * a + b) mod m) / 10000), one eval input per case
BIG = [
    # name, training (n, a, b, m), validation (n, a, b, m), flags
    ("training 4999 rows, 3 validation rows", (4999, 7919, 3, 10007), (3, 100, 4000, 10007), (True,)),
    ("training 5000 rows, 3 validation rows", (5000, 7919, 3, 10007), (3, 100, 4000, 10007), (False, True)),
    ("training 5001 rows, 3 validation rows", (5001, 7919, 3, 10007), (3, 100, 4000, 10007), (True,)),
    ("12 training rows, 5000 validation rows in a narrow range", (12, 800, 100, 10007), (5000, 1, 3000, 2003), (True,)),
    ("12 training rows, 5001 validation rows in a narrow range", (12, 800, 100, 10007), (5001, 1, 3000, 2003), (False, True)),
]


def suite_psibig() -> Suite:
    s = Suite("r3_psibig")
    g = Group(PSIBIG)
    for k, (name, tp, vp, flags) in enumerate(BIG):
        if k == 3:
            g.flush(s)
        t, v = gen_frame(*tp), gen_frame(*vp)
        ga = lambda p: "(G " + " ".join(str(x) for x in p) + ")"  # noqa: E731
        for j, fx in enumerate(flags):
            g.add(f"psi1 {ga(tp)} {ga(vp)} {'true' if fx else 'false'}", psi_cases(f"generated: {name}", t, v, flags=(fx,), guard=True)
                  if j == 0 else [(c[0] + " (again)", *c[1:]) if "input" in c[0] else c for c in psi_cases(f"generated: {name}", t, v, flags=(fx,))])
    g.flush(s)
    s.notes = {U06: "bin heights around 5000 / 5001 (0.5 / height against 1e-4), frames generated inside Lean and mirrored in Python "
                    "(input digests compared first); the slice's source lines executed verbatim"
                    + ("; " + "; ".join(dict.fromkeys(RAISED)) if RAISED else "")}
    return s


def capture_metrics() -> dict:
    """The real metrics_calculation.run on every input of real_metric_inputs, both flags, traced."""
    cap = {}
    for name, vt, tt in real_metric_inputs():
        loc, snap0 = {}, None
        ok = True
        for fix in (False, True):
            try:
                r, snap = traced(mc.run.__code__, ["s05", "s06"], lambda vt=vt, tt=tt, fix=fix: b6.pyrun(vt, tt, fix))
                if r["raised"] is not None:
                    r, snap = traced(mc.run.__code__, ["s05", "s06"], lambda vt=vt, tt=tt, fix=fix: b6.pyrun(vt, tt, fix, no_raise=True))
            except Exception as e:  # noqa: BLE001  the upstream code of `run` raises on this input
                r = {"raised": f"{type(e).__name__}: {str(e)[:80]}", "locals": None}
            if r["raised"] is not None or r["locals"] is None:
                ok = False
                print(f"[{name}] the real run does not finish (fix={fix}): {r['raised']}")
                break
            loc[fix] = r["locals"]
            snap0 = snap0 or snap
        if ok:
            cap[name] = {"snap": snap0, "locals": loc}
    return cap


if __name__ == "__main__":
    a = sys.argv[1:]
    want = set(a) or {"conf", "lift", "psi", "psibig"}
    if "conf" in want:
        suite_conf().write()
    if want & {"lift", "psi"}:
        cap = capture_metrics()
        if "lift" in want:
            suite_lift(cap).write()
        if "psi" in want:
            suite_psi(cap).write()
    if "psibig" in want:
        suite_psibig().write()
