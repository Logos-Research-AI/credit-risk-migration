/* Inventory experiment X01 (prompt 02): settle two SAS behaviors empirically.
   (a) one-to-one MERGE (no BY) when one input has more rows than another
       -- metrics_calculation.sas:332 merges auc_summary (1 row), ks_statistic
          (1+ rows on KS ties), psi_summary (1 row).
   (b) PROC SQL "select x + 1 as x ... group by x": source column or alias?
       -- metrics_calculation.sas:192 (decile + 1 as decile ... group by decile). */
data a; auc = 0.8; run;
data k; ks = 0.5; output; ks = 0.6; output; run;
data p; psi = 0.01; run;
data merged; merge a k p; run;
proc print data=merged noobs; title "X01a one-to-one merge"; run;

data r; input decile v; datalines;
0 1
0 2
1 3
2 4
;
proc sql;
  create table g as select decile + 1 as decile, count(*) as n, sum(v) as s
  from r group by decile order by decile;
quit;
proc print data=g noobs; title "X01b alias vs column in group by"; run;
