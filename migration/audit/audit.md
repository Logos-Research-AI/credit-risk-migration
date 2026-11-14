# Audit of the equivalence pass, 2026-11-13

Auditor: the orchestrating session, which wrote the specification and neither translated nor
proved. Everything was read from the blueprint `py-credit-risk-port` through the Logos tools;
nothing was copied to disk.

## What was checked

| Check | Result |
|---|---|
| Blueprint status | `verification_approved: true`; 316 items, 300 statements formalized, nothing to state or prove, 16 flagged false |
| All 14 stage statements, read in full | Each matches the specification: the right Python stage with all flags off, the right composition of SAS units, only the hypotheses the specification allows, conclusion an equality of the file with the SAS table |
| The 4 stage-input well-formedness definitions | Match section 2: at least one row; exact columns by name, order and kind; row id present and distinct; value ranges where the table carries them |
| The Python preconditions of two stages (`run`, `run_py`) | Structural only: table shape, columns the code reads, and each step's own precondition on the values the stage computes. Nothing in them restricts the result |
| A sample of 8 other contracts (H1, H8, H12, S3(b), S5(b), I1 on, I1 off, F1 frame) | Each matches its specification text. S3(b) and S5(b) assume the Python precondition only |
| The SAS tie constant, from both blueprints | Identical after the profile refresh: 3184525836262887 / 2^78 |
| Local Lean | None in any workspace; one saved tool result with Lean goal text deleted |

## What was not checked

- The other 106 contract statements: their match with the specification rests on the judge and on
  the prover's own reviewers.
- No proof was read. Proofs are machine-checked by the service.
- That no accepted proof uses `axiom` or `sorry` is the prover's statement and the service's
  acceptance; the tool available to the auditor lists direct dependencies only.
- That the 145 original definitions changed only where the code changed is the prover's own audit
  against a server-side dump, repeated each round. The auditor did not repeat it.
- The composition of SAS units in each stage statement was checked against the SAS manifest's
  data flow, not against the `.sas` files line by line.

## Weak points found

1. **Stage hypotheses shown satisfiable by evaluation only.** For all four stages, that some
   input meets every hypothesis was shown by evaluating hand-written Boolean checks at `Float`.
   Round 5 replaces this with four proved witness contracts (W1 to W4).
2. **Three step contracts disproved through the specification** (S12(a), S12(b), S18(b)). Round 5
   restates them.
3. **Stale informal texts on some translator items** (the Lean is current, the displayed source or
   docstring is old): `_pairs`, `roc_association`, the step 02 and 03 definitions, and five others
   listed in the round 3 report. For the Python translator to refresh.

## Conditions attached to the headline result

All fourteen files are proved equal to SAS over the real numbers, on well-formed inputs, flags
off, under:

- `invLink`: PROC LOGISTIC's predicted probability is 1 / (1 + exp(-x)) of the linear predictor
  (three train files). True as mathematics; the open question on the SAS side was only its
  floating-point evaluation.
- `input_best32`: the CSV number conversion equals SAS's (feature and predict files). A later pass.
- Tables of fewer than 10^8 rows (three metrics files).
- The fitted model is the same on both sides (train and predict). The fit is a later pass.
- Nothing is claimed about floating point beyond what each translation's differential evaluation
  against its source showed.
