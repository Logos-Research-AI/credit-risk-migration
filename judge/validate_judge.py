"""Validate the judge against deliberately broken ORIGINAL code (prompt 00b, step 3).

For every mutation run in runs/m_<mutation>/, compare against its reference:
  * real-data mutations   -> reference/
  * edge-scenario ones    -> reference/scenarios/<scenario>/   (mutations.EDGE_SCENARIO)
Verdict per mutation:
  CAUGHT      port mode fails (good)
  EQUIVALENT  every judged file byte-identical to the reference: no judge could see it
  MISSED      outputs differ but port mode passes: a JUDGE BUG
  NOT RUN     no run folder yet
Also re-checks the references themselves: each must pass against itself and its
run_meta.json must show no SAS errors and no unexpected warnings.

Usage (from judge/): uv run python validate_judge.py   -> prints + writes validation_report.md
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import compare as C
from mutations import EDGE_SCENARIO, MUTATIONS

JUDGE = Path(__file__).resolve().parent
REF = JUDGE / "reference"
SCEN_FILES = {"real_metrics": C.STAGES["metrics"], "edge_predict": None, "edge_metrics_a": C.STAGES["metrics"], "edge_metrics_b": C.STAGES["metrics"],
              "edge_metrics_c": C.STAGES["metrics"]}


def reference_for(mutation: str) -> tuple[Path, list[str]]:
    scen = EDGE_SCENARIO.get(mutation)
    if scen is None:
        return REF, list(C.FILES)
    if scen == "real_metrics":
        return REF, C.STAGES["metrics"]
    files = SCEN_FILES[scen] or list(C.FILES)
    return REF / "scenarios" / scen, files


def split_drift(ref: Path, run: Path) -> str:
    """SAS's own 70/30 split is not guaranteed (PROC SQL join order feeds SURVEYSELECT).
    A run whose split differs from the reference cannot validate anything."""
    f = "model_features_train.csv"
    if not (run / f).exists() or not (ref / f).exists():
        return ""
    ids = lambda p: set(C.read_text_csv(p).get_column("row_id").to_list())
    a, b = ids(ref / f), ids(run / f)
    return "" if a == b else f"{len(a ^ b)} row_ids differ in training membership"


def summarize(results: list[C.FileResult]) -> str:
    bad = [r for r in results if r.status != "PASS"]
    return "; ".join(f"{r.file}[{','.join(sorted(r.failed))}]" for r in bad) or "-"


def main() -> int:
    lines = ["# Judge validation report", "",
             "## References", "", "| Reference | Self-check | SAS errors | New warnings |", "|---|---|---|---|"]
    ok = True
    for ref, files in [(REF, list(C.FILES))] + [(REF / "scenarios" / s, SCEN_FILES[s] or list(C.FILES))
                                                for s in SCEN_FILES if s != "real_metrics"]:
        if not ref.exists():
            lines.append(f"| {ref.relative_to(JUDGE)} | MISSING | | |")
            ok = False
            continue
        meta = C.load_meta(ref)
        res = C.compare_dir(ref, ref, files, "strict")
        selfok = all(r.status == "PASS" for r in res)
        errs = sum(len(v) for v in meta.get("errors", {}).values())
        neww = sum(len(v) for v in meta.get("new_warnings", {}).values())
        ok &= selfok and errs == 0
        lines.append(f"| {ref.relative_to(JUDGE)} ({len(files)} files) | {'PASS' if selfok else 'FAIL'} | {errs} | {neww} |")

    # Staged protocol check: metrics_calculation.sas alone, fed the reference risk scores,
    # must reproduce the reference metrics byte-for-byte (the port is judged this way).
    staged = JUDGE / "runs" / "ref_real_metrics"
    if (staged / "run_meta.json").exists():
        res = C.compare_dir(REF, staged, C.STAGES["metrics"], "strict")
        sok = all(r.status == "PASS" for r in res)
        ok &= sok
        lines.append(f"| staged metrics run on reference risk scores vs reference ({len(res)} files, strict) "
                     f"| {'PASS' if sok else 'FAIL: ' + summarize(res)} | | |")
    else:
        ok = False
        lines.append("| staged metrics run (runs/ref_real_metrics) | NOT RUN | | |")

    lines += ["", "## Mutations (port mode)", "",
              "| Mutation | Reference | Verdict | Failing files [columns] | SAS errors in run |", "|---|---|---|---|---|"]
    counts: dict[str, int] = {}
    for m in MUTATIONS:
        run = JUDGE / "runs" / f"m_{m}"
        ref, files = reference_for(m)
        if not run.exists():
            verdict, detail, errs = "NOT RUN", "-", "-"
        elif not (run / "run_meta.json").exists():
            verdict, detail, errs = "IN PROGRESS", "-", "-"
        else:
            meta = json.loads((run / "run_meta.json").read_text())
            errs = str(sum(len(v) for v in meta.get("errors", {}).values()))
            drift = split_drift(ref, run)
            strict = C.compare_dir(ref, run, files, "strict")
            port = C.compare_dir(ref, run, files, "port")
            if drift:
                verdict, detail = "RERUN", f"SAS split drift: {drift} (verdict would be contaminated)"
            elif all(r.status == "PASS" for r in strict):
                verdict, detail = "EQUIVALENT", "outputs byte-identical"
            elif any(r.status != "PASS" for r in port):
                verdict, detail = "CAUGHT", summarize(port)
            else:
                verdict, detail = "MISSED", f"strict diffs: {summarize(strict)}"
        counts[verdict] = counts.get(verdict, 0) + 1
        ok &= verdict in ("CAUGHT", "EQUIVALENT")
        lines.append(f"| `{m}` | {ref.relative_to(JUDGE)} | **{verdict}** | {detail} | {errs} |")

    lines += ["", "Totals: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())), ""]
    report = "\n".join(lines)
    (JUDGE / "validation_report.md").write_text(report)
    print(report)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
