"""Checks of credit_risk/sas_compat.py against SAS's own outputs (judge/reference, judge/scenarios).
Run from the repo root:  uv run python migration/stress-test/sas_compat_checks.py
One PASS/FAIL line per check, with counts. Exit code 1 if any check fails."""

from __future__ import annotations

import csv
import glob
import math
import re
import sys
import tempfile
from collections import Counter
from collections.abc import Callable
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[2]
JUDGE = ROOT / "judge"
REF = JUDGE / "reference"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(JUDGE))

import compare  # noqa: E402  (judge/compare.py: tolerances and compare_file)

from credit_risk import sas_compat as sc  # noqa: E402

RESULTS: list[tuple[str, bool, str]] = []
TMP = Path(tempfile.mkdtemp(prefix="sas_compat_checks_"))


def report(name: str, ok: bool, detail: str) -> None:
    RESULTS.append((name, ok, detail))
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}", flush=True)


def counted(name: str, bad: list[str], total: int, what: str = "cells") -> None:
    detail = f"{total - len(bad)}/{total} {what}"
    if bad:
        detail += "; e.g. " + " | ".join(bad[:4])
    report(name, not bad, detail)


def judge_file(name: str, ref: Path, cand: Path, mode: str = "port") -> None:
    res = compare.compare_file(name, ref, cand, mode)
    detail = f"judge {mode}-mode compare_file {res.status}"
    if res.excused:
        detail += f", excused {res.excused}"
    if res.problems:
        detail += "; " + "; ".join(res.problems)[:300]
    report(f"{name} vs reference ({ref.parent.name}, {mode})", res.status == "PASS", detail)


NUM = re.compile(r"^-?(\d+\.?\d*|\.\d+)(E-?\d+)?$")


# ------------------------------------------------------------- formatting -----
def check_best12() -> None:
    bad: list[str] = []
    total = 0
    n_e = 0
    for f in sorted(glob.glob(str(REF / "**" / "*.csv"), recursive=True)):
        name = Path(f).name
        if name in compare.MODEL_STAT_FILES:
            continue
        rows = list(csv.reader(open(f, newline="")))
        fmtcols = compare.FORMATTED.get(name, set())
        hdr = rows[0]
        for r in rows[1:]:
            for h, v in zip(hdr, r, strict=True):
                if h in fmtcols or not NUM.match(v):
                    continue
                total += 1
                n_e += "E" in v
                if sc.sas_best12(float(v)) != v:
                    bad.append(f"{Path(f).relative_to(REF)}:{h} ref={v} got={sc.sas_best12(float(v))}")
    counted("sas_best12 unformatted numeric cells", bad, total)
    report("sas_best12 E-notation cells exercised", n_e > 0, f"{n_e} E-notation cells in the reference")


def check_best_small() -> None:
    cases = [
        (0.0666666666, 8, "0.066667"),
        (1 / 3, 8, "0.333333"),
        (123456789.0, 8, "1.2346E8"),
        (61728395.0, 8, "61728395"),
        (7000.0, 8, "7000"),
        (9.670322e-6, 12, "9.670322E-6"),
        (-9.670322e-6, 12, "-9.670322E-6"),
        (0.0, 12, "0"),
        (-0.0, 12, "0"),
        (28.0, 12, "28"),
        (174544.687515, 12, "174544.68752"),
    ]
    bad = [f"best({x},{w})={sc.sas_best(x, w)!r} want {t!r}" for x, w, t in cases if sc.sas_best(x, w) != t]
    bad += [] if sc.sas_best(None, 12) == "" else ["None"]
    counted("sas_best BEST8./E-notation/zero (X03, A9, A15)", bad, len(cases) + 1, "cases")


def check_percent_wd() -> None:
    bad: list[str] = []
    total = 0
    # percent8.2: interest_rate in every risk_scores file
    for f in sorted(glob.glob(str(REF / "**" / "risk_scores_*.csv"), recursive=True)):
        col = pl.read_csv(f, infer_schema=False).get_column("interest_rate").unique().to_list()
        for v in col:
            total += 1
            if sc.fmt_percent(float(v[:-1]) / 100, 8, 2) != v:
                bad.append(f"{v}")
    for v in ("5.00%", "7.00%", "9.00%", "12.00%", "100.0%"):
        total += 1
        x = float(v[:-1]) / 100
        if sc.fmt_percent(x, 8, 2) != v:
            bad.append(f"percent {v}->{sc.fmt_percent(x, 8, 2)}")
    # percent8.2 / 8.2 from the integer counts of printed_cumulative_lift
    dirs = [REF] + [REF / "scenarios" / f"edge_metrics_{x}" for x in "abc"]
    for d in dirs:
        rows = list(csv.DictReader(open(d / "printed_cumulative_lift.csv")))
        big_d = sum(int(r["defaults"]) for r in rows)
        big_n = sum(int(r["total_count"]) for r in rows)
        overall = float(sc.sas_best(big_d / big_n, 8))  # A9: the INTO text
        cd = cc = 0
        for r in rows:
            k, n = int(r["defaults"]), int(r["total_count"])
            cd += k
            cc += n
            rate = k / n
            want = {
                "default_rate": sc.fmt_percent(rate, 8, 2),
                "capture_rate": sc.fmt_percent(k / big_d, 8, 2),
                "cum_capture_rate": sc.fmt_percent(cd / big_d, 8, 2),
                "lift": sc.fmt_wd(rate / overall, 8, 2),
                "cum_lift": sc.fmt_wd((cd / cc) / overall, 8, 2),
            }
            for col, got in want.items():
                total += 1
                if got != r[col]:
                    bad.append(f"{d.name} d{r['decile']} {col} ref={r[col]} got={got}")
    counted("fmt_percent percent8.2 and fmt_wd 8.2 (A14, A24)", bad, total)


def metrics_inputs() -> list[tuple[str, Path, Path]]:
    out = [("real", REF / "risk_scores_validation.csv", REF)]
    for x in "abc":
        out.append((f"edge_{x}", JUDGE / "scenarios" / f"edge_metrics_{x}" / "risk_scores_validation.csv",
                    REF / "scenarios" / f"edge_metrics_{x}"))
    return [(a, b, c) for a, b, c in out]


def check_rank_and_wd84() -> None:
    bad_cnt: list[str] = []
    bad_fmt: list[str] = []
    bad_cal: list[str] = []
    n_cnt = n_fmt = n_cal = 0
    for tag, src, refdir in metrics_inputs():
        d = sc.proc_import_csv(src, 20).select("default_flag", "pd_logistic")
        dec = sc.proc_rank_groups(d["pd_logistic"], 10, descending=True) + 1
        g = (
            d.with_columns(decile=dec)
            .group_by("decile", maintain_order=True)
            .agg(
                n=pl.len(),
                k=pl.col("default_flag").sum(),
                s=pl.col("pd_logistic").sum(),
                lo=pl.col("pd_logistic").min(),
                hi=pl.col("pd_logistic").max(),
            )
            .sort("decile")
        )
        ref = pl.read_csv(refdir / "decile_analysis.csv", infer_schema=False)
        n_cnt += ref.height
        if g.height != ref.height:
            bad_cnt.append(f"{tag}: {g.height} deciles vs {ref.height}")
            continue
        for r, a in zip(ref.iter_rows(named=True), g.iter_rows(named=True), strict=True):
            if int(r["decile"]) != a["decile"] or int(r["total_count"]) != a["n"] or int(r["defaults"]) != a["k"]:
                bad_cnt.append(f"{tag} decile {r['decile']}: ref {r['total_count']}/{r['defaults']} got {a['n']}/{a['k']}")
            for col, val in (("avg_pd", a["s"] / a["n"]), ("min_pd", a["lo"]), ("max_pd", a["hi"])):
                n_fmt += 1
                if sc.fmt_wd(val, 8, 4) != r[col]:
                    bad_fmt.append(f"{tag} d{r['decile']} {col} ref={r[col]} got={sc.fmt_wd(val, 8, 4)}")
        cal = d.with_columns(b=sc.proc_rank_groups(d["pd_logistic"], 20))
        cg = cal.group_by("b", maintain_order=True).agg(
            n=pl.len(), sp=pl.col("pd_logistic").sum(), sd=pl.col("default_flag").sum()
        ).sort("b")
        cref = pl.read_csv(refdir / "calibration_plot.csv", infer_schema=False)
        n_cal += cref.height
        if cg.height != cref.height:
            bad_cal.append(f"{tag}: {cg.height} bins vs {cref.height}")
            continue
        for r, a in zip(cref.iter_rows(named=True), cg.iter_rows(named=True), strict=True):
            got = (str(a["b"]), sc.fmt_wd(a["sp"] / a["n"], 8, 4), sc.fmt_wd(a["sd"] / a["n"], 8, 4), str(a["n"]))
            want = (r["pred_bin"], r["mean_predicted"], r["mean_actual"], r["bin_count"])
            if got != want:
                bad_cal.append(f"{tag} {want} vs {got}")
    counted("proc_rank_groups decile counts (real + edge a/b/c)", bad_cnt, n_cnt, "deciles")
    counted("proc_rank_groups groups=20 calibration bins (real + edge a/b/c)", bad_cal, n_cal, "bins")
    counted("fmt_wd 8.4 avg/min/max pd per decile", bad_fmt, n_fmt)


# ------------------------------------------------------------------ import -----
def check_import() -> None:
    bad: list[str] = []
    total = 0
    for log in sorted((REF / "listings").glob("*.log")):
        text = log.read_text()
        starts = [m for m in re.finditer(r'proc import datafile="&(data_path|output_path)/([^"]+)"', text)]
        for i, m in enumerate(starts):
            end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
            seg = text[m.start() : end]
            inf = re.findall(r'informat\s+("?)([^"\s]+)\1(?:N)?\s+(best32\.|\$(\d+)\.)\s*;', seg)
            if not inf:
                continue
            gr = re.search(r"guessingrows=(\w+)", seg)
            guess = None if gr and gr.group(1).lower() == "max" else (int(gr.group(1)) if gr else 20)
            base = ROOT / "data" if m.group(1) == "data_path" else REF
            df = sc.proc_import_csv(base / m.group(2), guess)
            total += len(inf)
            if df.columns != [x[1] for x in inf]:
                bad.append(f"{log.name}:{m.group(2)} names {df.columns[:3]} vs {[x[1] for x in inf][:3]}")
                continue
            for (_, nm, kind, width), col in zip(inf, df.iter_columns(), strict=True):
                if kind == "best32.":
                    ok = col.dtype == pl.Float64
                else:
                    mx = col.drop_nulls().str.len_chars().max()
                    ok = col.dtype == pl.String and (mx == int(width) or (mx is None and int(width) == 1))
                if not ok:
                    bad.append(f"{log.name}:{m.group(2)}:{nm} want {kind} got {col.dtype}")
    counted("proc_import_csv informats of the four listings logs", bad, total, "columns")

    raw = pl.read_csv(ROOT / "data" / "cs-training.csv", infer_schema=False)
    imp = sc.proc_import_csv(ROOT / "data" / "cs-training.csv", 20)
    mi_raw = raw.get_column("MonthlyIncome").drop_nulls()
    n_long = int((mi_raw.str.len_chars() > 5).sum())
    mi = imp.get_column("MonthlyIncome")
    n_trunc = int((raw.get_column("MonthlyIncome") != mi).fill_null(False).sum())
    ok_trunc = mi.drop_nulls().str.len_chars().max() == 5 and n_trunc == n_long == 77
    report("proc_import_csv 77 truncated MonthlyIncome values", ok_trunc, f"raw >5 chars: {n_long}, changed by import: {n_trunc}")
    ref = pl.read_csv(REF / "model_features_train.csv", infer_schema=False)
    j = (
        ref.select("row_id", "monthly_income")
        .join(imp.select(pl.col("VAR1").cast(pl.Int64).cast(pl.String).alias("row_id"), "MonthlyIncome"), on="row_id")
        .filter(pl.col("MonthlyIncome").str.len_chars() == 5)
        .join(
            raw.select(pl.col("").alias("row_id"), pl.col("MonthlyIncome").alias("raw_mi")).filter(
                pl.col("raw_mi").str.len_chars() > 5
            ),
            on="row_id",
        )
    )
    badm = [
        f"row {r['row_id']} ref={r['monthly_income']} import={r['MonthlyIncome']}"
        for r in j.iter_rows(named=True)
        if float(r["monthly_income"]) != float(r["MonthlyIncome"])
    ]
    counted("truncated incomes equal reference model_features monthly_income (train rows)", badm, j.height, "rows")
    ti = sc.proc_import_csv(REF / "model_features_train.csv", None)
    report("proc_import_csv guessingrows=None: 42 numeric columns", ti.width == 42 and all(t == pl.Float64 for t in ti.dtypes), f"{ti.width} columns, dtypes {set(ti.dtypes)}")


# --------------------------------------------------------------- expressions -----
def one(e: pl.Expr) -> object:
    return pl.select(e.alias("v")).item()


def nul() -> pl.Expr:
    return pl.lit(None, dtype=pl.Float64)


def check_edge_cases() -> None:
    cases: list[tuple[str, object, object]] = [
        ("sum(.,1)=1", one(sc.sas_sum(nul(), pl.lit(1.0))), 1.0),
        ("sum(.,.)=.", one(sc.sas_sum(nul(), nul())), None),
        ("sum(2,3)=5", one(sc.sas_sum(pl.lit(2.0), pl.lit(3.0))), 5.0),
        ("min(.,200)=200", one(sc.sas_min(nul(), 200)), 200.0),
        ("max(.,200)=200", one(sc.sas_max(nul(), 200)), 200.0),
        ("min(.,.)=.", one(sc.sas_min(nul(), nul())), None),
        ("log(0)=.", one(sc.sas_log(pl.lit(0.0))), None),
        ("log(-1)=.", one(sc.sas_log(pl.lit(-1.0))), None),
        ("log(.)=.", one(sc.sas_log(nul())), None),
        ("log(e)=1", one(sc.sas_log(pl.lit(math.e))), 1.0),
        ("input('')=.", one(sc.input_best32(pl.lit(""))), None),
        ("input('NA')=.", one(sc.input_best32(pl.lit("NA"))), None),
        ("input('15979')=15979", one(sc.input_best32(pl.lit("15979"))), 15979.0),
        ("input('9.670322E-6')", one(sc.input_best32(pl.lit("9.670322E-6"))), 9.670322e-6),
        ("input('nan')=.", one(sc.input_best32(pl.lit("nan"))), None),
        ("lt(.,2500)=true", one(sc.lt(nul(), 2500)), True),
        ("gt(.,30)=false", one(sc.gt(nul(), 30)), False),
        ("le(.,0)=true", one(sc.le(nul(), 0)), True),
        ("ge(.,0)=false", one(sc.ge(nul(), 0)), False),
        ("eq(.,.)=true", one(sc.eq(nul(), nul())), True),
        ("eq(.,1)=false", one(sc.eq(nul(), 1)), False),
        ("lt(3,2500)=true", one(sc.lt(pl.lit(3.0), 2500)), True),
        ("gt(3000,2500)=true", one(sc.gt(pl.lit(3000.0), 2500)), True),
        ("flag(null)=0", one(sc.flag(pl.lit(None, dtype=pl.Boolean))), 0),
        ("flag(true)=1", one(sc.flag(pl.lit(True))), 1),
        ("div(1,0)=.", one(sc.div(1, 0)), None),
        ("div(.,2)=.", one(sc.div(nul(), 2)), None),
        ("div(1,.)=.", one(sc.div(1, nul())), None),
        ("div(1,4)=0.25", one(sc.div(1, 4)), 0.25),
        ("round(2.5)=3", one(sc.sas_round(pl.lit(2.5))), 3.0),
        ("round(-2.5)=-3", one(sc.sas_round(pl.lit(-2.5))), -3.0),
        ("round(.)=.", one(sc.sas_round(nul())), None),
        ("round_scalar(0.5)=1", sc.sas_round_scalar(0.5), 1.0),
        ("round_scalar(-0.5)=-1", sc.sas_round_scalar(-0.5), -1.0),
        ("date9(2026-11-05)", sc.date9(__import__("datetime").date(2026, 11, 5)), "05NOV2026"),
    ]
    bad = [f"{n}: got {g!r}" for n, g, w in cases if g != w or type(g) is not type(w)]
    counted("A31 edge cases (sum/min/max/log/input/compare/div/round/date9)", bad, len(cases), "cases")
    df = pl.DataFrame({"a": [1.0, None, 3.0]})
    res = df.select(sc.lt(pl.col("a"), 2).alias("lt"), sc.gt(pl.col("a"), 2).alias("gt"))
    ok = res["lt"].to_list() == [True, True, False] and res["gt"].to_list() == [False, False, True]
    report("comparison helpers on a column are non-null Boolean", ok and res["lt"].null_count() == 0, str(res.rows()))
    # A13: aggregate divisor, same value as numpy, and PSI-style share 10500/105000 exact
    cnt = pl.DataFrame({"c": [10500.0] * 10})
    got = cnt.select(sc.div(pl.col("c"), pl.col("c").sum()).alias("p"))["p"].to_list()
    want = [float(np.divide(10500.0, 105000.0))] * 10
    report("div by aggregate divisor == np.divide (A13, psi_div.py)", got == want and want[0] == 0.1, f"{got[0]!r}")


# ----------------------------------------------------------------- procedures -----

C36 = (
    "credit_utilization_capped debt_ratio_capped num_late_30_59 num_late_60_89 num_late_90_plus "
    "total_late_payments has_delinquency has_serious_delinquency age monthly_income log_monthly_income "
    "num_credit_lines num_real_estate_loans log_num_credit_lines num_dependents income_per_dependent "
    "credit_lines_per_person flag_high_utilization flag_very_high_utilization flag_high_debt_ratio "
    "flag_very_high_debt_ratio flag_recent_late_payments flag_serious_delinquency "
    "flag_multiple_delinquencies flag_low_income flag_many_dependents flag_few_credit_lines "
    "total_risk_flags credit_util_category debt_category age_category financial_health "
    "age_income_interaction utilization_debt_interaction MonthlyIncome_missing Dependents_missing"
).split()


def write_text(df: pl.DataFrame, name: str, sub: str = "cand") -> Path:
    d = TMP / sub
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    sc.write_sas_csv(df, p)
    return p


def check_stepwise() -> sc.LogisticFit:
    feats = sc.proc_import_csv(REF / "model_features_train.csv", None)
    res = sc.stepwise_logistic(feats, "default_flag", C36)
    ref = pl.read_csv(REF / "stepwise_summary.csv", infer_schema=False).fill_null("")
    got = [((s.entered or "")[:20], (s.removed or "")[:20]) for s in res.steps]
    want = [(r["EffectEntered"], r["EffectRemoved"]) for r in ref.iter_rows(named=True)]
    bad = [f"step {i + 1}: ref {w} got {g}" for i, (g, w) in enumerate(zip(got, want, strict=False)) if g != w]
    if len(got) != len(want):
        bad.append(f"{len(got)} steps vs {len(want)}")
    counted("stepwise_logistic 24-step path (entered/removed names)", bad, len(want), "steps")
    final = res.final
    assert final is not None and res.intercept_only is not None
    report("fit_logistic converged on every step", all(s.fit.converged for s in res.steps), f"max n_iter {max(s.fit.n_iter for s in res.steps)}")
    # stepwise_summary.csv
    rows = []
    for s in res.steps:
        chi = s.score_chisq if s.entered else s.wald_chisq
        rows.append(
            [str(s.step), (s.entered or "")[:20], (s.removed or "")[:20], str(s.df), str(s.number_in_model),
             sc.fmt_wd(chi, 10, 4) if s.entered else "_", "_" if s.entered else sc.fmt_wd(chi, 10, 4), sc.sas_pvalue(s.p_value)]
        )
    cols = ["Step", "EffectEntered", "EffectRemoved", "DF", "NumberInModel", "ScoreChiSq", "WaldChiSq", "ProbChiSq"]
    for r in rows:  # entry rows: ScoreChiSq = chi, WaldChiSq = '_'; removal rows the opposite
        if r[1]:
            r[6] = "_"
        else:
            r[5] = "_"
    judge_file("stepwise_summary.csv", REF / "stepwise_summary.csv",
               write_text(pl.DataFrame(rows, schema=cols, orient="row"), "stepwise_summary.csv"))
    # model_coefficients.csv (MODEL statement order, D8., PVALUE6.4)
    sel = [c for c in C36 if c in final.names]
    idx = {n: i for i, n in enumerate(final.names)}
    crow = []
    for nm in ["Intercept", *sel]:
        i = idx[nm]
        se = math.sqrt(final.cov[i, i])
        w = final.beta[i] ** 2 / final.cov[i, i]
        crow.append([nm[:20], "1", sc.sas_d8(float(final.beta[i])), sc.sas_d8(se), sc.fmt_wd(float(w), 10, 4),
                     sc.sas_pvalue(sc.chi2_sf(float(w), 1)), "MLE"])
    judge_file("model_coefficients.csv", REF / "model_coefficients.csv",
               write_text(pl.DataFrame(crow, schema=["Variable", "DF", "Estimate", "StdErr", "WaldChiSq", "ProbChiSq", "_ESTTYPE_"], orient="row"), "model_coefficients.csv"))
    # printed_fit_statistics.csv and printed_rsquare.csv (D12.3, 9.3)
    n = feats.height
    m0 = -2 * res.intercept_only.loglik
    fs = [["0", "M2LOGL0", "-2 Log L", "=", sc.sas_d12_3(m0), sc.fmt_wd(m0, 9, 3)]]
    rs = []
    lnn = math.log(n)
    r2max = 1 - math.exp(-m0 / n)
    for s in res.steps:
        m2 = -2 * s.fit.loglik
        q = s.number_in_model
        fs += [
            [str(s.step), "AIC", "AIC", "", sc.sas_d12_3(m0 + 2), sc.fmt_wd(m2 + 2 * (q + 1), 9, 3)],
            [str(s.step), "SBC", "SC", "", sc.sas_d12_3(m0 + lnn), sc.fmt_wd(m2 + (q + 1) * lnn, 9, 3)],
            [str(s.step), "M2LOGL", "-2 Log L", "", sc.sas_d12_3(m0), sc.fmt_wd(m2, 9, 3)],
        ]
        r2 = 1 - math.exp(-(m0 - m2) / n)
        rs.append([str(s.step), "R-Square", sc.fmt_wd(r2, 6, 4), sc.sas_d12_3(r2), "Max-rescaled R-Square",
                   sc.fmt_wd(r2 / r2max, 6, 4), sc.sas_d12_3(r2 / r2max)])
    judge_file("printed_fit_statistics.csv", REF / "printed_fit_statistics.csv",
               write_text(pl.DataFrame(fs, schema=["Step", "RowId", "Criterion", "Equals", "InterceptOnly", "InterceptAndCovariates"], orient="row"), "printed_fit_statistics.csv"))
    judge_file("printed_rsquare.csv", REF / "printed_rsquare.csv",
               write_text(pl.DataFrame(rs, schema=["Step", "Label1", "cValue1", "nValue1", "Label2", "cValue2", "nValue2"], orient="row"), "printed_rsquare.csv"))
    # classification table from the converged final fit
    x = np.column_stack([np.ones(n)] + [feats[c].to_numpy().astype(np.float64) for c in final.names[1:]])
    y = feats["default_flag"].to_numpy().astype(np.float64)
    ct = sc.classification_table(y, x, final)
    exp_cols = pl.read_csv(REF / "printed_classification.csv", infer_schema=False).columns
    report("classification_table columns == printed_classification.csv header", ct.columns == exp_cols, str(ct.columns))
    pct = {c: "8.1" for c in ("Correct", "Sensitivity", "Specificity", "FalsePositive", "FalseNegative", "PPV", "NPV")}
    p = TMP / "cand" / "printed_classification.csv"
    sc.write_sas_csv(ct, p, {"ProbLevel": "8.3", **pct})
    judge_file("printed_classification.csv", REF / "printed_classification.csv", p)
    pd_conv = 1 / (1 + np.exp(-(x @ final.beta)))
    hl_and_assoc(pl.Series("y", y), pl.Series("pd", pd_conv), "converged fit")
    return final


def write_hl_assoc(y: pl.Series, pd: pl.Series, d: Path) -> tuple[pl.DataFrame, float | None, int, float | None]:
    """Render HL partition, HL chi-square and Association exactly as train does, into folder d."""
    tab, chisq, dof, pv = sc.hosmer_lemeshow(y, pd)
    sc.write_sas_csv(tab, d / "printed_hl_partition.csv", {"EventsExpected": "12.2", "NoneventsExpected": "12.2"})
    hl = pl.DataFrame([[sc.fmt_wd(chisq, 10, 4), str(dof), sc.sas_pvalue(pv), str(tab.height)]],
                      schema=["ChiSq", "DF", "ProbChiSq", "NGroups"], orient="row")
    sc.write_sas_csv(hl, d / "printed_hosmer_lemeshow.csv")
    a = sc.association_table(y, pd)
    rows = [
        ["Percent Concordant", sc.fmt_wd(a.concordant_pct, 8, 1), sc.sas_d12_3(a.concordant_pct), "Somers' D", sc.fmt_wd(a.somers_d, 8, 3), sc.sas_d12_3(a.somers_d)],
        ["Percent Discordant", sc.fmt_wd(a.discordant_pct, 8, 1), sc.sas_d12_3(a.discordant_pct), "Gamma", sc.fmt_wd(a.gamma, 8, 3), sc.sas_d12_3(a.gamma)],
        ["Percent Tied", sc.fmt_wd(a.tied_pct, 8, 1), sc.sas_d12_3(a.tied_pct), "Tau-a", sc.fmt_wd(a.tau_a, 8, 3), sc.sas_d12_3(a.tau_a)],
        ["Pairs", str(a.pairs), sc.sas_d12_3(float(a.pairs)), "c", sc.fmt_wd(a.c, 8, 3), sc.sas_d12_3(a.c)],
    ]
    sc.write_sas_csv(pl.DataFrame(rows, schema=["Label1", "cValue1", "nValue1", "Label2", "cValue2", "nValue2"], orient="row"),
                     d / "printed_association.csv")
    return tab, chisq, dof, pv


def hl_and_assoc(y: pl.Series, pd: pl.Series, tag: str, mode: str = "port") -> None:
    d = TMP / f"hl_{tag.split()[0]}_{mode}"
    d.mkdir(parents=True, exist_ok=True)
    tab, _, _, _ = write_hl_assoc(y, pd, d)
    exp_cols = pl.read_csv(REF / "printed_hl_partition.csv", infer_schema=False).columns
    report(f"hosmer_lemeshow columns == printed_hl_partition.csv header ({tag})", tab.columns == exp_cols, str(tab.columns))
    for f in ("printed_hl_partition.csv", "printed_hosmer_lemeshow.csv"):
        judge_file(f, REF / f, d / f, mode)
    # Percent Tied depends on pd at full precision; the exported risk_scores pd is BEST12, so the
    # association file is judged in port mode even for SAS's pd (documented noise, not a defect).
    judge_file("printed_association.csv", REF / "printed_association.csv", d / "printed_association.csv", "port")


def check_reference_pd_tables() -> None:
    s = sc.proc_import_csv(REF / "risk_scores_train.csv", 20)
    hl_and_assoc(s["default_flag"], s["pd_logistic"], "SAS reference pd", "strict")
    ref = pl.read_csv(REF / "printed_association.csv", infer_schema=False)
    a = sc.association_table(s["default_flag"], s["pd_logistic"])
    tied = float(ref.filter(pl.col("Label1") == "Percent Tied")["nValue1"][0])
    got = a.tied_pct if a.tied_pct is not None else float("nan")
    report("association_table Percent Tied on the reference pd", abs(got - tied) <= 1e-5, f"ref {tied} got {got:.9f}")


def check_roc() -> None:
    cases: list[tuple[str, Path, Path, str]] = [
        ("train", REF / "risk_scores_train.csv", REF / "printed_roc_train.csv", "Training Set"),
        ("valid", REF / "risk_scores_validation.csv", REF / "printed_roc_validation.csv", "Validation Set"),
        ("metrics", REF / "risk_scores_validation.csv", REF / "printed_roc_metrics.csv", "Logistic Model"),
    ]
    for x in "abc":
        cases.append((f"edge_{x}", JUDGE / "scenarios" / f"edge_metrics_{x}" / "risk_scores_validation.csv",
                      REF / "scenarios" / f"edge_metrics_{x}" / "printed_roc_metrics.csv", "Logistic Model"))
    for tag, src, ref, label in cases:
        d = sc.proc_import_csv(src, 20)
        r = sc.roc_association(d["default_flag"], d["pd_logistic"])
        vals = [r.area, r.std_err, r.lower, r.upper, r.somers_d, r.gamma, r.tau_a]
        df = pl.DataFrame([[label, *[sc.sas_d8(v) for v in vals]]],
                          schema=["ROCModel", "Area", "StdErr", "LowerArea", "UpperArea", "SomersD", "Gamma", "TauA"], orient="row")
        sub = TMP / f"roc_{tag}"
        sub.mkdir(parents=True, exist_ok=True)
        sc.write_sas_csv(df, sub / ref.name)
        judge_file(ref.name, ref, sub / ref.name, "strict")  # SAS's own pd in: exact


def check_d_formats() -> None:
    cases = [
        (sc.sas_d8(-4.16684), "-4.1668"), (sc.sas_d8(0.0025012), "0.00250"), (sc.sas_d8(6.42e-6), "6.42E-6"),
        (sc.sas_d8(0.00234), "0.00234"), (sc.sas_d8(-0.00003), "-0.00003"),
        (sc.sas_d12_3(51477.5208), "51478"), (sc.sas_d12_3(85.9220644), "85.922064"),
        (sc.sas_d12_3(0.000040773), "0.000040773"), (sc.sas_d12_3(686727936.0), "686727936"),
        (sc.sas_pvalue(0.00009), "<.0001"), (sc.sas_pvalue(0.0512), "0.0512"), (sc.sas_pvalue(1.0), "1.0000"),
        (sc.sas_pvalue(0.0001), "0.0001"),
    ]
    bad = [f"{g!r} want {w!r}" for g, w in cases if g != w]
    counted("sas_d8 / sas_d12_3 / sas_pvalue spot values from the inventory rows", bad, len(cases), "cases")


def check_writer() -> None:
    df = pl.DataFrame(
        {"a": [1.0, None, 9.670322e-6], "b": ["x,y", None, 'q"r'], "p": [0.05, 1.0, None], "i": [1, 2, 3]}
    )
    p = TMP / "w.csv"
    sc.write_sas_csv(df, p, {"p": "percent8.2"})
    want = 'a,b,p,i\n1,"x,y",5.00%,1\n,,100.0%,2\n9.670322E-6,"q""r",,3\n'
    got = p.read_bytes().decode()
    report("write_sas_csv layout (E-notation, quoting, missing, percent, LF)", got == want, repr(got) if got != want else "exact")
    pth = TMP / "i.csv"
    pth.write_text(",a b,c\n1,3,\n2,x,\n3,12345678901234567890,\n")
    imp = sc.proc_import_csv(pth, 2)
    report("proc_import_csv VAR1, text width, all-empty column", imp.columns == ["VAR1", "a b", "c"] and imp["a b"].to_list() == ["3", "x", "1"] and imp["c"].dtype == pl.String
           and imp["VAR1"].dtype == pl.Float64, f"{imp.columns} {imp['a b'].to_list()} {imp['c'].dtype}")


# ------------------------------------------- settled rules (X05) and review fixes -----
def sel_df(vals: list[object], dtype: pl.DataType | type[pl.DataType] = pl.Float64) -> pl.DataFrame:
    return pl.DataFrame({"x": vals}, schema={"x": dtype})


def check_x05_scalars() -> None:
    r = sc.sas_round_scalar
    rounds = [
        (2.4999999999999996, 3.0), (2.49999999999999, 3.0), (2.4999999999, 2.0), (712.49999999999989, 713.0),
        (-2.5, -3.0), (-2.4999999999999996, -3.0), (4503599627370497.0, 4503599627370497.0), (-0.4, 0.0), (0.5, 1.0),
    ]
    bad = [f"round({x})={r(x)} want {w}" for x, w in rounds if r(x) != w or math.copysign(1.0, r(x)) < 0 < w]
    bad += [f"expr round({x})" for x, w in rounds if one(sc.sas_round(pl.lit(x))) != w]
    bad += [] if math.copysign(1.0, r(-0.4)) > 0 else ["round(-0.4) is -0.0"]
    counted("X05 round() fuzz, 2^52 and -0.0 (scalar and expression)", bad, 2 * len(rounds) + 1, "cases")
    wd = [
        (sc.fmt_wd(-0.00001, 8, 4), "-0.0000"), (sc.fmt_wd(-0.004, 8, 2), "-0.00"), (sc.fmt_wd(0.00001, 8, 4), "0.0000"),
        (sc.fmt_wd(123456789.0, 8, 4), "1.2346E8"), (sc.fmt_wd(1e10, 8, 2), "1E10"), (sc.fmt_wd(-4.5, 8, 4), "-4.5000"),
        (sc.fmt_percent(-0.05, 8, 2), "( 5.00%)"), (sc.fmt_percent(-1.0, 8, 2), "(100.0%)"), (sc.fmt_percent(0.05, 8, 2), "5.00%"),
        (sc.sas_best(0.000015, 6), "15E-6"), (sc.sas_best(0.000015, 8), "0.000015"), (sc.sas_best(0.000015, 12), "0.000015"),
        (sc.sas_best(1.5e-5, 12), "0.000015"), (sc.sas_best(9.670322e-6, 12), "9.670322E-6"),
        (sc.sas_d8(6.321e-6), "6.321E-6"), (sc.sas_d8(6.418e-6), "6.418E-6"), (sc.sas_d8(-9.88e-6), "-9.88E-6"),
        (sc.sas_d8(123456789.0), "1.2346E8"), (sc.sas_d8(-99.99999), "-100.000"), (sc.sas_d8(0.000999999), "0.00100"),
        (sc.sas_d12_3(9999.9999996), "10000"), (sc.sas_d12_3(1e12), "1E12"),
    ]
    bad = [f"{g!r} want {w!r}" for g, w in wd if g != w]
    counted("X05 w.d sign / percent parentheses / BEST width / D8 E-notation / overflow fallback", bad, len(wd), "cases")


def check_x05_exprs() -> None:
    bad: list[str] = []
    exp_ok = [one(sc.sas_exp(pl.lit(1000.0))) is None, one(sc.sas_exp(pl.lit(709.0))) == math.exp(709.0),
              one(sc.sas_exp(nul())) is None, one(sc.sas_exp(pl.lit(0.0))) == 1.0, one(sc.sas_exp(pl.lit(-1000.0))) == 0.0]
    bad += [f"sas_exp case {i}" for i, ok in enumerate(exp_ok) if not ok]
    counted("S1 sas_exp: overflow -> missing (exp(1000) = .)", bad, len(exp_ok), "cases")
    s2 = pl.DataFrame({"t": ["1E400", "-1e999", "inf", "1", "x", None], "n": [1.5, None, float("inf"), 2.0, float("nan"), 3.0]})
    got_t = s2.select(sc.input_best32(pl.col("t")))["t"].to_list()
    got_n = s2.select(sc.input_best32(pl.col("n")))["n"].to_list()
    int_col = pl.DataFrame({"i": [1, None, 3]}).select(sc.input_best32(pl.col("i")))
    ok = (got_t == [None, None, None, 1.0, None, None] and got_n == [1.5, None, None, 2.0, None, 3.0]
          and int_col["i"].to_list() == [1.0, None, 3.0] and int_col["i"].dtype == pl.Float64)
    report("S2 input_best32: numeric column = identity cast, '1E400' / inf -> missing", ok, f"{got_t} {got_n}")
    x = [0.1 + 0.2, 1e-300, 123456789.123456789, 2.0**-1074]
    ident = pl.DataFrame({"n": x}).select(sc.input_best32(pl.col("n")))["n"].to_list() == x
    report("S2 input_best32 numeric identity is bit-exact", ident, str(x))


def check_sql_and_merge() -> None:
    df = pl.DataFrame({"g": [1, 1, 2, 2], "v": [1.0, 3.0, None, None]})
    sel = df.select(sc.sql_sum(pl.col("v")).alias("s"), sc.sql_mean(pl.col("v")).alias("m"),
                    sc.sql_min(pl.col("v")).alias("lo"), sc.sql_max(pl.col("v")).alias("hi"))
    empty = df.filter(pl.col("g") == 99).select(sc.sql_sum(pl.col("v")).alias("s"), sc.sql_mean(pl.col("v")).alias("m"),
                                                  sc.sql_min(pl.col("v")).alias("lo"), sc.sql_max(pl.col("v")).alias("hi"))
    agg = df.group_by("g", maintain_order=True).agg(sc.sql_sum(pl.col("v")), sc.sql_max(pl.col("v")).alias("hi"))
    ok = (sel.row(0) == (4.0, 2.0, 1.0, 3.0) and empty.row(0) == (None, None, None, None)
          and agg["v"].to_list() == [4.0, None] and agg["hi"].to_list() == [3.0, None])
    report("S10 sql_sum/mean/min/max: missing over 0 (or all-missing) rows, in select and agg", ok, f"{sel.row(0)} {empty.row(0)} {agg.rows()}")
    a = pl.DataFrame({"a": [1, 2, 3], "b": [10, 10, 10]})
    b = pl.DataFrame({"b": [7, 8], "c": [1.5, 2.5]})
    m = sc.merge_one_to_one(a, b)
    ok = (m.columns == ["a", "b", "c"] and m["b"].to_list() == [7, 8, None] and m["c"].to_list() == [1.5, 2.5, None]
          and m["a"].to_list() == [1, 2, 3] and sc.merge_one_to_one(a).equals(a) and sc.merge_one_to_one().is_empty())
    m3 = sc.merge_one_to_one(b, a, pl.DataFrame({"z": [True]}))
    ok = ok and m3.columns == ["b", "c", "a", "z"] and m3.height == 3 and m3["b"].to_list() == [10, 10, 10]
    report("S5 merge_one_to_one: longest frame, null padding, later same-name column overwrites (X01a, A6)", ok, f"{m.rows()} {m3.columns}")


def check_helper_names_and_agg() -> None:
    df = pl.DataFrame({"g": [1, 1, 2], "x": [1.0, 2.0, None], "y": [3.0, 4.0, 5.0]})
    helpers: dict[str, pl.Expr] = {
        "div": sc.div(pl.col("x"), 2), "sas_sum": sc.sas_sum(pl.col("x"), 1), "sas_min": sc.sas_min(pl.col("x"), 1),
        "sas_max": sc.sas_max(pl.col("x"), 1), "sas_log": sc.sas_log(pl.col("y")), "sas_exp": sc.sas_exp(pl.col("x")),
        "sas_round": sc.sas_round(pl.col("x")), "lt": sc.lt(pl.col("x"), 2), "le": sc.le(pl.col("x"), 2),
        "gt": sc.gt(pl.col("x"), 2), "ge": sc.ge(pl.col("x"), 2), "eq": sc.eq(pl.col("x"), 2),
        "flag": sc.flag(pl.col("x") > 1), "input_best32": sc.input_best32(pl.col("x")),
        "sql_sum": sc.sql_sum(pl.col("x")), "sql_mean": sc.sql_mean(pl.col("x")),
    }
    bad = [f"{k} -> {df.select(e).columns}" for k, e in helpers.items() if df.select(e).columns != ["y" if k == "sas_log" else "x"]]
    counted("A-03 every expression helper is named after its first argument", bad, len(helpers), "helpers")
    rep = df.with_columns(sc.div(pl.col("y"), 2))
    ok_rep = rep.columns == ["g", "x", "y"] and rep["y"].to_list() == [1.5, 2.0, 2.5]
    agg = df.group_by("g", maintain_order=True).agg(
        sc.div(pl.col("y").sum(), pl.col("y").count()).alias("d"), sc.sas_sum(pl.col("y").sum(), 1).alias("s"),
        sc.sas_round(pl.col("y").mean()).alias("r"), sc.div(pl.col("y"), 2).alias("elem"))
    ok_agg = (agg["d"].dtype == pl.Float64 and agg["d"].to_list() == [3.5, 5.0] and agg["s"].to_list() == [8.0, 6.0]
              and agg["r"].to_list() == [4.0, 5.0] and agg["elem"].dtype == pl.List(pl.Float64))
    report("A-03 with_columns replaces the column; helpers inside agg return a scalar per group", ok_rep and ok_agg, f"{rep.columns} {agg.dtypes}")
    cases = [sc.lt(1.0, 2), sc.sas_log(1.0), sc.sas_round(2.5), sc.le(1, 1), sc.eq(1, 1)]
    vals = [one(c) for c in cases]
    s12 = pl.select(sc.sas_sum(1, 2).alias("v"))["v"]
    report("A-16 literal first argument and sas_sum Float64", vals == [True, 0.0, 3.0, True, True] and s12.dtype == pl.Float64, f"{vals} {s12.dtype}")


def check_writer_rules() -> None:
    d = TMP / "newfolder" / "sub"
    sc.write_sas_csv(pl.DataFrame({"a": [1.0]}), d / "o.csv")
    report("S12 write_sas_csv creates the parent folder", (d / "o.csv").read_text() == "a\n1\n", str(d))
    errs = 0
    for df, fm in ((pl.DataFrame({"a": [1.0]}), {"b": "8.2"}), (pl.DataFrame({"a": ["x"]}), {"a": "percent8.2"})):
        try:
            sc.write_sas_csv(df, TMP / "e.csv", fm)
        except ValueError:
            errs += 1
    df = pl.DataFrame({"a": [0.05, 1234.5678, None], "b": [True, False, None], "t": ["ab  ", None, "c"], "n": [-0.05, 0.5, 2.0]})
    sc.write_sas_csv(df, TMP / "f.csv", {"a": "best8.", "n": "percent8.2"})
    got = (TMP / "f.csv").read_text()
    want = "a,b,t,n\n0.05,1,ab,( 5.00%)\n1234.568,0,,50.00%\n,,c,200.0%\n"
    report("A-07/A-08 writer: unknown/mismatched format raises; best8., Boolean, rstrip, negative percent", errs == 2 and got == want, repr(got))
    got2 = (TMP / "g.csv")
    sc.write_sas_csv(pl.DataFrame({"a": [7.0, -0.00001]}), got2, {"a": "8."})
    report("A-08 w. format (8.) = w.0", got2.read_text() == "a\n7\n-0\n", repr(got2.read_text()))


def check_fit_and_stepwise_edges() -> None:
    x1 = np.arange(1.0, 9.0)
    xm = np.column_stack([np.ones(8), x1])
    cases = {
        "complete separation": (xm, np.array([0, 0, 0, 0, 1, 1, 1, 1.0])),
        "quasi-complete separation": (xm, np.array([0, 0, 0, 0, 0, 1, 1, 1.0])),
        "all-zero response": (xm, np.zeros(8)),
        "collinear design": (np.column_stack([np.ones(8), x1, 2 * x1]), np.array([0, 1, 0, 1, 0, 1, 1, 0.0])),
    }
    bad: list[str] = []
    for name, (xx, yy) in cases.items():
        try:
            f = sc.fit_logistic(xx, yy, [f"c{i}" for i in range(xx.shape[1])])
            if f.converged:
                bad.append(f"{name}: converged=True")
        except Exception as exc:
            bad.append(f"{name}: raised {type(exc).__name__}")
    xt = np.concatenate([np.arange(1.0, 5.0), [5.0, 5.0], np.arange(6.0, 9.0)])
    yt = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1.0])
    ft = sc.fit_logistic(np.column_stack([np.ones(9), xt]), yt, ["Intercept", "x"])
    if ft.converged:
        bad.append("true quasi-complete separation (tie at x=5): converged=True")
    ok_fit = np.array([0, 1, 0, 0, 1, 1, 0, 1, 1, 0.0])
    fo = sc.fit_logistic(np.column_stack([np.ones(10), np.arange(10.0)]), ok_fit, ["Intercept", "x"])
    if not fo.converged:
        bad.append("ordinary fit: converged=False")
    counted("A-09/A-10 fit_logistic: separation, singular, all-zero -> converged=False; ordinary fit converges", bad, len(cases) + 2, "cases")
    df = pl.DataFrame({"y": np.array([0, 0, 0, 0, 1, 1, 1, 1.0] * 5), "x": np.tile(x1, 5)})
    df = df.with_columns(sep=pl.col("y") * 10.0 + pl.col("x") * 0.0)
    try:
        sc.stepwise_logistic(df, "y", ["sep"])
        raised = False
    except RuntimeError as exc:
        raised = "did not converge" in str(exc)
    report("A-09 stepwise_logistic raises a clear error on a non-converging fit", raised, "RuntimeError")
    rng = np.random.default_rng(7)
    n = 400
    base = rng.normal(size=n)
    yy = (rng.random(n) < 1 / (1 + np.exp(-(0.2 + 1.2 * base)))).astype(np.float64)
    d2 = pl.DataFrame({"y": yy, "b": base, "b_copy": base * 3.0, "noise": rng.normal(size=n)})
    r2 = sc.stepwise_logistic(d2, "y", ["b", "b_copy", "noise"])
    ent = [s.entered for s in r2.steps if s.entered in ("b", "b_copy")]
    ok2 = len(ent) == 1
    report("stepwise aliased candidate (b_copy = 3b) is skipped", ok2, str([(s.entered, s.removed) for s in r2.steps]))
    d3 = pl.DataFrame({"y": yy, "noise": rng.normal(size=n)})
    r3 = sc.stepwise_logistic(d3, "y", ["noise"], slentry=1e-9)
    report("stepwise nothing enters: intercept-only fit returned (S8 latent)", r3.steps == [] and r3.final is r3.intercept_only, "no steps")


def check_degenerate_stats() -> None:
    yv = pl.Series([1.0, 1.0, 0.0, 0.0])
    tied = sc.roc_association(yv, pl.Series([0.5] * 4))
    one_cls = sc.association_table(pl.Series([1.0, 1.0]), pl.Series([0.2, 0.7]))
    tab, chisq, dof, pv = sc.hosmer_lemeshow(pl.Series([1.0, 0.0] * 3), pl.Series([0.3, 0.3] * 3))
    ok = (tied.gamma is None and tied.area == 0.5 and one_cls.somers_d is None and one_cls.concordant_pct is None
          and dof < 1 and pv is None and tab.height <= 2)
    report("A-18/B-10/B-11 degenerate inputs give None, never NaN or a crash", ok, f"{tied} dof={dof} pv={pv}")
    groups = sc._hl_groups([100] * 10 + [3], 1003, 10)  # pyright: ignore[reportPrivateUsage]
    report("HL last-group merge (small last group joins its predecessor)", len(groups) == 10 and groups[-1] == 103 and sum(groups) == 1003, str(groups))
    lab = sc.roc_association(pl.Series([1.0, 0.0, 1.0, 0.0, 1.0]), pl.Series([0.9, 0.2, 0.6, 0.5, 0.4]), "Training Set")
    num = sc.roc_association(pl.Series([1.0, 0.0, 1.0, 0.0, 1.0]), pl.Series([0.9, 0.2, 0.6, 0.5, 0.4]))
    ok = (lab.columns == ["ROCModel", "Area", "StdErr", "LowerArea", "UpperArea", "SomersD", "Gamma", "TauA"] and lab.height == 1
          and lab["ROCModel"][0] == "Training Set" and lab["Area"][0] == num.area and lab["TauA"][0] == num.tau_a)
    report("B-05 roc_association(label=) returns the one-row inventory frame", ok, str(lab.columns))


def feat_matrix(run: Path, names: list[str]) -> tuple[FloatMat, FloatMat]:
    feats = pl.read_csv(run / "model_features_train.csv", infer_schema=False)
    cols = {c[:20]: c for c in feats.columns}
    xs = [np.ones(feats.height)] + [feats[cols[n]].cast(pl.Float64).to_numpy().astype(np.float64) for n in names]
    return np.column_stack(xs), feats["default_flag"].cast(pl.Float64).to_numpy().astype(np.float64)


FloatMat = np.ndarray


def run_dirs(*files: str) -> list[Path]:
    return [d for d in sorted((JUDGE / "runs").iterdir()) if d.is_dir() and all((d / f).exists() for f in files)]


def check_runs_sas_pd() -> None:
    """HL, ROC, ctable, D8 against EVERY judge/runs folder that has the files; SAS's own pd in, EXACT out (B-14/B-15)."""
    bad_hl: list[str] = []
    n_hl = 0
    for d in run_dirs("risk_scores_train.csv", "printed_hl_partition.csv", "printed_hosmer_lemeshow.csv", "printed_association.csv"):
        s = sc.proc_import_csv(d / "risk_scores_train.csv", 20)
        out = TMP / "runs_hl" / d.name
        out.mkdir(parents=True, exist_ok=True)
        write_hl_assoc(s["default_flag"], s["pd_logistic"], out)
        for f in ("printed_hl_partition.csv", "printed_hosmer_lemeshow.csv", "printed_association.csv"):
            n_hl += 1
            res = compare.compare_file(f, d / f, out / f, "port" if f == "printed_association.csv" else "strict")
            if res.status != "PASS":
                bad_hl.append(f"{d.name}/{f}: {'; '.join(res.problems)[:120]}")
    counted("HL partition/chisq STRICT + association (port: exported pd is BEST12), SAS pd, every judge/runs folder", bad_hl, n_hl, "files")

    bad_roc: list[str] = []
    n_roc = 0
    pairs = (("printed_roc_train.csv", "risk_scores_train.csv"), ("printed_roc_validation.csv", "risk_scores_validation.csv"),
             ("printed_roc_metrics.csv", "risk_scores_validation.csv"))
    for d in sorted((JUDGE / "runs").iterdir()):
        for rf, sf in pairs:
            if not ((d / rf).exists() and (d / sf).exists()):
                continue
            n_roc += 1
            s = sc.proc_import_csv(d / sf, 20)
            label = next(csv.DictReader(open(d / rf, newline="")))["ROCModel"]
            r = sc.roc_association(s["default_flag"], s["pd_logistic"], label)
            out = TMP / "runs_roc" / d.name
            out.mkdir(parents=True, exist_ok=True)
            txt = pl.DataFrame([[label, *[sc.sas_d8(v) for v in r.row(0)[1:]]]], schema=r.columns, orient="row")
            sc.write_sas_csv(txt, out / rf)
            res = compare.compare_file(rf, d / rf, out / rf, "strict")
            if res.status != "PASS":
                bad_roc.append(f"{d.name}/{rf}: {'; '.join(res.problems)[:120]}")
    counted("ROC association + D8, SAS pd, STRICT, every judge/runs folder", bad_roc, n_roc, "files")

    bad_ct: list[str] = []
    bad_d8: list[str] = []
    n_ct = n_d8 = 0
    rows_by_run: dict[str, int] = {}
    for d in run_dirs("risk_scores_train.csv", "printed_classification.csv", "model_features_train.csv", "model_coefficients.csv"):
        coef = pl.read_csv(d / "model_coefficients.csv", infer_schema=False)
        names = [v for v in coef["Variable"].to_list() if v != "Intercept"]
        x, y = feat_matrix(d, names)
        s = sc.proc_import_csv(d / "risk_scores_train.csv", 20)
        pdv = np.asarray(s["pd_logistic"].to_numpy(), dtype=np.float64)
        ct = sc.classification_table(x, y, pdv)  # the inventory's (X, y, pd)
        ct_kw = sc.classification_table(y, x, pd=pdv)
        out = TMP / "runs_ct" / d.name
        out.mkdir(parents=True, exist_ok=True)
        pct = {c: "8.1" for c in ("Correct", "Sensitivity", "Specificity", "FalsePositive", "FalseNegative", "PPV", "NPV")}
        sc.write_sas_csv(ct, out / "printed_classification.csv", {"ProbLevel": "8.3", **pct})
        n_ct += 1
        rows_by_run[d.name] = ct.height
        res = compare.compare_file("printed_classification.csv", d / "printed_classification.csv", out / "printed_classification.csv", "strict")
        if res.status != "PASS" or not ct.equals(ct_kw):
            bad_ct.append(f"{d.name}: {'; '.join(res.problems)[:120] or 'argument orders disagree'}")
        w = pdv * (1 - pdv)
        se = np.sqrt(np.diag(np.linalg.inv(x.T @ (x * w[:, None]))))
        for nm, v, ref in zip(["Intercept", *names], se, coef["StdErr"].to_list(), strict=True):
            n_d8 += 1
            if sc.sas_d8(float(v)) != ref:
                bad_d8.append(f"{d.name}:{nm} ref={ref} got={sc.sas_d8(float(v))}")
    counted("ctable (X, y, SAS pd) STRICT, every judge/runs folder", bad_ct, n_ct, "files")
    split = rows_by_run.get("x_split_drift_m_metrics_threshold", 0)
    report("B-01 ctable grid from pstar: x_split_drift run has 46 rows (0.000..0.900)", split == 46, f"{split} rows")
    counted("D8 StdErr from SAS's own pd vs model_coefficients.csv, every judge/runs folder (B-02)", bad_d8, n_d8)


def check_runs_stepwise() -> None:
    """The stepwise path, D8 E-notation and the ctable grid from OUR converged fit, on every run (port tolerance: fit noise)."""
    sl = {"m_train_slentry": (0.10, 0.05), "m_train_slstay": (0.05, 0.10)}
    bad_path: list[str] = []
    bad_ct: list[str] = []
    bad_se: list[str] = []
    n_path = n_ct = n_se = 0
    for d in run_dirs("model_features_train.csv", "stepwise_summary.csv", "printed_classification.csv", "model_coefficients.csv"):
        feats = sc.proc_import_csv(d / "model_features_train.csv", None)
        cols = [c for c in feats.columns if c in set(C36)]
        order = [c for c in C36 if c in cols]
        res = sc.stepwise_logistic(feats, "default_flag", order, *sl.get(d.name, (0.05, 0.05)))
        ref = pl.read_csv(d / "stepwise_summary.csv", infer_schema=False).fill_null("")
        want = [(r["EffectEntered"], r["EffectRemoved"]) for r in ref.iter_rows(named=True)]
        got = [((s.entered or "")[:20], (s.removed or "")[:20]) for s in res.steps]
        n_path += 1
        if got != want:
            bad_path.append(f"{d.name}: {len(got)} vs {len(want)} steps")
        final = res.final
        assert final is not None
        x = np.column_stack([np.ones(feats.height)] + [feats[c].to_numpy().astype(np.float64) for c in final.names[1:]])
        y = feats["default_flag"].to_numpy().astype(np.float64)
        ct = sc.classification_table(y, x, final)
        pct = {c: "8.1" for c in ("Correct", "Sensitivity", "Specificity", "FalsePositive", "FalseNegative", "PPV", "NPV")}
        out = TMP / "runs_conv" / d.name
        out.mkdir(parents=True, exist_ok=True)
        sc.write_sas_csv(ct, out / "printed_classification.csv", {"ProbLevel": "8.3", **pct})
        n_ct += 1
        rr = compare.compare_file("printed_classification.csv", d / "printed_classification.csv", out / "printed_classification.csv", "port")
        nrows = pl.read_csv(d / "printed_classification.csv", infer_schema=False).height
        if rr.status != "PASS" or ct.height != nrows:
            bad_ct.append(f"{d.name}: {ct.height} vs {nrows} rows {'; '.join(rr.problems)[:100]}")
        coef = pl.read_csv(d / "model_coefficients.csv", infer_schema=False)
        for nm, ref_se in zip(coef["Variable"].to_list(), coef["StdErr"].to_list(), strict=True):
            if "E-" not in ref_se:
                continue
            n_se += 1
            i = final.names.index(next(c for c in final.names if c[:20] == nm))
            got_se = sc.sas_d8(math.sqrt(final.cov[i, i]))
            if abs(float(got_se) - float(ref_se)) > 2e-8:
                bad_se.append(f"{d.name}:{nm} ref={ref_se} got={got_se}")
    counted("stepwise path (entered/removed) vs SAS, every judge/runs folder with a train fit", bad_path, n_path, "runs")
    counted("ctable from the converged fit: rows and port-mode compare, every judge/runs folder", bad_ct, n_ct, "runs")
    counted("D8 E-notation StdErr cells from the converged fit within the judge tolerance (2e-8)", bad_se, n_se)


def check_x06_oddsr() -> None:
    """X06 (migration/experiments/x06_printing.log): ODDSR8.3 cells, exact."""
    cases = [(1234.5, ">999.999"), (0.0005, "<0.001"), (0.001, "0.001"), (999.999, "999.999"),
             (1000.0, ">999.999"), (0.0009999, "<0.001"), (3.7495, "3.750")]
    bad = [f"{x!r}: {sc.fmt_oddsr(x, 8, 3)!r} want {w!r}" for x, w in cases if sc.fmt_oddsr(x, 8, 3) != w]
    counted("X06 ODDSR8.3 cells (fmt_oddsr)", bad, len(cases), "cases")


def check_x06_input() -> None:
    """X06: input(s, best32.): a 37-digit string reads as its first 32 digits; leading blanks ignored."""
    got = pl.select(
        sc.input_best32(pl.lit("1234567890123456789012345678901234567")).alias("a"),
        sc.input_best32(pl.lit("   12.5")).alias("b"),
    ).row(0)
    ok = got[0] == 12345678901234566802609541218304.0 and got[1] == 12.5
    report("X06 input best32. 32-column cut and leading blanks", ok, f"{got!r}")


def check_x06_best() -> None:
    """X06 BEST cells (value, w=8, w=12, w=6), exact; the stored text is stripped."""
    cases = [
        (0.0000123, "0.000012", "0.0000123", "123E-7"), (1.23e-6, "1.23E-6", "1.23E-6", "123E-8"),
        (0.00012345, "0.000123", "0.00012345", "0.0001"), (0.000012345, "0.000012", "0.000012345", "123E-7"),
        (9.9999e-6, "1E-5", "9.9999E-6", "1E-5"), (1234567.891, "1234568", "1234567.891", "1.23E6"),
        (-0.0000123, "-0.00001", "-0.0000123", "-12E-6"), (123456789012.0, "1.235E11", "123456789012", "123E9"),
    ]
    bad = []
    for x, b8, b12, b6 in cases:
        for w, want in ((8, b8), (12, b12), (6, b6)):
            got = sc.sas_best(x, w)
            if got != want:
                bad.append(f"{x!r} w={w}: {got!r} want {want!r}")
    counted("X06 BESTw. cells at w = 6, 8, 12", bad, len(cases) * 3)


def check_x06_percent() -> None:
    """X06 PERCENT8.2 cells, exact (SAS text before the export strips it)."""
    cases = [(9.99, "999.0%"), (9.999, "999.9%"), (12.34, "1234%"), (-12.34, "( 1234%)"), (1e-7, "0.00%")]
    bad = [f"{x!r}: {sc.fmt_percent(x, 8, 2)!r} want {w!r}" for x, w in cases if sc.fmt_percent(x, 8, 2) != w]
    counted("X06 PERCENT8.2 cells", bad, len(cases), "cases")


def check_x06_d8() -> None:
    """X06 D8. cells, exact."""
    cases = [
        (0.000029, "0.000029"), (0.00001, "0.000010"), (6.42e-6, "6.42E-6"), (0.000123456, "0.000123"),
        (123.456789, "123.5"), (12345.6789, "12345.7"), (-0.5, "-0.5000"), (0.0, "0"),
        (1234567.89, "1234568"), (-0.000029, "-0.00003"), (0.5, "0.5000"), (99.123456789, "99.1235"),
        (250.5, "250.5"), (1.2345e-6, "1.235E-6"),
    ]
    bad = [f"{x!r}: {sc.sas_d8(x)!r} want {w!r}" for x, w in cases if sc.sas_d8(x) != w]
    counted("X06 D8. cells", bad, len(cases), "cases")


def check_x06_d12() -> None:
    """X06 D12.3 cells, exact."""
    cases = [
        (0.000029, "0.000029000"), (0.00001, "0.000010000"), (6.42e-6, "0.000006420"),
        (0.000123456, "0.000123"), (123.456789, "123.456789"), (12345.6789, "12346"), (-0.5, "-0.500000"),
        (0.0, "0"), (1234567.89, "1234568"), (-0.000029, "-0.000029000"), (0.5, "0.500000"),
        (99.123456789, "99.123457"), (250.5, "250.500000"), (1.2345e-6, "0.000001235"),
    ]
    bad = [f"{x!r}: {sc.sas_d12_3(x)!r} want {w!r}" for x, w in cases if sc.sas_d12_3(x) != w]
    counted("X06 D12.3 cells", bad, len(cases), "cases")


def check_best_width_invariant() -> None:
    """BESTw. never prints wider than w (review of 06674b5); the digits kept are not SAS-verified."""
    cases = [(1.005e-9, 6), (1.005e-8, 6), (9.96e-9, 6), (-9.948e-9, 6), (-1.05e-9, 7), (-9.948e-9, 7)]
    bad = [f"{x!r} w={w}: {sc.sas_best(x, w)!r}" for x, w in cases if len(sc.sas_best(x, w)) > w]
    counted("BEST6/BEST7 width invariant on tiny values", bad, len(cases), "cases")


def main() -> None:
    steps: list[Callable[[], object]] = [
        check_best_small, check_best12, check_percent_wd, check_rank_and_wd84, check_import,
        check_edge_cases, check_d_formats, check_writer, check_stepwise, check_reference_pd_tables, check_roc,
        check_x05_scalars, check_x05_exprs, check_sql_and_merge, check_helper_names_and_agg, check_writer_rules,
        check_fit_and_stepwise_edges, check_degenerate_stats, check_runs_sas_pd, check_runs_stepwise,
        check_x06_oddsr, check_x06_input, check_x06_best, check_x06_percent, check_x06_d8, check_x06_d12, check_best_width_invariant,
    ]
    for f in steps:
        try:
            f()
        except Exception as exc:  # report, keep going
            import traceback

            traceback.print_exc()
            report(f.__name__, False, f"raised {type(exc).__name__}: {exc}")
    n_fail = sum(1 for _, ok, _ in RESULTS if not ok)
    print(f"\nSUMMARY: {len(RESULTS) - n_fail} PASS, {n_fail} FAIL of {len(RESULTS)} checks")
    sys.exit(1 if n_fail else 0)


if __name__ == "__main__":
    main()
