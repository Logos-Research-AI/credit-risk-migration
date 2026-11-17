"""X20: which slope SAS leaves out of the global Wald test (global-wald-rule.md).

Seed 6, step 7 (judge/runs/gen_s06): SAS prints Wald 406.4827 with DF 7, the port 407.3550. 406.4827 is
the Wald over the 6 other slopes at the same fit: SAS leaves utilization_debt_interaction out (variance
6.3e-25). Here the step-7 model is fitted alone (PROC LOGISTIC, no selection, MODEL order of train.sas,
COVB), on the step's feature file with columns scaled. A scaled column scales its estimate and its
covariance, the fit is otherwise the same, so each run prints one of two numbers: 406.4827 (left out)
or 407.3550 (kept).
  A<k>  utilization_debt_interaction times 10**-k: its absolute and its relative pivot both grow by 10**2k
  B<m>  the six other slopes times 10**m: the interaction's absolute pivot is unchanged, its pivot
        relative to the largest element of the slopes' covariance grows by 10**2m
An absolute tolerance flips A and never B; a tolerance relative to the largest element flips both at
the same step. `predict` prints the two pivots of each case from the port's fit and what the bracket
of the runs in hand (out/rv/wald_scan2.txt) says, before SAS is run.

usage, from judge/ (SAS OnDemand profile oda_eu):
  uv run python ../migration/legacy-to-port/experiments/x20_global_wald.py predict   (needs the port: --project ../port)
  uv run python ../migration/legacy-to-port/experiments/x20_global_wald.py run [cases]
  uv run python ../migration/legacy-to-port/experiments/x20_global_wald.py collect
SAS logs go to out/x20/sas (git-ignored: they name the SAS account's folder); results to x20_sas_results.json.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "out" / "x20"
SRC = ROOT / "judge" / "runs" / "gen_s06" / "model_features_train.csv"
STEP7 = {"financial_health", "flag_high_debt_ratio", "flag_multiple_delinquencies", "flag_high_utilization",
         "age_category", "log_num_credit_lines", "utilization_debt_interaction"}
INTER = "utilization_debt_interaction"
train = (ROOT / "legacy" / "train.sas").read_text()
MODEL_ALL = re.sub(r"/\*.*?\*/", "", re.search(r"model default_flag =(.*?)/ selection=stepwise", train, re.S).group(1), flags=re.S).split()
VARS = [v for v in MODEL_ALL if v in STEP7]
CASES = {"A0": (0, 0), **{f"A{k}": (k, 0) for k in range(1, 6)}, **{f"B{m}": (0, m) for m in range(1, 6)}}
# second round, after A and B: the interaction's pivot set to a target between A4 and A5 (T), and A5 with
# log_num_credit_lines shifted by 1000 (S1), which leaves the slopes' covariance as it is and multiplies the
# intercept's variance by about 2.5e4: a tolerance relative to the intercept's variance flips it, an absolute one not
PIVOT_A0 = 6.2920e-25
TARGETS = {"T1": 1e-16, "T2": 2e-16, "T3": 5e-16, "T4": 1e-15, "T5": 2e-15}
CASES.update({t: (0.5 * __import__("math").log10(v / PIVOT_A0), 0) for t, v in TARGETS.items()})
CASES["S1"] = (5, 0)
SHIFT = {"S1": ("log_num_credit_lines", 1000.0)}
DUMP = """
%macro dump(tag, ds); %if %sysfunc(exist(work.&ds)) %then %do;
data _null_; set work.&ds; format _numeric_ best32.; put "&tag|" (_all_)(=); run;
proc datasets lib=work nolist; delete &ds; quit; %end; %mend;
"""


def data(case: str) -> Path:
    k, m = CASES[case]
    rows = list(csv.DictReader(SRC.open()))
    path = OUT / "data" / f"{case}.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write(",".join(["default_flag", *VARS]) + "\n")
        for r in rows:
            vals = []
            for v in VARS:
                x = float(r[v])
                x = x * 10.0**-k if v == INTER else x * 10.0**m
                if case in SHIFT and SHIFT[case][0] == v:
                    x += SHIFT[case][1]
                vals.append(repr(x))
            f.write(",".join([r["default_flag"], *vals]) + "\n")
    return path


def predict() -> None:
    import numpy as np

    sys.path.insert(0, str(ROOT / "port"))
    from credit_risk import sas_compat as S

    for case in CASES:
        rows = list(csv.reader(data(case).open()))[1:]
        a = np.array(rows, dtype=float)
        y, x = a[:, 0], np.column_stack([np.ones(len(a)), a[:, 1:]])
        f = S._fit_as_sas(x, y, ["Intercept", *VARS])
        c = f.cov[1:, 1:]
        b = f.beta[1:]
        j = VARS.index(INTER)
        o = [i for i in range(len(VARS)) if i != j]
        piv = c[j, j] - c[j, o] @ np.linalg.solve(c[np.ix_(o, o)], c[o, j])
        rel = piv / np.abs(np.diag(c)).max()
        rel0 = piv / f.cov[0, 0]
        full = b @ np.linalg.solve(c, b)
        wo = b[o] @ np.linalg.solve(c[np.ix_(o, o)], b[o])
        say = lambda lo, hi, v: "left out" if v <= lo else "kept" if v >= hi else "open"
        print(f"{case}: pivot {piv:.3e} (absolute: {say(6.3e-25, 2.6e-15, piv)}), relative {rel:.3e} "
              f"(relative: {say(5.3e-23, 1.9e-15, rel)}), to the intercept's variance {rel0:.3e}; Wald kept {full:.4f}, left out {wo:.4f}")


def run(cases: list[str]) -> None:
    import saspy

    (OUT / "sas").mkdir(parents=True, exist_ok=True)
    sas = saspy.SASsession(cfgname="oda_eu", results="TEXT")
    try:
        log = sas.submit("%put JH=%sysget(HOME);")["LOG"]
        home = next(line.split("=", 1)[1].strip() for line in log.splitlines() if line.startswith("JH="))
        sas.submit("options linesize=max nonotes;" + DUMP)
        sas.submit(f'options dlcreatedir; libname _mk "{home}/sasmig"; libname _mk "{home}/sasmig/x20"; libname _mk clear;')
        for case in cases:
            remote = f"{home}/sasmig/x20/{case}.csv"
            assert sas.upload(str(data(case)), remote, overwrite=True).get("Success")
            res = sas.submit(
                f'proc import datafile="{remote}" out=work.f dbms=csv replace; getnames=yes; guessingrows=max; run;\n'
                f'title "X20 {case}"; proc logistic data=work.f descending; model default_flag = {" ".join(VARS)} / covb;\n'
                "ods output GlobalTests=work.gt ParameterEstimates=work.pe CovB=work.cb ConvergenceStatus=work.cs; run;\n"
                "%dump(GT, gt) %dump(PE, pe) %dump(CB, cb) %dump(CS, cs)"
            )
            (OUT / "sas" / f"{case}.log").write_text(res["LOG"])
            gt = [ln for ln in res["LOG"].splitlines() if ln.startswith("GT|") and "Wald" in ln]
            print(case, gt[0] if gt else "no global Wald line", flush=True)
    finally:
        sas.endsas()


def collect() -> None:
    out: dict[str, dict[str, list[str]]] = {}
    for path in sorted((OUT / "sas").glob("*.log")):
        recs: dict[str, list[str]] = {}
        cur: list[str] | None = None
        for line in path.read_text().splitlines():
            if line[:3] in ("GT|", "PE|", "CB|", "CS|"):
                cur = recs.setdefault(line[:2], [])
                cur.append(line[3:])
            elif cur is not None and re.match(r"^\w+=", line):
                cur[-1] += " " + line
            else:
                cur = None
        out[path.stem] = recs
    (Path(__file__).parent / "x20_sas_results.json").write_text(json.dumps(out, indent=0))
    for case, recs in out.items():
        print(case, [r for r in recs.get("GT", []) if "Wald" in r])


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "predict":
        predict()
    elif cmd == "run":
        run(sys.argv[2:] or list(CASES))
        collect()
    else:
        collect()
