# Stress-test amendment queue (prompt 03, round 1)

Proposed rulebook changes found by the pilot (implementers, reviewers, fixers) and the bakeoff
diff inspector. Under the user's standing instruction (2026-11-05), the orchestrator applies
them at the end of round 1 and records the decision.

| ID | Rule | Change | Evidence | What goes wrong today |
|---|---|---|---|---|
| S1 | §2 `exp(x)` | `sas_compat.sas_exp(x)`: overflow (x > ~709.78) → **missing**, as SAS's exp gives missing (+ note) | pilot predict reviewers A and B (both): predict.py:229 | polars `exp` → inf, so pd = 0, score 850, grade A where SAS gives missing pd and grade F (latent: not reached on judged inputs, min eta −124.7) |
| S2 | §2 `input(s, best32.)` / sas_compat.input_best32 | Accept a column already imported as numeric (identity); text → parse | pilot predict reviewer A | a test file whose income column has no 'NA' imports as numeric and `input_best32` would fail (latent) |
| S3 | §6 PORT STATUS trailer | Literal format with no brackets: `# PORT STATUS: confidence=high todos=0` | pilot predict reviewer B | §6 shows `confidence=[high\|medium\|low] todos=[N]`; implementers copy the brackets |
| S4 | §2 sas_compat API conventions | The rulebook (or the module docstrings, which the rulebook cites) fixes the procedure helpers' return conventions: `LogisticFit.names[0]='Intercept'`, `loglik` = log-likelihood, Association percents in percent units, `hosmer_lemeshow` / `classification_table` return the reference files' columns as numbers | pilot train implementer (5 ambiguities) | each translator guesses the column names and units |
| S5 | §2 one-to-one merge (A6) | Add `sas_compat.merge_one_to_one(*frames)` (pad shorter frames with nulls, `horizontal_extend`), so no translation writes a private copy | pilot metrics implementer wrote a private `_merge_one_to_one` (§4: no translation defines its own helper) | duplicated helper logic per file |

## Arbiter rulings (single-reviewer findings), pilot predict
- A-02 (input_best32 on a numeric column): confirmed, as S2.
- B-03 (trailer brackets): confirmed, as S3.
- B-04 (`output_dir.mkdir`): not confirmed. It is harmless, and SAS writes into an existing folder.

## From pilot train reviewer A
| ID | Rule | Change | Evidence | What goes wrong today |
|---|---|---|---|---|
| S6 | inventory: printed_fit_statistics.csv vs printed_association.csv rows | InterceptOnly is rendered ONLY by `sas_compat.sas_d12_3` (inventory fix: the fit-statistics row must not prescribe `round()`) | train-A A1; inventory rows for printed_fit_statistics.csv and printed_association.csv | two mappings for one D12.3 cell; identical only because every reachable value is ≥ 1e4 |
| S7 | §2 ODS tables (A19/A20) + inventory rows | Every pre-rendered numeric column uses the STORED format width from train.sas.log: chi-square 10.4, HL expected 8.2, ctable 5.3/5.1 (inventory rows must name them; a `sas_compat.fmt_wd(x, w, d)` call with those widths) | train-A A2 | 12.4/12.2/8.3/8.1 give the same text today; a chi-square ≥ 1e5 would print differently |
| S8 | §2 stepwise (A5) | If nothing enters at step 1, SAS still fits, stores and exports the intercept-only model; `stepwise_logistic` returns it as `final` and train proceeds | train-A A4 | the port raises RuntimeError (latent on the fixed train input) |

## From pilot train reviewer B (+ arbiter rulings)
| ID | Rule | Change | Evidence | What goes wrong today |
|---|---|---|---|---|
| S9 | §0 structure-preserving | Two DATA steps with the same logic stay two code blocks at their own positions, with literal names. A shared Python function only exists where SAS has a `%macro` (A23). Deduplication is post-parity (prompt 06) | train-B B01/B02: `_confusion_metrics` and `_score_columns` merged train.sas:118-139/:180-201 and :213-244/:247-275 | the structure stops mirroring the source; review and diff by line become harder; silently does prompt 06's job |

Arbiter rulings, train (single-reviewer findings): B01/B02 confirmed (S9); B03 (`# pyright: ignore`, §3) confirmed; A4 (nothing enters) confirmed as a TODO pointing to S8; A9 (one listing-only comment per PROC) confirmed.

## From pilot metrics reviewer A
| ID | Rule | Change | Evidence | What goes wrong today |
|---|---|---|---|---|
| S10 | §2 PROC SQL aggregates | SQL `sum/mean/min/max` over ZERO rows (or all missing) → **missing**: `sas_compat.sql_sum(expr)` = `pl.when(expr.count() > 0).then(expr.sum())`, and the same for the others | metrics-A latent, metrics_calculation.py:299 (PSI total over an empty inner join) | polars `.sum()` over 0 rows = 0.0, so PSI prints `0.0000` where SAS prints an empty field (latent: needs train and validation bins with no shared value) |
| S11 | inventory: PSI_interpretation (S320, S321) | classify the PSI operand: MISSING_NULLABLE once S10 applies (PSI can be missing) → helpers | metrics-A nit | A2 cannot be applied to an unclassified operand |

## From the orchestrator's pilot judge run (outside the loop)
| ID | Rule | Change | Evidence | What goes wrong today |
|---|---|---|---|---|
| S12 | §4 stage entry points | `run()` creates `output_dir` (`mkdir(parents=True, exist_ok=True)`) before writing; `write_sas_csv` also creates the parent folder | pilot metrics crashed with FileNotFoundError on a fresh output folder; train and predict happened to mkdir | a stage fails on a fresh output folder. This reverses the arbiter's ruling on predict B-04, which was wrong |
