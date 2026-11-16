# Informal specification, version 3 (DRAFT): the port equals the corrected SAS

Draft of 2026-11-16, by the prover, for the lead's review. **It is not in force**: version 2.3
(`informal-spec.md`) stays the text of record until the lead replaces it, and nothing below is on
a blueprint. No item may be stated from this draft before the requirements change of ruling G54
has gone through and the owner has refreshed the profiles (SAS, then port). This file holds no
Lean.

Why a version 3. Version 2.3 compared each Python unit with a SAS unit on "well-formed" frames,
with flags and with a part (b) off the domain. Since then: the SAS program was corrected and
verified against 26 documented requirements on valid input (signed off 2026-11-16); the port was
brought back in line with it; the flags are gone; ruling G53 limits every claim to valid input.
The claim is now stated on the interface the requirements use, `CreditRisk.Pipeline`, so that the
requirements can be carried over to the port (playbook stage 6).

Rulings built in: G53, G54, G55. Decisions D1 to D9 of `plan-after-verification.md` are all
decided (2026-11-16): D1 and D2 by the owner's rulings G55 and G54; D3 to D9 by the lead as
recommended, D7 with the owner's answer (the 84 cleared theorems may be removed; Judging stays
off on `5365851c`, so the match of Lean and text rests on the reviews). The marks `[D3]` to
`[D9]` now show where each decision is applied.

## 1. Form of every contract

The contracts are items of the port blueprint `py-credit-risk-port` (`5365851c`). The SAS and
requirement declarations they name come through the profile from `sas-credit-risk-spec`
(`3f5df696`) and `credit-risk-requirements` (`006ff04c`).

**The three definitions** all contracts rest on (`definitions-v3-draft.md`): `pyPipeline py`, the
port as a pipeline; `PyLinks py`, what the port's out-of-scope code is taken to do; `Paired py
sas`, how the port's parameters relate to the SAS parameters.

**The form.** "At the real numbers: for all port parameters `py` and SAS parameters `sas` with
`PyLinks py` and `Paired py sas`, for every raw training table, raw test table and seed that are
valid input (`CreditRisk.InputOK`), this step of `pyPipeline py` returns what the same step of
`sasPipeline sas` returns, on the arguments named." "Returns what" includes returning nothing:
if the SAS step stops, so does the port's, and conversely.

**Hypotheses.** `PyLinks py`, `Paired py sas`, `InputOK`, and, where a contract names arguments
that a run reaches, the equations saying they were reached. No other hypothesis may be added. In
particular no precondition of a port unit, no `wf_` domain, and no clause of `SasLinks` beyond
those `Paired` restates. A contract that cannot be proved or disproved as written is left open
and reported.

**Read-backs (ruling G55).** The files passed between scripts are read by one function shared by
both sides and otherwise free (`Paired` 4, `PyLinks` 8). Every equality contract therefore holds
both when hand-off files are taken at full precision and when they are read as the 12-character
files the programs write.

**Number type.** The reals. Nothing is claimed about `Float`: overflow, NaN, summation order.

**Disproof.** A contract that fails is disproved by its negation, proved with a concrete valid
input and concrete parameters meeting `PyLinks` and `Paired`; the input and one sentence on what
differs go in the negation's text. A checked disproof is a difference: the port changes.

## 2. Equality contracts on the interface

Write P for `pyPipeline py` and S for `sasPipeline sas`.

| # | Output | Statement, under the form of section 1 |
|---|---|---|
| E1 | training feature table | `P.features train seed` and `S.features train seed` both return a pair or both return nothing; when they return pairs, the first tables are equal |
| E2 | validation feature table | when both return pairs, the second tables are equal |
| E3 | the model | for the tables F1, F2 that `S.features train seed` returns: `P.fit F1` is `S.fit F1` |
| E4 | scores | for every model m and every table F of feature shape: `P.score m F` is `S.score m F` |
| E5 | the training scores of the port | for F1 as in E3 and m with `P.fit F1` returning m: the table of `risk_scores_train.csv` that the training chain of the train stage produces (step 04 onward) is `P.score m F1` |
| E6 | test predictions | for F1 as in E3 and m with `S.fit F1` returning m: `P.scoreTest m test train` is `S.scoreTest m test train` |
| E8 | validation summary | for F1, F2, m as above and S1, S2 with `S.score m F1` returning S1 and `S.score m F2` returning S2: `P.metrics S1 S2` and `S.metrics S1 S2` both return tables or both return nothing; when they return tables, the summary tables are equal |
| E9 | KS table | as E8: the KS tables are equal |
| E10 | decile table | as E8: the decile tables are equal |
| E11 | threshold table | as E8: the threshold tables are equal |

(E7 is in section 5.)

*Feature shape* (E4): every row of F has the same column names in the same order, no name twice;
every name of a term of m is among them; every cell is numeric. It is wider than "reached by a
run" on purpose: requirements Q12 and Q13 score a test feature table that no step returns
(section 6). The reviewer of E4 fixes the exact wording against the port's scoring units and the
SAS shape lemma of section 6 before it is stated.

Tables are compared as tables: same rows in the same order, same column names in the same order,
same cells. `[D6]`: no contract is "up to the order of rows"; `Paired` 6 takes the SAS join order
as the identity.

## 3. Faithfulness of the assembly

`pyPipeline` wires `fit` and `score` from step units, because the train stage does the fit and
both scorings in one call. So that the contracts are about the port and not about a paraphrase:

| # | On | Statement |
|---|---|---|
| A1 | `run` | on valid input, under `PyLinks`: when `run` returns files on the imported training table and the split, the tables of its two feature files are the pair `P.features` returns |
| A2 | `run_py_py_py` | when the train stage returns on the two feature tables as read back: the model it returns is `P.fit F1`; its `risk_scores_validation.csv` is `P.score m F2`; its `risk_scores_train.csv` is the table of E5 |
| A3 | `run_py_py` | when the predict stage returns on the arguments `P.scoreTest` gives it: its `test_predictions.csv` is `P.scoreTest m test train` |
| A4 | `run_py` | when the metrics stage returns: its four files are the four tables of `P.metrics S1 S2` |

A1, A3 and A4 hold by the way `pyPipeline` is written and are expected to be short; A2 is the
real one.

## 4. Coverage of the stage preconditions

The Lean of the port has no way to say "the Python raises": its units are total, and a case
where the program raises is excluded by the unit's precondition (RULEBOOK of the port, section
1). A contract of section 2 assumes no precondition, so by itself it does not say the real
stage completes. **The claim for a stage is therefore the pair**: its equality contracts and its
coverage contract. One contract per stage says the port's own stated precondition holds where a
valid run takes it:

| # | On | Statement |
|---|---|---|
| G1 | `run` | on valid input, under `PyLinks`, the precondition of `run` holds of the arguments `P.features` gives it |
| G2 | `run_py_py_py` | likewise for the train stage on the feature tables a valid run returns, read back |
| G3 | `run_py_py` | likewise for the predict stage |
| G4 | `run_py` | likewise for the metrics stage |

`[D3]`: no exception is written into these. Where a valid input falls outside a precondition,
the coverage contract is disproved with that input: a difference, fixed in the port.

Known before proving (rule H13 of the port's RULEBOOK 2.8): **G2 is expected to fail.** A valid
training file of one, two or three rows puts every row in the training set (seven tenths,
rounded up), the fit is a parameter taken to return, and the SAS pipeline produces every result
(`thm:sas_Q27`); the port's train stage raises on a validation file with no row and writes none
of its exports. A header-only test file is not such a case: the port completes (H13 (d)), so G3
is expected to hold there.

The precondition of the train stage also carries conditions on the printed steps
(Hosmer-Lemeshow, classification table) that depend on the numpy parameters: G2 is stated for
the part that concerns the compared files, and the rest is reported as not covered.

## 5. Outputs outside the interface `[D5]`

The playbook asks for one contract per output of the program. Six compared files are not carried
by the interface. Each gets a contract of the old per-file form: on valid input, under `PyLinks`
and `Paired`, the table of the file equals what the composed SAS units give on the same run.

| # | File | SAS units |
|---|---|---|
| F1 | `income_medians.csv` | `income_medians_all`, `income_medians_export` |
| F2 | `kaggle_submission.csv` | `kaggle_submission` |
| F3 | `final_model_output.csv` | `final_model_output` |
| F4 | `model_summary.csv` | `model_summary` |
| F5 | `calibration_plot.csv` | `calibration_data`, `calibration_plot` |
| F6 | `model_performance_metrics.csv` | `model_performance_metrics` |
| E7 | column names of `test_predictions.csv` and `kaggle_submission.csv` | the names and order the SAS units give |

Not given a contract, with the reason: `model_coefficients.csv` and `stepwise_summary.csv` (the
fit is out of scope on both sides and no SAS unit models them); the `printed_*` files (printed
formats); the ROC tables beyond the area.

## 6. Requirements carried over (stage 6)

Stated only after every contract of section 2 is proved.

- **T0, parameters exist.** For every `py` with `PyLinks py` there is `sas` with `Paired py sas`;
  and when the read-backs of `py` are the identity, that `sas` meets `SasLinks`.
- **T1, not empty.** There is a `py` meeting `PyLinks` whose read-backs are the identity.
- **T2, the test feature table has feature shape.** For the SAS pipeline on valid input, the
  feature table that requirements Q12 and Q13 score meets the feature shape of E4. `[D8]`: an
  item of the port blueprint, about SAS units seen through the profile; the signed-off SAS
  blueprint is not touched.
- **Transport, one per requirement.** For each of Q1 to Q16 and Q18 to Q27: if two pipelines
  with the same model type agree as the contracts E1 to E4, E6 and E8 to E11 say, and the
  requirement holds of the second, it holds of the first. These name only `CreditRisk`
  definitions and neither program.
- **The 26 carried requirements.** For each: "For every `py` with `PyLinks py` whose read-backs
  are the identity, requirement Qn holds of `pyPipeline py`. The hand-off files are taken at
  full precision (ruling G55), as in the verification of the SAS program; what the 12-character
  files lose between scripts is outside this statement." Proved from `thm:sas_Qn`, the equality
  contracts, T0 and the transport lemma, and from nothing about the code. If a proof needs an
  argument about the port, the contracts or the conditions do not line up: that is a finding.

## 7. What stands from version 2.3, and what is withdrawn

- **Stand, as proved** (46 items, checked after the re-base, plan section 0.1): the helper
  contracts H1 to H11 and H13, and the step contracts S2, S3, S6, S7, S8, S9, S10, S13, S16,
  S20, S21b, S22b, S25, S28, with `predict_run_03_cleaned_S31` and C3. They are lemmas for the
  proofs of section 2 where their hypotheses can be met on a valid run; they are no longer the
  claim.
- **Stands, as a recorded fact about the port**: C4 and its proved negation (the fit mask also
  drops a row with a missing outcome). No effect on valid input.
- **Withdrawn** (the 84 items the update cleared; their removal was allowed by the owner on 2026-11-16, `[D7]`; record in `reports/removed-2026-11-16.md`):
  the stage contracts ST1 to ST4 and witnesses W1 to W4 (replaced by sections 2 to 5); the flag
  contracts F1 to F4 of version 2.3 (the flags are gone); every part (b) and the `wf_` domains
  (G53); the intent contracts I1 to I8 (intent is now the 26 requirements); S31 and I8 (now
  requirement Q12); the cleared step contracts, which return only as lemmas inside the proofs or
  as `lem:` items shared by a group; H12 returns as a lemma if F4 is kept; C2 is dropped (a
  printed column).

## 8. How the work is divided

Groups A (E1, E2, A1, G1), B (E3, E4, E5, A2, G2), C (E6, E7, A3, G3), D (E8 to E11, A4, G4) in
parallel; E (section 6) stated after A to D are stated; F (section 5) last. Every statement is
checked against this text by a teammate who did not write it before its proof is started. Shared
lemmas are `lem:` items (plan section 4.3).

## 9. Not covered

- The fit: stepwise selection and the optimiser, on both sides a parameter. A fit that does not
  return is outside both models.
- CSV reading itself: the importers and read-backs are parameters, described by `PyLinks` from
  observed runs (RULEBOOK 2.8), not modelled.
- What the 12-character and 15-digit hand-off files lose, for the carried requirements (G55).
  The equality contracts do cover it.
- Printed formats, the `printed_*` files, the coefficient and stepwise files.
- Any input that is not valid (G53).
- Raw files of 10^8 rows or more (ruling G56): the 8-character count round trip is taken as
  exact on both sides (`PyLinks` 10); beyond that size neither program counts exactly. Every
  report states this limit.
- Floating-point behaviour.

## 10. Owed before anything is stated

1. The requirements change of G54 formalised, and the owner's refresh of both profiles; then the
   profile check again, including the state of the 46 kept theorems.
2. (Done 2026-11-16: decisions D3 to D9 are settled.)
3. (Done 2026-11-16: the runs are rules H8 to H14 of the port's RULEBOOK 2.8; each clause of
   `PyLinks` cites its rule.) D4 is closed by ruling G56 (owner, 2026-11-16): counts are taken as exact on
   both sides and the claims hold for raw files of fewer than 10^8 rows. Open: the port's train
   stage on an empty validation set (H13), to be fixed in the port before contracts are stated.
4. Review of the three definitions: wiring, and each condition against the port in both
   directions.
