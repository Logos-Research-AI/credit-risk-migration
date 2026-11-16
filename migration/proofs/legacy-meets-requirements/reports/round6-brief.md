# Round 6 brief for the provers (SAS blueprint 3f5df696-7c80-45cc-809f-b2881714663d)

The owner refreshed the profile after rulings G54 and G55: `CreditRisk.TrainOK` and
`CreditRisk.TestOK` each have one more clause (income and dependents, where present, satisfy
`CreditRisk.decimal12`). `def:SasLinks` was revised in text only (plus one comment in its Lean).
That cleared the statements and proofs of its 34 consumers. Nothing else changed: no unit, not
`def:sasPipeline`, no requirement Q.

For each item assigned to you:

1. Restate it with exactly the Lean it had. The source is the blueprint's stored draft
   (`read_scratch`) if it is still there, otherwise `statement_lean` in
   `migration/proofs/legacy-meets-requirements/reports/snapshot-round5.json`. No hypothesis added,
   removed or reworded. The snapshot holds the sha256 of each statement and the audit compares.
2. Resubmit the stored proof unchanged (`submit_solution` on the stored draft, or
   `write_solution` with the stored text). Statements of lemmas a proof uses must be back first:
   if one you need belongs to a teammate, restate your statements meanwhile and message them.
3. If a stored proof no longer compiles, the cause should be the new clause in TrainOK / TestOK
   (an `obtain` or `rcases` pattern on their conjuncts, a witness that must now also show
   decimal12). Make the smallest repair and say exactly what changed. `lem:sasLinks_witness`,
   `lem:sas_links_sat` are the likely ones: their witnesses must satisfy the new clause.
4. If a statement can no longer be proved, do not weaken it: negate, check, and report to the
   lead at once.

Standing rules as before: Logos MCP Staging only, blueprint by id, all Lean on the blueprint,
change no unit and no definition, do not go idle while something of yours is unproved (an idle
agent is not woken by a compile finishing). Report to the lead when all your items are in state
proved: item, restated from which source, proof resubmitted unchanged or repaired (what).
