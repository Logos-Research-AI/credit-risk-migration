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
