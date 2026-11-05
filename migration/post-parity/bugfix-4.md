# Bugfix row 4: PSI always 0 (flag `--fix-psi-bins`, off by default)

Site: `metrics_calculation.py` valid_bins; new helper `sas_compat.proc_rank_apply_groups` (training PROC RANK groups=10 group starts, validation rows go to the highest group whose start <= pd; below all -> 0). Marked `FIXED(post-parity, flag --fix-psi-bins)`.

## Flag off
`rm -rf out/off && migration/parity/run_contract.sh out/off`: all 10 lines PASS. Referee clean.

## Flag on
`python -m credit_risk.metrics_calculation --input-dir judge/reference --output-dir out/on/psi --fix-psi-bins`
- Only PSI-related cells change: `validation_summary.csv` PSI, `model_performance_metrics.csv` PSI, `printed_psi_calculation.csv` (10 rows: valid_pct, psi_component). Every other file is identical; PSI_interpretation and status stay "No significant change" / "Production Ready" (PSI is small because the split is random).
- PSI 0.0000 -> 0.0002. valid_pct per training decile: 0.1027, 0.0976, 0.1013, 0.0986, 0.0985, 0.0999, 0.0999, 0.1002, 0.0998, 0.1016 (train_pct stays 0.1).
