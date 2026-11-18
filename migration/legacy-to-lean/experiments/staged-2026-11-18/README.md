# SAS runs staged for the SAS translators (2026-11-18)

Copied by the lead from the judge's SAS runs (SAS outputs and logs only; nothing of the port).

- `x27_C60_full`, `x27_E60_full`: the whole SAS program on a valid input whose training part has
  one outcome (every default_flag 0). Train fits nothing and runs on; metrics on a header-only
  validation score file; predict stops.
- `oneclass_n60_all1`: the same with every training outcome 1.
- `emptyval_n3_both`: three training rows with both outcomes and an empty validation part (G57;
  for contrast).
- `x22_A`, `x22_B`, `x22_C` and `x22_sas_results.json`: experiment X22, train.sas with the MODEL
  statement fixed to a design's variables (no selection) where a final parameter is left out of a
  singular information matrix (A: one event flagged; B: a linearly dependent column; C: a flag
  whose row has weight 0 at the last iteration); then metrics_calculation.sas and predict.sas.
