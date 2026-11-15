# Round 4: working notes (2026-11-15)

Run from the orchestrator's session with ordinary background agents (team mode did not come on
after the restart). Follows the verification kit's playbook, stages 5 to 7.

## Profile check: passed

Seven names of the requirements blueprint resolve from the legacy blueprint and equal its current
statements (`TrainOK`, `TestOK`, `Q12`, `Q13`, `Q26`, `Q27`, `Spec`).

## Pipeline revised (prover), accepted

- `def:sasPipeline`: new parameter `importTestColumns : Table ℝ → List String` after `importTest`
  (17 parameters). `score` carries no stop. `fit` is unchanged and is now the only place
  `train_inputs_stop` sits. `scoreTest` passes `importTestColumns test` to `test_raw_columns_ok`.
- `def:SasLinks`: one link added, (2b): on a test table meeting `TestOK`, `importTestColumns raw`
  is a permutation of the twelve names, and `test_raw_columns_ok_precond` holds of it. Links (1)
  to (8) textually unchanged.
- The informal text of both items was rewritten to the round 4 wiring: the judge is active on
  these two items and rejected the new Lean against the round 3 text.
- Stops: `features` credit_raw_stop; `fit` train_inputs_stop; `score` none; `scoreTest`
  predict_inputs_stop then test_raw_stop; `metrics` metrics_inputs_stop.

Noted by the author:
- `[]` is the only row-less table and meets `TestOK`, so link (2b) asserts the twelve names for
  the empty test table. A header-only file with a wrong header, or no table, is the same raw
  table `[]` at the interface: the third clause of Q27 is never tested on a bad header.
- With `score` total, link (8) makes `scoresTrainExists S` / `scoresValidExists S` true exactly
  when S is the scoring chain applied to some model and some table.
- The second conjunct of (2b) is redundant (the twelve names stay distinct when upper-cased) but
  that is not machine-checked.

Blueprint after the revision: 143 items; to restate: 26 contracts, `thm:score_chains_agree`, five
lemmas (`lem:sasLinks_witness`, `lem:sas_feature_rows`, `lem:sas_features_some`,
`lem:sas_links_sat`, `lem:sas_split_sat`). `lem:sas_features_row_total` and `lem:sas_score_rows`
remain proved.

## Review of the revised pipeline (a second prover): no defect in the round 4 changes

- `score` is the validation chain alone, four units in manifest order, no stop; `fit` carries
  `train_inputs_stop` as train.sas 34-42; it appears nowhere else.
- Link (2b) is exactly "on a `TestOK` table, a permutation of the twelve names", the strings are
  those of `def:TestOK` and section 5; the extra conjunct is implied (by inspection, not machine).
- `[]` meets `TestOK`, so the empty test file of G44 is covered faithfully. A header-only file
  with a wrong header, and "no table", are not inputs of the requirements' interface (both are
  `[]`, which is valid): the contract neither asserts nor denies their rejection; that rests on
  the SAS runs only.
- Link (8) with `score` total: `metrics` can now run on score tables no SAS run could have on
  disk; no contract is affected; on run tables nothing stops where SAS would not.
- Informal texts agree with the Lean, two wording points apart.

**Finding that decides Q27 (not a round 4 change).** Links (1), (2), (2b) constrain the imports
only on tables meeting `TrainOK` / `TestOK` (the wording of the brief since round 3). On a faulty
table the imports are free, so an import that returns `[]` or a valid table for every faulty one
satisfies the links, and then `scoreTest` / `features` return a result: clauses (2) and (3) of
Q27 ("on an invalid input the pipeline stops") are false by construction, for a reason that is
not the program's. Rescuing them needs a link on faulty tables: a decision on the brief, put to
the owner.

Minor: `manifest.tsv` still lists `test_raw_columns_ok` at predict.sas 71-86 with the R39 note.

## Owner's decision on the import links (2026-11-15): they cover every table

Put to the owner as the finding above. Decision: option A. Links (1) and (2) are extended to
every raw table: the import delivers a file as it is (rows, order, column names, cell contents;
a number may arrive as text that reads back to the same number), and the clauses for valid
tables are kept as they were. The links must not say that a check fails on a faulty table: that
is for the SAS checks to do and for the contract to prove. Recorded in `brief-prover.md`
(commit 22c4b03). A prover is revising `def:SasLinks` on that brief; a second prover reviews it.

## State before that revision

- Contracts: all 26 and `thm:score_chains_agree` were restated after the first revision of the
  pipeline, with the new parameter `importTestColumns` and nothing else changed. The revision of
  `def:SasLinks` clears them again; they are resubmitted unchanged.
- Shared lemmas after the first revision: `lem:sas_feature_rows`, `lem:sas_features_some`,
  `lem:sas_split_sat`, `lem:sas_links_sat` statement and proof accepted; `lem:sasLinks_witness`
  statement accepted, proof not started (it is the proof of `lem:sas_links_sat` with the reads
  written `fun t => t`). `lem:sas_features_row_total` and `lem:sas_score_rows` were never
  cleared. Witness for `importTestColumns`: the constant list of the twelve names of link (2b).
- What the extension will ask of the lemmas: `lem:sas_feature_rows` and `lem:sas_features_some`
  use link (1) as an implication from `TrainOK`; the witness imports of `lem:sas_links_sat` are
  proved to deliver rows only on valid tables, so the extended links need new work there, not
  only the new parameter.

## The extended links: accepted, lemmas restored, statements back

`def:SasLinks` revision 744271cb: links (1) and (2) are each `(round 3 clause) ∧ (∀ raw,
deliveredTable raw (import raw))`; (2b), (3)-(8) and `def:sasPipeline` untouched. All 26
contracts and `thm:score_chains_agree` resubmitted unchanged and accepted. All seven shared
lemmas proved; `lem:sas_links_sat` and `lem:sasLinks_witness` with a two-case witness (round 3
delivery on valid tables, delivery as it is elsewhere), so the links are satisfiable
(machine-checked).

## Review of the extended links (a prover that did not write them)

Sound: rows, order, cell count and names kept; `[]` to `[]`; no conclusion assumed; satisfiable;
text agrees with the Lean. The round 3 clauses could not be compared word for word (no item
history), only indirectly.

Defects, all on tables outside `TrainOK` / `TestOK` (so they touch only clauses 2 and 3 of Q27):

- D1. A text cell is delivered with its leading blanks; PROC IMPORT removes them (x23 parts I,
  J). Ids `"7"` and `" 7"` escape the duplicate check in the Lean; SAS stops. Correction: deliver
  the text trimmed.
- D2. One column may be delivered with mixed kinds (`num 7`, `str "7"`, `str "8"`); a SAS column
  has one type. Correction: one kind per column, where every number of the column has a text.
- D3. Tables whose rows do not have the same columns: delivered as they are, the checks read the
  first row only, no stop. No CSV file is such a table.
- D4. Names are kept where PROC IMPORT changes them (a repeated name becomes `VAR12`); the two
  text columns are recognised by exact name, SAS by any capitalisation (x21 part B).
- D5. A column empty in every row is character in SAS (`SeriousDlqin2yrs` in the real test
  file); the links say numeric missing. The checks treat both alike.

Not corrected now, on purpose: a correction clears every statement and proof again, and Q27 has
a disproof that depends on none of these: a header in other capitalisation (`AGE`) fails
`TrainOK` (exact names) and SAS accepts it (x21 part B: `columns_ok=1`, `bad_rows=0`). In this
round a disproof of Q27 may rest only on a table a real SAS run stands behind; tables of the
kinds D1-D3 are not accepted. D1-D5 are corrected before Q27 can be proved.

For the owner, after the round: O1 what a raw text cell is (`07`, `+7`, `" 7"`: number or
text?), with one SAS run to settle what makes the id column character; O2 tables that are not
rectangular; O3 capitalisation of column names; O4 the all-empty column.
