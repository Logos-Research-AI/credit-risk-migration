"""Run the ORIGINAL SAS pipeline on SAS OnDemand (via saspy) and download its outputs.

The .sas scripts are submitted unmodified except for:
  * the two path macros (%let data_path / %let output_path), redirected to a fresh
    per-run folder in the ODA home directory;
  * observation-only instrumentation: train.sas's own `ods output` statement inside
    PROC LOGISTIC is widened to also capture printed tables (stepwise path, fit
    statistics, Hosmer-Lemeshow, ...), and work datasets the scripts already build
    (ROC tables, confusion matrices, cumulative lift, PSI table) are exported after
    each script. The Python port must emit the same files (judge/README.md);
  * environment setup: a writable ODS graphics path (see below);
  * optional mutations (mutations.py) used to prove the judge catches breakage.

All selected scripts run in ONE SAS session, in README order, because predict.sas
restores work.logit_model created by train.sas.

Usage (from judge/):
    uv run python run_sas.py --run-id baseline --write-warning-allowlist
    uv run python run_sas.py --run-id m_x --mutation <name>
    uv run python run_sas.py --run-id edge_predict --data-dir scenarios/edge_predict
    uv run python run_sas.py --run-id edge_metrics_a --scripts metrics_calculation.sas \
        --stage-inputs scenarios/edge_metrics_a
Outputs land in judge/runs/<run-id>/ (CSV outputs + per-script LOG/LST + run_meta.json).
A run-id is never reused: stale outputs must not be judged as fresh.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import saspy

from mutations import MUTATIONS, apply_mutation

JUDGE = Path(__file__).resolve().parent
REPO = JUDGE.parent
SCRIPTS = ["feature_engineering.sas", "train.sas", "metrics_calculation.sas", "predict.sas"]
DATA_FILES = ["cs-training.csv", "cs-test.csv"]
ORIGINAL_HOME = "/home/u64352077"
ALLOWLIST = JUDGE / "known_warnings.txt"

# Observation-only: widen train.sas's own ODS OUTPUT statement inside PROC LOGISTIC.
CAPTURE_ANCHOR = "    ods output ParameterEstimates=work.model_coefficients;"
CAPTURE_TABLES = {  # ODS table name -> exported file
    "ModelBuildingSummary": "stepwise_summary.csv",
    "FitStatistics": "printed_fit_statistics.csv",
    "GlobalTests": "printed_global_tests.csv",
    "RSquare": "printed_rsquare.csv",
    "Association": "printed_association.csv",
    "OddsRatios": "printed_odds_ratios.csv",
    "LackFitPartition": "printed_hl_partition.csv",
    "LackFitChiSq": "printed_hosmer_lemeshow.csv",
    "Classification": "printed_classification.csv",
}
# Work datasets the scripts already build but only print/plot -> exported file.
EXPORT_AFTER = {
    "train.sas": {"roc_train": "printed_roc_train.csv", "roc_valid": "printed_roc_validation.csv",
                  "confusion_matrix_train": "printed_confusion_train.csv",
                  "confusion_matrix": "printed_confusion_validation.csv"},
    "metrics_calculation.sas": {"roc_stats": "printed_roc_metrics.csv",
                                "cumulative_lift": "printed_cumulative_lift.csv",
                                "psi_calculation": "printed_psi_calculation.csv"},
}


def capture_statement() -> str:
    parts = " ".join(f"{t}=work._j_{t.lower()}" for t in CAPTURE_TABLES)
    return f"    ods output {parts} ParameterEstimates=work.model_coefficients;"


def export_code(dataset: str, filename: str) -> str:
    return (f'proc export data={dataset} outfile="&output_path/{filename}" dbms=csv replace; run;\n')


def redirect_paths(src: str, data_dir: str, out_dir: str) -> str:
    """Point the scripts' hardcoded %let paths at this run's folders."""
    src, n_data = re.subn(r"%let\s+data_path\s*=\s*[^;]*;", f"%let data_path = {data_dir};", src)
    src, n_out = re.subn(r"%let\s+output_path\s*=\s*[^;]*;", f"%let output_path = {out_dir};", src)
    if n_out != 1 or n_data > 1:
        raise RuntimeError(f"unexpected path macros: data_path={n_data} output_path={n_out}")
    if ORIGINAL_HOME in src:
        raise RuntimeError(f"{ORIGINAL_HOME} still referenced after redirection")
    return src


def instrument(name: str, code: str) -> str:
    if name == "train.sas":
        if code.count(CAPTURE_ANCHOR) != 1:
            raise RuntimeError("capture anchor not found exactly once in train.sas")
        code = code.replace(CAPTURE_ANCHOR, capture_statement())
        code += "".join(export_code(f"work._j_{t.lower()}", f) for t, f in CAPTURE_TABLES.items())
    code += "".join(export_code(f"work.{d}", f) for d, f in EXPORT_AFTER.get(name, {}).items())
    return code


def warnings_in(log: str) -> list[str]:
    return [re.sub(r"\s+", " ", ln).strip() for ln in log.splitlines() if ln.startswith("WARNING")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--mutation", choices=sorted(MUTATIONS), default=None)
    ap.add_argument("--profile", default="oda_eu")
    ap.add_argument("--data-dir", type=Path, default=REPO / "data", help="local folder with cs-training.csv, cs-test.csv")
    ap.add_argument("--scripts", default=",".join(SCRIPTS), help="comma-separated subset, run in README order")
    ap.add_argument("--stage-inputs", type=Path, help="local folder whose files are uploaded into the output folder first")
    ap.add_argument("--write-warning-allowlist", action="store_true", help="record this run's WARNINGs as the known set")
    args = ap.parse_args()

    scripts = [s for s in SCRIPTS if s in args.scripts.split(",")]
    if len(scripts) != len(args.scripts.split(",")):
        ap.error(f"unknown script in --scripts; choose from {SCRIPTS}")
    local_dir = JUDGE / "runs" / args.run_id
    if local_dir.exists():
        ap.error(f"{local_dir} exists; run-ids are never reused (delete it deliberately to rerun)")
    local_dir.mkdir(parents=True)

    sources = {name: (REPO / name).read_text() for name in SCRIPTS}
    if args.mutation:
        sources = apply_mutation(sources, args.mutation)

    known = set(ALLOWLIST.read_text().splitlines()) if ALLOWLIST.exists() else set()
    sas = saspy.SASsession(cfgname=args.profile, results="TEXT")
    t0 = time.time()
    meta: dict = {"run_id": args.run_id, "mutation": args.mutation, "scripts": scripts,
                  "data_dir": str(args.data_dir), "stage_inputs": str(args.stage_inputs or ""),
                  "sas_version": sas.sasver, "errors": {}, "new_warnings": {}}
    all_warnings: list[str] = []
    try:
        log = sas.submit("%put JUDGEHOME=%sysget(HOME);")["LOG"]
        home = next(ln.split("=", 1)[1].strip() for ln in log.splitlines() if ln.startswith("JUDGEHOME="))
        run_root = f"{home}/sasmig/runs/{args.run_id}-{time.strftime('%Y%m%dT%H%M%S')}"
        data_dir, out_dir, gdir = f"{run_root}/data", f"{run_root}/output", f"{run_root}/graphs"
        sas.submit(f"""options dlcreatedir;
            libname _mk "{home}/sasmig"; libname _mk "{home}/sasmig/runs"; libname _mk "{run_root}";
            libname _mk "{data_dir}"; libname _mk "{out_dir}"; libname _mk "{gdir}"; libname _mk clear;""")
        # Environment, not code: under IOM the default graphics path is a read-only
        # server folder, and a failed ROC image write also drops the ROCAssociation
        # table (AUC). SAS Studio, where the goldens were made, has a writable path.
        sas.submit(f'ods listing gpath="{gdir}";')
        uploads = [(args.data_dir / f, f"{data_dir}/{f}") for f in DATA_FILES]
        if args.stage_inputs:
            uploads += [(p, f"{out_dir}/{p.name}") for p in sorted(args.stage_inputs.glob("*.csv"))]
        for local, remote in uploads:  # always upload: never trust a same-named remote file
            res = sas.upload(str(local), remote, overwrite=True)
            if not res.get("Success"):
                raise RuntimeError(f"upload failed for {local}: {res}")

        for name in scripts:
            code = instrument(name, redirect_paths(sources[name], data_dir, out_dir))
            ts = time.time()
            res = sas.submit(code)
            (local_dir / f"{name}.log").write_text(res["LOG"])
            (local_dir / f"{name}.lst").write_text(res["LST"])
            meta["errors"][name] = [ln for ln in res["LOG"].splitlines() if ln.startswith("ERROR")]
            w = warnings_in(res["LOG"])
            all_warnings += w
            meta["new_warnings"][name] = sorted({x for x in w if x not in known})
            print(f"{name}: {time.time() - ts:.0f}s, {len(meta['errors'][name])} ERROR, "
                  f"{len(meta['new_warnings'][name])} new WARNING", flush=True)

        staged = {p.name for p in args.stage_inputs.glob("*.csv")} if args.stage_inputs else set()
        for f in sorted(sas.dirlist(out_dir)):
            if f.endswith(".csv") and f not in staged:
                res = sas.download(str(local_dir / f), f"{out_dir}/{f}")
                if not res.get("Success"):
                    raise RuntimeError(f"download failed for {f}: {res}")
        meta["remote_run_root"] = run_root
    finally:
        meta["wall_clock_s"] = round(time.time() - t0)
        (local_dir / "run_meta.json").write_text(json.dumps(meta, indent=2))
        sas.endsas()
    if args.write_warning_allowlist:
        ALLOWLIST.write_text("\n".join(sorted(set(all_warnings))) + "\n")
        print(f"wrote {len(set(all_warnings))} known warnings to {ALLOWLIST.name}")
    print(json.dumps({k: meta[k] for k in ("run_id", "mutation", "wall_clock_s")}))
    return 1 if any(meta["errors"].values()) else 0


if __name__ == "__main__":
    sys.exit(main())
