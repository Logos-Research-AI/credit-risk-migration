"""Fuzz of def:classification_table (2026-11-17): which printed levels k * 0.02 can a probability
of a fit with a variable equal exactly? Searches, for each level L, a float eta near logit(L) with
sas_compat._expit(eta) == L bit for bit (numpy). Used by diffeval/units/fz_ctable_gen.py for its
pool of linear predictors.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python experiments/fz_ctable_pool.py
"""
import math

import numpy as np

from credit_risk import sas_compat as sc

inf = float("inf")


def hits() -> dict[int, float | None]:
    out: dict[int, float | None] = {}
    for k in range(51):
        lv = float(np.round(k * 0.02, 3))
        if k == 0:
            out[k] = -800.0  # exp(800) = inf, 1 / (1 + inf) = 0.0
            continue
        if k == 50:
            out[k] = 40.0  # 1 / (1 + exp(-40)) = 1.0 in double precision
            continue
        e = math.log(lv) - math.log1p(-lv)
        lo = hi = e
        found = None
        for d in range(4000):
            for cand in ((lo,) if d == 0 else (lo, hi)):
                if float(sc._expit(np.array([cand]))[0]) == lv:
                    found = cand
                    break
            if found is not None:
                break
            lo, hi = math.nextafter(lo, -inf), math.nextafter(hi, inf)
        out[k] = found
    return out


if __name__ == "__main__":
    h = hits()
    for k, v in h.items():
        assert v is None or float(sc._expit(np.array([v]))[0]) == float(np.round(k * 0.02, 3))
    print("levels with no eta found:", [k for k, v in h.items() if v is None])
    print("levels reached:", sum(v is not None for v in h.values()), "of 51")
    miss = []
    for k in range(1, 50):
        lv = float(np.round(k * 0.02, 3))
        p = np.array([lv])
        if float(sc._expit(np.log(p) - np.log1p(-p))[0]) != lv:
            miss.append(k)
    print("pd path: levels L where _expit(log(L) - log1p(-L)) != L:", miss)
