"""SAS-compatibility helpers: the ONE implementation of every `sas_compat.*` mapping in
migration/RULEBOOK.md §2 (v1.2). Translations import this module and never re-implement a helper.

Conventions
- Missing numeric = polars null (never NaN).
- Expression helpers take and return `pl.Expr`. A float or int argument is a literal.
- Formatting helpers take one Python float (None = missing) and return the text SAS prints.
- Every behaviour cites the inventory row or experiment that decided it.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import numpy.typing as npt
import polars as pl

FloatArray = npt.NDArray[np.float64]

Z975: float = 1.959963984540054  # A25: the only normal quantile (odds-ratio and ROC CIs)
MONTHS: tuple[str, ...] = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")

ExprOrNum = pl.Expr | float | int


# ----------------------------------------------------------- comparisons -----
# SAS: missing is smaller than every number; a comparison is never missing (A1).
def lt(x: pl.Expr, c: ExprOrNum) -> pl.Expr:
    """SAS `x < c` with missing smallest. Non-null pl.Boolean."""
    raise NotImplementedError


def le(x: pl.Expr, c: ExprOrNum) -> pl.Expr:
    """SAS `x <= c`. No inventory site (A31): unverified."""
    raise NotImplementedError


def gt(x: pl.Expr, c: ExprOrNum) -> pl.Expr:
    """SAS `x > c` (missing > anything is false). Non-null pl.Boolean."""
    raise NotImplementedError


def ge(x: pl.Expr, c: ExprOrNum) -> pl.Expr:
    """SAS `x >= c`. Non-null pl.Boolean."""
    raise NotImplementedError


def eq(x: pl.Expr, c: ExprOrNum) -> pl.Expr:
    """SAS `x = c` (`. = .` is true). No inventory site (A31): unverified."""
    raise NotImplementedError


def flag(cond: pl.Expr) -> pl.Expr:
    """SAS boolean assignment `x = (cond);` -> Int64 0/1. A null condition counts as 0."""
    raise NotImplementedError


# ------------------------------------------------------------ arithmetic -----
def div(a: ExprOrNum, b: ExprOrNum) -> pl.Expr:
    """Element-wise IEEE division (A13; experiment X04): numpy `np.divide` on Float64.
    Missing in either operand -> missing; division by 0 -> missing (SAS note, no inf).
    Mandatory for any scalar, literal or aggregate divisor."""
    raise NotImplementedError


def sas_sum(*args: pl.Expr) -> pl.Expr:
    """SAS sum(a, b, ...): ignores missing; all missing -> missing."""
    raise NotImplementedError


def sas_min(*args: ExprOrNum) -> pl.Expr:
    """SAS min(...): ignores missing; all missing -> missing."""
    raise NotImplementedError


def sas_max(*args: ExprOrNum) -> pl.Expr:
    """SAS max(...): ignores missing; all missing -> missing."""
    raise NotImplementedError


def sas_log(x: pl.Expr) -> pl.Expr:
    """SAS log(x): natural log; x <= 0 or missing -> missing."""
    raise NotImplementedError


def sas_round(x: pl.Expr) -> pl.Expr:
    """SAS round(x) to an integer: half away from zero. Missing stays missing. Float64 result."""
    raise NotImplementedError


def sas_round_scalar(x: float) -> float:
    """Scalar form of sas_round."""
    raise NotImplementedError


def input_best32(s: pl.Expr) -> pl.Expr:
    """SAS input(s, best32.): numeric text -> Float64; anything else ('NA', '') -> missing."""
    raise NotImplementedError


def date9(d: dt.date) -> str:
    """DATE9. with fixed English month names (A16): 05NOV2026."""
    raise NotImplementedError


def today_date9() -> str:
    """today() formatted DATE9. (training_date / validation_date)."""
    raise NotImplementedError


# ------------------------------------------------------------ formatting -----
def sas_best(x: float | None, w: int) -> str:
    """BESTw. text. Plain notation rounded half up from the value's 15-significant-digit form
    (A18); E-notation for 0 < |x| < 1e-5 with the mantissa rounded to fill w characters and
    trailing zeros stripped (A15). Integers print without a decimal point. None -> '' (export) .
    BEST8. is what `select ... into` stores (A9)."""
    raise NotImplementedError


def sas_best12(x: float | None) -> str:
    """BEST12., the default export format of unformatted numerics."""
    raise NotImplementedError


def fmt_wd(x: float | None, w: int, d: int) -> str:
    """w.d (e.g. 8.4, 8.2, 10.4): half away from zero from the 15-significant-digit form (A24).
    None -> ''."""
    raise NotImplementedError


def fmt_percent(x: float | None, w: int, d: int) -> str:
    """percentw.d: 100*x with d decimals and '%', keeping width w, so percent8.2 prints
    '5.00%' but '100.0%' (A14, A24). None -> ''."""
    raise NotImplementedError


def sas_d8(x: float | None) -> str:
    """D8. as exported for ODS statistics (inventory: model_coefficients.csv, ROC rows)."""
    raise NotImplementedError


def sas_d12_3(x: float | None) -> str:
    """D12.3 as exported (inventory: printed_association.csv, printed_rsquare.csv,
    printed_fit_statistics.csv InterceptOnly): |x| >= 1e4 -> 0 decimals; 1e-4 <= |x| < 100 ->
    6 decimals; 1e-5 <= |x| < 1e-4 -> 9 decimals; last digit half up (A18)."""
    raise NotImplementedError


def sas_pvalue(x: float | None) -> str:
    """PVALUE6.4: '<.0001' below 0.0001, else 4 decimals with SAS's leading-zero rule."""
    raise NotImplementedError


# ------------------------------------------------------------------- I/O -----
def proc_import_csv(path: Path, guessingrows: int | None = 20) -> pl.DataFrame:
    """PROC IMPORT dbms=csv getnames=yes (RULEBOOK §2, A3): numeric if every one of the first
    `guessingrows` data values parses as a number (None = all rows), else text of width = the
    longest of those values, LATER VALUES TRUNCATED to that width (BUG(port)); an all-empty
    column in the guessing window is text of width 1; empty header -> VAR1; names cut to 32."""
    raise NotImplementedError


def write_sas_csv(df: pl.DataFrame, path: Path, formats: Mapping[str, str] | None = None) -> None:
    """PROC EXPORT dbms=csv. Unformatted numeric columns -> sas_best12; `formats` maps a
    column to 'w.d', 'percentw.d' or 'date9.'; str columns written verbatim (pre-rendered
    model-statistics text, A20); missing -> empty field; header = column names; LF line ends."""
    raise NotImplementedError


# ------------------------------------------------------------ procedures -----
def proc_rank_groups(x: pl.Series, k: int, descending: bool = False) -> pl.Series:
    """PROC RANK groups=k: rank with ties = mean, group = floor(rank * k / (n + 1)), n = number
    of non-missing values; missing -> missing. Int64."""
    raise NotImplementedError


@dataclass
class LogisticFit:
    """A fitted logistic model P(y = 1) on columns `names` (intercept first)."""

    names: list[str]
    beta: FloatArray
    cov: FloatArray  # inverse information matrix
    loglik: float
    n_iter: int
    converged: bool


def fit_logistic(x: FloatArray, y: FloatArray, names: Sequence[str]) -> LogisticFit:
    """Newton-Raphson from all-zero coefficients, halving the step while -2 Log L increases,
    until max|step| < 1e-10 (RULEBOOK §2 model fitting, A17). `x` includes the intercept column."""
    raise NotImplementedError


@dataclass
class StepwiseStep:
    step: int
    entered: str | None
    removed: str | None
    df: int
    number_in_model: int
    score_chisq: float | None  # for an entry
    wald_chisq: float | None  # for a removal
    p_value: float
    fit: LogisticFit  # the model after this step


@dataclass
class StepwiseResult:
    steps: list[StepwiseStep] = field(default_factory=list[StepwiseStep])
    final: LogisticFit | None = None
    intercept_only: LogisticFit | None = None


def stepwise_logistic(df: pl.DataFrame, response: str, candidates: Sequence[str],
                      slentry: float = 0.05, slstay: float = 0.05) -> StepwiseResult:
    """PROC LOGISTIC descending selection=stepwise exactly as RULEBOOK §2 (A5) and the train.sas
    stepwise inventory row: removal before entry; aliased candidates skipped (relative residual
    < 1e-8); enter the largest score chi-square (strict >, ties to the first in MODEL order);
    stop when nothing enters or the best entry was just removed. Reference implementation:
    migration/experiments/x02_stepwise_reference.py."""
    raise NotImplementedError


@dataclass
class RocAssociation:
    area: float
    std_err: float
    lower: float
    upper: float
    somers_d: float
    gamma: float
    tau_a: float


def roc_association(y: pl.Series, score: pl.Series) -> RocAssociation:
    """PROC LOGISTIC nofit + roc (ROCAssociation): Mann-Whitney area with ties counted 1/2,
    DeLong standard error, Wald CI with Z975, Somers' D, Gamma, Tau-a (inventory ROC rows)."""
    raise NotImplementedError


@dataclass
class AssociationTable:
    concordant_pct: float
    discordant_pct: float
    tied_pct: float
    pairs: int
    somers_d: float
    gamma: float
    tau_a: float
    c: float


def association_table(y: pl.Series, pd: pl.Series) -> AssociationTable:
    """ODS Association of the fitted model: pairs tied when |dpd| <= 1e-8 (A8)."""
    raise NotImplementedError


def hosmer_lemeshow(y: pl.Series, pd: pl.Series) -> tuple[pl.DataFrame, float, int, float]:
    """`lackfit`: SAS's HL partition (blocks of rows whose pd agree within 1e-6 of the block's
    smallest pd; documented group-size rule; last group merged when small) as the inventory row
    printed_hl_partition.csv decides. Returns (partition table, chi-square, DF, p-value)."""
    raise NotImplementedError


def classification_table(y: FloatArray, x: FloatArray, fit: LogisticFit) -> pl.DataFrame:
    """`ctable`: bias-adjusted (one-step leave-one-out) probabilities at levels 0.000..0.880 by
    0.02, as the inventory row printed_classification.csv decides; 0/0 percentages missing."""
    raise NotImplementedError
