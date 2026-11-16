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
- The rule for the kept estimates (`sas_compat._fit_separated`) is SAS's documented one (PROC
  LOGISTIC, "Existence of Maximum Likelihood Estimates"), started from the intercept-only
  estimates. It reproduces the printed tables of the separated steps in the nine SAS runs in hand
  (`judge/runs/gen_s16`, `s17`, `s18`, `s20`, `small_sep60`, `oneclass_n60_two_variables` steps 3
  and 4: complete, stopped at iteration 8; `gen_s21`, `gen_s24`, `oneclass_n60_quasi`:
  quasi-complete, stopped at iterations 9, 10 and 9). The two-variable run, where the final model
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
