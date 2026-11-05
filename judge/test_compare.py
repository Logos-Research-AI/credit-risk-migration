"""Comparator self-test: known faults injected into copies of the reference outputs, each
with the expected verdict per column (prompt 00b: debug the referee before trusting it).
Includes a POSITIVE control (a fully converged refit = a correct port, which must pass)
and the defects adversarial reviews A, B and C constructed to slip past earlier versions.

Usage (from judge/): uv run python test_compare.py
"""

from __future__ import annotations

import datetime as dt
import shutil
import sys
import tempfile
from pathlib import Path

import polars as pl

import compare as C
import make_converged_candidate

JUDGE = Path(__file__).resolve().parent
REF = JUDGE / "reference"
CONV = JUDGE / "fixtures" / "converged"
RS, RV, FM = "risk_scores_train.csv", "risk_scores_validation.csv", "final_model_output.csv"
FT, CO, MS = "model_features_train.csv", "model_coefficients.csv", "model_summary.csv"
KG, ST, DA, TA = "kaggle_submission.csv", "stepwise_summary.csv", "decile_analysis.csv", "threshold_analysis.csv"
HL, HP, FS = "printed_hosmer_lemeshow.csv", "printed_hl_partition.csv", "printed_fit_statistics.csv"
CT, PM = "printed_confusion_train.csv", "model_performance_metrics.csv"
PASS = frozenset()
TODAY = dt.date.today().strftime("%d%b%Y").upper()


def load(f: str) -> pl.DataFrame:
    return C.read_text_csv(REF / f)


def setc(df: pl.DataFrame, row: int, col: str, value: str) -> pl.DataFrame:
    s = df.get_column(col).to_list()
    s[row] = value
    return df.with_columns(pl.Series(col, s, dtype=pl.Utf8))


def b12(v: str, d: float) -> str:
    return C.sas_best12(float(v) + d)


def raw_frac(pd_: float) -> float:
    raw = 600 + 250 * (1 - pd_)
    return raw - int(raw)


def rescore(df: pl.DataFrame, pds: list[float]) -> pl.DataFrame:
    """Rewrite pd and everything SAS derives from it, consistently (like a port would)."""
    score = [C.sas_round(600 + 250 * (1 - p)) for p in pds]
    tup = [make_converged_candidate.sas_tuple(s) for s in score]
    upd = {"pd_logistic": [C.sas_best12(p) for p in pds], "credit_risk_score": [str(s) for s in score],
           "risk_grade": [t[0] for t in tup], "recommendation": [t[1] for t in tup], "interest_rate": [t[2] for t in tup]}
    if "pred_logistic" in df.columns:
        upd["pred_logistic"] = ["1" if p >= 0.5 else "0" for p in pds]
    return df.with_columns([pl.Series(k, v, dtype=pl.Utf8) for k, v in upd.items()])


def cases():
    rs, ft, co, ms = load(RS), load(FT), load(CO), load(MS)
    kg, st, da, ta = load(KG), load(ST), load(DA), load(TA)
    hl, hp, fs, ct, pm = load(HL), load(HP), load(FS), load(CT), load(PM)
    pd_ = rs.get_column("pd_logistic").cast(pl.Float64).to_list()
    far = next(i for i, p in enumerate(pd_) if abs(raw_frac(p) - 0.5) > 0.1 and abs(p - 0.5) > 0.01)
    near = next(i for i, p in enumerate(pd_) if 0 < 0.5 - raw_frac(p) <= 250 * C.PD_TOL / 2)  # rounds down, can go up
    zero_flag = rs.get_column("default_flag").to_list().index("0")
    zero_util = rs.get_column("credit_utilization").to_list().index("0")
    PDv = rs["pd_logistic"][far]

    # (name, file judged, {file: candidate df or raw bytes}, expected failed tags, strict passes?, excused)
    # expected failed tags: a frozenset = exactly these; a tuple ("atleast", {...}) = these and maybe more
    yield "identical", RS, {RS: rs}, PASS, True, {}
    yield "rows reordered", RS, {RS: rs.reverse()}, PASS, True, {}
    # positive control: a correct port (fully converged refit, SAS rules applied)
    conv = {f: C.read_text_csv(CONV / f) for f in (RS, RV, FM)}
    yield "CONVERGED REFIT = correct port (train)", RS, conv, PASS, False, {"credit_risk_score": 42}
    yield "CONVERGED REFIT = correct port (valid)", RV, conv, PASS, False, {"credit_risk_score": 29}
    yield "CONVERGED REFIT = correct port (final)", FM, conv, PASS, False, {"credit_risk_score": 42}
    # pd value / distribution / format
    yield "pd +2e-4 (beyond PD_TOL)", RS, {RS: setc(rs, far, "pd_logistic", b12(PDv, 2e-4))}, {"pd_logistic"}, False, {}
    yield "pd +5e-5 one row (within PD_TOL)", RS, {RS: setc(rs, far, "pd_logistic", b12(PDv, 5e-5))}, PASS, False, {}
    bias = rescore(rs, [p + 5e-5 for p in pd_])
    yield "C/D2: +5e-5 bias on every pd, rescored", RS, {RS: bias}, ("atleast", {"pd_logistic(mean)"}), False, None
    pd4 = rs.with_columns(pl.Series("pd_logistic", [f"{p:.4f}" for p in pd_], dtype=pl.Utf8))
    yield "C/D3: pd printed %.4f", RS, {RS: pd4}, ("atleast", {"pd_logistic"}), False, None
    yield "C/D4: pd in E-notation", RS, {RS: setc(rs, far, "pd_logistic", f"{float(PDv):.9E}")}, {"pd_logistic"}, False, {}
    yield "pd 'nan'", RS, {RS: setc(rs, far, "pd_logistic", "nan")}, {"pd_logistic"}, False, {}
    yield "pd missing", RS, {RS: setc(rs, far, "pd_logistic", "")}, {"pd_logistic"}, False, {}
    # structure
    yield "row dropped", RS, {RS: rs.slice(1)}, {"rows", "keys"}, False, {}
    yield "row duplicated", RS, {RS: pl.concat([rs, rs.slice(0, 1)])}, {"rows", "keys"}, False, {}
    yield "extra key row", RS, {RS: pl.concat([rs, setc(rs.slice(0, 1), 0, "row_id", "999999")])}, {"rows", "keys"}, False, {}
    yield "columns swapped", RS, {RS: rs.select([rs.columns[1], rs.columns[0], *rs.columns[2:]])}, {"columns"}, False, {}
    yield "column dropped", RS, {RS: rs.drop("risk_grade")}, {"columns"}, False, {}
    # integers / flags exact; printed formats enforced (reviews A1, C2)
    yield "default_flag 0->1", RS, {RS: setc(rs, zero_flag, "default_flag", "1")}, {"default_flag"}, False, {}
    yield "age +1", RS, {RS: setc(rs, far, "age", str(int(rs["age"][far]) + 1))}, {"age"}, False, {}
    floats = rs.with_columns((pl.col(c) + ".0").alias(c) for c in ("default_flag", "age", "has_delinquency"))
    yield "C/D4: integers printed as floats", RS, {RS: floats}, {"default_flag", "age", "has_delinquency"}, False, {}
    yield "base_rate 0.06 all rows", RS, {RS: rs.with_columns(pl.lit("0.06").alias("base_rate"))}, {"base_rate"}, False, {}
    yield "credit_utilization '0'->'0.99'", RS, {RS: setc(rs, zero_util, "credit_utilization", "0.99")}, {"credit_utilization"}, False, {}
    yield "comma thousands separator", FT, {FT: setc(ft, 0, "income_per_dependent", "1,566.6666667")}, {"income_per_dependent"}, False, {}
    fv = ft["income_per_dependent"][0]
    yield "BEST12 value with extra digits", FT, {FT: setc(ft, 0, "income_per_dependent", fv + "1")}, {"income_per_dependent"}, False, {}
    yield "BEST12 value +2 units", FT, {FT: setc(ft, 0, "income_per_dependent", b12(fv, 2e-7))}, {"income_per_dependent"}, False, {}
    li = ft.get_column("log_monthly_income").str.len_chars().to_list().index(11)
    lv = ft["log_monthly_income"][li]  # e.g. '8.455530531' = rounded 8.45553053102 (review B6)
    yield "BEST12 short rounded value +9e-11 (1 unit)", FT, {FT: setc(ft, li, "log_monthly_income", b12(lv, 9e-11))}, PASS, False, {}
    yield "BEST12 short rounded value +3e-10", FT, {FT: setc(ft, li, "log_monthly_income", b12(lv, 3e-10))}, {"log_monthly_income"}, False, {}
    # discrete pd-derived columns and excusals (reviews A2, C1)
    yield "grade ' A' (whitespace)", RS, {RS: setc(rs, far, "risk_grade", " " + rs["risk_grade"][far])}, {"risk_grade"}, False, {}
    yield "score +1 far from boundary", RS, {RS: setc(rs, far, "credit_risk_score", str(int(rs["credit_risk_score"][far]) + 1))}, {"credit_risk_score"}, False, {}
    p_up = pd_[near] - (0.5 - raw_frac(pd_[near]) + 1e-9) / 250  # just crosses round()'s .5 boundary
    legit = pl.concat([rs.slice(0, near), rescore(rs.slice(near, 1), [p_up]), rs.slice(near + 1)])
    yield "legit flip: pd crosses .5 boundary, rescored", RS, {RS: legit}, PASS, False, {"credit_risk_score": 1}
    yield "score +1 at boundary but pd unchanged", RS, {RS: setc(rs, near, "credit_risk_score", str(int(rs["credit_risk_score"][near]) + 1))}, {"credit_risk_score"}, False, {}
    d1 = rescore(rs, [round(p, 4) for p in pd_]).with_columns(rs["pd_logistic"])
    yield "C/D1: scores from pd rounded to 4dp, pd exact", RS, {RS: d1}, ("atleast", {"credit_risk_score"}), False, None
    garbage = setc(setc(rs, near, "credit_risk_score", "-999"), near, "risk_grade", "Z")
    yield "near boundary, garbage score+grade", RS, {RS: garbage}, {"credit_risk_score", "risk_grade"}, False, {}
    yield "pred_logistic '7'", RS, {RS: setc(rs, far, "pred_logistic", "7")}, {"pred_logistic"}, False, {}
    yield "rate '5.0%'", RS, {RS: setc(rs, far, "interest_rate", "5.0%")}, {"interest_rate"}, False, {}
    # model-fit tables (review B2/B5/C5)
    yield "coef Estimate +2 DU", CO, {CO: setc(co, 1, "Estimate", "0.00252")}, PASS, False, {}
    yield "coef Estimate +3 DU", CO, {CO: setc(co, 1, "Estimate", "0.00253")}, {"Estimate"}, False, {}
    w = co["WaldChiSq"][3]
    yield "coef WaldChiSq +0.05%", CO, {CO: setc(co, 3, "WaldChiSq", f"{float(w) * 1.0005:.4f}")}, PASS, False, {}
    yield "coef WaldChiSq +0.5%", CO, {CO: setc(co, 3, "WaldChiSq", f"{float(w) * 1.005:.4f}")}, {"WaldChiSq"}, False, {}
    yield "coef DF 1->2", CO, {CO: setc(co, 1, "DF", "2")}, {"DF"}, False, {}
    yield "p-value 0.0436->0.0437", CO, {CO: setc(co, 1, "ProbChiSq", "0.0437")}, PASS, False, {}
    yield "p-value '<.0001' -> number", CO, {CO: setc(co, 0, "ProbChiSq", "0.00005")}, {"ProbChiSq"}, False, {}
    s0 = st["ScoreChiSq"][0]
    yield "stepwise ScoreChiSq +0.05%", ST, {ST: setc(st, 0, "ScoreChiSq", f"{float(s0) * 1.0005:.4f}")}, PASS, False, {}
    yield "stepwise ScoreChiSq +1%", ST, {ST: setc(st, 0, "ScoreChiSq", f"{float(s0) * 1.01:.4f}")}, {"ScoreChiSq"}, False, {}
    yield "stepwise '_' -> ''", ST, {ST: setc(st, 0, "WaldChiSq", "")}, {"WaldChiSq"}, False, {}
    yield "stepwise effect renamed", ST, {ST: setc(st, 4, "EffectEntered", "age_category")}, {"EffectEntered"}, False, {}
    yield "stepwise NumberInModel +1", ST, {ST: setc(st, 0, "NumberInModel", "2")}, {"NumberInModel"}, False, {}
    aic = [i for i, r in enumerate(fs["RowId"].to_list()) if r == "AIC"][-1]
    av = fs["InterceptAndCovariates"][aic]
    yield "fit stats -2LL-class +0.001 (2 DU)", FS, {FS: setc(fs, aic, "InterceptAndCovariates", f"{float(av) + 0.001:.3f}")}, PASS, False, {}
    yield "C/D6: AIC +2 (parameter count)", FS, {FS: setc(fs, aic, "InterceptAndCovariates", f"{float(av) + 2:.3f}")}, {"InterceptAndCovariates"}, False, {}
    yield "HL ChiSq +0.05%", HL, {HL: setc(hl, 0, "ChiSq", "121.9700")}, PASS, False, {}
    yield "HL ChiSq +1", HL, {HL: setc(hl, 0, "ChiSq", "122.9130")}, {"ChiSq"}, False, {}
    yield "HL DF 8->9", HL, {HL: setc(hl, 0, "DF", "9")}, {"DF"}, False, {}
    yield "HL EventsObserved +1", HP, {HP: setc(hp, 0, "EventsObserved", str(int(hp["EventsObserved"][0]) + 1))}, PASS, False, {}
    yield "HL EventsObserved +3", HP, {HP: setc(hp, 0, "EventsObserved", str(int(hp["EventsObserved"][0]) + 3))}, {"EventsObserved"}, False, {}
    t0, t1 = int(hp["Total"][0]), int(hp["Total"][1])
    yield "C/D6: HL 10 rows moved between groups", HP, {HP: setc(setc(hp, 0, "Total", str(t0 + 10)), 1, "Total", str(t1 - 10))}, {"Total"}, False, {}
    c0, c1 = int(ct["COUNT"][0]), int(ct["COUNT"][1])
    yield "C/D6: confusion row moved, no flips", CT, {CT: setc(setc(ct, 0, "COUNT", str(c0 - 1)), 1, "COUNT", str(c1 + 1))}, {"COUNT"}, False, {}
    # metrics and summaries
    yield "decile defaults +1", DA, {DA: setc(da, 0, "defaults", str(int(da["defaults"][0]) + 1))}, {"defaults"}, False, {}
    yield "decile default_rate +1 DU", DA, {DA: setc(da, 0, "default_rate", "35.05%")}, PASS, False, {}
    yield "decile default_rate no '%'", DA, {DA: setc(da, 0, "default_rate", "35.04")}, {"default_rate"}, False, {}
    yield "C/D4: default_rate percent8.3", DA, {DA: setc(da, 0, "default_rate", "35.040%")}, {"default_rate"}, False, {}
    yield "C/D4: Train_AUC printed 8.5", MS, {MS: setc(setc(ms, 0, "Train_AUC", "0.85920"), 0, "training_date", TODAY)}, {"Train_AUC"}, False, {}
    msd = setc(ms, 0, "training_date", TODAY)
    yield "summary training_records +1", MS, {MS: setc(msd, 0, "training_records", "105001")}, {"training_records"}, False, {}
    yield "summary valid_precision +1 DU", MS, {MS: setc(msd, 0, "valid_precision", "0.5691")}, PASS, False, {}
    yield "summary valid_precision +2 DU, no flips", MS, {MS: setc(msd, 0, "valid_precision", "0.5692")}, {"valid_precision"}, False, {}
    yield "C/D5: train_accuracy +8e-4, no flips", MS, {MS: setc(msd, 0, "train_accuracy", "0.9377")}, {"train_accuracy"}, False, {}
    yield "date: today, DATE9.", MS, {MS: msd}, PASS, True, {}
    yield "C/D7: date '99ZZZ0000'", MS, {MS: setc(ms, 0, "training_date", "99ZZZ0000")}, {"training_date"}, True, {}
    yield "C/D7: date hard-coded 01JAN2020", MS, {MS: setc(ms, 0, "training_date", "01JAN2020")}, {"training_date"}, True, {}
    yield "date ISO format", MS, {MS: setc(ms, 0, "training_date", dt.date.today().isoformat())}, {"training_date"}, True, {}
    yield "metrics date ISO format", PM, {PM: setc(pm, 0, "validation_date", dt.date.today().isoformat())}, {"validation_date"}, True, {}
    # keys and raw formatting
    yield "row_id '85073.0'", KG, {KG: kg.with_columns(pl.col("row_id") + ".0")}, {"row_id"}, False, {}
    yield "threshold key float noise", TA, {TA: setc(ta, 3, "threshold", "0.6000000000000001")}, {"threshold"}, False, {}
    raw = (REF / CO).read_bytes()
    yield "CRLF line endings", CO, {CO: raw.replace(b"\n", b"\r\n")}, PASS, False, {}
    yield "quoted text fields", CO, {CO: raw.replace(b"MLE", b'"MLE"')}, PASS, False, {}
    yield "empty candidate file", CO, {CO: b""}, {"error"}, False, {}


def main() -> int:
    if not CONV.exists():
        make_converged_candidate.main()
    wrong = 0
    for name, f, files, exp_port, exp_strict, exp_exc in cases():
        tmp = Path(tempfile.mkdtemp(prefix="judge_selftest_"))
        try:
            for fn, cand in files.items():
                cand.write_csv(tmp / fn) if isinstance(cand, pl.DataFrame) else (tmp / fn).write_bytes(cand)
            port = C.compare_dir(REF, tmp, [f], "port")[0]
            strict = C.compare_dir(REF, tmp, [f], "strict")[0]
        finally:
            shutil.rmtree(tmp)
        if isinstance(exp_port, tuple):
            port_ok = exp_port[1] <= port.failed and port.status == "FAIL"
        else:
            port_ok = port.failed == set(exp_port)
        ok = port_ok and (strict.status == "PASS") == exp_strict and (exp_exc is None or port.excused == exp_exc)
        wrong += not ok
        print(f"{'ok ' if ok else 'BAD'}  {name:46s} port={sorted(port.failed) or 'PASS'} strict={strict.status} "
              f"excused={port.excused}" + ("" if ok else f"\n       expected port={exp_port} strict_pass={exp_strict} "
                                                         f"excused={exp_exc}\n       {port.problems[:3]}"))
    print(f"\n{'ALL CASES OK' if not wrong else f'{wrong} CASE(S) WRONG'}")
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main())
