/*****************************************************************************
 * Credit Risk Scoring Model - Prediction on Test Set
 *
 * Purpose: Score Kaggle test set using trained model
 * Author: Risk Analytics Team
 * Date: 2025
 *
 * Data Source: Kaggle "Give Me Some Credit" competition test set
 *
 * This script:
 * - Loads cs-test.csv from data/ directory
 * - Applies same feature engineering as training
 * - Scores using trained logistic regression model
 * - Generates risk scores, grades, and recommendations
 * - Exports predictions for submission
 *****************************************************************************/

/* Define paths */
%let data_path = /home/u64352077;
%let output_path = /home/u64352077/output;

/*****************************************************************************
 * 1. Load Kaggle Test Data
 *****************************************************************************/

/* Import test data */
proc import datafile="&data_path/cs-test.csv"
    out=work.test_raw
    dbms=csv
    replace;
    getnames=yes;
    guessingrows=max;
run;

/* Check if import succeeded */
proc contents data=work.test_raw;
    title "Test Data - Column Check";
run;

/*****************************************************************************
 * 2. Data Cleaning and Missing Value Handling
 *****************************************************************************/

/* First convert MonthlyIncome to numeric if needed */
data work.test_raw_clean;
    set work.test_raw;

    /* Convert to numeric - input function handles character to numeric */
    MonthlyIncome_num = input(MonthlyIncome, best32.);
    NumberOfDependents_num = input(NumberOfDependents, best32.);

    /* Keep the numeric versions, drop character if they exist */
    drop MonthlyIncome NumberOfDependents;
    rename MonthlyIncome_num = MonthlyIncome
           NumberOfDependents_num = NumberOfDependents;
run;

/* Read the training income medians by age group (exported by feature_engineering.sas) */
proc import datafile="&output_path/income_medians.csv"
    out=work.train_income_medians
    dbms=csv
    replace;
    getnames=yes;
run;

data work.test_cleaned;
    set work.test_raw_clean;

    /* Create age group for income imputation */
    if age < 30 then age_group = 1;
    else if age < 40 then age_group = 2;
    else if age < 50 then age_group = 3;
    else if age < 60 then age_group = 4;
    else age_group = 5;

    /* Handle missing values - create flags */
    if missing(MonthlyIncome) then MonthlyIncome_missing = 1;
    else MonthlyIncome_missing = 0;

    if missing(NumberOfDependents) then do;
        NumberOfDependents = 0;
        Dependents_missing = 1;
    end;
    else Dependents_missing = 0;
run;

/* Merge and impute income - rename columns in SQL */
proc sql;
    create table work.test_imputed as
    select
        a.VAR1 as row_id,
        a.age,
        case when a.MonthlyIncome_missing = 1 then coalesce(b.median_income, b.overall_median_income)
             else a.MonthlyIncome
        end as monthly_income,
        a.MonthlyIncome_missing,
        a.NumberOfDependents as num_dependents,
        a.Dependents_missing,
        a.age_group,
        a."NumberOfTime30-59DaysPastDueNotW"n as num_late_30_59,
        a."NumberOfTime60-89DaysPastDueNotW"n as num_late_60_89,
        a.NumberOfTimes90DaysLate as num_late_90_plus,
        a.RevolvingUtilizationOfUnsecuredL * 100 as credit_utilization,
        a.DebtRatio * 100 as debt_ratio,
        a.NumberOfOpenCreditLinesAndLoans as num_credit_lines,
        a.NumberRealEstateLoansOrLines as num_real_estate_loans
    from work.test_cleaned a
    left join work.train_income_medians b
    on a.age_group = b.age_group;
quit;

/*****************************************************************************
 * 3. Feature Engineering (Same as Training)
 *****************************************************************************/

data work.test_features;
    set work.test_imputed;

    /* Total late payments across all categories */
    total_late_payments = sum(num_late_30_59, num_late_60_89, num_late_90_plus);

    /* Has any delinquency indicator */
    has_delinquency = (total_late_payments > 0);

    /* Has serious delinquency (90+ days) */
    has_serious_delinquency = (num_late_90_plus > 0);

    /* Credit utilization categories */
    if credit_utilization < 30 then credit_util_category = 1;
    else if credit_utilization < 50 then credit_util_category = 2;
    else if credit_utilization < 75 then credit_util_category = 3;
    else credit_util_category = 4;

    /* Debt ratio categories */
    if debt_ratio < 30 then debt_category = 1;
    else if debt_ratio < 43 then debt_category = 2;
    else if debt_ratio < 60 then debt_category = 3;
    else debt_category = 4;

    /* Income per dependent */
    if num_dependents > 0 then income_per_dependent = monthly_income / (num_dependents + 1);
    else income_per_dependent = monthly_income;

    /* Credit lines per person in household */
    credit_lines_per_person = num_credit_lines / (num_dependents + 1);

    /* Age categories */
    if age < 25 then age_category = 1;
    else if age < 35 then age_category = 2;
    else if age < 50 then age_category = 3;
    else if age < 65 then age_category = 4;
    else age_category = 5;

    /* Risk flags */
    flag_high_utilization = (credit_utilization > 75);
    flag_very_high_utilization = (credit_utilization > 100);
    flag_high_debt_ratio = (debt_ratio > 43);
    flag_very_high_debt_ratio = (debt_ratio > 60);
    flag_recent_late_payments = (num_late_30_59 > 0);
    flag_serious_delinquency = (num_late_90_plus > 0);
    flag_multiple_delinquencies = (total_late_payments >= 3);
    flag_low_income = (monthly_income < 2500);
    flag_many_dependents = (num_dependents >= 3);
    flag_few_credit_lines = (num_credit_lines <= 2);

    /* Total risk flags */
    total_risk_flags = sum(flag_high_utilization, flag_very_high_utilization,
                          flag_high_debt_ratio,
                          flag_serious_delinquency, flag_multiple_delinquencies,
                          flag_low_income, flag_many_dependents,
                          flag_few_credit_lines);

    /* Financial health score */
    financial_health = 100;
    if credit_utilization > 30 then financial_health = financial_health - 15;
    if credit_utilization > 75 then financial_health = financial_health - 15;
    if debt_ratio > 43 then financial_health = financial_health - 20;
    if has_delinquency then financial_health = financial_health - 20;
    if num_late_90_plus > 0 then financial_health = financial_health - 30;
    financial_health = max(0, financial_health);

    /* Log transformations */
    log_monthly_income = log(monthly_income + 1);
    log_num_credit_lines = log(num_credit_lines + 1);
    log_total_late_payments = log(total_late_payments + 1);

    /* Interaction features */
    if monthly_income > 0 then age_income_interaction = age * log(monthly_income);
    else age_income_interaction = age * log_monthly_income;
    utilization_debt_interaction = credit_utilization * debt_ratio;

    /* Cap extreme outliers */
    credit_utilization_capped = min(credit_utilization, 200);
    debt_ratio_capped = min(debt_ratio, 500);
run;

/*****************************************************************************
 * 4. Score Test Set Using Trained Model
 *****************************************************************************/

/* Score test set with trained model */
proc plm restore=work.logit_model;
    score data=work.test_features
          out=work.test_scored_temp
          predicted=predicted_logit;
run;

/* Convert logit to probability */
data work.test_scored;
    set work.test_scored_temp;

    /* Apply inverse logit function */
    pd_logistic = 1 / (1 + exp(-predicted_logit));

    drop predicted_logit;
run;

/*****************************************************************************
 * 5. Generate Risk Scores and Recommendations
 *****************************************************************************/

data work.test_predictions;
    set work.test_scored;

    /* Binary prediction at 0.5 threshold */
    pred_logistic = (pd_logistic >= 0.5);

    /* Convert probability to credit risk score (300-850 scale) */
    base_score = 600;
    score_range = 250;
    credit_risk_score = round(base_score + score_range * (1 - pd_logistic));

    /* Assign risk grades */
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

    /* Suggested interest rate */
    base_rate = 0.05;
    if risk_grade = 'A' then interest_rate = base_rate;
    else if risk_grade = 'B' then interest_rate = base_rate + 0.02;
    else if risk_grade = 'C' then interest_rate = base_rate + 0.04;
    else if risk_grade = 'D' then interest_rate = base_rate + 0.07;
    else if risk_grade = 'E' then interest_rate = base_rate + 0.10;
    else interest_rate = base_rate + 0.15;

    format interest_rate percent8.2;
run;

/*****************************************************************************
 * 6. Create Output Datasets
 *****************************************************************************/

/* Kaggle submission format (row_id, probability) */
data work.kaggle_submission;
    set work.test_predictions;
    keep row_id pd_logistic;
run;

/* Full predictions with all scores and recommendations */
data work.test_predictions_full;
    set work.test_predictions;
    keep row_id pd_logistic pred_logistic credit_risk_score risk_grade
         recommendation interest_rate age monthly_income
         credit_utilization debt_ratio total_late_payments
         num_credit_lines financial_health total_risk_flags;
run;

/*****************************************************************************
 * 7. Export Results
 *****************************************************************************/

/* Export Kaggle submission file */
proc export data=work.kaggle_submission
    outfile="&output_path/kaggle_submission.csv"
    dbms=csv
    replace;
run;

/* Export full predictions */
proc export data=work.test_predictions_full
    outfile="&output_path/test_predictions.csv"
    dbms=csv
    replace;
run;

/* Summary statistics */
proc freq data=work.test_predictions;
    tables risk_grade recommendation;
    title "Test Set - Risk Grade Distribution";
run;

proc means data=work.test_predictions n mean std min max;
    var pd_logistic credit_risk_score;
    title "Test Set - Prediction Summary";
run;

/* Print sample predictions */
proc print data=work.test_predictions_full(obs=20) noobs;
    var row_id pd_logistic pred_logistic credit_risk_score risk_grade recommendation;
    title "Sample Test Set Predictions";
run;

%put NOTE: Test set scoring completed successfully;
%put NOTE: Kaggle submission file: &output_path/kaggle_submission.csv;
%put NOTE: Full predictions: &output_path/test_predictions.csv;
%put NOTE: Total records scored: 101,503;
