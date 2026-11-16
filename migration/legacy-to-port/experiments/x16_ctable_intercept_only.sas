/* X16: the classification table (ctable) of an intercept-only fit. Which leave-one-out probability does
   PROC LOGISTIC use, how are the levels built, and is a probability equal to a level counted at it?
   For n observations with e events: the Classification table with ProbLevel in hex16., and the
   cross-validated probability of the OUTPUT statement (predprobs=crossvalidate), which the documentation
   gives as the probability the ctable option uses, in hex16.
   The first eight cases are the fits of judge/runs (emptyval_n2/n3/n4_both, gen_s19, s22, s23, s25, s29),
   as a check that this program's table is the pipeline's. */
options linesize=max nonotes;
%macro one(n, e);
data work.d; do i = 1 to &n; y = (i <= &e); output; end; run;
ods select none;
proc logistic data=work.d descending;
  model y = / ctable;
  output out=work.o predprobs=(individual crossvalidate);
  ods output Classification=work.ct ParameterEstimates=work.pe;
run;
ods select all;
data _null_; set work.pe; put "PE|&n|&e|" Estimate hex16. " " Estimate best32.; run;
data _null_; set work.ct;
  put "CT|&n|&e|" ProbLevel hex16. " " ProbLevel best32. " " CorrectEvents CorrectNonevents IncorrectEvents IncorrectNonevents;
run;
proc sort data=work.o out=work.o1 nodupkey; by y; run;
data _null_; set work.o1; put "XP|&n|&e|y=" y " IP_1=" IP_1 hex16. " " IP_1 best32. " XP_1=" XP_1 hex16. " " XP_1 best32.; run;
proc datasets lib=work nolist; delete d o o1 ct pe; quit;
%mend;
%one(2,1) %one(3,1) %one(3,2) %one(6,2) %one(11,3) %one(14,2) %one(21,8) %one(42,6)
%one(4,1) %one(4,2) %one(4,3) %one(5,1) %one(5,4) %one(6,1) %one(6,3) %one(6,4) %one(6,5) %one(10,9)
%one(11,1) %one(11,2) %one(11,4) %one(11,5) %one(11,6) %one(11,7) %one(11,8) %one(11,9) %one(11,10)
%one(21,5) %one(21,15) %one(26,5) %one(26,13) %one(26,20) %one(26,25) %one(41,8) %one(41,29)
%one(51,10) %one(51,25) %one(51,40) %one(101,30) %one(101,80)
