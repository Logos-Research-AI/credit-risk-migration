# Make the Python port agree with SAS where formal verification found it does not

## What this is for

`port/credit_risk/` is a Python port of the SAS pipeline in this repository. The port passed the
migration's judge (`judge/README.md`): on the judged inputs its outputs match SAS. A formal
verification pass has since compared the port with SAS on **all** inputs, by proof, and found
places where they differ on inputs the judge never exercised. Your job is to act on those
findings.

The findings are in
`migration/proofs/port-equals-legacy/reports/findings-for-code.md`. That file is
your work list. Each entry gives the function, the smallest input that shows the difference, what
SAS gives, what Python gives, and a kind.

Reading that file:

- Its paths are relative to another folder. `python/credit_risk/x.py` is `port/credit_risk/x.py`
  here, and `sas/x.sas` is `legacy/x.sas` here. The code is identical, so its line numbers are valid as
  of commit `143ddf2`; they shift as you edit.
- "SAS rulebook" there means
  `migration/legacy-to-lean/RULEBOOK.md`, written by the
  team that studied SAS's behaviour. You may read it, and `experiments/` and
  `migration/evidence/` next to it, as evidence of what SAS does. It is not this repository's
  `migration/legacy-to-port/RULEBOOK.md`.
- Act only on the sections `port-differs-from-sas`, `fix-defect` and `record-inaccurate`. The
  sections "Specification gaps", "Proved equal to SAS" and "Open" are for someone else.

Do not open any Logos blueprint: the Lean is
not your concern, and the people who translate your code to Lean must see only what the code
does.

## The rule for each kind

- **`port-differs-from-sas`**: change the Python so it gives what SAS gives. SAS is the
  specification and cannot change. Make the change general, not a special case for the witness:
  if a plain comparison is wrong on a missing value, use the `sas_compat` helper, as RULEBOOK §2
  prescribes for a nullable operand. Where the finding states a SAS rule that the `.sas` source
  does not show (the behaviour of a PROC or a function), check the evidence the SAS rulebook
  cites for it. Where that rulebook marks a point as open, or you doubt the rule, settle it by
  running SAS (`judge/run_sas.py`, an experiment under `migration/legacy-to-port/experiments/`) before
  implementing it, and say in your report what you ran. A helper shared by several outputs
  (`_pairs` feeds both the ROC and the association tables) is changed only as far as the
  evidence reaches.
- **`fix-defect`**: there is no SAS behaviour to copy, so the right behaviour is a design
  choice. Do not change the code. In your report, state the defect in one sentence and give two
  or three concrete ways to fix it, with what each does on the finding's input.
- **`record-inaccurate`**: correct the record (`migration/legacy-to-port/post-parity/`, `judge/README.md`,
  comments in `sas_compat.py`). No code change.
- **`shared-intent-failure`**: do **not** change default behaviour. These are bugs inherited from
  SAS, and fixing them changes the model's outputs, which is a business decision. If the entry
  has no flag yet, list it in your report as a candidate for a new off-by-default flag and leave
  the code alone.

## Constraints

- **Parity must hold.** After your changes, `migration/legacy-to-port/parity/run_contract.sh` must pass every
  line with all flags off, exactly as before. None of the findings occurs in the judged data, so
  a judged output that changes means the fix is wrong.
- Follow `migration/legacy-to-port/RULEBOOK.md`. It is read-only: where a fix contradicts a rule (amendment A2
  requires a plain comparison where the inventory says `MISSING_NEVER`), make the fix and queue
  the amendment in `migration/legacy-to-port/rulebook-amendments.md` with the finding's id. Update the affected
  rows of `migration/legacy-to-port/inventory.tsv` the same way.
- Keep the structure: same functions, same steps in the same order, same names. Change only the
  lines a finding requires. The Lean translation mirrors the code line range by line range, and
  every line you move has to be translated again.
- `ruff check`, `ruff format` and `pyright` clean.
- One commit per finding, on the current branch, message starting with the finding's id. Commit
  only when the parity contract passes.

Work through the list without stopping for sign-off. Stop only if a finding cannot be fixed
without changing a judged output, or if SAS, when you run it, does not behave as the finding
says: report that entry and continue with the rest.

## Report

`migration/proofs/port-equals-legacy/changes.md`, and the same in your last message. Per finding: what
you did (fixed, record corrected, left as flag candidate, could not fix and why), the commit, and
the **functions and line ranges changed**, old and new. That last list goes to the team that
re-translates the changed code to Lean, so it must be complete and exact. End with the parity
contract's output.
