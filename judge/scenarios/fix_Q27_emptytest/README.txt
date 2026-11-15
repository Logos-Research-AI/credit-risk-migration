Finding Q27 (round 4, ruling G44): a test file with its header line and no applicant is valid.
good: the valid 3000-row training file and 200-row test file of scenarios/fix_Q27_textid/good.
header_only: the same training file; cs-test.csv is the header line of the good test file alone.
crlf_good, crlf_header_only: the good and the header-only test file with CR LF line ends.
plan.json (run_sas_sequence.py, one session, one output folder): good (four scripts);
header_only (predict.sas must write kaggle_submission.csv and test_predictions.csv with their
header lines only, no ERROR); good again.
plan_crlf.json: good (four scripts); crlf_good (predict.sas); crlf_header_only (predict.sas).
The files were written by hand (head -1, sed), not by make_fix_scenarios.py.
header_only_noterminator: the header line with no line end after it (260 bytes).
plan_noterminator.json: good (four scripts); header_only_noterminator (predict.sas);
crlf_header_only (predict.sas, last, so the uploaded file stays on the server to be measured).
