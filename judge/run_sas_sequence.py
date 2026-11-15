"""Run several submissions of the SAS scripts one after the other in ONE SAS session and ONE
output folder, and record what is in the output folder after each.

run_sas.py gives every run a fresh folder, so it cannot show what a stopped run leaves
behind after an earlier good run (requirement Q27). This driver can. The scripts are
submitted exactly as run_sas.py submits them (same path redirection and instrumentation).

Usage (from judge/):
    uv run python run_sas_sequence.py --run-id <id> --plan <plan.json>
plan.json: [{"label": "good", "data_dir": "scenarios/x", "scripts": "feature_engineering.sas,train.sas"}, ...]
Outputs: runs/<run-id>/<nn>_<label>/ (logs, listings, the CSVs then in the output folder) and
runs/<run-id>/sequence_meta.json (errors, new warnings and the folder listing after each step).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import saspy

from run_sas import ALLOWLIST, DATA_FILES, JUDGE, REPO, SCRIPTS, instrument, redirect_paths, warnings_in


# Observation only, submitted after a step's scripts: the files then in the session's WORK
# folder (tables and any other file) and the size of the test file as it lies on the server.
INSPECT = """data _null_;
    length fref $8 name $256 size $32;
    fref = ' ';
    rc = filename(fref, "%sysfunc(pathname(work))");
    did = dopen(fref);
    do i = 1 to dnum(did);
        name = dread(did, i);
        put 'INSPECT work ' name;
    end;
    rc = dclose(did);
    rc = filename(fref, "@DATA@/cs-test.csv");
    fid = fopen(fref, 'i', 1, 'b');
    size = finfo(fid, 'File Size (bytes)');
    put 'INSPECT size ' size;
    rc = fclose(fid);
    rc = filename(fref);
run;
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--plan", type=Path, required=True)
    ap.add_argument("--profile", default="oda_eu")
    ap.add_argument("--no-download", action="store_true", help="record the listing only")
    ap.add_argument("--inspect", action="store_true",
                    help="after each step, record the files in the WORK folder and the size of the uploaded cs-test.csv")
    args = ap.parse_args()

    plan = json.loads(args.plan.read_text())
    local_dir = JUDGE / "runs" / args.run_id
    if local_dir.exists():
        ap.error(f"{local_dir} exists; run-ids are never reused")
    local_dir.mkdir(parents=True)
    sources = {name: (REPO / name).read_text() for name in SCRIPTS}
    known = set(ALLOWLIST.read_text().splitlines()) if ALLOWLIST.exists() else set()

    sas = saspy.SASsession(cfgname=args.profile, results="TEXT")
    meta: dict = {"run_id": args.run_id, "sas_version": sas.sasver, "steps": []}
    try:
        log = sas.submit("%put JUDGEHOME=%sysget(HOME);")["LOG"]
        home = next(ln.split("=", 1)[1].strip() for ln in log.splitlines() if ln.startswith("JUDGEHOME="))
        run_root = f"{home}/sasmig/runs/{args.run_id}-{time.strftime('%Y%m%dT%H%M%S')}"
        data_dir, out_dir, gdir = f"{run_root}/data", f"{run_root}/output", f"{run_root}/graphs"
        sas.submit(f"""options dlcreatedir;
            libname _mk "{home}/sasmig"; libname _mk "{home}/sasmig/runs"; libname _mk "{run_root}";
            libname _mk "{data_dir}"; libname _mk "{out_dir}"; libname _mk "{gdir}"; libname _mk clear;""")
        sas.submit(f'ods listing gpath="{gdir}";')
        meta["remote_run_root"] = run_root

        for i, step in enumerate(plan, 1):
            label = f"{i:02d}_{step['label']}"
            step_dir = local_dir / label
            step_dir.mkdir()
            src_dir = Path(step["data_dir"])
            for f in DATA_FILES:
                res = sas.upload(str(src_dir / f), f"{data_dir}/{f}", overwrite=True)
                if not res.get("Success"):
                    raise RuntimeError(f"upload failed for {src_dir / f}: {res}")
            scripts = [s for s in SCRIPTS if s in step["scripts"].split(",")]
            rec: dict = {"label": label, "data_dir": str(src_dir), "scripts": scripts,
                         "errors": {}, "new_warnings": {}}
            for name in scripts:
                res = sas.submit(instrument(name, redirect_paths(sources[name], data_dir, out_dir)))
                (step_dir / f"{name}.log").write_text(res["LOG"])
                (step_dir / f"{name}.lst").write_text(res["LST"])
                rec["errors"][name] = [ln for ln in res["LOG"].splitlines() if ln.startswith("ERROR")]
                rec["new_warnings"][name] = sorted({x for x in warnings_in(res["LOG"]) if x not in known})
            if args.inspect:
                res = sas.submit(INSPECT.replace("@DATA@", data_dir))
                (step_dir / "inspect.log").write_text(res["LOG"])
                found = [ln[8:].strip() for ln in res["LOG"].splitlines() if ln.startswith("INSPECT ")]
                rec["work_folder"] = sorted(x[5:] for x in found if x.startswith("work "))
                rec["cs_test_bytes"] = next((x[5:] for x in found if x.startswith("size ")), None)
            files = sorted(f for f in sas.dirlist(out_dir) if f.endswith(".csv"))
            rec["output_folder"] = {}
            for f in files:
                info = sas.file_info(f"{out_dir}/{f}", quiet=True) or {}
                rec["output_folder"][f] = {"modified": info.get("Last Modified"), "bytes": info.get("File Size (bytes)")}
                if not args.no_download:
                    sas.download(str(step_dir / f), f"{out_dir}/{f}")
            meta["steps"].append(rec)
            n_err = sum(len(v) for v in rec["errors"].values())
            print(f"{label}: {n_err} ERROR, {len(files)} csv in output folder", flush=True)
    finally:
        (local_dir / "sequence_meta.json").write_text(json.dumps(meta, indent=2))
        sas.endsas()
    return 0


if __name__ == "__main__":
    sys.exit(main())
