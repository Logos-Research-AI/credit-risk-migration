/* X09: INPUT(x, best32.) on a column PROC IMPORT typed as numeric (guessingrows=max, no NA):
   is the number first written as BEST12. text and read back? Also what BEST32. prints for
   values of more than 15 significant digits (the format of income_medians.csv). */
filename x09 temp;
data _null_;
  file x09;
  put 'id,MonthlyIncome';
  put '1,1234567890123';
  put '2,123456789.12345';
  put '3,3000';
  put '4,0.000001234567891';
  put '5,';
  put '6,123456789012';
  put '7,1234567.123456789';
run;
proc import datafile=x09 out=work.x09_raw dbms=csv replace; getnames=yes; guessingrows=max; run;
data work.x09_clean;
  set work.x09_raw;
  type = vtype(MonthlyIncome);
  MonthlyIncome_num = input(MonthlyIncome, best32.);
  put "X09 input " id= type= MonthlyIncome= hex16. MonthlyIncome_num= hex16. MonthlyIncome_num= best32.;
run;
data _null_;
  do x = 12345678901234567, 1234567.123456789, 6172839450618783.5, 2499.9999999999995, 0.1, 1e15, 123456789012345678;
    put "X09 best32 " x= hex16. x= best32.;
  end;
run;
