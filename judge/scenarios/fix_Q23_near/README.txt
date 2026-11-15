Finding Q23 (round 3, ruling G40): validation probabilities closer than 1e-8 but different.
Defaulters 0.300000000005 and 0.5000000000001; non-defaulters 0.300000000001, 0.300000000005, 0.1, 0.5.
Of the 8 defaulter/non-defaulter pairs 6 are concordant, 1 is exactly tied, 1 is discordant:
exact AUC = 6.5 / 8 = 0.8125, Gini 0.625. PROC LOGISTIC's ROC statement groups the near-equal
values and reports 5.5 / 8 = 0.6875 (printed_roc_metrics.csv keeps that printed value).
Run: metrics_calculation.sas with these stage inputs.
