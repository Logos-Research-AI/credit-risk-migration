# Round 2: work from version 2 of the specification

`informal-spec.md` in this folder is now version 2. Read it in full, starting with "What changed
from version 1, and why". `PROMPT.md` still holds: the rules the audit checks, how to work, never
touching a `def:` item, no local Lean. This brief only says what is different.

## What is different

1. **Contracts are over the real numbers.** Do not attempt "every number type". Nothing is
   claimed about `Float`; do not run new Float evaluations except to find a witness.
2. **The judge is on.** Trust layers on `py-credit-risk-port` are now Judging: each statement you
   write is checked against its informal text. Write the text first, exactly as the
   specification gives it, instantiated for the item. A statement the judge rejects is fixed to
   say what the text says, never the other way round.
3. **Do only what section 9 lists.** Restate the contracts listed there, settle the three open
   ones, and do not touch any item marked "stands". A restated contract replaces the round 1
   item of the same name: rewrite its text and statement, redo its proof, and remove its old
   negation item if the verdict changes.
4. **Well-formed inputs** (section 2) are part of every restated contract's hypotheses. State
   well-formedness once per stage or step shape and reuse it; show for each that a concrete
   input meets it.
5. **Stage contracts are one item per output file** (section 3).

## The findings file, for the coding agent

When the round is done, write `findings-for-code.md` in this folder. A separate agent that changes
the Python code will act on it directly, without seeing any Lean, so it must stand on its own.
Include every contract that is disproved today, from round 1 or round 2, as one entry:

- an id (the contract's), and one sentence saying what differs;
- **kind**, exactly one of:
  - `port-differs-from-sas`: SAS and Python give different results on a well-formed input;
  - `shared-intent-failure`: SAS and Python agree, and both fail what the pipeline was meant to do;
  - `fix-defect`: a flag-on behaviour that does not do what its bug-fix record says;
  - `record-inaccurate`: a statement in the migration's records that the code contradicts;
- the Python file, function and line range;
- the smallest input that shows it, written as plain values (column names and cell values), and
  what SAS gives and what Python gives on it;
- for `port-differs-from-sas`: the SAS rule in words, with the `.sas` lines or the SAS-side
  rulebook rule it comes from, precise enough to implement;
- whether the judged data or the edge scenarios reach it.

Leave out contracts that fail only on inputs that are not well formed; version 2 should leave
none, and any that remain are listed separately under "specification gaps" for me.

## Report

`report-round2.md`, same shape as `report.md`: per contract touched, the result and the witness;
then the three settled contracts; then counts from `get_status`. Say plainly which stage files
are proved equal to SAS, which are disproved and by which finding, and which are open.
