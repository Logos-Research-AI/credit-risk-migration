#!/bin/bash
# Judge contract (judge/README.md "Contract"): runs 1-9 of the Python port, judged in port mode.
# usage: migration/legacy-to-port/parity/run_contract.sh <outdir> [stages...]   stages: fe train metrics predict e2e (default: all)
set -u
ROOT=$(cd "$(dirname "$0")/../../.." && pwd); J=$ROOT/judge; R=$J/reference; O=${1:?outdir}; shift; mkdir -p "$O"; O=$(cd "$O" && pwd)
STAGES=${*:-fe train metrics predict e2e}
mkdir -p "$O"; cd "$ROOT"
SPLIT=$O/split_ids.csv
python3 - "$R/model_features_train.csv" "$SPLIT" <<'PY'
import csv, sys
rows = csv.DictReader(open(sys.argv[1]))
with open(sys.argv[2], "w") as f:
    f.write("row_id\n")
    for r in rows: f.write(r["row_id"] + "\n")
PY
py() { uv run --quiet --project "$ROOT/port" python -m "$@"; }
judge() { local n=$1 st=$2 ref=$3 out=$4; printf '%-4s %-8s ' "$n" "$st";
  (cd "$J" && uv run --quiet python compare.py "$ref" "$out" --mode port --stage "$st" --json "$out/judge_$st.json" > "$out/judge_$st.txt" 2>&1); rc=$?
  grep -E "files pass" "$out/judge_$st.txt" | tr -d '\n'; [ $rc -eq 0 ] && echo "  PASS" || { echo "  FAIL"; grep -E "^FAIL|^      -" "$out/judge_$st.txt" | head -12; }; }
run() { local name=$1; shift; local t0=$(date +%s); py "$@" > "$O/$name.log" 2>&1 || { echo "$name CRASH:"; tail -3 "$O/$name.log"; }; echo "$name $(( $(date +%s)-t0 ))s" >> "$O/timings.txt"; }
# medians: income_medians.csv is in no stage of judge/compare.py; fe's file must be the reference file byte for byte
# (age_group, median_income, overall_median_income: feature_engineering.sas 165-184, 380-391).
medians() { local n=$1 out=$2; printf '%-4s %-8s ' "$n" medians
  if [ ! -f "$out/income_medians.csv" ]; then echo "income_medians.csv not written  FAIL"
  elif cmp -s "$R/income_medians.csv" "$out/income_medians.csv"; then echo "income_medians.csv identical to the reference  PASS"
  else echo "income_medians.csv differs from the reference  FAIL"; diff "$R/income_medians.csv" "$out/income_medians.csv" | head -12; fi; }
for st in $STAGES; do case $st in
  fe) run fe credit_risk.feature_engineering --data-dir legacy/data --output-dir $O/r1_fe --split-ids $SPLIT; judge 1 fe $R $O/r1_fe; medians 1 $O/r1_fe ;;
  train) run train credit_risk.train --input-dir $R --output-dir $O/r2_train; judge 2 train $R $O/r2_train ;;
  metrics) run metrics credit_risk.metrics_calculation --input-dir $R --output-dir $O/r3_metrics; judge 3 metrics $R $O/r3_metrics
     for s in a b c; do n=$((5 + $(printf '%d' "'$s") - 96)); run metrics_$s credit_risk.metrics_calculation --input-dir $J/scenarios/edge_metrics_$s --output-dir $O/r${n}_metrics_$s; judge $n metrics $R/scenarios/edge_metrics_$s $O/r${n}_metrics_$s; done ;;
  predict) run predict credit_risk.predict --input-dir $O/r2_train --data-dir legacy/data --income-medians $R/income_medians.csv --output-dir $O/r4_predict; judge 4 predict $R $O/r4_predict
     mkdir -p $O/edge_data && cp $J/scenarios/edge_predict/cs-test.csv $O/edge_data/
     run predict_edge credit_risk.predict --input-dir $O/r2_train --data-dir $O/edge_data --income-medians $R/scenarios/edge_predict/income_medians.csv --output-dir $O/r5_predict_edge; judge 5 predict $R/scenarios/edge_predict $O/r5_predict_edge ;;
  e2e) E=$O/r9_e2e; mkdir -p $E
     run e2e_fe credit_risk.feature_engineering --data-dir legacy/data --output-dir $E --split-ids $SPLIT
     run e2e_train credit_risk.train --input-dir $E --output-dir $E
     run e2e_metrics credit_risk.metrics_calculation --input-dir $E --output-dir $E
     run e2e_predict credit_risk.predict --input-dir $E --data-dir legacy/data --income-medians $E/income_medians.csv --output-dir $E
     judge 9 fe $R $E; medians 9 $E; judge 9 predict $R $E ;;
esac; done
