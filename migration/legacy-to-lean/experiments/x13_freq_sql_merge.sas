/* X13: PROC FREQ OUT= with missing levels; PROC SQL aggregates, grouping order, remerge,
   join with missing keys and row order, median; one-to-one MERGE corner cases. */
data f; input a b @@; datalines;
1 1  0 0  1 0  0 0  . 1  1 .  0 1  0 0  1 1  . .  0 0
;
proc freq data=f noprint; tables a * b / out=fo; run;
data _null_; set fo; put "X13 freq " a= b= count= percent= hex16. percent= best32.; run;
data f2; input a b @@; datalines;
1 1  1 1  1 1
;
proc freq data=f2 noprint; tables a * b / out=fo2; run;
data _null_; set fo2; put "X13 freq2 " a= b= count= percent=; run;
/* 3 of 7 and 5 of 13: 100*c/N vs c/N*100 differ in the last bit */
data f3; do i = 1 to 7; a = (i <= 1); b = 0; output; end; run;
proc freq data=f3 noprint; tables a * b / out=fo3; run;
data _null_; set fo3; put "X13 freq3 " a= b= count= percent= hex16.; run;
data f4; do i = 1 to 13; a = (i <= 5); b = 0; output; end; run;
proc freq data=f4 noprint; tables a * b / out=fo4; run;
data _null_; set fo4; put "X13 freq4 " a= b= count= percent= hex16.; run;

/* SQL aggregates with missing; grouping order from unsorted input; sum order inside a group */
data s; input g x y; id = _n_; datalines;
2 1e16 1
1 0.1 0
. 5 1
2 1 .
1 0.2 1
2 -1e16 0
3 . .
1 0.3 0
2 1 1
. 7 0
;
proc sql;
  create table sg as select g, count(*) as n, sum(x) as sx, mean(x) as mx, min(x) as mnx, max(x) as mxx,
     sum(y) as sy, mean(y) as my, sum(y = 0) as n0, sum(y = 1) as n1, median(x) as medx
  from s group by g;
quit;
data _null_; set sg; put "X13 sqlgrp " g= n= sx= hex16. mx= hex16. mnx= mxx= sy= my= hex16. n0= n1= medx= hex16.; run;
/* reversed input: does the group sum depend on input order? */
proc sort data=s out=srev; by descending id; run;
proc sql; create table sg2 as select g, sum(x) as sx, mean(x) as mx from srev group by g; quit;
data _null_; set sg2; put "X13 sqlgrp_rev " g= sx= hex16. mx= hex16.; run;
proc sql noprint;
  select sum(y = 0), sum(y = 1), sum(y), mean(y), count(*) into :n0, :n1, :sy, :my, :cnt from s;
quit;
%put X13 into n0=[&n0] n1=[&n1] sy=[&sy] my=[&my] cnt=[&cnt];
/* remerge with ties: row order of the result */
data k; input ks pd; id = _n_; datalines;
0.2 0.9
0.5 0.4
0.1 0.3
0.5 0.2
0.5 0.6
0.3 0.1
;
proc sql; create table kso as select max(ks) as KS_Statistic, pd as KS_Cutoff, id from k
   where ks = (select max(ks) from k); quit;
data _null_; set kso; put "X13 remerge " KS_Statistic= KS_Cutoff= id=; run;
data km; ks = .; pd = 0.1; output; ks = .; pd = 0.2; output; run;
proc sql; create table kmo as select max(ks) as KS_Statistic, pd as KS_Cutoff from km
   where ks = (select max(ks) from km); quit;
data _null_; set kmo; put "X13 remerge_allmiss " KS_Statistic= KS_Cutoff=; run;
/* joins: missing keys match; row order */
data ja; input bin p; datalines;
3 0.3
. 0.05
0 0.2
1 0.25
2 0.2
;
data jb; input bin q; datalines;
0 0.1
. 0.2
2 0.4
4 0.3
;
proc sql;
  create table jo as select a.bin, a.p, b.q, (a.p - b.q) * log(a.p / b.q) as comp
    from (select bin, p from ja) a join (select bin, q from jb) b on a.bin = b.bin;
  create table js as select sum(comp) as PSI format=8.4,
     case when calculated PSI < 0.1 then 'No significant change'
          when calculated PSI < 0.25 then 'Some change' else 'Significant change' end as interp
     from jo;
  create table je as select sum(comp) as PSI format=8.4,
     case when calculated PSI < 0.1 then 'No significant change'
          when calculated PSI < 0.25 then 'Some change' else 'Significant change' end as interp
     from jo where bin > 100;
quit;
data _null_; set jo; put "X13 join " bin= p= q= comp= hex16.; run;
data _null_; set js; put "X13 psisum " PSI= hex16. interp=; run;
data _null_; set je; put "X13 psisum_empty " PSI= interp=; run;
/* left join order: 40 rows, keys 1..5 unsorted */
data la; do id = 1 to 40; key = mod(id * 7, 5) + 1; if id in (13, 29) then key = .; output; end; run;
data lb; do key = 1 to 4; med = key * 100; output; end; run;
proc sql; create table lo as select a.id, a.key, b.med from la a left join lb b on a.key = b.key; quit;
data _null_; set lo; put "X13 leftjoin " id= key= med=; run;
/* SQL division by zero, log of zero */
proc sql; create table dz as select 1 / 0 as a, log(0) as b, 0.1 / 0.1 as c from lb(obs=1); quit;
data _null_; set dz; put "X13 sqlarith " a= b= c=; run;
/* mean of 0/1 flag over all rows + division by scalar subquery */
proc sql; create table dq as select g, sum(y) / (select sum(y) from s) as cap, mean(y) / (select mean(y) from s) as lift
   from s group by g order by g; quit;
data _null_; set dq; put "X13 subq " g= cap= hex16. lift= hex16.; run;

/* MERGE: where= selecting no rows; 2-row middle dataset; length after merge */
data m1; length ROCModel $14; ROCModel = 'Logistic Model'; AUC = 0.8; Gini = 0.6; run;
data m2; KS = 0.5; cut = 0.1; output; KS = 0.5; cut = 0.2; output; run;
data m3; PSI = 0.01; length interp $21; interp = 'No significant change'; run;
data m4; threshold = 0.4; acc = 1; output; threshold = 0.6; acc = 2; output; run;
data mm; merge m1 m2 m3 m4(where=(threshold = 0.5));
  length model $20 status $20; model = "Logistic Regression";
  if AUC >= 0.7 and KS >= 0.3 and PSI < 0.25 then status = "Production Ready";
  else if AUC >= 0.65 then status = "Requires Review"; else status = "Needs Improvement";
run;
data _null_; set mm; put "X13 merge " ROCModel= AUC= Gini= KS= cut= PSI= interp= threshold= acc= model= status=; run;
data m0; set m1; if 0; run;
data mm0; merge m0 m3; x = 1; run;
data _null_; set mm0; put "X13 merge_empty " ROCModel= AUC= PSI= x=; run;
/* character length from first assignment */
data ch; g = 'C'; if g in ('A', 'B') then rec = 'Approve'; else if g = 'C' then rec = 'Review'; else rec = 'Decline';
  l = lengthc(rec); put "X13 char rec=[" rec $char7. "] l=" l; run;
/* retain without initial value + sum statement with missing */
data rt; input d t; datalines;
. 5
3 .
2 4
;
data _null_; set rt; retain cd cc; if _n_ = 1 then do; cd = d; cc = t; end; else do; cd + d; cc + t; end;
  put "X13 retain " _n_= cd= cc=; run;
