"""X17: what PROC LOGISTIC does when a Fisher scoring step lowers the log likelihood (its ridge).

PROC LOGISTIC as legacy/train.sas calls it (same MODEL statement and options), plus ITPRINT, on
  real          judge/reference/model_features_train.csv (105,000 rows)
  subN_S        N of its rows, drawn with random.Random(1000 * S + N), written as the same text lines
  sNN           the feature file of a generated seed's SAS run (judge/runs/gen_sNN, git-ignored)
Each SAS log (tagged lines IH| iteration history, CS| convergence status, 32-character numbers) is
written to out/ridge/sas/R_<case>.log (git-ignored: it names the SAS account's folder), and the
histories of all logs found there are collected into x17_sas_iteration_histories.json:
  {case: [{step, variables, ridge (per iteration), neg2loglike (iteration 0 on), estimates (last)}]}

usage, from judge/ (SAS OnDemand profile oda_eu):
  uv run python ../migration/legacy-to-port/experiments/x17_ridging_run.py real s02 s06 s08 s26 s27 \\
      sub3000_1 sub3000_2 sub6000_1 sub6000_2 sub12000_1 sub12000_2 sub25000_1 sub25000_2 \\
      sub50000_1 sub50000_2 sub80000_1 sub80000_2
  uv run python ../migration/legacy-to-port/experiments/x17_ridging_run.py        (collect only)
"""

from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "out" / "ridge"
TAGS = ("IH|", "CS|")
train = (ROOT / "legacy" / "train.sas").read_text()
MODEL = re.sub(
    r"/\*.*?\*/",
    "",
    re.search(r"model default_flag =(.*?)/ selection=stepwise", train, re.S).group(1),
    flags=re.S,
)
OPTS = "selection=stepwise slentry=0.05 slstay=0.05 itprint"
DUMP = """
%macro dump(tag, ds); %if %sysfunc(exist(work.&ds)) %then %do;
data _null_; set work.&ds; format _numeric_ best32.; put "&tag|" (_all_)(=); run;
proc datasets lib=work nolist; delete &ds; quit; %end; %mend;
"""
ODS = "ods output IterHistory=work.ih ConvergenceStatus=work.cs;"


def source(case: str) -> Path:
    if case == "real":
        return ROOT / "judge/reference/model_features_train.csv"
    if case.startswith("sub"):
        n, seed = (int(v) for v in case[3:].split("_"))
        lines = (ROOT / "judge/reference/model_features_train.csv").read_text().splitlines()
        rows = sorted(random.Random(1000 * seed + n).sample(range(len(lines) - 1), n))
        path = OUT / "data" / f"{case}.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join([lines[0], *[lines[i + 1] for i in rows]]) + "\n")
        return path
    return ROOT / "judge/runs" / f"gen_{case}" / "model_features_train.csv"


def run(cases: list[str]) -> None:
    import saspy

    (OUT / "sas").mkdir(parents=True, exist_ok=True)
    sas = saspy.SASsession(cfgname="oda_eu", results="TEXT")
    try:
        log = sas.submit("%put JH=%sysget(HOME);")["LOG"]
        home = next(line.split("=", 1)[1].strip() for line in log.splitlines() if line.startswith("JH="))
        sas.submit("options linesize=max nonotes;" + DUMP)
        sas.submit(
            f'options dlcreatedir; libname _mk "{home}/sasmig"; libname _mk "{home}/sasmig/x17"; libname _mk clear;'
        )
        for case in cases:
            remote = f"{home}/sasmig/x17/R_{case}.csv"
            assert sas.upload(str(source(case)), remote, overwrite=True).get("Success")
            res = sas.submit(
                f'proc import datafile="{remote}" out=work.f dbms=csv replace; getnames=yes; guessingrows=max; run;\n'
                f'title "R_{case}"; proc logistic data=work.f descending; model default_flag = {MODEL} / {OPTS}; {ODS} run;\n'
                "%dump(IH, ih) %dump(CS, cs)"
            )
            (OUT / "sas" / f"R_{case}.log").write_text(res["LOG"])
            print(
                case,
                sum(line.startswith("IH|") for line in res["LOG"].splitlines()),
                "iteration lines",
                flush=True,
            )
    finally:
        sas.endsas()


def records(path: Path) -> dict[str, list[dict[str, str]]]:
    """The tagged lines of a log; a line the log wrapped (256 characters) is joined to its start."""
    recs: dict[str, list[list[str]]] = {t[:2]: [] for t in TAGS}
    cur: list[str] | None = None
    for line in path.read_text().splitlines():
        if line[:3] in TAGS:
            cur = [line[3:]]
            recs[line[:2]].append(cur)
        elif cur is not None and re.match(r"^\w+=", line):
            cur[0] += " " + line
        else:
            cur = None
    return {t: [dict(re.findall(r"(\w+)=(.*?)(?= \w+=|$)", r[0])) for r in v] for t, v in recs.items()}


def collect() -> None:
    out: dict[str, list[dict[str, object]]] = {}
    for path in sorted((OUT / "sas").glob("R_*.log")):
        recs = records(path)
        status = {int(d["Step"]): d["Reason"] for d in recs["CS"]}
        steps: list[dict[str, object]] = []
        for st in sorted({int(d["Step"]) for d in recs["IH"]}):
            rows = [d for d in recs["IH"] if int(d["Step"]) == st]
            skip = ("Step", "Iteration", "Ridge", "Neg2LogLike")
            names = [k for k in rows[0] if k not in skip and rows[0][k] != "."]
            if len(names) < 2:
                continue  # step 0: the intercept alone
            assert "GCONV" in status[st], (path.name, st, status[st])  # every step of these runs converged
            steps.append(
                {
                    "step": st,
                    "variables": names[1:],
                    "ridge": [float(d["Ridge"]) for d in rows[1:]],
                    "neg2loglike": [float(d["Neg2LogLike"]) for d in rows],
                    "estimates": [float(rows[-1][k]) for k in names],
                }
            )
        out[path.stem[2:]] = steps
    (Path(__file__).parent / "x17_sas_iteration_histories.json").write_text(json.dumps(out, indent=0))
    ridged = sum(sum(r > 0 for r in s["ridge"]) for v in out.values() for s in v)  # type: ignore[union-attr]
    print(f"{len(out)} runs, {sum(len(v) for v in out.values())} steps, {ridged} ridged iterations")


if __name__ == "__main__":
    if sys.argv[1:]:
        run(sys.argv[1:])
    collect()
