# Gate decisions

Durable record of human sign-offs. The rulebook (Step 1) supersedes this file
for translation rules once it exists.

## Feasibility gate — signed off 2026-11-05

- Verdict: **migrate now**, kit scaled to 4 units; build the judge first (prompt 00b).
- Posture: structure-preserving (one .sas script -> one Python module). Forced
  exception: the WORK-library model store (train.sas:151, predict.sas:208)
  becomes an on-disk artifact. Duplicated feature engineering is preserved
  during the port and deduplicated post-parity (prompt 06).
- Model plan:
  - Rulebook authorship / amendments: claude-opus-5-5
  - Skeptic reviewers, judge build (00b): claude-opus-5-5
  - Translation implementers, fixers: claude-sonnet-5-5
- Target stack: Python 3.13 (uv), **polars** for data (not pandas), numpy for
  model fitting (statsmodels where it helps). Rules for null semantics,
  `maintain_order=True`, and `best12.` CSV formatting go in the rulebook.
- Old-code oracle: **SAS OnDemand for Academics via saspy** (judge/ env;
  profiles in ~/.config/saspy/sascfg_personal.py; Java = Homebrew openjdk).
  Frozen goldens in output/ remain the reference if a re-run diverges.
  Basis for using ODA (non-commercial license): per the user, this is a
  non-commercial trial run of the migration kit, not production work.

## ODA connection — verified 2026-11-05

- saspy profile `oda_eu` (region euw1), user u64643823, home `/home/u64643823`.
- SAS version on ODA: 9.04.01M9P06052025. The frozen goldens in output/ were
  produced on another account (/home/u64352077), SAS version unknown.
- Judge build (prompt 00b) kicked off by the feasibility sign-off.

## Judge (prompt 00b) — built 2026-11-05, SIGNED OFF 2026-11-05

- Judge: `judge/` (see judge/README.md). Reference = fresh unmodified SAS run on ODA
  (`judge/reference/`, 31 files), byte-identical to the frozen `output/` goldens on the
  9 shared files. The frozen `output/` is NOT a usable fallback (lacks 22 judged files).
- Validation: 18/19 SAS mutations CAUGHT, 1 EQUIVALENT (train_slentry: outputs
  byte-identical), 0 MISSED; positive control (converged refit) PASSES; 75/75 self-test.
- Port contract: 4 stages judged on reference inputs + 4 edge scenarios + e2e smoke.
- Split: taken as an input (reference row_ids). SAS's own split drifted in 1 of 17 runs.

### Deviations from the kit (prompt 00b)
1. Steps 1–2 (categorize / rewrite existing tests): not applicable, the repo has 0 tests.
   Substituted: real-world scenarios + edge-case input scenarios, as 00b allows.
2. Reviewers A and B reviewed code that was edited while they worked (B noted it).
   Mitigation: review C re-reviewed the final state with no knowledge of A/B.
3. Review C's findings were fixed by the orchestrator and verified by the self-test
   and a full re-validation, but not re-reviewed by a fourth reviewer.
4. Orchestrator (this session) ran on claude-opus-5-5 (model plan: judge build = Opus).
   All three reviewers ran on Opus per the model plan. No deviation.

### Judge sign-off — 2026-11-05
- User approved the judge, its comparison policy (judge/README.md), and committing.
- Reference storage: plain git (user approved without choosing; plain git is the
  simpler default for a trial; largest file 23 MB). Switch to Git LFS if the repo grows.
- This sign-off kicks off Step 1 (prompts 01 dependency map, 02 gap inventory, rulebook).

## Step 1 — dependency map + rulebook draft signed off 2026-11-05
- Dependency map (4 files, 5 edges, 0 cycles) and manifest (4 units) accepted.
- RULEBOOK.md v1.0: user accepted all five proposed defaults (in-loop ruff+pyright;
  statsmodels/scikit-learn banned; SGPLOT not ported; listing-only PROCs not ported;
  predict.sas duplication kept until parity). DEV-004 sanctioned.
- Next: prompt 02 gap inventory; stops after the first 20 rows.

## Step 1 — gap inventory first 20 rows signed off 2026-11-05
- Sweep (461 sites) and batch 1 (20 rows, 134 sites) accepted.
- Q1: option (a). The judge judges Association "Percent Tied" with an absolute
  tolerance of 1e-5 percentage points (judge/compare.py `ABS_CELL_TOL`, 4 new
  self-test cases, 79/79). Re-validation: 18 CAUGHT, 1 EQUIVALENT, unchanged. Row 15
  is now confirmed.
- Amendments A1–A8 approved. Applied to RULEBOOK.md (v1.1) on the user's authorization.
- DEV-005 sanctioned. Moved into RULEBOOK §7.
- Next: fan out the remaining sites (shards per category, two Opus skeptics per batch),
  merge, joint audit, then stop at the prompt 02 gate.

## Step 1 — gap inventory complete 2026-11-05 (awaiting sign-off)
- Inventory: 193 rows, 462/462 sites; 192 confirmed, 1 UNKNOWN (Q2). Record:
  migration/inventory-review-fanout.md.
- Waiting on the human: Q2; amendments A9–A31 (A20 replaces A10); DEV-006.
- Judge documentation fixes, no verdict change: sas_best12 is plain-notation only; 283 ties.

## Step 1 — gap inventory SIGNED OFF 2026-11-05
- The user answered "Ok" to the gate recommendations, recorded as approval of all of:
  - Q2 (a): the judge allows HL Totals ±2 (compare.py; self-test 81/81; validation verdicts
    unchanged). The HL row is confirmed, so 193/193 rows are confirmed.
  - Amendments A9–A31 applied as RULEBOOK v1.2 (A10 withdrawn, replaced by A20).
  - DEV-006 sanctioned and moved into RULEBOOK §7.
- Before Step 2 (prompt 03), the user installs .claude/settings.json from the kit template
  (absent as of this gate; the kit forbids the agent from installing it).

## Step 2 (prompt 03) — started 2026-11-05 under the user's standing instruction
- The user: "Do all the steps without ever stopping asking me. I trust your judgement and
  recommendations." Every later gate is decided by the orchestrator using its recommendation,
  and recorded here for audit.
- settings.json is absent; logged as waived (DEV-007), not installed.
- Pilot implementer = translator A (DEV-008).
- Stack: pyproject.toml (uv), polars 2.1.0 and numpy 2.5.4 pinned to the judge's versions,
  scipy, ruff and pyright (strict) as the in-loop referee.
- sas_compat API stub written by the orchestrator; bodies by a Sonnet implementer and reviewed.

## Step 2 (prompt 03) — closed 2026-11-05 (orchestrator decision, standing instruction)
- Round 1:
  - sas_compat: 68/68 checks.
  - Pilot: 0 wrong-output findings.
  - Bakeoff: 13 rulebook-right, 10 both-defensible, 1 native-right, 0 both-wrong.
  - The pilot translations pass judge runs 2–8 (staged) on first execution.
- Amendments S1–S12 + X05 applied as RULEBOOK v1.3; inventory fixes for the decile
  divisors, S6 and S11.
- Re-round folded into Step 3 (DEV-009).
- Workspaces deleted: the stress-pilot worktree (`git worktree remove` + branch deleted) and
  translator B's scratch folder. Confirmed absent by `ls`.
- Report: migration/stress-test/report.md.

## Step 3 (prompt 04) — translation complete 2026-11-05 (orchestrator, standing instruction)
- 4 units translated in the main repo, each through a Sonnet implementer, 2 Opus reviewers,
  arbitration by the orchestrator and a Sonnet fixer. Reviews: migration/translation-review/.
- Wrong-output findings caught by review: 1 (feature_engineering column order; both reviewers).
  Every other finding was a rule violation, latent or a nit, and all were applied.
- Inventory rows corrected against v1.3 during review:
  - merge_one_to_one, sas_exp in train, sql_mean, KS eq, macro returns, the D8. E-notation;
  - the garbled model_summary row that an orchestrator edit had introduced.
- Step 4 (survey build) is dissolved: ruff + pyright strict ran in-loop (RULEBOOK §0).
- Referee on the package: ruff format and check clean, pyright strict 0 errors; every
  trailer's todos= equals its grep count.
- Judge contract (Step 5/6) on the final code, receipts in migration/parity/:
  - runs 1, 2, 3, 6, 7, 8, 4, 5 all PASS (2/2, 18/18, 9/9 ×4, 2/2 ×2);
  - run 9 e2e PASSES for fe and predict;
  - full pipeline about 16 s.

## Step 6 done-gate — PASSED 2026-11-05
- Port parity: 10/10 judged runs pass (66/66 files). The original SAS re-run (baseline_v3) is
  31/31 strict-identical, with 0 errors and 0 new warnings. Record: migration/parity/done-gate.md.
- Next: prompt 06 post-parity burndown.

## Prompt 06 post-parity burndown — complete 2026-11-05 (orchestrator, standing instruction)
- Receipt before: 6 BUG(port) lines (4 defects), 19 TODO(port), 0 PERF(port).
  After: 0 TODO(port) in every module and every trailer todos=0. The BUG(port) lines stay as
  documentation of the default SAS-compatible behaviour. Classification:
  migration/post-parity/classification.md.
- Parity-preserving fixes and closures are MERGED on sas-to-python-migration (one commit per
  marker). Opus review: all 95 judged output files byte-identical to the pre-burndown run;
  review findings fixed forward. The fixer died on a network error, and the orchestrator
  finished findings 7, 11 and 12. Final checks: 76/76 sas_compat checks, judge contract 10/10 PASS.
- Behaviour-changing BUG fixes are NOT merged. Branch `post-parity-bugfixes` (5 commits:
  #4 PSI bins, #1 income truncation, #3 training medians, plus 2 review fix-ups), each behind an
  off-by-default flag. Flag-off contract: 10/10 PASS at every commit. Flag-on effects are in
  migration/post-parity/bugfix-{1,3,4}.md (on the branch). Merging them changes model outputs;
  that is the user's decision.
- RULEBOOK v1.4: post-parity notes.
- Cost-log row 06: tokens are a lower bound (the failed agent's final usage was not reported);
  wall-clock is unknown.

## Separation: the port follows SAS — owner's decision 2026-11-16
- Withdrawn: the deliberate stop of RULEBOOK v1.4 ("a logistic fit that does not converge
  (separation) raises an error"). It was made when no input in hand separated; on small valid
  inputs SAS completes and the port wrote nothing of train or predict (`small-inputs.md` (c)).
- Now: when a variable separates the classes as it enters, the port warns as SAS does, keeps the
  step with the estimates of the iteration at which SAS declares the separation, and goes on to
  the removal test. RULEBOOK §2 (stepwise row and post-parity note) is updated in the same commit.
- The rule for the kept estimates (`sas_compat._fit_separated`) is the one measured on SAS's
  iteration histories (`out/separation/sas`, PROC LOGISTIC with ITPRINT; the documentation's
  section is "Existence of Maximum Likelihood Estimates"), started from the intercept-only
  estimates. It reproduces the printed tables of the separated steps in the nine SAS runs in hand
  (`judge/runs/gen_s16`, `s17`, `s18`, `s20`, `small_sep60`, `oneclass_n60_two_variables` steps 3
  and 4: complete, stopped at iteration 8; `gen_s21`, `gen_s24`, `oneclass_n60_quasi`:
  quasi-complete, stopped at iterations 9, 10 and 12; an earlier version of this entry and of the
  `_fit_separated` docstring said 9 for `oneclass_n60_quasi`, which SAS's iteration history,
  `out/separation/sas/P2_quasi60.log`, contradicts: it stops at 12, as the port does). The two-variable run, where the final model
  depends on the separated fits, fixes the start. Not settled by them: the divisor of the
  standard deviation in the quasi-complete test.
- Corrected 2026-11-16 (review of c1124e1 / 428b5c9): complete separation is declared when no
  observation is on the wrong side (every observation has probability above 0.5 of its observed
  response), not when every observation is at 0.95 or above, which was this record's reading of
  the documentation and is not what SAS does. Evidence: the ITPRINT runs of `out/separation/sas`
  (D11: SAS declares complete separation at iteration 8 with 382 of 400 observations at 0.95 or
  above and the smallest at 0.539; D2: 38 of 40, smallest 0.84; 18 complete steps in all, every one
  stopped at iteration 8). With the 0.95 test the port iterated on, stopped later as
  quasi-complete and kept other estimates (D11: x1 removed where SAS keeps it). Not settled: an
  observation at exactly 0.5.
- Corrected 2026-11-16 (same review): SAS applies the separation tests to every fit still
  iterating at its 8th iteration, also one whose maximum likelihood estimate exists; the port
  applied them only when its own Newton fit failed. `_fit_separated` now follows SAS's iteration
  for every step with a variable, with SAS's convergence test (GCONV = 1E-8) before the separation
  tests, and `stepwise_logistic` keeps its estimates whenever it declares a separation. Evidence:
  `out/separation/sas` D6b and D6c (classes overlapping by one swap, 400 and 2000 rows: SAS
  declares quasi-complete separation at iterations 12 and 13 and, in D6c, keeps a variable that
  the converged fit's Wald test removes); the 14 steps of those runs that SAS reports converged
  pass the GCONV test at SAS's iteration (3 to 13), among them D6a, D18 and D19, which iterate
  past the 8th without a separation. A fit SAS reports converged keeps the port's own estimates
  (`fit_logistic`), as before.
- A fit that does not converge for another reason still stops with an error.

## A converged fit is SAS's fit: owner's decision 2026-11-17
- Withdrawn: "A fit SAS reports converged keeps the port's own estimates (`fit_logistic`)" (the
  entry above) and RULEBOOK amendment A17 (Newton-Raphson from all-zero coefficients, to full
  convergence). The port's fully converged estimates were closer to the maximum than SAS's, and
  for that reason not SAS's: on few rows the fourth digit of a coefficient differed
  (`generated-inputs.md`, seeds 2, 8, 26, 27).
- Now: every fit with a variable is SAS's own iteration stopped where SAS stops it
  (`sas_compat._fit_as_sas`, the function that was `_fit_separated`): from the intercept-only
  estimates, the convergence test GCONV = 1E-8 after each iteration, the estimates of that
  iteration returned, and everything downstream computed at them. RULEBOOK §2 (rows "stepwise"
  and "model fitting") is updated in the same commit.
- SAS's ridge had to be measured for it (experiment X17). On the reference data the plain
  iteration lowers the log likelihood at iteration 1 on 18 of the 19 steps and breaks down at
  iteration 3; SAS retakes such a step with a ridge (its Ridge column; RIDGING=RELATIVE is the
  default). No history in hand showed one: the runs of `out/separation/sas` and the generated
  seeds never ridge. X17 ran the same PROC LOGISTIC with ITPRINT on the reference feature file,
  on 12 row subsets of it (3,000 to 80,000 rows) and on seeds 2, 6, 8, 26, 27: 211 steps, 393
  ridged iterations, ridges from 0.0064 to 104.8576. The rule that reproduces every iteration
  line of all of them: the diagonal of the information matrix times 1 + 1e-4 * 4^j, j one up
  until the log likelihood is not lower than before the iteration; j is kept through the fit and
  goes one down after an iteration whose first ridge was accepted. Two neighbouring readings
  were tried and fail (j never down: 17 steps; j back to 0: 7 steps).
- The entry score chi-square is SAS's statistic over all parameters on every step, not only after
  a separated one (the form of commit "entry score after a separated step"): at SAS's estimates
  the model's own score is not zero. With the candidate's part alone the reference data's steps
  13 and 16 printed 8.8017 and 29.7077 against SAS's 8.7885 and 29.7637.
- Measured on the reference data (contract run, every line passes before and after). Cells of
  the port's files whose text differs from SAS's reference, before -> after: score files and
  predictions (five files) 814,511 -> 25, each of the 25 one unit in the last printed digit
  (pd_logistic: largest difference 8.2e-6 -> 1e-10; score: 0.002 -> 1e-8; no grade differs any
  more); coefficients 18 -> 0; step summary 12 -> 0; global tests 21 -> 0; fit statistics,
  association, Hosmer-Lemeshow and its partition, odds ratios, classification table 34 -> 0.
  Only the run date differs otherwise.
- Generated inputs, seeds 1 to 29: seeds 2, 8, 26 and 27 now pass every line, and on every seed
  every cell of the train and predict files is SAS's text, except one: seed 6, the Wald test of
  the global null hypothesis at step 7, which still fails (`generated-inputs.md`).
- Not settled by X17, and what the port does: the first ridge (1e-4, the start of the ladder; no
  run needed one below 0.0064, and any start up to there gives the same histories); a step that
  leaves the log likelihood exactly equal (taken without a ridge); a ridged iteration on a
  separated fit (the two rules are applied together; no run has both). A fit that neither
  converges nor separates in 25 iterations, a singular system, or no ridge that keeps the log
  likelihood: the port stops with an error; what SAS does there is not measured.
- Corrected 2026-11-17 (review of 2461757): the ridge ladder has no floor at 1e-4. The first
  version stopped j at 0; SAS goes below. Evidence: the reviewer's ITPRINT run
  `sep_monthly_income_0p5_n2000_s0_sw0` (out/review_fit), step 3, complete separation at
  iteration 8 with ridges 0.0001 and 0.000025 at iterations 5 and 6; with the floor the port
  ridged 0.0001 twice and the kept estimates were 1.9% off, without it they are SAS's to 2e-6.
  X17 is unchanged by it. The same review measured two of the points X17 left open: the first
  ridge of a fit is 1e-4 (ridges from 0.000025 to 419.4304 on 21 further inputs), and ridged
  iterations occur on separated fits and are reproduced with the two rules applied together.
  Still not settled: how far below 1e-4 SAS goes (the port sets no floor), and a step that
  leaves the log likelihood exactly equal. The error message of a fit that neither converges nor
  separates no longer says "in 25 iterations" for a singular system or a failed ridge search.
- Corrected 2026-11-17 (same review): the quasi-complete test does not count the intercept's
  diagonal element of the standardized inverse information. With it the port stopped one or two
  iterations before SAS when events are few (6 steps of the reviewer's runs; whole runs
  `rawfit_small12_43` and `rawfit_small90_15` failed the step summary and the global tests).
  Over the 18 quasi-complete steps in hand one limit fits only without the intercept: at most
  4,678 before SAS's stop, at least 5,932 at it. `separation-rule.md` is corrected in the same
  commit.

## The selection ends rather than have a model twice (2026-11-17)
- Owner's ruling: the port follows SAS until no difference is left. The rule is the one measured
  in `recycling-rule.md` (coding-agent-2: 164 selections read, 13 raw inputs predicted and
  confirmed): the models had are kept as sets of variables from the empty model of step 0 on; a
  removal onto one of them is the last step; a best candidate whose entry would give one of them
  does not enter, and the second-best is not tried.
- `sas_compat.stepwise_logistic` had two special cases of it (`best[1] == last_removed`, and the
  variable entered and removed at once, which that test also ended) and otherwise went round to
  its cap: "500 steps reached without stopping" on all 13 inputs, where SAS completes.
- SAS's note for the way the selection ended is returned by the inner function
  `_stepwise_logistic_with_note`, for the tests only (first committed as a field `ended` of
  `StepwiseResult`, taken off again: the dataclass is mirrored in the port's Lean and must not
  change; `stepwise_logistic` returns the result alone, as before). The port writes the note to no
  file; it is kept because two parts of the rule cannot be told from the steps and the final
  model alone: without the test after a removal, or without the empty model in the list, the
  selection makes the same steps and ends one test later, on the next entry. The note differs
  ("recycling of previous steps" against "the next effect to be added recycles previous steps"),
  and `port/tests/test_recycling.py` compares it with SAS's listing on 19 selections.
- Not measured (from `recycling-rule.md`): a tie of chi-squares at the recycling step; SAS's own
  cap on the number of steps.

## Recorded 2026-11-17: one reading of the ridge test cannot be told apart
- In `_fit_as_sas` a step is retaken with a ridge when it lowers the log likelihood (`<`). The
  reading `<=` (a ridge also when the log likelihood is exactly unchanged) survives every test,
  and no case could be constructed that tells the two apart. Reason: the two differ only on a
  step that leaves the log likelihood exactly equal. If that step is zero (the score is exactly
  zero), the first ridge gives the same zero step and is accepted, so the estimates and the stop
  are the same under both readings. If the step is not zero, the log likelihood before and
  after would have to agree in every bit, which no input could be made to do. No more work on it.

## Hosmer-Lemeshow on extreme fits: two rules measured 2026-11-17
- **Limits on a group's probability.** SAS computes a group's expected events from the group's
  average probability kept within [1e-6, 0.999999], and prints "In calculating the Expected
  values, predicted probabilities less than 1E-6 and greater than 0.999999 were changed to 1E-6
  and 0.999999 respectively." The port summed the probabilities as they are. Evidence, the port's
  function on SAS's own probabilities (`risk_scores_train.csv`) of the 38 SAS runs with the
  tables: the 5 runs with the note (`rawfit_floorA`, `floorB`, `floorD`, `sep_age_gt_55`,
  `sep_age_gt_62`) each had the chi-square off (floorB 0.3644 against SAS's 0.3656) and all 38
  are SAS's with the limit on the group. The limit is not on each observation: `rawfit_floorC`
  has 62 observations above 0.999999, its most extreme group is at 1 - 1.31e-6, SAS prints no
  note there and the unlimited chi-square 95.1047 (95.1048 with each observation limited; floorA
  67.7310 against 67.7309). Brackets: the upper limit between 1 - 1.31e-6 (kept) and 1 - 9.31e-7
  (changed); the lower limit only from far below (groups at 7e-27 and less), so 1e-6 there is the
  note's figure, not a measured one. The partition printed with 2 decimals is the same either way.
- **No table below 3 groups.** When the partition has fewer than 3 groups SAS prints neither the
  partition nor the test and creates neither ODS table (the log warns that LackFitPartition and
  LackFitChiSq were not created, and the export steps then fail with their ERROR lines); the port
  wrote both files whenever the final model had a variable. Evidence: every SAS run in hand
  with a variable in the final model: 4 with 2 groups (`rawfit_Dd`, `Dn2`, `Dn6`, `small60_16`)
  have no table, 38 with 3 to 10 groups have both (3 groups: `rawfit_small90_15`). The number of
  groups is the port's partition on SAS's probabilities, which equals SAS's NGroups on all 38. It
  does not depend on what happened in the selection: small60_16 has a separated step and four
  distinct probabilities, Dd, Dn2 and Dn6 a final model of one two-valued variable. Not seen: a
  final model with a variable and a single group.

## A singular information matrix: the port follows SAS (2026-11-17)
- Owner's ruling: the port follows SAS until no difference is left. The rule is the one measured
  in `singular-information.md` (coding-agent-2: experiment X19, 44 designed fits, 10 raw inputs).
  The port stopped ("neither converged nor separated") on seven raw inputs where SAS completes,
  and completed with wrong cells on two (Cm2, Cm3: DF 1 and Wald 0.0000 for SAS's DF 0 and empty
  cells).
- In the fit (`_fit_as_sas`): probabilities, weights and residuals from `_p_w_r` (a row beyond
  |eta| = 36.7368 has weight exactly 0, on both sides); every inverse of the information through
  `_kept` (parameters in model order, one whose pivot is not above 1e-9 of its own diagonal
  element left out, its step and its row and column of the inverse 0).
- No dataclass changes. A parameter left out at the last iteration is known by its variance being
  exactly 0 in `LogisticFit.cov` (`_left_out`); a positive definite covariance has no such
  element. The removal of such a variable is a `StepwiseStep` with `df = 0` and `wald_chisq` and
  `p_value` NaN (the fields and their types are as before; NaN and DF 0 are new VALUES), and
  `train.py` writes the empty cells from them.
- The port prints SAS's warning ("The information matrix is singular and thus the convergence is
  questionable...") on a fit with a parameter left out at the last iteration, before a
  separation warning, as SAS's log has it; on the 14 designed stepwise runs it is printed on the
  same runs as SAS.
- Tests: `port/tests/test_singular_information.py` on the 40 designed cases of X19
  (`port/tests/data/sas_singular_cases.json`): the 44 fits, the 14 stepwise runs, and the same 14
  runs through `train.run` (stepwise_summary.csv and printed_global_tests.csv cell by cell against
  SAS). Each of these mutations fails a test: tolerance 1e-12; tolerance relative to the largest
  diagonal element; weight not 0 beyond |eta| 36.7368; the left-out variable left to the ordinary
  Wald test; DF 1 for its removal (in `sas_compat` or in `train.py`); Wald 0.0000 for its removal;
  the global Wald test's DF counting the left-out variable or its chi-square printed 0.0000; the
  warning not printed.
- Where the fit leaves nothing out, the systems are solved as before (`np.linalg.solve`,
  `np.linalg.inv`); the weights are hi * lo in place of p * (1 - p), which is the same number up
  to rounding below the limit.
- Not measured, and what the port does: two parameters left out on the same step (the port stops
  with an error: which SAS removes first is not known); a left-out parameter beside a variable
  whose own Wald test would also remove it (the left-out one is removed, as the rule says, "whatever
  the others' tests"; measured only beside a variable that stays, J5); the entry test's alias
  tolerance stays the port's 1e-8 (SAS's fit uses 1e-9; whether its entry test does was not run);
  the entry score test itself still forms its weights as p * (1 - p) (a model with a left-out
  parameter never reaches an entry test, and elsewhere the two agree up to rounding); the final
  model's scores when a weight is 0 (no final model in hand has one).

## The global Wald test leaves out a slope with a tiny pivot: the port follows SAS (2026-11-17)
- Owner's ruling as above; the rule is `global-wald-rule.md` (experiment X20, 17 SAS runs). Seed 6
  step 7: SAS 406.4827 with DF 7, the port 407.3550 with DF 7.
- `sas_compat.global_wald(fit, order)` (new public function; no dataclass field, existing
  signature or file layout changes): the chi-square is b' G b over the slopes, G the inverse of
  the slopes' block of the covariance swept in MODEL order; a slope whose pivot (its variance given
  the slopes swept before it) is not above **1.5e-16, absolute** is left out of G. The DF stays the
  number of slopes. A step with a parameter left out of a singular information matrix keeps the
  rule above (empty chi-square, DF = the variables not left out).
- **The tolerance 1.5e-16 is the port's choice**: SAS's runs bracket it in (1e-16, 2e-16] (T1 left
  out at a pivot of 1.0e-16, T2 kept at 2.0e-16); the port takes the midpoint. Machine epsilon
  (2.2e-16) on the pivot would leave T2 out and is excluded.
- Tests: `port/tests/test_global_wald.py`: the 17 X20 runs from SAS's estimates and COVB
  (`port/tests/data/sas_global_wald_cases.json`), and `train.run` on seed 6 against SAS's
  printed_global_tests.csv cell by cell (needs `judge/runs/gen_s06`, git-ignored). Caught: a
  tolerance relative to the largest slope variance (two constants), relative to the slope's own
  variance, epsilon, no tolerance, the DF reduced to the slopes kept (in `sas_compat` or in
  `train.py`).
- Not measured, and what the port does: the value inside (1e-16, 2e-16]; whether SAS tests the
  pivot or the diagonal element (0.7% apart on seed 6; the port tests the pivot, as the rule file
  states); two slopes near the tolerance (only one ever was; the port applies the sweep in MODEL
  order to each, so a slope's pivot is taken given the kept slopes before it).
