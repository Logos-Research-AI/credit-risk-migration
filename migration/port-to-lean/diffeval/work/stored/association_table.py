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
