"""Fidelity pass 2026-11-20, third attempt (label glue-end-to-end): the four compositions chained at Float
exactly as def:pyPipeline wires them (feature_engineering.run -> train.run -> predict.run ->
metrics_calculation.run, each stage reading what the stage before wrote), evaluated end to end through
def:zz_carrier_fid_2 against the REAL port (HEAD 4a757fb) run on the same files.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_glue_gen.py py A B
      runs the Python pipeline on seeds A..B-1 (pickles work/fz10c_glue/<seed>.pkl)
  ... fz10c_glue_gen.py lean <name> <seeds...>     -> work/fz10c_glue_<name>.inputs.json (one eval input)
  ... fz10c_glue_gen.py cmp <name>                 compares work/fz10c_glue_<name>.out.txt

One seed s:
  cs-training.csv  the frame mk(s) of diffeval/units/fz_run_gen.py (1-12 rows; modes: valid, repeated / missing
                   id, edge cells, text columns, names, no known income), with the split file of
                   diffeval/units/fz10_run_gen.py (a file that fits, or ids the port's seeded draw replaces);
                   for s >= BIG the frame mkB(s): 20-60 valid rows (more fits)
  cs-test.csv      the frame mk(s + TOFF) (resp. mkB(s + TOFF))
Python: the four REAL stages in a temp folder, each on the files the stage before wrote; write_sas_csv is
the real writer, wrapped to record each frame; the run is made twice, with the real formatters and with the
injective encodings of t18_gen.py (fmt_wd, fmt_oddsr, sas_d8, sas_d12_3, sas_pvalue; the writer itself
always renders with the real ones), and the two must agree cell by cell after decoding.
Lean (one term per seed, chained ON THE LEAN VALUES):
  R1 := run full IB SB (some (Pl.toTable (mk s))) (sp s)                       pyPipeline.features
  F1r, F2r := RB (read-back) of the two feature tables of R1                    py.readFeatures
  R2 := run_py_py_py fw fo d8 d12 pv chi2 today SW fsum inv solve ... F1r F2r   pyPipeline.fit / score
  R3 := run_py_py full IB icpt coefs SB coefExists TEST (RB medians of R1)      pyPipeline.scoreTest
  R4 := run_py msb mpf d8 today fsum (RB of R2's validation scores) (RB of R2's training scores)
  plus ScoreRun as pyPipeline.score / noFitTrain (def:PyLinks) wire it: S1, S2 against the port's
  risk_scores_train.csv / risk_scores_validation.csv frames.
Out-of-scope parameters (RULEBOOK 3, def:PyParams): IB / SB the tables of fz_run_gen (real input_best32 /
sas_best12 over the pools); SW the real stepwise result of the seed; the numeric routines, chi2, fsum,
log1p, pow2: tables of the real results keyed on the bits of their arguments (x27_train_gen.py); msb / mpf:
tables of the real sas_best / parse_float; the read-backs RB: proc_import_csv's rule (numeric iff every
non-empty value of the window is a number; else text cut to the window's widest value), with the value
read back from the BEST12. / BEST32. / percent8.2 text in a table keyed on the bits written (only values
that change); the Python mirror of RB is asserted equal to the real import on every read.
"""
from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import math
import pickle
import re
import shutil
import sys
import tempfile
import traceback
import warnings
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
_argv = list(sys.argv)
sys.argv = [sys.argv[0]]
import fz10_run_gen as F  # noqa: E402  (patches fz_run_gen: split rule of 4a757fb)
sys.argv = _argv
import kit  # noqa: E402
import leanterm as lt  # noqa: E402
import t18_gen as b  # noqa: E402
import u18b_gen as u  # noqa: E402
import x27_train_gen as x27  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import metrics_calculation as mc  # noqa: E402
from credit_risk import predict as pr  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

g = F.g
WORK = HERE.parent / "work"
PK = WORK / "fz10c_glue"
TOFF = 7_777_777
BIG = 50_000_000
BLUEPRINT = "5365851c-5549-44b7-9207-4bd4c422031d"
ITEM, DECL = "def:zz_carrier_fid_2", "zz_carrier_fid_2"
fb, w, ts = b.fb, b.w, b.ts
NUMRE = re.compile(sc._NUM_RE)
FILES1 = ["income_medians.csv", "model_features_train.csv", "model_features_validation.csv"]


# ------------------------------------------------------------------ inputs
def mkB(s: int) -> pl.DataFrame:
    """20-60 valid rows: the pools of fz_run_gen, every column numeric, ids 1..n (more rows: fits)."""
    n = 30 + kit.hsh(s, 98) % 31
    cols = {}
    for j, nm in enumerate(g.N0):
        if j == 0:
            cols[nm] = pl.Series([float(i + 1) for i in range(n)], dtype=pl.Float64)
        else:
            cols[nm] = pl.Series(kit.gF(s * 16 + j, n, 100, 0, PSB[j - 1]), dtype=pl.Float64)
    return pl.DataFrame(cols)


PSB = [[v for v in pool if v is None or (abs(v) < 1e6 and (v == 0 or abs(v) > 1e-6))] for pool in g.PS]


REAL = 90_000_000           # real-data seeds: rows of legacy/data (REAL + k: training rows 30k.., test rows 20k..)
NR_TR, NR_TE = 30, 20
RAW = HERE.parent.parent.parent.parent / "legacy" / "data"


def real_frame(name: str, n: int, k: int) -> pl.DataFrame:
    """n consecutive rows of the raw file, every column Float64 (NA -> null), named as the port's import names them"""
    d = pl.read_csv(RAW / name, null_values=["NA"], infer_schema_length=0)
    d = d.slice(k * n, n)
    # a column with no value at all (the test file's target) is what the port's import makes of it: String
    return pl.DataFrame({nm: d.get_column(d.columns[j]).cast(pl.String if d.get_column(d.columns[j]).null_count() == n else pl.Float64)
                         for j, nm in enumerate(g.N0)})


def frame(s: int) -> pl.DataFrame:
    if s >= REAL + TOFF:
        return real_frame("cs-test.csv", NR_TE, s - REAL - TOFF)
    if s >= REAL:
        return real_frame("cs-training.csv", NR_TR, s - REAL)
    return mkB(s) if s >= BIG else g.mk(s)


def lean_frame(df: pl.DataFrame) -> str:
    def cell(v):
        return "none" if v is None else f"some (Float.ofBits {fb(float(v))})"

    def col(n):
        c = df.get_column(n)
        if c.dtype == pl.String:
            assert c.null_count() == len(c)
            return f'("{n}", Pl.Col.str (List.replicate {len(c)} none))'
        return f'("{n}", Pl.Col.f64 [' + ", ".join(cell(v) for v in c.to_list()) + "])"
    return "[" + ", ".join(col(n) for n in df.columns) + "]"


def split_ids(s: int, n: int) -> list[float]:
    if s < BIG:
        return g.split(s)
    if kit.hsh(s, 397) % 4 >= 2:
        nt = (7 * n + 9) // 10
        r = kit.hsh(s, 398) % n
        return [float((i + r) % n + 1) for i in range(nt)]
    return [float(i + 1) for i in range(n + 2) if kit.hsh(s, 400 + i) % 2 == 0] or [1.0]


# ------------------------------------------------------------------ tabular mirror (Pl.toTable)
def cell_of(dtype, v):
    if dtype == pl.String:
        return ("s", None if v is None else v)
    if dtype == pl.Date:
        return ("s", v.isoformat())
    if v is None or dtype == pl.Null:
        return ("n", None)
    return ("n", float(v))


def to_tab(df: pl.DataFrame) -> list[list[tuple]]:
    cols = [(n, df.schema[n], df.get_column(n).to_list()) for n in df.columns]
    return [[(n, cell_of(t, v[i])) for n, t, v in cols] for i in range(df.height)]


def tab_bits(t):
    return [[(n, k, (None if v is None else (fb(v) if k == "n" else v))) for n, (k, v) in r] for r in t]


# ------------------------------------------------------------------ the read-back (proc_import_csv after write_sas_csv)
def render(c: tuple, fmt: str | None) -> str:
    k, v = c
    if k == "s":
        return "" if v is None else v.rstrip(" ")
    if v is None:
        return ""
    if fmt is None:
        return sc.sas_best12(v)
    if fmt == "best32":
        return sc.sas_best(v, 32)
    if fmt == "percent":
        return sc.fmt_percent(v, 8, 2)
    raise ValueError(fmt)


CODES = {None: 0, "best32": 1, "percent": 2}


class RBTables:
    """the per-value tables the Lean read-back uses (pure functions of the bits: shared by every seed)"""

    def __init__(self):
        self.b12: dict[int, int] = {}   # bits -> bits read back from the BEST12. text (only values that change)
        self.b32: dict[int, int] = {}   # the same for BEST32.
        self.txt: dict[tuple, tuple] = {}  # (code, bits) -> (text, numeric?): every number whose text is no number,
        #                                    and every number in a column read back as text


def rb_mirror(t, win: int | None, fmts: dict[str, str], T: RBTables):
    """what the Lean RB computes on table t (and the table entries it needs)."""
    if not t:
        return []
    names = [n for n, _ in t[0]]
    cols = {n: [dict(r)[n] for r in t] for n in names}
    out_cols = {}
    for n in names:
        cs = cols[n]
        fmt = fmts.get(n)
        code = CODES[fmt]
        texts = [render(c, fmt) for c in cs]
        for c, x in zip(cs, texts):
            if c[0] == "s" and x != "":
                assert not NUMRE.match(x.strip()), (n, x, "a numeric text cell written")
            if c[0] == "n" and c[1] is not None and not NUMRE.match(x.strip()):
                T.txt[(code, fb(c[1]))] = (x, False)
        wt = [x for x in (texts if win is None else texts[:win]) if x != ""]
        if wt and all(NUMRE.match(x.strip()) for x in wt):
            new = []
            for c, x in zip(cs, texts):
                if x == "" or not NUMRE.match(x.strip()):
                    new.append(("n", None))
                    continue
                assert c[0] == "n", (n, c)
                r = float(x.strip())
                tb = T.b32 if fmt == "best32" else T.b12
                if fb(r) != fb(c[1]):
                    assert tb.setdefault(fb(c[1]), fb(r)) == fb(r)
                new.append(("n", r))
            out_cols[n] = new
        else:
            wd = max((len(x) for x in wt), default=0) or 1
            new = []
            for c, x in zip(cs, texts):
                if c[0] == "n" and c[1] is not None:
                    T.txt[(code, fb(c[1]))] = (x, bool(NUMRE.match(x.strip())))
                new.append(("s", None if x == "" else x[:wd]))
            out_cols[n] = new
    return [[(n, out_cols[n][i]) for n in names] for i in range(len(t))]


# ------------------------------------------------------------------ the Python pipeline
def csv_text(df: pl.DataFrame) -> str:
    return g.csv_text(df)


class Rec:
    pass


def run_pipeline(s: int, encoded: bool) -> dict:
    """the four real stages on files; recorders as in x27_train_gen.real_run plus metrics' sas_best."""
    rec: dict = {"imports": [], "writes": [], "chi2": [], "solve": [], "inv": [], "fsum": [], "stepwise": None,
                 "locals": None, "in_fit": False, "model_json": None, "stage": {}, "best": {}, "today": dt.date.today()}
    o_import, o_write, o_step, o_chi2 = sc.proc_import_csv, sc.write_sas_csv, sc.stepwise_logistic, sc.chi2_sf
    o_solve, o_inv, o_fsum, o_best = np.linalg.solve, np.linalg.inv, math.fsum, sc.sas_best
    cur = {"stage": None}

    def w_import(path, guessingrows=20):
        d = o_import(path, guessingrows=guessingrows)
        rec["imports"].append((cur["stage"], Path(path).name, guessingrows, d.clone()))
        return d

    def w_write(df, path, formats=None):
        rec["writes"].append((cur["stage"], Path(path).name, df.clone(), dict(formats or {})))
        saved = {k: getattr(sc, k) for k in b.ENCODERS}
        for k, f in b.REAL.items():
            setattr(sc, k, f)
        try:
            o_write(df, path, formats=formats)
        finally:
            for k, f in saved.items():
                setattr(sc, k, f)

    def w_step(*a, **k):
        rec["in_fit"] = True
        try:
            r = o_step(*a, **k)
        finally:
            rec["in_fit"] = False
        rec["stepwise"] = r
        return r

    def w_chi2(x, df):
        r = o_chi2(x, df)
        if not rec["in_fit"]:
            rec["chi2"].append((float(x), int(df), float(r)))
        return r

    def w_solve(a, bb):
        r = o_solve(a, bb)
        if not rec["in_fit"]:
            rec["solve"].append((np.array(a, dtype=np.float64), np.array(bb, dtype=np.float64), np.array(r, dtype=np.float64)))
        return r

    def w_inv(a):
        r = o_inv(a)
        if not rec["in_fit"]:
            rec["inv"].append((np.array(a, dtype=np.float64), np.array(r, dtype=np.float64)))
        return r

    def w_fsum(xs):
        xs = [float(x) for x in xs]
        r = o_fsum(xs)
        if not rec["in_fit"]:
            rec["fsum"].append((xs, float(r)))
        return r

    def w_best(x, width):
        r = o_best(x, width)
        if cur["stage"] == "metrics" and sys._getframe(1).f_code is mc._into_float.__code__:
            assert width == 8
            k = None if x is None else fb(float(x))
            assert rec["best"].setdefault(k, r) == r
        return r

    def prof(frame_, event, arg):
        if event == "return" and frame_.f_code is train.run.__code__:
            rec["locals"] = dict(frame_.f_locals)

    df = frame(s)
    dt_ = frame(s + TOFF)
    sp = split_ids(s, df.height)
    math.fsum = w_fsum
    np.linalg.solve, np.linalg.inv = w_solve, w_inv
    sc.proc_import_csv, sc.write_sas_csv, sc.stepwise_logistic, sc.chi2_sf, sc.sas_best = w_import, w_write, w_step, w_chi2, w_best
    if encoded:
        for k, f in b.ENCODERS.items():
            setattr(sc, k, f)
    try:
        with tempfile.TemporaryDirectory() as td, warnings.catch_warnings():
            warnings.simplefilter("ignore")
            data, out = Path(td) / "data", Path(td) / "out"
            data.mkdir()
            (data / "cs-training.csv").write_text(csv_text(df), encoding="utf-8")
            (data / "cs-test.csv").write_text(csv_text(dt_), encoding="utf-8")
            (Path(td) / "split.csv").write_text("row_id\n" + "".join(f"{int(i)}\n" for i in sp))
            stages = [
                ("fe", lambda: fe.run(data, out, split_ids=Path(td) / "split.csv"), "Feature engineering stopped"),
                ("train", lambda: train.run(out, out), "Model training stopped"),
                ("predict", lambda: pr.run(out, out, data_dir=data, income_medians=out / "income_medians.csv"), "Test set scoring stopped"),
                ("metrics", lambda: mc.run(out, out), None),
            ]
            for name, fn, _msg in stages:
                cur["stage"] = name
                if name == "train":
                    sys.setprofile(prof)
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        fn()
                    rec["stage"][name] = "completed"
                except ValueError as e:
                    if "stopped" in str(e) and "Nothing is exported" in str(e):
                        rec["stage"][name] = "stopped"
                    else:
                        rec["stage"][name] = f"raised ValueError: {str(e)[:120]}"
                except Exception as e:  # noqa: BLE001
                    rec["stage"][name] = f"raised {type(e).__name__}: {str(e)[:120]}"
                finally:
                    sys.setprofile(None)
                if name == "train" and (out / "model.json").exists() and rec["stage"]["train"] == "completed":
                    rec["model_json"] = json.loads((out / "model.json").read_text())
                if rec["stage"][name].startswith("raised"):
                    break
    finally:
        math.fsum = o_fsum
        np.linalg.solve, np.linalg.inv = o_solve, o_inv
        sc.proc_import_csv, sc.write_sas_csv, sc.stepwise_logistic, sc.chi2_sf, sc.sas_best = o_import, o_write, o_step, o_chi2, o_best
        for k, f in b.REAL.items():
            setattr(sc, k, f)
    rec["frame"], rec["test"], rec["split"] = df, dt_, sp
    return rec


def check_encoded(real: dict, enc: dict) -> int:
    assert real["stage"] == enc["stage"], (real["stage"], enc["stage"])
    assert [(a, n) for a, n, _, _ in real["writes"]] == [(a, n) for a, n, _, _ in enc["writes"]]
    k = 0
    for (_, name, a, _), (_, _, bb, _) in zip(real["writes"], enc["writes"], strict=True):
        assert a.columns == bb.columns and a.dtypes == bb.dtypes and a.height == bb.height, name
        for c in a.columns:
            for x, y in zip(a.get_column(c).to_list(), bb.get_column(c).to_list(), strict=True):
                if isinstance(y, str) and (r := b.decode_and_format(y)) is not None:
                    assert x == r, (name, c, x, y, r)
                    k += 1
                elif isinstance(x, float):
                    assert y is not None and fb(x) == fb(y), (name, c, x, y)
                else:
                    assert x == y, (name, c, x, y)
    assert real["model_json"] == enc["model_json"]
    return k


# ------------------------------------------------------------------ expected values
def tdig(t) -> list[int]:
    """t18_gen.TD on a mirrored table"""
    if not t:
        return [0]
    names = [n for n, _ in t[0]]
    out = [len(t), len(names)]
    for j, n in enumerate(names):
        toks = ts(n)
        for r in t:
            k, v = r[j][1]
            if k == "n":
                toks += [1, 0] if v is None else [1, 1, fb(v)]
            else:
                toks += [2, 0] if v is None else [2, 1] + ts(v)
        out.append(w(toks))
    return out


def tdn(name, t) -> int:
    return w([w(ts(name))] + tdig(t))


def tdp(name, cols, t) -> int:
    return w([w(ts(name)), w([x for c in cols for x in ts(c)])] + tdig(t))


def stage_writes(rec, st):
    return [(n, df) for a, n, df, _ in rec["writes"] if a == st]


def mj_digest(mj) -> int:
    if mj is None:
        return -1
    i = mj["intercept"]
    return w(([0] if i is None else [1, fb(i)]) + [t for c, v in mj["coefficients"].items() for t in ts(c) + [fb(v)]])


def expected(rec) -> dict:
    st = rec["stage"]
    e = {}
    for name in ("fe", "train", "predict", "metrics"):
        r = st.get(name)
        if r is None or r.startswith("raised"):
            e[name] = None
            continue
        ws = stage_writes(rec, name)
        if r == "stopped":
            assert not ws
            e[name] = w([-1])
        elif name == "predict":
            e[name] = w([len(ws)] + [tdp(n, df.columns, to_tab(df)) for n, df in ws])
        else:
            e[name] = w([len(ws)] + [tdn(n, to_tab(df)) for n, df in ws])
    if st.get("train") == "stopped":
        e["model"], e["S1"], e["S2"] = -1, -3, -3
    if st.get("train") == "completed":
        e["model"] = mj_digest(rec["model_json"])
        ws = dict(stage_writes(rec, "train"))
        e["S1"] = w(tdig(to_tab(ws["risk_scores_train.csv"])))
        e["S2"] = w(tdig(to_tab(ws["risk_scores_validation.csv"])))
    return e


# ------------------------------------------------------------------ one seed, Python side (pickled)
def py_seed(s: int) -> dict:
    out = {"seed": s}
    try:
        real = run_pipeline(s, encoded=False)
        enc = run_pipeline(s, encoded=True)
        out["n_fmt"] = check_encoded(real, enc)
    except AssertionError:
        out["error"] = "assert: " + traceback.format_exc()[-600:]
        return out
    rec = enc
    out["stage"] = rec["stage"]
    held = True
    imp = {(a, n): d for a, n, _, d in rec["imports"]}
    # the generated frames are what the port imported (fz_run_gen's "held" test)
    fr = imp.get(("fe", "cs-training.csv"))
    if fr is not None and g.bits(fr) != g.bits(rec["frame"]):
        held = False
    te = imp.get(("predict", "cs-test.csv"))
    if te is not None and g.bits(te) != g.bits(rec["test"]):
        held = False
    out["held"] = held
    out["expected"] = expected(rec)
    T = RBTables()
    # the read-backs: mirror == real import
    reads = {"train": [("model_features_train.csv", None, {}), ("model_features_validation.csv", None, {})],
             "predict": [("income_medians.csv", 20, {"median_income": "best32", "overall_median_income": "best32"})],
             "metrics": [("risk_scores_validation.csv", 20, {"interest_rate": "percent"}),
                         ("risk_scores_train.csv", 20, {"interest_rate": "percent"})]}
    written = {n: df for a, n, df, _ in rec["writes"]}
    for st_, lst in reads.items():
        for n, win, fm in lst:
            if (st_, n) in imp:
                mir = rb_mirror(to_tab(written[n]), win, fm, T)
                real_ = to_tab(imp[(st_, n)])
                assert tab_bits(mir) == tab_bits(real_), (s, n)
    out["rb"] = dict(T.__dict__)
    # what Lean needs: stepwise, routine tables, sas_best tables, today, texts
    out["stepwise"] = rec["stepwise"]
    out["T"] = x27.routine_tables(rec) if rec["stage"].get("train") == "completed" else None
    out["best"] = rec["best"]
    out["mfsum"] = {b.vw(xs): fb(r) for xs, r in rec["fsum"]}
    out["today"] = rec["today"].isoformat()
    out["texts_ok"] = (g.texts_used(rec["frame"]) <= g.KEYS) and (g.texts_used(rec["test"]) <= g.KEYS) if s < BIG else True
    sw = rec["stepwise"]
    out["fit"] = None if sw is None else ("nofit" if sw.final is None else len(sw.final.names) - 1)
    out["nofit_empty"] = sw is not None and sw.final is None and sw.steps == [] and sw.intercept_only is None
    out["rows"] = (rec["frame"].height, rec["test"].height)
    return out


def py_range(a: int, z: int) -> None:
    PK.mkdir(parents=True, exist_ok=True)
    stats: dict = {}
    for s in range(a, z):
        try:
            o = py_seed(s)
        except Exception:  # noqa: BLE001
            o = {"seed": s, "error": traceback.format_exc()[-600:]}
        (PK / f"{s}.pkl").write_bytes(pickle.dumps(o))
        k = ("ERROR" if "error" in o else
             f"{'held' if o['held'] else 'NOTHELD'} fe={o['stage'].get('fe')} train={o['stage'].get('train')} "
             f"predict={o['stage'].get('predict')} metrics={o['stage'].get('metrics')} fit={o.get('fit')}")
        stats[k] = stats.get(k, 0) + 1
    for k, v in sorted(stats.items(), key=lambda x: -x[1]):
        print(v, k)


# ------------------------------------------------------------------ Lean
LRB = (
    "let rstr := fun (t : String) => String.ofList (t.toList.reverse.dropWhile (fun (c : Char) => c == ' ')).reverse; "
    "let TXF := fun (code : Nat) (x : Float) => TXT.find? (fun (e : Nat × UInt64 × String × Bool) => e.1 == code && e.2.1 == x.toBits); "
    "let rnd := fun (code : Nat) (c : Tabular.Cell Float) => (match c with "
    "| .num none => (true, \"\", false) "
    "| .num (some x) => (match TXF code x with | some e => (e.2.2.1.isEmpty, e.2.2.1, e.2.2.2) | none => (false, \"\", true)) "
    "| .str none => (true, \"\", false) "
    "| .str (some t) => (let r := rstr t; (r.isEmpty, r, false)) : Bool × String × Bool); "
    "let rv := fun (code : Nat) (x : Float) => (match (if code == 1 then B32 else B12).find? (fun (p : UInt64 × Int) => p.1 == x.toBits) with "
    "| some p => Float.ofBits (((x.toBits.toNat : Int) + p.2).toNat.toUInt64) | none => x : Float); "
    "let RB := fun (win : Option Nat) (codes : List (String × Nat)) (t : Tabular.Table Float) => (match t with "
    "| [] => ([] : Tabular.Table Float) "
    "| r0 :: _ => (let wt := (match win with | none => t | some k => t.take k : Tabular.Table Float); "
    "let conv := r0.map (fun (p0 : String × Tabular.Cell Float) => (let n := p0.1; let code := (codes.lookup n).getD 0; "
    "let wr := (wt.map (fun (r : Tabular.Row Float) => rnd code ((r.lookup n).getD (Tabular.Cell.num none)))).filter (fun (q : Bool × String × Bool) => !q.1); "
    "let isNum := !wr.isEmpty && wr.all (fun (q : Bool × String × Bool) => q.2.2); "
    "let wd := max 1 (wr.foldl (fun (m : Nat) (q : Bool × String × Bool) => max m q.2.1.length) 0); "
    "(n, code, isNum, wd))); "
    "t.map (fun (r : Tabular.Row Float) => conv.map (fun (q : String × Nat × Bool × Nat) => (q.1, "
    "(let c := (r.lookup q.1).getD (Tabular.Cell.num none); let z := rnd q.2.1 c; "
    "if q.2.2.1 then (match c with | .num (some x) => (if z.2.2 then Tabular.Cell.num (some (rv q.2.1 x)) else Tabular.Cell.num none) | _ => Tabular.Cell.num none : Tabular.Cell Float) "
    "else (if z.1 then Tabular.Cell.str none else Tabular.Cell.str (some (String.ofList (z.2.1.toList.take q.2.2.2)))) : Tabular.Cell Float)))))); "
)
LGEN = (
    "let PSB : List (List (Option Float)) := PS.map (fun (L : List (Option Float)) => L.filter (fun (v : Option Float) => "
    "(match v with | none => true | some x => (x.abs < 1000000.0 && (x == 0.0 || x.abs > 0.000001)) : Bool))); "
    f"let mkB := fun (s : Nat) => (let n := 30 + h s 98 31; (List.range 12).map (fun (j : Nat) => (N0.getD j \"\", ("
    "(if j == 0 then Pl.Col.f64 ((List.range n).map (fun (i : Nat) => some (Float.ofNat (i + 1)))) "
    "else Pl.Col.f64 (gF (s * 16 + j) n 100 0 (PSB.getD (j - 1) []))) : Pl.Col Float))) : Pl.Frame Float); "
    "let spB := fun (s n : Nat) => ((if h s 397 4 ≥ 2 then (List.range ((7 * n + 9) / 10)).map (fun (i : Nat) => (i + h s 398 n) % n) "
    "else (let v := (List.range (n + 2)).filter (fun (i : Nat) => h s (400 + i) 2 == 0); if v.isEmpty then [0] else v)).map "
    "(fun (i : Nat) => [(\"row_id\", Tabular.Cell.num (some (Float.ofNat (i + 1))))]) : Tabular.Table Float); "
    f"let FRM := fun (s : Nat) => (if s ≥ {REAL + TOFF} then RT else if s ≥ {REAL} then RF else if s ≥ {BIG} then mkB s else mk s); "
    f"let SPL := fun (s : Nat) => (if s ≥ {REAL} then spB s {NR_TR} else if s ≥ {BIG} then spB s (30 + h s 98 31) else sp s); "
    "let isS := fun (c : Pl.Col Float) => (match c with | .str _ => true | _ => false : Bool); "
)
LCHAIN = (
    "let msb := fun (x : Option Float) (_ : Int) => (match MSBT.lookup (x.map Float.toBits) with | some t => t | none => \"?\" : String); "
    "let mpf := fun (t : String) => Float.ofBits ((MPFT.lookup t).getD 1); "
    "let TDP := fun (f : String × List String × Tabular.Table Float) => W ([W (ts f.1), W (f.2.1.flatMap ts)] ++ TD f.2.2); "
    "let EF := fun (r : Option (List (String × Tabular.Table Float))) => W (match r with | none => [-1] | some fs => (fs.length : Int) :: fs.map (fun (p : String × Tabular.Table Float) => W (TDN p)) : List Int); "
    "let SC := fun (i : Float) (cs : List (String × Float)) (F : Tabular.Table Float) => "
    "(let filler : LogisticFit Float := { names := [], beta := Np.NDArray.d1 [], cov := Np.NDArray.d2 [], loglik := 0, n_iter := 0, converged := false }; "
    "let scored := train_run_10_score_valid (some i) cs (some filler) (Pl.ofTable F); "
    "let risk := (train_run_12_risk_scores scored scored).2; "
    "(train_run_14_final_and_summary today none risk risk risk risk risk risk risk false false).lookup \"risk_scores_validation.csv\"); "
    "let NF := fun (F : Tabular.Table Float) => (let mft := Pl.ofTable F; "
    "let s01 := train_run_01_fit_frame ({} : StepwiseResult Float) mft; "
    "let s04 := train_run_04_score_train s01.1 s01.2.1 s01.2.2.2.1 mft; "
    "let s09 := train_run_09_confusion_train s04.2.2.2.2.2.2.1; "
    "let risk := (train_run_12_risk_scores s09.1 s09.1).1; "
    "(train_run_14_final_and_summary today s01.2.2.2.1 risk risk risk risk risk risk risk false false).lookup \"risk_scores_train.csv\"); "
    "let SDg := fun (o : Option (Tabular.Table Float)) => (match o with | none => (-2 : Int) | some t => W (TD t) : Int); "
    "let GLUE := fun (s : Nat) (SW : StepwiseResult Float) => (let full := s % 2 == 0; let FR := FRM s; let TE := FRM (s + " + str(TOFF) + "); "
    "let R1 := run (α := Float) full IB SB (some (Pl.toTable FR)) (SPL s); "
    "let fs1 := R1.getD []; "
    "let F1r := (fs1.lookup \"model_features_train.csv\").map (RB none []); "
    "let F2r := (fs1.lookup \"model_features_validation.csv\").map (RB none []); "
    "let MDr := (fs1.lookup \"income_medians.csv\").map (RB (some 20) [(\"median_income\", 1), (\"overall_median_income\", 1)]); "
    "let R2 := run_py_py_py fw fo d8 d12 pv chi2 today SW fsum inv solve matmul matvec dot einsum log1p pow2 F1r F2r; "
    "let fs2 := (R2.map Prod.fst).getD []; let mj := R2.bind Prod.snd; "
    "let coefE := fs2.any (fun (p : String × Tabular.Table Float) => p.1 == \"model_coefficients.csv\"); "
    "let TEST := some (TE.map (fun (p : String × Pl.Col Float) => (p.1, isS p.2)), Pl.toTable TE); "
    "let R3 := (match mj with | some (some i, cs) => run_py_py full IB i cs SB coefE TEST MDr "
    "| some (none, _) => none | none => run_py_py full IB 0.0 [] SB coefE TEST MDr : Option (List (String × List String × Tabular.Table Float))); "
    "let RS := fun (n : String) => (fs2.lookup n).map (RB (some 20) [(\"interest_rate\", 2)]); "
    "let R4 := run_py msb mpf d8 today fsum (RS \"risk_scores_validation.csv\") (RS \"risk_scores_train.csv\"); "
    "let S12 : Int × Int := (if R2.isNone then (-3, -3) else (match mj with "
    "| some (some i, cs) => (SDg (F1r.bind (SC i cs)), SDg (F2r.bind (SC i cs))) "
    "| some (none, _) => (-4, -4) "
    "| none => (SDg (F1r.bind NF), W (TD [])) : Int × Int)); "
    "[EF R1, EF (R2.map Prod.fst), (match mj with | none => (-1 : Int) | some (i, cs) => W (o i ++ cs.flatMap (fun (p : String × Float) => ts p.1 ++ [bi p.2])) : Int), "
    "W (match R3 with | none => [-1] | some fs => (fs.length : Int) :: fs.map TDP : List Int), EF R4, S12.1, S12.2]); "
)
POS = ["fe", "train", "model", "predict", "metrics", "S1", "S2"]


def merge_T(Ts: list[dict]) -> dict:
    M = {"solve": [], "matmul": [], "matvec": [], "dot": [], "inv": [], "einsum": [], "log1p": {}, "pow2": {}, "chi2": [], "fsum": {}}
    seen = {k: set() for k in M}
    for T in Ts:
        for k in ("solve", "matmul", "matvec", "dot", "einsum", "inv"):
            for row in T[k]:
                key = row[:1] if k == "inv" else row[:2]
                if key not in seen[k]:
                    seen[k].add(key)
                    M[k].append(row)
        for k in ("log1p", "pow2", "fsum"):
            for a, r in T[k].items():
                assert M[k].setdefault(a, r) == r
        for row in T["chi2"]:
            if row[:2] not in seen["chi2"]:
                seen["chi2"].add(row[:2])
                M["chi2"].append(row)
    return M


def lean_tables(outs: list[dict]) -> str:
    Ts = [o["T"] for o in outs if o.get("T")]
    M = merge_T(Ts + [{"solve": [], "matmul": [], "matvec": [], "dot": [], "inv": [], "einsum": [], "log1p": {}, "pow2": {}, "chi2": [],
                        "fsum": o["mfsum"]} for o in outs])
    b12, b32, txt, best = {}, {}, {}, {}
    for o in outs:
        rb = o["rb"]
        for d, src in ((b12, rb["b12"]), (b32, rb["b32"]), (txt, rb["txt"]), (best, o["best"])):
            for k, v in src.items():
                assert d.setdefault(k, v) == v
    today = {o["today"] for o in outs}
    assert len(today) == 1, today
    pf = sorted({v for v in best.values() if v})
    return (x27.lean_routines(M)
            + f"let B12 : List (UInt64 × Int) := [{', '.join(f'({a}, {c - a})' for a, c in b12.items())}]; "
            + f"let B32 : List (UInt64 × Int) := [{', '.join(f'({a}, {c - a})' for a, c in b32.items())}]; "
            + "let TXT : List (Nat × UInt64 × String × Bool) := ["
            + ", ".join(f"({cd}, {bt}, {lt.lean_str(t)}, {'true' if nm else 'false'})" for (cd, bt), (t, nm) in txt.items()) + "]; "
            + "let MSBT : List (Option UInt64 × String) := ["
            + ", ".join(f"({'none' if k is None else f'some {k}'}, {lt.lean_str(v)})" for k, v in best.items()) + "]; "
            + "let MPFT : List (String × UInt64) := [" + ", ".join(f"({lt.lean_str(v)}, {fb(float(v))})" for v in pf) + "]; "
            + f'let today : Tabular.Cell Float := Tabular.Cell.str (some "{today.pop()}"); ')


PREFIX = (g.MINI + kit.GEN + g.TAB + g.LETS[:g.LETS.index("let u := fun (i : Int)")] + b.W + b.BI + b.OF + b.TS + b.TX + b.TD + b.FL + b.MW + b.FMT + b.KEYED + u.MKFIT)


def load(s: int) -> dict:
    return pickle.loads((PK / f"{s}.pkl").read_bytes())


CHUNK = 20


def seed_value(o) -> tuple[str, int]:
    """('full', W of the 7 values) or ('fe', W [fe]); asserts every value of a full seed is compared"""
    e = o["expected"]
    if o["stage"].get("train", "").startswith("raised"):
        assert e["fe"] is not None
        return "fe", w([e["fe"]])
    vals = [e.get(p_) for p_ in POS]
    assert all(v is not None for v in vals), (o["seed"], e)
    return "full", w(vals)


def lean_input(name: str, seeds: list[int]) -> None:
    outs = [load(s) for s in seeds]
    for o in outs:
        assert "error" not in o and o["held"] and o["texts_ok"], o["seed"]
    kinds = {o["seed"]: seed_value(o) for o in outs}

    def empty(sw):
        return sw is None or (not sw.steps and sw.final is None and sw.intercept_only is None)
    fe_only = [o for o in outs if kinds[o["seed"]][0] == "fe"]
    full_e = [o for o in outs if kinds[o["seed"]][0] == "full" and empty(o["stepwise"])]
    rest = [o for o in outs if kinds[o["seed"]][0] == "full" and not empty(o["stepwise"])]
    order = fe_only + full_e + rest
    body = [f"let SF : List Nat := {[o['seed'] for o in fe_only]}; let SZ : List Nat := {[o['seed'] for o in full_e]}; "
            "let vF : List Int := SF.map (fun (s : Nat) => W [(GLUE s ({} : StepwiseResult Float)).headD 0]); "
            "let vZ : List Int := SZ.map (fun (s : Nat) => W (GLUE s ({} : StepwiseResult Float))); "]
    for k, o in enumerate(rest):
        body.append(f"let r{k} : Int := W (GLUE {o['seed']} {u.lean_stepwise(o['stepwise'])}); ")
    tab_outs = [o for o in outs if kinds[o["seed"]][0] == "full"]
    reals = [o["seed"] for o in outs if o["seed"] >= REAL]
    assert len(reals) <= 1
    rf = (f"let RF : Pl.Frame Float := {lean_frame(frame(reals[0]))}; let RT : Pl.Frame Float := {lean_frame(frame(reals[0] + TOFF))}; "
          if reals else "let RF : Pl.Frame Float := []; let RT : Pl.Frame Float := []; ")
    prefix = PREFIX
    if reals:
        # the real-data values of MonthlyIncome / NumberOfDependents are outside fz_run_gen's SB / IB pools:
        # extend both tables with the real sas_best12 text and the real input_best32 of that text
        vals = sorted({v for s_ in (reals[0], reals[0] + TOFF) for c in ("MonthlyIncome", "NumberOfDependents")
                       for v in frame(s_).get_column(c).to_list() if v is not None and not isinstance(v, str)})
        txt = [sc.sas_best12(v) for v in vals]
        back = pl.DataFrame({"t": txt}).select(sc.input_best32(pl.col("t"))).to_series().to_list()
        ext_b = (f"let BF : List Float := BF ++ [{', '.join(f'Float.ofBits {fb(v)}' for v in vals)}]; "
                 f"let BT : List String := BT ++ [{', '.join(lt.lean_str(t) for t in txt)}]; ")
        ext_t = ("let T : List (String × Float) := T ++ ["
                 + ", ".join(f"({lt.lean_str(t)}, Float.ofBits {fb(b_)})" for t, b_ in zip(txt, back) if b_ is not None) + "]; ")
        assert prefix.count("let SB :=") == 1 and prefix.count("let IB :=") == 1
        prefix = prefix.replace("let SB :=", ext_b + "let SB :=").replace("let IB :=", ext_t + "let IB :=")
    text = ("(" + prefix + lean_tables(tab_outs or outs[:1]) + LRB + rf + LGEN + LCHAIN + "".join(body)
            + "let V : List Int := vF ++ vZ ++ [" + ", ".join(f"r{k}" for k in range(len(rest))) + "]; "
            + f"(List.range ((V.length + {CHUNK - 1}) / {CHUNK})).map (fun (c : Nat) => W ((V.drop (c * {CHUNK})).take {CHUNK})))")
    meta = {"seeds": [o["seed"] for o in order], "kinds": [kinds[o["seed"]][0] for o in order],
            "values": [kinds[o["seed"]][1] for o in order], "expected": [o["expected"] for o in order]}
    (WORK / f"fz10c_glue_{name}.meta.json").write_text(json.dumps(meta))
    (WORK / f"fz10c_glue_{name}.in.txt").write_text(text)
    print(name, len(seeds), f"seeds (fe only {len(fe_only)}, full no-SW {len(full_e)}, with SW {len(rest)})", len(text), "chars")


def cmp_out(name: str) -> dict:
    meta = json.loads((WORK / f"fz10c_glue_{name}.meta.json").read_text())
    got = json.loads((WORK / f"fz10c_glue_{name}.out.txt").read_text().strip())
    vals = meta["values"]
    exp = [w(vals[c * CHUNK:(c + 1) * CHUNK]) for c in range((len(vals) + CHUNK - 1) // CHUNK)]
    bad = [c for c, (a, b_) in enumerate(zip(exp, got)) if a != b_]
    res = {"seeds": len(vals), "fe_only": meta["kinds"].count("fe"), "full": meta["kinds"].count("full"),
           "values_compared": sum(1 if k == "fe" else 7 for k in meta["kinds"]), "chunks": len(exp), "got_chunks": len(got),
           "differing_chunks": [(c, meta["seeds"][c * CHUNK:(c + 1) * CHUNK]) for c in bad]}
    print(json.dumps(res))
    return res


if __name__ == "__main__":
    if sys.argv[1] == "py":
        py_range(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == "lean":
        lean_input(sys.argv[2], [int(x) for x in sys.argv[3:]])
    elif sys.argv[1] == "cmp":
        cmp_out(sys.argv[2])
