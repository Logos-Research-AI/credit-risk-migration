# Dependency-map review notes (prompt 01, round 1 — clean)

Two skeptic reviewers (claude-opus-5-5, separate contexts, disjoint halves: train+metrics /
feature_engineering+predict) derived dependencies from source without seeing the map.
Diff vs edges.tsv: 0 missed, 0 invented (5/5 edges confirmed, both directions).
External reads correctly excluded: cs-training.csv (feature_engineering.sas:28), cs-test.csv (predict.sas:27).

Observations that are not edges, carried to the gap inventory (prompt 02):
- metrics_calculation.sas:29,37 imports into work.logit_scored_valid / logit_scored_train, the same
  WORK names train.sas creates (train.sas:86,103,158); the import replaces them. If an import failed,
  metrics would silently run on train's stale tables. Port: metrics reads only its CSV inputs.
- metrics_calculation.sas:28-41 PROC IMPORT has no guessingrows= (default 20), unlike train.sas:31,40.
  Type guessing applies to the risk_scores CSVs (interest_rate is text "5.00%").
- metrics_calculation.sas:75 sorts logit_scored_valid in place; KS (:105-110) depends on that sort and
  on the CSV row order -> stable sort in input order (RULEBOOK §1 row order).
- predict.sas:44-201 duplicates feature_engineering.sas:44-202 (schema coupling only; no runtime edge).
- predict.sas:58-73 imputes test incomes with TEST medians, not training medians (BUG(port)).
- &output_path / &data_path are redefined identically in every program; no macro-variable edge.
