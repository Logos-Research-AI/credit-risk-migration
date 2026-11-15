Finding Q26 (round 4, ruling G45): a validation set with no defaulter.
Four validation rows, none a defaulter (the inputs of fix_Q23_nodefaulter). PROC RANK puts them
in deciles 3, 6, 6 and 9. decile_analysis.csv must have ten rows with capture rate 0 and lift 0
on every one, also on deciles 3, 6 and 9, which were 0/0 (missing) before the correction
(runs/ev5_fix_Q23_nodefaulter/decile_analysis.csv).
Run: metrics_calculation.sas with these stage inputs.
