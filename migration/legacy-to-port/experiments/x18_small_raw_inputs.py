"""X18: small raw inputs, valid by section 3 of the requirements, through the whole pipeline: the sweep.

Every input is a list of rows of legacy/data/cs-training.csv (by their id, in file order), each with the
outcome it carries in this input (x18_small_raw_inputs.json: {name: {how, sas_run, rows: [[id, outcome]]}});
every other field is the row's own. The test file is the first 40 rows of legacy/data/cs-test.csv.
Two facts make the inputs designable (measured, small-inputs.md and recycling-rule.md):
  - SAS's split and its feature files do not depend on the outcome column, so an input with a new outcome
    column on rows already run has a known training part and known features;
  - the split leaves out fixed positions of work.credit_features, whose order is not the file's.

usage, from the repository root:
  python3 migration/legacy-to-port/experiments/x18_small_raw_inputs.py list
  python3 migration/legacy-to-port/experiments/x18_small_raw_inputs.py make <dir> [names]     writes <dir>/<name>/cs-*.csv
  python3 migration/legacy-to-port/experiments/x18_small_raw_inputs.py sas <dir> [names]      the SAS program on each (judge/run_sas.py,
                                                                                    run-id = sas_run, a run-id is never reused)
  cd judge && uv run python ../migration/legacy-to-port/experiments/x18_small_raw_inputs.py judge <dir> [names] [--port <folder holding credit_risk>]
      the port on each input as the contract runs it (generated_inputs.judge: fe, train, metrics, predict, end to end,
      file by file where the SAS run logged errors), against judge/runs/<sas_run>; one line per input.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUTS = json.loads((HERE / "x18_small_raw_inputs.json").read_text())


def make(name: str, out: Path) -> Path:
    raw = (ROOT / "legacy/data/cs-training.csv").read_text().splitlines()
    by_id = {ln.split(",", 1)[0]: ln.split(",") for ln in raw[1:]}
    lines = [raw[0]]
    for rid, outcome in INPUTS[name]["rows"]:
        f = list(by_id[str(rid)])
        f[1] = str(outcome)
        lines.append(",".join(f))
    d = out / name
    d.mkdir(parents=True, exist_ok=True)
    (d / "cs-training.csv").write_text("\n".join(lines) + "\n")
    test = (ROOT / "legacy/data/cs-test.csv").read_text().splitlines()[:41]
    (d / "cs-test.csv").write_text("\n".join(test) + "\n")
    return d


def main() -> int:
    cmd, args = sys.argv[1], sys.argv[2:]
    port = None
    if "--port" in args:
        port = Path(args[args.index("--port") + 1]).resolve()
        args = args[: args.index("--port")] + args[args.index("--port") + 2 :]
    if cmd == "list":
        for name, spec in INPUTS.items():
            ev = sum(o == 1 for _, o in spec["rows"])
            print(f"{name:14s} {len(spec['rows']):5d} rows, {ev:4d} events, SAS run {spec['sas_run']}: {spec['how']}")
        return 0
    out = Path(args[0]).resolve()
    names = args[1:] or list(INPUTS)
    if cmd == "make":
        for name in names:
            print(make(name, out))
        return 0
    if cmd == "sas":
        for name in names:
            d = make(name, out)
            if (ROOT / "judge/runs" / INPUTS[name]["sas_run"]).exists():
                print(f"{name}: judge/runs/{INPUTS[name]['sas_run']} exists, not run again")
                continue
            res = subprocess.run(
                ["uv", "run", "--quiet", "python", "run_sas.py", "--run-id", INPUTS[name]["sas_run"], "--data-dir", str(d)],
                cwd=ROOT / "judge", capture_output=True, text=True,
            )
            print(f"{name}: " + "; ".join(ln for ln in res.stdout.splitlines() if ".sas:" in ln))
        return 0
    if cmd == "judge":
        sys.path.insert(0, str(ROOT / "judge"))
        import generated_inputs as gi

        if port is not None:
            os.environ["PYTHONPATH"] = str(port)  # the port's modules are taken from this folder
        same = 0
        for name in names:
            d = make(name, out)
            sas = ROOT / "judge/runs" / INPUTS[name]["sas_run"]
            meta = json.loads((sas / "run_meta.json").read_text())
            n_err = sum(len(v) for v in meta.get("errors", {}).values())
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = gi.judge(0, d, sas, out / name / "port", True, True)
            (out / name / "judge.txt").write_text(buf.getvalue())
            crash = [ln.strip() for ln in buf.getvalue().splitlines() if "CRASH" in ln]
            fails = [ln.split()[0] + ":" + ln.split()[1] for ln in buf.getvalue().splitlines() if ln.rstrip().endswith("FAIL")]
            same += rc == 0
            train_rows = len((sas / "model_features_train.csv").read_text().splitlines()) - 1
            print(
                f"{name:14s} {len(INPUTS[name]['rows']):5d} rows ({train_rows} training); SAS {n_err} ERROR lines; port "
                + ("EQUAL" if rc == 0 else "DIFFERENT " + " ".join(fails))
                + (" | " + crash[0][:150] if crash else ""),
                flush=True,
            )
        print(f"{same} of {len(names)} inputs: the port equals SAS on every file SAS wrote")
        return 0 if same == len(names) else 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
