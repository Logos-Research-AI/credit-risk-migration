"""X22: train.sas on a final model with a parameter left out of a singular information matrix (variance
exactly 0), and what the port gives (task of 2026-11-18, second port fix; X21 S1 measured the fit alone).

The selection path of train.sas is not known to reach such a final model (a parameter left out at a step is
removed at the next one, singular-information.md), so the model is fixed: train.sas runs as it is except
that its MODEL statement names the design's variables, in train.sas's MODEL order, without
`selection=stepwise slentry=0.05 slstay=0.05` (the options `ctable lackfit rsquare`, the OUTPUT, STORE and
ODS OUTPUT statements and every later step unchanged), on staged feature files; metrics_calculation.sas and
predict.sas follow in the same session, as judge/run_sas.py runs them (same path redirection and the same
observation-only instrumentation, plus best32. dumps of the parameter estimates, odds ratios, the
convergence status and every pd_logistic).

Designs (rows of the reference feature files, the design's columns overwritten):
  A  X21 S1: 60 training rows, one event, flag_recent_late_payments 1 on it alone, age 0 to 6;
     MODEL age flag_recent_late_payments. The flag's row passes |eta| = 36.7 at iteration 1 and has weight 0:
     the flag is left out at the last iteration, which SAS stops at 8 (complete separation).
  B  120 rows, overlapping outcomes, num_late_90_plus = 2 * flag_recent_late_payments; MODEL num_late_90_plus
     age flag_recent_late_payments: the flag is collinear from the start, left out at every iteration;
     the fit converges.
  C  200 rows, three events, one of them flagged alone (flag 1 on that row only); MODEL age
     flag_recent_late_payments: the flag is left out at the last iteration (weight 0), the fit converges.
The validation file: 40 rows of the reference validation file, flag_recent_late_payments 1 on every 8th
(and num_late_90_plus = 2 * flag in B); predict.sas: the first 300 rows of legacy/data/cs-test.csv.

usage (SAS on ODA, from judge/):   uv run python ../migration/legacy-to-port/experiments/x22_left_out_final.py sas
       (the port, from port/):     uv run python ../migration/legacy-to-port/experiments/x22_left_out_final.py port
SAS's outputs land in judge/runs/x22_<design> (run_sas.py's layout, git-ignored); the facts are written to
x22_sas_results.json beside this file. `port` runs train.py, metrics_calculation.py and predict.py on the same
staged inputs, with the selection replaced by the design's fit (`_fit_as_sas` on the MODEL columns), and
compares every file SAS wrote with the judge's comparator (port mode), and which files exist.

Results (SAS runs judge/runs/x22_A, x22_B, x22_C of 2026-11-18, SAS 9.04.01M9; facts in x22_sas_results.json):
  - All three: the port's fit (`_fit_as_sas` on the MODEL columns) leaves the flag out with variance exactly 0,
    and SAS prints it with DF 0, Estimate 0 and missing standard error, Wald chi-square and p-value
    (model_coefficients.csv `flag_recent_late_pay,0,0,,,,MLE`), and gives it no row of the odds ratios.
  - OUTPUT PREDICTED= (risk_scores_train.csv) and PROC PLM (risk_scores_validation.csv, the 5 flagged validation
    rows; predict.sas, 41 flagged test rows of 300) predict with 0 for the flag, not the last iteration's
    value (A 61.0169, C 68.1384). The Hosmer-Lemeshow partition and test are of those probabilities
    (C: chi-square 222.9472; with the iteration's value it would be 2.5380).
  - The Association table is of the LAST ITERATION's estimates, the flag's value included (C: 90.2% concordant,
    c 0.904; with 0 for the flag 60.2% and 0.605; A: 100% concordant against 100% tied).
  - Classification table: none in A and C (the flag left out because its one row has weight 0 at the last
    iteration: "WARNING: The information matrix is singular"; X21 S1 likewise had H= and XP_ missing), one in
    B (the flag a linear combination of the other columns: "NOTE: The following parameters have been set to 0,
    since the variables are a linear combination of other variables"); B's table is the port's with the
    inverse taken over the kept parameters (`_inv_sas`). LackFit: A has one group (no table), B and C ten.
  - The port, with train.py following these rules, gives every file SAS wrote (train, metrics and predict
    stages, the four selection tables aside) in B and C, and in A all but one cell: the age estimate, which
    has no information in A (SAS 2.19E-15, the port's iteration -1.1E-15, rounding residues of 0).
  - Not measured: a final model with a weight-0 left-out parameter AND a linearly dependent one; a left-out
    intercept; any of this reached through train.sas's selection.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
JUDGE = ROOT / "judge"
RESULTS = HERE / "x22_sas_results.json"
STAGED = ROOT / "out" / "x22" / "staged"
PORT_OUT = ROOT / "out" / "x22" / "port"

MODEL_RE = re.compile(r"    model default_flag =.*?ctable lackfit rsquare;", re.S)
SCRIPTS = ["train.sas", "metrics_calculation.sas", "predict.sas"]


def _a(i: int) -> float:
    return round(((i * 7919) % 101 - 50) / 25.0, 2)


def designs() -> dict[str, tuple[list[str], list[dict[str, float]]]]:
    """name -> (MODEL variables in train.sas order, per training row the overwritten columns)"""
    d: dict[str, tuple[list[str], list[dict[str, float]]]] = {}
    rows = [{"default_flag": 1, "age": 0, "flag_recent_late_payments": 1}] + [
        {"default_flag": 0, "age": (i * 37 + 11) % 7, "flag_recent_late_payments": 0} for i in range(1, 60)
    ]
    d["A"] = (["age", "flag_recent_late_payments"], rows)
    rows = []
    for i in range(120):
        a = _a(i)
        f = int((i * 13) % 5 == 0)
        y = int(1.2 * a + ((i * 37) % 17 - 8) / 4.0 > 0)
        rows.append({"default_flag": y, "num_late_90_plus": 2 * f, "age": 40 + 10 * a, "flag_recent_late_payments": f})
    d["B"] = (["num_late_90_plus", "age", "flag_recent_late_payments"], rows)
    rows = []
    for i in range(200):
        y = 1 if i in (5, 77, 150) else 0
        rows.append({"default_flag": y, "age": 40 + 10 * _a(i), "flag_recent_late_payments": int(i == 150)})
    d["C"] = (["age", "flag_recent_late_payments"], rows)
    return d


def _fmt(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else repr(float(v))


def make() -> None:
    """The staged inputs of each design under out/x22/staged/<design>: the two feature files, income_medians.csv
    (the reference's) and data/cs-test.csv (its first 300 rows)."""
    ref = JUDGE / "reference"
    for name, (cols, rows) in designs().items():
        out = STAGED / name
        (out / "data").mkdir(parents=True, exist_ok=True)
        for part, n in (("train", len(rows)), ("validation", 40)):
            lines = (ref / f"model_features_{part}.csv").read_text().splitlines()
            head = lines[0].split(",")
            body = []
            for i, ln in enumerate(lines[1 : n + 1]):
                f = ln.split(",")
                over: dict[str, float]
                if part == "train":
                    over = rows[i]
                else:
                    flag = int(i % 8 == 0)
                    over = {"flag_recent_late_payments": flag}
                    if "num_late_90_plus" in cols:
                        over["num_late_90_plus"] = 2 * flag
                for k, v in over.items():
                    f[head.index(k)] = _fmt(v)
                body.append(",".join(f))
            (out / f"model_features_{part}.csv").write_text("\n".join([lines[0], *body]) + "\n")
        (out / "income_medians.csv").write_text((ref / "income_medians.csv").read_text())
        test = (ROOT / "legacy" / "data" / "cs-test.csv").read_text().splitlines()[:301]
        (out / "data" / "cs-test.csv").write_text("\n".join(test) + "\n")


DUMP = """%macro x22dump(tag, ds); %if %sysfunc(exist(&ds)) %then %do;
data _null_; set &ds; format _numeric_ best32.; put "&tag|" (_all_)(=); run; %end;
%else %put &tag|NOTCREATED; %mend;"""


def _parse(log: str, tags: tuple[str, ...]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for ln in log.splitlines():
        tag, _, rest = ln.partition("|")
        if tag not in tags:
            continue
        if rest.strip() == "NOTCREATED":
            out[tag] = None
            continue
        rec = {}
        for tok in re.findall(r"(\S+?)=(\S*)", rest):
            rec[tok[0]] = tok[1]
        out.setdefault(tag, []).append(rec)
    return out


def sas(names: list[str]) -> int:
    import saspy

    sys.path.insert(0, str(JUDGE))
    import run_sas as rs  # the judge's own redirection and instrumentation

    make()
    results: dict[str, Any] = json.loads(RESULTS.read_text()) if RESULTS.exists() else {}
    known = set(rs.ALLOWLIST.read_text().splitlines()) if rs.ALLOWLIST.exists() else set()
    for name, (cols, _rows) in designs().items():
        if names and name not in names:
            continue
        local = JUDGE / "runs" / f"x22_{name}"
        if local.exists():
            raise SystemExit(f"{local} exists; run-ids are never reused")
        local.mkdir(parents=True)
        staged = STAGED / name
        session = saspy.SASsession(cfgname="oda_eu", results="TEXT")
        meta: dict[str, Any] = {
            "run_id": local.name, "mutation": None, "scripts": SCRIPTS, "data_dir": str(staged / "data"),
            "stage_inputs": str(staged), "sas_version": session.sasver, "errors": {}, "new_warnings": {},
            "experiment": "x22_left_out_final.py", "model": cols, "selection": "none",
        }
        t0 = time.time()
        facts: dict[str, Any] = {"model": cols, "logs": {}}
        try:
            log = session.submit("%put JUDGEHOME=%sysget(HOME);")["LOG"]
            home = next(ln.split("=", 1)[1].strip() for ln in log.splitlines() if ln.startswith("JUDGEHOME="))
            run_root = f"{home}/sasmig/runs/{local.name}-{time.strftime('%Y%m%dT%H%M%S')}"
            data_dir, out_dir, gdir = f"{run_root}/data", f"{run_root}/output", f"{run_root}/graphs"
            session.submit(f"""options dlcreatedir;
                libname _mk "{home}/sasmig"; libname _mk "{home}/sasmig/runs"; libname _mk "{run_root}";
                libname _mk "{data_dir}"; libname _mk "{out_dir}"; libname _mk "{gdir}"; libname _mk clear;""")
            session.submit(f'ods listing gpath="{gdir}";' + DUMP)
            uploads = [(staged / "data" / "cs-test.csv", f"{data_dir}/cs-test.csv")]
            uploads += [(p, f"{out_dir}/{p.name}") for p in sorted(staged.glob("*.csv"))]
            for src, dst in uploads:
                res = session.upload(str(src), dst, overwrite=True)
                if not res.get("Success"):
                    raise RuntimeError(f"upload failed for {src}: {res}")
            for script in SCRIPTS:
                code = rs.redirect_paths((rs.REPO / script).read_text(), data_dir, out_dir)
                if script == "train.sas":
                    code, n = MODEL_RE.subn(
                        f"    model default_flag = {' '.join(cols)}\n    / ctable lackfit rsquare;", code
                    )
                    assert n == 1, n
                    code = rs.instrument(script, code).replace(
                        rs.capture_statement(),
                        rs.capture_statement().replace(";", " ConvergenceStatus=work._x22_cs;"),
                    )
                    code += (
                        "%x22dump(PE, work.model_coefficients) %x22dump(OR, work._j_oddsratios) "
                        "%x22dump(CS, work._x22_cs) %x22dump(CT, work._j_classification) "
                        "%x22dump(AS, work._j_association) %x22dump(HL, work._j_lackfitchisq) "
                        "data work._x22_pd; set work.risk_scores_train(keep=row_id pd_logistic); run; "
                        "%x22dump(PDT, work._x22_pd) "
                        "data work._x22_pv; set work.risk_scores_validation(keep=row_id pd_logistic); run; "
                        "%x22dump(PDV, work._x22_pv)"
                    )
                else:
                    code = rs.instrument(script, code)
                res = session.submit(code)
                (local / f"{script}.log").write_text(res["LOG"])
                (local / f"{script}.lst").write_text(res["LST"])
                meta["errors"][script] = [ln for ln in res["LOG"].splitlines() if ln.startswith("ERROR")]
                w = rs.warnings_in(res["LOG"])
                meta["new_warnings"][script] = sorted({x for x in w if x not in known})
                facts["logs"][script] = {"errors": meta["errors"][script], "warnings": sorted(set(w))}
                if script == "train.sas":
                    facts.update(_parse(res["LOG"], ("PE", "OR", "CS", "CT", "AS", "HL", "PDT", "PDV")))
                print(f"{name} {script}: {len(meta['errors'][script])} ERROR, {len(set(w))} WARNING", flush=True)
            staged_names = {p.name for p in staged.glob("*.csv")}
            files = sorted(f for f in session.dirlist(out_dir) if f.endswith(".csv"))
            for f in files:
                if f in staged_names:
                    continue
                res = session.download(str(local / f), f"{out_dir}/{f}")
                if not res.get("Success"):
                    raise RuntimeError(f"download failed for {f}: {res}")
            facts["files"] = [f for f in files if f not in staged_names]
            meta["remote_run_root"] = run_root
        finally:
            meta["wall_clock_s"] = round(time.time() - t0)
            (local / "run_meta.json").write_text(json.dumps(meta, indent=2))
            session.endsas()
        results[name] = facts
        RESULTS.write_text(json.dumps(results, indent=1) + "\n")
    return 0


def port(names: list[str]) -> int:
    import numpy as np

    sys.path.insert(0, str(JUDGE))
    import compare  # the judge's comparator

    from credit_risk import metrics_calculation, predict, sas_compat, train

    make()
    results = json.loads(RESULTS.read_text())
    bad = 0
    for name, (cols, _rows) in designs().items():
        if names and name not in names or name not in results:
            continue
        staged = STAGED / name
        out = PORT_OUT / name
        if out.exists():
            for p in out.iterdir():
                p.unlink()
        out.mkdir(parents=True, exist_ok=True)
        real = sas_compat.stepwise_logistic

        def fixed(df: Any, response: str, candidates: Any, *a: Any, _cols: list[str] = cols) -> Any:
            used = df.select([response, *candidates]).drop_nulls()
            y = used.get_column(response).to_numpy().astype(np.float64)
            x = np.column_stack([np.ones(len(y)), *[used.get_column(c).to_numpy().astype(np.float64) for c in _cols]])
            fit = sas_compat._fit_as_sas(x, y, ["Intercept", *_cols])
            io_fit = sas_compat.fit_logistic(x[:, :1], y, ["Intercept"])
            return sas_compat.StepwiseResult([], fit, io_fit)

        sas_compat.stepwise_logistic = fixed  # type: ignore[assignment]
        log = io.StringIO()
        try:
            with contextlib.redirect_stdout(log):
                train.run(staged, out)
                metrics_calculation.run(out, out)
                predict.run(out, out, data_dir=staged / "data", income_medians=staged / "income_medians.csv")
        except Exception as e:  # noqa: BLE001
            print(f"{name}: port stopped: {type(e).__name__}: {e}")
            bad += 1
            continue
        finally:
            sas_compat.stepwise_logistic = real  # type: ignore[assignment]
        sas_dir = JUDGE / "runs" / f"x22_{name}"
        judged = [f for f in compare.FILES if f not in ("stepwise_summary.csv", "printed_fit_statistics.csv",
                                                       "printed_global_tests.csv", "printed_rsquare.csv")
                  and f not in compare.STAGES["fe"]]
        exist_sas = {f for f in judged if (sas_dir / f).exists()}
        exist_port = {f for f in judged if (out / f).exists()}
        res = compare.compare_dir(sas_dir, out, sorted(exist_sas), "port")
        fails = [r for r in res if r.status != "PASS"]
        print(f"{name}: {len(res) - len(fails)}/{len(res)} files SAS wrote pass; files only SAS wrote "
              f"{sorted(exist_sas - exist_port)}, only the port {sorted(exist_port - exist_sas)}")
        for r in fails:
            print(f"   {r.status} {r.file}: {r.problems[:4]}")
        bad += len(fails) + len(exist_sas ^ exist_port)
    return 1 if bad else 0


if __name__ == "__main__":
    cmd, rest = sys.argv[1], sys.argv[2:]
    if cmd == "make":
        make()
        sys.exit(0)
    sys.exit(sas(rest) if cmd == "sas" else port(rest))
