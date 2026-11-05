"""Parity comparator: CANDIDATE output dir vs REFERENCE output dir.

Usage (from judge/):
    uv run python compare.py REFERENCE_DIR CANDIDATE_DIR [--mode strict|port]
                             [--stage fe|train|metrics|predict] [--only f1,f2] [--json OUT]
Exit code 0 = every compared file passes, 1 = any failure, 2 = unusable reference/arguments.

Stages: the SAS scripts hand off through CSV files, so each stage is judged on the
REFERENCE's inputs (README "Contract"); model-fit noise stays out of later stages.

Modes
-----
strict  SAS-vs-SAS. Every compared cell identical text AND raw file lines identical as a
        multiset (quoting, line endings). Validates the judge itself.
port    Python-port-vs-SAS. Two checks on every numeric cell:
        VALUE   within the precision SAS printed: FORMATTED columns 1 display unit;
                other numbers (BEST12.) 1 unit in the 12th character; integers and flags
                effectively exact.
        FORMAT  printed the way SAS prints it: integer cells stay integers ('28', not
                '28.0'); E-notation only where SAS used it; FORMATTED columns keep their
                decimals; BEST12. cells must be exactly what BEST12. prints for the
                candidate's own value (sas_best12 reproduces all 2.9M distinct BEST12
                cells of the reference).
        Text cells exact. Model-fit exceptions (POLICY; evidence in README):
          * pd_logistic: |diff| <= PD_TOL per row AND mean |diff| <= PD_MEAN_TOL per file.
          * Model-fit tables: 2 display units + MODEL_REL_TOL relative; likelihood-based
            statistics (-2 Log L, AIC, SC, likelihood-ratio test) LIKELIHOOD_REL_TOL;
            Estimate/StdErr 2 display units; integer cells relative only; Association
            "Percent Tied" absolute 1e-5 percentage points (ABS_CELL_TOL).
          * credit_risk_score may differ by exactly 1 only where the reference pd is within
            PD_TOL of round()'s .5 boundary AND the candidate's score is SAS round() of the
            candidate's own pd; grade/recommendation/rate must then be the tuple SAS
            assigns to that score. pred_logistic may flip only within PD_TOL of 0.5 and
            only to (candidate pd >= 0.5).
          * Each such 0.5 flip widens the confusion-matrix outputs by exactly one flip's
            worth (computed from the files themselves, independent of --only).
        Every excusal is counted and reported; none are silent.

Rows are matched by key (output row order is an artifact of SAS's SQL join engine); key
columns are also compared as exact text. Columns must match in name and order. Columns
stamped with today() must be a valid DATE9. date within 2 days of the candidate file.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import polars as pl

# ---------------------------------------------------------------- policy -----
PD_TOL = 1e-4  # per row; fully converged MLE vs SAS (GCONV=1E-8) measured up to 3.6e-5
PD_MEAN_TOL = 1e-5  # per file mean |dpd|; converged MLE measured ~2e-6 (make_converged_candidate.py)
MODEL_REL_TOL = 1e-3  # Score/Wald chi-squares, odds ratios, ...; measured Wald diffs up to 9.3e-5 rel
LIKELIHOOD_REL_TOL = 1e-6  # -2 Log L, AIC, SC, LR test; measured -2LL gap 4.5e-6 abs on 37961
FLOAT_EPS = 1e-12  # relative slack for float parsing / last-bit noise only
BEST_WIDTH = 12

STAGES: dict[str, list[str]] = {
    "fe": ["model_features_train.csv", "model_features_validation.csv"],
    "train": ["risk_scores_train.csv", "risk_scores_validation.csv", "final_model_output.csv",
              "model_coefficients.csv", "stepwise_summary.csv", "model_summary.csv",
              "printed_fit_statistics.csv", "printed_global_tests.csv", "printed_rsquare.csv",
              "printed_association.csv", "printed_odds_ratios.csv", "printed_hl_partition.csv",
              "printed_hosmer_lemeshow.csv", "printed_classification.csv", "printed_roc_train.csv",
              "printed_roc_validation.csv", "printed_confusion_train.csv", "printed_confusion_validation.csv"],
    "metrics": ["validation_summary.csv", "ks_statistic.csv", "model_performance_metrics.csv",
                "decile_analysis.csv", "threshold_analysis.csv", "calibration_plot.csv",
                "printed_roc_metrics.csv", "printed_cumulative_lift.csv", "printed_psi_calculation.csv"],
    "predict": ["kaggle_submission.csv", "test_predictions.csv"],
}

KEYS: dict[str, list[str]] = {  # file -> key columns (absent = positional)
    "model_features_train.csv": ["row_id"], "model_features_validation.csv": ["row_id"],
    "risk_scores_train.csv": ["row_id"], "risk_scores_validation.csv": ["row_id"],
    "final_model_output.csv": ["row_id"], "test_predictions.csv": ["row_id"],
    "kaggle_submission.csv": ["row_id"],
    "model_coefficients.csv": ["Variable"], "stepwise_summary.csv": ["Step"],
    "decile_analysis.csv": ["decile"], "threshold_analysis.csv": ["threshold"],
    "calibration_plot.csv": ["pred_bin"],
    "printed_fit_statistics.csv": ["Step", "RowId"], "printed_global_tests.csv": ["Step", "Test"],
    "printed_rsquare.csv": ["Step"], "printed_odds_ratios.csv": ["Effect"],
    "printed_hl_partition.csv": ["Group"], "printed_classification.csv": ["ProbLevel"],
    "printed_confusion_train.csv": ["default_flag", "pred_logistic"],
    "printed_confusion_validation.csv": ["default_flag", "pred_logistic"],
    "printed_cumulative_lift.csv": ["decile"], "printed_psi_calculation.csv": ["score_bin"],
}
FILES: dict[str, list[str]] = {f: KEYS.get(f, []) for s in STAGES.values() for f in s}

FORMATTED: dict[str, set[str]] = {  # fixed-decimal SAS formats (from the .sas format statements)
    "model_summary.csv": {"Train_AUC", "Valid_AUC", "train_precision", "train_recall", "train_f1_score",
                          "train_accuracy", "valid_precision", "valid_recall", "valid_f1_score",
                          "valid_accuracy"},
    "validation_summary.csv": {"AUC", "Gini", "KS_Statistic", "KS_Cutoff", "PSI"},
    "ks_statistic.csv": {"KS_Statistic", "KS_Cutoff"},
    "model_performance_metrics.csv": {"AUC", "Gini", "KS_Statistic", "KS_Cutoff", "PSI"},
    "decile_analysis.csv": {"default_rate", "avg_pd", "min_pd", "max_pd", "capture_rate", "lift"},
    "printed_cumulative_lift.csv": {"default_rate", "avg_pd", "min_pd", "max_pd", "capture_rate", "lift",
                                    "cum_capture_rate", "cum_lift"},
    "calibration_plot.csv": {"mean_predicted", "mean_actual"},
    "printed_roc_metrics.csv": {"Area", "StdErr", "LowerArea", "UpperArea", "SomersD", "Gamma", "TauA"},
}
CONFUSION_FILES = {"printed_confusion_train.csv": "train", "printed_confusion_validation.csv": "valid"}
# Outputs of the model fit itself, printed through ODS templates: fit tolerance.
MODEL_STAT_FILES = {"model_coefficients.csv", "stepwise_summary.csv"} | {
    f for f in STAGES["train"] if f.startswith("printed_") and f not in CONFUSION_FILES}
DU_ONLY_COLS = {"Estimate", "StdErr"}
# (file, column) -> absolute tolerance overriding the model-fit rule
ABS_COL_TOL = {
    ("printed_hl_partition.csv", "Total"): 0.0,  # HL groups are formed by count: exact
    ("printed_hl_partition.csv", "EventsObserved"): 2.0,  # rows adjacent in pd may swap groups
    ("printed_hl_partition.csv", "NoneventsObserved"): 2.0,
}
# (file, column) -> (label column, label, absolute tolerance) for one labelled cell
ABS_CELL_TOL = {
    # SAS counts pairs with |dpd| <= ~1e-8 as tied (280 pairs, 4.0773e-5 %); a correct
    # converged port gets 283 (4.12e-5 %). Printed diagnostic: absolute 1e-5 percentage
    # points (human sign-off Q1, 2026-11-05; migration/rulebook-amendments.md A8).
    ("printed_association.csv", "nValue1"): ("Label1", "Percent Tied", 1e-5),
}

DATE_COLS = {"model_summary.csv": {"training_date"}, "model_performance_metrics.csv": {"validation_date"}}
DATE_WINDOW_DAYS = 2

PD_COL = "pd_logistic"
SCORE_COL = "credit_risk_score"
SCORE_TUPLE = ["credit_risk_score", "risk_grade", "recommendation", "interest_rate"]
CUTOFF_COL = "pred_logistic"  # = (pd >= 0.5)
ROW_LEVEL_FILES = {f for f, k in FILES.items() if k == ["row_id"]}
SCORED = {"train": "risk_scores_train.csv", "valid": "risk_scores_validation.csv"}


# --------------------------------------------------------------- helpers -----
def sas_best12(x: float) -> str:
    """SAS BEST12. in plain notation: round to fit 12 characters, drop trailing zeros.
    Reproduces the 2,942,611 distinct plain-notation cells of the reference. Used only for
    cells printed without E-notation (format_ok); SAS prints 0 < |x| < 1e-5 in E-notation,
    which this function does not (RULEBOOK amendment A15)."""
    if x == 0 or not math.isfinite(x):
        return "0" if x == 0 else repr(x)
    ilen = len(str(int(abs(x)))) + (1 if x < 0 else 0)
    s = f"{x:.{max(0, BEST_WIDTH - 1 - ilen)}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s == "-0" else s


def sas_round(x: float) -> int:
    return math.floor(x + 0.5) if x >= 0 else -math.floor(-x + 0.5)  # half away from zero


def read_text_csv(path: Path) -> pl.DataFrame:
    """Read every column as raw text: no inference, no whitespace stripping."""
    df = pl.read_csv(path, infer_schema=False)
    return df.with_columns(pl.all().fill_null(""))  # empty CSV field == SAS missing == ""


def load_meta(run_dir: Path) -> dict:
    for p in (run_dir / "run_meta.json", run_dir / "listings" / "run_meta.json"):
        if p.exists():
            return json.loads(p.read_text())
    return {}


def parse_num(e: pl.Expr) -> pl.Expr:
    """Parse a SAS-printed number ('5.00%' -> 5.0 in percent units). Null if not a number."""
    return e.str.strip_suffix("%").cast(pl.Float64, strict=False)


def display_unit(e: pl.Expr) -> pl.Expr:
    """10^-(decimals printed), honoring E-notation: '0.8592'->1e-4, '6.42E-6'->1e-8, '12'->1."""
    s = e.str.strip_suffix("%").str.to_uppercase()
    exp = s.str.extract(r"E([-+]?\d+)$", 1).cast(pl.Int64).fill_null(0)
    mant = s.str.replace(r"E[-+]?\d+$", "")
    decs = mant.str.extract(r"\.(\d*)$", 1).str.len_chars().fill_null(0).cast(pl.Int64)
    return pl.lit(10.0).pow((exp - decs).cast(pl.Float64))


def best12_unit(e: pl.Expr) -> pl.Expr:
    """Resolution of BEST12.: 1 unit in the 12th character ('8.455530531'->1e-10, '600'->1e-8)."""
    s = e.str.strip_suffix("%")
    int_len = s.str.split(".").list.first().str.len_chars().cast(pl.Int64)
    decs = (BEST_WIDTH - 1 - int_len).clip(lower_bound=0)
    plain = pl.lit(10.0).pow(-decs.cast(pl.Float64))
    return pl.when(s.str.to_uppercase().str.contains("E")).then(display_unit(e)).otherwise(plain)


def canon_key(e: pl.Expr) -> pl.Expr:
    """Join key: finite numbers canonicalized to 12 significant digits, else exact text.
    Key TEXT is compared exactly as well, so this only decides which rows pair up."""
    num = e.cast(pl.Float64, strict=False)
    finite = num.is_not_null() & num.is_finite()
    as_num = (num.round_sig_figs(12) + 0.0).cast(pl.Utf8)  # +0.0 folds -0 into 0
    return pl.when(finite).then(pl.lit("n:") + as_num).otherwise(pl.lit("t:") + e)


def column_kind(name: str, col: str) -> str:
    if name in MODEL_STAT_FILES:
        return "model"
    return "formatted" if col in FORMATTED.get(name, set()) else "best"


def format_ok(ref: str, cand: str, kind: str) -> bool:
    """Is the candidate printed the way SAS prints this cell? (value is checked separately)"""
    r, c = ref.rstrip("%"), cand.rstrip("%")
    is_int = lambda s: "." not in s and "e" not in s.lower()
    if is_int(r) != is_int(c) or ("e" in r.lower()) != ("e" in c.lower()):
        return False
    if kind == "formatted":
        dec = lambda s: len(s.split(".")[1]) if "." in s else 0
        return dec(r) == dec(c)
    if kind == "best" and "e" not in c.lower():
        try:
            return c == sas_best12(float(c))
        except ValueError:
            return False
    return True


@dataclass
class FileResult:
    file: str
    status: str = "PASS"
    problems: list[str] = field(default_factory=list)
    failed: set[str] = field(default_factory=set)  # column names or tags ('columns', 'keys', ...)
    excused: dict[str, int] = field(default_factory=dict)

    def fail(self, tag: str, msg: str) -> None:
        self.status = "FAIL"
        self.failed.add(tag)
        self.problems.append(f"{tag}: {msg}")


# ------------------------------------------------------------ comparison -----
def raw_lines_check(res: FileResult, ref_path: Path, cand_path: Path) -> None:
    ref_lines = sorted(ref_path.read_bytes().splitlines(keepends=True))
    cand_lines = sorted(cand_path.read_bytes().splitlines(keepends=True))
    if ref_lines != cand_lines:
        diff = len(set(ref_lines) ^ set(cand_lines))
        res.fail("raw", f"raw lines differ (quoting/line endings/formatting), {diff} distinct lines")


def value_bad(name: str, col: str, r: pl.Expr, c: pl.Expr, extra_tol: float) -> pl.Expr:
    """Port-mode VALUE mismatch for a column whose reference has at least one numeric cell."""
    rn, cn = parse_num(r), parse_num(c)
    is_int = ~r.str.contains(r"[.Ee]")
    if col == PD_COL:
        tol = pl.lit(PD_TOL)
    elif (name, col) in ABS_COL_TOL:
        tol = pl.lit(ABS_COL_TOL[(name, col)])
    elif name in MODEL_STAT_FILES:
        rel = MODEL_REL_TOL
        if name == "printed_fit_statistics.csv":
            rel_e = pl.lit(LIKELIHOOD_REL_TOL)
        elif name == "printed_global_tests.csv":
            rel_e = pl.when(pl.col("Test") == "Likelihood Ratio").then(LIKELIHOOD_REL_TOL).otherwise(rel)
        else:
            rel_e = pl.lit(0.0 if col in DU_ONLY_COLS else rel)
        du_part = pl.when(is_int).then(0.0).otherwise(2 * display_unit(r))  # integers: relative only
        tol = du_part + rel_e * rn.abs()
    elif col in FORMATTED.get(name, set()):
        tol = display_unit(r)
    else:
        tol = best12_unit(r)
    if (name, col) in ABS_CELL_TOL:
        label_col, label, cell_tol = ABS_CELL_TOL[(name, col)]
        tol = pl.when(pl.col(label_col) == label).then(pl.lit(cell_tol)).otherwise(tol)
    tol = tol + extra_tol + FLOAT_EPS * rn.abs()
    pct_mismatch = r.str.ends_with("%") != c.str.ends_with("%")
    within = ((rn - cn).abs() <= tol).fill_null(False)  # unparseable / NaN candidate -> False
    return pl.when(rn.is_not_null()).then(pct_mismatch | ~within).otherwise(r != c)  # tokens: exact


def date_ok(text: str, cand_path: Path) -> bool:
    try:
        d = dt.datetime.strptime(text.title(), "%d%b%Y").date()
    except ValueError:
        return False
    written = dt.date.fromtimestamp(cand_path.stat().st_mtime)
    return text == text.upper() and abs((d - written).days) <= DATE_WINDOW_DAYS


def compare_file(name: str, ref_path: Path, cand_path: Path, mode: str,
                 extra_tol: dict[str, float] | None = None) -> FileResult:
    res = FileResult(name)
    if not cand_path.exists():
        res.fail("file", "candidate file missing")
        return res
    try:
        return _compare_file(res, name, ref_path, cand_path, mode, extra_tol or {})
    except Exception as exc:  # malformed candidate: fail this file, keep judging the rest
        res.fail("error", f"{type(exc).__name__}: {exc}")
        return res


def _compare_file(res: FileResult, name: str, ref_path: Path, cand_path: Path, mode: str,
                  extra_tol: dict[str, float]) -> FileResult:
    ref, cand = read_text_csv(ref_path), read_text_csv(cand_path)
    dates = DATE_COLS.get(name, set())
    if mode == "strict" and not dates:
        raw_lines_check(res, ref_path, cand_path)

    if ref.columns != cand.columns:
        missing = [c for c in ref.columns if c not in cand.columns]
        extra = [c for c in cand.columns if c not in ref.columns]
        res.fail("columns", f"missing={missing} extra={extra} "
                 f"same_set_different_order={sorted(ref.columns) == sorted(cand.columns)}")
        if missing:
            return res
    if ref.height != cand.height:
        res.fail("rows", f"reference={ref.height} candidate={cand.height}")

    keys = FILES[name]
    data_cols = list(ref.columns)
    if keys:
        kcols = [f"__k_{k}" for k in keys]
        ref = ref.with_columns([canon_key(pl.col(k)).alias(f"__k_{k}") for k in keys])
        cand = cand.with_columns([canon_key(pl.col(k)).alias(f"__k_{k}") for k in keys])
        for side, df in (("reference", ref), ("candidate", cand)):
            dup = df.select(kcols).is_duplicated().sum()
            if dup:
                res.fail("keys", f"{side} has {dup} duplicated key rows")
        if "keys" in res.failed:
            return res
        only_ref = ref.join(cand, on=kcols, how="anti").height
        only_cand = cand.join(ref, on=kcols, how="anti").height
        if only_ref or only_cand:
            res.fail("keys", f"{only_ref} reference rows missing from candidate, {only_cand} extra in candidate")
        joined = ref.join(cand, on=kcols, how="inner", suffix="__c")
    else:
        if ref.height != cand.height:
            return res
        joined = pl.concat([ref, cand.rename({c: f"{c}__c" for c in cand.columns})], how="horizontal")

    compare_cols = [c for c in data_cols if c in cand.columns]

    # Excusals (port mode, row-level files): only where the CANDIDATE is self-consistent.
    excuse: dict[str, pl.Expr] = {}
    if mode == "port" and name in ROW_LEVEL_FILES and PD_COL in data_cols:
        ref_pd, cand_pd = parse_num(pl.col(PD_COL)), parse_num(pl.col(f"{PD_COL}__c"))
        raw_ref, raw_cand = 600 + 250 * (1 - ref_pd), 600 + 250 * (1 - cand_pd)
        near_half = ((raw_ref - raw_ref.floor()) - 0.5).abs() <= 250 * PD_TOL
        if SCORE_COL in data_cols:
            tuple_cols = [c for c in SCORE_TUPLE if c in data_cols]
            sas_tuples = joined.select(tuple_cols).unique().rename({c: f"{c}__c" for c in tuple_cols}) \
                .with_columns(pl.lit(True).alias("__tuple_is_sas"))
            joined = joined.join(sas_tuples, on=[f"{c}__c" for c in tuple_cols], how="left")
            cand_score = parse_num(pl.col(f"{SCORE_COL}__c"))
            score_step = (parse_num(pl.col(SCORE_COL)) - cand_score).abs() == 1
            self_consistent = cand_score == (raw_cand + 0.5).floor()  # SAS round() of candidate pd
            row_ok = (near_half & score_step & self_consistent & (cand_pd - ref_pd).abs().le(PD_TOL)
                      & pl.col("__tuple_is_sas").fill_null(False)).fill_null(False)
            excuse.update({c: row_ok for c in tuple_cols})
        if CUTOFF_COL in data_cols:
            near_cut = (ref_pd - 0.5).abs() <= PD_TOL
            cand_says = pl.when(cand_pd >= 0.5).then(pl.lit("1")).otherwise(pl.lit("0"))
            excuse[CUTOFF_COL] = (near_cut & (pl.col(f"{CUTOFF_COL}__c") == cand_says)).fill_null(False)

    for col in compare_cols:
        r, c = pl.col(col), pl.col(f"{col}__c")
        fmt_flagged = 0
        if col in dates:
            if mode == "port":
                bad_dates = [v for v in joined.get_column(f"{col}__c").to_list() if not date_ok(v, cand_path)]
                if bad_dates:
                    res.fail(col, f"not a DATE9. date within {DATE_WINDOW_DAYS} days of the run: {bad_dates[:3]}")
            continue
        if mode == "strict" or col in keys or col in SCORE_TUPLE or col == CUTOFF_COL:
            bad = r != c  # exact text (excusals applied below)
        else:
            ref_vals = joined.get_column(col)
            has_numeric = ref_vals.str.strip_suffix("%").cast(pl.Float64, strict=False).is_not_null().any()
            if not has_numeric:
                bad = r != c
            else:
                bad = value_bad(name, col, r, c, extra_tol.get(col, 0.0))
                kind = column_kind(name, col)
                diff = joined.filter((r != c) & parse_num(r).is_not_null()).select(col, f"{col}__c")
                fmt_bad = [(a, b) for a, b in diff.iter_rows() if not format_ok(a, b, kind)]
                if fmt_bad:
                    fmt_flagged = len(fmt_bad)
                    res.fail(col, f"{fmt_flagged} cells not printed as SAS prints them ({kind}), "
                                  f"e.g. (reference, candidate) {fmt_bad[:3]}")
                if col == PD_COL and name in ROW_LEVEL_FILES:
                    mean_abs = joined.select((parse_num(r) - parse_num(c)).abs().mean()).item()
                    if mean_abs is not None and mean_abs > PD_MEAN_TOL:
                        res.fail(f"{col}(mean)", f"mean |dpd| = {mean_abs:.2e} > PD_MEAN_TOL {PD_MEAN_TOL:.0e}")
        flagged = joined.filter(bad)
        if col in excuse and flagged.height:
            n_exc = flagged.filter(excuse[col]).height
            if n_exc:
                res.excused[col] = n_exc
            flagged = flagged.filter(~excuse[col])
        if flagged.height:
            show = [k for k in keys if k != col] + [col, f"{col}__c"]
            res.fail(col, f"{flagged.height} mismatches, e.g. (key.., reference, candidate) "
                          f"{flagged.select(show).head(3).rows()}")
    return res


def flips(ref_dir: Path, cand_dir: Path, part: str) -> tuple[int, dict[str, int]]:
    """Rows whose 0.5-cutoff prediction differs between reference and candidate risk scores,
    plus the reference confusion counts. Read from the files, independent of --only."""
    f = SCORED[part]
    if not (cand_dir / f).exists():
        return 0, {}
    cols = ["row_id", "default_flag", CUTOFF_COL]
    ref = pl.read_csv(ref_dir / f, columns=cols, infer_schema=False)
    cand = pl.read_csv(cand_dir / f, columns=cols, infer_schema=False)
    n = ref.join(cand, on="row_id", suffix="__c").filter(pl.col(CUTOFF_COL) != pl.col(f"{CUTOFF_COL}__c")).height
    tp = ref.filter((pl.col("default_flag") == "1") & (pl.col(CUTOFF_COL) == "1")).height
    counts = {"N": ref.height, "TP": tp,
              "PP": ref.filter(pl.col(CUTOFF_COL) == "1").height, "P": ref.filter(pl.col("default_flag") == "1").height}
    return n, counts


def confusion_allowance(name: str, ref_dir: Path, cand_dir: Path) -> dict[str, float]:
    """Exactly one flip's worth per excused 0.5-cutoff flip, per metric."""
    extra: dict[str, float] = {}
    if name == "model_summary.csv":
        for part in ("train", "valid"):
            k, n = flips(ref_dir, cand_dir, part)
            if k:
                extra[f"{part}_accuracy"] = k / n["N"]
                extra[f"{part}_recall"] = k / n["P"]
                extra[f"{part}_precision"] = k / max(n["PP"] - k, 1)
                extra[f"{part}_f1_score"] = 2 * k / max(min(n["PP"] - k, n["P"]), 1)
    elif name in CONFUSION_FILES:
        k, n = flips(ref_dir, cand_dir, CONFUSION_FILES[name])
        if k:
            extra = {"COUNT": float(k), "PERCENT": 100.0 * k / n["N"]}
    return extra


def compare_dir(ref_dir: Path, cand_dir: Path, files: list[str], mode: str) -> list[FileResult]:
    return [compare_file(f, ref_dir / f, cand_dir / f, mode,
                         confusion_allowance(f, ref_dir, cand_dir) if mode == "port" else {})
            for f in files]


def check_reference(ref_dir: Path, files: list[str]) -> list[str]:
    problems = [f"missing from reference: {f}" for f in files if not (ref_dir / f).exists()]
    meta = load_meta(ref_dir)
    if not meta:
        problems.append("reference has no run_meta.json (provenance unknown)")
    reviewed = set((meta.get("warnings_reviewed") or {}).get("warnings", []))
    for script, errs in meta.get("errors", {}).items():
        if errs:
            problems.append(f"reference run had SAS ERRORs in {script}")
    for script, warns in meta.get("new_warnings", {}).items():
        unreviewed = [w for w in warns if w not in reviewed]
        if unreviewed:
            problems.append(f"reference run had unreviewed WARNINGs in {script}: {unreviewed[:2]}")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("reference", type=Path)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--mode", choices=["strict", "port"], default="port")
    ap.add_argument("--stage", choices=sorted(STAGES))
    ap.add_argument("--only", help="comma-separated subset of files (named in the report)")
    ap.add_argument("--allow-unprovenanced-reference", action="store_true",
                    help="permit a reference without run_meta.json (e.g. the frozen ../output goldens)")
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    files = STAGES[args.stage] if args.stage else list(FILES)
    if args.only:
        files = args.only.split(",")
    unknown = [f for f in files if f not in FILES]
    problems = check_reference(args.reference, [f for f in files if f in FILES])
    if args.allow_unprovenanced_reference:
        problems = [p for p in problems if "run_meta" not in p]
    if unknown or problems:
        print(f"UNUSABLE: unknown files {unknown}; reference problems {problems}")
        return 2
    if len(files) < len(FILES):
        print(f"NOTE: judging {len(files)}/{len(FILES)} files" + (f" (stage {args.stage})" if args.stage else ""))

    results = compare_dir(args.reference, args.candidate, files, args.mode)
    for r in results:
        note = f"  (excused near-boundary: {r.excused})" if r.excused else ""
        print(f"{r.status}  {r.file}{note}")
        for p in r.problems:
            print(f"      - {p}")
    n_pass = sum(r.status == "PASS" for r in results)
    print(f"\n{n_pass}/{len(results)} files pass ({args.mode} mode)")
    if args.json:
        args.json.write_text(json.dumps([{**r.__dict__, "failed": sorted(r.failed)} for r in results], indent=2))
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
