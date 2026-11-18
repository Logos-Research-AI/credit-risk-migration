"""X23: what SAS's "no one-step adjustment" rule for an observation of leverage near 1 is a test ON (review of
R3, commit 88df42d). X21 bracketed it at 1 - h in (8.56e-9, 1.489e-8], but all 13 T fits put the observation
at the same probability (p = 0.999998, weight w = 1.9e-6) and the same column scale, so a rule on
(1 - h) / w, on q = h / w or on an unscaled quantity agrees with the port's `1 - h <= 1e-8` there.

Here the estimates are FIXED (INEST= with MAXITER=0: SAS scores, and builds H=, PREDPROBS=(CROSSVALIDATE) and
CTABLE, at the given parameters), so the observation's probability and its leverage are set independently:
rows (y, a, c), a and y as X21's `logistic_rows(60, 1.5, -1, 0)`, c = s on row 7, s * eps on row 9 and 0
elsewhere; row 7 has leverage about 1 - eps^2 w9 / w7. Each case fixes the probability of row 7 (through the
estimate of c), the scale s of c, the outcome of row 7, and eps so that the port's 1 - h of row 7 is a target.

usage (SAS on ODA, from judge/), E = ../migration/legacy-to-port/experiments:
    uv run python $E/x23_leverage_tolerance.py sas
(the port, from port/):
    uv run python $E/x23_leverage_tolerance.py port
SAS's facts are written to x23_sas_results.json beside this file (logs in out/x23/sas_logs, git-ignored).

Results (17 runs of 2026-11-18 on ODA, SAS 9.04.01M9, one session; port at a9b1f41):
  - SAS keeps the probability of row 7 (XP_1 = P_) at 1 - h = 5e-9 and 9.496e-9 and adjusts it (XP_1 0 or 1)
    at 1.2e-8, 1.4e-8 and 2e-8, at every probability of row 7 (0.5, 1e-9, 0.999, so a weight from 1e-9 to
    0.25), every scale of c (1e-3, 1, 1e3) and both outcomes. The rule is a test on 1 - h alone, and the
    bracket narrows to (9.496e-9, 1.2e-8]: the port's 1e-8 is inside it.
  - SAS's printed H agrees with the port's h to the digits printed on all 17; the port's classification
    table (`sas_compat.classification_table`, pd from the fixed estimates) is SAS's on all 17
    (port/tests/test_leverage_one.py, test_rule_is_on_one_minus_h).
  - MAXITER=0 only adds SAS's "Convergence was not attained in 0 iterations" warnings; the estimates are
    INEST='s.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RESULTS = HERE / "x23_sas_results.json"
LOGS = ROOT / "out" / "x23" / "sas_logs"
B0, BA = 0.05, 1.5  # the fixed intercept and slope of a


def _a(i: int) -> float:
    return round(((i * 7919) % 101 - 50) / 25.0, 2)


def _rows(eps: float, s: float, y7: int) -> list[tuple[float, float, float]]:
    rows = []
    for i in range(60):
        a = _a(i)
        y = int(1.5 * a + ((i * 37) % 17 - 8) / 4.0 > 0)
        c = 0.0
        if i == 7:
            y, c = y7, s
        elif i == 9:
            y, c = 0, s * eps
        rows.append((float(y), a, c))
    return rows


def _beta_c(p7: float, s: float) -> float:
    return (math.log(p7) - math.log1p(-p7) - B0 - BA * _a(7)) / s


def _one_minus_h(rows: list[tuple[float, float, float]], beta: np.ndarray) -> np.ndarray:
    arr = np.array(rows)
    x = np.column_stack([np.ones(len(arr)), arr[:, 1], arr[:, 2]])
    p = 1.0 / (1.0 + np.exp(-(x @ beta)))
    w = p * (1.0 - p)
    v = np.linalg.inv(x.T @ (x * w[:, None]))
    return 1.0 - w * np.einsum("ij,jk,ik->i", x, v, x)


def cases() -> dict[str, dict[str, Any]]:
    """name -> {p7, s, y7, target, eps (4 significant digits), bc (8), rows}"""
    out: dict[str, dict[str, Any]] = {}
    grid = [
        # (p7, s, y7, targets of 1 - h)
        (0.5, 1.0, 1, (5e-9, 9.5e-9, 1.2e-8, 1.4e-8, 2e-8)),
        (1e-9, 1.0, 1, (5e-9, 1.2e-8, 2e-8)),
        (0.999, 1.0, 0, (5e-9, 1.2e-8, 2e-8)),
        (0.5, 1000.0, 1, (5e-9, 1.2e-8, 2e-8)),
        (0.5, 1e-3, 0, (5e-9, 1.2e-8, 2e-8)),
    ]
    for p7, s, y7, targets in grid:
        bc = float(f"{_beta_c(p7, s):.8g}")
        for t in targets:
            lo, hi = 1e-12, 1.0
            for _ in range(200):  # 1 - h grows with eps
                mid = math.sqrt(lo * hi)
                beta = np.array([B0, BA, bc])
                if _one_minus_h(_rows(mid, s, y7), beta)[7] < t:
                    lo = mid
                else:
                    hi = mid
            eps = float(f"{math.sqrt(lo * hi):.4g}")
            rows = _rows(eps, s, y7)
            name = f"p{p7:g}_s{s:g}_y{y7}_t{t:g}"
            out[name] = {"p7": p7, "s": s, "y7": y7, "target": t, "eps": eps, "bc": bc, "rows": rows}
    return out


def _fmt(v: float) -> str:
    return repr(float(v)) if not float(v).is_integer() else str(int(v))


DUMP = """%macro dump(tag, ds); %if %sysfunc(exist(&ds)) %then %do;
data _null_; set &ds; format _numeric_ best32.; put "&tag|" (_all_)(=); run;
proc datasets lib=work nolist; delete %scan(&ds,2,.); quit; %end; %else %put &tag|NOTCREATED; %mend;"""


def sas(names: list[str]) -> int:
    import saspy

    out: dict[str, Any] = json.loads(RESULTS.read_text()) if RESULTS.exists() else {}
    session = saspy.SASsession(cfgname="oda_eu", results="TEXT")
    try:
        session.submit("options linesize=max nonotes;" + DUMP)
        for name, c in cases().items():
            if names and name not in names:
                continue
            lines = "\n".join(" ".join(_fmt(v) for v in r) for r in c["rows"])
            res = session.submit(
                f"""options notes; data work.d; input y a c; datalines;\n{lines}\n;\nrun;
data work.est; input Intercept a c; datalines;\n{B0!r} {BA!r} {c["bc"]!r}\n;\nrun;
title "{name}"; proc logistic data=work.d descending inest=work.est;
model y = a c / ctable maxiter=0;
output out=work._OUT predicted=p h=lev xbeta=xb predprobs=(crossvalidate);
ods output Classification=work._CT ParameterEstimates=work._PE; run; options nonotes;
data work._OUT; set work._OUT; n = _n_; if n in (7 8 10); run;
%dump(PE, work._PE) %dump(CT, work._CT) %dump(OUT, work._OUT)"""
            )
            parsed: dict[str, list[dict[str, str]]] = {}
            for ln in res["LOG"].splitlines():
                tag, _, rest = ln.partition("|")
                if tag in ("PE", "CT", "OUT") and "=" in rest:
                    parsed.setdefault(tag, []).append(dict(t.partition("=")[::2] for t in rest.split()))
            warn = [ln.strip() for ln in res["LOG"].splitlines() if ln.startswith(("WARNING", "ERROR"))]
            out[name] = {
                "case": {k: v for k, v in c.items() if k != "rows"},
                "tables": parsed,
                "warnings": warn,
            }
            LOGS.mkdir(parents=True, exist_ok=True)
            (LOGS / f"{name}.log").write_text(res["LOG"])
            row = next((r for r in parsed.get("OUT", []) if r.get("n") == "8"), {})  # _n_ 8: row 7
            print(
                name,
                f"eps={c['eps']}",
                "lev",
                row.get("lev"),
                "p",
                row.get("p"),
                "XP_1",
                row.get("XP_1"),
                "CT",
                len(parsed.get("CT", [])),
                warn[:2],
                flush=True,
            )
    finally:
        session.endsas()
    RESULTS.write_text(json.dumps(out, separators=(",", ":")) + "\n")
    return 0


def port(names: list[str]) -> int:
    import warnings

    from credit_risk import sas_compat as sc

    sasr = json.loads(RESULTS.read_text())
    bad = 0
    for name, c in cases().items():
        if names and name not in names or name not in sasr:
            continue
        s = sasr[name]["tables"]
        arr = np.array(c["rows"])
        y = arr[:, 0]
        x = np.column_stack([np.ones(len(arr)), arr[:, 1], arr[:, 2]])
        p = 1.0 / (1.0 + np.exp(-(x @ np.array([B0, BA, c["bc"]]))))
        om = _one_minus_h(c["rows"], np.array([B0, BA, c["bc"]]))[7]
        row = next(r for r in s.get("OUT", []) if r.get("n") == "8")  # data step _n_ is 1-based: row 7
        sas_kept = float(row["XP_1"]) == float(row["p"])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            t = sc.classification_table(y, x, pd=p)
        got = [
            (round(float(r[0]), 3), *(int(v) for v in r[1:]))
            for r in t.select(
                "ProbLevel", "CorrectEvents", "CorrectNonevents", "IncorrectEvents", "IncorrectNonevents"
            ).iter_rows()
        ]
        want = [
            (
                round(float(r["ProbLevel"]), 3),
                *(
                    int(float(r[k]))
                    for k in ("CorrectEvents", "CorrectNonevents", "IncorrectEvents", "IncorrectNonevents")
                ),
            )
            for r in s.get("CT", [])
        ]
        ok = got == want
        bad += not ok
        print(
            f"{name}: port 1-h {om:.4g} SAS 1-h {1 - float(row['lev']):.4g} w7 {p[7] * (1 - p[7]):.3g}; "
            f"SAS {'keeps' if sas_kept else 'adjusts'} (p {row['p']} XP_1 {row['XP_1']}); port rule "
            f"{'keeps' if om <= 1e-8 else 'adjusts'}; "
            f"table {'= SAS' if ok else 'DIFFERS'} ({len(got)}/{len(want)})"
        )
    return 1 if bad else 0


if __name__ == "__main__":
    cmd, rest = sys.argv[1], sys.argv[2:]
    sys.exit(sas(rest) if cmd == "sas" else port(rest))
