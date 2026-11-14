# Round 3: after the code changes

`informal-spec.md` in this folder is now version 2.1. Read its header, the changes in sections 1
and 2 (the count link, the row bound, the cell guarantees of step frames), and section 9, which
is your work list. `PROMPT.md` and `ROUND2.md` still hold: contracts over the real numbers, the
judge on, text first, never touching a `def:` item, no local Lean, not even a scratch copy of a
tool result.

## What happened since round 2

- The Python code was changed on your findings P1 to P9, and the PSI floor (D1) was changed to
  `min(1e-4, 0.5 / n_train, 0.5 / n_valid)`. The Python translator has translated the changed
  units again; `../python/credit_risk/` holds the new code.
- The SAS translation's ROC tie constant was corrected from new SAS experiments
  (`../sas/experiments/x07_roc_ties.*`, `x08_roceps_boundary.*`).
- You did not make these changes and must not adjust them. If a changed definition looks wrong
  against its source, report it.

## What to do

1. `get_status` first: list the contracts that lost their proof, and the items that changed.
   Check that every changed `def:` item is one section 9 gives a reason for; report any other.
2. Re-prove what lost its proof. For the contracts section 9 expects to change verdict, the text
   stays as it is: prove the contract, and remove its negation item. If one of them still fails,
   that is a finding: keep the disproof, with the new witness.
3. Restate the contracts section 9 lists as restated.
4. Do not touch a contract that still has its proof.

## Report and findings

`report-round3.md`: per contract touched, the result; a table of the fourteen stage files (proved,
disproved by which finding, open); the verdicts that changed and those that were expected to and
did not; counts from `get_status`.

Rewrite `findings-for-code.md` for the code as it now stands, in the same format: only what is
disproved today. Keep the `shared-intent-failure` entries that still hold, and state plainly if
no `port-differs-from-sas` entry is left.
