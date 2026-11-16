"""T20 (2026-11-16): refresh manifest.tsv from the blueprint after the update.

Values below were read from the blueprint with get_items (state, statement_dependencies; the
`-- OPEN(port):` trailers and signatures of the units reviewed) on 2026-11-16. The line ranges are
the lines where diffeval/stored_source_check.py found the stored source in the port.
Run from migration/port-to-lean; running it again changes nothing.
"""

import csv
from pathlib import Path

M = Path(__file__).resolve().parent.parent / "manifest.tsv"
F = "DefinitionFormalized"

# item -> (lines or None, upstream, precondition or None, open_params or None)
UPD = {
    "def:run": (None, "def:ExprOrNum,def:fe_run_00_input_check,def:fe_run_01_clean,def:fe_run_02_income_medians,"
                "def:fe_run_02b_medians_all,def:fe_run_03_cleaned,def:fe_run_04_imputed,def:fe_run_05_features,"
                "def:fe_run_06_split,def:flag,def:sas_sum,def:sas_max,def:sas_min,def:sas_log,def:div",
                "def:run_precond", "full,input_best32,sas_best12,cs_training,split_ids"),
    "def:fe_run_00_input_check": (None, "def:ExprOrNum,def:flag,def:ge,def:eq,def:lt",
                                  "def:fe_run_00_input_check_precond", "input_best32"),
    "def:fe_run_01_clean": (None, "def:ExprOrNum", None, "input_best32,sas_best12"),
    "def:fe_run_02b_medians_all": (None, "def:ExprOrNum", "def:fe_run_02b_medians_all_precond", "-"),
    "def:fe_run_04_imputed": (None, "def:ExprOrNum", None, None),
    "def:fe_run_05_features": (None, "def:ExprOrNum,def:flag,def:sas_sum,def:sas_max,def:sas_min,def:sas_log,def:lt,def:le",
                               None, None),
    "def:metrics_run_01_roc_auc": ("109-152", "def:roc_association,def:ExprOrNum,def:flag", None, "fsum"),
    "def:metrics_run_02_ks": ("156-196", "def:_into_float,def:flag,def:sql_sum,def:sql_max,def:sql_min,def:div,def:eq,"
                              "def:ExprOrNum", None, None),
    "def:metrics_run_04_deciles": ("214-283", "def:proc_rank_groups,def:sql_sum,def:sql_mean,def:sql_min,def:sql_max,"
                                   "def:div,def:ExprOrNum", None, None),
    "def:metrics_run_05_cumulative_lift": ("287-321", "def:_into_float,def:sql_sum,def:sql_mean,def:div,def:gt,"
                                           "def:ExprOrNum", None, None),
    "def:metrics_run_06_psi": ("325-401", "def:div,def:sas_log,def:sql_sum,def:lt,def:gt,def:flag,def:sas_max,"
                               "def:ExprOrNum", None, None),
    "def:run_py_py": (None, "def:predict_run_00_input_check,def:predict_run_01_clean,def:predict_run_02_medians,"
                      "def:predict_run_03_cleaned,def:predict_run_04_imputed,def:predict_run_05_features,"
                      "def:predict_run_06_score,def:predict_run_07_predictions,def:predict_run_08_outputs,def:flag,"
                      "def:lt,def:ge,def:sas_sum,def:sas_max,def:sas_min,def:sas_log,def:sas_exp,def:ExprOrNum",
                      None, "full,input_best32,intercept,coefficients,sas_best12,model_coefficients_exists,cs_test,"
                      "income_medians"),
    "def:predict_run_00_input_check": (None, "def:ExprOrNum,def:flag,def:ge,def:eq,def:lt", None, None),
    "def:predict_run_01_clean": (None, "def:ExprOrNum", None, "input_best32,sas_best12"),
    "def:predict_run_02_medians": (None, "def:ExprOrNum", None, "income_medians"),
    "def:predict_run_04_imputed": (None, "def:ExprOrNum", None, None),
    "def:predict_run_05_features": (None, "def:ExprOrNum,def:sas_sum,def:flag,def:lt,def:le,def:sas_max,def:sas_log,"
                                    "def:sas_min", None, None),
    "def:predict_run_07_predictions": (None, "def:ExprOrNum,def:flag,def:ge,def:lt,def:le", None, None),
    "def:predict_run_08_outputs": ("446-469", "def:ExprOrNum", "def:predict_run_08_outputs_precond", None),
    "def:_pairs": (None, "def:_Pairs,def:_TIE_EPS,def:_SE_EPS,def:_groups,def:FloatArray_,def:ExprOrNum", None, None),
    "def:roc_association": (None, "def:RocAssociation,def:_pairs,def:_ratio,def:Z975,def:_SQRTBIG,def:FloatArray_,"
                            "def:ExprOrNum", None, "fsum"),
    "def:association_table": (None, "def:AssociationTable,def:_pairs,def:_ratio", None, None),
    "def:_SE_EPS": (None, "-", "-", "-"),
    "def:_SQRTBIG": (None, "-", "-", "-"),
    "def:_groups": (None, "def:FloatArray_,def:ExprOrNum", "def:_groups_precond", "-"),
    "def:run_py_py_py": (None, "def:train_run_01_fit_frame,def:train_run_02_stepwise_summary,"
                         "def:train_run_03_fit_global_rsquare,def:train_run_04_score_train,def:train_run_05_association,"
                         "def:train_run_06_coefficients_odds,def:train_run_07_hl,def:train_run_08_ctable,"
                         "def:train_run_09_confusion_train,def:train_run_10_score_valid,def:train_run_11_confusion_valid,"
                         "def:train_run_12_risk_scores,def:train_run_13_roc,def:train_run_14_final_and_summary,"
                         "def:train_run_15_printed_roc,def:StepwiseResult,def:StepwiseStep,def:LogisticFit,"
                         "def:association_table,def:hosmer_lemeshow,def:classification_table,def:roc_association,"
                         "def:merge_one_to_one,def:chi2_sf,def:Z975,def:flag,def:div,def:gt,def:ge,def:sas_exp,"
                         "def:ExprOrNum,def:FloatArray_", None,
                         "fmt_wd,fmt_oddsr,sas_d8,sas_d12_3,sas_pvalue,chi2,today,stepwise,fsum,inv,solve,matmul,matvec,"
                         "dot,einsum_q,log1p,pow2,model_features_train,model_features_validation"),
    "def:train_run_05_association": (None, "def:association_table,def:AssociationTable,def:ExprOrNum,def:FloatArray_",
                                     None, None),
    "def:train_run_12_risk_scores": (None, "def:ExprOrNum,def:lt,def:le", None, None),
    "def:train_run_13_roc": (None, "def:roc_association,def:RocAssociation,def:ExprOrNum,def:FloatArray_", None, "fsum"),
}

rows = list(csv.reader(M.open(), delimiter="\t"))
head = rows[0]
ix = {n: i for i, n in enumerate(head)}
out = [head]
for r in rows[1:]:
    item = r[ix["item_id"]]
    if item == "def:proc_rank_apply_groups":
        r[ix["state"]] = "removed from the blueprint (with its precondition)"
        r[ix["update_2026_11_16"]] = "REMOVED with T15 (function deleted from the port)"
    elif item in UPD:
        lines, up, pre, params = UPD[item]
        if lines:
            r[ix["lines"]] = lines
        r[ix["upstream"]] = up
        if pre:
            r[ix["precondition"]] = pre
        if params:
            r[ix["open_params"]] = params
        r[ix["state"]] = F
    out.append(r)
with M.open("w", newline="") as fh:
    csv.writer(fh, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, escapechar=None).writerows(out)
print(len(out) - 1, "rows;", sum(1 for r in out[1:] if r[ix["state"]] == F), "DefinitionFormalized")
