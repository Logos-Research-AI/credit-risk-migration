Finding Q27 (round 4, ruling G44): a wrong header with no data line is still rejected.
Training file: the valid 3000-row file of scenarios/fix_Q27_emptytest/good. Test files, no applicant:
wrong_name: the header line with the column age named years.
eleven_names: the header line without its last name (NumberOfDependents).
blank_line: the right header line followed by one empty line (PROC IMPORT cannot read it;
            rejected before and after the correction).
plan.json (run_sas_sequence.py, one session, one output folder): good (four scripts), then each
faulty file (predict.sas must stop and leave no prediction file) followed by good again.
The files were written by hand (head -1, sed), not by make_fix_scenarios.py.
