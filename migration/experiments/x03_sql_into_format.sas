/* Inventory experiment X03 (prompt 02 fan-out): what text does PROC SQL INTO: store for a
   numeric aggregate without a format? metrics_calculation.sas:213-217 stores
   sum(default_flag) / mean(default_flag) in &total_defaults / &overall_default_rate and
   divides by them at :232 and :236 (cum_capture_rate, cum_lift). */
data d; do i = 1 to 3; y = (i = 1); output; end; run;          /* mean = 1/3 */
data e; do i = 1 to 105000; y = (mod(i, 15) = 0); output; end; run; /* mean = 0.0666... */
data f; y = 123456789; output; y = 1; output; run;              /* sum needs 9 digits */
proc sql noprint;
  select sum(y), mean(y) into :s1, :m1 from d;
  select sum(y), mean(y) into :s2, :m2 from e;
  select sum(y), mean(y) into :s3, :m3 from f;
quit;
%put X03 s1=[&s1] m1=[&m1];
%put X03 s2=[&s2] m2=[&m2];
%put X03 s3=[&s3] m3=[&m3];
data _null_; x = 1 / &m1; put "X03 1/m1 = " x best32.; run;
/* (b) same, with the BEST12. format PROC IMPORT attaches to default_flag (metrics log) */
data g; set e; format y best12.; run;
proc sql noprint;
  select sum(y), mean(y) into :s4, :m4 from g;
quit;
%put X03 formatted s4=[&s4] m4=[&m4];
