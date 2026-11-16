"""T19: current line ranges of every code item (ast for top-level names, fixed step ranges checked by first/last line)."""
import ast, json, pathlib, sys
P = pathlib.Path("../../port/credit_risk")
out = {}
def top(fn, names, rename=None):
    src = (P / fn).read_text(); tree = ast.parse(src); lines = src.splitlines()
    for node in tree.body:
        nm = None
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)): nm = node.name
        elif isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name): nm = node.targets[0].id
        elif isinstance(node, ast.AnnAssign): nm = node.target.id
        if nm in names:
            start = min([node.lineno] + [d.lineno for d in getattr(node, "decorator_list", [])])
            # leading comment block directly above a constant belongs to it (as stored for _TIE_EPS)
            if nm in ("_TIE_EPS", "_SE_EPS", "_SQRTBIG"):
                while lines[start - 2].startswith("#"): start -= 1
            key = (rename or {}).get(nm, nm)
            if key in out and fn == "sas_compat.py":  # overloads: keep the first start
                out[key] = (fn, out[key][1], node.end_lineno)
            else:
                out[key] = (fn, start, node.end_lineno)
top("sas_compat.py", {"FloatArray","Z975","ExprOrNum","_e","_named","_has_bare_column","_is_scalar","chi2_sf","lt","le","gt","ge","eq","flag","div","sas_sum","sas_min","sas_max","sas_log","sas_exp","_ROUND_FUZZ_CAP","_ROUND_FUZZ","sas_round","sql_sum","sql_mean","sql_min","sql_max","merge_one_to_one","proc_rank_groups","LogisticFit","_expit","StepwiseStep","StepwiseResult","RocAssociation","_TIE_EPS","_SE_EPS","_SQRTBIG","_Pairs","_groups","_pairs","_ratio","roc_association","AssociationTable","association_table","_hl_groups","hosmer_lemeshow","classification_table"}, {"FloatArray": "FloatArray_"})
top("metrics_calculation.py", {"_into_float", "confusion_metrics", "run"}, {"run": "run_py"})
top("feature_engineering.py", {"run"}); top("predict.py", {"run"}, {"run": "run_py_py"}); top("train.py", {"run"}, {"run": "run_py_py_py"})
steps = {
 "feature_engineering.py": {"fe_run_00_input_check": (43,128), "fe_run_01_clean": (138,152), "fe_run_02_income_medians": (157,173), "fe_run_02b_medians_all": (179,186), "fe_run_03_cleaned": (189,204), "fe_run_04_imputed": (208,229), "fe_run_05_features": (234,336), "fe_run_06_split": (342,350)},
 "predict.py": {"predict_run_00_input_check": (82,182), "predict_run_01_clean": (192,206), "predict_run_02_medians": (211,222), "predict_run_03_cleaned": (228,241), "predict_run_04_imputed": (247,271), "predict_run_05_features": (277,372), "predict_run_06_score": (376,394), "predict_run_07_predictions": (398,443), "predict_run_08_outputs": (446,478)},
 "metrics_calculation.py": {"metrics_run_01_roc_auc": (114,152), "metrics_run_02_ks": (157,196), "metrics_run_03_thresholds": (201,210), "metrics_run_04_deciles": (216,283), "metrics_run_05_cumulative_lift": (290,321), "metrics_run_06_psi": (328,401), "metrics_run_07_calibration": (407,423), "metrics_run_08_validation_summary": (430,442), "metrics_run_09_model_performance": (471,485), "metrics_run_10_printed_roc": (508,520)},
 "train.py": {"train_run_01_fit_frame": (55,111), "train_run_02_stepwise_summary": (117,148), "train_run_03_fit_global_rsquare": (154,255), "train_run_04_score_train": (259,275), "train_run_05_association": (279,312), "train_run_06_coefficients_odds": (318,358), "train_run_07_hl": (363,393), "train_run_08_ctable": (397,434), "train_run_09_confusion_train": (443,502), "train_run_10_score_valid": (509,524), "train_run_11_confusion_valid": (528,578), "train_run_12_risk_scores": (584,673), "train_run_13_roc": (681,690), "train_run_14_final_and_summary": (697,785), "train_run_15_printed_roc": (789,805)},
}
for fn, d in steps.items():
    lines = (P / fn).read_text().splitlines()
    for k, (a, b) in d.items():
        out[k] = (fn, a, b)
        if "-v" in sys.argv: print(f"{k:36s} {a:4d} | {lines[a-1].strip()[:50]:50s} ... {b:4d} | {lines[b-1].strip()[:40]}")
json.dump(out, open("experiments/t19_ranges.json", "w"), indent=0)
for k, v in out.items():
    if v[0] in ("sas_compat.py",) or k.startswith("run") or k in ("_into_float", "confusion_metrics"): print(k, v)
