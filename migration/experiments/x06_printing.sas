/* Inventory experiment X06 (prompt 06 post-parity): verify the printing rules that
   credit_risk/sas_compat.py marks TODO(port) as unverified. One value per line. */
data _null_;
  length s $40;
  s = '1234567890123456789012345678901234567'; x = input(s, best32.); put "X06 input32 " x best32.;
  s = '   12.5'; x = input(s, best32.); put "X06 input_lead " x best32.;
  array b{8} _temporary_ (0.0000123 0.00000123 0.00012345 0.000012345 0.0000099999 1234567.891 -0.0000123 123456789012);
  do i = 1 to 8; v = b{i}; put "X06 best " v best32. " b8=[" v best8. "] b12=[" v best12. "] b6=[" v best6. "]"; end;
  array p{5} _temporary_ (9.99 9.999 12.34 -12.34 0.0000001);
  do i = 1 to 5; v = p{i}; put "X06 pct " v best32. " p82=[" v percent8.2 "]"; end;
  array d{14} _temporary_ (0.000029 0.00001 0.00000642 0.000123456 123.456789 12345.6789 -0.5 0 1234567.89 -0.000029 0.5 99.123456789 250.5 0.0000012345);
  do i = 1 to 14; v = d{i}; put "X06 d " v best32. " d8=[" v d8. "] d123=[" v d12.3 "]"; end;
  array o{7} _temporary_ (1234.5 0.0005 0.001 999.999 1000 0.0009999 3.7495);
  do i = 1 to 7; v = o{i}; put "X06 oddsr " v best32. " o83=[" v oddsr8.3 "]"; end;
run;
