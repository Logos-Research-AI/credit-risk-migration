R='/Users/cristophersalvi/GitHub/sas-migration/judge/reference/'
hdr=lambda f: open(R+f).readline().strip().split(',')
rs=hdr('risk_scores_train.csv')
keep_fmo="row_id default_flag pd_logistic credit_risk_score risk_grade recommendation interest_rate age monthly_income credit_utilization debt_ratio total_late_payments num_credit_lines".split()
pdv=[c for c in rs if c in set(keep_fmo)]
print('final_model_output PDV-filter == ref:', pdv==hdr('final_model_output.csv'), '; keep-list order == ref:', keep_fmo==hdr('final_model_output.csv'))
# predict PDV
imp="row_id age monthly_income MonthlyIncome_missing num_dependents Dependents_missing age_group num_late_30_59 num_late_60_89 num_late_90_plus credit_utilization debt_ratio num_credit_lines num_real_estate_loans".split()
feat="total_late_payments has_delinquency has_serious_delinquency credit_util_category debt_category income_per_dependent credit_lines_per_person age_category flag_high_utilization flag_very_high_utilization flag_high_debt_ratio flag_very_high_debt_ratio flag_recent_late_payments flag_serious_delinquency flag_multiple_delinquencies flag_low_income flag_many_dependents flag_few_credit_lines total_risk_flags financial_health log_monthly_income log_num_credit_lines log_total_late_payments age_income_interaction utilization_debt_interaction credit_utilization_capped debt_ratio_capped".split()
rest="pd_logistic pred_logistic base_score score_range credit_risk_score risk_grade recommendation base_rate interest_rate".split()
tp=imp+feat+rest
keep_tp="row_id pd_logistic pred_logistic credit_risk_score risk_grade recommendation interest_rate age monthly_income credit_utilization debt_ratio total_late_payments num_credit_lines financial_health total_risk_flags".split()
print('test_predictions PDV-filter == ref:', [c for c in tp if c in set(keep_tp)]==hdr('test_predictions.csv'), '; keep-list order == ref:', keep_tp==hdr('test_predictions.csv'))
print('kaggle:', [c for c in tp if c in {'row_id','pd_logistic'}]==hdr('kaggle_submission.csv'))
mf=hdr('model_features_validation.csv')
print('risk_scores_validation == features+rest:', mf+rest==hdr('risk_scores_validation.csv'), '; train same:', hdr('model_features_train.csv')+rest==rs)
print('ip_/xp_ prefixed cols:', [c for c in rs if c.lower().startswith(('ip_','xp_'))])
# metrics_x PDV: set cols, TP TN FP FN, threshold accuracy precision recall f1 specificity
m="default_flag predicted COUNT PERCENT TP TN FP FN threshold accuracy precision recall f1_score specificity".split()
k=set("threshold accuracy precision recall f1_score specificity".split())
print('threshold_analysis:', [c for c in m if c in k]==hdr('threshold_analysis.csv'))
# model_summary
roc="ROCModel Area StdErr LowerArea UpperArea SomersD Gamma TauA".split()
pdv=[('Train_AUC' if c=='Area' else c) for c in roc]
pdv+= ['Valid_AUC']
pdv+="train_precision train_recall train_f1_score train_accuracy valid_precision valid_recall valid_f1_score valid_accuracy model_name training_date training_records validation_records".split()
keep=set("model_name training_date training_records validation_records Train_AUC Valid_AUC train_precision train_recall train_f1_score train_accuracy valid_precision valid_recall valid_f1_score valid_accuracy".split())
print('model_summary:', [c for c in pdv if c in keep]==hdr('model_summary.csv'), hdr('printed_roc_train.csv'))
# model_performance_metrics
pdv="ROCModel AUC Gini KS_Statistic KS_Cutoff PSI PSI_interpretation threshold acc_50 prec_50 rec_50 f1_50 spec_50 model_name validation_date dataset".split()
ren=dict(acc_50='accuracy_at_50',prec_50='precision_at_50',rec_50='recall_at_50',f1_50='f1_score_at_50',spec_50='specificity_at_50')
out=[ren.get(c,c) for c in pdv if c not in ('threshold','ROCModel')]
print('model_performance_metrics:', out==hdr('model_performance_metrics.csv'))
print('validation_summary:', "ROCModel AUC Gini KS_Statistic KS_Cutoff PSI PSI_interpretation model status".split()==hdr('validation_summary.csv'))
