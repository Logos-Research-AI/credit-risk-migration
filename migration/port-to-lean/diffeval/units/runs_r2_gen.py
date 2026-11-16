"""Reviewer 2 of the three `run` units: END-TO-END differential tests on real data.

  uv run python migration/diffeval/units/runs_r2_gen.py [fe] [pred] [met]
      -> work/runs_r2_fe, runs_r2_pred, runs_r2_met (.json + .inputs.json), work/runs_r2_stats.json
  (eval_decl each input of work/runs_r2_<suite>.inputs.json on def:zz_carrier / zz_carrier, save the
   outputs one per line as work/runs_r2_<suite>.out.txt)
  uv run python migration/diffeval/compare.py migration/diffeval/work/runs_r2_<suite>.json migration/diffeval/work/runs_r2_<suite>.out.txt
  uv run python migration/diffeval/receipts.py units runs_r2
  uv run python migration/diffeval/units/runs_r2_gen.py explain   (accounts for the exp last-bit difference)

Only the whole `run` functions are evaluated (def:run, def:run_py_py, def:run_py), on rows the
implementers did not use. Python side: the REAL run is called on a temporary directory;
`sas_compat.write_sas_csv` is replaced by a recorder (the frames, in call order, are the expected
output tables); a profile hook copies the locals of `run` at return (only to read the imported
frame and the frame after input_best32, and for the statistics of the report).

  feature_engineering.run  three disjoint samples of data/cs-training.csv, rows > 50000 (the
      implementer used rows 1-20, 2551-2778 and four long incomes below 7200), with
      inputs/split_ids.csv restricted to the sample (file order kept):
        mid       150 seeded random rows of 50001..100000 + edge rows of that range
        end       150 seeded random rows of 100001..150000 + edge rows of that range
        extremes  edge rows only (not in the two others); fix_income_truncation=True
      edge rows: age < 22, age > 100, utilization > 10, DebtRatio > 5000, 90-days-late >= 90,
      dependents >= 8, income 0, income >= 100000 (cut by the default import).
      4 runs each: full x export_train_medians.
  predict.run  model.json = the REAL model: feature_engineering.run on the full data
      (export_train_medians=True) then train.run, computed once into work/runs_r2_pipe/;
      income_medians.csv of that run, read as predict.py reads it.
        test_last   the last 200 data lines of data/cs-test.csv
        test_rand   200 seeded random lines of data/cs-test.csv (none used by b8_gen.pick)
        edge_mix    edge_predict/cs-test.csv: the last 100 lines + 100 seeded random lines, 60 of
                    them among the lines that differ from data/cs-test.csv
      4 runs each: (fix_train_medians false | true with the real medians) x full.
  metrics_calculation.run  fix_psi_bins false and true:
        edge_metrics_a|b|c  last 300 validation / last 700 training rows; seeded random 300 / 700
                            rows of the middle (the implementer used the first 300 / 700)
        real_wide    the last 20 / 30 lines of the REAL risk_scores_validation / _train files, all
                     51 columns (text columns included)
        real_narrow  150 / 350 seeded random lines of the REAL files, columns row_id,
                     default_flag, pd_logistic

Lean side: every table is built inside Lean from one string literal (rows separated by ';',
cells by ','; a numeric cell is the shortest decimal text of the float, parsed with
Float.ofScientific, or '#<bits>' when the decimal is within 2^-9 ulp of a rounding boundary; the
scenario tables are 4 digits per row, 2 * (pd * 1000) + flag). The first digests of every input
compare the tables with what Python imported, so the inputs are the same bit for bit.
`input_best32` is the test double IB of b7_gen (String: null / "NA" -> null, digits -> value;
Float64: identity, non-finite -> null), checked in every input against the real function: the
digest of `<stage>_run_01_clean IB (Pl.ofTable T)` is compared with the local of the real run.
`sas_best` / `parse_float` / `sas_d8` are lookups in the tables of the (argument, text) pairs the
real functions produced during the run; `today` is the String cell of the run's date.
"""
from __future__ import annotations

# RETIRED 2026-11-16: this script is a record of the port before the update of 2026-11-16 and no longer
# runs as a script (its helper functions are still imported by later generators): it calls export_train_medians, fix_income_truncation, fix_train_medians, medians, fix_psi_bins; see t6_gen.py, t11_gen.py, t16_gen.py, t18_gen.py.
# Its recorded outputs describe the port as it was then.
import sys as _sys

if __name__ == "__main__":  # retired as a script; its helpers may still be imported
    _sys.exit("RETIRED 2026-11-16: " + __file__ + " calls keywords the port no longer has; see the note at its top")


import contextlib
import io
import json
import math
import random
import sys
import tempfile
from decimal import Decimal
from fractions import Fraction
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(ROOT))

import compare as cmp  # noqa: E402
import leanterm as lt  # noqa: E402
from suite import WORK, Suite  # noqa: E402

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import metrics_calculation as mc  # noqa: E402
from credit_risk import predict as pr  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train  # noqa: E402

SEED = 20261110
PIPE = WORK / "runs_r2_pipe"
STATS: dict = {}


# ---------------------------------------------------------------- tables as one string literal
def _safe(text: str, v: float) -> bool:
    """True when the decimal `text` is not within 2^-9 ulp of the midpoint of two doubles (any
    conversion that keeps 64 bits before rounding then gives float(text))."""
    x = Fraction(Decimal(text))
    if Fraction(v) == x:
        return True
    lo, hi = (v, math.nextafter(v, math.inf)) if Fraction(v) < x else (math.nextafter(v, -math.inf), v)
    mid = (Fraction(lo) + Fraction(hi)) / 2
    return abs(x - mid) / (Fraction(hi) - Fraction(lo)) > Fraction(1, 512)


def num_text(v: float | None) -> str:
    if v is None:
        return ""
    assert v == v and 0 <= v < math.inf and cmp.fbits(v) != cmp.fbits(-0.0), v
    s = format(Decimal(repr(v)), "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    assert cmp.fbits(float(s)) == cmp.fbits(v), (s, v)
    return s if _safe(s, v) else f"#{cmp.fbits(v)}"


PARSE = (
    'let pn := fun (s : String) => (let q := s.splitOn "#"; if q.length == 2 then Float.ofBits ((q.getD 1 "").toNat?.getD 0).toUInt64 '
    'else (let p := s.splitOn "."; let b := p.getD 1 ""; Float.ofScientific ((p.getD 0 "" ++ b).toNat?.getD 0) true b.length)); '
    'let mkT := fun (names : List String) (kinds : List Nat) (d : String) => (((d.splitOn ";").map (fun (r : String) => '
    'let c := (r.splitOn ",").toArray; (List.range names.length).map (fun (j : Nat) => let s := c.getD j ""; '
    '(names.getD j "", (if kinds.getD j 0 == 0 then Tabular.Cell.num (if s == "" then none else some (pn s)) '
    'else Tabular.Cell.str (if s == "" then none else some s) : Tabular.Cell Float))))) : Tabular.Table Float); '
)
# the test double of sas_compat.input_best32 (b7_gen), checked by the `..._run_01_clean` case
IB = (
    "let IB := fun (e : Pl.Expr Float) => ({ e with eval := fun (g : Option (List (List Nat))) (fr : Pl.Frame Float) => "
    '(match e.eval g fr with | .str v => Pl.Col.f64 (v.map (fun (o : Option String) => (match o with | some s => (if s == "NA" then none else s.toNat?.map Float.ofNat) | none => none))) '
    "| c => Pl.Col.f64 (c.asF64.map (fun (o : Option Float) => o.bind (fun (x : Float) => if x.isFinite then some x else none)))) } : Pl.Expr Float); "
)
# scenario tables: w gap digits (w = 0: every gap is 1) + 4 code digits per row; the row id is
# base + the running sum of the gaps
MK3 = (
    "let cell := fun (o : Option Float) => (Tabular.Cell.num o : Tabular.Cell Float); "
    "let dn := fun (A : Array Nat) (o w : Nat) => (List.range w).foldl (fun (acc j : Nat) => acc * 10 + A.getD (o + j) 0) 0; "
    "let mk3 := fun (base w : Nat) (s : String) => (let A := (s.toList.map (fun (c : Char) => c.toNat - 48)).toArray; "
    "(((List.range (A.size / (w + 4))).foldl (fun (acc : Nat × List (Tabular.Row Float)) (i : Nat) => let o := i * (w + 4); "
    "let ix := acc.1 + (if w == 0 then 1 else dn A o w); let m := dn A (o + w) 4; "
    '(ix, [("row_id", cell (some (Float.ofNat (base + ix)))), ("default_flag", cell (some (Float.ofNat (m % 2)))), '
    '("pd_logistic", cell (some (Float.ofScientific (m / 2) true 3)))] :: acc.2)) (0, [])).2.reverse : Tabular.Table Float)); '
)

def lean_table(df: pl.DataFrame) -> str:
    """`mkT names kinds "rows"` for a frame of Float64 / String columns."""
    kinds = []
    for n in df.columns:
        assert df.schema[n] in (pl.Float64, pl.String), (n, df.schema[n])
        kinds.append(1 if df.schema[n] == pl.String else 0)
    rows = []
    for r in df.iter_rows():
        cells = []
        for k, v in zip(kinds, r, strict=True):
            if k:
                assert v is None or (v != "" and not any(ch in v for ch in ',;#"\\')), v
                cells.append("" if v is None else v)
            else:
                cells.append(num_text(v))
        rows.append(",".join(cells))
    return (f"(mkT [{', '.join(lt.lean_str(n) for n in df.columns)}] [{', '.join(map(str, kinds))}] "
            f"{lt.lean_str(';'.join(rows))})")


def lean_mk3(df: pl.DataFrame, base: int, idx: list[int] | None) -> str:
    """`mk3 (base + first index - 1) w "digits"`: row_id = base + index, default_flag 0/1, pd_logistic = k / 1000.
    idx None: consecutive rows (no gap digits); else the 0-based indices, sent as 2-digit gaps."""
    assert df.columns == ["row_id", "default_flag", "pd_logistic"] and all(t == pl.Float64 for t in df.dtypes)
    out = []
    start = 0 if idx is None else idx[0]
    prev = start - 1
    for i, (r, f, p) in enumerate(df.iter_rows()):
        ix = i if idx is None else idx[i]
        assert r == base + ix and f in (0.0, 1.0) and 0 < ix - prev < 100
        k = round(p * 1000)
        assert cmp.fbits(float(f"{k}e-3")) == cmp.fbits(p) and _safe(f"{k}e-3", p) and k * 2 + 1 < 10000, p
        out.append(("" if idx is None else f"{ix - prev:02d}") + f"{k * 2 + int(f):04d}")
        prev = ix
    return f'(mk3 {base + start - 1} {0 if idx is None else 2} "{"".join(out)}")'


def dgf(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_frame(df)))


def dgt(name: str, df: pl.DataFrame) -> int:
    df = df.with_columns([pl.col(n).cast(pl.String) for n in df.columns if df.schema[n] == pl.Date])
    return cmp.digest(cmp.tok_str(name) + cmp.tokens(cmp.canon_table(df)))


def dgtab(df: pl.DataFrame) -> int:
    return cmp.digest(cmp.tokens(cmp.canon_table(df)))


def instrumented(code, call) -> dict:
    """Run `call()` with write_sas_csv recorded and the locals of the function `code` captured."""
    rec: dict = {"files": [], "locals": None}
    o_write = sc.write_sas_csv

    def prof(frame, event, arg):
        if event == "return" and frame.f_code is code:
            rec["locals"] = dict(frame.f_locals)

    sc.write_sas_csv = lambda df, path, formats=None: rec["files"].append((Path(path).name, df))
    sys.setprofile(prof)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            call()
    finally:
        sys.setprofile(None)
        sc.write_sas_csv = o_write
    return rec


def nonfinite(df: pl.DataFrame) -> int:
    return sum(int((~df.get_column(n).is_finite()).sum() or 0) for n in df.columns if df.schema[n] == pl.Float64)


# ---------------------------------------------------------------- the real pipeline (once)
def pipeline() -> Path:
    if not (PIPE / "model.json").exists():
        with contextlib.redirect_stdout(io.StringIO()):
            fe.run(ROOT / "data", PIPE, split_ids=ROOT / "inputs" / "split_ids.csv", export_train_medians=True)
            train.run(PIPE, PIPE)
    return PIPE


# ---------------------------------------------------------------- feature_engineering.run
def fe_samples() -> dict[str, list[int]]:
    t = pl.read_csv(ROOT / "data" / "cs-training.csv", infer_schema=False).with_row_index("i", offset=1)
    f = lambda c: pl.col(c).cast(pl.Float64, strict=False)  # noqa: E731
    crit = {
        "age<22": f("age") < 22, "age>100": f("age") > 100, "util>10": f("RevolvingUtilizationOfUnsecuredLines") > 10,
        "debt>5000": f("DebtRatio") > 5000, "late90>=90": f("NumberOfTimes90DaysLate") >= 90,
        "deps>=8": f("NumberOfDependents") >= 8, "income0": pl.col("MonthlyIncome") == "0",
        "income>=100000": pl.col("MonthlyIncome").str.len_chars() >= 6,
    }
    rows = {k: t.filter(c & (pl.col("i") > 50000)).get_column("i").to_list() for k, c in crit.items()}
    STATS["fe_edge_rows_above_50000"] = {k: len(v) for k, v in rows.items()}
    rng = random.Random(SEED)
    out: dict[str, list[int]] = {}
    used: set[int] = set()
    for name, lo, hi in (("mid", 50001, 100000), ("end", 100001, 150000)):
        chosen = set(rng.sample(range(lo, hi + 1), 150))
        for k, v in rows.items():
            inr = [r for r in v if lo <= r <= hi]
            chosen |= set(inr if k in ("age>100", "deps>=8") else rng.sample(inr, min(len(inr), 6)))
        if name == "end":
            chosen.add(150000)
        out[name] = sorted(chosen)
        used |= chosen
    chosen = set()
    for k, v in rows.items():
        free = [r for r in v if r not in used]
        chosen |= set(rng.sample(free, min(len(free), 28)))
    out["extremes"] = sorted(chosen)
    assert not (set(out["mid"]) & set(out["end"])) and not (set(out["extremes"]) & used)
    STATS["fe_edge_rows_in_samples"] = {
        n: {k: len(set(v) & set(r)) for k, v in rows.items()} for n, r in out.items()}
    return out


def suite_fe() -> Suite:
    s = Suite("runs_r2_fe")
    lines = (ROOT / "data" / "cs-training.csv").read_text().splitlines(keepends=True)
    ids = pl.read_csv(ROOT / "inputs" / "split_ids.csv", infer_schema=False).get_column("row_id").cast(pl.Int64).to_list()
    for name, rows in fe_samples().items():
        fix = name == "extremes"
        keep = set(rows)
        split = [i for i in ids if i in keep]
        runs = {}
        with tempfile.TemporaryDirectory() as d:
            ind = Path(d) / "in"
            ind.mkdir()
            (ind / "cs-training.csv").write_text(lines[0] + "".join(lines[r] for r in rows))  # line r has row id r
            (ind / "split.csv").write_text("row_id\n" + "".join(f"{i}\n" for i in split))
            for ex in (False, True):
                runs[ex] = instrumented(fe.run.__code__, lambda ex=ex: fe.run(
                    ind, Path(d) / "out", split_ids=ind / "split.csv", fix_income_truncation=fix, export_train_medians=ex))
        L = runs[False]["locals"]
        raw = L["credit_raw"]
        assert [f for f, _ in runs[False]["files"]] == ["model_features_train.csv", "model_features_validation.csv"]
        assert [f for f, _ in runs[True]["files"]] == ["income_medians.csv", "model_features_train.csv", "model_features_validation.csv"]
        assert L["train_ids"].to_list() == [float(i) for i in split]
        lets = (PARSE + IB + f"let T := {lean_table(raw)}; "
                + 'let S : Tabular.Table Float := ("' + ",".join(map(str, split)) + '".splitOn ",").map (fun (x : String) => '
                + '[("row_id", (Tabular.Cell.num (some (Float.ofNat (x.toNat?.getD 0))) : Tabular.Cell Float))]); ')
        body = (f"let rr := fun (full ex : Bool) => (run full IB T S {lt.lean_bool(fix)} ex).map "
                "(fun (p : String × Tabular.Table Float) => dg (tS p.1 ++ tA p.2)); "
                "[dg (tA T), dg (tA S), dg (tR (fe_run_01_clean IB (Pl.ofTable T)))] "
                "++ rr true false ++ rr false false ++ rr true true ++ rr false true")
        c = lambda cid, val: (f"{name}: {cid}", "run", val)  # noqa: E731
        cases = [c("input table cs_training (the imported frame)", dgtab(raw)),
                 c("input table split_ids", dgtab(pl.DataFrame({"row_id": L["train_ids"]}))),
                 c("check of the input_best32 double: fe_run_01_clean IB = credit_raw_clean", dgf(L["credit_raw_clean"]))]
        for ex in (False, True):
            for full in (True, False):
                cases += [c(f"{f} full={full} export_train_medians={ex} fix_income_truncation={fix}", dgt(f, df))
                          for f, df in runs[ex]["files"]]
        s.ints(lets, body, cases, table=True)
        cf = L["credit_features"]
        STATS[f"fe:{name}"] = {
            "rows": raw.height, "first_row": rows[0], "last_row": rows[-1], "split_ids": len(split),
            "MonthlyIncome": str(raw.schema["MonthlyIncome"]), "NumberOfDependents": str(raw.schema["NumberOfDependents"]),
            "medians": L["income_medians"].sort("age_group").rows(), "train": L["credit_train"].height,
            "validation": L["credit_validation"].height,
            "null_monthly_income": cf["monthly_income"].null_count(),
            "income_NA": int(cf["MonthlyIncome_missing"].sum()), "dependents_NA": int(cf["Dependents_missing"].sum()),
            "num_dependents_eq_-1 (zero divisor, outside the precondition)": int((cf["num_dependents"] == -1).sum()),
            "nonfinite_feature_values": nonfinite(cf),
            "incomes_cut_by_import": sum(
                1 for r, v in zip(rows, raw.get_column("MonthlyIncome").to_list(), strict=True)
                if isinstance(v, str) and v != lines[r].rstrip("\n").split(",")[6]),
            "age_min_max": [cf["age"].min(), cf["age"].max()],
            "financial_health_values": sorted(set(cf["financial_health"].to_list())),
            "total_risk_flags_values": sorted(set(cf["total_risk_flags"].to_list())),
        }
    s.notes = {"run": "reviewer 2 real-data samples"}
    return s


# ---------------------------------------------------------------- predict.run
# exp last-bit differences between polars (Apple libm on the machine that ran the Python) and the
# Lean runtime of eval_decl, found by `explain`: sample -> (bits polars returns, bits Lean returns, note)
KNOWN_ULP = {
    "test_rand": (4630238058052490439, 4630238058052490438,
                  "exp last bit only: row 34475, exp(3.5785111395443048) is bits 4630238058052490439 in polars / Python "
                  "(0.50026 ulp from the exact value) and ...438 in Lean's runtime (the correctly rounded value), so pd_logistic "
                  "is 0.027159027319719514 in Python and 0.027159027319719517 in Lean (1 ulp, that row only); with that one "
                  "exp value replaced the real predict.run gives the digests Lean returned (runs_r2_gen.py explain)"),
}


def explain():
    """For each sample of KNOWN_ULP: (1) rank the exp / log arguments of the real run by the distance of
    polars' result from the exact value (the candidates for a last-bit difference; their Lean values are
    asked with one small eval_decl: `Float.exp (Float.ofBits b)`); (2) rerun the real predict.run with
    the one exp value replaced by Lean's and compare the digests with those Lean returned."""
    from decimal import getcontext

    getcontext().prec = 60
    pipe = pipeline()
    model_text, med_text = (pipe / "model.json").read_text(), (pipe / "income_medians.csv").read_text()
    samples = pred_samples()
    outs = [cmp.parse_lean(ln) for ln in (WORK / "runs_r2_pred.out.txt").read_text().splitlines() if ln.strip()]
    for k, name in enumerate(samples):
        if name not in KNOWN_ULP:
            continue
        py_bits, lean_bits, _ = KNOWN_ULP[name]
        path, rows = samples[name]
        lines = path.read_text().splitlines(keepends=True)
        orig = sc.sas_exp

        def patched(x):
            e = orig(x)
            return pl.when(e == lt.from_bits(py_bits)).then(pl.lit(lt.from_bits(lean_bits))).otherwise(e)

        for j, fx in enumerate((False, True)):
            res = {}
            for patch in (False, True):
                sc.sas_exp = patched if patch else orig
                try:
                    with tempfile.TemporaryDirectory() as d:
                        dd, ind = Path(d) / "data", Path(d) / "in"
                        dd.mkdir()
                        ind.mkdir()
                        (dd / "cs-test.csv").write_text(lines[0] + "".join(lines[r] for r in rows))
                        (ind / "model.json").write_text(model_text)
                        (ind / "income_medians.csv").write_text(med_text)
                        res[patch] = instrumented(pr.run.__code__, lambda: pr.run(
                            ind, Path(d) / "out", data_dir=dd, fix_train_medians=fx,
                            medians=(ind / "income_medians.csv") if fx else None))
                finally:
                    sc.sas_exp = orig
            ts = res[False]["locals"]["test_scored_temp"]
            sus = []
            for i, (x, m) in enumerate(zip(ts["predicted_logit"].to_list(), ts["monthly_income"].to_list(), strict=True)):
                if x is not None:
                    e = math.exp(-x)
                    sus.append((abs(float((Decimal(-x).exp() - Decimal(e)) / Decimal(math.ulp(e)))), "exp", rows[i], cmp.fbits(-x), cmp.fbits(e)))
                if m is not None and m + 1 > 0:
                    v = math.log(m + 1)
                    sus.append((abs(float((Decimal(m + 1).ln() - Decimal(v)) / Decimal(math.ulp(v)))), "log", rows[i], cmp.fbits(m + 1), cmp.fbits(v)))
            sus.sort(reverse=True)
            lean = outs[k][2 + 4 * j:4 + 4 * j]
            got = [dgt(f, df) for f, df in res[True]["files"]]
            print(f"{name} fix_train_medians={fx}: Python digests {[dgt(f, df) for f, df in res[False]['files']]}; "
                  f"with exp bits {py_bits} -> {lean_bits}: {got}; Lean returned {lean}; equal: {got == lean}")
            print("   largest |polars - exact| in ulp (function, row id, argument bits, result bits):", sus[:4])
            for (f, a), (_, b) in zip(res[False]["files"], res[True]["files"], strict=True):
                for cn in a.columns:
                    dd_ = [(rows[i], u, v) for i, (u, v) in enumerate(zip(a[cn].to_list(), b[cn].to_list(), strict=True)) if u != v]
                    if dd_:
                        print(f"   {f}.{cn}: rows that change {dd_}")


def pred_samples() -> dict[str, tuple[Path, list[int]]]:
    import b8_gen

    real, edge = ROOT / "data" / "cs-test.csv", ROOT / "inputs" / "scenarios" / "edge_predict" / "cs-test.csv"
    a, b = real.read_text().splitlines(), edge.read_text().splitlines()
    n = len(a) - 1
    assert len(b) - 1 == n
    theirs = {p: {int(ln.split(",")[0]) for ln in b8_gen.pick(p, 120, 200).splitlines()[1:]} for p in (real, edge)}
    rng = random.Random(SEED + 1)
    last = list(range(n - 199, n + 1))
    rand = sorted(rng.sample([i for i in range(1000, n - 199) if i not in theirs[real]], 200))
    differ = [i for i in range(1000, n - 99) if a[i] != b[i] and i not in theirs[edge]]
    e1 = set(rng.sample(differ, 60))
    e2 = set(rng.sample([i for i in range(1000, n - 99) if i not in e1 and i not in theirs[edge]], 40))
    out = {"test_last": (real, last), "test_rand": (real, rand),
           "edge_mix": (edge, sorted(e1 | e2 | set(range(n - 99, n + 1))))}
    for k, (p, rows) in out.items():
        assert not (set(rows) & theirs[p]), k
    return out


def suite_pred() -> Suite:
    s = Suite("runs_r2_pred")
    pipe = pipeline()
    model_text = (pipe / "model.json").read_text()
    model = json.loads(model_text)
    med_text = (pipe / "income_medians.csv").read_text()
    co = "[" + ", ".join(f"({lt.lean_str(k)}, {lt.lean_float(float(v))})" for k, v in model["coefficients"].items()) + "]"
    STATS["model.json"] = model
    STATS["income_medians.csv"] = med_text
    for name, (path, rows) in pred_samples().items():
        lines = path.read_text().splitlines(keepends=True)
        runs = {}
        with tempfile.TemporaryDirectory() as d:
            dd, ind = Path(d) / "data", Path(d) / "in"
            dd.mkdir()
            ind.mkdir()
            (dd / "cs-test.csv").write_text(lines[0] + "".join(lines[r] for r in rows))
            (ind / "model.json").write_text(model_text)
            (ind / "income_medians.csv").write_text(med_text)
            med = pl.read_csv(ind / "income_medians.csv", schema_overrides={"age_group": pl.Int32, "median_income": pl.Float64})
            for fx in (False, True):
                runs[fx] = instrumented(pr.run.__code__, lambda fx=fx: pr.run(
                    ind, Path(d) / "out", data_dir=dd, fix_train_medians=fx, medians=(ind / "income_medians.csv") if fx else None))
        L = runs[False]["locals"]
        raw = L["test_raw"]
        assert cmp.canon_frame(med) == cmp.canon_frame(runs[True]["locals"]["test_income_medians"])
        assert dgf(L["test_raw_clean"]) == dgf(runs[True]["locals"]["test_raw_clean"])
        lets = (PARSE + IB + f"let T := {lean_table(raw)}; let CO : List (String × Float) := {co}; "
                f"let IC : Float := {lt.lean_float(float(model['intercept']))}; "
                f"let MED : Option (Pl.Frame Float) := some {lt.lean_frame(med)}; ")
        body = ("let rp := fun (fl : Bool) (m : Option (Pl.Frame Float)) (fx : Bool) => (run_py_py fl IB IC CO m T fx).map "
                "(fun (p : String × Tabular.Table Float) => dg (tS p.1 ++ tA p.2)); "
                "[dg (tA T), dg (tR (predict_run_01_clean IB (Pl.ofTable T)))] "
                "++ rp true none false ++ rp false none false ++ rp true MED true ++ rp false MED true")
        c = lambda cid, val: (f"{name}: {cid}", "run_py_py", val)  # noqa: E731
        cases = [c("input table cs_test (the imported frame)", dgtab(raw)),
                 c("check of the input_best32 double: predict_run_01_clean IB = test_raw_clean", dgf(L["test_raw_clean"]))]
        known = ({"expect_diff": True, "note": KNOWN_ULP[name][2]},) if name in KNOWN_ULP else ()
        for fx in (False, True):
            assert [f for f, _ in runs[fx]["files"]] == ["kaggle_submission.csv", "test_predictions.csv"]
            for full in (True, False):
                cases += [c(f"{f} full={full} fix_train_medians={fx}", dgt(f, df)) + known for f, df in runs[fx]["files"]]
        s.ints(lets, body, cases, table=True)
        st = {"rows": raw.height, "first_row": rows[0], "last_row": rows[-1],
              "MonthlyIncome": str(raw.schema["MonthlyIncome"]), "NumberOfDependents": str(raw.schema["NumberOfDependents"])}
        for fx in (False, True):
            Lx = runs[fx]["locals"]
            P = Lx["test_predictions"]
            st[f"fix_train_medians={fx}"] = {
                "medians": Lx["test_income_medians"].sort("age_group").rows(),
                "null_monthly_income": Lx["test_imputed"]["monthly_income"].null_count(),
                "null_pd": P["pd_logistic"].null_count(),
                "grades": dict(sorted(P.group_by("risk_grade").len().iter_rows())),
                "num_dependents_eq_-1 (zero divisor, outside the precondition)": int((Lx["test_imputed"]["num_dependents"] == -1).sum()),
                "nonfinite_feature_values": nonfinite(Lx["test_features"]),
                "pd_min_max": [P["pd_logistic"].min(), P["pd_logistic"].max()],
            }
        STATS[f"pred:{name}"] = st
    s.notes = {"run_py_py": "reviewer 2 real-data samples"}
    return s


# ---------------------------------------------------------------- metrics_calculation.run
def met_run(vtext: str, ttext: str, fix: bool, no_raise: bool = False) -> dict:
    """The real mc.run on a temp directory; sas_best / sas_d8 recorded."""
    best: dict = {}
    d8: dict = {}
    o_best, o_d8 = sc.sas_best, sc.sas_d8
    key = lambda x: None if x is None else cmp.fbits(float(x))  # noqa: E731

    def w_best(x, w):
        r = o_best(x, w)
        assert w == 8 and best.setdefault(key(x), r) == r
        return r

    def w_d8(x):
        r = o_d8(x)
        assert d8.setdefault(key(x), r) == r
        return r

    raised = None
    with tempfile.TemporaryDirectory() as d:
        ind = Path(d) / "in"
        ind.mkdir()
        (ind / "risk_scores_validation.csv").write_text(vtext)
        (ind / "risk_scores_train.csv").write_text(ttext)
        valid = sc.proc_import_csv(ind / "risk_scores_validation.csv", guessingrows=20)
        trainf = sc.proc_import_csv(ind / "risk_scores_train.csv", guessingrows=20)
        sc.sas_best, sc.sas_d8 = w_best, w_d8
        if no_raise:
            mc.abs = lambda x: 0.0  # disables the test of :276 only (b6_gen technique)
        try:
            rec = instrumented(mc.run.__code__, lambda: mc.run(ind, Path(d) / "out", fix_psi_bins=fix))
        except ValueError as e:
            raised, rec = str(e), {"files": [], "locals": None}
        finally:
            sc.sas_best, sc.sas_d8 = o_best, o_d8
            if no_raise:
                del mc.abs
    rec.update(valid=valid, train=trainf, best=best, d8=d8, raised=raised)
    return rec


FILES_M = ["validation_summary.csv", "decile_analysis.csv", "threshold_analysis.csv", "ks_statistic.csv",
           "calibration_plot.csv", "model_performance_metrics.csv", "printed_roc_metrics.csv",
           "printed_cumulative_lift.csv", "printed_psi_calculation.csv"]
RUNM = (
    "let runM := fun (V T : Tabular.Table Float) (SB : List (Option UInt64 × String)) (PF : List (String × UInt64)) "
    "(D8 : List (Option UInt64 × String)) => ("
    'let sb := fun (x : Option Float) (_ : Int) => (match SB.lookup (x.map Float.toBits) with | some s => s | none => "?"); '
    "let pf := fun (s : String) => Float.ofBits ((PF.lookup s).getD 1); "
    'let d8 := fun (x : Option Float) => (match D8.lookup (x.map Float.toBits) with | some s => s | none => "?"); '
    "let per := fun (fx : Bool) => (run_py sb pf d8 today V T fx).map (fun (p : String × Tabular.Table Float) => dg (tS p.1 ++ tA p.2)); "
    "([dg (tA V), dg (tA T)] ++ per false ++ per true : List Int)); "
)


def met_scenario(name: str, vtext: str, ttext: str, vterm, tterm) -> tuple[str, list, str]:
    runs, raised = {}, {}
    for fix in (False, True):
        r = met_run(vtext, ttext, fix)
        if r["raised"] is not None:
            raised[fix] = r["raised"]
            r = met_run(vtext, ttext, fix, no_raise=True)
            assert r["raised"] is None
        runs[fix] = r
    r0 = runs[False]
    best = {**runs[False]["best"], **runs[True]["best"]}
    d8 = {**runs[False]["d8"], **runs[True]["d8"]}
    k_ = lambda k: "none" if k is None else f"some {k}"  # noqa: E731
    sb = ", ".join(f"({k_(k)}, {lt.lean_str(v)})" for k, v in best.items())
    pf = ", ".join(f"({lt.lean_str(v)}, {cmp.fbits(float(v))})" for v in sorted({v for v in best.values() if v}))
    dd = ", ".join(f"({k_(k)}, {lt.lean_str(v)})" for k, v in d8.items())
    today = r0["locals"]["model_performance_metrics"].get_column("validation_date").to_list()[0].isoformat()
    call = f"runM {vterm(r0['valid'])} {tterm(r0['train'])} [{sb}] [{pf}] [{dd}]"
    c = lambda cid, val: (f"{name}: {cid}", "run_py", val)  # noqa: E731
    cases = [c("input table risk_scores_validation", dgtab(r0["valid"])), c("input table risk_scores_train", dgtab(r0["train"]))]
    st = {"validation_rows": r0["valid"].height, "train_rows": r0["train"].height, "columns": len(r0["valid"].columns),
          "python_raises": {str(k): v for k, v in raised.items()}}
    for fix in (False, True):
        r, L = runs[fix], runs[fix]["locals"]
        assert [f for f, _ in r["files"]] == FILES_M
        tag = f"fix_psi_bins={fix}" + (" (Python raises ValueError :277; expected = the continued code path)" if fix in raised else "")
        cases += [c(f"{f} {tag}", dgt(f, df)) for f, df in r["files"]]
        st[f"fix_psi_bins={fix}"] = {
            "ks_rows": L["ks_statistic"].height, "psi_rows": L["psi_calculation"].height, "PSI": L["psi_summary"].item(0, "PSI"),
            "AUC": L["auc_summary"].item(0, "AUC"), "deciles": L["decile_analysis"].height,
            "calibration_bins": L["calibration_plot"].height,
            "status": L["validation_summary"].get_column("status").to_list()[:2],
            "null_psi_components": L["psi_calculation"]["psi_component"].null_count(),
            "nulls_in_threshold_analysis": sum(L["threshold_analysis"].null_count().row(0)),
        }
    STATS[f"met:{name}"] = st
    return call, cases, today


def suite_met() -> Suite:
    s = Suite("runs_r2_met")
    rng = random.Random(SEED + 2)

    def lets(today: str) -> str:
        return PARSE + MK3 + f"let today : Tabular.Cell Float := Tabular.Cell.str (some {lt.lean_str(today)}); " + RUNM

    def emit(scen: list):
        calls, cases, today = [], [], ""
        for a in scen:
            call, cs, today = met_scenario(*a)
            calls.append(call)
            cases += cs
        s.ints(lets(today), " ++ ".join(calls), cases, table=True)

    NV, NT = 300, 700
    texts = {}
    for k in "abc":
        d = ROOT / "inputs" / "scenarios" / f"edge_metrics_{k}"
        texts[k] = ((d / "risk_scores_validation.csv").read_text().splitlines(keepends=True),
                    (d / "risk_scores_train.csv").read_text().splitlines(keepends=True))
    # the last 300 / 700 rows (consecutive row ids)
    scen = []
    for k, (v, t) in texts.items():
        nv, nt = len(v) - 1, len(t) - 1
        scen.append((f"edge_metrics_{k} last {NV}/{NT}", v[0] + "".join(v[-NV:]), t[0] + "".join(t[-NT:]),
                     lambda df, b=100001 + nv - NV: lean_mk3(df, b, None), lambda df, b=1 + nt - NT: lean_mk3(df, b, None)))
    emit(scen)
    # a seeded random 300 / 700 sample of the middle rows (file order)
    scen = []
    for k, (v, t) in texts.items():
        nv, nt = len(v) - 1, len(t) - 1
        iv = sorted(rng.sample(range(NV, nv - NV), NV))  # 0-based data line indices
        it = sorted(rng.sample(range(NT, nt - NT), NT))
        scen.append((f"edge_metrics_{k} random {NV}/{NT}", v[0] + "".join(v[i + 1] for i in iv), t[0] + "".join(t[i + 1] for i in it),
                     lambda df, iv=iv: lean_mk3(df, 100001, iv), lambda df, it=it: lean_mk3(df, 1, it)))
    emit(scen)
    # the REAL risk_scores files of the real pipeline
    pipe = pipeline()
    v = (pipe / "risk_scores_validation.csv").read_text().splitlines(keepends=True)
    t = (pipe / "risk_scores_train.csv").read_text().splitlines(keepends=True)
    emit([("real risk_scores, all 51 columns, last 20/30", v[0] + "".join(v[-20:]), t[0] + "".join(t[-30:]), lean_table, lean_table)])
    hdr = v[0].rstrip("\n").split(",")
    cols = [hdr.index(n) for n in ("row_id", "default_flag", "pd_logistic")]

    def narrow(lines: list[str], n: int) -> str:
        pickd = sorted(rng.sample(range(1, len(lines) - 30), n))
        return "row_id,default_flag,pd_logistic\n" + "".join(
            ",".join(lines[i].rstrip("\n").split(",")[c] for c in cols) + "\n" for i in pickd)

    emit([("real risk_scores, 3 columns, random 150/350", narrow(v, 150), narrow(t, 350), lean_table, lean_table)])
    s.notes = {"run_py": "reviewer 2 real-data samples"}
    return s


if __name__ == "__main__":
    if sys.argv[1:] == ["explain"]:
        explain()
        sys.exit(0)
    want = set(sys.argv[1:]) or {"fe", "pred", "met"}
    sp = WORK / "runs_r2_stats.json"
    if sp.exists():
        STATS.update(json.loads(sp.read_text()))
    if "fe" in want:
        suite_fe().write()
    if "pred" in want:
        suite_pred().write()
    if "met" in want:
        suite_met().write()
    sp.write_text(json.dumps(STATS, indent=1, default=str))
