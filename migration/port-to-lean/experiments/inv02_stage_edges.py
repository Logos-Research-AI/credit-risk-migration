# RETIRED 2026-11-16: this script is a record of the port before the update of 2026-11-16 and no longer
# runs as a script (its helper functions are still imported by later generators): it calls export_train_medians, fix_train_medians, medians, fix_psi_bins; the stage edges are now in diffeval/units/t6_gen.py, t11_gen.py, t16_gen.py.
# Its recorded outputs describe the port as it was then.
import sys as _sys

if __name__ == "__main__":  # retired as a script; its helpers may still be imported
    _sys.exit("RETIRED 2026-11-16: " + __file__ + " calls keywords the port no longer has; see the note at its top")

"""INV02: the four stages on crafted edge inputs behind migration/inventory.tsv. Run: uv run python migration/experiments/inv02_stage_edges.py"""
import sys, io, contextlib, json, polars as pl
from pathlib import Path
from credit_risk import metrics_calculation as mc, feature_engineering as fe, predict as pr
S=Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__import__("tempfile").mkdtemp())
def run(fn,*a,**k):
    try:
        with contextlib.redirect_stdout(io.StringIO()): fn(*a,**k)
        return "ok"
    except Exception as e: return "RAISED "+repr(e)[:300]
def dump(d, names=None):
    for p in sorted(d.glob("*.csv")):
        if names and p.name not in names: continue
        print(f"--- {p.name}"); print(p.read_text()[:1800])
HDR=",SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,age,NumberOfTime30-59DaysPastDueNotWorse,DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents\n"
rows=["1,1,0.5,45,2,0.8,9120,13,0,6,0,2",   # normal
      "2,0,0.9,25,0,0.1,NA,4,0,0,0,NA",      # age<30 income NA, deps NA: only under-30 row -> no median
      "3,0,,35,,0.5,3000,,,1,,0",            # null utilization, all three late null, null credit lines
      "4,0,0.2,,1,0.2,NA,2,1,0,0,-1",        # null age, deps = -1 (divisor 0), income NA -> group 5 median
      ",1,2.5,70,0,50,1000,1,0,0,0,3",       # null row id
      "6,0,0.1,65,0,0.1,5000,3,0,0,0,1",
      "7,0,0.1,66,0,0.1,7000,3,0,0,0,1"]
d=S/"fe_in"; d.mkdir(exist_ok=True); (d/"cs-training.csv").write_text(HDR+"\n".join(rows)+"\n")
(S/"split.csv").write_text("row_id\n1\n3\n6\n")
print("FE:", run(fe.run, d, S/"fe_out", split_ids=S/"split.csv", export_train_medians=True)); dump(S/"fe_out")
(S/"split2.csv").write_text("row_id\n1\n\n6\n"); print("FE split with empty id:", run(fe.run, d, S/"fe_out2", split_ids=S/"split2.csv"))
print("train rows", pl.read_csv(S/"fe_out2/model_features_train.csv")["row_id"].to_list(), "valid rows", pl.read_csv(S/"fe_out2/model_features_validation.csv")["row_id"].to_list())
# predict on the same rows
d2=S/"pr_in"; d2.mkdir(exist_ok=True); (d2/"cs-test.csv").write_text(HDR+"\n".join(rows)+"\n")
m=S/"pr_model"; m.mkdir(exist_ok=True); (m/"model.json").write_text(json.dumps({"intercept":-2.5,"coefficients":{"credit_utilization_capped":0.01,"log_monthly_income":-0.1,"total_late_payments":0.5}}))
print("PREDICT:", run(pr.run, m, S/"pr_out", data_dir=d2)); dump(S/"pr_out")
(m/"model.json").write_text(json.dumps({"intercept":-2.5,"coefficients":{"nope":0.01}})); print("PREDICT absent col:", run(pr.run, m, S/"pr_out2", data_dir=d2))
(m/"model.json").write_text(json.dumps({"intercept":800,"coefficients":{"age":1000.0}})); print("PREDICT huge eta:", run(pr.run, m, S/"pr_out3", data_dir=d2)); dump(S/"pr_out3",{"test_predictions.csv"})
print("PREDICT fix no medians:", run(pr.run, m, S/"pr_out4", data_dir=d2, fix_train_medians=True))
(S/"med.csv").write_text("age_group,median_income\n1,100\n2,200\n3,300\n4,400\n5,500\n5,555\n"); print("PREDICT fix dup medians:", run(pr.run, m, S/"pr_out5", data_dir=d2, fix_train_medians=True, medians=S/"med.csv")); print(" rows:", pl.read_csv(S/"pr_out5/kaggle_submission.csv").height)
(S/"med2.csv").write_text("age_group,median_income\n1,100\n2,200\n3,300\n4,400\n"); print("PREDICT fix missing group:", run(pr.run, m, S/"pr_out6", data_dir=d2, fix_train_medians=True, medians=S/"med2.csv"))
# metrics crafted
def mrun(name, valid, train, fix=False, show=("validation_summary.csv","ks_statistic.csv","decile_analysis.csv","printed_psi_calculation.csv","threshold_analysis.csv","printed_cumulative_lift.csv","calibration_plot.csv","printed_roc_metrics.csv","model_performance_metrics.csv")):
    d=S/f"m_in_{name}"; d.mkdir(exist_ok=True)
    (d/"risk_scores_validation.csv").write_text("row_id,default_flag,pd_logistic\n"+"\n".join(valid)+"\n"); (d/"risk_scores_train.csv").write_text("row_id,default_flag,pd_logistic\n"+"\n".join(train)+"\n")
    print(f"=== METRICS {name} fix={fix}:", run(mc.run, d, S/f"m_out_{name}_{int(fix)}", fix_psi_bins=fix)); dump(S/f"m_out_{name}_{int(fix)}", set(show))
tr=[f"{i},{i%2},{0.05*i:.2f}" for i in range(1,13)]
mrun("nulls", ["1,0,0.1","2,1,0.9","3,,0.5","4,1,","5,0,0.2","6,1,0.7","7,0,0.7","8,,"], tr)
mrun("oneclass", ["1,0,0.1","2,0,0.9","3,0,0.5"], tr, show=("validation_summary.csv","ks_statistic.csv","threshold_analysis.csv","printed_cumulative_lift.csv"))
mrun("kstie", ["1,0,0.1","2,1,0.2","3,0,0.3","4,1,0.4"], tr, show=("validation_summary.csv","ks_statistic.csv","model_performance_metrics.csv"))
mrun("fixgap", ["1,0,0.01","2,1,0.02","3,0,0.03"], tr, fix=True, show=("printed_psi_calculation.csv","validation_summary.csv"))
mrun("fixnull", ["1,0,0.01","2,1,","3,0,0.03"], tr, fix=True, show=("printed_psi_calculation.csv","validation_summary.csv"))
mrun("trainallnull", ["1,0,0.01","2,1,0.5","3,0,0.03"], ["1,0,","2,1,"], fix=True, show=("printed_psi_calculation.csv",))
mrun("trainallnull", ["1,0,0.01","2,1,0.5","3,0,0.03"], ["1,0,","2,1,"], fix=False, show=("printed_psi_calculation.csv","validation_summary.csv"))

# the three delivered edge scenarios (labels: edge a, edge b, edge c)
for scn in "abc":
    for fix in (False, True):
        out = S / f"out_m_{scn}_{int(fix)}"
        print(f"=== METRICS edge {scn} fix={fix}:", run(mc.run, Path(f"inputs/scenarios/edge_metrics_{scn}"), out, fix_psi_bins=fix))
        dump(out, {"validation_summary.csv", "ks_statistic.csv", "printed_psi_calculation.csv", "threshold_analysis.csv", "decile_analysis.csv"} if not fix else {"validation_summary.csv", "printed_psi_calculation.csv"})
    v = pl.read_csv(f"inputs/scenarios/edge_metrics_{scn}/risk_scores_validation.csv"); t = pl.read_csv(f"inputs/scenarios/edge_metrics_{scn}/risk_scores_train.csv")
    print("valid nulls", v.null_count().row(0), "distinct valid pd", v["pd_logistic"].n_unique(), "distinct train pd", t["pd_logistic"].n_unique())
