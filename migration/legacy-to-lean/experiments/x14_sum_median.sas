/* X14: association order of the SUM function; PROC SQL MEDIAN with an even count on values
   where (a+b)/2 and a+(b-a)/2 differ; MIN/MAX. */
data _null_;
  s1 = sum(1e16, 1, -1e16, 1); s2 = sum(1, 1e16, -1e16, 1); s3 = sum(1, 1, 1e16, -1e16); s4 = sum(0.1, 0.2, 0.3); s5 = sum(0.3, 0.2, 0.1);
  s6 = sum(., 0.1, ., 0.2, 0.3); s7 = sum(1e16, ., 1, 1);
  put "X14 sum " s1= hex16. s2= hex16. s3= hex16. s4= hex16. s5= hex16. s6= hex16. s7= hex16.;
  t = 0.1; t + 0.2; t + 0.3; put "X14 sumstmt " t= hex16.;
run;
data md; input g x; datalines;
1 1016.85
1 7098.24
2 3
2 1
2 .
2 8
2 5
3 4
;
proc sql; create table mo as select g, median(x) as med from md group by g; quit;
data _null_; set mo; put "X14 median " g= med= hex16. med= best32.; run;
