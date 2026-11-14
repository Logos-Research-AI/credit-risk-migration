/* X10 probe: connectivity + missing-value comparison and arithmetic basics. */
data _null_;
  m = .;
  a = (m < 2500); b = (m > 0); c = (m >= 3); d = (m <= 2); e = (m = .); f = (m > .);
  put "X10 cmp lt=" a " gt=" b " ge=" c " le=" d " eq=" e " gtmiss=" f;
  if m then t = 1; else t = 0; put "X10 truth_missing=" t;
  z = 0; if z then t = 1; else t = 0; put "X10 truth_zero=" t;
  n = -0.5; if n then t = 1; else t = 0; put "X10 truth_neg=" t;
  s1 = sum(., ., .); s2 = sum(1, ., 2); s3 = sum(., 0); put "X10 sum " s1= s2= s3=;
  mn1 = min(., 200); mn2 = min(., .); mx1 = max(0, .); mx2 = max(., .); put "X10 minmax " mn1= mn2= mx1= mx2=;
  p1 = m + 1; p2 = m * 100; p3 = 1 / 0; p4 = 0 / 0; p5 = m / 0; p6 = 5 / m; put "X10 arith " p1= p2= p3= p4= p5= p6=;
  l1 = log(0); l2 = log(-1); l3 = log(m); l4 = log(1); put "X10 log " l1= l2= l3= l4=;
  big = 1e308; o1 = big * 10; o2 = big + big; o3 = exp(710); o4 = exp(709); o5 = exp(-1000); o6 = 1 / (1 + exp(1000)); o7 = -big - big; o8 = big / 1e-10;
  put "X10 overflow " o1= o2= o3= o4= o5= o6= o7= o8=;
  ab1 = abs(m); ab2 = abs(-3); put "X10 abs " ab1= ab2=;
  r1 = round(m); put "X10 roundmiss " r1=;
run;
