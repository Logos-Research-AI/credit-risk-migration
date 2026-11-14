/* X11: where does one-argument ROUND switch from rounding down to rounding up below a
   half-integer m? Bisect on doubles; print the smallest x < m that still rounds up. */
data _null_;
  array ms{9} _temporary_ (0.5 2.5 100.5 600.5 712.5 849.5 1000000.5 1e9 4.5e12);
  do i = 1 to 9;
    m = ms{i}; if i = 8 then m = 1e9 + 0.5; if i = 9 then m = 4.5e12 + 0.5;
    up = round(m);
    lo = m - m * 1e-6; hi = m;
    do j = 1 to 200;
      mid = (lo + hi) / 2;
      if mid = lo or mid = hi then leave;
      if round(mid) = up then hi = mid; else lo = mid;
    end;
    gap = m - hi; rel = gap / m;
    put "X11 m=" m best32. " up=" up best32. " thr=" hi hex16. " m_hex=" m hex16. " gap=" gap e12. " rel=" rel e12.;
  end;
  /* negative side and exact halves */
  x = -2.5; r = round(x); put "X11 neg " x= r=;
  x = -712.49999999999989; r = round(x); put "X11 neg " x= best32. r=;
  x = 0.49999999999999994; r = round(x); put "X11 below_half " x= hex16. r=;
  x = 0.4999999999999; r = round(x); put "X11 below_half13 " r=;
  x = 0.499999999999; r = round(x); put "X11 below_half12 " r=;
  x = 0.49999999999; r = round(x); put "X11 below_half11 " r=;
  /* the pipeline expression */
  do pd = 0.002, 0.25, 0.5, 0.998, 1, 0, 1 - 0.5/250, 1 - 1.5/250, 0.75;
    s = round(600 + 250 * (1 - pd)); put "X11 score pd=" pd best32. " s=" s best32.;
  end;
run;
