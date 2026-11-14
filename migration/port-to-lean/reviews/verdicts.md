# Review verdicts (orchestrator; a third ruling only where the two reviewers disagree)

## B4 (ROC / association) — reviews B4_r1.md, B4_r2.md
- DEFECT: none (302 + 264 + 17 exact cases, 0 differences). Both reviewers agree.
- RULE (form, both reviewers): `def:Z975` has no trailer / short header; trailer spelling differs
  between units (`confidence=high` vs `confidence=[high]`). CONFIRMED as form findings, WAIVED:
  re-submitting an accepted dependency clears its dependents, and the value is correct. Rule
  clarified in amendment batch 2 (B9): trailer is `-- PORT STATUS: confidence=high todos=0`;
  precondition items carry no trailer.
- PRECOND (both): `_pairs_precond` excludes String / Date columns on which Python runs.
  CONFIRMED as a recorded limit (no in-scope caller passes one); no change.
- NOTE: stale inventory rows (sas_compat L848, L851/852, L890, L901) — inventory to be corrected.
- Fixer: nothing to fix.

## B3 (merge / rank) — B3_r1.md (r2 pending)
- F1 DEFECT `proc_rank_apply_groups` for k < 0 (group minima not sorted): CONFIRMED -> fixer: add
  `0 ≤ k` to `def:proc_rank_apply_groups_precond`.
- F2 PRECOND `proc_rank_groups_precond` vacuous for empty/all-null x with huge k: CONFIRMED ->
  fixer: state the bound on k independently of x.
- F3 PRECOND `merge_one_to_one_precond` excludes padding a Null column: CONFIRMED, fixed in the
  prelude at the next prelude batch (amendment B5).
- F4 NOTE zero-width frames with height: recorded limit (amendment B10).

## B3 — B3_r2.md (second reviewer)
- Same DEFECT (k < 0) found independently: CONFIRMED twice. Fixer: both precondition fixes
  accepted (`0 ≤ k`; finiteness of the cast of k); body untouched; stale comment "lo is sorted"
  left (editing an accepted unit clears its dependents) — recorded.
- `_ratio` beyond 2^53: recorded limit.

## B1 (plumbing / comparisons / sas_round / confusion_metrics) — B1_r1.md, B1_r2.md
- DEFECT: none (about 1,100 + 275 exact cases). Both reviewers agree.
- PRECOND (both): `flag` on a non-Boolean argument, comparisons / `sas_round` on String operands:
  CONFIRMED, resolved by rule (amendment B12): the dtype requirement is stated by the unit that
  evaluates the expression. No call site in the package passes such an argument. No fixer.
- PRECOND (r1): `confusion_metrics_precond` excludes Boolean / Null-dtype columns on which Python
  runs: CONFIRMED as a narrowing; to be annotated when the item is next touched.
- NOTE: `_has_bare_column` has no `α` and uses `where` helpers: accepted (the recursion over the
  nested inductive does not go through otherwise).

## B2 (div / sas_* / sql_*) — B2_r1.md (single reviewer, DEV-009)
- DEFECT: none (163/163 call-site cases incl. 3000-row sums and means, to the last bit).
- NOTES 1–5 (aggregate or non-aggregated operand of a helper inside `agg`, Boolean input of
  `sql_sum`, String columns parsed by polars casts, `sas_log(lit(None))`): none reached by the
  package; recorded limits (amendment C1). No fixer.

## B5 (chi2_sf / LogisticFit / _expit / _hl_groups / hosmer_lemeshow / classification_table) — B5_r1.md, B5_r2.md
- DEFECT (r1): `classification_table` on y sums beyond 2^53 inside the precondition; PRECOND (r1):
  same gap in `hosmer_lemeshow` (Int64 overflow raise). CONFIRMED (reproducers) -> fixer
  (`reviews/B5_confirmed.md`), preconditions only. r2 (fitted real data, 118 values) found no
  defect and does not contradict.
- `_hl_groups`: 39,000 evaluated cases + 105,035 simulated: Float comparison under R-F2I never
  differs from Python's exact integer comparison inside the precondition.
- Recorded exp difference (r2 N1): `Float.exp` on the evaluation server vs numpy `exp` differ by
  1 ulp on 2 of 200 arguments of the last `_expit` (Lean's value is the correctly rounded one);
  the classification table is still equal. Recorded, not chased (PROMPT.md).

## B6 (metrics run) — B6_r1.md
- DEFECT: none inside the recorded limits (450/456; the 6 differences are the signed-zero limit
  of `max` on zeros of both signs: a pd of -0.0). Coverage of every statement confirmed.
- RULE (form): missing `TODO(port): F2I` marks on some sites, one unmarked narrowing, a helper
  declaration shared with a precondition: CONFIRMED as form, WAIVED (DEV-010).

## B7 / B8 (feature engineering, predict runs) — B7B8_r1.md
- Code faithful (100/100). PRECOND F1–F3 CONFIRMED -> fixer (`reviews/B7B8_confirmed.md`).
- F4 (`full` passed to 2–3 operand reductions in B7, literal `true` in B8): form only, value
  cannot differ (checked): WAIVED.
- F5 (position of parameters that replace a Python path parameter): rule C2 queued; `run_py_py`
  to be reordered after the end-to-end review finishes.

## Runs, reviewer 2 (end to end, real data) — RUNS_r2.md
- 40 whole-run evaluations (12 feature engineering, 12 predict, 16 metrics), 198 output tables:
  190 identical; the 8 that differ are ONE value: `exp(3.5785111395443048)` in
  `predict_run_06_score` (row id 34475) is 1 ulp apart between Lean's runtime (correctly rounded)
  and polars; replacing that single result in the real Python reproduces Lean's tables exactly.
  Recorded, not chased (PROMPT.md). No float sum, mean or median differs. No DEFECT, no PRECOND.
- Fixers: B7/B8 preconditions (join suffix clash, `median_income` kind, narrowing comments) and
  B5 preconditions (bounds on the sums of y) applied and accepted; 146/146 formalized.

## B9 (train run) — B9_r1.md, B9_r2.md
- DEFECT: none. r1: full statement coverage, 388 own values over steps 01–15, 0 differences.
  r2: four new samples (60/30, 90/40, two with planted nulls; stepwise paths of 3, 6, 4, 2 steps
  incl. removals; an intercept-only final model), 4,131 values, 0 differences; no exp/log
  last-bit difference.
- PRECOND (r1): shapes of the step fits (`cov` square of the size of `beta`) unconstrained while
  `np.linalg.solve` raises: CONFIRMED -> fixer (`reviews/B9_confirmed.md`), with narrowing
  comments and frame wording.
- RULE (form): `getF` on Int64 columns in steps 07/08, trailer counts: WAIVED (DEV-010).
- NOTE (r2): a final model without effects writes a header-only printed_odds_ratios.csv; the
  Lean returns `[]` (zero-row tables: recorded limit, §6).

## B2, second reviewer (2026-11-11, `reviews/B2_r2.md`) — 110 frame cases, 163,108 cells
- Unit texts: faithful, no finding on any of the 10 units.
- DEFECT F1 (prelude, sorted-flag group key): CONFIRMED as a model limit, not reachable in the
  package -> recorded limit (RULEBOOK §6, amendment E1). Prelude not edited.
- DEFECT F2 (1-ulp `exp`/`log` between the Lean evaluator and polars): CONFIRMED, outside the
  statements (`RealLike.exp`/`log` are abstract) -> recorded (E2); receipts annotated.
- PRECOND F3 (`sum_horizontal`, 9 or more operands): CONFIRMED, not reached (the package uses at
  most 5) -> recorded limit (E3); precondition pending the user's decision.
- RULE F4 (trailer on three precondition items): WAIVED (DEV-010).
