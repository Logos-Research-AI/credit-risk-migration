"""Records step 2026-11-18: adds the column update_2026_11_18_records to manifest.tsv.
Run once: cd migration/port-to-lean && python3 diffeval/work/manifest_records_2026-11-18.py
"""
from pathlib import Path

M = Path(__file__).resolve().parent.parent.parent / "manifest.tsv"
lines = M.read_text().splitlines()
head = lines[0].split("\t")
assert len(head) == 12 and head[-1] == "update_2026_11_18_fifth", head
head.append("update_2026_11_18_records")

# items whose stored code was compared with its statement_text (equal) and with port/ (current)
CODE_OK = {
    "def:confusion_metrics", "def:metrics_run_05_cumulative_lift", "def:metrics_run_08_validation_summary",
    "def:metrics_run_09_model_performance", "def:train_run_02_stepwise_summary", "def:train_run_04_score_train",
    "def:train_run_05_association", "def:train_run_06_coefficients_odds", "def:train_run_15_printed_roc",
    "def:_hl_groups", "def:_kept", "def:_solve_sas", "def:_inv_sas", "def:_left_out", "def:classification_is_made",
}
# stored code is the version before the fifth diff (statement_text equals it); refresh needs write_code (clears Lean)
CODE_STALE = {
    "def:train_run_01_fit_frame", "def:train_run_08_ctable", "def:train_run_10_score_valid",
    "def:train_run_11_confusion_valid", "def:train_run_13_roc",
}
# not compared (over the fetch cap or not fetched in this step)
NOT_COMPARED = {
    "def:run_py", "def:run_py_py_py", "def:classification_table", "def:train_run_03_fit_global_rsquare",
    "def:train_run_14_final_and_summary", "def:hosmer_lemeshow",
}
TEXT_PRECOND = {
    "def:train_run_10_score_valid": "def:train_run_10_score_valid_precond statement_text reworded (edit_text)",
    "def:hosmer_lemeshow": "def:hosmer_lemeshow_precond statement_text reworded (edit_text)",
}
out = ["\t".join(head)]
for ln in lines[1:]:
    c = ln.split("\t")
    c += [""] * (12 - len(c))
    note = ""
    if c[11].strip():
        item = c[3]
        parts = []
        if item in CODE_OK:
            parts.append("statement_text = code, code = port (checked, no edit)")
        elif item in CODE_STALE:
            parts.append("STALE CODE: stored code is the version before the fifth diff, statement_text equals it; needs write_code (lead)")
        elif item in NOT_COMPARED:
            parts.append("code/statement_text not compared in this step")
        else:
            parts.append("precondition change only: no code edit")
        if item in TEXT_PRECOND:
            parts.append(TEXT_PRECOND[item])
        if c[1].endswith(("train.py", "sas_compat.py", "metrics_calculation.py")) and "precondition change" not in c[11]:
            parts.append("source reference re-set to credit_risk/%s:%s (update_item_source accepted)" % (c[1].split("/")[-1], c[2]))
        note = "; ".join(parts)
    c.append(note)
    out.append("\t".join(c[:13]))
M.write_text("\n".join(out) + "\n")
print("rows", len(out) - 1)
