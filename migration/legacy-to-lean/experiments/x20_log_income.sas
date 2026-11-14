/* x20: the corrected log and interaction statements of feature_engineering.sas / predict.sas
   (copied verbatim) on incomes at and below -1, between -1 and 0, at 0 and above. */
data work.x20;
    age = 40;
    do monthly_income = -7.5, -1, -0.5, 0, 5000;
    if monthly_income > -1 then log_monthly_income = log(monthly_income + 1);
    else log_monthly_income = 0;
    if monthly_income > 0 then age_income_interaction = age * log(monthly_income);
    else age_income_interaction = age * log_monthly_income;
        put 'X20 ' monthly_income= log_monthly_income= age_income_interaction=;
        output;
    end;
run;
