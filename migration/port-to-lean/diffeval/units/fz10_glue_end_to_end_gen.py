"""Fidelity pass 2026-11-20, label glue-end-to-end: the glue of the contracts (def:pyPipeline as
def:PyLinks constrains its parameters, def:ScoreRun) against the REAL port pipeline (port HEAD 4a757fb):
feature_engineering.run -> train.run -> predict.run -> metrics_calculation.run, each stage reading
the files the stage before wrote.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python \
      diffeval/units/fz10_glue_end_to_end_gen.py seeds S0 COUNT      -> work/fz10_glue_seeds_<S0>.jsonl
  ... fz10_glue_end_to_end_gen.py real                               -> work/fz10_glue_real.jsonl
  ... fz10_glue_end_to_end_gen.py receipt                            -> receipts/fuzz_2026-11-20-glue-end-to-end.tsv

LEAN SIDE: NOT EVALUATED. eval_decl refuses (server schema error, the failure recorded in
diffeval/eval_decl-errors-2026-11-18.md section 1) every item whose dependency cone holds a field of
pyPipeline: def:run, def:run_py_py_py, def:run_py_py, def:run_py, def:train_run_04_score_train,
def:train_run_10_score_valid, def:train_run_14_final_and_summary, def:predict_run_08_outputs,
def:metrics_run_09_model_performance (probed 2026-11-20, input "1"); def:pyPipeline itself is
noncomputable (Pipeline over the reals); and the carriers that worked around the refusal
(def:zz_carrier*, def:zz_carrier_e) are no longer in the blueprint. So this script checks, on the
Python side only, the WIRING the glue states: that each field of pyPipeline, with its parameters
instantiated as the port does (fit = the port's stepwise, read-backs = the port's CSV round trip,
split = the ids the port used, flags = file existence, modelFile = model.json), names the files the
port writes. Where the glue applies a chain the port does not apply to that file, the chain is run
with the port's OWN code, so a difference is a difference between the glue and the port, not a
translation error.

One case = one run of the four stages on one input. Checks (each a receipt row):
  G1 features   model_features_train/validation.csv are written exactly when fe completes; the ids
                the split draws from (credit_features.row_id) are the VAR1 column of the import as
                cleaned (pyPipeline passes cleaned.getF "VAR1"): multiset of row_id over the two
                files = the imported VAR1 cells read by input_best32 (BEST12. round trip as step 01).
  G2 fit        model.json is written exactly when both feature files exist and the stage fitted
                (final is not None); its intercept is a number (pyPipeline.fit: none when step 04
                gives no intercept); model_coefficients.csv exists exactly when model.json does
                (PyLinks 7: coefExists m <-> some F, fit F = some m).
  G3 score F2   risk_scores_validation.csv: has no row in a run without fit (ScoreRun: S2 = []).
  G4 score F1   (ScoreRun fitted: S1 = Q.score m F1, the VALIDATION chain of train, steps 10-12-14,
                applied to the training feature file) against risk_scores_train.csv, which the port
                writes from the TRAINING chain (steps 04-09-12). Computed with the port's own code:
                train.run is run a second time on a folder whose model_features_validation.csv is a
                byte copy of model_features_train.csv, with the stepwise result of the first run
                (sas_compat.stepwise_logistic recorded and replayed), and its
                risk_scores_validation.csv frame (as handed to write_sas_csv) is compared bit for bit
                (float bits, null vs NaN, names, dtypes, order) with the first run's
                risk_scores_train.csv frame.
  G5 medians    income_medians.csv is written exactly when fe completes (PyLinks 7: mediansExist).
  G6 metrics    when metrics completes, validation_summary.csv and threshold_analysis.csv are among
                its files (pyPipeline.metrics looks them up; none otherwise).
Inputs (seeded, random.Random(seed)): n = 0..60 rows of cs-training in the file's own column order;
modes by seed: valid; one outcome (no fit); a stop of fe (repeated id / a bad row / no known income /
header only); a split file that does not fit (draw) or fits; extreme magnitudes in DebtRatio,
RevolvingUtilization, MonthlyIncome (1e300, 1e15, 1e-300, 0, -0.0 where valid), ties. cs-test: 0..8
rows. Real data: legacy/data with inputs/split_ids.csv.
"""
from __future__ import annotations

import contextlib
import io
import json
import math
import random
import shutil
import struct
import sys
import tempfile
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
PTL = HERE.parents[1]
WORK = HERE.parent / "work"
REC = HERE.parent / "receipts" / "fuzz_2026-11-20-glue-end-to-end.tsv"
DATA = PTL.parents[1] / "legacy" / "data"
SPLIT = PTL / "inputs" / "split_ids.csv"

from credit_risk import feature_engineering as fe  # noqa: E402
from credit_risk import metrics_calculation as mc  # noqa: E402
from credit_risk import predict as pr  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402
from credit_risk import train as tr  # noqa: E402

HEADER = ("," + "SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,age,NumberOfTime30-59DaysPastDueNotWorse,"
          "DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,"
          "NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents")

# ---------------------------------------------------------------- recorders ----
_REC: dict = {"files": None, "stepwise": None, "replay": None}
_o_write, _o_step = sc.write_sas_csv, sc.stepwise_logistic


def _w(df, path, formats=None):
    if _REC["files"] is not None:
        _REC["files"].append((Path(path).name, df.clone()))
    return _o_write(df, path, formats=formats)


def _step(*a, **k):
    if _REC["replay"] is not None:
        return _REC["replay"]
    r = _o_step(*a, **k)
    _REC["stepwise"] = r
    return r


sc.write_sas_csv = _w
sc.stepwise_logistic = _step


def quiet(fn):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            fn()
        return None
    except Exception as e:  # noqa: BLE001
        return f"{type(e).__name__}: {e}"[:200]


# ------------------------------------------------------------- exact compare ----
def fbits(x):
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def canon(df: pl.DataFrame):
    cols = []
    for c in df.columns:
        s = df.get_column(c)
        if s.dtype.is_float():
            vals = [None if v is None else ("nan" if math.isnan(v) else fbits(v)) for v in s.to_list()]
            kind = "f64"
        else:
            vals = [None if v is None else str(v) for v in s.to_list()]
            kind = str(s.dtype)
        cols.append((c, kind, vals))
    return cols


def first_diff(a: pl.DataFrame, b: pl.DataFrame):
    ca, cb = canon(a), canon(b)
    if [c[0] for c in ca] != [c[0] for c in cb]:
        return {"what": "names", "port": [c[0] for c in ca], "glue": [c[0] for c in cb]}
    if a.height != b.height:
        return {"what": "height", "port": a.height, "glue": b.height}
    for (n, ka, va), (_, kb, vb) in zip(ca, cb):
        if ka != kb:
            return {"what": f"{n}.dtype", "port": ka, "glue": kb}
        for i, (x, y) in enumerate(zip(va, vb)):
            if x != y:
                return {"what": f"{n}[{i}]", "port": x, "glue": y,
                        "port_row": a.row(i, named=True), "glue_row": b.row(i, named=True)}
    return None


# --------------------------------------------------------------- generation ----
def fmt(x):
    if x is None:
        return ""
    if isinstance(x, str):
        return x
    if x == math.inf:
        return "1e400"
    if float(x).is_integer() and abs(x) < 1e15:
        return str(int(x)) if not (x == 0 and math.copysign(1, x) < 0) else "-0"
    return repr(float(x))


BIG = [1e9, 1e8, 3e7, 1e6, 123456.789, 1e-300, 5e-324, 0.0]
BIG_HUGE = [1e300, 1e200, 1e15]


def gen(seed: int):
    if seed >= 11000:  # family "excluded far row": a slope-family input plus one training row that the fit
        # leaves out (utilization_debt_interaction overflows to a missing cell) with a far credit-line count
        g = gen(9000 + (seed - 11000))
        r = random.Random(seed)
        body = g["train"].rstrip("\n").split("\n")
        n = len(body)  # header + n-1 rows; the new row gets id n
        far = r.choice(["1e80", "1e150", "1e300", "1e40", "5000"])
        body.append(f"{n},0,1e200,40,0,1e200,5000,{far},0,1,0,1")
        nt = (7 * n + 9) // 10
        split = "row_id\n" + "".join(f"{i}\n" for i in [n] + list(range(1, nt)))
        return dict(seed=seed, mode=g["mode"], n=n, ext=True, train="\n".join(body) + "\n", split=split,
                    test=g["test"])
    r = random.Random(seed)
    mode = seed % 20
    n = [0, 1, 2, 3, 5, 8, 12, 20, 30, 45, 60][r.randrange(11)] if mode in (17,) else r.randrange(12, 61)
    if mode == 17:
        n = r.choice([0, 1, 2, 3])
    if seed >= 9000 and mode not in (7, 8, 9, 17):
        n = r.randrange(150, 400)
    ext = r.random() < 0.6  # extreme magnitudes on
    huge = r.random() < 0.1  # 1e300-class magnitudes (the stepwise of the port overflows on most)
    rows = []
    for i in range(n):
        y = 0 if mode in (5, 6) else (1 if r.random() < 0.3 else 0)
        util = r.choice(BIG_HUGE) if huge and r.random() < 0.05 else r.choice(BIG) if ext and r.random() < 0.08 else round(r.random() * r.choice([1, 1, 1.5, 3]), r.choice([2, 6, 9]))
        age = r.choice([21, 29, 30, 39, 40, 49, 50, 59, 60, 75, 0]) if r.random() < 0.5 else r.randrange(18, 95)
        d30 = r.choice([0, 0, 0, 1, 2, 98])
        debt = r.choice(BIG) if ext and r.random() < 0.08 else round(r.random() * r.choice([1, 2, 50, 3000]), r.choice([1, 4, 9]))
        inc = (None if r.random() < 0.15 else r.choice(BIG[:4]) if ext and r.random() < 0.05
               else float(r.choice([0, 1, 2500, 2500, 4000, 9120, 15000, 250000])) if r.random() < 0.5 else float(r.randrange(0, 30000)))
        lines = r.choice([0, 1, 3, 5, 8, 13, 40])
        d90 = r.choice([0, 0, 0, 1, 3, 98])
        re_ = r.choice([0, 0, 1, 2, 6])
        d60 = r.choice([0, 0, 0, 1, 98])
        dep = None if r.random() < 0.1 else float(r.choice([0, 0, 1, 2, 3, 20]))
        rows.append([float(i + 1), float(y), util, float(age), float(d30), debt, inc, float(lines), float(d90), float(re_), float(d60), dep])
    if seed >= 9000 and n:  # family "slope": P(outcome) falls smoothly with one unbounded candidate column
        col, mid, sc_, farv = [(6, 6000.0, 1500.0, [1e6, 1e7, 1e8, 1e9]), (7, 8.0, 2.0, [200.0, 500.0, 5000.0]),
                                (4, 3.0, 1.0, [98.0, 500.0, 5000.0]), (3, 50.0, 6.0, [500.0, 1e4, 1e6])][seed % 4]
        for row in rows:
            x = float(r.randrange(0, int(mid * 2.5) + 1))
            row[col] = max(x, 18.0) if col == 3 else x
            row[1] = float(r.random() < 1 / (1 + math.exp((row[col] - mid) / sc_)))
        for k in r.sample(range(n), max(1, n // 12)):
            rows[k][col] = r.choice(farv)
            rows[k][1] = 0.0
    elif seed >= 5000 and n:  # family "eta": outcome driven by one column, one row of that column far out
        col = [2, 5, 4, 3, 3][seed % 5]  # utilization, DebtRatio, 30-59 count, age (twice)
        for row in rows:
            v = r.random()
            row[col] = (float(round(v * 3, 2)) if col in (2, 5) else float(r.randrange(0, 4)) if col == 4
                        else float(r.randrange(20, 80)))
            cut = 45.0 if col == 3 else 1.0
            row[1] = float((row[col] < cut) if r.random() < 0.85 else (row[col] >= cut))
        far = (r.choice([1e3, 1e4, 1e5, 1e6, 1e7, 1e8]) if col in (2, 5) else float(r.choice([50, 98, 500, 5000]))
               if col == 4 else float(r.choice([150, 500, 2000, 1e4, 1e5, 1e6])))
        for k in r.sample(range(n), max(1, n // 15)):
            rows[k][col] = far
            rows[k][1] = float(r.random() < 0.2)
    if n >= 2 and mode == 7:  # repeated id -> fe stops
        rows[-1][0] = rows[0][0]
    if n and mode == 8:  # bad row (negative count) -> fe stops
        rows[r.randrange(n)][4] = -1.0
    if n and mode == 9:  # no known income -> fe stops
        for row in rows:
            row[6] = None
    if mode == 10 and n:  # ties: every score row equal
        for row in rows[1:]:
            row[1:] = rows[0][1:]
            row[1] = float(r.random() < 0.5)
    lines_ = [HEADER] + [",".join(fmt(v) for v in row) for row in rows]
    train_txt = "\n".join(lines_) + "\n"
    ids = [row[0] for row in rows]
    nt = (7 * n + 9) // 10
    if mode in (11, 12) or not ids:  # does not fit -> the seeded draw
        split = [float(10 ** 6 + k) for k in range(max(nt, 1))]
    else:
        sh = ids[:]
        r.shuffle(sh)
        split = sh[:nt]
    split_txt = "row_id\n" + "".join(fmt(x) + "\n" for x in split)
    m = r.randrange(0, 9)
    test_rows = []
    for i in range(m):
        test_rows.append([float(i + 1), None, round(r.random(), 4), float(r.randrange(20, 90)), 0.0,
                          r.choice([0.3, 1.5, 1e300]) if ext and r.random() < 0.1 else round(r.random() * 2, 3),
                          None if r.random() < 0.2 else float(r.randrange(0, 20000)), 4.0, 0.0, 1.0, 0.0,
                          None if r.random() < 0.2 else 1.0])
    test_txt = "\n".join([HEADER] + [",".join(fmt(v) for v in row) for row in test_rows]) + "\n"
    return dict(seed=seed, mode=mode, n=n, ext=ext, train=train_txt, split=split_txt, test=test_txt)


# --------------------------------------------------------------- one case ----
# Kept / rejected (prompts/fuzz-2026-11-16.md step 4): a run is "raised" when a stage raises (the port's
# stepwise OverflowError on 1e150-class inputs, a polars ComputeError on 1-3 row inputs): not compared.
# Of the step preconditions only the Convention 1 clause of def:train_run_04_score_train_precond is
# rendered ("pre04"); a G4 case where it fails is "rejected". The other clauses are rendered by the
# unit fuzzers of the stages.
def run_case(data: Path, split: Path, out: Path, label) -> dict:
    res: dict = {"case": label}
    shutil.rmtree(out, ignore_errors=True)
    out.mkdir(parents=True)
    files: dict[str, list] = {}
    _REC["stepwise"] = None
    _REC["replay"] = None
    for st, fn in [("fe", lambda: fe.run(data, out, split_ids=split)),
                   ("train", lambda: tr.run(out, out)),
                   ("predict", lambda: pr.run(out, out, data_dir=data, income_medians=out / "income_medians.csv")),
                   ("metrics", lambda: mc.run(out, out))]:
        _REC["files"] = []
        err = quiet(fn)
        files[st] = _REC["files"]
        res[st] = "completed" if err is None else ("stopped" if "stopped" in err or "Nothing is exported" in err else "raised: " + err)
        res[st + "_files"] = [f for f, _ in _REC["files"]]
    _REC["files"] = None
    fit = _REC["stepwise"]
    fitted = fit is not None and fit.final is not None
    res["fitted"] = fitted
    # G1
    fe_ok = res["fe"] == "completed"
    exists = {p.name for p in out.iterdir()}
    g1 = (("model_features_train.csv" in exists and "model_features_validation.csv" in exists) == fe_ok)
    if fe_ok:
        raw = sc.proc_import_csv(data / "cs-training.csv", guessingrows=None)
        v = raw.get_column(raw.columns[0])
        if v.dtype != pl.String:
            pass
        ids_in = sorted(fbits(float(x)) for x in raw.select(pl.col(raw.columns[0]).cast(pl.Float64)).to_series().to_list())
        ft = dict(files["fe"])
        ids_out = sorted(fbits(float(x)) for x in pl.concat([ft["model_features_train.csv"].select("row_id"),
                                                               ft["model_features_validation.csv"].select("row_id")]).to_series().to_list())
        g1 = g1 and ids_in == ids_out
    res["G1"] = g1
    res["raised"] = any(str(res[st]).startswith("raised") for st in ("fe", "train", "predict", "metrics"))
    # G2 / G5
    tr_ok = res["train"] == "completed"
    mj = out / "model.json"
    g2 = mj.exists() == (tr_ok and fitted) and ((out / "model_coefficients.csv").exists() == mj.exists())
    if mj.exists():
        g2 = g2 and isinstance(json.loads(mj.read_text())["intercept"], float)
    res["G2"] = g2
    res["G5"] = (("income_medians.csv" in exists) == fe_ok)
    # G3
    tfiles = dict(files["train"])
    if tr_ok and not fitted:
        res["G3"] = tfiles["risk_scores_validation.csv"].height == 0
    else:
        res["G3"] = None
    # G6
    if res["metrics"] == "completed":
        mf = res["metrics_files"]
        res["G6"] = "validation_summary.csv" in mf and "threshold_analysis.csv" in mf
    else:
        res["G6"] = None
    # def:train_run_04_score_train_precond, last clause (Convention 1 narrowing): for every training row
    # with a non-null eta (built as train.py:312-314 builds eta_train), exp(-eta) is finite. Rendered on
    # the frame the train stage imported (the first recorded write's source is not needed: the
    # feature file is re-imported exactly as train.py:46-51 does).
    res["pre04"] = True
    if tr_ok and fitted and mj.exists():
        m = json.loads(mj.read_text())
        mft = sc.proc_import_csv(out / "model_features_train.csv", guessingrows=None)
        eta = pl.lit(m["intercept"], pl.Float64)
        for c, b in m["coefficients"].items():
            eta = eta + b * pl.col(c)
        e = mft.select((-eta).exp().alias("e")).get_column("e")
        res["pre04"] = bool(e.drop_nulls().is_finite().all())
    # G4: the validation chain on F1, with the port's own code
    res["G4"] = None
    if tr_ok and fitted:
        alt = out.parent / (out.name + "_g4")
        shutil.rmtree(alt, ignore_errors=True)
        alt.mkdir(parents=True)
        shutil.copyfile(out / "model_features_train.csv", alt / "model_features_train.csv")
        shutil.copyfile(out / "model_features_train.csv", alt / "model_features_validation.csv")
        _REC["files"] = []
        _REC["replay"] = fit
        err = quiet(lambda: tr.run(alt, alt))
        _REC["replay"] = None
        f2 = dict(_REC["files"])
        _REC["files"] = None
        if err is not None:
            res["G4"] = False
            res["G4_diff"] = {"what": "second run raised", "err": err}
        else:
            # same model in both runs (model.json bytes)
            same_model = (alt / "model.json").read_bytes() == mj.read_bytes()
            d = first_diff(tfiles["risk_scores_train.csv"], f2["risk_scores_validation.csv"])
            res["G4"] = same_model and d is None
            res["G4_rows"] = tfiles["risk_scores_train.csv"].height
            if d is not None:
                p = tfiles["risk_scores_train.csv"]
                g = f2["risk_scores_validation.csv"]
                ndiff = sum(1 for i in range(min(p.height, g.height)) if canon(p[i]) != canon(g[i]))
                res["G4_diff"] = {**d, "rows_differing": ndiff}
                res["G4_diff"] = json.loads(json.dumps(res["G4_diff"], default=str))
            if not same_model:
                res["G4_model"] = "model.json differs between the two runs"
        shutil.rmtree(alt, ignore_errors=True)
    return res


def seeds_main(s0: int, count: int) -> None:
    WORK.mkdir(exist_ok=True)
    outp = WORK / f"fz10_glue_seeds_{s0}.jsonl"
    tmp = Path(tempfile.mkdtemp(prefix="fz10_tmp_", dir=WORK))
    with outp.open("w") as fh:
        for s in range(s0, s0 + count):
            g = gen(s)
            d = tmp / f"d{s}"
            d.mkdir()
            (d / "cs-training.csv").write_text(g["train"])
            (d / "cs-test.csv").write_text(g["test"])
            (d / "split.csv").write_text(g["split"])
            res = run_case(d, d / "split.csv", tmp / f"o{s}", s)
            res.update(mode=g["mode"], n=g["n"], ext=g["ext"])
            fh.write(json.dumps(res, default=str) + "\n")
            fh.flush()
            shutil.rmtree(d, ignore_errors=True)
            shutil.rmtree(tmp / f"o{s}", ignore_errors=True)
    print(outp)


def real_main() -> None:
    WORK.mkdir(exist_ok=True)
    out = WORK / "fz10_glue_real_out"
    res = run_case(DATA, SPLIT, out, "legacy/data")
    (WORK / "fz10_glue_real.jsonl").write_text(json.dumps(res, default=str) + "\n")
    print(json.dumps(res, default=str)[:3000])


if __name__ == "__main__":
    if sys.argv[1] == "seeds":
        seeds_main(int(sys.argv[2]), int(sys.argv[3]))
    elif sys.argv[1] == "real":
        real_main()
    elif sys.argv[1] == "one":
        g = gen(int(sys.argv[2]))
        print(g["train"]); print(g["split"]); print(g["test"])
