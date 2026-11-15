Finding Q27, defect D1 of the second review (ruling G44): a test file with its header and no
applicant is valid whatever the order of its twelve columns.
Training file: a link to ../../fix_Q27_emptytest/good/cs-training.csv. Test files: the good 200-row
file of scenarios/fix_Q27_emptytest/good with its columns reordered (<order>_rows) and the header
line of that file alone (<order>_only):
perm: columns 2 and 3 exchanged (RevolvingUtilizationOfUnsecuredLines before SeriousDlqin2yrs).
ageswap: age and MonthlyIncome exchanged.
reversed: the row id first, the other eleven columns in reverse order.
plan.json (run_sas_sequence.py --inspect, one session, one output folder): good (four scripts),
then for each order <order>_rows, <order>_only, good (predict.sas). Each pair must get the same
verdict: accepted, the _only file giving both prediction files with header lines only, no ERROR,
no new WARNING.
plan_fresh_header_only.json, plan_fresh_perm_only.json: one step, the four scripts, on a
header-only test file (Kaggle's order; columns 2 and 3 exchanged). predict.sas runs once in the
session, so no table of an earlier scoring exists.
The files were written by a few lines of Python (csv module), not by make_fix_scenarios.py.
