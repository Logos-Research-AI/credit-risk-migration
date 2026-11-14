/* X15: (A) one-to-one MERGE when a later data set with a same-named variable runs out;
   (B) PROC LOGISTIC ROC statement with PRED= on small inputs: ties, near-ties (ROCEPS),
       missing values, full-precision Area; (C) a small fit with OUTPUT, LACKFIT, Association,
       and PROC PLM SCORE, printed in hex so that scoring and grouping rules can be checked. */
data a; x = 1; y = 10; output; x = 2; y = 20; output; x = 3; y = 30; output; run;
data b; x = 5; z = 7; output; run;
data mab; merge a b; run;
data _null_; set mab; put "X15A merge_ab " x= y= z=; run;
data mba; merge b a; run;
data _null_; set mba; put "X15A merge_ba " x= y= z=; run;

%macro roc(ds, tag);
  ods select none;
  proc logistic data=&ds;
    model y(event='1') = p / nofit;
    roc 'M' pred=p;
    ods output ROCAssociation=ra_&tag;
  run;
  ods select all;
  data _null_; set ra_&tag; put "X15B &tag " ROCModel= Area= hex16. Area= best32. StdErr= hex16. SomersD= hex16. Gamma= hex16. TauA= hex16.; run;
%mend;
data r1; input p y @@; datalines;
.1 0 .2 0 .2 1 .3 0 .3 1 .3 0 .4 1 .5 0 .5 1 .6 1 .7 0 .9 1
;
%roc(r1, r1);
/* near ties: event 0.3 vs nonevent 0.3+5e-9 (inside 1e-8); event 0.6+2e-8 vs nonevent 0.6 */
data r2; p = 0.3; y = 1; output; p = 0.3 + 5e-9; y = 0; output; p = 0.6 + 2e-8; y = 1; output; p = 0.6; y = 0; output; run;
%roc(r2, r2);
/* chain: a (event), a+0.6e-8 (nonevent), a+1.2e-8 (event), plus anchors */
data r3; p = 0.5; y = 1; output; p = 0.5 + 0.6e-8; y = 0; output; p = 0.5 + 1.2e-8; y = 1; output; p = 0.1; y = 0; output; p = 0.9; y = 1; output; run;
%roc(r3, r3);
/* reversed near pair: nonevent lower by 5e-9 (would be concordant if exact) */
data r4; p = 0.3; y = 0; output; p = 0.3 + 5e-9; y = 1; output; p = 0.8; y = 0; output; p = 0.2; y = 1; output; run;
%roc(r4, r4);
/* missing p and missing y rows */
data r5; set r1 end=e; output; if e then do; p = .; y = 1; output; p = 0.45; y = .; output; p = .; y = 0; output; end; run;
%roc(r5, r5);
/* 7 events, 13 nonevents, no ties except two */
data r6; input p y @@; datalines;
.11 0 .13 0 .17 1 .19 0 .23 0 .29 1 .31 0 .37 0 .41 1 .43 0 .47 0 .53 1 .59 0 .61 0 .67 1 .71 0 .73 1 .79 0 .83 1 .83 0
;
%roc(r6, r6);

/* (C) fit */
data fit; call streaminit(20261110);
  do i = 1 to 3000;
    x1 = round(rand('normal'), 0.1); x2 = rand('uniform');
    eta = -2 + x1 + 0.5 * x2; y = rand('bernoulli', 1 / (1 + exp(-eta)));
    if i = 2998 then y = .; if i = 2999 then x2 = .; if i = 3000 then x1 = .;
    output;
  end;
  drop eta;
run;
ods select none;
proc logistic data=fit descending;
  model y = x1 x2 / lackfit;
  output out=fo predicted=p xbeta=xb;
  store work.fitmodel;
  ods output Association=fa LackFitPartition=fh LackFitChiSq=fc ParameterEstimates=fp;
run;
proc plm restore=work.fitmodel; score data=fit out=fs predicted=pl; run;
ods select all;
data _null_; set fp; put "X15C coef " Variable= Estimate= hex16.; run;
data _null_; set fa; put "X15C assoc " Label1= nValue1= hex16. nValue1= best32. Label2= nValue2= hex16.; run;
data _null_; set fh; put "X15C hl " Group= Total= EventsObserved= EventsExpected= hex16. NoneventsObserved= NoneventsExpected= hex16.; run;
data _null_; set fc; put "X15C hlchisq " ChiSq= hex16. ChiSq= best32. DF= ProbChiSq= hex16.; run;
data _null_; merge fo fs(keep=pl); put "X15C row " i= y= x1= hex16. x2= hex16. p= hex16. xb= hex16. pl= hex16.; run;

/* (D) discrete covariate: few distinct probabilities, big tie blocks */
data fit2; call streaminit(7);
  do i = 1 to 1000; x1 = rand('integer', 0, 15); y = rand('bernoulli', 1 / (1 + exp(-(-2.5 + 0.3 * x1)))); output; end;
run;
ods select none;
proc logistic data=fit2 descending;
  model y = x1 / lackfit;
  output out=fo2 predicted=p;
  ods output Association=fa2 LackFitPartition=fh2 LackFitChiSq=fc2;
run;
ods select all;
data _null_; set fa2; put "X15D assoc " Label1= nValue1= hex16. Label2= nValue2= hex16.; run;
data _null_; set fh2; put "X15D hl " Group= Total= EventsObserved= EventsExpected= hex16. NoneventsObserved= NoneventsExpected= hex16.; run;
data _null_; set fc2; put "X15D hlchisq " ChiSq= hex16. DF= ProbChiSq= hex16.; run;
data _null_; set fo2; put "X15D row " i= y= x1= p= hex16.; run;
