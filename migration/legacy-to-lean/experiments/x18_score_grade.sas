/* x18: findings Q15 and Q18. The corrected scoring statements of predict.sas section 5 (copied verbatim below;
   train.sas has the same score and grade statements twice) on chosen probabilities, since no input file can
   set a probability: 0.25 (Q15: score 787.5) and 0.20 (Q18: grade C), the band edges of Q18 with their
   neighbours, and a missing probability. */
data work.test_scored;
    input pd_logistic @@;
    datalines;
0.25 0.20 0 0.0999 0.10 0.1499 0.15 0.2499 0.35 0.3501 0.50 0.5001 1 .
;
run;

data work.test_predictions;
    set work.test_scored;

    /* Binary prediction at 0.5 threshold */
    pred_logistic = (pd_logistic >= 0.5);

    /* Convert probability to credit risk score (300-850 scale) */
    base_score = 600;
    score_range = 250;
    credit_risk_score = base_score + score_range * (1 - pd_logistic);

    /* Assign risk grades from the probability (a missing probability is graded F) */
    if missing(pd_logistic) then risk_grade = 'F';
    else if pd_logistic < 0.10 then risk_grade = 'A';
    else if pd_logistic < 0.15 then risk_grade = 'B';
    else if pd_logistic < 0.25 then risk_grade = 'C';
    else if pd_logistic < 0.35 then risk_grade = 'D';
    else if pd_logistic <= 0.50 then risk_grade = 'E';
    else risk_grade = 'F';

    /* Recommended actions */
    if risk_grade in ('A', 'B') then recommendation = 'Approve';
    else if risk_grade = 'C' then recommendation = 'Review';
    else recommendation = 'Decline';

    /* Suggested interest rate */
    base_rate = 0.05;
    if risk_grade = 'A' then interest_rate = base_rate;
    else if risk_grade = 'B' then interest_rate = base_rate + 0.02;
    else if risk_grade = 'C' then interest_rate = base_rate + 0.04;
    else if risk_grade = 'D' then interest_rate = base_rate + 0.07;
    else if risk_grade = 'E' then interest_rate = base_rate + 0.10;
    else interest_rate = base_rate + 0.15;

    format interest_rate percent8.2;
run;

proc print data=work.test_predictions noobs;
    var pd_logistic pred_logistic credit_risk_score risk_grade recommendation interest_rate;
    format credit_risk_score best12.;
run;
