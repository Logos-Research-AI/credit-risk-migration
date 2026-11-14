/* x21: rules questioned by the reviewers of round 2.
   (A) what INPUT(strip(text), ?? best32.) returns for texts that are not [sign]digits[.digits];
   (B) the input check on a file whose headers have another capitalisation (AGE, monthlyincome);
   (C) the test-file check on a file holding the header line only;
   (D) %num on a column the file does not have;
   (E) a character VAR1 through the check and through `a.VAR1 as row_id`;
   (F) `if _n_ = 1 then set psi_cuts;` when psi_cuts has no row (training score table empty). */
%let x21_dir = %sysfunc(pathname(work));

/* ---------- (A) ---------- */
data work.x21_a;
    length txt $40;
    infile datalines truncover dsd dlm='|';
    input txt $char40.;
    v = ifn(lengthn(strip(txt)) <= 32, input(strip(txt), ?? best32.), .);
    put 'X21A [' txt $char20. '] ' v= best32. ' hex=' v hex16.;
    datalines;
5000
5000-1
5000+1
1+2
1-2
1e3
1E3
1d2
1D2
1e-2
1E+2
1e
1e+
e5
E
d
D
bad
undefined
abcde
NA
na
.
-
+
--5
+-5
-5
+5
- 5
+ 5
5-
5+
5.
.5
-.5
+.5
1.2.3
1 2
1 e5
1,000
$5
5%
0x10
1F
1.5e3
1.5-3
.5e1
5.e1
-1e2
1e400
1e-400
 12
0005
00.50
1..2
1.e
A
Z
._
.A
;
run;

/* ---------- the check of feature_engineering.sas 52-123 and predict.sas 60-130, on a named table,
   reporting instead of stopping ---------- */
%macro num(v);
    %local dsid pos vtype;
    %let vtype = ;
    %let dsid = %sysfunc(open(work.&x21_tab));
    %let pos = %sysfunc(varnum(&dsid, &v));
    %if &pos > 0 %then %let vtype = %sysfunc(vartype(&dsid, &pos));
    %let dsid = %sysfunc(close(&dsid));
    %if &vtype = N %then "&v"n;
    %else ifn(lengthn(strip("&v"n)) <= 32, input(strip("&v"n), ?? best32.), .);
%mend;

%macro check(tab, kind, label);
    %global x21_tab;
    %let x21_tab = &tab;
    %let columns_ok = 0;
    %let bad_rows = 1;
    %let duplicate_ids = 1;
    %let known_incomes = 0;
    proc sql noprint;
        select (count(*) = 12 and sum(upcase(name) in
                   ('VAR1', 'SERIOUSDLQIN2YRS', 'AGE', 'MONTHLYINCOME', 'NUMBEROFDEPENDENTS',
                    'REVOLVINGUTILIZATIONOFUNSECUREDL', 'DEBTRATIO',
                    'NUMBEROFTIME30-59DAYSPASTDUENOTW', 'NUMBEROFTIME60-89DAYSPASTDUENOTW',
                    'NUMBEROFTIMES90DAYSLATE', 'NUMBEROFOPENCREDITLINESANDLOANS',
                    'NUMBERREALESTATELOANSORLINES')) = 12)
        into :columns_ok trimmed
        from dictionary.columns
        where libname = 'WORK' and memname = "%upcase(&tab)";
    quit;
    data work.input_check;
        set work.&tab;
        %if &kind = train %then %do;
        bad_row = (missing(VAR1)
            or %num(SeriousDlqin2yrs) not in (0, 1)
        %end;
        %else %do;
        bad_row = (missing(VAR1)
            or (upcase(cats(SeriousDlqin2yrs)) not in ('', '.', 'NA') and
                %num(SeriousDlqin2yrs) not in (0, 1))
        %end;
            or missing(%num(age))
            or missing(%num(RevolvingUtilizationOfUnsecuredL))
            or missing(%num(DebtRatio))
            or missing(%num(NumberRealEstateLoansOrLines))
            or not (%num(NumberOfTime30-59DaysPastDueNotW) >= 0 and
                    %num(NumberOfTime30-59DaysPastDueNotW) = int(%num(NumberOfTime30-59DaysPastDueNotW)))
            or not (%num(NumberOfTime60-89DaysPastDueNotW) >= 0 and
                    %num(NumberOfTime60-89DaysPastDueNotW) = int(%num(NumberOfTime60-89DaysPastDueNotW)))
            or not (%num(NumberOfTimes90DaysLate) >= 0 and
                    %num(NumberOfTimes90DaysLate) = int(%num(NumberOfTimes90DaysLate)))
            or not (%num(NumberOfOpenCreditLinesAndLoans) >= 0 and
                    %num(NumberOfOpenCreditLinesAndLoans) = int(%num(NumberOfOpenCreditLinesAndLoans)))
            or (upcase(cats(MonthlyIncome)) not in ('', '.', 'NA') and missing(%num(MonthlyIncome)))
            or (not missing(%num(MonthlyIncome)) and %num(MonthlyIncome) < 0)
            or (upcase(cats(NumberOfDependents)) not in ('', '.', 'NA') and
                not (%num(NumberOfDependents) >= 0 and
                     %num(NumberOfDependents) = int(%num(NumberOfDependents)))));
        known_income = not missing(%num(MonthlyIncome));
        x21_age = %num(age);
        x21_income = %num(MonthlyIncome);
        put "X21 ROW &label " VAR1= bad_row= known_income= x21_age= x21_income=;
        keep VAR1 bad_row known_income;
    run;
    proc sql noprint;
        select coalesce(sum(bad_row), 0), count(*) - count(distinct VAR1), coalesce(sum(known_income), 0),
               count(*)
        into :bad_rows trimmed, :duplicate_ids trimmed, :known_incomes trimmed, :x21_n trimmed
        from work.input_check;
    quit;
    %put X21 CHECK &label kind=&kind rows=&x21_n columns_ok=&columns_ok bad_rows=&bad_rows duplicate_ids=&duplicate_ids known_incomes=&known_incomes;
%mend;

%macro imp(file, tab);
    proc import datafile="&x21_dir/&file" out=work.&tab dbms=csv replace;
        getnames=yes;
        guessingrows=max;
    run;
    proc contents data=work.&tab varnum; title "x21 &tab"; run;
%mend;

/* ---------- (B) other capitalisation ---------- */
data _null_;
    file "&x21_dir/x21_b.csv" lrecl=1000;
    put ',seriousdlqin2yrs,RevolvingUtilizationOfUnsecuredLines,AGE,NumberOfTime30-59DaysPastDueNotWorse,DEBTRATIO,monthlyincome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,numberofdependents';
    put '1,1,0.766,45,2,0.80,9120,13,0,6,0,2';
    put '2,0,0.957,40,0,0.12,NA,4,0,0,0,1';
    put '3,0,0.658,38,1,0.08,3042,2,1,0,0,NA';
run;
%imp(x21_b.csv, x21_b)
%check(x21_b, train, B_case)

/* ---------- (C) header only, test file ---------- */
data _null_;
    file "&x21_dir/x21_c.csv" lrecl=1000;
    put ',SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,age,NumberOfTime30-59DaysPastDueNotWorse,DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents';
run;
%imp(x21_c.csv, x21_c)
%check(x21_c, test, C_header_only_test)
%check(x21_c, train, C_header_only_train)
%put X21 C syserr=&syserr sqlobs=&sqlobs;

/* ---------- (D) a column the file does not have ---------- */
data _null_;
    file "&x21_dir/x21_d.csv" lrecl=1000;
    put ',SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,NumberOfTime30-59DaysPastDueNotWorse,DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents';
    put '1,1,0.766,2,0.80,9120,13,0,6,0,2';
    put '2,0,0.957,0,0.12,NA,4,0,0,0,1';
run;
%imp(x21_d.csv, x21_d)
%check(x21_d, test, D_no_age)

/* ---------- (E) character VAR1 ---------- */
data _null_;
    file "&x21_dir/x21_e.csv" lrecl=1000;
    put ',SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,age,NumberOfTime30-59DaysPastDueNotWorse,DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents';
    put 'A1,NA,0.766,45,2,0.80,9120,13,0,6,0,2';
    put 'A2,NA,0.957,40,0,0.12,NA,4,0,0,0,1';
    put 'A2,NA,0.957,40,0,0.12,NA,4,0,0,0,1';
    put ' ,NA,0.957,40,0,0.12,NA,4,0,0,0,1';
run;
%imp(x21_e.csv, x21_e)
%check(x21_e, test, E_char_id)
proc sql;
    create table work.x21_e_imputed as
    select a.VAR1 as row_id, a.age from work.x21_e a;
quit;
proc contents data=work.x21_e_imputed varnum; title "x21 e imputed"; run;
proc print data=work.x21_e_imputed; run;

/* ---------- (F) metrics_calculation.sas 278-359 with an empty training score table ---------- */
data work.logit_scored_train;
    length default_flag pd_logistic credit_risk_score 8;
    stop;
run;
data work.logit_scored_valid;
    do credit_risk_score = 600, 700, 800;
        default_flag = 0; pd_logistic = 0.1;
        output;
    end;
run;
proc sort data=work.logit_scored_train(keep=credit_risk_score)
          out=work.train_scores_sorted;
    by credit_risk_score;
run;

data work.psi_cuts;
    set work.train_scores_sorted nobs=n_train end=eof;
    array cut{9};
    retain cut1-cut9;
    do k = 1 to 9;
        if _n_ = ceil(k * n_train / 10) then cut{k} = credit_risk_score;
    end;
    if eof then output;
    keep cut1-cut9;
run;

data work.train_bins;
    if _n_ = 1 then set work.psi_cuts;
    set work.logit_scored_train;
    array cut{9};
    score_bin = 0;
    do k = 1 to 9;
        if credit_risk_score > cut{k} then score_bin = score_bin + 1;
    end;
    drop k cut1-cut9;
run;

data work.valid_bins;
    if _n_ = 1 then set work.psi_cuts;
    set work.logit_scored_valid;
    array cut{9};
    score_bin = 0;
    do k = 1 to 9;
        if credit_risk_score > cut{k} then score_bin = score_bin + 1;
    end;
    drop k cut1-cut9;
run;

data work.psi_bins;
    do score_bin = 0 to 9;
        output;
    end;
run;

%let psi_floor = unset;
proc sql noprint;
    select 0.5 / max(t.n, v.n) into :psi_floor trimmed
    from (select count(*) as n from work.train_bins) t,
         (select count(*) as n from work.valid_bins) v;
quit;
%put X21 F psi_floor=[&psi_floor];

proc sql;
    create table work.psi_calculation as
    select
        s.score_bin,
        coalesce(a.train_pct, 0) as train_pct,
        coalesce(b.valid_pct, 0) as valid_pct,
        (max(calculated train_pct, &psi_floor) - max(calculated valid_pct, &psi_floor))
            * log(max(calculated train_pct, &psi_floor) / max(calculated valid_pct, &psi_floor)) as psi_component
    from work.psi_bins s
    left join
        (select score_bin, count(*) / (select count(*) from work.train_bins) as train_pct
         from work.train_bins group by score_bin) a
    on s.score_bin = a.score_bin
    left join
        (select score_bin, count(*) / (select count(*) from work.valid_bins) as valid_pct
         from work.valid_bins group by score_bin) b
    on s.score_bin = b.score_bin
    order by s.score_bin;

    create table work.psi_summary as
    select sum(psi_component) as PSI format=best12.,
           case
              when calculated PSI < 0.1 then 'No significant change'
              when calculated PSI < 0.25 then 'Some change'
              else 'Significant change'
           end as PSI_interpretation
    from work.psi_calculation;
quit;
data _null_;
    do ds = 'PSI_CUTS', 'TRAIN_BINS', 'VALID_BINS', 'PSI_CALCULATION', 'PSI_SUMMARY';
        dsid = open(cats('work.', ds));
        n = attrn(dsid, 'nlobs');
        nv = attrn(dsid, 'nvars');
        rc = close(dsid);
        put 'X21 F ' ds= n= nv=;
    end;
run;
proc print data=work.psi_calculation; title "x21 F psi_calculation"; run;
proc print data=work.psi_summary; title "x21 F psi_summary"; run;
