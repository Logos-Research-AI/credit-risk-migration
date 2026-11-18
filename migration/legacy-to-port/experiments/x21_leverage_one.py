"""X21: the classification table (CTABLE) on a fit with an observation of leverage 1, and the fit with a
parameter left out at its last iteration (task R3/R4 of 2026-11-18, facts about the real fit).

An observation has leverage h = 1 when a direction of the parameters moves its linear predictor alone,
for instance a flag that is 1 on that one observation. Each case is fitted WITHOUT selection, so the flag
stays in the model whatever its Wald test (train.sas's stepwise selection would remove it; see the report):
PROC LOGISTIC descending, `model y = <vars> / ctable itprint`, OUTPUT with PREDICTED=, H= (leverage),
XBETA= and PREDPROBS=(CROSSVALIDATE) (SAS's one-step leave-one-out probability, the one CTABLE counts).

usage (SAS on ODA, from judge/):   uv run python ../migration/legacy-to-port/experiments/x21_leverage_one.py sas
       (the port, from port/):     uv run python ../migration/legacy-to-port/experiments/x21_leverage_one.py port
       (the raw input of R3):      python3 migration/legacy-to-port/experiments/x21_leverage_one.py make <dir>
SAS's results are written to x21_sas_results.json beside this file (the OUTPUT data set only for the rows
of leverage above 0.5 or missing; full logs in out/x21/sas_logs, git-ignored); `port` compares the port.

Results (runs of 2026-11-18, port at 70c4d9c):
  - SAS makes no one-step adjustment for an observation whose leverage is within about 1e-8 of 1: its
    cross-validated probability (XP_1) is its predicted probability. Adjusted at 1 - h = 1.489e-8 and above,
    kept at 8.56e-9 and below (T cases); kept at h printed 1 (L cases). With that rule (1 - h <= 1e-8: no
    adjustment) the port's classification table equals SAS's on all 18 fits that have one.
  - The port divides by 1 - h as it comes: at h = 1.0 exactly it gets an infinite step and a probability
    of 0 or 1, the opposite of the observed response; when 1 - h is a rounding residue (1e-14) the sign of
    that residue decides. Its classification table differs from SAS's on 10 of the 18 fits (L1 to L5, T 1E-7,
    1E-8, 3E-7, 2E-7, 1.5E-7) and equals it on the 8 where SAS adjusts.
  - S1 (a parameter left out at the last iteration): SAS prints that parameter with DF 0, Estimate 0 and
    no standard error, predicts with 0 for it (the port's fit keeps the iteration's 61.017), and makes no
    Classification table; H= and XP_ are missing on every row.
  - R3 on a valid raw input through the whole program (`make`, SAS run judge/runs/x21_r3_s03): the
    generated input of seed 3 with four training defaulters (row ids 63, 144, 216, 271) and no other on the
    training part; final model utilization_debt_interaction, age, flag_recent_late_payments (quasi-complete
    separation at step 3). Row id 276 (utilization_debt_interaction 8.2e8, no default, p = 0.0060) has
    leverage 1 within 1e-13. The port equals SAS on every file only because its 1 - h came out -3.2e-14:
    with the same probabilities summed in another order (5.9e-15 apart) 1 - h is +5.4e-15 and 49 of the
    51 rows of printed_classification.csv differ from SAS.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RESULTS = HERE / "x21_sas_results.json"
LOGS = ROOT / "out" / "x21" / "sas_logs"
# R3's raw input: judge/generated_inputs.py make --seed 3 (out/generated/s03), with these outcomes on the
# training part SAS's split gives that file (judge/runs/gen_s03; the split does not depend on the outcome)
R3_BASE = ROOT / "out" / "generated" / "s03"
R3_TRAINING_DEFAULTERS = ["63", "144", "216", "271"]


def make(out: Path) -> Path:
    """The raw files of R3: every training row (ids of judge/runs/gen_s03) a non-default except the four."""
    train_ids = {
        str(int(float(ln.split(",")[0])))
        for ln in (ROOT / "judge/runs/gen_s03/model_features_train.csv").read_text().splitlines()[1:]
    }
    lines = (R3_BASE / "cs-training.csv").read_text().splitlines()
    rows = [lines[0]]
    for ln in lines[1:]:
        f = ln.split(",")
        if f[0] in train_ids:
            f[1] = "1" if f[0] in R3_TRAINING_DEFAULTERS else "0"
        rows.append(",".join(f))
    out.mkdir(parents=True, exist_ok=True)
    (out / "cs-training.csv").write_text("\n".join(rows) + "\n")
    (out / "cs-test.csv").write_text((R3_BASE / "cs-test.csv").read_text())
    return out


def _a(i: int) -> float:
    """a deterministic, roughly normal predictor value"""
    return round(((i * 7919) % 101 - 50) / 25.0, 2)


def cases() -> dict[str, tuple[list[str], list[tuple[float, ...]], str]]:
    """name -> (variables, rows (y, x...), MODEL variables)"""
    c: dict[str, tuple[list[str], list[tuple[float, ...]], str]] = {}

    def logistic_rows(n: int, slope: float, flag_row: int, flag_y: int) -> list[tuple[float, ...]]:
        rows = []
        for i in range(n):
            a = _a(i)
            # y from a fixed threshold on slope * a plus a deterministic jitter, so both outcomes overlap
            y = int(slope * a + ((i * 37) % 17 - 8) / 4.0 > 0)
            f = 0
            if i == flag_row:
                y, f = flag_y, 1
            rows.append((y, a, f))
        return rows

    c["L1_n60_flag_on_a_nonevent"] = (["a", "f"], logistic_rows(60, 1.5, 7, 0), "a f")
    c["L2_n60_flag_on_an_event"] = (["a", "f"], logistic_rows(60, 1.5, 7, 1), "a f")
    c["L3_n200_flag_on_an_event"] = (["a", "f"], logistic_rows(200, 1.0, 11, 1), "a f")
    c["L4_n120_flag_on_a_nonevent"] = (["a", "f"], logistic_rows(120, 2.0, 3, 0), "a f")
    # L5: the flag order reversed in the MODEL statement (the table should not depend on it)
    c["L5_n60_flag_first"] = (["a", "f"], logistic_rows(60, 1.5, 7, 1), "f a")
    # T: leverage near 1 but not 1 and no separation: c is 1 on an event, eps on a non-event, 0 elsewhere;
    # the event's leverage is about 1 - eps^2 w2 / w1, so the tolerance SAS applies (if any) can be bracketed
    for eps in ("1E-2", "1E-3", "1E-4", "1E-5", "1E-6", "1E-7", "1E-8", "7E-7", "5E-7", "4E-7", "3E-7", "2E-7", "1.5E-7"):
        rows = []
        for i, (y, a, _f) in enumerate(logistic_rows(60, 1.5, -1, 0)):
            cval = "1" if i == 7 else eps if i == 9 else "0"
            yy = 1 if i == 7 else 0 if i == 9 else y
            rows.append((yy, a, cval))  # type: ignore[arg-type]
        c[f"T_eps_{eps}"] = (["a", "c"], rows, "a c")
    # S1: one event in 60, flagged (singular-information.md G2 without selection): the flag is left out at the
    # last iteration, its row has weight 0
    c["S1_n60_one_event_flagged"] = (
        ["x1", "z"],
        [(1, 1, 0)] + [(0, 0, (i * 37 + 11) % 7) for i in range(1, 60)],
        "x1 z",
    )
    return c


TABLES = {"CT": "Classification", "PE": "ParameterEstimates", "CS": "ConvergenceStatus", "IH": "IterHistory"}
DUMP = """%macro dump(tag, ds); %if %sysfunc(exist(&ds)) %then %do;
data _null_; set &ds; format _numeric_ best32.; put "&tag|" (_all_)(=); run; proc datasets lib=work nolist; delete %scan(&ds,2,.); quit; %end; %mend;"""


def sas(names: list[str]) -> int:
    import saspy

    out: dict[str, dict] = json.loads(RESULTS.read_text()) if RESULTS.exists() else {}
    session = saspy.SASsession(cfgname="oda_eu", results="TEXT")
    try:
        session.submit("options linesize=max nonotes;" + DUMP)
        for name, (xs, rows, model) in cases().items():
            if names and name not in names:
                continue
            lines = "\n".join(" ".join(str(v) for v in r) for r in rows)
            ods = "ods output " + " ".join(f"{t}=work._{k}" for k, t in TABLES.items()) + ";"
            res = session.submit(
                f"""options notes; data work.d; input y {' '.join(xs)}; datalines;\n{lines}\n;\nrun;
title "{name}"; proc logistic data=work.d descending; model y = {model} / ctable itprint;
output out=work._OUT predicted=p h=lev xbeta=xb predprobs=(crossvalidate); {ods} run; options nonotes;
"""
                + " ".join(f"%dump({k}, work._{k})" for k in [*TABLES, "OUT"])
            )
            parsed: dict[str, list[dict[str, str]]] = {}
            for ln in res["LOG"].splitlines():
                tag, _, rest = ln.partition("|")
                if tag in (*TABLES, "OUT") and "=" in rest:
                    rec = {}
                    for tok in rest.split():
                        k, _, v = tok.partition("=")
                        rec[k] = v
                    parsed.setdefault(tag, []).append(rec)
            warn = [ln.strip() for ln in res["LOG"].splitlines() if ln.startswith(("WARNING", "ERROR"))]
            out[name] = {"tables": parsed, "warnings": warn}
            parsed["OUT"] = [r for r in parsed.get("OUT", []) if r.get("lev") in (".", "") or float(r["lev"]) > 0.5]
            LOGS.mkdir(parents=True, exist_ok=True)
            (LOGS / f"{name}.log").write_text(res["LOG"])
            (LOGS / f"{name}.lst").write_text(res["LST"])
            print(name, {k: len(v) for k, v in parsed.items()}, warn, flush=True)
    finally:
        session.endsas()
    RESULTS.write_text(json.dumps(out, separators=(",", ":")) + "\n")
    return 0


def port(names: list[str]) -> int:
    import contextlib
    import io
    import warnings

    import numpy as np

    from credit_risk import sas_compat as sc

    sasr = json.loads(RESULTS.read_text())
    for name, (xs, rows, model) in cases().items():
        if names and name not in names or name not in sasr:
            continue
        cols = model.split()
        arr = np.array(rows, dtype=float)
        y = arr[:, 0]
        x = np.column_stack([np.ones(len(rows)), *[arr[:, 1 + xs.index(c)] for c in cols]])
        s = sasr[name]["tables"]
        pe = {r["Variable"]: (float(r["Estimate"]), r.get("StdErr", "")) for r in s.get("PE", [])}
        print(f"== {name}: SAS {sasr[name]['warnings'][:2]}")
        print("   SAS estimates", {k: v for k, v in pe.items()})
        with contextlib.redirect_stdout(io.StringIO()):
            fit = sc._fit_as_sas(x, y, ["Intercept", *cols])
        if fit is not None:
            print("   port estimates", dict(zip(fit.names, fit.beta.tolist(), strict=True)), "var", np.diag(fit.cov).tolist())
        # SAS's leave-one-out probability and leverage on its rows of leverage above 0.5 (matched to the data
        # by their values), against the port's helper's
        sas_out = s.get("OUT", [])
        if not sas_out:
            continue
        beta = np.array([pe["Intercept"][0], *[pe[c][0] for c in cols]])
        eta = x @ beta
        p = 1.0 / (1.0 + np.exp(-eta))  # train.py's pd_logistic from the estimates
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            w = p * (1.0 - p)
            try:
                v = np.linalg.inv(x.T @ (x * w[:, None]))
                q = np.einsum("ij,jk,ik->i", x, v, x)
                h = w * q
                e2 = np.log(p) - np.log1p(-p)
                ps = sc._expit(e2 - (y - p) * q / (1.0 - h))
            except np.linalg.LinAlgError as e:
                h = ps = np.full(len(y), math.nan)
                print("   port: LinAlgError", e)
        for r in sas_out:
            key = (float(r["y"]), *[float(r[c]) for c in cols])
            match = [i for i in range(len(y)) if (y[i], *x[i, 1:]) == key]
            if len(match) != 1 or r["lev"] in (".", ""):
                continue
            i = match[0]
            print(
                f"   row {i}: y={y[i]:.0f} SAS p={r['p']} h={r['lev']} XP_1={r['XP_1']} | "
                f"port h={h[i]!r} 1-h={1 - h[i]!r} pstar={ps[i]!r}"
            )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    t = sc.classification_table(y, x, pd=p)
            except Exception as e:  # noqa: BLE001
                print("   port classification_table:", type(e).__name__, e)
                continue
        sas_ct = [
            (round(float(r["ProbLevel"]), 3), int(float(r["CorrectEvents"])), int(float(r["CorrectNonevents"])))
            for r in s.get("CT", [])
        ]
        port_ct = [
            (round(float(a), 3), int(b), int(cc))
            for a, b, cc in zip(
                t.get_column("ProbLevel").to_list(),
                t.get_column("CorrectEvents").to_list(),
                t.get_column("CorrectNonevents").to_list(),
                strict=True,
            )
        ]
        diff = [(a, b) for a, b in zip(sas_ct, port_ct, strict=False) if a != b]
        if len(sas_ct) != len(port_ct):
            diff.append(("rows", len(sas_ct), len(port_ct)))
        print(f"   CTABLE rows SAS {len(sas_ct)} port {len(port_ct)}; differing rows: {diff[:6]}")
        print(f"   SAS first/last {sas_ct[:1]} {sas_ct[-1:]}; port first/last {port_ct[:1]} {port_ct[-1:]}")
    return 0


if __name__ == "__main__":
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "make":
        print(make(Path(rest[0]).resolve()))
        sys.exit(0)
    sys.exit(sas(rest) if cmd == "sas" else port(rest))
