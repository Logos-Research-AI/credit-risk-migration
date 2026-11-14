# Report: credit-risk-requirements

Blueprint id: `006ff04c-d34c-4a9c-b230-ccd725b1be6f` (Logos MCP Staging)

Status: **stopped at the first check of PROMPT.md. Nothing was formalised.**

## Why the run stopped

PROMPT.md says: "Check first that `Tabular.RealLike` is visible from your blueprint; if not, stop
and tell me." It is not visible.

Evidence, all on Logos MCP Staging:

- `credit-risk-foundation` (`02011d57-8b15-43bb-8744-c6646fdfe9ae`) opens by id and holds its 17
  items, including `def:RealLike`, `def:Row`, `def:Table`, `def:Row.get`, all formalised.
- From an item of `credit-risk-requirements`, `check_decl` on `Tabular.RealLike` and on
  `Tabular.Row.get` answers "does not exist in the referenced environment".
- A statement that uses `Tabular.Row ℝ` and `Tabular.Row.get` does not compile:
  "Unknown identifier `Tabular.Row`", "Unknown identifier `Tabular.Row.get`".
- `search` for the real-like number type from the new blueprint returns only Mathlib/LogosLib
  results, none from the foundation: the foundation is not in this blueprint's profile.

I did not work around it (no copy of the foundation into this blueprint, no
`consolidate_blueprints`): the brief says to stop, and a private copy of the shared types would
defeat their purpose.

## What is needed to resume

Make `credit-risk-foundation` visible from `credit-risk-requirements` on the staging server (pin
it as a profile of the blueprint, or whatever the server's mechanism is), then rerun.

## State of the blueprint

`get_status`: total_items 0, statements_formalized 0, statements_pinned 0, statements_to_write
none, proofs_to_write none, waiting none, verification_approved false.

Two probe items (`def:Cells`, `def:num`) were added to run the visibility check and then removed.
The blueprint is empty. No requirement was stated, no reviewer was run, no proof was started.

## Two things the next run will meet (found while probing, not acted on)

- The server accepts exactly one Lean declaration per item, named after the item id. Shared
  vocabulary (reading a numeric cell, the age group, the training median of Q1) therefore needs
  its own items, beyond the notions PROMPT.md lists (median, KS distributions, PSI bin shares,
  AUC).
- `open_blueprint` by name was not tried; the foundation was opened by id as instructed.

## Readings, unformalisable text, consistency witness

None to report: the formalisation was not started.
