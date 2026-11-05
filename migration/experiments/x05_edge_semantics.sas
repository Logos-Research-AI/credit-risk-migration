/* Inventory experiment X05 (prompt 03 round 1): settle latent semantics the stress test
   found (amendment queue S1, S10, sas_compat review A-01/A-04/A-05/A-06/A-19, diff D21). */
data e; x = 1; if 0; run;                         /* zero rows */
proc sql noprint; select sum(x), mean(x), max(x) into :s, :m, :mx from e; quit;
%put X05 sql_empty sum=[&s] mean=[&m] max=[&mx];
data _null_;
  array v{12} _temporary_ (2.4999999999999996 2.5 2.4999999999 2.49999999999999 -2.4999999999999996
                           712.49999999999989 712.5 0.5 1.5 4503599627370497 -0.5 2.5000000000000004);
  do i = 1 to 12; r = round(v{i}); put "X05 round " v{i} best32. " -> " r best32.; end;
  a = -0.00001; put "X05 w.d neg-zero 8.4 [" a 8.4 "]";
  b = -0.05;    put "X05 percent8.2 neg [" b percent8.2 "]";
  c = 0.000015; put "X05 best6 [" c best6. "] best8 [" c best8. "] best12 [" c best12. "]";
  d = 123456789; put "X05 8.4 overflow [" d 8.4 "]";
  f = exp(1000); put "X05 exp(1000) [" f "]";
run;
