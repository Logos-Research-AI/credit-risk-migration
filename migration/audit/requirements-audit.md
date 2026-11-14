# Audit of the requirements formalisation

Orchestrator, 2026-11-14. Blueprint `credit-risk-requirements`
(`006ff04c-d34c-4a9c-b230-ccd725b1be6f`), 58 items, against `migration/requirements/requirements.md`
draft 3.

## What was checked

I read the accepted Lean statement of 50 of the 58 items and compared each with the requirement
and its rulings: the interface and input conditions (`Pipeline`, `MetricsTables`, `Fitted`,
`TrainOK`, `TestOK`, `InputOK`), `Q27`, `Spec`, both theorem statements, all nine row rules
(`rowQ1` to `rowQ9`), `Q1`, `Q6`, `Q10` to `Q16`, `Q18` to `Q26`, and the notions they use (`num`,
`ageGroup`, `median`, `q1Median`, `outcomeRecorded`, `classProbs`, `confCount`, `auc`, `somersD`,
`ecdf`, `ksStat`, `decileCut`, `psiShare`).

Not read by me: `Q2` to `Q5` and `Q7` to `Q9` (the per-applicant wrappers of row rules I did read;
they have the same shape as `Q6`), and `str`. The workflow's independent reviewers read all of them.

## Result

No statement I read differs from draft 3. In particular:

- Grade bands (`Q18`): edges exactly as rulings G1 and G2, 50 % in E.
- Flags (`rowQ6`): the eight thresholds as documented, on raw value x 100 for the two ratios, 1
  when the condition holds and 0 when it does not.
- Imputation (`rowQ1`, `q1Median`, `ageGroup`): five age groups, group median with the overall
  median as fallback, medians over the whole raw training file; the test set uses the same (`Q12`,
  `Q13`).
- Split (`Q10`): every applicant exactly once, sizes within one applicant of 70 % and 30 %.
- Score (`Q15`, `Q16`), rates as fractions (`Q19`), recommendations (`Q20`).
- Metrics on the validation set with the outcome tied to the raw file (`outcomeRecorded`);
  PSI on nearest-rank training deciles with ties to the lower bin; ten decile rows.
- `Q27`: all steps produce results on good input; no features on a bad training file; no test
  predictions on a bad test file.
- `Spec` is the conjunction of Q1 to Q16 and Q18 to Q27; `consistent` states that some pipeline
  satisfies it.

## Weak points, recorded not fixed

- `Q11` holds of every pipeline: the interface makes the split a function of file and seed.
- `Q3` and `Q21`: the indicator and the prediction are required to be 1 exactly in their case;
  otherwise only "not 1", not 0.
- `Q25` fixes only whether PSI is 0 or positive; `Q26` fixes only the shape of the decile table
  and the capture sum. The documentation defines no more.
- No requirement says the feature files' `age`, late-payment counts or `default_flag` equal the
  raw values; the metrics requirements tie `default_flag` to the raw outcome for the validation
  scores only.
- The consistency witness is artificial (probability = flags / 8, trivial model). It shows the
  requirements do not contradict each other, nothing more.
