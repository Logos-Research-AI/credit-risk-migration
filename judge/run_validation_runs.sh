#!/usr/bin/env bash
# Runs every SAS run the judge validation needs (prompt 00b step 3). Each run-id is
# skipped if its folder already exists, so this is resumable: rerun after a failure.
# Usage (from judge/): ./run_validation_runs.sh [A|B]   (two queues, safe to run in parallel)
set -u
cd "$(dirname "$0")"
run() {  # run-id, then run_sas.py args
  local id=$1; shift
  if [ -d "runs/$id" ]; then echo "skip $id (exists)"; return; fi
  uv run python run_sas.py --run-id "$id" "$@" 2>&1 | grep -E '^(feature|train|metrics|predict|\{)|Error|Traceback' | sed "s/^/[$id] /"
}
M=metrics_calculation.sas
queue_a() {
  run ref_edge_predict --data-dir scenarios/edge_predict
  run ref_edge_metrics_a --scripts $M --stage-inputs scenarios/edge_metrics_a
  run ref_edge_metrics_b --scripts $M --stage-inputs scenarios/edge_metrics_b
  run ref_edge_metrics_c --scripts $M --stage-inputs scenarios/edge_metrics_c
  run ref_real_metrics --scripts $M --stage-inputs scenarios/real_metrics
  run m_metrics_decile_groups --mutation metrics_decile_groups --scripts $M --stage-inputs scenarios/real_metrics
  run m_metrics_threshold --mutation metrics_threshold --scripts $M --stage-inputs scenarios/real_metrics
  run m_metrics_status_threshold --mutation metrics_status_threshold --scripts $M --stage-inputs scenarios/edge_metrics_c
  run m_metrics_rank_ties --mutation metrics_rank_ties --scripts $M --stage-inputs scenarios/edge_metrics_a
  run m_metrics_psi_sign --mutation metrics_psi_sign --scripts $M --stage-inputs scenarios/edge_metrics_b
  run m_predict_rate_f --mutation predict_rate_f --data-dir scenarios/edge_predict
  run m_predict_null_compare_false --mutation predict_null_compare_false --data-dir scenarios/edge_predict
  for m in fe_health_penalty fe_impute_mean train_slentry train_slstay; do run "m_$m" --mutation "$m"; done
}
queue_b() {
  for m in train_grade_cutoff train_round_floor train_rate_format \
           predict_no_dep_impute fe_import_guessingrows fe_median_group_misaligned fe_low_income_boundary \
           predict_grade_b_boundary; do run "m_$m" --mutation "$m"; done
}
case "${1:-A}" in A) queue_a ;; B) queue_b ;; *) echo "usage: $0 [A|B]"; exit 2 ;; esac
