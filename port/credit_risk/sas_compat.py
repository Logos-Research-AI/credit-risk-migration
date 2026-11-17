"""SAS-compatibility helpers: the ONE implementation of every `sas_compat.*` mapping in
migration/RULEBOOK.md §2 (v1.2). Translations import this module and never re-implement a helper.

Conventions
- Missing numeric = polars null (never NaN).
- Expression helpers take and return `pl.Expr`. A float or int argument is a literal (any argument
  of a comparison, `div`, `sas_sum/min/max`, `sas_log`, `sas_exp`, `sas_round`, `sql_*`;
  `input_best32` takes text).
- Every expression helper returns an expression NAMED after its FIRST argument's output name (A-03),
  so `with_columns(div(pl.col("x"), k))` replaces `x`. Inside `group_by().agg` a helper whose
  operands are all aggregates or literals returns a scalar per group.
- Formatting helpers take one Python float (None = missing) and return the text SAS prints
  (without the leading blanks of right alignment, except where noted).
- Every behaviour cites the inventory row or experiment that decided it.
- API conventions of the model-statistics helpers (fixed with the train translation):
  `LogisticFit.names[0]` is "Intercept" and `LogisticFit.loglik` is the log-likelihood, so
  -2 Log L = -2 * loglik; `AssociationTable` percentages are in PERCENT units (85.92, not 0.859);
  `hosmer_lemeshow` and `classification_table` return NUMERIC frames whose columns are exactly those
  of printed_hl_partition.csv / printed_classification.csv (the caller renders text);
  `roc_association` returns numbers only unless `label=` is given (then the one-row frame of the
  inventory rows, ROCModel first).
"""

from __future__ import annotations

import datetime as dt
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from decimal import ROUND_DOWN, ROUND_HALF_UP, Context, Decimal
from pathlib import Path
from typing import cast, overload

import numpy as np
import numpy.typing as npt
import polars as pl
from scipy.stats import chi2

FloatArray = npt.NDArray[np.float64]

Z975: float = 1.959963984540054  # A25: the only normal quantile (odds-ratio and ROC CIs)
MONTHS: tuple[str, ...] = ("JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC")

ExprOrNum = pl.Expr | float | int

_CTX = Context(prec=80)
# Wide enough for the product of two doubles to be exact (a double has at most 767 significant digits).
_CTX_EXACT = Context(prec=1200)
_MIN_NORMAL = 2.2250738585072014e-308


def _e(c: ExprOrNum) -> pl.Expr:
    return c if isinstance(c, pl.Expr) else pl.lit(c)


def _named(first: ExprOrNum, out: pl.Expr) -> pl.Expr:
    """Name `out` after the output name of `first` (A-03), when determinable."""
    n = _e(first).meta.output_name(raise_if_undetermined=False)
    return out.alias(n) if n else out


def _has_bare_column(node: object) -> bool:
    """True if the serialized expression tree reads a column outside any aggregation."""
    if isinstance(node, dict):
        d = cast(dict[str, object], node)
        if "Agg" in d:
            return False
        if "Column" in d:
            return True
        return any(_has_bare_column(v) for v in d.values())
    if isinstance(node, list):
        return any(_has_bare_column(v) for v in cast(list[object], node))
    return False


def _is_scalar(e: pl.Expr) -> bool:
    """Heuristic: the expression has no un-aggregated column, so it yields one value (per group)."""
    return not _has_bare_column(json.loads(e.meta.serialize(format="json")))


def chi2_sf(x: float, df: int) -> float:
    """Upper tail of chi-square(df): the one p-value mapping (RULEBOOK §1, scipy.stats.chi2.sf)."""
    return float(chi2.sf(x, df))  # pyright: ignore[reportUnknownMemberType]


# ----------------------------------------------------------- comparisons -----
# SAS: missing is smaller than every number; a comparison is never missing (A1).
def lt(x: ExprOrNum, c: ExprOrNum) -> pl.Expr:
    """SAS `x < c` with missing smallest. Non-null pl.Boolean."""
    xe, ce = _e(x), _e(c)
    out = (
        pl.when(xe.is_null())
        .then(ce.is_not_null())
        .when(ce.is_null())
        .then(pl.lit(False))
        .otherwise(xe < ce)
        .fill_null(False)
    )
    return _named(x, out)


def le(x: ExprOrNum, c: ExprOrNum) -> pl.Expr:
    """SAS `x <= c`. Site: flag_few_credit_lines (findings P4, P5)."""
    return _named(x, ~lt(_e(c), x))


def gt(x: ExprOrNum, c: ExprOrNum) -> pl.Expr:
    """SAS `x > c` (missing > anything is false). Non-null pl.Boolean."""
    return _named(x, lt(_e(c), x))


def ge(x: ExprOrNum, c: ExprOrNum) -> pl.Expr:
    """SAS `x >= c`. Sites: pred_logistic = flag(ge(pd, 0.5)) (train, predict), the model_status tests
    of metrics_calculation, the whole-number test of %num (feature_engineering, predict)."""
    return _named(x, ~lt(x, c))


def eq(x: ExprOrNum, c: ExprOrNum) -> pl.Expr:
    """SAS `x = c` (`. = .` is true). Site: the KS remerge filter of metrics_calculation (R4)."""
    xe, ce = _e(x), _e(c)
    return _named(x, (xe.is_null() & ce.is_null()) | (xe == ce).fill_null(False))


def flag(cond: pl.Expr) -> pl.Expr:
    """SAS boolean assignment `x = (cond);` -> Int64 0/1. A null condition counts as 0."""
    return _named(cond, cond.fill_null(False).cast(pl.Int64))


# ------------------------------------------------------------ arithmetic -----
def div(a: ExprOrNum, b: ExprOrNum) -> pl.Expr:
    """Element-wise IEEE division (A13; experiment X04): numpy `np.divide` on Float64.
    Missing in either operand -> missing; division by 0 -> missing (SAS note, no inf).
    Mandatory for any scalar, literal or aggregate divisor. Inside `agg`, aggregate or literal
    operands give a scalar per group."""

    def run(s: pl.Series) -> pl.Series:
        num = np.asarray(s.struct.field("a").cast(pl.Float64).to_numpy(), dtype=np.float64)
        den = np.asarray(s.struct.field("b").cast(pl.Float64).to_numpy(), dtype=np.float64)
        with np.errstate(all="ignore"):
            q = np.asarray(np.divide(num, den), dtype=np.float64)
        q[~np.isfinite(q)] = np.nan
        return pl.Series(q, dtype=pl.Float64, nan_to_null=True)

    ae, be = _e(a), _e(b)
    out = pl.struct(ae.cast(pl.Float64).alias("a"), be.cast(pl.Float64).alias("b")).map_batches(
        run, return_dtype=pl.Float64, returns_scalar=_is_scalar(ae) and _is_scalar(be)
    )
    return _named(a, out)


def sas_sum(*args: ExprOrNum) -> pl.Expr:
    """SAS sum(a, b, ...): ignores missing; all missing -> missing. Float64."""
    es = [_e(a).cast(pl.Float64) for a in args]
    out = pl.when(pl.all_horizontal([e.is_null() for e in es])).then(None).otherwise(pl.sum_horizontal(es))
    return _named(args[0], out)


def sas_min(*args: ExprOrNum) -> pl.Expr:
    """SAS min(...): ignores missing; all missing -> missing."""
    return _named(args[0], pl.min_horizontal([_e(a) for a in args]))


def sas_max(*args: ExprOrNum) -> pl.Expr:
    """SAS max(...): ignores missing; all missing -> missing."""
    return _named(args[0], pl.max_horizontal([_e(a) for a in args]))


def sas_log(x: ExprOrNum) -> pl.Expr:
    """SAS log(x): natural log; x <= 0 or missing -> missing."""
    xe = _e(x)
    return _named(x, pl.when(xe > 0).then(xe.log()).otherwise(None))


def sas_exp(x: ExprOrNum) -> pl.Expr:
    """SAS exp(x): overflow (x > ~709.78) -> missing, not inf (S1; experiment X05: exp(1000) = .)."""
    v = _e(x).cast(pl.Float64).exp()
    return _named(x, pl.when(v.is_finite()).then(v))


_ROUND_FUZZ_CAP = 1e-6
_ROUND_FUZZ = 1e-12


def sas_round(x: ExprOrNum) -> pl.Expr:
    """SAS round(x) to an integer (finding P8): with a = |x| and eps = min(1e-6, a * 1e-12), the result is
    floor((a + 0.5) + eps) with the sign of x (SAS's documented fuzz; SAS experiment X11 reproduces nine
    half-way thresholds to the bit); an integer is returned unchanged. Missing stays missing."""
    xf = _e(x).cast(pl.Float64)
    a = xf.abs()
    fl = a.floor()
    eps = pl.min_horizontal(pl.lit(_ROUND_FUZZ_CAP), a * _ROUND_FUZZ)
    r = xf.sign() * ((a + 0.5) + eps).floor()
    return _named(x, pl.when(a == fl).then(xf).otherwise(r) + 0.0)


def sas_round_scalar(x: float) -> float:
    """Scalar form of sas_round (same rule)."""
    if not math.isfinite(x):
        return x
    a = abs(x)
    eps = min(_ROUND_FUZZ_CAP, a * _ROUND_FUZZ)
    r = a if a == math.floor(a) else math.floor((a + 0.5) + eps)
    return math.copysign(float(r), x) + 0.0


def sql_sum(x: ExprOrNum) -> pl.Expr:
    """PROC SQL sum(x): missing when there are 0 non-missing values (S10; experiment X05)."""
    xe = _e(x)
    return _named(x, pl.when(xe.count() > 0).then(xe.sum()))


def sql_mean(x: ExprOrNum) -> pl.Expr:
    """PROC SQL mean(x): missing when there are 0 non-missing values (S10; experiment X05)."""
    xe = _e(x)
    return _named(x, pl.when(xe.count() > 0).then(xe.mean()))


def sql_min(x: ExprOrNum) -> pl.Expr:
    """PROC SQL min(x): missing when there are 0 non-missing values (S10)."""
    xe = _e(x)
    return _named(x, pl.when(xe.count() > 0).then(xe.min()))


def sql_max(x: ExprOrNum) -> pl.Expr:
    """PROC SQL max(x): missing when there are 0 non-missing values (S10; experiment X05)."""
    xe = _e(x)
    return _named(x, pl.when(xe.count() > 0).then(xe.max()))


_NUM_RE = r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$"


def input_best32(s: pl.Expr) -> pl.Expr:
    """SAS input(s, best32.): numeric text -> Float64; anything else ('NA', '') -> missing. The
    argument is text. For a column PROC IMPORT typed as numeric SAS first writes the number as BEST12.
    text, so the value can change (X09: 1234567890123 is read back as 1234567900000): the callers
    render such a column with sas_best12 before calling. Overflow ('1E400') and inf -> missing.
    RESOLVED (post-parity): X06 confirms the 32-column cut (37 digits read as 32); leading blanks ignored."""
    t = s.cast(pl.String).str.slice(0, 32).str.strip_chars()
    v = t.cast(pl.Float64, strict=False)
    return _named(s, pl.when(t.str.contains(_NUM_RE) & v.is_finite()).then(v))


def merge_one_to_one(*frames: pl.DataFrame) -> pl.DataFrame:
    """SAS one-to-one MERGE (no BY; A6, experiment X01a). Rows = the longest frame; shorter frames
    are padded with nulls at the end. Columns are in frame order (first appearance). A later frame's
    column with the same name OVERWRITES the earlier one on the rows the later frame has; on the rows
    after its end the earlier value is kept (finding P9; SAS experiment X15A)."""
    if not frames:
        return pl.DataFrame()
    n = max(f.height for f in frames)
    cols: dict[str, pl.Series] = {}
    for f in frames:
        for s in f.iter_columns():
            pad = n - s.len()
            prev = cols.get(s.name)
            rest = pl.Series(s.name, [None] * pad, dtype=s.dtype) if prev is None else prev.slice(s.len())
            cols[s.name] = (
                s
                if pad == 0
                else pl.concat([s.to_frame(), rest.to_frame()], how="vertical_relaxed").to_series()
            )
    return pl.DataFrame(list(cols.values()))


def date9(d: dt.date) -> str:
    """DATE9. with fixed English month names (A16): 05NOV2026."""
    return f"{d.day:02d}{MONTHS[d.month - 1]}{d.year}"


def today_date9() -> str:
    """today() formatted DATE9. (training_date / validation_date)."""
    return date9(dt.date.today())


# ------------------------------------------------------------ formatting -----
def _sig15(x: float) -> Decimal:
    """The value's 15-significant-digit decimal form (A18, X04)."""
    return Decimal(f"{abs(x):.14e}")


def _strip_zeros(s: str) -> str:
    return s.rstrip("0").rstrip(".") if "." in s else s


def _fixed(x: float, dec: int, keep_sign: bool = False) -> str:
    """|x| rounded half up (= half away from zero) at `dec` decimals from its 15-digit form.
    A negative value that rounds to zero loses its sign unless `keep_sign`."""
    q = _sig15(x).quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP, context=_CTX)
    s = f"{q:f}"
    return "-" + s if x < 0 and (q != 0 or keep_sign) else s


def _enotation(x: float, w: int, mant_dec: int | None = None) -> str:
    d = _sig15(x)
    neg = x < 0
    exp = d.adjusted()
    mant = Decimal(0)
    for _ in range(2):
        es = f"E{exp}"
        dec = mant_dec if mant_dec is not None else max(w - len(es) - (1 if neg else 0) - 2, 0)
        mant = d.scaleb(-exp).quantize(Decimal(1).scaleb(-dec), rounding=ROUND_HALF_UP, context=_CTX)
        if mant >= 10:
            exp += 1
            continue
        break
    s = f"{mant:f}"
    if mant_dec is None:
        s = _strip_zeros(s)
    return ("-" if neg else "") + s + f"E{exp}"


def _best_e(x: float, w: int) -> str:
    """E-notation text of BESTw. at w != 12 (X05, X06). With at least two mantissa decimals
    available ('1.23E-6' at w=8, '1.23E6' at w=6) it is the decimal form; with fewer the integer-mantissa
    form fills the width ('123E-7' at w=6, '-12E-6', '123E9'), trailing zeros stripped ('1E-5', '15E-6').
    The text never exceeds w: digits are dropped until the
    printed exponent fits (BEST6 of 1.005e-9 -> '1E-9'); the digits kept there are unverified."""
    d15 = _sig15(x)
    neg = 1 if x < 0 else 0
    adj = d15.adjusted()
    if w - len(f"E{adj}") - neg - 2 >= 2:
        return _enotation(x, w)
    sign = "-" if neg else ""
    out = ""
    for nd in range(max(w - neg - len(f"E{adj}"), 1), 0, -1):  # fewer digits until the text fits w
        e = adj - nd + 1
        m = int(d15.scaleb(-e).quantize(Decimal(1), rounding=ROUND_HALF_UP, context=_CTX))
        if m >= 10**nd:
            m //= 10
            e += 1
        while m % 10 == 0:
            m //= 10
            e += 1
        out = sign + str(m) + f"E{e}"
        if len(out) <= w:
            break
    return out


def _best_below_one(x: float, w: int) -> str:
    """BESTw. for 0 < |x| < 1 at w != 12: plain notation (w - 2 - sign decimals, trailing zeros
    stripped) when |x| >= 1e-5 and the plain text is not zero, else E-notation (_best_e). X06 cells:
    1.23E-5 -> BEST8 '0.000012', BEST6 '123E-7'; 9.9999E-6 -> '1E-5'; 1.2345E-4 -> BEST6 '0.0001';
    -1.23E-5 -> BEST8 '-0.00001', BEST6 '-12E-6'; X05: 0.000015 -> BEST6 '15E-6', BEST8 '0.000015'."""
    neg = 1 if x < 0 else 0
    if abs(x) >= 1e-5:
        plain = _strip_zeros(_fixed(x, max(w - 2 - neg, 0)))
        if plain.strip("-0.") != "":
            return plain
    return _best_e(x, w)


def _best32(x: float) -> str:
    """BEST32. text of a non-zero finite value (experiments X09, X11, X13, X14, X15).
    A whole number below 2**106 whose text fits in 32 characters prints every digit of the double
    (12345678901234567 -> '12345678901234568'; X15: the double below 2**106 in full, 2**106 not, and
    no 32-digit negative). Any other value from 1e-5 up: |x| * (1 + 2**-52) is CUT, not rounded, to
    15 - (number of integer digits) decimals, 16 characters before the sign, trailing zeros stripped:
    1234567.123456789 -> '1234567.12345678', 2/3 -> '0.66666666666666', 2499.9999999999995 -> '2500',
    0.1 + 0.7 -> '0.8' (X09 and X11: 620 values, all reproduced; X13: 51 more from 1e15 to 2**53).
    The rest is E-notation, a mantissa of 14 digits: |x| * (1 + 2**-49) cut to 14 significant digits
    (the three doubles below 1e-5 -> '1E-5', 9.276747499544084e-200 -> '9.2767474995441E-200',
    1e32 -> '1E32'). That factor reproduces 1,147 of the 1,172 E-notation values measured (X11, X13,
    X14); the 25 others (24 of X14, one of X13) are doubles within an ulp or two of a step of the
    mantissa, where SAS's own arithmetic decides: NOT pinned down. A value below the smallest normal
    double prints '0' (X14; a negative one is not measured)."""
    sign = "-" if x < 0 else ""
    ax = abs(x)
    if ax < _MIN_NORMAL:
        return "0"
    if ax == math.floor(ax):
        whole = sign + str(int(ax))
        if ax < 2.0**106 and len(whole) <= 32:
            return whole
    elif ax >= 1e-5:
        xp = ax * (1 + 2.0**-52)
        dec = max(15 - len(str(int(xp))), 0)
        q = Decimal(xp).quantize(Decimal(1).scaleb(-dec), rounding=ROUND_DOWN, context=_CTX)
        return sign + _strip_zeros(f"{q:f}")
    d = _CTX_EXACT.multiply(Decimal(ax), Decimal(1 + 2.0**-49))
    exp = d.adjusted()
    mant = d.scaleb(-exp, context=_CTX_EXACT).quantize(
        Decimal(1).scaleb(-13), rounding=ROUND_DOWN, context=_CTX_EXACT
    )
    return sign + _strip_zeros(f"{mant:f}") + f"E{exp}"


def sas_best(x: float | None, w: int) -> str:
    """BESTw. text. Plain notation rounded half up from the value's 15-significant-digit form
    (A18); at w = 12 E-notation for 0 < |x| < 1e-5 with the mantissa rounded to fill w characters and
    trailing zeros stripped (A15). Integers print without a decimal point. None -> '' (export).
    BEST8. is what `select ... into` stores (A9). A value whose integer part does not fit in w
    characters also prints in E-notation (experiment X03: 123456789 -> '1.2346E8' at BEST8.).
    At other widths a value below 1 prints in E-notation when plain notation cannot show it within w
    (experiment X05: 0.000015 -> BEST6 '15E-6', BEST8 and BEST12 '0.000015').
    RESOLVED (post-parity): X06 fixes the BEST8/BEST6 cells below 1 and above 1e11 (see _best_e).
    Still unverified: a w too small to show any digit (-100 at w=3 gives '-1E2').
    At w = 32 (the medians of income_medians.csv) the text is `_best32`: more than 15 digits for a
    whole number, a cut and not a rounding otherwise (X09, X11, X13-X15).
    Non-finite -> ''."""
    if x is None or not math.isfinite(x):
        return ""
    if x == 0:
        return "0"
    if w == 32:
        return _best32(x)
    ax = abs(x)
    if w != 12 and ax < 1:
        return _best_below_one(x, w)
    if ax >= 1e-5:
        s = f"{x:.15g}"
        if "e" not in s and len(s) <= w:  # already fits: rounding to w characters is a no-op
            return s
        neg = 1 if x < 0 else 0
        ilen = len(str(int(ax))) + neg
        if ilen <= w:
            out = _strip_zeros(_fixed(x, max(w - 1 - ilen, 0)))
            if len(out) <= w:
                return out
    return _enotation(x, w) if w == 12 else _best_e(x, w)


def sas_best12(x: float | None) -> str:
    """BEST12., the default export format of unformatted numerics."""
    return sas_best(x, 12)


def fmt_wd(x: float | None, w: int, d: int) -> str:
    """w.d (e.g. 8.4, 8.2, 10.4): half away from zero from the 15-significant-digit form (A24).
    None -> ''. When the text exceeds w, decimals are dropped one at a time (SAS keeps the width);
    when even 0 decimals do not fit, BESTw. is used (experiment X05: 123456789 at 8.4 -> '1.2346E8').
    A negative value that rounds to zero keeps its minus sign (X05: -0.00001 at 8.4 prints ' -0.0000',
    right-aligned in w; this function returns the stripped '-0.0000', as the export writes it)."""
    if x is None or not math.isfinite(x):
        return ""
    for dec in range(d, -1, -1):
        s = _fixed(x, dec, keep_sign=True)
        if len(s) <= w:
            return s
    return sas_best(x, w)


def fmt_oddsr(x: float | None, w: int, d: int) -> str:
    """ODDSRw.d (X06: ODDSR8.3). In range [10**-d, 10**(w-d-2) - 10**-d] it is w.d (half away from
    zero, 15-digit form); below the range it prints '<' + the lower bound and above it '>' + the upper
    bound ('<0.001', '>999.999'). The range test is on the value, not the rounded text (X06: 0.0009999
    -> '<0.001', 1000 -> '>999.999'). None -> ''; the text is stripped, as the export writes it."""
    if x is None or not math.isfinite(x):
        return ""
    lo = Decimal(1).scaleb(-d)
    hi = Decimal(10) ** (w - d - 2) - lo  # one position is reserved (X06: max 999.999 at 8.3)
    if x < float(lo):
        return "<" + f"{lo:f}"
    if x > float(hi):
        return ">" + f"{hi:f}"
    return fmt_wd(x, w, d)


def fmt_percent(x: float | None, w: int, d: int) -> str:
    """percentw.d: 100*x with d decimals and '%', keeping width w, so percent8.2 prints
    '5.00%' but '100.0%' (A14, A24). A negative value is enclosed in parentheses and right-aligned
    inside them (experiment X05: -0.05 at percent8.2 -> '( 5.00%)'); this is SAS's text before any
    stripping. None -> ''.
    RESOLVED (post-parity): X06 overflow cells (1234%, ( 1234%), 0.00%) match. Still unverified: a negative
    value that rounds to zero prints unsigned; the BEST fallback for 6+ digit percentages (>= 123456%)."""
    if x is None or not math.isfinite(x):
        return ""
    v = x * 100
    room = w - 2  # percentw.d reserves two positions beyond the digits and '%' (the parentheses)
    body = ""
    for dec in range(d, -1, -1):
        body = _fixed(abs(v), dec) + "%"
        if len(body) <= room:
            break
    else:
        body = sas_best(abs(v), max(room - 1, 1)) + "%"
    if v < 0 and body.strip("0.%") != "":
        return "(" + body.rjust(room) + ")"
    return body


def sas_d8(x: float | None) -> str:
    """D8. as exported for ODS statistics (inventory: model_coefficients.csv, ROC rows).
    |x| < 1e-5: E-notation filling width 8 with trailing zeros stripped, as BEST8. ('6.321E-6',
    reviewer B-02; evidence judge/runs, 5 SAS cells); else fixed with min(8 - integer digits - 1 - sign,
    max(4, decimals for 3 significant digits)) decimals ('-4.1668', '0.00250', '0.0170'), decided
    from the ROUNDED value (a carry across a power of ten re-decides once); a value that does not fit
    in 8 falls back to BEST8. Fitted on 1,239 fixed reference cells.
    RESOLVED (post-parity): X06 fixes 14 cells. |x| >= 100 printing 1 decimal is interpolated (no cell in
    [1e3, 1e4), none negative >= 100); E-notation below 1e-5 is only bracketed (6.42e-6 E, 1e-5 fixed)."""
    if x is None or not math.isfinite(x):
        return ""
    if x == 0:
        return "0"
    ax = abs(x)
    if ax < 1e-5:
        return _enotation(x, 8)
    neg = 1 if x < 0 else 0

    def decimals(v: float) -> int:
        cap = 8 - len(str(int(abs(v)))) - 1 - neg
        need = max(0, 3 - (_sig15(v).adjusted() + 1))
        return max(0, min(cap, max(4, need)))

    if ax >= 100:  # X06: 123.5, 12345.7, 250.5; 1234568 (no room for a decimal)
        s = _fixed(x, max(0, min(8 - len(str(int(ax))) - 1 - neg, 1)))
        return s if len(s) <= 8 else sas_best(x, 8)
    dec = decimals(x)
    s = _fixed(x, dec)
    dec2 = decimals(float(s))
    if dec2 != dec:
        s = _fixed(x, dec2)
    return s if len(s) <= 8 else sas_best(x, 8)


def sas_d12_3(x: float | None) -> str:
    """D12.3 as exported (inventory: printed_association.csv, printed_rsquare.csv,
    printed_fit_statistics.csv InterceptOnly): |x| >= 1e4 -> 0 decimals; 1e-4 <= |x| < 1e4 -> 6
    decimals; 0 < |x| < 1e-4 -> 9 decimals, never E-notation (X06: 1.2345E-6 -> '0.000001235'); last
    digit half up (A18). The branch is chosen from the value rounded at the branch's decimals
    (9999.9999996 -> '10000'); a text wider than 12 falls back to BEST12; 0 prints '0'.
    RESOLVED (post-parity): X06 verifies 100 <= |x| < 1e4 (6 decimals) and 9 decimals down to 1.2e-6.
    Unverified: |x| below about 1e-6 (rounds to 0.000000000, sign dropped)."""
    if x is None or not math.isfinite(x):
        return ""
    if x == 0:
        return "0"

    def decimals(v: float) -> int:
        av = abs(v)
        return 0 if av >= 1e4 else 6 if av >= 1e-4 else 9

    dec = decimals(x)
    for _ in range(3):
        s = _fixed(x, dec)
        nxt = decimals(float(s))
        if nxt == dec:
            return s if len(s) <= 12 else sas_best(x, 12)
        dec = nxt
    return sas_best(x, 12)


def sas_pvalue(x: float | None) -> str:
    """PVALUE6.4: '<.0001' below 0.0001, else 4 decimals with SAS's leading-zero rule
    (width 6 holds '0.0512' and '1.0000', so the zero is kept)."""
    if x is None or not math.isfinite(x):
        return ""
    if x < 0.0001:
        return "<.0001"
    return _fixed(x, 4)


# ------------------------------------------------------------------- I/O -----
def proc_import_csv(path: Path, guessingrows: int | None = 20) -> pl.DataFrame:
    """PROC IMPORT dbms=csv getnames=yes (RULEBOOK §2, A3): numeric if every one of the first
    `guessingrows` data values parses as a number (None = all rows), else text of width = the
    longest of those values, LATER VALUES TRUNCATED to that width, as PROC IMPORT does (guessingrows=20
    sized MonthlyIncome $5., so 159791 -> 15979 on 77 rows: the SAS programs now read cs-training.csv
    and cs-test.csv with guessingrows=max, the callers pass None); an all-empty
    column in the guessing window is text of width 1; empty header -> VAR1; names cut to 32.
    Numeric columns are Float64 (unparseable later values -> null); empty cells are null."""
    raw = pl.read_csv(path, infer_schema=False)
    names: list[str] = []
    for i, c in enumerate(raw.columns):
        n = (c if c != "" else f"VAR{i + 1}")[:32]
        if n in names:
            raise ValueError(f"duplicate column name after truncation: {n!r}")
        names.append(n)
    raw.columns = names
    window = raw if guessingrows is None else raw.head(guessingrows)
    out: list[pl.Series] = []
    for n in names:
        col = raw.get_column(n).replace("", None)
        vals = window.get_column(n).drop_nulls().filter(window.get_column(n).drop_nulls() != "")
        if vals.len() > 0 and bool(vals.str.strip_chars().str.contains(_NUM_RE).all()):
            t = col.str.strip_chars()
            num = pl.select(
                pl.when(t.str.contains(_NUM_RE)).then(t.cast(pl.Float64, strict=False)).otherwise(None)
            ).to_series()
            out.append(num.alias(n))
        else:
            mx = vals.str.len_chars().max()
            width = mx if isinstance(mx, int) and mx > 0 else 1
            out.append(col.str.slice(0, width).alias(n))
    return pl.DataFrame(out)


_WD_RE = re.compile(r"^(\d+)\.(\d+)$")
_PCT_RE = re.compile(r"^percent(\d+)\.(\d+)$", re.IGNORECASE)
_BEST_RE = re.compile(r"^best(\d+)\.$", re.IGNORECASE)
_W_RE = re.compile(r"^(\d+)\.$")


def _render_column(s: pl.Series, fmt: str | None) -> list[str]:
    if s.dtype == pl.Boolean:  # SAS has no boolean: 1 / 0
        s = s.cast(pl.Int64)
    vals: list[object] = s.to_list()
    if s.dtype == pl.String:  # SAS's DSD export trims trailing blanks
        return ["" if v is None else str(v).rstrip(" ") for v in vals]
    if s.dtype == pl.Date or (fmt is not None and fmt.lower() == "date9."):
        epoch = dt.date(1960, 1, 1)
        res: list[str] = []
        for v in vals:
            if v is None:
                res.append("")
            elif isinstance(v, dt.date):
                res.append(date9(v))
            else:
                res.append(date9(epoch + dt.timedelta(days=int(float(str(v))))))
        return res
    nums: list[float | None] = [None if v is None else float(str(v)) for v in vals]
    if fmt is None:
        if s.dtype.is_integer():
            return ["" if v is None else (str(int(v)) if abs(v) < 1e11 else sas_best12(v)) for v in nums]
        return [sas_best12(v) for v in nums]
    m = _WD_RE.match(fmt)
    if m:
        return [fmt_wd(v, int(m.group(1)), int(m.group(2))) for v in nums]
    m = _PCT_RE.match(fmt)
    if m:
        return [fmt_percent(v, int(m.group(1)), int(m.group(2))) for v in nums]
    m = _BEST_RE.match(fmt)
    if m:
        return [sas_best(v, int(m.group(1))) for v in nums]
    m = _W_RE.match(fmt)
    if m:
        return [fmt_wd(v, int(m.group(1)), 0) for v in nums]
    raise ValueError(f"unsupported format {fmt!r}")


def _quote(f: str) -> str:
    return '"' + f.replace('"', '""') + '"' if any(ch in f for ch in ',"\n\r') else f


def write_sas_csv(df: pl.DataFrame, path: Path, formats: Mapping[str, str] | None = None) -> None:
    """PROC EXPORT dbms=csv. Unformatted numeric columns -> sas_best12; `formats` maps a
    column to 'w.d', 'percentw.d' or 'date9.'; str columns written verbatim (pre-rendered
    model-statistics text, A20, trailing blanks trimmed); missing -> empty field; header = column
    names; LF line ends. Also 'bestw.' and 'w.' formats; Boolean columns write 1/0. Creates the
    parent folder (S12). A `formats` key that names no column, or any format on a text column,
    raises ValueError (A-07)."""
    fm = dict(formats or {})
    for k in fm:
        if k not in df.columns:
            raise ValueError(f"format given for unknown column {k!r}")
        if df.schema[k] == pl.String:
            raise ValueError(f"format {fm[k]!r} given for text column {k!r}")
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = [_render_column(df.get_column(c), fm.get(c)) for c in df.columns]
    with path.open("w", encoding="utf-8", newline="") as fh:
        fh.write(",".join(_quote(c) for c in df.columns) + "\n")
        rows: list[tuple[str, ...]] = list(zip(*cols, strict=True)) if cols else []
        for row in rows:
            fh.write(",".join(_quote(f) for f in row) + "\n")


# ------------------------------------------------------------ procedures -----
def proc_rank_groups(x: pl.Series, k: int, descending: bool = False) -> pl.Series:
    """PROC RANK groups=k: rank with ties = mean, group = floor(rank * k / (n + 1)), n = number
    of non-missing values; missing -> missing. Int64."""
    n = x.len() - x.null_count()
    r = x.rank("average", descending=descending)
    g = np.floor(np.divide(np.asarray(r.to_numpy(), dtype=np.float64) * k, n + 1))
    return pl.Series(x.name, g, dtype=pl.Float64, nan_to_null=True).cast(pl.Int64)


@dataclass
class LogisticFit:
    """A fitted logistic model P(y = 1) on columns `names`. `names[0]` is "Intercept";
    `loglik` is the log-likelihood (-2 Log L = -2 * loglik). `converged` is False after a singular
    system, complete or quasi-complete separation, an exhausted line search or the iteration cap.
    `separation` is "complete" or "quasicomplete" on the estimates `_fit_as_sas` keeps. On a fit
    with a variable `n_iter` is SAS's iteration count and the estimates are those of that
    iteration, converged or separated (`_fit_as_sas`)."""

    names: list[str]
    beta: FloatArray
    cov: FloatArray  # inverse information matrix (NaN when it cannot be computed)
    loglik: float
    n_iter: int
    converged: bool
    separation: str | None = None


def _loglik(eta: FloatArray, y: FloatArray) -> float:
    return float(np.sum(y * eta - np.logaddexp(0.0, eta)))


def _expit(eta: FloatArray) -> FloatArray:
    with np.errstate(over="ignore"):
        return np.asarray(1.0 / (1.0 + np.exp(-eta)), dtype=np.float64)


def fit_logistic(x: FloatArray, y: FloatArray, names: Sequence[str]) -> LogisticFit:
    """Newton-Raphson from all-zero coefficients, halving the step while -2 Log L increases,
    until max|full Newton step| < 1e-10 (RULEBOOK §2 model fitting, A17). `x` includes the intercept
    column. Convergence is tested on the FULL step, never the damped one. `converged=False` when the
    system is singular (LinAlgError), the line search is exhausted, 100 iterations pass, or some row is
    perfectly predicted (pd within 1e-8 of its response) while the standardized information matrix is
    rank-deficient (min eigenvalue < 1e-10): complete or quasi-complete separation.
    RESOLVED (post-parity): caps are port choices.
    Since 2026-11-17 (owner's decision) `stepwise_logistic` uses this fit for the intercept-only
    model alone, whose estimate is log(events / non-events) either way; every fit with a variable
    is `_fit_as_sas`, which stops where SAS stops."""
    b = np.zeros(x.shape[1])
    ll = _loglik(x @ b, y)
    converged = False
    n_iter = 0
    try:
        for _ in range(100):
            n_iter += 1
            p = _expit(x @ b)
            w = p * (1.0 - p)
            step = np.linalg.solve(x.T @ (x * w[:, None]), x.T @ (y - p))
            if not bool(np.all(np.isfinite(step))):
                break
            t = 1.0
            found = False
            for _ in range(40):
                if _loglik(x @ (b + t * step), y) >= ll - 1e-12 * abs(ll):
                    found = True
                    break
                t /= 2.0
            if not found:  # halving exhausted: stalled, not converged
                break
            b = b + t * step
            ll = _loglik(x @ b, y)
            if float(np.max(np.abs(step))) < 1e-10:
                converged = True
                break
    except np.linalg.LinAlgError:
        converged = False
    p = _expit(x @ b)
    w = p * (1.0 - p)
    if converged and bool(np.any((y == 1) & (p > 1 - 1e-8)) or np.any((y == 0) & (p < 1e-8))):
        info = x.T @ (
            x * w[:, None]
        )  # perfectly predicted rows: separation if the information is rank-deficient
        dd = np.sqrt(np.diag(info))
        if bool(np.any(dd <= 0)) or float(np.linalg.eigvalsh(info / np.outer(dd, dd)).min()) < 1e-10:
            converged = False  # the Newton step underflowed, the estimates diverge
    try:
        cov = np.linalg.inv(x.T @ (x * w[:, None]))
    except np.linalg.LinAlgError:
        cov = np.full((x.shape[1], x.shape[1]), np.nan)
        converged = False
    return LogisticFit(list(names), b, cov, ll, n_iter, converged)


def _p_w_r(eta: FloatArray, y: FloatArray) -> tuple[FloatArray, FloatArray, FloatArray]:
    """Probability, weight and residual y - p of each row as SAS's fit forms them
    (singular-information.md, rule 1). With e = exp(-|eta|), hi = 1 / (1 + e) is the probability of
    the likelier outcome and lo = e * hi that of the other; lo is exactly 0 when hi rounds to 1
    (|eta| > 53 ln 2 = 36.7368). The weight is hi * lo, and the residual is taken from hi and lo, so
    a probability near 0 is treated as one near 1 and a row beyond the limit has weight 0."""
    e = np.exp(-np.abs(eta))
    hi = 1.0 / (1.0 + e)
    lo = np.where(hi == 1.0, 0.0, e * hi)
    up = eta >= 0
    p = np.where(up, hi, lo)
    r = np.where(y == 1, np.where(up, lo, hi), -p)
    return (
        np.asarray(p, dtype=np.float64),
        np.asarray(hi * lo, dtype=np.float64),
        np.asarray(r, dtype=np.float64),
    )


def _kept(a: FloatArray) -> list[int]:
    """The parameters SAS does not leave out of a singular information matrix `a`
    (singular-information.md, rule 2): taken in order, intercept first, a parameter is left out
    when its pivot (its diagonal element after the kept parameters before it are swept out) is not
    above 1e-9 times its own diagonal element. Measured on the designed cases of experiment x19:
    left out up to a relative pivot of about 8.6e-10, kept from about 1.18e-9, the same when a
    column is multiplied by 1000."""
    kept: list[int] = []
    for i in range(a.shape[0]):
        pivot = float(a[i, i])
        if kept:
            c = a[kept, i]
            pivot -= float(c @ np.linalg.solve(a[np.ix_(kept, kept)], c))
        if pivot > 1e-9 * float(a[i, i]):
            kept.append(i)
    return kept


def _solve_sas(a: FloatArray, g: FloatArray) -> FloatArray:
    """inverse(a) @ g with the left-out parameters' part 0 (`_kept`); an ordinary solve when none is."""
    kept = _kept(a)
    if len(kept) == a.shape[0]:
        return np.asarray(np.linalg.solve(a, g), dtype=np.float64)
    out = np.zeros(a.shape[0])
    if kept:
        out[kept] = np.linalg.solve(a[np.ix_(kept, kept)], g[kept])
    return out


def _inv_sas(a: FloatArray) -> FloatArray:
    """The inverse of `a` with the rows and columns of the left-out parameters 0 (`_kept`); the
    ordinary inverse when none is left out. A parameter left out at the last iteration of a fit is
    known afterwards by the exact 0 of its diagonal element in `LogisticFit.cov` (`_left_out`)."""
    kept = _kept(a)
    if len(kept) == a.shape[0]:
        return np.asarray(np.linalg.inv(a), dtype=np.float64)
    out = np.zeros(a.shape)
    if kept:
        out[np.ix_(kept, kept)] = np.linalg.inv(a[np.ix_(kept, kept)])
    return out


def _left_out(fit: LogisticFit) -> list[str]:
    """The parameters SAS left out at the last iteration of `fit` (singular information): those
    whose variance in `fit.cov` is exactly 0. They have no standard error and no Wald test."""
    return [n for i, n in enumerate(fit.names) if float(fit.cov[i, i]) == 0.0]


# global-wald-rule.md (experiment X20): SAS leaves a slope out of the global Wald test when its pivot is
# not above an absolute tolerance measured between 1e-16 (T1: left out) and 2e-16 (T2: kept); the port
# takes the midpoint. Not settled: the value inside the bracket, pivot or diagonal element (0.7% apart
# on seed 6), the order when two slopes are near it (only one ever was).
_GLOBAL_WALD_TOL = 1.5e-16


def global_wald(fit: LogisticFit, order: Sequence[str]) -> tuple[float, int]:
    """The Wald test of the global null hypothesis as SAS prints it: (chi-square, DF).
    A step with a parameter left out of a singular information matrix (`_left_out`) has no
    chi-square (NaN, the cells are empty) and DF = the variables not left out
    (singular-information.md). Otherwise the chi-square is b' G b over the slopes, G the inverse of
    the slopes' block of `fit.cov` (intercept left out) taken by sweeping the slopes in `order` (the
    MODEL statement's): a slope whose pivot, its variance given the slopes swept before it, is not
    above `_GLOBAL_WALD_TOL` is left out (its row and column of G are 0). The DF stays the number of
    slopes (global-wald-rule.md: seed 6 step 7, 406.4827 with DF 7)."""
    slopes = sorted(fit.names[1:], key=list(order).index)
    q = len(slopes)
    idx = [fit.names.index(s) for s in slopes]
    singular = [s for s in _left_out(fit) if s != "Intercept"]
    if singular:
        return math.nan, q - len(singular)
    v = fit.cov[np.ix_(idx, idx)]
    b = fit.beta[idx]
    kept: list[int] = []
    for i in range(q):
        pivot = float(v[i, i])
        if kept:
            c = v[kept, i]
            pivot -= float(c @ np.linalg.solve(v[np.ix_(kept, kept)], c))
        if pivot > _GLOBAL_WALD_TOL:
            kept.append(i)
    bk = b[kept]
    return float(bk @ np.linalg.solve(v[np.ix_(kept, kept)], bk)), q


def _fit_as_sas(x: FloatArray, y: FloatArray, names: Sequence[str]) -> LogisticFit | None:
    """The estimates PROC LOGISTIC ends with for a model with a variable, as `train.sas` calls it:
    SAS's own iteration, stopped where SAS stops it. Fisher scoring from the intercept-only
    estimates (intercept log(events / non-events), every other coefficient 0), at most 25
    iterations (SAS's MAXITER). An iteration whose step would lower the log likelihood is taken
    with SAS's ridge instead (RIDGING=RELATIVE, the default): the diagonal of the information
    matrix is multiplied by 1 + ridge, ridge = 1e-4 * 4**j, and j goes up by one until the log
    likelihood is not lower than before the iteration. j is kept from one ridged iteration of
    the fit to the next, and goes down by one after an iteration whose first ridge was accepted.
    Measured (experiment x17, ITPRINT on the reference feature file and on 12 row subsets of it,
    3,000 to 80,000 rows): 185 converged steps, 393 ridged iterations, ridges 0.0064 to 104.8576;
    every iteration line (ridge, -2 Log L, estimates) and every stop iteration is reproduced.
    Two other readings fail there: j kept after a first-trial success (17 steps, among them step
    8 of the reference data), j back to 0 after one (7 steps of the subsets). On the reference data 18 of the 19 steps are
    ridged at iteration 1; without the ridge the iteration breaks down at iteration 3.
    Review of 2026-11-17 (21 more inputs, SAS logs under out/review_fit, the cases of
    port/tests/data/sas_fit_cases.json): the first ridge of a fit is 1e-4 (9 fits start there);
    j has no floor at 0 (a separated step with ridges 0.0001 and then 0.000025; with a floor the
    kept estimates are 1.9% off); the ridge and the separation tests work together (9 separated
    steps with ridged iterations); ridges from 0.000025 to 419.4304.
    Not settled: how far below 1e-4 SAS goes (0.000025 is the smallest seen; no floor here), and
    a step that leaves the log likelihood exactly equal (taken here without a ridge).
    After each iteration, first SAS's convergence test (GCONV:
    gradient' * inverse information * gradient / (|log likelihood| + 1e-6) below 1e-8, all at the
    new estimates): the fit has converged and the estimates of THIS iteration are returned with
    the inverse information at them, `converged=True` (owner's decision 2026-11-17: SAS's
    estimates, not the fully converged ones; on few rows the two differ in the fourth digit of a
    coefficient, generated-inputs.md seeds 2, 6, 8, 26, 27). Then, from the 8th iteration on, the
    estimates SAS keeps for a model it declares separated ("Existence of Maximum Likelihood
    Estimates"; SAS warns and continues, "Results shown are based on the last maximum likelihood
    iteration"):
    complete separation when no observation is on the wrong side, that is every observation has
    probability above 0.5 of its observed response;
    else quasi-complete separation when some observation has probability >= 0.95 of its observed
    response and a diagonal element of the inverse information matrix for the standardized columns
    (mean 0, standard deviation 1, divisor n - 1), the intercept's own element left out, exceeds
    5000 (review of 2026-11-17: with the intercept's element, the largest when events are few,
    the port stopped one or two iterations before SAS on 6 steps; over the 18 quasi-complete
    steps in hand the variables' largest element is at most 4,678 before SAS's stop and at least
    5,932 at it, and no single limit fits when the intercept's counts). The iteration stops there and its
    estimates are returned, `converged=False`. None when neither is found in 25 iterations, a
    system is singular or no ridge up to 1e-4 * 4**40 keeps the log likelihood: what SAS does
    then is not measured, and the caller stops with an error.
    A singular information matrix (singular-information.md; experiment x19, 44 designed fits and
    10 raw inputs): the weights and residuals are those of `_p_w_r`, exactly 0 beyond
    |eta| = 36.7368, and wherever the inverse of the information is needed (the step, the ridged
    step, the convergence test, the 5000 test, the covariance) a parameter whose pivot is not above
    1e-9 of its own diagonal element is left out: its step is 0 and its row and column of the
    inverse are 0 (`_kept`). A parameter left out at the last iteration has variance 0 in the
    returned `cov` (`_left_out`); the caller gives it no Wald test and removes it at the next step.
    Measured on the ITPRINT runs of out/separation/sas (`migration/legacy-to-port/small-inputs.md`):
    18 complete steps, all stopped at iteration 8, the smallest probability of an observed response
    there from 0.539 (D11, 382 of 400 observations at 0.95 or above) to 0.9999; 8 quasi-complete
    steps, stopped at iterations 9 to 15, each at the first iteration whose largest diagonal element
    exceeds 5000. The stop iteration and the kept estimates are SAS's in all 26 (to 1e-10 relative).
    The rule is applied to every fit, also one whose maximum likelihood estimate exists: D6b and D6c
    (classes that overlap by one swap, 400 and 2000 rows) are declared quasi-complete by SAS at
    iterations 12 and 13 although the iteration would converge later. The 14 steps of those runs
    that SAS reports converged (3 to 13 iterations) pass the GCONV test here at SAS's iteration.
    The two-variable run (P3) fixes the start (the estimates of the step before give other numbers).
    Not settled by those runs: an observation at probability exactly 0.5 at the complete test, and
    the divisor of the standard deviation (n and n - 1 agree on the quasi-complete runs)."""
    b = np.zeros(x.shape[1])
    b[0] = math.log(float(y.sum()) / float(len(y) - y.sum()))
    with np.errstate(divide="ignore", invalid="ignore"):
        xs = np.column_stack([x[:, 0], (x[:, 1:] - x[:, 1:].mean(axis=0)) / x[:, 1:].std(axis=0, ddof=1)])
    ll = _loglik(x @ b, y)
    j = 0  # the next ridge to try is 1e-4 * 4**j
    try:
        for n_iter in range(1, 26):
            _, w, r = _p_w_r(x @ b, y)
            info = x.T @ (x * w[:, None])
            g = x.T @ r
            new_b = b + _solve_sas(info, g)
            new_ll = _loglik(x @ new_b, y)
            if new_ll < ll:  # the step lowers the log likelihood: SAS's ridge
                first_trial = True
                while True:
                    if j > 40:
                        return None
                    new_b = b + _solve_sas(info + np.diag(1e-4 * 4.0**j * np.diag(info)), g)
                    new_ll = _loglik(x @ new_b, y)
                    if not new_ll < ll:
                        break
                    j += 1
                    first_trial = False
                if first_trial:
                    j -= 1  # also below 0: SAS's next ridge after 1e-4 is 0.000025
            b, ll = new_b, new_ll
            _, w, r = _p_w_r(x @ b, y)
            info = x.T @ (x * w[:, None])
            g = x.T @ r
            if float(g @ _solve_sas(info, g)) / (abs(ll) + 1e-6) < 1e-8:
                # SAS's fit converged (GCONV): its estimates are those of this iteration
                return LogisticFit(list(names), b, _inv_sas(info), ll, n_iter, True)
            if n_iter < 8:
                continue
            p_obs = 1.0 - np.abs(r)  # the probability of the observed response, from hi and lo
            separation: str | None = None
            if bool(np.all(p_obs > 0.5)):
                separation = "complete"
            elif bool(np.any(p_obs >= 0.95)) and (
                float(np.diag(_inv_sas(xs.T @ (xs * w[:, None])))[1:].max()) > 5000.0
            ):
                separation = "quasicomplete"
            if separation is not None:
                return LogisticFit(list(names), b, _inv_sas(info), ll, n_iter, False, separation)
    except np.linalg.LinAlgError:
        return None
    return None


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


def _entry_score_chisq(
    x: FloatArray, y: FloatArray, cur: LogisticFit, others: Mapping[str, FloatArray]
) -> list[tuple[str, float]]:
    """The score chi-square with which each column of `others` (name -> values, in MODEL order)
    would enter the model `cur` fitted on the columns `x`; a column aliased with the model
    (relative residual information < 1e-8) is left out.
    SAS's estimates are not at a maximum, neither after a separated step nor after a converged
    one (the iteration stops at the GCONV test, `_fit_as_sas`), so the score of the model's own
    parameters is not zero, and SAS's statistic is U' I^-1 U over ALL parameters of the enlarged
    model at those estimates (the model's and the candidate's), not the candidate's part alone.
    By blocks: the model's own g' I_m^-1 g, plus the candidate's score corrected for g, squared
    over its residual information. Measured: the 175 score chi-squares SAS prints after the
    separated step "age" of five files agree to 1e-10 relative
    (migration/legacy-to-port/separation-rule.md part 3; port/tests/test_entry_score.py); after
    the converged steps of the reference data the 18 printed entry chi-squares are SAS's to the
    4 decimals printed, where the candidate's part alone at SAS's estimates is not (step 13:
    8.8017 against SAS's 8.7885; step 16: 29.7077 against 29.7637)."""
    p = _expit(x @ cur.beta)
    w = p * (1.0 - p)
    info = x.T @ (x * w[:, None])
    g = x.T @ (y - p)
    info_g = np.linalg.solve(info, g)
    own = float(g @ info_g)
    out: list[tuple[str, float]] = []
    for c, z in others.items():
        zwz = float(z @ (z * w))
        v = x.T @ (z * w)
        resid = zwz - float(v @ np.linalg.solve(info, v))
        # RESOLVED (post-parity): alias alternation not reached on judged inputs (path matches SAS);
        # a longer cycle would stop at the 500-step cap with RuntimeError.
        if zwz <= 0.0 or resid / zwz < 1e-8:
            continue  # aliased with the current model
        u = float(z @ (y - p))
        out.append((c, own + (u - float(v @ info_g)) ** 2 / resid))
    return out


def stepwise_logistic(
    df: pl.DataFrame,
    response: str,
    candidates: Sequence[str],
    slentry: float = 0.05,
    slstay: float = 0.05,
) -> StepwiseResult:
    """PROC LOGISTIC descending selection=stepwise exactly as RULEBOOK §2 (A5) and the train.sas
    stepwise inventory row: removal before entry; aliased candidates skipped (relative residual
    < 1e-8); enter the largest score chi-square (strict >, ties to the first in MODEL order);
    stop when nothing enters, or rather than have a model twice (recycling-rule.md: the models had
    are kept as sets of variables from the empty model of step 0 on; a removal that gives one of
    them is the last step; a best candidate whose entry would give one of them does not enter and
    the second-best is not tried). After a separated step the entry
    score chi-square is over all parameters of the enlarged model (see the entry loop). Reference implementation:
    migration/experiments/x02_stepwise_reference.py. Rows with a missing response or candidate are
    dropped. The model columns of each fit are in ENTRY order (names[0] = "Intercept").
    Every fit with a variable is SAS's own iteration stopped where SAS stops it (`_fit_as_sas`): at
    its convergence test, or at the iteration where it declares a separation, whose estimates SAS
    keeps with a warning before going on to the removal test (owner's decisions 2026-11-16 and
    2026-11-17, RULEBOOK §2).
    Raises RuntimeError when a fit neither converges nor separates in SAS's 25 iterations, or the
    500-step cap is hit."""
    return _stepwise_logistic_with_note(df, response, candidates, slentry, slstay)[0]


def _stepwise_logistic_with_note(
    df: pl.DataFrame,
    response: str,
    candidates: Sequence[str],
    slentry: float = 0.05,
    slstay: float = 0.05,
) -> tuple[StepwiseResult, str]:
    """`stepwise_logistic` with SAS's note on why the selection ended (the NOTE of its listing). The
    port writes the note to no file and the pipeline does not carry it; it is returned here for the
    tests, because two parts of the recycling rule cannot be told from the steps and the final model
    alone (port/tests/test_recycling.py)."""
    used = df.select([response, *candidates]).drop_nulls()
    y = np.asarray(used.get_column(response).to_numpy(), dtype=np.float64)
    z_all = {c: np.asarray(used.get_column(c).to_numpy(), dtype=np.float64) for c in candidates}
    order = {c: i for i, c in enumerate(candidates)}
    ones = np.ones(len(y))
    step = 0

    def mkey(m: str) -> int:
        return order[m]

    def fit(cols: list[str]) -> LogisticFit:
        x = np.column_stack([ones, *[z_all[c] for c in cols]])
        if not cols:  # intercept only: log(events / non-events)
            f = fit_logistic(x, y, ["Intercept"])
            if not f.converged:
                raise RuntimeError(f"stepwise_logistic: the fit at step {step} ({cols}) did not converge")
            return f
        # SAS's iteration, stopped where SAS stops: converged (GCONV) or separated, where SAS warns and
        # continues with that iteration's estimates, also when the maximum likelihood estimate exists
        sep = _fit_as_sas(x, y, ["Intercept", *cols])
        if sep is None:
            raise RuntimeError(
                f"stepwise_logistic: the fit at step {step} ({cols}) neither converged nor separated: "
                "SAS's iteration ended on 25 iterations, a singular system or no ridge that keeps the log likelihood"
            )
        if _left_out(sep):
            print(
                "WARNING: The information matrix is singular and thus the convergence is questionable. "
                "Try specifying a larger SINGULAR= value."
            )
        if sep.separation is not None:
            if sep.separation == "complete":
                print(
                    f"WARNING: There is a complete separation of data points in Step {step}. "
                    "The maximum likelihood estimate does not exist."
                )
            else:
                print(
                    f"WARNING: There is possibly a quasicomplete separation of data points in step {step}. "
                    "The maximum likelihood estimate may not exist."
                )
            print(
                "WARNING: The LOGISTIC procedure continues in spite of the above warning. "
                "Results shown are based on the last maximum likelihood iteration."
            )
        return sep

    model: list[str] = []
    cur = fit(model)
    res = StepwiseResult(intercept_only=cur, final=cur)
    note = ""
    # The models the selection has had, each the set of its variables, from the model without a
    # variable of step 0 on (recycling-rule.md): SAS ends the selection rather than have one twice.
    had: list[frozenset[str]] = [frozenset()]
    while step < 500:
        if model:  # removal first: smallest Wald chi-square, ties to the first in MODEL order
            best_w: tuple[float, str] | None = None
            singular = [c for c in _left_out(cur) if c in model]
            if len(singular) > 1:
                raise RuntimeError(
                    f"stepwise_logistic: step {step} left {singular} out of a singular information matrix; "
                    "which of two SAS removes first is not measured"
                )
            if singular:
                # a parameter left out at the last iteration has no Wald test and is removed at the next
                # step whatever the others' tests are: DF 0, no chi-square, no probability
                step += 1
                model.remove(singular[0])
                cur = fit(model)
                res.steps.append(
                    StepwiseStep(step, None, singular[0], 0, len(model), None, math.nan, math.nan, cur)
                )
                if frozenset(model) in had:
                    entered_before = len(res.steps) > 1 and res.steps[-2].entered == singular[0]
                    note = (
                        "Model building terminates because the last effect entered is removed by the Wald "
                        "statistic criterion."
                        if entered_before
                        else "Model building terminates because of recycling of previous steps."
                    )
                    break
                had.append(frozenset(model))
                continue
            for c in sorted(model, key=mkey):
                i = cur.names.index(c)
                wv = float(cur.beta[i] ** 2 / cur.cov[i, i])
                # equal up to rounding is a tie: on symmetric data (D10 of out/separation/sas, three
                # columns with the same role on a separated step) the equal chi-squares differ in the
                # 15th digit and SAS removes the first in MODEL order. 1e-9 is the port's choice.
                if best_w is None or wv < best_w[0] * (1.0 - 1e-9):
                    best_w = (wv, c)
            if best_w is not None and chi2_sf(best_w[0], 1) > slstay:
                step += 1
                model.remove(best_w[1])
                cur = fit(model)
                res.steps.append(
                    StepwiseStep(
                        step, None, best_w[1], 1, len(model), None, best_w[0], chi2_sf(best_w[0], 1), cur
                    )
                )
                if frozenset(model) in had:
                    # a model it has had: the removal is the last step and this model is final
                    entered_before = len(res.steps) > 1 and res.steps[-2].entered == best_w[1]
                    note = (
                        "Model building terminates because the last effect entered is removed by the Wald "
                        "statistic criterion."
                        if entered_before
                        else "Model building terminates because of recycling of previous steps."
                    )
                    break
                had.append(frozenset(model))
                continue
        best: tuple[float, str] | None = None
        x = np.column_stack([ones, *[z_all[c] for c in model]])
        for c, sc in _entry_score_chisq(x, y, cur, {c: z_all[c] for c in candidates if c not in model}):
            if best is None or sc > best[0]:
                best = (sc, c)
        if best is None or chi2_sf(best[0], 1) >= slentry:
            note = (
                "All effects have been entered into the model."
                if len(model) == len(candidates)
                else f"No (additional) effects met the {slentry:g} significance level for entry into the model."
            )
            break
        if frozenset([*model, best[1]]) in had:
            # the best candidate would give a model it has had: nothing enters, the second-best is not tried
            note = "Model building terminates because the next effect to be added recycles previous steps."
            break
        step += 1
        model.append(best[1])
        cur = fit(model)
        res.steps.append(
            StepwiseStep(step, best[1], None, 1, len(model), best[0], None, chi2_sf(best[0], 1), cur)
        )
        had.append(frozenset(model))
    else:
        raise RuntimeError("stepwise_logistic: 500 steps reached without stopping")
    res.final = cur
    return res, note


@dataclass
class RocAssociation:
    area: float | None
    std_err: float | None
    lower: float | None
    upper: float | None
    somers_d: float | None
    gamma: float | None
    tau_a: float | None


# ROCEPS, PROC LOGISTIC's tie tolerance (finding P1). SAS uses 0x3E46A09E667F3BCE, one ulp above the
# double sqrt(2**-53) = 1.0536712127723509e-8: experiment X08 (a pair is tied up to that distance, at
# every magnitude, and not tied one ulp further).
_TIE_EPS = math.nextafter(math.sqrt(2.0**-53), 1.0)
# The standard error of the ROC area groups the probabilities the same way with a smaller tolerance,
# 1000 * 2**-53 = 1.11e-13: experiments X10, X10b (two values 1000 ulps of 0.5 apart are equal there,
# 1001 are not; the same distance at 0, 0.3 and 0.85).
_SE_EPS = 1000 * 2.0**-53
# What PROC LOGISTIC divides a class of ONE observation by, where the standard error's formula has
# n - 1 = 0: constant('SQRTBIG'), sqrt of the largest double as SAS writes it. sqrt(0.5 / _SQRTBIG) is
# bit for bit the 6.106693348777218e-78 of X07 groups 91, 92 and X12 (70 groups); one ulp either side is not.
_SQRTBIG = 1.3407807929943e154


@dataclass
class _Pairs:
    conc: int
    disc: int
    tied: int
    n1: int
    n0: int
    v10: FloatArray
    v01: FloatArray


def _groups(ss: FloatArray, eps: float) -> npt.NDArray[np.int64]:
    """SAS groups the probabilities from the largest down: a value joins the current group while it is
    within `eps` of the group's largest value, else it opens a new group (finding P1; X07, X08).
    The group number is larger for a higher probability."""
    gg = np.zeros(len(ss), dtype=np.int64)
    top, g = 0.0, 0
    for k, i in enumerate(np.argsort(ss, kind="stable")[::-1].tolist()):
        v = float(ss[i])
        if k == 0 or top - v > eps:
            top, g = v, g - 1
        gg[i] = g
    return gg


def _pairs(y: pl.Series, score: pl.Series) -> _Pairs:
    d = pl.DataFrame({"y": y.cast(pl.Float64), "s": score.cast(pl.Float64)}).drop_nulls()
    yy = np.asarray(d.get_column("y").to_numpy(), dtype=np.float64)
    ss = np.asarray(d.get_column("s").to_numpy(), dtype=np.float64)
    # A pair is concordant, discordant or tied by the _TIE_EPS groups of its two members.
    gg = _groups(ss, _TIE_EPS)
    ev = np.sort(gg[yy == 1])
    ne = np.sort(gg[yy == 0])
    n1, n0 = len(ev), len(ne)
    lo_ne = np.searchsorted(ne, ev, side="left")
    le_ne = np.searchsorted(ne, ev, side="right")
    conc = int(lo_ne.sum())
    tied = int((le_ne - lo_ne).sum())
    # v10, v01 (the components of the standard error) compare the two members by their _SE_EPS groups:
    # two probabilities 1e-9 apart are tied in the area and different here (X07, X10).
    fg = _groups(ss, _SE_EPS)
    ev = np.sort(fg[yy == 1])
    ne = np.sort(fg[yy == 0])
    lo_ne = np.searchsorted(ne, ev, side="left")
    le_ne = np.searchsorted(ne, ev, side="right")
    lo_ev = np.searchsorted(ev, ne, side="left")
    le_ev = np.searchsorted(ev, ne, side="right")
    v10 = (lo_ne + 0.5 * (le_ne - lo_ne)) / max(n0, 1)
    v01 = ((n1 - le_ev) + 0.5 * (le_ev - lo_ev)) / max(n1, 1)
    return _Pairs(conc, n1 * n0 - conc - tied, tied, n1, n0, np.asarray(v10), np.asarray(v01))


def _ratio(a: float, b: float) -> float | None:
    return None if b == 0 else a / b


@overload
def roc_association(y: pl.Series, score: pl.Series) -> RocAssociation: ...
@overload
def roc_association(y: pl.Series, score: pl.Series, label: str) -> pl.DataFrame: ...
def roc_association(
    y: pl.Series, score: pl.Series, label: str | None = None
) -> RocAssociation | pl.DataFrame:
    """PROC LOGISTIC nofit + roc (ROCAssociation): Mann-Whitney area with ties counted 1/2,
    DeLong standard error, Wald CI with Z975, Somers' D, Gamma, Tau-a (inventory ROC rows).
    Tied = same ROCEPS group (`_pairs`). Without `label`: a RocAssociation of numbers (the caller adds the
    ROCModel label and renders every value with sas_d8). With `label`: the ONE-row frame the inventory
    rows specify (ROCModel, Area, StdErr, LowerArea, UpperArea, SomersD, Gamma, TauA; full-precision
    Float64). The standard error takes each class's components (`_pairs`: compared by the _SE_EPS
    groups) around the Area, sum of squares / (n - 1) / n; for a class of one observation the divisor
    is _SQRTBIG, not 0: it adds nothing that shows beside a class of two or more (X10: one defaulter and
    two others gives 0.5) and gives 6.1e-78, not 0, when both classes have one observation and the two
    probabilities are tied for the Area and different here (X07 groups 91, 92; X12).
    The limits stay within 0 and 1 (X07, X10; fix_Q26_small: UpperArea 1.0000). An undefined statistic
    (empty class; Gamma when all pairs are tied) is None, except TauA: on a single-class input it is 0
    (None only with at most one usable row)."""
    q = _pairs(y, score)
    n = q.n1 + q.n0
    p = q.n1 * q.n0
    area = _ratio(q.conc + 0.5 * q.tied, p)
    se: float | None = None
    if area is not None:
        s10 = math.fsum(((q.v10 - area) ** 2).tolist()) / (q.n1 - 1 if q.n1 >= 2 else _SQRTBIG) / q.n1
        s01 = math.fsum(((q.v01 - area) ** 2).tolist()) / (q.n0 - 1 if q.n0 >= 2 else _SQRTBIG) / q.n0
        se = math.sqrt(s10 + s01)
    cd = q.conc - q.disc
    r = RocAssociation(
        area,
        se,
        None if area is None or se is None else max(area - Z975 * se, 0.0),
        None if area is None or se is None else min(area + Z975 * se, 1.0),
        _ratio(cd, p),
        _ratio(cd, q.conc + q.disc),
        _ratio(cd, n * (n - 1) / 2),
    )
    if label is None:
        return r
    return pl.DataFrame(
        {
            "ROCModel": [label],
            "Area": [r.area],
            "StdErr": [r.std_err],
            "LowerArea": [r.lower],
            "UpperArea": [r.upper],
            "SomersD": [r.somers_d],
            "Gamma": [r.gamma],
            "TauA": [r.tau_a],
        },
        schema={
            "ROCModel": pl.String,
            **{k: pl.Float64 for k in "Area StdErr LowerArea UpperArea SomersD Gamma TauA".split()},
        },
    )


@dataclass
class AssociationTable:
    """Percentages are in PERCENT units (85.92, not 0.859). An undefined statistic is None."""

    concordant_pct: float | None
    discordant_pct: float | None
    tied_pct: float | None
    pairs: int
    somers_d: float | None
    gamma: float | None
    tau_a: float | None
    c: float | None


def association_table(y: pl.Series, pd: pl.Series) -> AssociationTable:
    """ODS Association of the fitted model: pairs tied when in the same ROCEPS group (`_pairs`; X07 C).
    concordant_pct / discordant_pct / tied_pct are in percent units. A statistic with a 0
    denominator (single-class response, all pairs tied) is None; tau_a is 0 on a single-class response.
    RESOLVED (post-parity): degenerate inputs are outside the pipeline domain (R1: not all missing)."""
    q = _pairs(y, pd)
    n = q.n1 + q.n0
    p = q.n1 * q.n0
    cd = q.conc - q.disc

    def pct(a: int) -> float | None:
        return None if p == 0 else 100.0 * a / p

    return AssociationTable(
        pct(q.conc),
        pct(q.disc),
        pct(q.tied),
        p,
        _ratio(cd, p),
        _ratio(cd, q.conc + q.disc),
        _ratio(cd, n * (n - 1) / 2),
        _ratio(q.conc + 0.5 * q.tied, p),
    )


def _hl_groups(blocks: list[int], n: int, g: int) -> list[int]:
    m = math.floor(n / g + 0.5)
    groups: list[int] = []
    c = 0
    for nj in blocks:
        if c == 0 or (c < m and c + math.floor(0.5 * nj) <= m):
            c += nj
        else:
            groups.append(c)
            c = nj
    groups.append(c)
    if len(groups) > 1 and groups[-1] <= math.floor(0.05 * n):
        last = groups.pop()
        groups[-1] += last
    return groups


def hosmer_lemeshow(y: pl.Series, pd: pl.Series) -> tuple[pl.DataFrame, float | None, int, float | None]:
    """`lackfit`: SAS's HL partition (blocks of rows whose pd agree within 1e-6 of the block's
    smallest pd; documented group-size rule; last group merged when small) as the inventory row
    printed_hl_partition.csv decides. Returns (partition table, chi-square, DF, p-value).
    The table is numeric with exactly the columns Group, Total, EventsObserved, EventsExpected,
    NoneventsObserved, NoneventsExpected (Int64 counts, Float64 expected; the caller renders
    the expected columns with 2 decimals). The chi-square is None when a group's expected count is 0;
    the p-value is None when it is None or DF < 1 (fewer than 3 groups).
    A group's expected events are its size times its average probability, and SAS keeps that
    average within [1e-6, 0.999999]. Measured 2026-11-17 on the six SAS runs with a group average
    beyond 0.99999 or below 0.00001 (rawfit_floorA to floorD, sep_age_gt_55, sep_age_gt_62): five
    have a group outside the limits, print SAS's note and the chi-square with the group's average
    limited (floorB 0.3656; unlimited 0.3644); floorC's most extreme group is at 1 - 1.31e-6,
    inside, and it has no note and the unlimited value, although 62 of its observations are
    above 0.999999: limiting each observation gives 95.1048 against SAS's 95.1047 (and 67.7310
    against 67.7309 on floorA). The upper limit is bracketed by 1 - 1.31e-6 (kept) and
    1 - 9.31e-7 (limited); the lower one only by groups far below it (7e-27 and less), so 1e-6
    there is the note's figure. The expected counts printed with 2 decimals do not show it.
    With fewer than 3 groups SAS prints no partition and no test and creates neither table
    (4 runs with 2 groups, 38 with 3 to 10): the caller writes no file then.
    RESOLVED (post-parity): an empty input returns an empty table with missing statistics (DF 0)."""
    d = pl.DataFrame({"y": y.cast(pl.Float64), "p": pd.cast(pl.Float64)}).drop_nulls()
    if d.height == 0:
        cols0 = [
            "Group",
            "Total",
            "EventsObserved",
            "EventsExpected",
            "NoneventsObserved",
            "NoneventsExpected",
        ]
        types0 = [pl.Int64, pl.Int64, pl.Int64, pl.Float64, pl.Int64, pl.Float64]
        return pl.DataFrame(schema=dict(zip(cols0, types0, strict=True))), None, 0, None
    p0 = np.asarray(d.get_column("p").to_numpy(), dtype=np.float64)
    y0 = np.asarray(d.get_column("y").to_numpy(), dtype=np.float64)
    o = np.argsort(p0, kind="stable")
    p, yy = p0[o], y0[o]
    n = len(p)
    blocks: list[int] = []
    i = 0
    while i < n:
        j = int(p.searchsorted(float(p[i]) + 1e-6, side="right"))
        blocks.append(j - i)
        i = j
    starts = np.concatenate([[0], np.cumsum(blocks)[:-1]]).astype(np.int64)
    p = np.repeat(p[starts], blocks)  # every member takes its block's smallest pd
    sizes = _hl_groups(blocks, n, 10)
    rows: list[tuple[int, int, int, float, int, float]] = []
    start = 0
    chisq: float | None = 0.0
    for gi, size in enumerate(sizes, 1):
        o1 = int(yy[start : start + size].sum())
        # SAS limits the group's average probability to [1e-6, 0.999999] ("In calculating the Expected
        # values, predicted probabilities less than 1E-6 and greater than 0.999999 were changed to
        # 1E-6 and 0.999999 respectively"): the group's, not each observation's (docstring)
        e1 = size * min(max(float(p[start : start + size].sum()) / size, 1e-6), 0.999999)
        start += size
        o0, e0 = size - o1, size - e1
        chisq = (
            None if chisq is None or e1 <= 0 or e0 <= 0 else chisq + (o1 - e1) ** 2 / e1 + (o0 - e0) ** 2 / e0
        )
        rows.append((gi, size, o1, e1, o0, e0))
    dof = len(sizes) - 2
    pv = chi2_sf(chisq, dof) if chisq is not None and dof >= 1 else None
    cols = ["Group", "Total", "EventsObserved", "EventsExpected", "NoneventsObserved", "NoneventsExpected"]
    table = pl.DataFrame(
        {
            cols[0]: [r[0] for r in rows],
            cols[1]: [r[1] for r in rows],
            cols[2]: [r[2] for r in rows],
            cols[3]: [r[3] for r in rows],
            cols[4]: [r[4] for r in rows],
            cols[5]: [r[5] for r in rows],
        },
        schema={
            cols[0]: pl.Int64,
            cols[1]: pl.Int64,
            cols[2]: pl.Int64,
            cols[3]: pl.Float64,
            cols[4]: pl.Int64,
            cols[5]: pl.Float64,
        },
    )
    return table, chisq, dof, pv


def hosmer_lemeshow_is_printed(n_groups: int) -> bool:
    """Whether SAS prints the Hosmer-Lemeshow partition and test and creates their two tables: only
    with 3 groups or more. Measured on the SAS runs in hand with a variable in the final model: the
    4 whose partition has 2 groups have neither table (and nothing in the listing; the ODS OUTPUT
    statement warns that the tables were not created), the 38 with 3 to 10 groups have both."""
    return n_groups >= 3


def classification_table(
    y: FloatArray,
    x: FloatArray,
    fit: LogisticFit | FloatArray | None = None,
    *,
    pd: FloatArray | None = None,
) -> pl.DataFrame:
    """`ctable`: bias-adjusted (one-step leave-one-out) probabilities at levels 0.000, 0.020, ...,
    as the inventory row printed_classification.csv decides; 0/0 percentages missing. Called as
    `classification_table(y, x, fit)` or, per the inventory row, `classification_table(X, y, pd)`
    (a 2-D first argument means the inventory order; `pd=` may also be a keyword). w = pd(1-pd) and
    V = inverse(X' diag(w) X) are computed from pd (from `fit.beta` when only a fit is given).
    The grid runs from floor(min pstar/0.02)*0.02 to ceil(max pstar/0.02)*0.02 over the BIAS-ADJUSTED
    pstar (SAS-proven for the upper end by judge/runs/x_split_drift_m_metrics_threshold: 46 rows).
    Numeric frame with exactly the columns ProbLevel, CorrectEvents, CorrectNonevents, IncorrectEvents,
    IncorrectNonevents, Correct, Sensitivity, Specificity, FalsePositive, FalseNegative, PPV, NPV
    (counts Int64, percentages Float64, null for 0/0).
    RESOLVED (post-parity): every SAS run starts the grid at 0.000; the helper reproduces all 19 runs.
    Intercept-only fit (`x` has the one column): SAS's probability is the exact leave-one-out mean
    (events - y) / (n - 1), not the logit step, and it is compared, exactly (>=), with SAS's own level
    values, which are not k * 0.02: the first level is k * 0.02, the second the first + 0.02, and from
    the third on a level at an even position is the level two before + 0.04 and one at an odd
    position the level before + 0.02; the level printed 1.000 is 1 + 1e-12. So a probability equal to
    a printed level is counted at some levels (0.200, 0.400, 0.500 from 0.000) and not at others
    (0.300 from 0.200, 0.700 as a first level, never at 1.000). Experiment X16
    (`migration/legacy-to-port/experiments/x16_ctable_intercept_only`: 40 fits of 2 to 101 rows, SAS's
    cross-validated probabilities and its 357 levels bit for bit, every count) and the 17
    intercept-only runs of judge/runs (small-inputs.md (b)). A probability that equals a printed level
    starts or ends the grid at that level (tolerance 1e-9 on the range, the port's choice: SAS's is
    not known; it gives SAS's rows in all 57 fits).
    Fit with a variable: the levels are k * 0.02 rounded, compared with >=, except the level printed
    1.000, where SAS counts no observation as a predicted event although leave-one-out probabilities
    equal 1 in double precision: the two separated fits judge/runs/sep_age_gt_55 and sep_age_gt_62
    (27 and 25 defaulters at probability 1; SAS's last row `1.000,0,165,0,115,...`). So that level
    is 1 + 1e-12 here too (port/tests/test_classification_level_one.py). Not established: what SAS
    does with a probability equal to a LOWER printed level on a fit with a variable; the plain >= on
    the rounded level stays."""
    if y.ndim == 2:  # inventory order (X, y, pd)
        y, x = x, y
    if fit is not None and not isinstance(fit, LogisticFit):
        pd, fit = fit, None
    if pd is not None:
        p = np.asarray(pd, dtype=np.float64)
        eta = np.log(p) - np.log1p(-p)
    elif fit is not None:
        eta = x @ fit.beta
        p = _expit(eta)
    else:
        raise ValueError("classification_table needs pd or a fit")
    w = p * (1.0 - p)
    v = np.linalg.inv(x.T @ (x * w[:, None]))
    q = np.einsum("ij,jk,ik->i", x, v, x)
    h = w * q
    ps = _expit(eta - (y - p) * q / (1.0 - h))
    tol = 0.0
    if x.shape[1] == 1:  # intercept only: the exact leave-one-out mean
        ps = (float(y.sum()) - y) / (len(y) - 1.0)
        tol = 1e-9
    klo = math.floor(float(ps.min()) / 0.02 + tol)
    khi = math.ceil(float(ps.max()) / 0.02 - tol)
    grid = np.round(np.arange(klo, khi + 1) * 0.02, 3)
    cut = [float(z) for z in grid]  # the values the probabilities are compared with
    if x.shape[1] == 1:  # intercept only: SAS's own level values (X16)
        cut[0] = klo * 0.02
        for i in range(1, len(cut)):
            cut[i] = cut[i - 2] + 0.04 if i >= 2 and i % 2 == 0 else cut[i - 1] + 0.02
    if khi == 50:  # the level printed 1.000: no observation is counted there, on any fit
        cut[-1] = 1.0 + 1e-12
    n1 = int(y.sum())
    n0 = len(y) - n1

    def pct(a: int, b: int) -> float | None:
        return None if b == 0 else 100.0 * a / b

    rec: dict[str, list[float | int | None]] = {
        k: []
        for k in (
            "ProbLevel CorrectEvents CorrectNonevents IncorrectEvents IncorrectNonevents Correct "
            "Sensitivity Specificity FalsePositive FalseNegative PPV NPV"
        ).split()
    }
    for z, c in zip(grid, cut, strict=True):
        pe = ps >= c
        ce = int(np.count_nonzero(pe & (y == 1)))
        ie = int(np.count_nonzero(pe & (y == 0)))
        cn, inn = n0 - ie, n1 - ce
        vals: list[float | int | None] = [
            float(z),
            ce,
            cn,
            ie,
            inn,
            pct(ce + cn, n1 + n0),
            pct(ce, n1),
            pct(cn, n0),
            pct(ie, ce + ie),
            pct(inn, cn + inn),
            pct(ce, ce + ie),
            pct(cn, cn + inn),
        ]
        for k, v in zip(rec, vals, strict=True):
            rec[k].append(v)
    ints = {"CorrectEvents", "CorrectNonevents", "IncorrectEvents", "IncorrectNonevents"}
    return pl.DataFrame(
        {k: pl.Series(k, v, dtype=pl.Int64 if k in ints else pl.Float64) for k, v in rec.items()}
    )


# PORT STATUS: confidence=medium todos=0
