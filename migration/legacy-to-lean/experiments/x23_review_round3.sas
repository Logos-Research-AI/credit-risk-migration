/* x23: rules questioned by the reviewers of round 3 (second update).
   (G) the check steps of feature_engineering.sas 81-114 and predict.sas 88-121 on a table that
       has no VAR1 column: which variables does work.input_check have, in which order, and what
       are the totals;
   (H) COUNT(DISTINCT VAR1) on a character id column whose texts read as numbers:
       '7', '07', '7.0', '+7', a value with a leading blank, values of different stored padding;
   (I) what PROC IMPORT stores for id texts with leading or trailing blanks in the CSV;
   (J) a CSV whose id texts all read as numbers: is the column character or numeric. */
%let x23_dir = %sysfunc(pathname(work));
options validvarname=any;

%macro num(v);
    %local dsid pos vtype;
    %let vtype = ;
    %let dsid = %sysfunc(open(work.&x23_tab));
    %let pos = %sysfunc(varnum(&dsid, &v));
    %if &pos > 0 %then %let vtype = %sysfunc(vartype(&dsid, &pos));
    %let dsid = %sysfunc(close(&dsid));
    %if &vtype = N %then "&v"n;
    %else ifn(lengthn(strip("&v"n)) <= 32, input(strip("&v"n), ?? best32.), .);
%mend;

%macro check(tab, kind, label);
    %global x23_tab;
    %let x23_tab = &tab;
    %let bad_rows = 1;
    %let duplicate_ids = 1;
    %let known_incomes = 0;
    data work.input_check;
        set work.&tab;
        %if &kind = train %then %do;
        bad_row = (missing(%num(VAR1))
            or %num(SeriousDlqin2yrs) not in (0, 1)
        %end;
        %else %do;
        bad_row = (missing(%num(VAR1))
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
        %if &kind = train %then %do;
        known_income = not missing(%num(MonthlyIncome));
        keep VAR1 bad_row known_income;
        %end;
        %else %do;
        keep VAR1 bad_row;
        %end;
    run;
    proc contents data=work.input_check varnum; title "x23 input_check &label"; run;
    proc print data=work.input_check; title "x23 input_check &label"; run;
    data _null_;
        set work.input_check;
        length x23_t $1;
        x23_t = vtype(VAR1);
        x23_l = vlength(VAR1);
        put "X23 ROW &label " _n_= x23_t= x23_l= bad_row= 'VAR1=[' VAR1 +(-1) ']';
    run;
    proc sql noprint;
        select coalesce(sum(bad_row), 0), count(*) - count(distinct VAR1), count(*), count(distinct VAR1)
        into :bad_rows trimmed, :duplicate_ids trimmed, :x23_n trimmed, :x23_d trimmed
        from work.input_check;
    quit;
    %put X23 CHECK &label kind=&kind rows=&x23_n distinct=&x23_d bad_rows=&bad_rows duplicate_ids=&duplicate_ids;
%mend;

/* ---------- (G) no VAR1 column ---------- */
data _null_;
    file "&x23_dir/x23_g.csv" lrecl=1000;
    put 'SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,age,NumberOfTime30-59DaysPastDueNotWorse,DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents';
    put '0,0.766,45,2,0.80,9120,13,0,6,0,2';
    put '0,0.957,40,0,0.12,2600,4,0,0,0,1';
run;
proc import datafile="&x23_dir/x23_g.csv" out=work.x23_g dbms=csv replace;
    getnames=yes;
    guessingrows=max;
run;
proc contents data=work.x23_g varnum; title "x23 g"; run;
%check(x23_g, train, G_no_var1_train)
%check(x23_g, test, G_no_var1_test)

/* ---------- (H) character ids that read as numbers ---------- */
data work.x23_h;
    length VAR1 $8;
    SeriousDlqin2yrs = 0; RevolvingUtilizationOfUnsecuredL = 0.5; age = 40;
    'NumberOfTime30-59DaysPastDueNotW'n = 0; DebtRatio = 0.1; MonthlyIncome = 1000;
    NumberOfOpenCreditLinesAndLoans = 1; NumberOfTimes90DaysLate = 0;
    NumberRealEstateLoansOrLines = 0; 'NumberOfTime60-89DaysPastDueNotW'n = 0;
    NumberOfDependents = 0;
    do VAR1 = '7', '07', '7.0', '+7', ' 7', '7', '8'; output; end;
run;
%check(x23_h, train, H_char_ids_train)
%check(x23_h, test, H_char_ids_test)
proc sql;
    title "x23 H distinct values";
    select distinct quote(VAR1) as v, put(VAR1, $hex16.) as hex from work.x23_h;
    select count(distinct VAR1) as d_raw, count(distinct strip(VAR1)) as d_strip,
           count(distinct input(strip(VAR1), ?? best32.)) as d_num
    from work.x23_h;
quit;
/* the same text kept in columns of different length, stacked: is '7' in $2 the same id as '7' in $8 */
data work.x23_h2; length VAR1 $2; VAR1 = '7'; output; run;
data work.x23_h3; set work.x23_h(keep=VAR1 where=(VAR1 = '7')) work.x23_h2; run;
proc sql noprint;
    select count(*), count(distinct VAR1) into :x23_n trimmed, :x23_d trimmed from work.x23_h3;
quit;
%put X23 H padding rows=&x23_n distinct=&x23_d;
data _null_;
    a = '7'; b = '7   ';
    same = (a = b);
    put 'X23 H compare ' same=;
run;

/* ---------- (I) PROC IMPORT of id texts with blanks ---------- */
data _null_;
    file "&x23_dir/x23_i.csv" lrecl=1000;
    put ',SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,age,NumberOfTime30-59DaysPastDueNotWorse,DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents';
    put '7,0,0.766,45,2,0.80,9120,13,0,6,0,2';
    put ' 7,0,0.957,40,0,0.12,2600,4,0,0,0,1';
    put '7 ,0,0.957,40,0,0.12,2600,4,0,0,0,1';
    put '" 7",0,0.957,40,0,0.12,2600,4,0,0,0,1';
    put '"7 ",0,0.957,40,0,0.12,2600,4,0,0,0,1';
    put '07,0,0.957,40,0,0.12,2600,4,0,0,0,1';
    put 'A9,0,0.957,40,0,0.12,2600,4,0,0,0,1';
run;
proc import datafile="&x23_dir/x23_i.csv" out=work.x23_i dbms=csv replace;
    getnames=yes;
    guessingrows=max;
run;
proc contents data=work.x23_i varnum; title "x23 i"; run;
data _null_;
    set work.x23_i;
    hex = put(VAR1, $hex12.);
    put 'X23 I ' _n_= 'VAR1=[' VAR1 $char6. '] ' hex=;
run;
%check(x23_i, train, I_import_blanks)

/* ---------- (J) every id text reads as a number ---------- */
data _null_;
    file "&x23_dir/x23_j.csv" lrecl=1000;
    put ',SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,age,NumberOfTime30-59DaysPastDueNotWorse,DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents';
    put '7,0,0.766,45,2,0.80,9120,13,0,6,0,2';
    put '" 7",0,0.957,40,0,0.12,2600,4,0,0,0,1';
    put '07,0,0.957,40,0,0.12,2600,4,0,0,0,1';
    put '7.0,0,0.957,40,0,0.12,2600,4,0,0,0,1';
    put '+7,0,0.957,40,0,0.12,2600,4,0,0,0,1';
run;
proc import datafile="&x23_dir/x23_j.csv" out=work.x23_j dbms=csv replace;
    getnames=yes;
    guessingrows=max;
run;
proc contents data=work.x23_j varnum; title "x23 j"; run;
%check(x23_j, train, J_import_number_texts)
