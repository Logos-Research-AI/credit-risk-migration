"""T19: rewrite manifest.tsv with the current line ranges, the new units and the task of each changed unit."""
import csv, json
R = json.load(open("experiments/t19_ranges.json"))
rows = list(csv.DictReader(open("manifest.tsv"), delimiter="\t"))
TASK = {"_pairs": "T1", "roc_association": "T1", "association_table": "T1 (restore)",
        "run": "T6", "fe_run_01_clean": "T3", "fe_run_04_imputed": "T4", "fe_run_05_features": "T5",
        "run_py_py": "T11", "predict_run_01_clean": "T8", "predict_run_02_medians": "T8", "predict_run_04_imputed": "T8",
        "predict_run_05_features": "T9", "predict_run_07_predictions": "T10", "predict_run_08_outputs": "T10",
        "run_py": "T16", "metrics_run_01_roc_auc": "T12", "metrics_run_02_ks": "T13", "metrics_run_04_deciles": "T14",
        "metrics_run_05_cumulative_lift": "T14", "metrics_run_06_psi": "T15",
        "run_py_py_py": "T18", "train_run_12_risk_scores": "T17", "train_run_13_roc": "T18 (restore)", "train_run_05_association": "T18 (restore)"}
NEW = [("_SE_EPS", "T1", "B4"), ("_SQRTBIG", "T1", "B4"), ("_groups", "T1", "B4"), ("fe_run_00_input_check", "T2", "B7"),
       ("fe_run_02b_medians_all", "T4", "B7"), ("predict_run_00_input_check", "T7", "B8")]
fields = list(rows[0].keys()) + ["update_2026_11_16"]
out = []
for r in rows:
    key = r["item_id"].removeprefix("def:")
    if key == "proc_rank_apply_groups":
        r["update_2026_11_16"] = "REMOVE with T15 (function deleted from the port)"; out.append(r); continue
    fn, a, b = R[key]
    r["file"] = f"port/credit_risk/{fn}"; r["lines"] = f"{a}-{b}"
    r["update_2026_11_16"] = f"CHANGE {TASK[key]}" if key in TASK else "unchanged (source range updated; stored source differs in a docstring only)" if key in ("le", "ge", "eq") else "unchanged (source range updated)"
    out.append(r)
for key, task, bundle in NEW:
    fn, a, b = R[key]
    out.append({"unit": key, "file": f"port/credit_risk/{fn}", "lines": f"{a}-{b}", "item_id": f"def:{key}", "upstream": "-", "bundle": bundle,
                "state": "to add", "precondition": "-", "open_params": "-", "update_2026_11_16": f"NEW {task}"})
w = csv.DictWriter(open("manifest.tsv", "w", newline=""), fieldnames=fields, delimiter="\t", lineterminator="\n"); w.writeheader(); w.writerows(out)
print(len(out), "rows;", sum(1 for r in out if r["update_2026_11_16"].startswith("CHANGE")), "change;", sum(1 for r in out if r["update_2026_11_16"].startswith("NEW")), "new")
