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
AS, PC, IM = "printed_association.csv", "printed_classification.csv", "income_medians.csv"
TP = "test_predictions.csv"
CUTS = [cut for cut, _, _ in C.GRADE_CUTS]
TUPLE = frozenset(C.GRADE_TUPLE)
PASS = frozenset()
# grade flips of the positive control that the judge excuses (a fully converged refit against SAS's fit)
CONV_TRAIN: dict[str, int] = {"risk_grade": 1, "recommendation": 1, "interest_rate": 1}  # applicant 108555, at the 15 % cut
CONV_VALID: dict[str, int] = {}
TODAY = dt.date.today().strftime("%d%b%Y").upper()


def load(f: str) -> pl.DataFrame:
    return C.read_text_csv(REF / f)


def setc(df: pl.DataFrame, row: int, col: str, value: str) -> pl.DataFrame:
    s = df.get_column(col).to_list()
    s[row] = value
    return df.with_columns(pl.Series(col, s, dtype=pl.Utf8))


def b12(v: str, d: float) -> str:
    return C.sas_best12(float(v) + d)


def cut_gap(pd_: float) -> float:
    """Distance to the nearest grade cut, positive when the probability is below it."""
    cut = min(CUTS, key=lambda k: abs(k - pd_))
    return cut - pd_


def flip_to(df: pl.DataFrame, i: int, g: str) -> pl.DataFrame:
    """Row i given the grade g with its recommendation and rate."""
    return setc(setc(setc(df, i, "risk_grade", g), i, "recommendation", C.GRADE_TERMS[g][0]), i, "interest_rate", C.GRADE_TERMS[g][1])


def rescore(df: pl.DataFrame, pds: list[float]) -> pl.DataFrame:
    """Rewrite pd and everything the corrected SAS derives from it, consistently (like a port would)."""
    score = [C.sas_best12(600 + 250 * (1 - p)) for p in pds]
    tup = [C.sas_grade(p) for p in pds]
    upd = {"pd_logistic": [C.sas_best12(p) for p in pds], "credit_risk_score": score,
           "risk_grade": [t[0] for t in tup], "recommendation": [t[1] for t in tup], "interest_rate": [t[2] for t in tup]}
    if "pred_logistic" in df.columns:
        upd["pred_logistic"] = ["1" if p >= 0.5 else "0" for p in pds]
    return df.with_columns([pl.Series(k, v, dtype=pl.Utf8) for k, v in upd.items()])


def cases():
    rs, ft, co, ms = load(RS), load(FT), load(CO), load(MS)
    kg, st, da, ta = load(KG), load(ST), load(DA), load(TA)
    hl, hp, fs, ct, pm = load(HL), load(HP), load(FS), load(CT), load(PM)
    pd_ = rs.get_column("pd_logistic").cast(pl.Float64).to_list()
    far = next(i for i, p in enumerate(pd_) if abs(cut_gap(p)) > 0.01)  # far from every grade cut (and from 0.5)
    near = next(i for i, p in enumerate(pd_) if 1e-6 < cut_gap(p) <= C.PD_TOL / 2)  # just below a cut, can cross it
    zero_flag = rs.get_column("default_flag").to_list().index("0")
    zero_util = rs.get_column("credit_utilization").to_list().index("0")
    PDv = rs["pd_logistic"][far]

    # (name, file judged, {file: candidate df or raw bytes}, expected failed tags, strict passes?, excused)
    # expected failed tags: a frozenset = exactly these; a tuple ("atleast", {...}) = these and maybe more
    yield "identical", RS, {RS: rs}, PASS, True, {}
    yield "rows reordered", RS, {RS: rs.reverse()}, PASS, True, {}
    # positive control: a correct port (fully converged refit, SAS rules applied)
    conv = {f: C.read_text_csv(CONV / f) for f in (RS, RV, FM)}
    yield "CONVERGED REFIT = correct port (train)", RS, conv, PASS, False, CONV_TRAIN
    yield "CONVERGED REFIT = correct port (valid)", RV, conv, PASS, False, CONV_VALID
    yield "CONVERGED REFIT = correct port (final)", FM, conv, PASS, False, CONV_TRAIN
    # pd value / distribution / format
    # a pd changed alone leaves the score that is not its own pd's formula: both rules speak
    yield "pd +2e-4 alone (beyond PD_TOL)", RS, {RS: setc(rs, far, "pd_logistic", b12(PDv, 2e-4))}, {"pd_logistic", "credit_risk_score"}, False, {}
    yield "pd +5e-5 alone (score not its formula)", RS, {RS: setc(rs, far, "pd_logistic", b12(PDv, 5e-5))}, {"credit_risk_score"}, False, {}
    one = lambda d: pl.concat([rs.slice(0, far), rescore(rs.slice(far, 1), [pd_[far] + d]), rs.slice(far + 1)])
    yield "pd +5e-5 one row, rescored (within PD_TOL)", RS, {RS: one(5e-5)}, PASS, False, {}
    yield "pd +2e-4 one row, rescored (beyond PD_TOL)", RS, {RS: one(2e-4)}, {"pd_logistic", "credit_risk_score"}, False, {}
    bias = rescore(rs, [p + 5e-5 for p in pd_])
    yield "C/D2: +5e-5 bias on every pd, rescored", RS, {RS: bias}, ("atleast", {"pd_logistic(mean)"}), False, None
    pd4 = rs.with_columns(pl.Series("pd_logistic", [f"{p:.4f}" for p in pd_], dtype=pl.Utf8))
    yield "C/D3: pd printed %.4f", RS, {RS: pd4}, ("atleast", {"pd_logistic"}), False, None
    yield "C/D4: pd in E-notation", RS, {RS: setc(rs, far, "pd_logistic", f"{float(PDv):.9E}")}, {"pd_logistic"}, False, {}
    yield "pd 'nan'", RS, {RS: setc(rs, far, "pd_logistic", "nan")}, {"pd_logistic", "credit_risk_score"} | TUPLE, False, {}
    yield "pd missing", RS, {RS: setc(rs, far, "pd_logistic", "")}, {"pd_logistic", "credit_risk_score"} | TUPLE, False, {}
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
    # the score: within 250 * PD_TOL of the reference AND 600 + 250 * (1 - candidate pd) (Q15, 2026-11-16)
    SCv = rs["credit_risk_score"][far]
    yield "score +0.01, pd unchanged (not its formula)", RS, {RS: setc(rs, far, "credit_risk_score", b12(SCv, 0.01))}, {"credit_risk_score"}, False, {}
    yield "score +1, pd unchanged", RS, {RS: setc(rs, far, "credit_risk_score", b12(SCv, 1))}, {"credit_risk_score"}, False, {}
    yield "score +1e-8 (one printed unit)", RS, {RS: setc(rs, far, "credit_risk_score", b12(SCv, 1e-8))}, PASS, False, {}
    yield "score +1e-6, pd unchanged", RS, {RS: setc(rs, far, "credit_risk_score", b12(SCv, 1e-6))}, {"credit_risk_score"}, False, {}
    yield "score rounded to an integer", RS, {RS: setc(rs, far, "credit_risk_score", str(round(float(SCv))))}, {"credit_risk_score"}, False, {}
    yield "score with extra digits", RS, {RS: setc(rs, far, "credit_risk_score", SCv + "1")}, {"credit_risk_score"}, False, {}
    yield "score missing", RS, {RS: setc(rs, far, "credit_risk_score", "")}, {"credit_risk_score"}, False, {}
    # review of 2026-11-16 (s03, s24, s25): a '%' after the score
    pct = lambda df: df.with_columns((pl.col("credit_risk_score") + "%").alias("credit_risk_score"))
    yield "review s03: every score with a '%'", RS, {RS: pct(rs)}, {"credit_risk_score"}, False, {}
    yield "review s02: one score with a '%'", RS, {RS: setc(rs, far, "credit_risk_score", SCv + "%")}, {"credit_risk_score"}, False, {}
    yield "review s24: every score with a '%' (final)", FM, {FM: pct(load(FM))}, {"credit_risk_score"}, False, {}
    yield "review s25: every score with a '%' (test)", TP, {TP: pct(load(TP))}, {"credit_risk_score"}, False, {}
    yield "score with a leading blank", RS, {RS: setc(rs, far, "credit_risk_score", " " + SCv)}, {"credit_risk_score"}, False, {}
    d1 = rescore(rs, [round(p, 4) for p in pd_]).with_columns(rs["pd_logistic"])
    yield "C/D1: scores from pd rounded to 4dp, pd exact", RS, {RS: d1}, ("atleast", {"credit_risk_score"}), False, None
    old = rs.with_columns(pl.Series("credit_risk_score", [str(round(float(x))) for x in rs["credit_risk_score"].to_list()], dtype=pl.Utf8))
    yield "every score rounded (the uncorrected SAS)", RS, {RS: old}, {"credit_risk_score"}, False, {}
    # grade, recommendation, rate: excused only near a cut AND as SAS grades the candidate's own pd (Q18)
    p_up = pd_[near] + cut_gap(pd_[near]) + 1e-9  # just crosses the grade cut
    legit = pl.concat([rs.slice(0, near), rescore(rs.slice(near, 1), [p_up]), rs.slice(near + 1)])
    moved = {c: 1 for c in C.GRADE_TUPLE if legit[c][near] != rs[c][near]}
    yield "legit flip: pd crosses a grade cut, rescored", RS, {RS: legit}, PASS, False, moved
    # review of 2026-11-16 (g08): the pd crosses the cut and the grade stays: equal to the reference, wrong for its own pd
    stay = legit
    for c in C.GRADE_TUPLE:
        stay = setc(stay, near, c, rs[c][near])
    yield "review g08: pd crossed a cut, grade not moved", RS, {RS: stay}, set(moved), False, {}
    # review of 2026-11-16 (g07, g10): a pd exactly on a cut gives a whole-number score; a correct port prints it so
    at = lambda cut: min((i for i, p in enumerate(pd_) if 0 < cut - p <= C.PD_TOL), key=lambda i: cut - pd_[i])
    i10, i50 = at(0.10), at(0.50)
    on10 = pl.concat([rs.slice(0, i10), rescore(rs.slice(i10, 1), [0.10]), rs.slice(i10 + 1)])
    yield "review g07: pd exactly 0.10, graded B, score 825", RS, {RS: on10}, PASS, False, {"risk_grade": 1, "interest_rate": 1}
    on50 = pl.concat([rs.slice(0, i50), rescore(rs.slice(i50, 1), [0.50]), rs.slice(i50 + 1)])
    yield "review g10: pd exactly 0.50, still E, score 725", RS, {RS: on50}, PASS, False, {"pred_logistic": 1}
    # a pd printed as 0.5 may be 0.50000000001: F is then right, and the print cannot tell (one unit either side)
    yield "pd printed 0.5, graded F", RS, {RS: flip_to(on50, i50, "F")}, PASS, False, {"risk_grade": 1, "interest_rate": 1, "pred_logistic": 1}
    below = pl.concat([rs.slice(0, i50), rescore(rs.slice(i50, 1), [0.49999]), rs.slice(i50 + 1)])
    yield "pd 0.49999 graded F", RS, {RS: flip_to(below, i50, "F")}, TUPLE - {"recommendation"}, False, {}
    flip = lambda df, i, g: setc(setc(setc(df, i, "risk_grade", g), i, "recommendation", C.GRADE_TERMS[g][0]), i, "interest_rate", C.GRADE_TERMS[g][1])
    other = C.sas_grade(p_up)[0]
    yield "grade flipped at a cut but pd unchanged", RS, {RS: flip(rs, near, other)}, set(moved), False, {}
    far_other = "C" if rs["risk_grade"][far] != "C" else "D"
    yield "grade flip far from a cut (whole tuple)", RS, {RS: flip(rs, far, far_other)}, {"risk_grade", "recommendation", "interest_rate"}, False, {}
    p_far = pd_[far] + 5e-5
    far_flip = pl.concat([rs.slice(0, far), flip(rescore(rs.slice(far, 1), [p_far]), 0, far_other), rs.slice(far + 1)])
    yield "grade flip far from a cut, pd moved 5e-5", RS, {RS: far_flip}, {"risk_grade", "recommendation", "interest_rate"}, False, {}
    wrong_rate = setc(legit, near, "interest_rate", "20.00%")
    yield "legit flip but rate of another grade", RS, {RS: wrong_rate}, {"interest_rate"} | (set(moved) - {"interest_rate"}), False, {}
    garbage = setc(setc(rs, near, "credit_risk_score", "-999"), near, "risk_grade", "Z")
    yield "near a cut, garbage score+grade", RS, {RS: garbage}, {"credit_risk_score", "risk_grade"}, False, {}
    cutoff = rs.with_columns(pl.Series("risk_grade", [C.sas_grade(p + 0.01)[0] for p in pd_], dtype=pl.Utf8))
    yield "every grade cut 1 point lower (mutated cut)", RS, {RS: cutoff}, {"risk_grade"}, False, None
    yield "pred_logistic '7'", RS, {RS: setc(rs, far, "pred_logistic", "7")}, {"pred_logistic"}, False, {}
    yield "rate '5.0%'", RS, {RS: setc(rs, far, "interest_rate", "5.0%")}, {"interest_rate"}, False, {}
    # model-fit tables (review B2/B5/C5)
    est = co["Estimate"][1]  # five decimals, e.g. '-0.00084'
    yield "coef Estimate +2 DU", CO, {CO: setc(co, 1, "Estimate", f"{float(est) + 2e-5:.5f}")}, PASS, False, {}
    yield "coef Estimate +3 DU", CO, {CO: setc(co, 1, "Estimate", f"{float(est) + 3e-5:.5f}")}, {"Estimate"}, False, {}
    w = co["WaldChiSq"][3]
    yield "coef WaldChiSq +0.05%", CO, {CO: setc(co, 3, "WaldChiSq", f"{float(w) * 1.0005:.4f}")}, PASS, False, {}
    yield "coef WaldChiSq +0.5%", CO, {CO: setc(co, 3, "WaldChiSq", f"{float(w) * 1.005:.4f}")}, {"WaldChiSq"}, False, {}
    yield "coef DF 1->2", CO, {CO: setc(co, 1, "DF", "2")}, {"DF"}, False, {}
    num_p = next((i for i, v in enumerate(co["ProbChiSq"].to_list()) if not v.startswith("<")), None)
    if num_p is not None:  # a coefficient whose p-value is printed as a number
        pv = float(co["ProbChiSq"][num_p])
        yield "p-value +1 DU", CO, {CO: setc(co, num_p, "ProbChiSq", f"{pv + 1e-4:.4f}")}, PASS, False, {}
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
    chi = float(hl["ChiSq"][0])
    yield "HL ChiSq +0.05%", HL, {HL: setc(hl, 0, "ChiSq", f"{chi * 1.0005:.4f}")}, PASS, False, {}
    yield "HL ChiSq +1", HL, {HL: setc(hl, 0, "ChiSq", f"{chi + 1:.4f}")}, {"ChiSq"}, False, {}
    yield "HL DF 8->9", HL, {HL: setc(hl, 0, "DF", "9")}, {"DF"}, False, {}
    yield "HL EventsObserved +1", HP, {HP: setc(hp, 0, "EventsObserved", str(int(hp["EventsObserved"][0]) + 1))}, PASS, False, {}
    yield "HL EventsObserved +3", HP, {HP: setc(hp, 0, "EventsObserved", str(int(hp["EventsObserved"][0]) + 3))}, {"EventsObserved"}, False, {}
    t0, t1 = int(hp["Total"][0]), int(hp["Total"][1])
    yield "C/D6: HL 10 rows moved between groups", HP, {HP: setc(setc(hp, 0, "Total", str(t0 + 10)), 1, "Total", str(t1 - 10))}, {"Total"}, False, {}
    # Q2 (2026-11-05): HL Totals within 2 (a converged port moves block-boundary rows: 6 Totals by 1)
    yield "Q2: HL 1 row moved between groups", HP, {HP: setc(setc(hp, 0, "Total", str(t0 + 1)), 1, "Total", str(t1 - 1))}, PASS, False, {}
    yield "Q2: HL Total +3", HP, {HP: setc(hp, 0, "Total", str(t0 + 3))}, {"Total"}, False, {}
    c0, c1 = int(ct["COUNT"][0]), int(ct["COUNT"][1])
    yield "C/D6: confusion row moved, no flips", CT, {CT: setc(setc(ct, 0, "COUNT", str(c0 - 1)), 1, "COUNT", str(c1 + 1))}, {"COUNT"}, False, {}
    # metrics and summaries
    yield "decile defaults +1", DA, {DA: setc(da, 0, "defaults", str(int(da["defaults"][0]) + 1))}, {"defaults"}, False, {}
    dr = da["default_rate"][0].rstrip("%")
    yield "decile default_rate +1 DU", DA, {DA: setc(da, 0, "default_rate", f"{float(dr) + 0.01:.2f}%")}, PASS, False, {}
    yield "decile default_rate no '%'", DA, {DA: setc(da, 0, "default_rate", dr)}, {"default_rate"}, False, {}
    yield "C/D4: default_rate percent8.3", DA, {DA: setc(da, 0, "default_rate", dr + "0%")}, {"default_rate"}, False, {}
    yield "C/D4: Train_AUC printed 8.5", MS, {MS: setc(setc(ms, 0, "Train_AUC", ms["Train_AUC"][0] + "0"), 0, "training_date", TODAY)}, {"Train_AUC"}, False, {}
    msd = setc(ms, 0, "training_date", TODAY)
    yield "summary training_records +1", MS, {MS: setc(msd, 0, "training_records", "105001")}, {"training_records"}, False, {}
    vp = float(ms["valid_precision"][0])
    yield "summary valid_precision +1 DU", MS, {MS: setc(msd, 0, "valid_precision", f"{vp + 1e-4:.4f}")}, PASS, False, {}
    yield "summary valid_precision +2 DU, no flips", MS, {MS: setc(msd, 0, "valid_precision", f"{vp + 2e-4:.4f}")}, {"valid_precision"}, False, {}
    yield "C/D5: train_accuracy +8e-4, no flips", MS, {MS: setc(msd, 0, "train_accuracy", f"{float(ms['train_accuracy'][0]) + 8e-4:.4f}")}, {"train_accuracy"}, False, {}
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
    # 2026-11-16: classification counts within 1; the percentages keep the model rule
    pc = load(PC)
    row = next(i for i, v in enumerate(pc["CorrectEvents"].to_list()) if 100 < int(v) < 1000)
    ce, ie = int(pc["CorrectEvents"][row]), int(pc["IncorrectNonevents"][row])
    yield "classification: one applicant moved", PC, {PC: setc(setc(pc, row, "CorrectEvents", str(ce + 1)), row, "IncorrectNonevents", str(ie - 1))}, PASS, False, {}
    yield "classification: CorrectEvents +2", PC, {PC: setc(pc, row, "CorrectEvents", str(ce + 2))}, {"CorrectEvents", "counts"}, False, {}
    big = int(pc["CorrectNonevents"][row])
    yield "classification: large count +2", PC, {PC: setc(pc, row, "CorrectNonevents", str(big + 2))}, {"CorrectNonevents", "counts"}, False, {}
    yield "classification: count '308.0'", PC, {PC: setc(pc, row, "CorrectEvents", f"{ce}.0")}, {"CorrectEvents", "counts"}, False, {}
    # review of 2026-11-16 (c01, c02): an applicant moves between the four counts, none is added or lost
    plus = pc
    for col in C.CLASSIFICATION_COUNTS:
        plus = setc(plus, row, col, str(int(pc[col][row]) + 1))
    yield "review c01: all four counts +1 in a row", PC, {PC: plus}, {"counts"}, False, {}
    zrow, zcol = next((i, col) for col in C.CLASSIFICATION_COUNTS for i, v in enumerate(pc[col].to_list()) if v == "0")
    yield "review c02: a count of 0 -> -1", PC, {PC: setc(pc, zrow, zcol, "-1")}, {zcol, "counts"}, False, {}
    two = setc(setc(pc, row, "CorrectEvents", str(ce + 2)), row, "IncorrectNonevents", str(ie - 2))
    yield "classification: two applicants moved", PC, {PC: two}, {"CorrectEvents", "IncorrectNonevents"}, False, {}
    yield "classification: Sensitivity +1.0", PC, {PC: setc(pc, row, "Sensitivity", f"{float(pc['Sensitivity'][row]) + 1:.1f}")}, {"Sensitivity"}, False, {}
    # 2026-11-16: income_medians.csv is judged in the fe stage
    im = load(IM)
    yield "income medians identical", IM, {IM: im}, PASS, True, {}
    yield "income medians: one median +1", IM, {IM: setc(im, 0, "median_income", str(int(im["median_income"][0]) + 1))}, {"median_income", "raw"}, False, {}
    yield "income medians: overall median +0.5", IM, {IM: im.with_columns(pl.lit("5400.5").alias("overall_median_income"))}, {"overall_median_income", "raw"}, False, {}
    yield "income medians: no overall column", IM, {IM: im.drop("overall_median_income")}, {"columns", "raw"}, False, {}
    yield "income medians: age group missing", IM, {IM: im.slice(1)}, {"rows", "keys", "raw"}, False, {}
    # review of 2026-11-16 (i02, i03, i04, i18, i22): the medians file is the reference's bytes
    imb = (REF / IM).read_bytes()
    head, *body = imb.splitlines(keepends=True)
    yield "review i02: income medians rows reversed", IM, {IM: head + b"".join(reversed(body))}, {"raw"}, True, {}
    yield "review i03: income medians CRLF", IM, {IM: imb.replace(b"\n", b"\r\n")}, {"raw"}, False, {}
    yield "review i04: income medians quoted fields", IM, {IM: imb.replace(b"age_group", b'"age_group"')}, {"raw"}, False, {}
    yield "review i18: income medians no final newline", IM, {IM: imb.rstrip(b"\n")}, {"raw"}, False, {}
    yield "review i22: income medians with a BOM", IM, {IM: b"\xef\xbb\xbf" + imb}, ("atleast", {"raw"}), False, None
    # Q1 (2026-11-05): Percent Tied absolute 1e-5 percentage points; other cells keep the model rule
    asc = load(AS)
    tied, conc, tau = float(asc["nValue1"][2]), float(asc["nValue1"][0]), float(asc["nValue2"][2])
    yield "Q1: Percent Tied +5e-6 pp (a converged port's ties)", AS, {AS: setc(asc, 2, "nValue1", f"{tied + 5e-6:.6f}")}, PASS, False, {}
    yield "Q1: Percent Tied +2e-5 pp", AS, {AS: setc(asc, 2, "nValue1", f"{tied + 2e-5:.6f}")}, {"nValue1"}, False, {}
    yield "Q1: Percent Concordant off by 0.2", AS, {AS: setc(asc, 0, "nValue1", f"{conc + 0.2:.6f}")}, {"nValue1"}, False, {}
    yield "Q1: Tau-a +1e-4 (not the tied cell)", AS, {AS: setc(asc, 2, "nValue2", f"{tau + 1e-4:.6f}")}, {"nValue2"}, False, {}


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
