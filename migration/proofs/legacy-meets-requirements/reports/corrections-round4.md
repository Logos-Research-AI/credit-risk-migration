# Corrections to the legacy code, round 4 (2026-11-15)

Rulings G44 (Q27) and G45 (Q26). Workflow run wf_84ab5b09-3ec: plan, one coding agent, one reviewer per finding, the coding agent's answer, then the whole-program run.

## Account

Both findings are fixed and shown on SAS by the correcting agents, and the corrections run together cleanly on the real data and the four edge scenarios. In this step I spot-checked the Q26 diff and its evidence files; I did not re-run or re-read the Q27 evidence runs.

**Q26 (G45): fixed and shown.** Commit a9acbf5, /Users/cristophersalvi/GitHub/credit-risk-migration/legacy/metrics_calculation.sas.
- Decile table: capture rate and lift are coalesced to 0, so a 0/0 with no defaulter gives 0 on every decile.
- Cumulative lift table: the same division was there and got the same rule. Cumulative capture rate is 0 on every row; cumulative lift is 0 from the first decile that holds an applicant and stays missing before it.
- Evidence: run ev6_fix_Q26_nodefaulter. I read its decile_analysis.csv and printed_cumulative_lift.csv and they show exactly that.
- That run still logs 3 ERROR lines and one WARNING from the kept PROC LOGISTIC ROC step on a one-class set. They predate the change and belong to Q23.
- Not covered by a requirement: the cumulative lift table. The G45 rule there is the agent's choice and changes printed_cumulative_lift.csv when there is no defaulter.
- Left alone knowingly: the KS division at line 150 (Q23/Q24).

**Q27 (G44): fixed and shown.** Commits 5913e11 and 56e52f7, /Users/cristophersalvi/GitHub/credit-risk-migration/legacy/predict.sas.
- A one-line test file is read by PROC IMPORT itself, through a copy of the header with one made-up applicant under it that is then removed. The existing column check then decides.
- Evidence (agent's account, runs ev7_fix_Q27_*): a header-only file gives prediction files with header lines only (19 and 211 bytes), 0 ERROR, 0 new WARNING. A wrong name, eleven names, a duplicated name and a leading blank are rejected with no prediction file left. Files with no line end and with CR LF are covered.
- The reviewer's first defect (the hand-written header parser was more lenient than PROC IMPORT) was answered by removing that parser. The three evidence gaps were answered with new runs.
- Unreviewed: the second commit, 56e52f7, and the ev7 runs were not seen by a reviewer. The review defects listed were raised against 5913e11.

**For the owner to decide**
- Q27: with applicants, PROC IMPORT accepts a header with names in single quotes, text after a closing quote, an unclosed quote, a name differing only after character 32, or a 13th name with no value under it. This is unchanged, before and after this round. A file with no applicant gets the same verdict, except that a 13-name header with no applicant is rejected.
- Q27: 'no applicant' means exactly one line. A header followed by an empty line is still rejected.
- Q27: the closing line of predict.sas still prints the fixed text 'Total records scored: 101,503' on every input. It predates the round and was not in the finding.

**Not done or not shown**
- No experiment x24 or x25 was written: the hook refused writes to migration/legacy-to-lean/experiments/ for the correcting agent, who did not work around it. The evidence is in the scenario runs instead.
- The header-only test file and the no-defaulter validation set were not replayed in the final full runs; they are shown only by the ev6 and ev7 scenario runs.
- The CR LF measurement was made by a script in the scratchpad (/private/tmp/claude-501/-Users-cristophersalvi-GitHub-credit-risk-migration/c1fe66b8-ae3b-4265-94cf-019bef1d754b/scratchpad/measure_uploaded.py), which is not in the repository.
- The parity contract fails on all nine lines, as expected by the brief; port/ and judge/compare.py were not touched. The system instruction says it must pass; the brief says that is the next stage.
- judge/README.md, judge/mutations.py and judge/scenarios/real_metrics remain out of date, as in earlier rounds. judge/test_compare.py and judge/validate_judge.py were not run.

**Housekeeping**
- 17 scenario folders under judge/scenarios/fix_Q27_emptytest_badheader hold cs-training.csv as a symbolic link to ../../fix_Q27_emptytest/good/cs-training.csv. Replace them with copies if links are unwelcome.
- Superseded runs still on disk: dbg7_fix_Q27_header_variants (an uncommitted intermediate version) and dbg5_fix_Q27_*.
- The reference run_meta.json files are the runs' own, without the hand-added 'warnings_reviewed' block of the original reference.
- The system instruction names migration/proofs/port-equals-legacy/brief-coding-agent.md; I followed the task's brief, /Users/cristophersalvi/GitHub/credit-risk-migration/migration/proofs/legacy-meets-requirements/brief-coding-agent.md, Round 4 item 3.
- No hook blocked any call in this step. The logos-mcp and ide servers failed to connect; neither was needed.
- Commits are on branch `initial`; nothing was pushed.

## Full runs

Five runs on the committed scripts (legacy at 56e52f7, working tree clean at start), all under /Users/cristophersalvi/GitHub/credit-risk-migration/judge/runs/ (git-ignored, on disk only):

- final4_real: real data, four scripts in one session, 329 s. 0 ERROR, 0 new WARNING, 32 CSVs. test_predictions.csv and kaggle_submission.csv have 101,503 rows plus header. Validation AUC 0.8559, Gini 0.7118, KS 0.5552 at cutoff 0.0587, PSI 0.0004404097 'No significant change', status 'Production Ready'.
- final4_edge_predict: scenario edge_predict, four scripts, 346 s. 0 ERROR, 0 new WARNING, 32 CSVs.
- final4_edge_metrics_a, final4_edge_metrics_b, final4_edge_metrics_c: metrics_calculation.sas on the stage inputs, 18 s each. 0 ERROR, 0 new WARNING, 9 CSVs each.

The only warnings in the logs are the seven known kinds in judge/known_warnings.txt. The predict.sas log of final4_real echoes the new G44 source (the line count and header copy), so both corrections ran together in one session.

Reference replaced in commit 2aec44b ('Reference: outputs of the corrected SAS'): judge/reference from final4_real, judge/reference/scenarios/edge_predict from final4_edge_predict, edge_metrics_a, b, c from the three metrics runs. Same layout as before; every copied file was compared byte for byte with its run file.

The parity contract (`bash migration/legacy-to-port/parity/run_contract.sh out/parity`) was run afterwards and still fails on every one of its nine lines (fe 0/2, train 14/18, metrics 6/9 and 5/9, predict 0/2). The port is still the port of the uncorrected SAS; this round changed no CSV it is judged against. Working tree clean after it.

## Output changes

No output CSV changed. All 32 real-data CSVs, all 32 edge_predict CSVs and all 9 CSVs of each edge_metrics scenario are byte-identical to the previous reference (commit 3eca5a3), date stamps included, since the runs fall on the same day. So coefficients, grade distribution, AUC, Gini, KS, PSI and the decile tables are unchanged. This is expected: the real data and the four edge scenarios have defaulters in the validation set and a test file with applicants, so neither correction's new branch is reached.

What did change in judge/reference/ (24 files, commit 2aec44b) is the listings only:
- the .log files now echo the corrected source of predict.sas and metrics_calculation.sas;
- the .lst files differ in timestamps, the SAS work folder path and inode number;
- run_meta.json carries the new run ids, remote folders and timings.

No new warning. No file added or removed.

## Code changed by the integration step

None. The program ran with both corrections together without error, so no script was touched. The only commit of this step is 2aec44b, which replaces files under judge/reference/ (listings only in effect).

## Fixes

### Q26 (G45): with no defaulter in the validation set, capture rate and lift were 0/0 (missing) on every decile that holds an applicant.

- State: fixed-and-shown; commit a9acbf5
- Change: Unchanged in this step (no defect was raised against it). /Users/cristophersalvi/GitHub/credit-risk-migration/legacy/metrics_calculation.sas lines 261-262: `coalesce(d.capture_rate, 0)` and `coalesce(d.lift, 0)`, so an empty decile (G41) and a 0/0 both give 0. Cumulative lift table, lines 305-312: the same division by zero was there; I applied the G45 rule: with no defaulter cum_capture_rate is 0 on every row and cum_lift is 0 from the first decile that holds an applicant (it stays missing while the deciles so far are empty, as round 3 left it). The KS division at line 150 was left alone (Q23/Q24).
- Copies: Decile table and cumulative lift table, both in metrics_calculation.sas. No copy in train.sas, predict.sas or feature_engineering.sas.
- Evidence: Scenario /Users/cristophersalvi/GitHub/credit-risk-migration/judge/scenarios/fix_Q26_nodefaulter. Run /Users/cristophersalvi/GitHub/credit-risk-migration/judge/runs/ev6_fix_Q26_nodefaulter: decile_analysis.csv has capture_rate 0.00% and lift 0.00 on all ten rows (deciles 3, 6 and 9 were empty cells in runs/ev5_fix_Q23_nodefaulter); printed_cumulative_lift.csv has cum_capture_rate 0.00% on all rows, cum_lift empty on deciles 1-2 and 0.00 on 3-10. The run still logs 3 ERROR lines and one new WARNING from the PROC LOGISTIC ROC step on a one-class set; they predate the change and belong to Q23. ev6_fix_Q26_small_unchanged and ev6_fix_Q26_ties_unchanged are byte-identical to the ev4 runs; ev6_fix_Q26_reference_scores_unchanged is byte-identical to judge/reference on all 9 files. Not re-run in this step: metrics_calculation.sas did not change.

### Q27 (G44): predict.sas stopped on a test file with its header line and no applicant, because PROC IMPORT cannot read it.

- State: fixed-and-shown; commit 56e52f7 (on top of 5913e11)
- Change: Defect 1 (hand-written header reading more lenient than PROC IMPORT): fixed by removing the hand-written reading. /Users/cristophersalvi/GitHub/credit-risk-migration/legacy/predict.sas lines 48-99: a data step counts the lines of cs-test.csv (up to two) and copies the first line to the WORK folder with one made-up applicant under it (twelve values, plus one more value for every name beyond twelve, same line end as the header). When the file has exactly one line, the same PROC IMPORT reads that copy instead of the file and the made-up applicant is then removed, leaving an empty WORK.TEST_RAW; the existing column check then decides. So the names of a file with no applicant are by construction the names PROC IMPORT gives. In every other case the PROC IMPORT of the file itself runs as before. The copy is deleted afterwards. The reviewer's premise turned out wrong on SAS for the example given: PROC IMPORT with applicants reads 'age' as age and accepts the file (run below), so accepting it with no applicant is consistent; I still replaced the parser because its agreement with PROC IMPORT could not be shown in general. Defects 2-4 (evidence gaps): answered with new scenarios and runs. Defect 5: none to fix.
- Copies: predict.sas only; no other script reads cs-test.csv. The sibling check on cs-training.csv in feature_engineering.sas is not covered by G44 and was not changed.
- Evidence: All runs made with the committed code, one SAS session and one output folder each, under /Users/cristophersalvi/GitHub/credit-risk-migration/judge/runs. (a) ev7_fix_Q27_header_variants (plan /Users/cristophersalvi/GitHub/credit-risk-migration/judge/scenarios/fix_Q27_emptytest_badheader/plan_header_variants.json): eight header variants, each with the 200 applicants and with no applicant. Same verdict in each pair: single_quote ('age'), double_quote ("age"), text_after_quote ("age"x), open_quote ("NumberOfDependents unclosed) and long_name (differs after character 32) are accepted by PROC IMPORT with applicants (200-row files, same md5 as the good run) and accepted with no applicant (19-byte and 211-byte header-only files); duplicate_name and leading_blank stop with columns_ok=0 and leave no prediction file in both forms. Thirteen names: with a 13th value on every row rejected; with no applicant rejected; with 12-value rows accepted (PROC IMPORT drops a name with no value under it; this behaviour with applicants predates the finding). 0 new WARNING in all 19 steps; the closing good step restores the 200-row files. (b) ev7_fix_Q27_emptytest: good, header_only, good: header_only has 0 ERROR, 0 new WARNING, kaggle_submission.csv 19 bytes, test_predictions.csv 211 bytes equal to the header line of the good file; good steps md5-identical to runs/ev4_fix_Q27_textid/01_good. (c) ev7_fix_Q27_emptytest_badheader: wrong_name and eleven_names stop with columns_ok=0, blank_line stops (Import unsuccessful, columns_ok=0), no prediction file left, each following good step restores the files; blank_line shows the same three WARNINGs as in the earlier run dbg5. (d) ev7_fix_Q27_emptytest_noterminator: a 260-byte header with no line end gives the header-only outputs, 0 ERROR, 0 new WARNING. (e) CR LF: ev7_fix_Q27_emptytest_crlf (good, crlf_good identical predictions, crlf_header_only header-only outputs). In both (d) and (e) the last step is crlf_header_only, and uploaded_test_file.json in each run folder records the file as it lay on the server afterwards: 262 bytes by SAS file info, downloaded back to cs-test_as_on_server.csv, byte-identical to the local file, ending in CR LF.

## Review defects

**review Q26 (G45): with no defaulter in the validation set, c**

- none

**review Q27 (G44): predict.sas stopped on a test file with it**

- Wrong header with no data line accepted (found by reading the code, not run on SAS). Input: a valid training file and a one-line cs-test.csv whose header has a name in single quotes, e.g. `,SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,'age',NumberOfTime30-59DaysPastDueNotWorse,DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents`. /Users/cristophersalvi/GitHub/credit-risk-migration/legacy/predict.sas line 67 uses `dequote(strip(scan(...)))`. DEQUOTE removes single quotes as well as double quotes, drops any text after a closing quote (`"age"x` becomes age), and removes an unmatched opening quote (a last field `"NumberOfDependents` becomes NumberOfDependents). PROC IMPORT only treats double quotes as CSV quoting, so with data rows it would name the column `'age'` and columns_ok would be 0. With no data row the new check sets test_header_ok=1, builds the empty table with the correct names, and writes header-only prediction files. This contradicts the finding's condition that a wrong header with no data line must still be rejected, and the comment's claim that the line is read 'as PROC IMPORT names them'. The same leniency applies to STRIP on a name with leading blanks, if PROC IMPORT keeps them; I did not verify that either. I did not run SAS because this step changes nothing.
- Evidence gap on rejection: the rejection scenarios in /Users/cristophersalvi/GitHub/credit-risk-migration/judge/scenarios/fix_Q27_emptytest_badheader cover only a renamed column, a dropped column and a trailing empty line. None exercises the parts of the hand-written header parser that can diverge from PROC IMPORT: quoted names, single quotes, a duplicated name, a name differing only after character 32, or a 13th name. So the runs do not show that 'a wrong header with no data line is still rejected' in general, only for those three files.
- Evidence gap on acceptance: both header-only files tested end with a line terminator (261 bytes with LF, 262 bytes with CR LF). A header-only file with no terminator after the header is not shown.
- Evidence gap on CR LF: nothing in /Users/cristophersalvi/GitHub/credit-risk-migration/judge/runs/dbg5_fix_Q27_emptytest_crlf records that the uploaded file still had CR LF on the server. sequence_meta.json lists only output files, and the log notes for the header-reading data step are not in the log. The CR LF claim therefore rests on the upload being binary.
- No other defect found. Checked: the header-only run has 0 ERROR and 0 new WARNING, with kaggle_submission.csv 19 bytes and test_predictions.csv 211 bytes equal to the good file's header line. All good steps give identical md5 for both prediction files, equal to runs/ev4_fix_Q27_textid/01_good made by the earlier code. wrong_name, eleven_names and blank_line each stop with `columns_ok=0` and leave no prediction file, and the good step after each one restores the 200-row files. The logs echo the same source as the committed predict.sas. No other legacy script reads cs-test.csv, so there is no unfixed copy; a header-only training file is not a valid input because section 3 requires at least one known income. Files with two or more lines, an empty file and a missing file still go through the unchanged PROC IMPORT. The diff touches only legacy/predict.sas and the new scenario folders. The final note 'Total records scored: 101,503' is wrong on every input, but it predates this commit and the finding did not ask to change it.

## Problems and notes from the coding agent

- Q27, a decision the owner may want to see: with applicants, PROC IMPORT (and so the legacy program, before and after this round) accepts a header whose names are in single quotes, have text after a closing quote, have an unclosed quote, differ from the right name only after character 32, or carry a 13th name with no value under it. I did not change that; a file with no applicant now gets the same verdict, except that a 13-name header with no applicant is rejected (it is read with a value under every name).
- Q27 limits unchanged: 'no applicant' means the file has exactly one line; the header followed by an empty line is still rejected. The last line of predict.sas still prints the fixed text 'Total records scored: 101,503'.
- The new scenario folders under judge/scenarios/fix_Q27_emptytest_badheader hold cs-training.csv as a symbolic link to ../../fix_Q27_emptytest/good/cs-training.csv (17 folders; to avoid committing 17 copies of 143 KB). If links are unwelcome in the repository they must be replaced by copies.
- The CR LF measurement was made after each run by a script of mine in the scratchpad (/private/tmp/claude-501/-Users-cristophersalvi-GitHub-credit-risk-migration/c1fe66b8-ae3b-4265-94cf-019bef1d754b/scratchpad/measure_uploaded.py), in a second SAS session reading the run's remote data folder; run_sas_sequence.py was not changed. The script is not in the repository.
- judge/runs/dbg7_fix_Q27_header_variants is a run of an intermediate, uncommitted version of the change (before the made-up applicant was given a value for every name); in it thirteen_names with no applicant was accepted. It is superseded by ev7_fix_Q27_header_variants. The dbg5_fix_Q27_* runs were made with the previous commit's code and are superseded by the ev7 runs.
- judge/runs/ is git-ignored: the run folders are on disk, not in the commits.
- `bash migration/legacy-to-port/parity/run_contract.sh out/parity` still does not pass (fe and predict stages, e.g. monthly_income in model_features_validation.csv, pd_logistic in kaggle_submission.csv): differences between the port and the reference from earlier rounds; I changed nothing in port/ or judge/reference/. Working tree clean after the run.
- Not done, as instructed: the full run on the real data, the edge scenarios and the replacement of judge/reference/. predict.sas on the real test file was not rerun; on the 200-row file its outputs are byte-identical to the earlier code's.
- No experiment x24/x25 was written: in the previous step the hook refused writes to migration/legacy-to-lean/experiments/; I did not try again or work around it.
- Q26, as before: the cumulative lift table is not covered by a requirement; I gave it the G45 rule, which changes printed_cumulative_lift.csv when there is no defaulter.
- The task names migration/proofs/legacy-meets-requirements/brief-coding-agent.md while the standing instructions name the port-equals-legacy brief; I followed the task (Round 4, items 1 and 2). No hook block was met in this step.

## Second review, of commit 56e52f7 (2026-11-15)

The workflow reviewed the Q27 change once, before it was rewritten. A second reviewer, who did not
make the change, read 56e52f7 and its evidence and made one SAS run
(`judge/runs/rev8_review_Q27_column_order`).

- **D1 (new, shown on SAS). A header-only test file whose columns are not in Kaggle's order is
  not scored correctly.** The made-up applicant under the copied header gives the column types by
  position, not by name. Section 3 does not fix the column order, so such a file is valid.
  - Columns 2 and 3 swapped, no applicant: `ERROR: Expression using multiplication (*) requires
    numeric types` in the imputation step; the script does not stop; in a session that already
    holds tables from an earlier step, both prediction files are rewritten from those tables. With
    the 200 applicants under the same header the file is accepted and scored as before.
  - `age` and `MonthlyIncome` swapped, no applicant: the header-only files are written, with an
    ERROR and a new WARNING from the scoring step.
- **D2 (already put to the owner).** One-line files with `'age'`, text after a closing quote, an
  unclosed quote, or a name differing only after character 32 are accepted. The same headers are
  accepted with applicants; this predates the round.
- **D3 (evidence gaps).** No run shows the temporary copy removed; the file without a line end is
  not recorded as it lay on the server; no header-only run was made in a fresh SAS session.
- Files with applicants: no change in behaviour found. The thirteen-name asymmetry does not break
  G44 (a 13-name header is invalid under section 3).
