/* x16: what does ABORT CANCEL do in a DATA step when the program is submitted through saspy (IOM)?
   Expected for the Q27 fix: the rest of the submission is cancelled, the session survives. */
data work.x16_before; x = 1; run;

data _null_;
    put "ERROR: Input validation failed (x16 test).";
    abort cancel;
run;

data work.x16_after; x = 1; run;
%put X16_STATEMENT_AFTER_ABORT_REACHED;
