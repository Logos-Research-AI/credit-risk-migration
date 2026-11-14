# Sign-off gates (run through without stopping, per PROMPT.md)

Each entry: what a sign-off would have reviewed.

## Gate 0b: judge
- Differential evaluation tooling: `migration/mcp_eval.py`, `migration/diffeval.py` (bit-exact
  readback of Lean results), `migration/run_stage.py` (staged SAS runs with HEX16 dumps),
  `migration/run_experiment.py`.
- Comparator validated on planted mismatches: see `migration/diffeval-validation.md`.
- Decision a human would review: experiments are run with `run_experiment.py` because
  `judge/run_sas.py` imports a file that is not in this workspace (DEV-004).

## Gate 1: map and rules
- `migration/manifest.tsv` (56 units), `migration/out-of-scope.tsv`, `migration/RULEBOOK.md`
  (29 behaviour rules, each with evidence), `migration/inventory.tsv` (354 rows),
  `migration/evidence/sas-docs.md` (D1-D15), `experiments/x10`-`x15`.
- Decisions a human would review: DEV-005 (helpers inside code items); the parameters P1-P7;
  restricting ROCAssociation to `ROCModel` and `Area`; Hosmer-Lemeshow limited to the
  partition counts.

## Gate 2: stress test
- `migration/stress-test/report.md`. No rule changed; three rules confirmed load-bearing.

## Gate 3: translation
- `migration/manifest.tsv`: 56 units, all `DefinitionFormalized`; 26 precondition items.
- Six review reports in `migration/reports/`; amendments A1-A10 in `migration/amendments.md`.
- Decisions a human would review: DEV-006 (evaluation helpers and sink dependencies), DEV-007
  (excerpted source for `def:logistic_lackfit`), and that `def:logistic_association` is judged
  against the whole PROC LOGISTIC step: the judge accepted it on three submissions and rejected
  it on two with identical Lean.
- Process deviation: helper-home units and a few small units were written by the orchestrating
  session rather than by a separate implementer; every unit still had two separate reviewers.

## Gate 5/6: differential evaluation
- `migration/diffeval-receipt.md`: about 101,000 cells, zero unexplained differences.

## Last step: intent properties
- `migration/intent-properties.md` (47 properties, not formalised). STOP.
