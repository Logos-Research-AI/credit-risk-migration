Finding Q27 (round 3, ruling G42): the row id must be a number in both raw files.
good: the valid 3000-row training file and 200-row test file of scenarios/fix_G34/income_zero.
train_text_id: the same, with the id of training row 34 replaced by the text A34.
test_text_id: the same, with the id of test row 30 replaced by the text A30.
plan.json (run_sas_sequence.py, one session, one output folder): good (four scripts);
train_text_id (feature_engineering.sas must stop and leave no feature file); good again;
test_text_id (predict.sas must stop and leave no prediction file); good again.
