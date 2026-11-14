/* x19: mechanics for the second round of the Q27 / Q14 / Q25 corrections.
   (1) a %num macro that takes a numeric column as it is and reads a character column with
       BEST32., rejecting text longer than 32 characters; (2) what PROC IMPORT does to
       '12345abc' and 'abc' after row 20 with and without guessingrows=max; (3) FDELETE and
       FILEEXIST on the server; (4) exp() overflow in the inverse logit; (5) BEST12. of a tiny PSI. */
%let x19_dir = %sysfunc(pathname(work));

data _null_;
    file "&x19_dir/x19.csv";
    put 'VAR1,age,MonthlyIncome,NumberOfTimes90DaysLate,NumberOfTime30-59DaysPastDueNotWorse,Other';
    do i = 1 to 25;
        put i +(-1) ',40,5000,0,1,7';
    end;
    put '26,40,12345abc,0,1,7';
    put '27,40,abc,0,1,7';
    put '28,40,NA,0.99999999999999,1,7';
    put '29,40,1234567,1,1,123456789012345678901234567890123456';
    put '30,40,1.0000000000000000000000000000000000000,2,1,7';
run;

proc import datafile="&x19_dir/x19.csv" out=work.x19_default dbms=csv replace;
    getnames=yes;
run;
proc import datafile="&x19_dir/x19.csv" out=work.x19_max dbms=csv replace;
    getnames=yes;
    guessingrows=max;
run;
proc contents data=work.x19_default; run;
proc contents data=work.x19_max; run;
proc print data=work.x19_default(firstobs=24) noobs; format _numeric_ best32.; run;
proc print data=work.x19_max(firstobs=24) noobs; format _numeric_ best32.; run;

%macro num(v);
    %local dsid pos vtype;
    %let vtype = ;
    %let dsid = %sysfunc(open(work.x19_max));
    %let pos = %sysfunc(varnum(&dsid, &v));
    %if &pos > 0 %then %let vtype = %sysfunc(vartype(&dsid, &pos));
    %let dsid = %sysfunc(close(&dsid));
    %if &vtype = N %then "&v"n;
    %else ifn(lengthn(strip("&v"n)) <= 32, input(strip("&v"n), ?? best32.), .);
%mend;

data work.x19_check;
    set work.x19_max;
    income = %num(MonthlyIncome);
    late90 = %num(NumberOfTimes90DaysLate);
    late30 = %num(NumberOfTime30-59DaysPastDueNotW);
    other = %num(Other);
    late90_whole = (late90 >= 0 and late90 = int(late90));
    old_late90 = input(cats(NumberOfTimes90DaysLate), ?? best32.);
    old_whole = (old_late90 >= 0 and old_late90 = int(old_late90));
    keep VAR1 income late90 late30 other late90_whole old_late90 old_whole;
run;
proc print data=work.x19_check(firstobs=24) noobs; format income late90 other old_late90 best32.; run;

/* (3) delete files */
data _null_;
    file "&x19_dir/x19_a.csv"; put 'a';
run;
data _null_;
    length fref $8 fname $64;
    do fname = 'x19_a.csv', 'x19_not_there.csv';
        fref = ' ';
        rc1 = filename(fref, cats("&x19_dir/", fname));
        ex = fexist(fref);
        if ex then rc2 = fdelete(fref);
        rc3 = filename(fref);
        after = fileexist(cats("&x19_dir/", fname));
        put 'X19 DELETE ' fname= rc1= ex= rc2= rc3= after=;
    end;
run;

/* (4) inverse logit at extreme logits, (5) tiny PSI printed with BEST12. and 8.4 */
data _null_;
    do logit = -800, -700, 0, 700, 800;
        pd = 1 / (1 + exp(-logit));
        put 'X19 LOGIT ' logit= pd=;
    end;
    psi = 2e-9;
    put 'X19 PSI ' psi= best12. psi= 8.4;
    x = log(-1 + 1);
    put 'X19 LOG ' x=;
run;
