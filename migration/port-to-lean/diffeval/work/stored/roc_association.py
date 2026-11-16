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
