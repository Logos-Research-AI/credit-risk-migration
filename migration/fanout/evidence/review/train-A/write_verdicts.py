rows = [l.rstrip('\n').split('\t') for l in open('migration/fanout/review-batch.train.tsv')][1:]
C = 'CONFIRMED'; E = 'EVIDENCE_DEFECT'; RC = 'RULEBOOK_CONFLICT'
V = {
1: (C, 'train.sas:19', 'Lines :19,:26,:35,:339-396 exports and %put :403-406 checked; input/output split matches RULEBOOK §4 and judge contract run 2.'),
2: (C, 'judge/reference/model_features_train.csv (all cells)', 'Recounted: 4 model_features files (reference + edge_predict) have 0 empty and 0 non-numeric cells, 9/4 E-notation cells, default_flag in {0,1}; log has 84 best32. informats.'),
3: (C, 'judge/reference/model_coefficients.csv', 'Own numpy Newton refit of the step-24 model plus the row\'s D8. rule: every Variable/DF/ProbChiSq/_ESTTYPE_ cell and the E/fixed choice and decimals of all 38 Estimate/StdErr cells text-identical; 3 Estimate and 1 StdErr differ by 1 du; compare.py --mode port PASS.'),
4: (E, 'judge/reference/listings/train.sas.lst:1193', 'Formula confirmed: own pstar (one-step LOO) ctable is identical to printed_classification.csv on all 45 rows (>= and > agree; pd instead of pstar: 41 rows differ); converged pd PASSES the judge. Minor: the cited listing range 1143-1192 stops one line short of the 0.880 row (lst:1193) that shows the missing Pos Pred the row describes; fix to lst:1143-1193.'),
5: (C, 'judge/reference/printed_fit_statistics.csv', 'Own rebuild of all 24 fits: labels, Equals and all 73 InterceptOnly cells (rounded to integers) text-identical; 5 InterceptAndCovariates cells differ by 0.001 (max rel 2.6e-8); compare.py PASS.'),
6: (C, 'judge/reference/printed_global_tests.csv', 'Own rebuild: Score at the intercept-only fit matches all 24 cells exactly; LR within 0.0002; Wald max 0.534 at step 1 (5.4e-5 rel); DF and ProbChiSq identical; compare.py PASS.'),
7: (RC, 'judge/compare.py ABS_COL_TOL (printed_hl_partition.csv, Total) = 0.0', 'Rule confirmed independently: anchored 1e-6 blocks plus block-min expected gives byte-identical partitions and chi-squares on judge/reference and all 17 judge/runs/*. But RULEBOOK §2 "model fitting ... full convergence" yields pd that moves 6 of 10 Totals by 1 (own refit and judge/fixtures/converged), and the judge requires exact Totals. The rulebook claim that the judge accepts a converged fit is false for this file. Fix in rulebook/judge: Total +-1 or a GCONV=1e-8 stopping rule (the row\'s open question).'),
8: (C, 'judge/reference/printed_hosmer_lemeshow.csv', 'Own HL on SAS pd: 121.9130, DF 8, <.0001, 10 groups exact; own-pd expected gives 121.9217 (refuted alternative reproduced); own converged pd 121.8389 passes compare.py.'),
9: (C, 'judge/reference/printed_odds_ratios.csv', 'Own exp(b), Wald limits with z=1.959964: 71/72 cells identical, has_delinquency UpperCL 3.749 vs 3.750 (1 du); compare.py PASS.'),
10: (C, 'judge/reference/printed_rsquare.csv', 'Own Cox-Snell and max-rescaled R2 from the per-step fits: 168/168 cells text-identical.'),
11: (C, 'judge/reference/stepwise_summary.csv', 'Own rebuild along the reference path (score at previous fit, Wald for removals): effects, DF, NumberInModel, every _ and ProbChiSq identical; 14 Score cells and 1 Wald cell differ within 5.2e-5 / 2.6e-4 rel; compare.py PASS.'),
12: (C, 'judge/reference/printed_confusion_train.csv', 'Recomputed from reference pd: 96957/1035/5590/1418, PERCENT 100*COUNT/N after aggregation matches; export code at log:2093-2111 is best12. for all four columns.'),
13: (C, 'train.sas:118-139', 'Recomputed TP=1418 TN=96957 FP=1035 FN=5590 and 0.5781/0.2023/0.2998/0.9369. Column order and absent-cell-stays-0 hold (edge_metrics_a threshold_analysis 0.7: empty precision). Note: its scalar f1 form differs from the helper form of the f1 row (S113).'),
14: (C, 'train.sas:122-125', 'default_flag is never missing and only 0/1 (data/cs-training.csv 139974/10026; feature_engineering.sas:101); pred_logistic is a flag; plain == is right; counts reproduce both confusion files.'),
15: (C, 'train.sas:127', 'END= flag is never missing; the confusion table is never empty on train inputs; one output row.'),
16: (C, 'train.sas:128', 'TP/FP never missing, so a plain comparison is right; guard true on the reference (TP+FP 2453/1065).'),
17: (C, 'train.sas:128-129', 'Guarded division needs no div helper; values reproduce model_summary.csv.'),
18: (C, 'train.sas:130', 'Plain comparison on never-missing counts; TP+FN 7008/3018.'),
19: (C, 'train.sas:130-131', 'Recomputed 0.2023 from reference counts.'),
20: (C, 'train.sas:132', 'Operands can be missing when their guards fail, so the helper is correct under A2; the edge_metrics_a 0.5/0.7 rows show f1 empty for p=r=0 and for missing precision.'),
21: (E, 'train.sas:132', 'The value is right, but the row is classified MISSING_NULLABLE and translates with a Python None/plain > check instead of sas_compat.gt, which A2 makes mandatory. That contradicts the f1 row for the same statement (S113: sas_compat.gt(p + r, 0) in a with_columns), so an implementer has to choose a form. Fix: use the S113 form, or state that the scalar path is sanctioned.'),
22: (C, 'train.sas:134', 'Counts sum to 105000/45000; guard can only fail on an empty set, which outputs no row.'),
23: (C, 'train.sas:134-135', 'Recomputed 0.9369.'),
24: (C, 'train.sas:141-144', 'PROC-step FORMAT is temporary; metrics_calculation threshold_analysis.csv stays BEST12 after its print-step 8.4.'),
25: (C, 'train.sas:151-155', 'Validation features never missing (0 empty in both reference and edge_predict files); eta from the stored model.'),
26: (C, 'judge/reference/risk_scores_validation.csv pd_logistic', 'pd range 0.00039..0.8722 gives logit range [-7.85, 1.92]; no overflow and no missing.'),
27: (C, 'judge/reference/risk_scores_validation.csv header', 'Header equals the risk_scores_train header (51 columns); predicted_logit is not present.'),
28: (C, 'judge/reference/printed_confusion_validation.csv', 'Recomputed 41523/459/2412/606, PERCENT 92.273333333 etc.; identical in edge_predict.'),
29: (C, 'train.sas:180-201', 'Recomputed TP=606 TN=41523 FP=459 FN=2412 and 0.5690/0.2008/0.2968/0.9362.'),
30: (C, 'train.sas:190-191', 'Recomputed 0.5690; divisor never missing.'),
31: (C, 'train.sas:192-193', 'Recomputed 0.2008.'),
32: (E, 'train.sas:194', 'Same defect as train_f1_score (S114): MISSING_NULLABLE but a scalar None/plain > check instead of the A2-mandated sas_compat.gt, contradicting the valid_f1 row for S142. Fix: use the S142 helper form.'),
33: (C, 'train.sas:196-197', 'Recomputed 0.9362.'),
34: (C, 'train.sas:203-206', 'Print-step format is temporary; model_summary 8.4 comes from :378-381.'),
35: (C, 'judge/reference/risk_scores_train.csv recommendation', 'The polars chain reproduces recommendation on all train and validation rows; values have no trailing blanks; grades A-D only.'),
36: (E, 'judge/reference/risk_scores_train.csv interest_rate', 'The translation is right, but the evidence claims 0.05+0.02 = 0.07000000000000001. In IEEE 0.05+0.02 == 0.07 exactly. The inexact sums are 0.05+0.07 = 0.12000000000000001 and 0.05+0.10 = 0.15000000000000002, as the interest_rate NO_GAP row says. Fix the example.'),
37: (C, 'judge/reference/risk_scores_train.csv interest_rate', 'Counts 101160/2576/1225/39 (train) and 43331/1129/523/17 (validation) per grade reproduced; IEEE sums verified (0.07, 0.09, 0.12000000000000001, 0.15000000000000002, 0.2).'),
38: (E, 'judge/reference/listings/train.sas.log:636-639', 'The output is right, but the claim that the drop names match no column and the warnings "prove the drop removes nothing" is false for train. That step warns only for IP_:, XP_:, _FROM_ and _INTO_, so SAS did drop _LEVEL_ (from OUTPUT OUT=). Fix: say the drop removes _LEVEL_, which the port never creates, as the drop row (S199) states.'),
39: (C, 'judge/reference/listings/train.sas.log:645-650', 'The validation step warns for all 5 names, so the drop matches nothing; 51 columns, 4 E-notation cells, 0 empty.'),
40: (C, 'train.sas:278-286', 'PROC FREQ without out= and PROC PRINT are listing-only.'),
41: (C, 'judge/reference/printed_roc_train.csv', 'Own sort/searchsorted Mann-Whitney + DeLong (fuzz 1e-8): C=590050824 D=96676837 T=275, row byte-identical; converged pd also passes compare.py.'),
42: (C, 'judge/reference/printed_roc_validation.csv', 'Own recompute: C=108510073 D=18191553 T=50, row byte-identical; converged pd passes.'),
43: (C, 'train.sas:309-319', 'Listing-only where clauses; the merge where= (S205) is ported elsewhere.'),
44: (C, 'judge/reference/listings/train.sas.log:636-650', 'Correct reading of the warnings (train lacks the _LEVEL_ warning); identity plus a strict=False guard is right.'),
45: (C, 'judge/reference/final_model_output.csv:1', 'Header is the PDV order, not the keep-list order.'),
46: (C, 'judge/reference/listings/train.sas.log:1204-1208', 'percent8.2 on interest_rate, best12. elsewhere; 105000 records.'),
47: (C, 'judge/reference/model_summary.csv:1', 'Header order confirmed; polars 2.1.0 raises ShapeError for how=horizontal with unequal heights and pads with how=horizontal_extend (tested).'),
48: (C, 'train.sas:374,378', 'Matches the RULEBOOK today()/date9. row.'),
49: (C, 'judge/reference/listings/train.sas.log:1310-1323', 'Export formats 8.4/$19./date9./best12. and column order confirmed; values reproduced.'),
50: (C, 'judge/reference/listings/train.sas.log:1389-1395', 'Export applies $20., 2., d8., d8., 10.4, pvalue6.4, $4.; 19 records.'),
}
assert len(V) == len(rows) == 50
with open('migration/fanout/review.train-A.tsv', 'w') as f:
    f.write('file\tsymbol\tsource_construct\tverdict\tcited_line\treason\n')
    for i, r in enumerate(rows, 1):
        v, c, why = V[i]
        assert '\t' not in why and '\n' not in why
        f.write('\t'.join([r[0], r[1], r[2], v, c, why]) + '\n')
from collections import Counter; print(Counter(v[0] for v in V.values()))
