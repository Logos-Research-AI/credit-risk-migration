"""port-translator-9, update 2026-11-16 (T18): differential test of train.run (def:run_py_py_py), the
restored def:train_run_05_association and def:train_run_13_roc, and the other step items, chained.

Adapted from units/b9_gen.py (same method: the REAL train.run under recorders on a row sample of
the real feature files, formatters as injective encodings, numeric routines as tables of what the
real routines returned). Changes: project paths; `fsum` (math.fsum, called inside roc_association)
is a table of the real results keyed on the digest of the list it received; the two input tables
are `some`; the result is an Option; three more cases: a feature file absent (the real train.run
raises ValueError, writes nothing, the five listed files are gone, the others stay).

  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t18_gen.py
      -> diffeval/work/t18_run.json + .inputs.json (ONE eval_decl input, on def:zz_carrier_t)
  ... t18_gen.py --mask <integer>   names the bits of the localisation mask
"""
from __future__ import annotations

import datetime as dt
import json
import math
import re
import struct
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np
import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import compare as cmp  # noqa: E402
from suite import Suite  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

ROOT = HERE.parents[3]
DATA = HERE.parent / "work" / "t18_data"
REALFE = HERE.parent / "work" / "t9" / "out"  # feature files of the real feature-engineering run (t9_realrun.py)
SENT = struct.unpack("<Q", struct.pack("<d", -7.25))[0]
N_TRAIN, STRIDE_TRAIN, OFF_TRAIN = 60, 1250, 2
N_VALID, STRIDE_VALID, OFF_VALID = 25, 1700, 1
# planted nulls: (row position in the sample, column)
NULLS_TRAIN = [(5, "monthly_income"), (20, "default_flag"), (33, "income_per_dependent"), (47, "age_group")]
NULLS_VALID = [(3, "income_per_dependent"), (9, "default_flag"), (15, "age_group"), (20, "has_delinquency")]
SHORT = 26  # the column-level localisation mask compares the values modulo SHORT (one letter each)


def fb(x) -> int:
    return cmp.fbits(float(x))


def w(t) -> int:
    h = 14695981039346656037
    for x in t:
        h = (h * 1099511628211 + x + 7) % 18446744073709551616
    return h


def ts(s: str) -> list[int]:
    return [len(s)] + [ord(c) for c in s]


def o(v) -> list[int]:
    return [0] if v is None else [1, fb(v)]


# ------------------------------------------------------------------ the sample
def sample_inputs() -> Path:
    """work/b9_data/in/model_features_{train,validation}.csv (built once from the real pipeline)."""
    ind = DATA / "in"
    if (ind / "model_features_train.csv").exists() and (ind / "model_features_validation.csv").exists():
        return ind
    full = REALFE
    if not (full / "model_features_train.csv").exists():
        fe.run(ROOT / "legacy" / "data", full, split_ids=HERE.parents[1] / "inputs" / "split_ids.csv")
    ind.mkdir(parents=True, exist_ok=True)
    for name, n, stride, off, nulls in [("model_features_train.csv", N_TRAIN, STRIDE_TRAIN, OFF_TRAIN, NULLS_TRAIN),
                                        ("model_features_validation.csv", N_VALID, STRIDE_VALID, OFF_VALID, NULLS_VALID)]:
        d = sc.proc_import_csv(full / name, guessingrows=None)[off::stride].head(n)
        assert d.height == n and all(t == pl.Float64 for t in d.dtypes)
        for row, col in nulls:
            d = d.with_columns(pl.when(pl.int_range(pl.len()) == row).then(None).otherwise(pl.col(col)).alias(col))
        d.write_csv(ind / name)
    return ind


# ------------------------------------------------------------------ the formatters as encodings
def enc(x) -> str:
    return "N" if x is None else str(fb(x))


ENCODERS = {
    "fmt_wd": lambda x, w_, d: f"w{enc(x)}/{w_}/{d}",
    "fmt_oddsr": lambda x, w_, d: f"o{enc(x)}/{w_}/{d}",
    "sas_d8": lambda x: f"e{enc(x)}",
    "sas_d12_3": lambda x: f"t{enc(x)}",
    "sas_pvalue": lambda x: f"p{enc(x)}",
}
REAL = {k: getattr(sc, k) for k in ENCODERS}
ENC_RE = re.compile(r"^([woetp])(N|\d+)(?:/(-?\d+)/(-?\d+))?$")


def decode_and_format(cell: str) -> str | None:
    """The real formatter applied to the arguments an encoded cell stands for (None: not encoded)."""
    m = ENC_RE.match(cell)
    if not m:
        return None
    x = None if m.group(2) == "N" else struct.unpack("<d", struct.pack("<Q", int(m.group(2))))[0]
    k = m.group(1)
    if k == "w":
        return REAL["fmt_wd"](x, int(m.group(3)), int(m.group(4)))
    if k == "o":
        return REAL["fmt_oddsr"](x, int(m.group(3)), int(m.group(4)))
    return REAL[{"e": "sas_d8", "t": "sas_d12_3", "p": "sas_pvalue"}[k]](x)


# ------------------------------------------------------------------ the real run under recorders
def real_run(ind: Path, encoded: bool) -> dict:
    rec: dict = {"imports": [], "writes": [], "chi2": [], "solve": [], "fsum": [], "stepwise": None, "locals": None, "in_fit": False}
    o_import, o_write, o_step, o_chi2, o_solve = sc.proc_import_csv, sc.write_sas_csv, sc.stepwise_logistic, sc.chi2_sf, np.linalg.solve

    def w_import(path, guessingrows=20):
        d = o_import(path, guessingrows=guessingrows)
        rec["imports"].append((Path(path).name, d.clone()))
        return d

    def w_write(df, path, formats=None):
        rec["writes"].append((Path(path).name, df.clone()))

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

    def w_solve(a, b):
        r = o_solve(a, b)
        if not rec["in_fit"]:
            rec["solve"].append((np.array(a, dtype=np.float64), np.array(b, dtype=np.float64), np.array(r, dtype=np.float64)))
        return r

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is train.run.__code__:
            rec["locals"] = dict(frame.f_locals)

    o_fsum = math.fsum

    def w_fsum(xs):
        xs = [float(x) for x in xs]
        r = o_fsum(xs)
        if not rec["in_fit"]:
            rec["fsum"].append((xs, float(r)))
        return r

    math.fsum = w_fsum
    sc.proc_import_csv, sc.write_sas_csv, sc.stepwise_logistic, sc.chi2_sf, np.linalg.solve = w_import, w_write, w_step, w_chi2, w_solve
    if encoded:
        for k, f in ENCODERS.items():
            setattr(sc, k, f)
    try:
        with tempfile.TemporaryDirectory() as td, warnings.catch_warnings():
            warnings.simplefilter("ignore")
            sys.setprofile(prof)
            try:
                import contextlib
                import io

                with contextlib.redirect_stdout(io.StringIO()):
                    train.run(ind, Path(td))
            finally:
                sys.setprofile(None)
            rec["model_json"] = json.loads((Path(td) / "model.json").read_text())
    finally:
        math.fsum = o_fsum
        sc.proc_import_csv, sc.write_sas_csv, sc.stepwise_logistic, sc.chi2_sf, np.linalg.solve = o_import, o_write, o_step, o_chi2, o_solve
        for k, f in REAL.items():
            setattr(sc, k, f)
    return rec


def check_real_against_encoded(real: dict, encd: dict) -> int:
    """Every frame of the run with the real formatters is the encoded run with the real formatter
    applied to the decoded arguments. Returns the number of formatted cells checked."""
    assert [n for n, _ in real["writes"]] == [n for n, _ in encd["writes"]]
    n = 0
    for (name, a), (_, b) in zip(real["writes"], encd["writes"], strict=True):
        assert a.columns == b.columns and a.dtypes == b.dtypes and a.height == b.height, name
        for c in a.columns:
            for x, y in zip(a.get_column(c).to_list(), b.get_column(c).to_list(), strict=True):
                if isinstance(y, str) and (r := decode_and_format(y)) is not None:
                    assert x == r, (name, c, x, y, r)
                    n += 1
                elif isinstance(x, float):
                    assert y is not None and fb(x) == fb(y), (name, c, x, y)
                else:
                    assert x == y, (name, c, x, y)
    assert real["model_json"] == encd["model_json"]
    return n


# ------------------------------------------------------------------ expected values (Python)
def kind_tokens(c: pl.Series) -> list[int]:
    v = c.to_list()
    t = c.dtype
    if t == pl.Float64 or t == pl.Float32:
        return [1, len(v)] + [x for e in v for x in o(e)]
    if t.is_integer():
        return [2, len(v)] + [x for e in v for x in ([0] if e is None else [1, int(e)])]
    if t == pl.Boolean:
        return [3, len(v)] + [x for e in v for x in ([0] if e is None else [1, int(e)])]
    if t == pl.String:
        return [4, len(v)] + [x for e in v for x in ([0] if e is None else [1] + ts(e))]
    if t == pl.Date:
        return [5, len(v)]
    if t == pl.Null:
        return [6, len(v)]
    raise TypeError(str(t))


def fd(df: pl.DataFrame) -> list[int]:
    """Frame digests: [number of columns] + one digest per column (name, kind, values)."""
    return [df.width] + [w(ts(n) + kind_tokens(df.get_column(n))) for n in df.columns]


def cell_tokens(t, v) -> list[int]:
    """The tokens of the Tabular cell Pl.toTable gives for a value of dtype t."""
    if t == pl.String:
        return [2, 0] if v is None else [2, 1] + ts(v)
    if t == pl.Date:  # the `today` cell
        return [2, 1] + ts(v.isoformat())
    if t == pl.Null or v is None:
        return [1, 0]
    return [1, 1, fb(v)]


def td(df: pl.DataFrame) -> list[int]:
    """Table digests of Pl.toTable df: [rows] and, when there is a row, [columns] + one digest per
    column (name, cells)."""
    if df.height == 0:
        return [0]
    return [df.height, df.width] + [
        w(ts(n) + [x for v in df.get_column(n).to_list() for x in cell_tokens(df.schema[n], v)]) for n in df.columns]


def tdn(name: str, df: pl.DataFrame) -> list[int]:
    return [w(ts(name))] + td(df)


def labels_fd(what: str, df: pl.DataFrame) -> list[str]:
    return [f"{what}: number of columns"] + [f"{what}.{n}" for n in df.columns]


def labels_tdn(name: str, df: pl.DataFrame) -> list[str]:
    if df.height == 0:
        return [f"{name}: file name", f"{name}: rows"]
    return [f"{name}: file name", f"{name}: rows", f"{name}: columns"] + [f"{name}.{n}" for n in df.columns]


# ------------------------------------------------------------------ Lean side
W = "let W := fun (t : List Int) => t.foldl (fun (h x : Int) => (h * 1099511628211 + x + 7) % 18446744073709551616) 14695981039346656037; "
BI = "let bi := fun (x : Float) => (x.toBits.toNat : Int); "
OF = "let o := fun (v : Option Float) => (match v with | none => [0] | some x => [1, bi x] : List Int); "
TS = "let ts := fun (s : String) => (s.length : Int) :: s.toList.map (fun (c : Char) => (c.toNat : Int)); "
TC = ("let tc := fun (c : Pl.Col Float) => (match c with | .f64 v => 1 :: (v.length : Int) :: v.flatMap o "
      "| .int v => 2 :: (v.length : Int) :: v.flatMap (fun (x : Option Int) => (match x with | none => [0] | some n => [1, n] : List Int)) "
      "| .bool v => 3 :: (v.length : Int) :: v.flatMap (fun (x : Option Bool) => (match x with | none => [0] | some b => [1, if b then 1 else 0] : List Int)) "
      "| .str v => 4 :: (v.length : Int) :: v.flatMap (fun (x : Option String) => (match x with | none => [0] | some s => 1 :: ts s : List Int)) "
      "| .cell v => [5, (v.length : Int)] | .null n => [6, (n : Int)] : List Int); ")
FD = "let FD := fun (fr : Pl.Frame Float) => (fr.length : Int) :: fr.map (fun (p : String × Pl.Col Float) => W (ts p.1 ++ tc p.2)); "
TX = ("let tx := fun (c : Tabular.Cell Float) => (match c with | .num none => [1, 0] | .num (some x) => [1, 1, bi x] "
      "| .str none => [2, 0] | .str (some s) => 2 :: 1 :: ts s : List Int); ")
TD = ("let TD := fun (t : Tabular.Table Float) => (match t with | [] => [0] | r0 :: _ => (t.length : Int) :: (r0.length : Int) :: "
      "(List.range r0.length).map (fun (j : Nat) => W (ts (r0.getD j (\"\", Tabular.Cell.num none)).1 ++ "
      "t.flatMap (fun (r : Tabular.Row Float) => tx (r.getD j (\"\", Tabular.Cell.num none)).2))) : List Int); "
      "let TDN := fun (p : String × Tabular.Table Float) => W (ts p.1) :: TD p.2; ")
FL = "let FL := fun (v : List UInt64) => v.map Float.ofBits; "
MW = ("let MW := fun (m : List (List Float)) => W ((m.length : Int) :: m.flatMap (fun (r : List Float) => (r.length : Int) :: r.map bi)); "
      "let VW := fun (v : List Float) => W ((v.length : Int) :: v.map bi); ")
# the five formatters: an injective encoding of the arguments (mirrors ENCODERS)
FMT = ('let en := fun (x : Option Float) => (match x with | none => "N" | some v => toString v.toBits.toNat : String); '
       'let fw := fun (x : Option Float) (a b : Int) => "w" ++ en x ++ "/" ++ toString a ++ "/" ++ toString b; '
       'let fo := fun (x : Option Float) (a b : Int) => "o" ++ en x ++ "/" ++ toString a ++ "/" ++ toString b; '
       'let d8 := fun (x : Option Float) => "e" ++ en x; '
       'let d12 := fun (x : Option Float) => "t" ++ en x; '
       'let pv := fun (x : Option Float) => "p" ++ en x; ')
# data decoder: a column is a string of tokens separated by spaces; a token is `~` (null), a
# decimal number, `#<bits>` or `<token>*<count>` (a run)
DEC = ('let pval := fun (s : String) => (if s == "~" then (none : Option Float) else '
       "let cs := s.toList; if cs.head? == some '#' then some (Float.ofBits (String.ofList (cs.drop 1)).toNat!.toUInt64) else "
       "let neg := cs.head? == some '-'; let cs := if neg then cs.drop 1 else cs; "
       "let ip := cs.takeWhile (fun (c : Char) => c != '.'); let fp := (cs.dropWhile (fun (c : Char) => c != '.')).drop 1; "
       "let v := Float.ofScientific (String.ofList (ip ++ fp)).toNat! true fp.length; some (if neg then -v else v)); "
       'let pcol := fun (s : String) => (s.splitOn " ").flatMap (fun (t : String) => (match t.splitOn "*" with '
       "| [v, k] => List.replicate k.toNat! (pval v) | _ => [pval t] : List (Option Float))); "
       "let mkT := fun (cols : List (String × String)) => let cs := cols.map (fun (p : String × String) => (p.1, pcol p.2)); "
       '((List.range (cs.headD ("", [])).2.length).map (fun (i : Nat) => cs.map (fun (p : String × List (Option Float)) => '
       "(p.1, Tabular.Cell.num (p.2.getD i none)))) : Tabular.Table Float); ")
KEYED = (
    f"let T1 := fun (T : List (UInt64 × UInt64)) (x : Float) => (match T.find? (fun (t : UInt64 × UInt64) => t.1 == x.toBits) with "
    f"| some t => Float.ofBits t.2 | none => Float.ofBits {SENT} : Float); "
    f"let T2 := fun (T : List (UInt64 × Int × UInt64)) (x : Float) (d : Int) => (match T.find? (fun (t : UInt64 × Int × UInt64) => t.1 == x.toBits && t.2.1 == d) with "
    f"| some t => Float.ofBits t.2.2 | none => Float.ofBits {SENT} : Float); "
    "let KVV := fun (T : List (Int × Int × List UInt64)) (ka kb : Int) => (match T.find? (fun (t : Int × Int × List UInt64) => t.1 == ka && t.2.1 == kb) with "
    "| some t => FL t.2.2 | none => ([] : List Float)); "
    "let KMM := fun (T : List (Int × Int × List (List UInt64))) (ka kb : Int) => (match T.find? (fun (t : Int × Int × List (List UInt64)) => t.1 == ka && t.2.1 == kb) with "
    "| some t => t.2.2.map FL | none => ([] : List (List Float))); "
)


def lean_float_decimal(x: float) -> str | None:
    """A decimal token that the Lean decoder reads back as exactly x, or None."""
    if x != x or math.isinf(x):
        return None
    s = repr(x)
    if "e" in s or "E" in s:
        return None
    if s.endswith(".0"):
        s = s[:-2]
    neg = s.startswith("-")
    u = s[1:] if neg else s
    ip, _, fp = u.partition(".")
    m, e = int(ip + fp), len(fp)
    # Lean's Float.ofScientific m true e (Init/Data/OfScientific.lean), emulated
    if m == 0:
        v = 0.0
    else:
        sh = max(64 - (m.bit_length() - 1), 0)
        mm = (m << (3 * e + sh)) // 5**e
        ex = -4 * e - sh
        s2 = max((mm.bit_length() - 1) - 63, 0)
        v = math.ldexp(float(mm >> s2), ex + s2)
    if neg:
        v = -v
    return s if fb(v) == fb(x) else None


def col_tokens(vals: list) -> str:
    toks = []
    for v in vals:
        if v is None:
            toks.append("~")
        else:
            d = lean_float_decimal(v)
            toks.append(d if d is not None else f"#{fb(v)}")
    out, i = [], 0
    while i < len(toks):
        j = i
        while j < len(toks) and toks[j] == toks[i]:
            j += 1
        n = j - i
        out.append(f"{toks[i]}*{n}" if n > 1 and len(toks[i]) * n > len(toks[i]) + 1 + len(str(n)) else " ".join([toks[i]] * n))
        i = j
    return " ".join(out)


def lean_table(df: pl.DataFrame) -> str:
    assert all(t == pl.Float64 for t in df.dtypes)
    return "(mkT [" + ", ".join(f'("{n}", "{col_tokens(df.get_column(n).to_list())}")' for n in df.columns) + "])"


def ul(xs) -> str:
    return "[" + ", ".join(str(fb(x)) for x in xs) + "]"


def ull(m) -> str:
    return "[" + ", ".join(ul(r) for r in m) + "]"


def lstr(s: str) -> str:
    return json.dumps(s, ensure_ascii=False)


def lean_fit(f: sc.LogisticFit) -> str:
    return (f"(mkfit [{', '.join(lstr(n) for n in f.names)}] {ul(f.beta)} {ull(np.atleast_2d(f.cov))} {fb(f.loglik)} "
            f"({int(f.n_iter)}) {'true' if f.converged else 'false'})")


MKFIT = ("let mkfit := fun (names : List String) (beta : List UInt64) (cov : List (List UInt64)) (ll : UInt64) (ni : Int) (cv : Bool) => "
         "({ names := names, beta := Np.NDArray.d1 (FL beta), cov := Np.NDArray.d2 (cov.map FL), loglik := Float.ofBits ll, "
         "n_iter := ni, converged := cv } : LogisticFit Float); ")


def lean_stepwise(r: sc.StepwiseResult) -> str:
    def opt_s(v):
        return "none" if v is None else f"some {lstr(v)}"

    def opt_f(v):
        return "none" if v is None else f"some (Float.ofBits {fb(v)})"

    steps = ", ".join(
        f"{{ step := {s.step}, entered := {opt_s(s.entered)}, removed := {opt_s(s.removed)}, df := {s.df}, "
        f"number_in_model := {s.number_in_model}, score_chisq := {opt_f(s.score_chisq)}, wald_chisq := {opt_f(s.wald_chisq)}, "
        f"p_value := Float.ofBits {fb(s.p_value)}, fit := {lean_fit(s.fit)} }}" for s in r.steps)
    fin = "none" if r.final is None else f"some {lean_fit(r.final)}"
    io = "none" if r.intercept_only is None else f"some {lean_fit(r.intercept_only)}"
    return f"({{ steps := [{steps}], final := {fin}, intercept_only := {io} }} : StepwiseResult Float)"


def mw(m) -> int:
    m = [list(r) for r in m]
    return w([len(m)] + [t for r in m for t in [len(r)] + [fb(v) for v in r]])


def vw(v) -> int:
    v = list(v)
    return w([len(v)] + [fb(x) for x in v])


def routine_tables(rec: dict) -> dict:
    """Argument / result pairs of the out-of-scope routines, from the captured run."""
    L = rec["locals"]
    stepwise, fit_frame, y_train, ybar, n_obs, final = rec["stepwise"], L["fit_frame"], L["y_train"], L["ybar"], L["n_obs"], L["final"]
    T = {"solve": [], "matmul": [], "matvec": [], "dot": [], "inv": [], "einsum": [], "log1p": {}, "pow2": {}, "explog": []}
    solves = list(rec["solve"])
    for st in stepwise.steps:  # train.py:159-193, the same numpy expressions
        names_k = st.fit.names
        x_k = np.column_stack([np.ones(n_obs), *[np.asarray(fit_frame.get_column(c).to_numpy(), dtype=np.float64) for c in names_k[1:]]])
        d = y_train - ybar
        u0 = x_k.T @ d
        g = x_k.T @ x_k
        i0 = ybar * (1.0 - ybar) * g
        a1, b1, s1 = solves.pop(0)
        assert mw(a1) == mw(i0) and vw(b1) == vw(u0), "recomputed i0 / u0 differ from what np.linalg.solve received"
        score = u0 @ s1
        b_slope = st.fit.beta[1:]
        a2, b2, s2 = solves.pop(0)
        assert mw(a2) == mw(st.fit.cov[1:, 1:]) and vw(b2) == vw(b_slope)
        wald = b_slope @ s2
        T["matvec"].append((mw(x_k.T), vw(d), u0))
        T["matmul"].append((mw(x_k.T), mw(x_k), g))
        T["solve"] += [(mw(a1), vw(b1), s1), (mw(a2), vw(b2), s2)]
        T["dot"] += [(vw(u0), vw(s1), float(score)), (vw(b_slope), vw(s2), float(wald))]
        m2ll = -2.0 * st.fit.loglik
        lr = L["m2ll0"] - m2ll
        T["explog"] += [(f"exp(-lr/n_obs) step {st.step}", "exp", -lr / n_obs, math.exp(-lr / n_obs))]
    assert not solves
    T["explog"] += [("log(n_obs)", "log", float(n_obs), math.log(n_obs)),
                    ("exp(-m2ll0/n_obs)", "exp", -L["m2ll0"] / n_obs, math.exp(-L["m2ll0"] / n_obs))]
    # classification_table(y_train, x_final, pd=pd_train): sas_compat.py:1071-1081
    x, p = L["x_final"], np.asarray(L["pd_train"], dtype=np.float64)
    with np.errstate(all="ignore"):
        for v in p:
            T["log1p"][fb(-v)] = fb(np.log1p(-v))
        wv = p * (1.0 - p)
        xw = x * wv[:, None]
        mm = x.T @ xw
        vi = np.linalg.inv(mm)
        q = np.einsum("ij,jk,ik->i", x, vi, x)
    T["matmul"].append((mw(x.T), mw(xw), mm))
    T["inv"].append((mw(mm), vi))
    T["einsum"].append((mw(x), mw(vi), q))
    # `** 2`: train.py:312 and sas_compat.py:1022
    for idx in [0, *L["final_index"]]:
        b = float(final.beta[idx])
        se = math.sqrt(float(final.cov[idx, idx]))
        T["pow2"][fb(b / se)] = fb((b / se) ** 2)
        if idx != 0:
            for nm, a in (("exp(b)", b), ("exp(b - Z975*se)", b - sc.Z975 * se), ("exp(b + Z975*se)", b + sc.Z975 * se)):
                T["explog"].append((f"{nm} idx {idx}", "exp", a, math.exp(a)))
    for _, _size, o1, e1, o0, e0 in L["hl_table"].iter_rows():
        for v in (float(o1) - e1, float(o0) - e0):
            T["pow2"][fb(v)] = fb(v**2)
    T["chi2"] = sorted({(fb(x), d, fb(r)) for x, d, r in rec["chi2"]})
    T["fsum"] = {vw(xs): fb(r) for xs, r in rec["fsum"]}
    for k in ("solve", "matmul", "matvec", "dot", "einsum"):  # one entry per key (a model fitted at two steps)
        seen, rows = set(), []
        for row in T[k]:
            if row[:2] not in seen:
                seen.add(row[:2])
                rows.append(row)
        T[k] = rows
    return T


def lean_routines(T: dict) -> str:
    kvv = lambda rows: "[" + ", ".join(f"({a}, {b}, {ul(out)})" for a, b, out in rows) + "]"  # noqa: E731
    kmm = lambda rows: "[" + ", ".join(f"({a}, {b}, {ull(out)})" for a, b, out in rows) + "]"  # noqa: E731
    return (
        f"let SV : List (Int × Int × List UInt64) := {kvv(T['solve'])}; "
        f"let MV : List (Int × Int × List UInt64) := {kvv(T['matvec'])}; "
        f"let EQ : List (Int × Int × List UInt64) := {kvv(T['einsum'])}; "
        f"let MM : List (Int × Int × List (List UInt64)) := {kmm(T['matmul'])}; "
        f"let IV : List (Int × Int × List (List UInt64)) := {kmm([(a, 0, out) for a, out in T['inv']])}; "
        f"let DT : List (Int × Int × UInt64) := [{', '.join(f'({a}, {b}, {fb(r)})' for a, b, r in T['dot'])}]; "
        f"let solve := fun (a : List (List Float)) (b : List Float) => KVV SV (MW a) (VW b); "
        f"let matvec := fun (a : List (List Float)) (b : List Float) => KVV MV (MW a) (VW b); "
        f"let einsum := fun (a b : List (List Float)) => KVV EQ (MW a) (MW b); "
        f"let matmul := fun (a b : List (List Float)) => KMM MM (MW a) (MW b); "
        f"let inv := fun (a : List (List Float)) => KMM IV (MW a) 0; "
        f"let dot := fun (a b : List Float) => (match DT.find? (fun (t : Int × Int × UInt64) => t.1 == VW a && t.2.1 == VW b) with "
        f"| some t => Float.ofBits t.2.2 | none => Float.ofBits {SENT} : Float); "
        f"let log1p := T1 [{', '.join(f'({a}, {b})' for a, b in T['log1p'].items())}]; "
        f"let pow2 := T1 [{', '.join(f'({a}, {b})' for a, b in T['pow2'].items())}]; "
        f"let chi2 := T2 [{', '.join(f'({a}, ({d}), {b})' for a, d, b in T['chi2'])}]; "
        f"let FS : List (Int × UInt64) := [{', '.join(f'({a}, {b})' for a, b in T['fsum'].items())}]; "
        f"let fsum := fun (v : List Float) => (match FS.find? (fun (t : Int × UInt64) => t.1 == VW v) with "
        f"| some t => Float.ofBits t.2 | none => Float.ofBits {SENT} : Float); "
    )


# ------------------------------------------------------------------ the stopped runs (real train.run)
REMOVED = ["risk_scores_train.csv", "risk_scores_validation.csv", "final_model_output.csv", "model_summary.csv",
           "model_coefficients.csv"]
KEPT = ["stepwise_summary.csv", "printed_roc_train.csv", "model.json"]


def stop_runs(ind: Path) -> list[int]:
    """The real train.run with a feature file absent: 1 when it raised the ValueError of :42, called
    write_sas_csv never, removed the five listed files planted in output_dir and left the others."""
    import contextlib
    import io
    import shutil

    out = []
    for absent in (["model_features_train.csv"], ["model_features_validation.csv"],
                   ["model_features_train.csv", "model_features_validation.csv"]):
        with tempfile.TemporaryDirectory() as td:
            i2, o2 = Path(td) / "in", Path(td) / "out"
            i2.mkdir()
            o2.mkdir()
            for n in ("model_features_train.csv", "model_features_validation.csv"):
                if n not in absent:
                    shutil.copy(ind / n, i2 / n)
            for n in REMOVED + KEPT:
                (o2 / n).write_text("earlier run\n")
            writes = []
            o_write = sc.write_sas_csv
            sc.write_sas_csv = lambda df, path, formats=None: writes.append(path)
            raised = False
            try:
                with contextlib.redirect_stdout(io.StringIO()) as buf:
                    train.run(i2, o2)
            except ValueError as e:
                raised = str(e) == "Model training stopped. Nothing is exported."
            finally:
                sc.write_sas_csv = o_write
            left = sorted(p.name for p in o2.iterdir())
            ok = raised and not writes and left == sorted(KEPT) and buf.getvalue().count("ERROR:") == 2
            print(f"[stop absent={absent}] raised={raised} writes={len(writes)} left={left}")
            out.append(1 if ok else 0)
    return out


# ------------------------------------------------------------------ the suite
def build(mask: int | None = None, smoke: bool = False):
    ind = sample_inputs()
    real = real_run(ind, encoded=False)
    rec = real_run(ind, encoded=True)
    n_fmt = check_real_against_encoded(real, rec)
    L, sw = rec["locals"], rec["stepwise"]
    (n1, mft), (n2, mfv) = rec["imports"]
    assert (n1, n2) == ("model_features_train.csv", "model_features_validation.csv")
    T = routine_tables(rec)
    if smoke:  # elaboration test: the same term on a few rows, one entry per table, one step
        mft, mfv = mft.head(6), mfv.head(4)
        T = {k: (dict(list(v.items())[:1]) if isinstance(v, dict) else v[:1]) for k, v in T.items()}
        T["einsum"] = [(a_, b_, out[:2]) for a_, b_, out in T["einsum"]]
        T["explog"] = T["explog"][:1]
        sw = sc.StepwiseResult(sw.steps[:1], sw.final, sw.intercept_only)
    today = L["model_summary"].get_column("training_date").to_list()[0]
    assert isinstance(today, dt.date)
    writes = dict(rec["writes"])
    order = [n for n, _ in rec["writes"]]
    assert len(writes) == len(order) == 18

    lets = (W + BI + OF + TS + TC + FD + TX + TD + FL + MW + FMT + DEC + KEYED + MKFIT + lean_routines(T)
            + f"let SW := {lean_stepwise(sw)}; "
            + f'let today : Tabular.Cell Float := Tabular.Cell.str (some "{today.isoformat()}"); '
            + f"let tT := {lean_table(mft)}; let tV := {lean_table(mfv)}; "
            + "let fT := Pl.ofTable tT; let fV := Pl.ofTable tV; ")
    # the steps, chained on the Lean results
    chain = (
        "let (cands, mask, ff, fin, io, nobs, ytr, m2ll0, ybar) := train_run_01_fit_frame (α := Float) SW fT; "
        "let o02 := train_run_02_stepwise_summary fw pv SW; "
        "let o03 := train_run_03_fit_global_rsquare fw d12 pv chi2 SW solve matmul matvec dot ff nobs ytr m2ll0 ybar; "
        "let (feff, fidx, icpt, coefs, lst, fsc) := train_run_04_score_train cands mask fin fT; "
        "let o05 := train_run_05_association fw d12 fsc; "
        "let (mcoef, o06) := train_run_06_coefficients_odds fw fo d8 pv chi2 pow2 fin feff fidx icpt; "
        "let o07 := train_run_07_hl fw pv chi2 pow2 fsc; "
        "let o08 := train_run_08_ctable fw inv matmul matvec einsum log1p mask ff fin nobs ytr lst; "
        "let (lst2, cmt, tm) := train_run_09_confusion_train lst; "
        "let lsv := train_run_10_score_valid icpt coefs fV; "
        "let (cmv, vm) := train_run_11_confusion_valid lsv; "
        "let (rst, rsv) := train_run_12_risk_scores lst2 lsv; "
        "let (roct, rocv) := train_run_13_roc fsum rst rsv; "
        "let o14 := train_run_14_final_and_summary today mcoef tm vm rst rsv roct rocv; "
        "let o15 := train_run_15_printed_roc d8 cmt cmv roct rocv; "
        "let RUN := run_py_py_py fw fo d8 d12 pv chi2 today SW fsum inv solve matmul matvec dot einsum log1p pow2; "
        "let R := (RUN (some tT) (some tV)).getD ([], (Float.ofBits 0, [])); "
    )
    CO = "W (coefs.flatMap (fun (p : String × Float) => ts p.1 ++ [bi p.2]))"
    parts: list[tuple[str, str, list[str], list[int]]] = []  # (unit, Lean term : List Int, labels, expected)

    def add(unit, term, labels, exp):
        assert len(labels) == len(exp), (unit, term)
        parts.append((unit, term, labels, [int(x) for x in exp]))

    if smoke:
        add("smoke", "FD fT", labels_fd("fT", mft), fd(mft))
        add("smoke", "FD fV", labels_fd("fV", mfv), fd(mfv))
    n_smoke = len(parts)
    u = "train_run_01_fit_frame"
    add(u, "[W (cands.flatMap ts), W (mask.map (fun (b : Bool) => if b then 1 else 0))]", ["candidates", "fit_mask"],
        [w([t for c in L["candidates"] for t in ts(c)]), w([int(b) for b in L["fit_mask"]])])
    add(u, "FD ff", labels_fd("fit_frame", L["fit_frame"]), fd(L["fit_frame"]))
    add(u, "[W (fin.names.flatMap ts), bi io.loglik, nobs, W (ytr.map bi), bi m2ll0, bi ybar]",
        ["final.names", "intercept_only.loglik", "n_obs", "y_train", "m2ll0", "ybar"],
        [w([t for c in L["final"].names for t in ts(c)]), fb(L["intercept_only"].loglik), L["n_obs"],
         w([fb(v) for v in L["y_train"]]), fb(L["m2ll0"]), fb(L["ybar"])])
    add("train_run_02_stepwise_summary", "TDN o02", labels_tdn(order[0], writes[order[0]]), tdn(order[0], writes[order[0]]))
    for k in (1, 2, 3):
        add("train_run_03_fit_global_rsquare", f"TDN (o03.getD {k - 1} (\"\", []))", labels_tdn(order[k], writes[order[k]]),
            tdn(order[k], writes[order[k]]))
    u = "train_run_04_score_train"
    add(u, f"[W (feff.flatMap ts), W fidx, bi icpt, {CO}]", ["final_effects", "final_index", "intercept", "coefficients"],
        [w([t for c in L["final_effects"] for t in ts(c)]), w(L["final_index"]), fb(L["intercept"]),
         w([t for c, b in L["coefficients"].items() for t in ts(c) + [fb(b)]])])
    lst_py = L["logit_scored_train"].drop("pred_logistic")
    add(u, "FD lst", labels_fd("logit_scored_train", lst_py), fd(lst_py))
    add(u, "FD fsc", labels_fd("fit_scored", L["fit_scored"]), fd(L["fit_scored"]))
    add("train_run_05_association", "TDN o05", labels_tdn(order[4], writes[order[4]]), tdn(order[4], writes[order[4]]))
    add("train_run_06_coefficients_odds", "FD mcoef", labels_fd("model_coefficients", L["model_coefficients"]), fd(L["model_coefficients"]))
    add("train_run_06_coefficients_odds", "TDN o06", labels_tdn(order[5], writes[order[5]]), tdn(order[5], writes[order[5]]))
    for k in (6, 7):
        add("train_run_07_hl", f"TDN (o07.getD {k - 6} (\"\", []))", labels_tdn(order[k], writes[order[k]]), tdn(order[k], writes[order[k]]))
    add("train_run_08_ctable", "TDN o08", labels_tdn(order[8], writes[order[8]]), tdn(order[8], writes[order[8]]))
    u = "train_run_09_confusion_train"
    add(u, "FD lst2", labels_fd("logit_scored_train+pred", L["logit_scored_train"]), fd(L["logit_scored_train"]))
    add(u, "FD cmt", labels_fd("confusion_matrix_train", L["confusion_matrix_train"]), fd(L["confusion_matrix_train"]))
    add(u, "FD tm", labels_fd("training_metrics", L["training_metrics"]), fd(L["training_metrics"]))
    add("train_run_10_score_valid", "FD lsv", labels_fd("logit_scored_valid", L["logit_scored_valid"]), fd(L["logit_scored_valid"]))
    u = "train_run_11_confusion_valid"
    add(u, "FD cmv", labels_fd("confusion_matrix", L["confusion_matrix"]), fd(L["confusion_matrix"]))
    add(u, "FD vm", labels_fd("validation_metrics", L["validation_metrics"]), fd(L["validation_metrics"]))
    u = "train_run_12_risk_scores"
    add(u, "FD rst", labels_fd("risk_scores_train", L["risk_scores_train"]), fd(L["risk_scores_train"]))
    add(u, "FD rsv", labels_fd("risk_scores_validation", L["risk_scores_validation"]), fd(L["risk_scores_validation"]))
    u = "train_run_13_roc"
    add(u, "FD roct", labels_fd("roc_train", L["roc_train"]), fd(L["roc_train"]))
    add(u, "FD rocv", labels_fd("roc_valid", L["roc_valid"]), fd(L["roc_valid"]))
    for k in range(9, 14):
        add("train_run_14_final_and_summary", f"TDN (o14.getD {k - 9} (\"\", []))", labels_tdn(order[k], writes[order[k]]),
            tdn(order[k], writes[order[k]]))
    for k in range(14, 18):
        add("train_run_15_printed_roc", f"TDN (o15.getD {k - 14} (\"\", []))", labels_tdn(order[k], writes[order[k]]),
            tdn(order[k], writes[order[k]]))
    # the whole run
    u = "run_py_py_py"
    stops = stop_runs(ind)
    add(u, "[(if (RUN (some tT) (some tV)).isSome then 1 else 0), (if (RUN none (some tV)).isNone then 1 else 0), "
           "(if (RUN (some tT) none).isNone then 1 else 0), (if (RUN none none).isNone then 1 else 0)]",
        ["completed run is some", "stop: train file absent", "stop: validation file absent", "stop: both absent"], [1] + stops)
    add(u, "[(R.1.length : Int)]", ["number of files"], [18])
    for k, n in enumerate(order):
        add(u, f"TDN (R.1.getD {k} (\"\", []))", ["run: " + s for s in labels_tdn(n, writes[n])], tdn(n, writes[n]))
    mj = rec["model_json"]
    add(u, "[bi R.2.1, W (R.2.2.flatMap (fun (p : String × Float) => ts p.1 ++ [bi p.2]))]",
        ["model.json intercept", "model.json coefficients (names, order, values)"],
        [fb(mj["intercept"]), w([t for c, b in mj["coefficients"].items() for t in ts(c) + [fb(b)]])])
    # StepwiseStep / StepwiseResult: the literal structure read back field by field
    add("StepwiseResult",
        "[(SW.steps.length : Int), (match SW.final with | some f => W (f.names.flatMap ts) | none => -1), "
        "(match SW.intercept_only with | some f => bi f.loglik | none => -1)]",
        ["steps", "final.names", "intercept_only.loglik"],
        [len(sw.steps), w([t for c in sw.final.names for t in ts(c)]), fb(sw.intercept_only.loglik)])
    add("StepwiseStep",
        "SW.steps.map (fun (s : StepwiseStep Float) => W ([s.step] ++ (match s.entered with | none => [0] | some e => 1 :: ts e) ++ "
        "(match s.removed with | none => [0] | some e => 1 :: ts e) ++ [s.df, s.number_in_model] ++ o s.score_chisq ++ o s.wald_chisq ++ "
        "[bi s.p_value, bi s.fit.loglik, s.fit.n_iter, if s.fit.converged then 1 else 0] ++ s.fit.names.flatMap ts ++ "
        "(match s.fit.beta with | .d1 v => 1 :: v.map bi | .d2 _ => [2]) ++ "
        "(match s.fit.cov with | .d1 _ => [1] | .d2 r => 2 :: r.flatMap (fun (q : List Float) => q.map bi))))",
        [f"step {s.step}" for s in sw.steps],
        [w([s.step] + ([0] if s.entered is None else [1] + ts(s.entered)) + ([0] if s.removed is None else [1] + ts(s.removed))
           + [s.df, s.number_in_model] + o(s.score_chisq) + o(s.wald_chisq)
           + [fb(s.p_value), fb(s.fit.loglik), int(s.fit.n_iter), int(s.fit.converged)] + [t for c in s.fit.names for t in ts(c)]
           + [1] + [fb(v) for v in s.fit.beta] + [2] + [fb(v) for r in s.fit.cov for v in r]) for s in sw.steps])

    # probes: Lean's Float.exp / Float.log against Python's math.exp / math.log on the arguments of the run
    for lab, fn, x, r in T["explog"]:
        unit = "train_run_06_coefficients_odds" if "idx" in lab else "train_run_03_fit_global_rsquare"
        add(unit, f"[bi (Float.{fn} (Float.ofBits {fb(x)}))]", [f"probe Float.{fn} vs math.{fn}: {lab}"], [fb(r)])

    labels = [lab for _, _, ls, _ in parts for lab in ls]
    if mask is not None:
        for k, lab in enumerate(labels):
            if (mask >> k) & 1:
                print(k, lab)
        return None
    allexp = [e for _, _, _, exp in parts for e in exp]
    body = ("(let P : List (List Int) := [" + ", ".join(p[1] for p in parts) + "]; let ALL := P.flatten.toArray; "
            + 'let EXP : Array Int := ("' + "".join(chr(97 + e % SHORT) for e in allexp)
            + '".toList.map (fun (c : Char) => ((c.toNat : Int) - 97))).toArray; '
            + f"let mask := (List.range (max ALL.size EXP.size)).foldl (fun (m : Int) (i : Nat) => if ALL.getD i 0 % {SHORT} == EXP.getD i (-1) "
            + "then m else m + (2 : Int) ^ i) 0; P.map W ++ [mask, (ALL.size : Int)])")
    cases = [(f"{p[2][0]} .. {p[2][-1]}" if len(p[2]) > 1 else p[2][0], p[0], w(p[3]), {"covers": len(p[3])}) for p in parts]
    cases.append(("localisation mask (bit i: value i differs modulo %d)" % SHORT, "run_py_py_py", 0))
    cases.append(("number of compared values", "run_py_py_py", len(allexp)))
    if smoke:  # only the decoded input tables are compared; the rest must elaborate and run
        body = body[:body.rindex("P.map W")] + f"(P.take {n_smoke}).map W ++ [(ALL.size : Int)])"
        cases = cases[:n_smoke] + [("number of values (the chain ran)", "smoke", -1)]
    s = Suite("t18_smoke" if smoke else "t18_run")
    s.item, s.decl = "def:zz_carrier_t", "zz_carrier_t"
    s.ints(lets + chain, body, cases, use_kit=False)
    info = (f"real train.run on {mft.height} training rows / {mfv.height} validation rows sampled from the real feature files "
            f"(planted nulls: train {NULLS_TRAIN}, validation {NULLS_VALID}); fit frame {L['n_obs']} rows; stepwise "
            f"{[(st.step, st.entered, st.removed) for st in sw.steps]}, final {sw.final.names}")
    common = ("formatters = the same injective encoding of their arguments on both sides (the run with the real formatters agrees "
              f"cell by cell: {n_fmt} formatted cells checked in Python); chi2 / pow2 / log1p = tables of the real values; "
              "solve / matmul / matvec / dot / inv / einsum_q = numpy's results keyed on the digest of the arguments; ")
    s.notes = {
        "run_py_py_py": info + "; " + common + "18 tables compared column by column (names, order, cells as bits / strings) and "
                        "model.json (intercept, coefficients in dict order); today = Cell.str of the run's ISO date",
        "train_run_01_fit_frame": "steps chained inside Lean on the Lean results of the earlier steps, each compared with the locals of the real run",
        "train_run_07_hl": "hosmer_lemeshow's Int64 observed counts reach fmt_wd as Python ints; the encoding takes float(v) (R-F2I, TODO(port) of the unit)",
        "train_run_08_ctable": "classification_table's Int64 counts reach fmt_wd as Python ints; the encoding takes float(v) (R-F2I, TODO(port) of the unit)",
        "StepwiseResult": "the real stepwise_logistic result as a literal structure, read back",
        "StepwiseStep": "every field of every step of the real result, read back",
    }
    s.write()
    return rec


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--mask":
        build(mask=int(sys.argv[2]))
    elif len(sys.argv) > 1 and sys.argv[1] == "--smoke":
        build(smoke=True)
    else:
        build()
