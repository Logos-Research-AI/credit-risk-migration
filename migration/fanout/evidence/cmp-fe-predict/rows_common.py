OUT="/Users/cristophersalvi/GitHub/sas-migration/migration/inventory.cmp-fe-predict.tsv"
HEADER="file\tsymbol\tsource_construct\tclassification\ttarget_translation\tevidence\tstatus"
import os
def append(rows):
    new = not os.path.exists(OUT)
    with open(OUT,"a") as f:
        if new: f.write(HEADER+"\n")
        for r in rows:
            r = r + ["proposed"] if len(r)==6 else r
            assert len(r)==7 and all("\t" not in x and "\n" not in x for x in r), r
            f.write("\t".join(r)+"\n")
FE_IN=("never missing on EVERY input feature_engineering can receive: data/cs-training.csv and judge/scenarios/edge_predict/cs-training.csv "
       "(byte copy, cmp-identical; judge/make_scenarios.py edge_predict) both have 0 empty/NA/non-numeric values in {cols} (150,000 rows), "
       "read best32. (judge/reference/listings/feature_engineering.sas.log:56-67)")
PR_IN=("never missing on EVERY input predict can receive: data/cs-test.csv and judge/scenarios/edge_predict/cs-test.csv "
       "(the edge file changes only MonthlyIncome; judge/make_scenarios.py edge_predict) both have 0 empty/NA/non-numeric values in {cols} (101,503 rows each), "
       "read best32. (judge/reference/listings/predict.sas.log:56-67 and judge/reference/scenarios/edge_predict/listings/predict.sas.log:56-67)")
FE_VER=("plain-polars recomputation from the raw CSV reproduces {what} on all 150,000 rows of judge/reference/model_features_{{train,validation}}.csv, 0 mismatches "
        "(scratchpad/fan/cmp-fe-predict/verify.py)")
PR_VER=("plain-polars recomputation reproduces {what} of judge/reference/test_predictions.csv AND judge/reference/scenarios/edge_predict/test_predictions.csv, "
        "all 101,503 rows each, 0 mismatches (scratchpad/fan/cmp-fe-predict/verify.py)")
