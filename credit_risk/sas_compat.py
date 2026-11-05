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
from decimal import ROUND_HALF_UP, Context, Decimal
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
    """SAS `x <= c`. No inventory site (A31): unverified."""
    return _named(x, ~lt(_e(c), x))


def gt(x: ExprOrNum, c: ExprOrNum) -> pl.Expr:
    """SAS `x > c` (missing > anything is false). Non-null pl.Boolean."""
    return _named(x, lt(_e(c), x))


def ge(x: ExprOrNum, c: ExprOrNum) -> pl.Expr:
    """SAS `x >= c`. Site: predict.sas grade chain and pred_logistic = flag(ge(pd, 0.5))."""
    return _named(x, ~lt(x, c))


def eq(x: ExprOrNum, c: ExprOrNum) -> pl.Expr:
    """SAS `x = c` (`. = .` is true). No inventory site (A31): unverified."""
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


_TWO52 = 2.0**52
_ROUND_FUZZ = 1e-12


def sas_round(x: ExprOrNum) -> pl.Expr:
    """SAS round(x) to an integer: half away from zero, with SAS's fuzz: |frac - 0.5| <= 1e-12 *
    max(1, |x|) counts as half (experiment X05: 1e-14 below .5 rounds up, 1e-10 below does not);
    |x| >= 2^52 is returned unchanged. Missing stays missing. Float64 result, no -0.0."""
    xf = _e(x).cast(pl.Float64)
    a = xf.abs()
    fl = a.floor()
    up = (a - fl) >= (0.5 - pl.max_horizontal(pl.lit(1.0), a) * _ROUND_FUZZ)
    r = xf.sign() * (fl + up.cast(pl.Float64))
    return _named(x, pl.when(a >= _TWO52).then(xf).otherwise(r) + 0.0)


def sas_round_scalar(x: float) -> float:
    """Scalar form of sas_round (same rule)."""
    if not math.isfinite(x) or abs(x) >= _TWO52:
        return x
    a = abs(x)
    fl = math.floor(a)
    up = (a - fl) >= 0.5 - _ROUND_FUZZ * max(1.0, a)
    return math.copysign(float(fl + (1 if up else 0)), x) + 0.0


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
    """SAS input(s, best32.): numeric text -> Float64; anything else ('NA', '') -> missing. An
    already-numeric column is an identity cast to Float64 (S2). Overflow ('1E400') and inf -> missing.
    RESOLVED (post-parity): X06 confirms the 32-column cut (37 digits read as 32); leading blanks ignored."""
    t = s.cast(pl.String).str.slice(0, 32).str.strip_chars()
    v = t.cast(pl.Float64, strict=False)
    return _named(s, pl.when(t.str.contains(_NUM_RE) & v.is_finite()).then(v))


def merge_one_to_one(*frames: pl.DataFrame) -> pl.DataFrame:
    """SAS one-to-one MERGE (no BY; A6, experiment X01a). Rows = the longest frame; shorter frames
    are padded with nulls at the end. Columns are in frame order (first appearance). A later frame's
    column with the same name OVERWRITES the earlier one, including with null on its padded rows
    (the shorter input's values are missing there)."""
    if not frames:
        return pl.DataFrame()
    n = max(f.height for f in frames)
    cols: dict[str, pl.Series] = {}
    for f in frames:
        for s in f.iter_columns():
            pad = n - s.len()
            cols[s.name] = s if pad == 0 else pl.concat([s, pl.Series(s.name, [None] * pad, dtype=s.dtype)])
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
    form fills the width ('123E-7' at w=6, '-12E-6', '123E9'), trailing zeros stripped ('1E-5', '15E-6')."""
    d15 = _sig15(x)
    neg = 1 if x < 0 else 0
    adj = d15.adjusted()
    if w - len(f"E{adj}") - neg - 2 >= 2:
        return _enotation(x, w)
    nd = max(w - neg - len(f"E{adj}"), 1)
    m = int(d15.scaleb(-(adj - nd + 1)).quantize(Decimal(1), rounding=ROUND_HALF_UP, context=_CTX))
    e = adj - nd + 1
    if m >= 10**nd:
        m //= 10
        e += 1
    while m % 10 == 0:
        m //= 10
        e += 1
    return ("-" if neg else "") + str(m) + f"E{e}"


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


def sas_best(x: float | None, w: int) -> str:
    """BESTw. text. Plain notation rounded half up from the value's 15-significant-digit form
    (A18); at w = 12 E-notation for 0 < |x| < 1e-5 with the mantissa rounded to fill w characters and
    trailing zeros stripped (A15). Integers print without a decimal point. None -> '' (export).
    BEST8. is what `select ... into` stores (A9). A value whose integer part does not fit in w
    characters also prints in E-notation (experiment X03: 123456789 -> '1.2346E8' at BEST8.).
    At other widths a value below 1 prints in E-notation when plain notation cannot show it within w
    (experiment X05: 0.000015 -> BEST6 '15E-6', BEST8 and BEST12 '0.000015').
    TODO(port): the 1e-5 threshold is verified at w = 12 only (A15); BEST8. below 1e-4 beyond the
    X05 cell, and a w too small to show any digit (e.g. -100 at w=3), are unverified.
    Non-finite -> ''."""
    if x is None or not math.isfinite(x):
        return ""
    if x == 0:
        return "0"
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
    return _enotation(x, w)


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
    TODO(port): a value that does not fit w at 0 decimals (> 999% at percent8.2) falls back to BEST
    (unverified), and a negative value that rounds to zero prints unsigned and unparenthesised
    (unverified)."""
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
    TODO(port): D8. fitted on 38 cells first; E threshold bracketed (2.90e-5 fixed, 6.42e-6 E);
    0 unverified."""
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

    dec = decimals(x)
    s = _fixed(x, dec)
    dec2 = decimals(float(s))
    if dec2 != dec:
        s = _fixed(x, dec2)
    return s if len(s) <= 8 else sas_best(x, 8)


def sas_d12_3(x: float | None) -> str:
    """D12.3 as exported (inventory: printed_association.csv, printed_rsquare.csv,
    printed_fit_statistics.csv InterceptOnly): |x| >= 1e4 -> 0 decimals; 1e-4 <= |x| < 100 ->
    6 decimals; 1e-5 <= |x| < 1e-4 -> 9 decimals; last digit half up (A18). The branch is chosen
    from the value rounded at the branch's decimals (9999.9999996 -> '10000'); a text wider than 12
    falls back to BEST12.
    TODO(port): 100 <= |x| < 1e4 (6 decimals assumed) and |x| < 1e-5 (BEST12 E-notation assumed)
    were never observed in SAS output; |x| < 1e-5 is reachable (Percent Tied is below 1e-5 when
    there are 68 or fewer tied pairs of 686,727,936); 0 prints '0'."""
    if x is None or not math.isfinite(x):
        return ""
    if x == 0:
        return "0"

    def decimals(v: float) -> int | None:
        av = abs(v)
        if av >= 1e4:
            return 0
        if av >= 1e-4:
            return 6
        return 9 if av >= 1e-5 else None

    dec = decimals(x)
    for _ in range(3):
        if dec is None:
            return sas_best(x, 12)
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
    longest of those values, LATER VALUES TRUNCATED to that width (BUG(port): guessingrows=20 sizes
    MonthlyIncome $5., so 159791 -> 15979, 77 rows); an all-empty
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
    system, complete or quasi-complete separation, an exhausted line search or the iteration cap."""

    names: list[str]
    beta: FloatArray
    cov: FloatArray  # inverse information matrix (NaN when it cannot be computed)
    loglik: float
    n_iter: int
    converged: bool


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
    TODO(port): non-convergence / separation behaviour is unspecified by A17 (SAS: MAXITER=25, prints
    separation warnings and continues); 100 iterations, 40 halvings and the 1e-12 relative roundoff
    slack of the halving test are port choices (queue a rulebook amendment)."""
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
    stop when nothing enters or the best entry was just removed. Reference implementation:
    migration/experiments/x02_stepwise_reference.py. Rows with a missing response or candidate are
    dropped. The model columns of each fit are in ENTRY order (names[0] = "Intercept").
    Raises RuntimeError when a fit does not converge or the 500-step cap is hit.
    TODO(port): SAS would print a warning (separation / non-convergence) and continue with the
    unconverged fit; the port stops with an error instead."""
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
        f = fit_logistic(x, y, ["Intercept", *cols])
        if not f.converged:
            raise RuntimeError(f"stepwise_logistic: the fit at step {step} ({cols}) did not converge")
        return f

    model: list[str] = []
    cur = fit(model)
    res = StepwiseResult(intercept_only=cur, final=cur)
    last_removed: str | None = None
    while step < 500:
        if model:  # removal first: smallest Wald chi-square, ties to the first in MODEL order
            best_w: tuple[float, str] | None = None
            for c in sorted(model, key=mkey):
                i = cur.names.index(c)
                wv = float(cur.beta[i] ** 2 / cur.cov[i, i])
                if best_w is None or wv < best_w[0]:
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
                last_removed = best_w[1]
                continue
        x = np.column_stack([ones, *[z_all[c] for c in model]])
        p = _expit(x @ cur.beta)
        w = p * (1.0 - p)
        info = x.T @ (x * w[:, None])
        best: tuple[float, str] | None = None
        for c in candidates:
            if c in model:
                continue
            z = z_all[c]
            zwz = float(z @ (z * w))
            v = x.T @ (z * w)
            resid = zwz - float(v @ np.linalg.solve(info, v))
            # TODO(port): an effect whose alias is outside the model, if removed, could alternate with
            # that alias (inventory stepwise row); the alias test below does not model it.
            if zwz <= 0.0 or resid / zwz < 1e-8:
                continue  # aliased with the current model
            u = float(z @ (y - p))
            sc = u * u / resid
            if best is None or sc > best[0]:
                best = (sc, c)
        if best is None or chi2_sf(best[0], 1) >= slentry or best[1] == last_removed:
            break
        step += 1
        model.append(best[1])
        cur = fit(model)
        res.steps.append(
            StepwiseStep(step, best[1], None, 1, len(model), best[0], None, chi2_sf(best[0], 1), cur)
        )
        last_removed = None
    else:
        raise RuntimeError("stepwise_logistic: 500 steps reached without stopping")
    res.final = cur
    return res


@dataclass
class RocAssociation:
    area: float | None
    std_err: float | None
    lower: float | None
    upper: float | None
    somers_d: float | None
    gamma: float | None
    tau_a: float | None


_TIE_EPS = 1e-8  # A8: SAS tie fuzz


@dataclass
class _Pairs:
    conc: int
    disc: int
    tied: int
    n1: int
    n0: int
    v10: FloatArray
    v01: FloatArray


def _pairs(y: pl.Series, score: pl.Series) -> _Pairs:
    d = pl.DataFrame({"y": y.cast(pl.Float64), "s": score.cast(pl.Float64)}).drop_nulls()
    yy = np.asarray(d.get_column("y").to_numpy(), dtype=np.float64)
    ss = np.asarray(d.get_column("s").to_numpy(), dtype=np.float64)
    ev = np.sort(ss[yy == 1])
    ne = np.sort(ss[yy == 0])
    n1, n0 = len(ev), len(ne)
    lo_ne = np.searchsorted(ne, ev - _TIE_EPS, side="left")
    le_ne = np.searchsorted(ne, ev + _TIE_EPS, side="right")
    lo_ev = np.searchsorted(ev, ne - _TIE_EPS, side="left")
    le_ev = np.searchsorted(ev, ne + _TIE_EPS, side="right")
    conc = int(lo_ne.sum())
    tied = int((le_ne - lo_ne).sum())
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
    Tied = |difference| <= 1e-8. Without `label`: a RocAssociation of numbers (the caller adds the
    ROCModel label and renders every value with sas_d8). With `label`: the ONE-row frame the inventory
    rows specify (ROCModel, Area, StdErr, LowerArea, UpperArea, SomersD, Gamma, TauA; full-precision
    Float64). An undefined statistic (empty class, all pairs tied, one observation in a class for the
    standard error) is None.
    TODO(port): SAS's output for these degenerate inputs is unverified."""
    q = _pairs(y, score)
    n = q.n1 + q.n0
    p = q.n1 * q.n0
    area = _ratio(q.conc + 0.5 * q.tied, p)
    se: float | None = None
    if q.n1 >= 2 and q.n0 >= 2:
        se = math.sqrt(float(np.var(q.v10, ddof=1)) / q.n1 + float(np.var(q.v01, ddof=1)) / q.n0)
    cd = q.conc - q.disc
    r = RocAssociation(
        area,
        se,
        None if area is None or se is None else area - Z975 * se,
        None if area is None or se is None else area + Z975 * se,
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
    """ODS Association of the fitted model: pairs tied when |dpd| <= 1e-8 (A8).
    concordant_pct / discordant_pct / tied_pct are in percent units. A statistic with a 0
    denominator (single-class response, all pairs tied) is None.
    TODO(port): SAS's output for these degenerate inputs is unverified."""
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
    TODO(port): SAS output for LACKFIT with fewer than 3 groups or an empty expected count is unverified."""
    d = pl.DataFrame({"y": y.cast(pl.Float64), "p": pd.cast(pl.Float64)}).drop_nulls()
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
        e1 = float(p[start : start + size].sum())
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
    TODO(port): the lower grid end is unproven (pd and pstar both give 0.000 on every SAS run)."""
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
    klo = math.floor(float(ps.min()) / 0.02)
    khi = math.ceil(float(ps.max()) / 0.02)
    grid = np.round(np.arange(klo, khi + 1) * 0.02, 3)
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
    for z in grid:
        pe = ps >= z
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


# PORT STATUS: confidence=medium todos=11
