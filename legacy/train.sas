/*****************************************************************************
 * Credit Risk Scoring Model - Model Training
 *
 * Purpose: Train logistic regression model for credit default prediction
 * Author: Risk Analytics Team
 * Date: 2025
 *
 * Data Source: Kaggle "Give Me Some Credit" competition
 *
 * This script:
 * - Trains logistic regression model with stepwise selection
 * - Generates predictions and probability scores
 * - Creates risk grades and recommendations
 * - Evaluates model performance
 * - Exports model results and coefficients
 *****************************************************************************/

/* Define output path */
%let output_path = /home/u64352077/output;

/*****************************************************************************
 * 1. Load Feature-Engineered Data
 *****************************************************************************/

/* Import training features */
proc import datafile="&output_path/model_features_train.csv"
    out=work.model_features_train
    dbms=csv
    replace;
    getnames=yes;
    guessingrows=max;
run;

/* Import validation features */
proc import datafile="&output_path/model_features_validation.csv"
    out=work.model_features_validation
    dbms=csv
    replace;
    getnames=yes;
    guessingrows=max;
run;

/*****************************************************************************
 * 2. Train Logistic Regression Model
 *****************************************************************************/

/* Train logistic regression with stepwise selection */
proc logistic data=work.model_features_train descending;
    model default_flag =
        /* Core risk metrics */
        credit_utilization_capped debt_ratio_capped

        /* Late payment indicators */
        num_late_30_59 num_late_60_89 num_late_90_plus
        total_late_payments has_delinquency has_serious_delinquency

        /* Financial metrics */
        age monthly_income log_monthly_income
        num_credit_lines num_real_estate_loans log_num_credit_lines
        num_dependents income_per_dependent credit_lines_per_person

        /* Risk flags */
        flag_high_utilization flag_very_high_utilization
        flag_high_debt_ratio flag_very_high_debt_ratio
        flag_recent_late_payments flag_serious_delinquency
        flag_multiple_delinquencies flag_low_income
        flag_many_dependents flag_few_credit_lines
        total_risk_flags

        /* Categorical indicators */
        credit_util_category debt_category age_category

        /* Composite scores */
        financial_health

        /* Interaction features */
        age_income_interaction utilization_debt_interaction

        /* Missing value flags */
        MonthlyIncome_missing Dependents_missing

    / selection=stepwise slentry=0.05 slstay=0.05
      ctable lackfit rsquare;

    /* Output predictions */
    output out=work.logit_scored_train
           predicted=pd_logistic;

    /* Store model for scoring */
    store work.logit_model;

    /* Output parameter estimates (coefficients) */
    ods output ParameterEstimates=work.model_coefficients;

    title "Logistic Regression Model - Credit Default Prediction";
run;

/*****************************************************************************
 * 3. Evaluate Model on Training Data
 *****************************************************************************/

/* Add binary prediction variable */
data work.logit_scored_train;
    set work.logit_scored_train;
    pred_logistic = (pd_logistic >= 0.5);
run;

/* Confusion matrix on training set */
proc freq data=work.logit_scored_train noprint;
    tables default_flag * pred_logistic / out=work.confusion_matrix_train;
run;

proc print data=work.confusion_matrix_train;
    title "Confusion Matrix - Training Set";
run;

/* Calculate precision, recall, and F1 score for training set */
data work.training_metrics;
    set work.confusion_matrix_train end=eof;
    retain TP TN FP FN 0;

    if default_flag = 1 and pred_logistic = 1 then TP = count;
    else if default_flag = 0 and pred_logistic = 0 then TN = count;
    else if default_flag = 0 and pred_logistic = 1 then FP = count;
    else if default_flag = 1 and pred_logistic = 0 then FN = count;

    if eof then do;
        if (TP + FP) > 0 then train_precision = TP / (TP + FP);
        else train_precision = .;
        if (TP + FN) > 0 then train_recall = TP / (TP + FN);
        else train_recall = .;
        if (train_precision + train_recall) > 0 then train_f1_score = 2 * (train_precision * train_recall) / (train_precision + train_recall);
        else train_f1_score = .;
        if (TP + TN + FP + FN) > 0 then train_accuracy = (TP + TN) / (TP + TN + FP + FN);
        else train_accuracy = .;
        output;
    end;
    keep train_precision train_recall train_f1_score train_accuracy;
run;

proc print data=work.training_metrics;
    title "Training Set - Performance Metrics";
    format train_precision train_recall train_f1_score train_accuracy 8.4;
run;

/*****************************************************************************
 * 4. Score Validation Set
 *****************************************************************************/

/* Score validation set with trained model */
proc plm restore=work.logit_model;
    score data=work.model_features_validation
          out=work.logit_scored_valid_temp
          predicted=predicted_logit;
run;

/* Convert logit to probability */
data work.logit_scored_valid;
    set work.logit_scored_valid_temp;

    /* Apply inverse logit (logistic) function */
    pd_logistic = 1 / (1 + exp(-predicted_logit));

    /* Add binary prediction */
    pred_logistic = (pd_logistic >= 0.5);

    drop predicted_logit;
run;

/* Confusion matrix on validation set */
proc freq data=work.logit_scored_valid noprint;
    tables default_flag * pred_logistic / out=work.confusion_matrix;
run;

proc print data=work.confusion_matrix;
    title "Confusion Matrix - Validation Set";
run;

/* Calculate precision, recall, and F1 score for validation set */
data work.validation_metrics;
    set work.confusion_matrix end=eof;
    retain TP TN FP FN 0;

    if default_flag = 1 and pred_logistic = 1 then TP = count;
    else if default_flag = 0 and pred_logistic = 0 then TN = count;
    else if default_flag = 0 and pred_logistic = 1 then FP = count;
    else if default_flag = 1 and pred_logistic = 0 then FN = count;

    if eof then do;
        if (TP + FP) > 0 then valid_precision = TP / (TP + FP);
        else valid_precision = .;
        if (TP + FN) > 0 then valid_recall = TP / (TP + FN);
        else valid_recall = .;
        if (valid_precision + valid_recall) > 0 then valid_f1_score = 2 * (valid_precision * valid_recall) / (valid_precision + valid_recall);
        else valid_f1_score = .;
        if (TP + TN + FP + FN) > 0 then valid_accuracy = (TP + TN) / (TP + TN + FP + FN);
        else valid_accuracy = .;
        output;
    end;
    keep valid_precision valid_recall valid_f1_score valid_accuracy;
run;

proc print data=work.validation_metrics;
    title "Validation Set - Performance Metrics";
    format valid_precision valid_recall valid_f1_score valid_accuracy 8.4;
run;

/*****************************************************************************
 * 5. Create Risk Scores and Grades
 *****************************************************************************/

/* Generate risk scores for training set */
data work.risk_scores_train;
    set work.logit_scored_train;

    /* Convert probability to credit risk score (300-850 scale like FICO) */
    base_score = 600;
    score_range = 250;
    credit_risk_score = base_score + score_range * (1 - pd_logistic);

    /* Assign risk grades based on score */
    if credit_risk_score >= 750 then risk_grade = 'A';
    else if credit_risk_score >= 700 then risk_grade = 'B';
    else if credit_risk_score >= 650 then risk_grade = 'C';
    else if credit_risk_score >= 600 then risk_grade = 'D';
    else if credit_risk_score >= 550 then risk_grade = 'E';
    else risk_grade = 'F';

    /* Recommended actions */
    if risk_grade in ('A', 'B') then recommendation = 'Approve';
    else if risk_grade = 'C' then recommendation = 'Review';
    else recommendation = 'Decline';

    /* Suggested interest rate (risk-based pricing) */
    base_rate = 0.05;
    if risk_grade = 'A' then interest_rate = base_rate;
    else if risk_grade = 'B' then interest_rate = base_rate + 0.02;
    else if risk_grade = 'C' then interest_rate = base_rate + 0.04;
    else if risk_grade = 'D' then interest_rate = base_rate + 0.07;
    else if risk_grade = 'E' then interest_rate = base_rate + 0.10;
    else interest_rate = base_rate + 0.15;

    format interest_rate percent8.2;
run;

/* Generate risk scores for validation set */
data work.risk_scores_validation;
    set work.logit_scored_valid;

    /* Same scoring logic as training */
    base_score = 600;
    score_range = 250;
    credit_risk_score = base_score + score_range * (1 - pd_logistic);

    if credit_risk_score >= 750 then risk_grade = 'A';
    else if credit_risk_score >= 700 then risk_grade = 'B';
    else if credit_risk_score >= 650 then risk_grade = 'C';
    else if credit_risk_score >= 600 then risk_grade = 'D';
    else if credit_risk_score >= 550 then risk_grade = 'E';
    else risk_grade = 'F';

    if risk_grade in ('A', 'B') then recommendation = 'Approve';
    else if risk_grade = 'C' then recommendation = 'Review';
    else recommendation = 'Decline';

    base_rate = 0.05;
    if risk_grade = 'A' then interest_rate = base_rate;
    else if risk_grade = 'B' then interest_rate = base_rate + 0.02;
    else if risk_grade = 'C' then interest_rate = base_rate + 0.04;
    else if risk_grade = 'D' then interest_rate = base_rate + 0.07;
    else if risk_grade = 'E' then interest_rate = base_rate + 0.10;
    else interest_rate = base_rate + 0.15;

    format interest_rate percent8.2;
run;

/* Risk grade distribution */
proc freq data=work.risk_scores_train;
    tables risk_grade * default_flag / nocol nopercent;
    title "Default Rate by Risk Grade - Training Set";
run;

proc freq data=work.risk_scores_validation;
    tables risk_grade * default_flag / nocol nopercent;
    title "Default Rate by Risk Grade - Validation Set";
run;

/*****************************************************************************
 * 6. ROC Curve and AUC
 *****************************************************************************/

/* ROC analysis for training set */
proc logistic data=work.risk_scores_train;
    model default_flag(event='1') = pd_logistic / nofit;
    roc 'Training Set' pred=pd_logistic;
    ods output ROCAssociation=work.roc_train;
    title "ROC Curve - Training Set";
run;

/* ROC analysis for validation set */
proc logistic data=work.risk_scores_validation;
    model default_flag(event='1') = pd_logistic / nofit;
    roc 'Validation Set' pred=pd_logistic;
    ods output ROCAssociation=work.roc_valid;
    title "ROC Curve - Validation Set";
run;

/* Display AUC */
proc print data=work.roc_train;
    where ROCModel = 'Training Set';
    var Area;
    title "Training Set AUC";
run;

proc print data=work.roc_valid;
    where ROCModel = 'Validation Set';
    var Area;
    title "Validation Set AUC";
run;

/*****************************************************************************
 * 7. Export Results
 *****************************************************************************/

/* Clean up training set - drop extra columns from PROC LOGISTIC */
data work.risk_scores_train_clean;
    set work.risk_scores_train;
    drop IP_: XP_: _FROM_ _INTO_ _LEVEL_;
run;

/* Clean up validation set - drop extra columns */
data work.risk_scores_validation_clean;
    set work.risk_scores_validation;
    drop IP_: XP_: _FROM_ _INTO_ _LEVEL_;
run;

/* Export scored training set */
proc export data=work.risk_scores_train_clean
    outfile="&output_path/risk_scores_train.csv"
    dbms=csv
    replace;
run;

/* Export scored validation set */
proc export data=work.risk_scores_validation_clean
    outfile="&output_path/risk_scores_validation.csv"
    dbms=csv
    replace;
run;

/* Create final model output for reporting */
data work.final_model_output;
    set work.risk_scores_train;
    keep row_id default_flag pd_logistic credit_risk_score
         risk_grade recommendation interest_rate
         age monthly_income credit_utilization debt_ratio
         total_late_payments num_credit_lines;
run;

proc export data=work.final_model_output
    outfile="&output_path/final_model_output.csv"
    dbms=csv
    replace;
run;

/* Export model performance summary */
data work.model_summary;
    merge work.roc_train(where=(ROCModel='Training Set') rename=(Area=Train_AUC))
          work.roc_valid(where=(ROCModel='Validation Set') rename=(Area=Valid_AUC))
          work.training_metrics
          work.validation_metrics;

    model_name = "Logistic Regression";
    training_date = today();
    training_records = 105000; /* Approximate 70% of 150K */
    validation_records = 45000; /* Approximate 30% of 150K */

    format training_date date9.
           Train_AUC Valid_AUC
           train_precision train_recall train_f1_score train_accuracy
           valid_precision valid_recall valid_f1_score valid_accuracy 8.4;
    keep model_name training_date training_records validation_records
         Train_AUC Valid_AUC
         train_precision train_recall train_f1_score train_accuracy
         valid_precision valid_recall valid_f1_score valid_accuracy;
run;

proc export data=work.model_summary
    outfile="&output_path/model_summary.csv"
    dbms=csv
    replace;
run;

/* Export model coefficients */
proc export data=work.model_coefficients
    outfile="&output_path/model_coefficients.csv"
    dbms=csv
    replace;
run;

%put NOTE: Model training completed successfully;
%put NOTE: Model stored as work.logit_model;
%put NOTE: Training set scored: &output_path/risk_scores_train.csv;
%put NOTE: Validation set scored: &output_path/risk_scores_validation.csv;
%put NOTE: Model summary: &output_path/model_summary.csv;
%put NOTE: Model coefficients: &output_path/model_coefficients.csv;
%put NOTE: Ready for validation metrics calculation;
