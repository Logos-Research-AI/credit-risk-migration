# Bugfix row 4: PSI always 0 (flag `--fix-psi-bins`, off by default)

Site: `metrics_calculation.py` valid_bins; new helper `sas_compat.proc_rank_apply_groups` (training PROC RANK groups=10 group starts, validation rows go to the highest group whose start <= pd; below all -> 0). Marked `FIXED(post-parity, flag --fix-psi-bins)`.

## Flag off
`rm -rf out/off && migration/parity/run_contract.sh out/off`: all 10 lines PASS. Referee clean.

## Flag on
`python -m credit_risk.metrics_calculation --input-dir judge/reference --output-dir out/on/psi --fix-psi-bins`
- On this input only PSI-related cells change: `validation_summary.csv` PSI, `model_performance_metrics.csv` PSI, `printed_psi_calculation.csv` (10 rows: valid_pct, psi_component). Every other file is identical; PSI_interpretation and status stay "No significant change" / "Production Ready" (PSI is small because the split is random).
- CORRECTED 2026-11-12 (formal verification, R3): "only PSI cells change" holds for this input, not in general. `PSI_interpretation` and `status` are computed from PSI (`status` from AUC, KS and PSI), so the flag can change them too; what is proved is that the PSI cells, `PSI_interpretation` and `status` can change and every other cell is identical. Example: training pd 0.1, 0.2 and validation pd 0.8, 0.9 with default_flag 0, 1 (AUC 1, KS 1): flag off gives PSI 0 and "Production Ready"; flag on puts both validation rows in the upper training bin, PSI is above 0.25 and status is "Requires Review".
- PSI 0.0000 -> 0.0002. valid_pct per training decile: 0.1027, 0.0976, 0.1013, 0.0986, 0.0985, 0.0999, 0.0999, 0.1002, 0.0998, 0.1016 (train_pct stays 0.1).

## Fix-up (review)
- Rule: validation values below the training minimum go to the LOWEST TRAINING group present (open below), not literal group 0. A value in the gap between max(g) and min(g+1) goes to g (lower-bound rule).
- Under the flag the join is from the TRAINING bins (left). A training bin with no validation rows keeps valid_pct = 0 (printed as 0) and its log term uses both shares floored at 1e-4 (ln(train/0) is undefined), so a vanished bin raises PSI rather than being dropped. sum(valid_pct) == 1 is checked (ValueError otherwise).
- Flag-on runs, PSI before (flag off, SAS-faithful) -> after:

| input | PSI off | PSI on | interpretation on |
|---|---|---|---|
| judge/reference | 0.0000 | 0.0002 | No significant change |
| edge_metrics_a | 0.0906 | 0.0038 | No significant change |
| edge_metrics_b | 1.5743 | 0.0560 | No significant change |
| edge_metrics_c | 0.1790 | 0.0210 | No significant change |

edge_metrics_b training groups are {4, 8, 9} (ties); the pre-fixup commit gave 0.7552 because 1988 validation rows went to a bin 0 that training lacks. Status is unchanged in all four (on other inputs the flag can change it: see the correction above).
