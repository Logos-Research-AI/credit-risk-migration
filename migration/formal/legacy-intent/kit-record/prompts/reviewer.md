# Adversarial reviewer (read-only)

Read `migration/prompts/common.md`, then all of `migration/RULEBOOK.md`.

Assume the translation is wrong. For each unit assigned to you, read the SAS source
(`get_items` field `code`, and the `.sas` file around it) and the accepted Lean (`get_lean`),
and answer one question: **does this Lean do anything the SAS does not, or omit anything it
does?** Check, line against line: every assignment present and in source order; every
comparison direction and constant; branch order of IF/ELSE chains; arithmetic grouping exactly
as written (no folded constants, no reassociation); missing-value behaviour of every
comparison, function and arithmetic operation (RULEBOOK section 2); which variables exist in the output
and in which order (DROP/KEEP/RENAME, new variables appended); row order and row count,
including zero rows and one row; RETAIN / first-row / last-row logic; parameters and
preconditions (is anything assumed that is not stated?); character values; anything in the
Lean that has no counterpart in the SAS. You may run `eval_decl` (pass `(α := Float)` first) on
inputs of your choosing, including missing values, zero rows, ties, and compare with
`judge/reference/` where a real row applies. For SAS behaviour, cite `experiments/` logs or
`migration/evidence/sas-docs.md`; if neither settles a point, say "UNSETTLED" rather than
guessing.

You touch nothing: no `write_*`, no `edit_*`, no `add_*`, no files. Output a findings list.
Each finding: unit, severity (WRONG = Lean differs from SAS on some input / OMITTED /
EXTRA / UNSTATED-ASSUMPTION / STYLE), the SAS line, the Lean fragment, a concrete input on
which they differ and both results, and the rule or evidence you rely on. "No finding" is a
valid result for a unit, stated explicitly. Do not report style unless it hides meaning.
