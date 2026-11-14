/* x22: follow-up of x21. (A) more texts through INPUT(strip(text), ?? best32.): a sign or
   nothing before an exponent letter, text after an exponent. (F) row counts of train_bins and
   valid_bins when psi_cuts has no row (x21 F showed them only through psi_calculation). */
options notes;
data work.x22_a;
    length txt $40;
    infile datalines truncover dsd dlm='|';
    input txt $char40.;
    v = ifn(lengthn(strip(txt)) <= 32, input(strip(txt), ?? best32.), .);
    put 'X22A [' txt $char20. '] ' v= best32. ' hex=' v hex16.;
    datalines;
-e5
+d2
-E
+D
e
.e5
-.e5
1e3x
1e3.5
1e 3
1ee3
1e3e2
1d-2
1D+2
2e0
2e00
1e05
x1e3
e1e3
-bad
+NA
1 000
1e--2
12d
12e
12.d
12.5E
;
run;

data work.psi_cuts;
    length cut1-cut9 8;
    stop;
run;
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
proc sql noprint;
    select count(*) into :x22_nt trimmed from work.train_bins;
    select count(*) into :x22_nv trimmed from work.valid_bins;
    select count(*) into :x22_nc trimmed from work.psi_cuts;
    select count(*) into :x22_nl trimmed from work.logit_scored_valid;
quit;
%put X22 F psi_cuts=&x22_nc logit_scored_valid=&x22_nl train_bins=&x22_nt valid_bins=&x22_nv;
