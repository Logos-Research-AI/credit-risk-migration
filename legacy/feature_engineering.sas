/*****************************************************************************
 * Credit Risk Scoring Model - Feature Engineering
 *
 * Purpose: Load Kaggle "Give Me Some Credit" data and create features
 * Author: Risk Analytics Team
 * Date: 2025
 *
 * Data Source: Kaggle "Give Me Some Credit" competition
 * https://www.kaggle.com/c/GiveMeSomeCredit
 *
 * This script:
 * - Loads cs-training.csv from data/ directory
 * - Handles missing values
 * - Creates derived features and risk indicators
 * - Splits into training (70%) and validation (30%) sets
 * - Exports engineered features for modeling
 *****************************************************************************/

/* Define base paths */
%let data_path = /home/u64352077;
%let output_path = /home/u64352077/output;

/*****************************************************************************
 * 1. Load Kaggle Training Data
 *****************************************************************************/

/* Import Kaggle training data */
proc import datafile="&data_path/cs-training.csv"
    out=work.credit_raw
    dbms=csv
    replace;
    getnames=yes;
run;

/* Display basic statistics */
proc means data=work.credit_raw n nmiss mean std min max;
    title "Raw Data Summary - Kaggle Give Me Some Credit";
run;

/*****************************************************************************
 * 2. Data Cleaning and Missing Value Handling
 *****************************************************************************/

/* First convert MonthlyIncome to numeric if needed */
data work.credit_raw_clean;
    set work.credit_raw;

    /* Convert to numeric - input function handles character to numeric */
    MonthlyIncome_num = input(MonthlyIncome, best32.);
    NumberOfDependents_num = input(NumberOfDependents, best32.);

    /* Keep the numeric versions, drop character if they exist */
    drop MonthlyIncome NumberOfDependents;
    rename MonthlyIncome_num = MonthlyIncome
           NumberOfDependents_num = NumberOfDependents;
run;

/* Calculate income medians by age group for imputation */
proc sql;
    create table work.income_medians as
    select
        case
            when age < 30 then 1
            when age < 40 then 2
            when age < 50 then 3
            when age < 60 then 4
            else 5
        end as age_group,
        median(MonthlyIncome) as median_income
    from work.credit_raw_clean
    where MonthlyIncome is not missing
    group by calculated age_group;
quit;

/* One row per age group, with the median of all known incomes:
   the fallback for an age group that has no known income */
data work.age_groups;
    do age_group = 1 to 5;
        output;
    end;
run;

proc sql;
    create table work.income_medians_all as
    select
        g.age_group,
        m.median_income,
        (select median(MonthlyIncome) from work.credit_raw_clean
         where MonthlyIncome is not missing) as overall_median_income
    from work.age_groups g
    left join work.income_medians m
    on g.age_group = m.age_group
    order by g.age_group;
quit;

data work.credit_cleaned;
    set work.credit_raw_clean;

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
    create table work.credit_imputed as
    select
        a.VAR1 as row_id,
        a.SeriousDlqin2yrs as default_flag,
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
    from work.credit_cleaned a
    left join work.income_medians_all b
    on a.age_group = b.age_group;
quit;

/*****************************************************************************
 * 3. Feature Engineering
 *****************************************************************************/

data work.credit_features;
    set work.credit_imputed;

    /* Total late payments across all categories */
    total_late_payments = sum(num_late_30_59, num_late_60_89, num_late_90_plus);

    /* Has any delinquency indicator */
    has_delinquency = (total_late_payments > 0);

    /* Has serious delinquency (90+ days) */
    has_serious_delinquency = (num_late_90_plus > 0);

    /* Credit utilization categories */
    if credit_utilization < 30 then credit_util_category = 1; /* Low */
    else if credit_utilization < 50 then credit_util_category = 2; /* Medium */
    else if credit_utilization < 75 then credit_util_category = 3; /* High */
    else credit_util_category = 4; /* Very High */

    /* Debt ratio categories */
    if debt_ratio < 30 then debt_category = 1; /* Low */
    else if debt_ratio < 43 then debt_category = 2; /* Medium */
    else if debt_ratio < 60 then debt_category = 3; /* High */
    else debt_category = 4; /* Very High */

    /* Income per dependent (handle division by zero) */
    if num_dependents > 0 then income_per_dependent = monthly_income / (num_dependents + 1);
    else income_per_dependent = monthly_income;

    /* Credit lines per person in household */
    credit_lines_per_person = num_credit_lines / (num_dependents + 1);

    /* Age categories for risk assessment */
    if age < 25 then age_category = 1; /* Young */
    else if age < 35 then age_category = 2; /* Young Adult */
    else if age < 50 then age_category = 3; /* Middle Age */
    else if age < 65 then age_category = 4; /* Mature */
    else age_category = 5; /* Senior */

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

    /* Financial health score (0-100) */
    financial_health = 100;
    if credit_utilization > 30 then financial_health = financial_health - 15;
    if credit_utilization > 75 then financial_health = financial_health - 15;
    if debt_ratio > 43 then financial_health = financial_health - 20;
    if has_delinquency then financial_health = financial_health - 20;
    if num_late_90_plus > 0 then financial_health = financial_health - 30;
    financial_health = max(0, financial_health);

    /* Log transformations for skewed variables (add 1 to handle zeros) */
    log_monthly_income = log(monthly_income + 1);
    log_num_credit_lines = log(num_credit_lines + 1);
    log_total_late_payments = log(total_late_payments + 1);

    /* Interaction features */
    age_income_interaction = age * log_monthly_income;
    utilization_debt_interaction = credit_utilization * debt_ratio / 100;

    /* Cap extreme outliers in credit_utilization and debt_ratio */
    credit_utilization_capped = min(credit_utilization, 200);
    debt_ratio_capped = min(debt_ratio, 500);
run;

/*****************************************************************************
 * 4. Split into Training and Validation Sets (70/30)
 *****************************************************************************/

/* Set random seed for reproducibility */
proc surveyselect data=work.credit_features
                  out=work.credit_split
                  samprate=0.7
                  seed=42
                  outall;
run;

data work.credit_train work.credit_validation;
    set work.credit_split;
    if selected = 1 then output work.credit_train;
    else output work.credit_validation;
    drop selected;
run;

/*****************************************************************************
 * 5. Summary Statistics
 *****************************************************************************/

proc means data=work.credit_train n mean std min max;
    var age monthly_income credit_utilization debt_ratio total_late_payments
        num_credit_lines num_real_estate_loans default_flag;
    title "Training Set Summary Statistics";
run;

proc freq data=work.credit_train;
    tables default_flag;
    title "Training Set - Default Rate";
run;

proc means data=work.credit_validation n mean std min max;
    var age monthly_income credit_utilization debt_ratio total_late_payments
        num_credit_lines num_real_estate_loans default_flag;
    title "Validation Set Summary Statistics";
run;

proc freq data=work.credit_validation;
    tables default_flag;
    title "Validation Set - Default Rate";
run;

/*****************************************************************************
 * 6. Export Engineered Features
 *****************************************************************************/

/* Ensure all variables are numeric before export */
data work.credit_train_export;
    set work.credit_train;
    /* Force numeric format for all variables */
    format _numeric_ best12.;
run;

data work.credit_validation_export;
    set work.credit_validation;
    /* Force numeric format for all variables */
    format _numeric_ best12.;
run;

/* Export training set */
proc export data=work.credit_train_export
    outfile="&output_path/model_features_train.csv"
    dbms=csv
    replace;
run;

/* Export validation set */
proc export data=work.credit_validation_export
    outfile="&output_path/model_features_validation.csv"
    dbms=csv
    replace;
run;

%put NOTE: Feature engineering completed successfully;
%put NOTE: Training set: exported to &output_path/model_features_train.csv;
%put NOTE: Validation set: exported to &output_path/model_features_validation.csv;
%put NOTE: Missing value imputation completed;
%put NOTE: Ready for model training;
