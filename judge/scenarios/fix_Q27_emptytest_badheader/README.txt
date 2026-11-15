Finding Q27 (round 4, ruling G44): a wrong header with no data line is still rejected.
Training file: the valid 3000-row file of scenarios/fix_Q27_emptytest/good. Test files, no applicant:
wrong_name: the header line with the column age named years.
eleven_names: the header line without its last name (NumberOfDependents).
blank_line: the right header line followed by one empty line (PROC IMPORT cannot read it;
            rejected before and after the correction).
plan.json (run_sas_sequence.py, one session, one output folder): good (four scripts), then each
faulty file (predict.sas must stop and leave no prediction file) followed by good again.
The files were written by hand (head -1, sed), not by make_fix_scenarios.py.

Second round of round 4 (the header of a file with no applicant is read by PROC IMPORT itself):
plan_header_variants.json: good (four scripts), then eight header variants, each one twice:
<variant>_rows (the header over the 200 applicants of the good file) and <variant>_only (the
header line alone). predict.sas must give the same verdict on both: stopped with columns_ok=0
and no prediction file, or accepted. Then good again.
single_quote: 'age'. double_quote: "age". text_after_quote: "age"x. open_quote: the last name
written "NumberOfDependents with no closing quote. duplicate_name: age in place of
NumberOfDependents. long_name: RevolvingUtilizationOfUnsecuredLoans (differs from the right
name after character 32). thirteen_names: one more name, Extra. leading_blank: a blank before age.
thirteen_names has three files: thirteen_names_full_rows (every applicant has a 13th value:
rejected), thirteen_names_rows (the applicants have twelve values; PROC IMPORT drops the name
with no value under it, so this file was and is accepted) and thirteen_names_only (no applicant:
rejected, because the header is read with a value under every name).
cs-training.csv in these folders is a link to ../../fix_Q27_emptytest/good/cs-training.csv.
