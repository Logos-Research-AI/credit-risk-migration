# When SAS's stepwise selection ends on a model it has already had (2026-11-17)

Measured for the owner's decision of 2026-11-17: the port follows SAS on every small input where SAS
completes. Nothing under `port/` or `legacy/` was changed for this file.

## The rule

PROC LOGISTIC `selection=stepwise` keeps the models it has had, starting with the model without a
variable (step 0). A model is the set of its variables; the order of entry does not matter.

1. **After a removal**, if the model now is one it has had before, the selection ends. The removal is a
   step like any other: it is in the step summary, it has its fit statistics and tests, and the model
   after it is the final model. SAS's note is
   "Model building terminates because the last effect entered is removed by the Wald statistic
   criterion" when the variable removed is the one entered at the step before, and
   "Model building terminates because of recycling of previous steps" otherwise.
2. **Before an entry**, if the model with the best candidate added is one it has had before, the
   selection ends without entering it. No step is added, and the model as it stands is the final
   model. SAS's note is "Model building terminates because the next effect to be added recycles
   previous steps". SAS does not go on to the second-best candidate.
3. Otherwise the selection goes on as before (removal first, then entry; RULEBOOK section 2).

The port as it stands has two special cases of this rule and nothing else: the variable entered and
removed at once (case 1 with the first note), and the best candidate being the variable just removed
(a case of 2). On every other case it goes round until its cap of 500 steps and stops with
`RuntimeError: stepwise_logistic: 500 steps reached without stopping`.

## Evidence

SAS's notes over every stepwise run in hand (`judge/runs/*/train.sas.lst`, `out/*/sas/*.lst`), 164
selections: 72 end with no candidate to enter, 5 with every variable entered, 64 with the first note,
10 with "recycling of previous steps", 13 with "the next effect to be added recycles previous steps".

The rule was written into a scratch copy of the port (`out/review_fit/sim`, the branch `entry-score`
with the ridge floor and the 5000 test corrected, plus the lines under "Smallest fix"). With it the
outcome column of a raw file was searched for each shape. This is possible because SAS's split and its
feature files do not depend on the outcome column (checked on two pairs of runs: same training ids in
the same order, every feature column equal), so the features of the training part are known before the
run. About 24,000 outcome columns were simulated on the rows of nine earlier raw runs: 0.3% end by a
removal onto the empty model, 0.1% by a removal onto another earlier model, 0.4% by a next entry
that is the variable just removed, 0.03% by a next entry that is another variable.

Thirteen raw inputs were then made, the steps predicted, and the whole SAS program run on each
(`judge/runs/rawfit_<name>`). **SAS made the predicted steps, ended at the predicted step with the
predicted note and final model on all thirteen.** `+` enters, `−` removes.

| Input | Raw rows (training) | Steps SAS made | Ends by | Final model |
|---|---|---|---|---|
| `Da` | 42 (30) | log_monthly_income+ monthly_income+ log_monthly_income− monthly_income− | removal onto the empty model | none |
| `Db` | 42 (30) | age+ income_per_dependent+ age− income_per_dependent− | removal onto the empty model | none |
| `Dc` | 85 (60) | flag_recent_late_payments+ num_late_30_59+ flag_recent_late_payments− num_late_30_59− | removal onto the empty model (step 2 quasi-complete) | none |
| `Df` | 171 (120) | flag_low_income+ total_risk_flags+ flag_low_income− total_risk_flags− | removal onto the empty model (step 2 quasi-complete) | none |
| `Dg` | 85 (60) | credit_lines_per_person+ age_category+ credit_lines_per_person− age_category− | removal onto the empty model (step 2 complete) | none |
| `Dd` | 171 (120) | flag_low_income+ financial_health+ age+ financial_health− age− | removal onto the model of step 1 | flag_low_income |
| `De` | 171 (120) | num_real_estate_loans+ MonthlyIncome_missing+ income_per_dependent+ MonthlyIncome_missing− income_per_dependent− | removal onto the model of step 1 | num_real_estate_loans |
| `Dn1` | 42 (30) | credit_lines_per_person+ total_risk_flags+ age_category+ age+ credit_lines_per_person− total_risk_flags− credit_lines_per_person+ | next entry (total_risk_flags) gives the model of step 4; the step before was an entry | age, credit_lines_per_person, age_category |
| `Dn2` | 64 (45) | utilization_debt_interaction+ flag_recent_late_payments+ financial_health+ utilization_debt_interaction− financial_health− | next entry gives the model of step 2; it is not the variable just removed | flag_recent_late_payments |
| `Dn3` | 64 (45) | num_late_60_89+ num_dependents+ credit_util_category+ num_late_60_89− credit_util_category− | same shape | num_dependents |
| `Dn4` | 85 (60) | flag_low_income+ debt_category+ income_per_dependent+ flag_low_income− income_per_dependent− | same shape | debt_category |
| `Dn5` | 128 (90) | Dependents_missing+ num_real_estate_loans+ credit_util_category+ Dependents_missing− credit_util_category− | same shape (two quasi-complete steps) | num_real_estate_loans |
| `Dn6` | 171 (120) | utilization_debt_interaction+ flag_low_income+ log_monthly_income+ utilization_debt_interaction− log_monthly_income− | same shape | flag_low_income |

Three feature files of real feature rows, run with ITPRINT before the rule was stated
(`out/review_fit/sas/small120_41`, `small30_7`, `small90_15`), end the same way, the last after six
steps (A+ B+ A− C+ B− C−) on the empty model: the model compared with is any earlier one, not only
the last few.

What is printed: the files of the train step are those of any other run. With the rule, the scratch
copy equals SAS on every file SAS wrote, through the whole contract (feature engineering, train,
metrics, predict, end to end), on ten of the thirteen inputs. On `Dd`, `Dn2` and `Dn6` every file both
wrote is equal and the port writes the two Hosmer-Lemeshow files where SAS writes none: a separate
difference, not part of this rule (the final model there has one two-valued variable).

The rule changes no other run: on the 70 feature files of `judge/runs` under 5 MB that have a SAS
model, the scratch copy differs from SAS only where the branch already did for another reason.

## Failing inputs for the port as it stands

All thirteen. The inputs are in `experiments/x18_small_raw_inputs.json` (row ids of
`legacy/data/cs-training.csv` and the outcome each carries); the script beside it writes the files,
runs SAS and judges a port:

```
python3 migration/legacy-to-port/experiments/x18_small_raw_inputs.py make <dir> Da
cd judge && uv run python ../migration/legacy-to-port/experiments/x18_small_raw_inputs.py judge <dir> Da Db Dc Dd De Df Dg Dn1 Dn2 Dn3 Dn4 Dn5 Dn6 --port <folder holding credit_risk>
```

Branch `entry-score` at 8a1f307: the train step stops on all thirteen with the 500-step error where
SAS completes (`De`, `Dn1`, `Dn3`, `Dn4`, `Dn5` are SAS runs with no ERROR line at all). The smallest
is `Da`, 42 rows.

## Smallest fix

In `sas_compat.stepwise_logistic`, about ten lines (as a patch against the branch with the ridge floor
and the 5000 test corrected: `experiments/x18_recycling_fix.patch`; its `recycled` lines are the
search's bookkeeping and are not needed):

```python
    visited = [frozenset()]                      # before the loop: the models the selection has had
    ...
                model.remove(best_w[1])          # removal branch, after the step is recorded
                ...
                if frozenset(model) in visited:  # rule 1: the removal is the last step
                    break
                visited.append(frozenset(model))
                continue
    ...
        if best is None or chi2_sf(best[0], 1) >= slentry:   # `or best[1] == last_removed` goes: rule 2 covers it
            break
        if frozenset([*model, best[1]]) in visited:           # rule 2: end without entering
            break
        ...
        model.append(best[1])
        ...
        visited.append(frozenset(model))
```

The 500-step cap can stay as a guard; with the rule it cannot be reached (there are finitely many
models and none is had twice).

## Not measured

- A run whose removal test and entry test would both act on a tie of chi-squares at the recycling
  step.
- SAS's own cap on the number of steps (`MAXSTEP`), which no run reached.
