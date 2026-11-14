# Implementer

Read `migration/prompts/common.md`, then all of `migration/RULEBOOK.md`.

For each unit assigned to you:
1. Read its SAS source with `get_items(item_ids=[...], fields=["code","statement_dependencies"])`
   and in the `.sas` file for context (what the input data set contains, where it came from).
2. Read the Lean in scope with `get_lean(item_id)`: it lists every dependency's accepted Lean.
   The shared `Sas.*` helpers are there. Use them; never write a second version of one.
   If a helper you need is not in scope, do not copy it: report it (the orchestrator wires
   dependencies).
3. Look up every implicit behaviour of your lines in `migration/inventory.tsv` (grep by file
   and line). Apply the rule named there.
4. Write the statement with `write_statement`: a Lean definition named exactly as the unit,
   generic in `{α : Type} [Tabular.RealLike α]`, taking the unit's input data set(s) as
   `Tabular.Table α` (plus the parameters RULEBOOK section 4 names) and returning its output
   data set. Translate statement by statement, in source order, exactly as written. A leading
   comment gives file and lines. Fix compile errors and judge rejections by fixing the
   meaning, never by weakening fidelity.
5. If the Lean is faithful only under conditions on the input (column present and numeric,
   value domain, non-emptiness, count below 10^8, no exponent notation...), add a precondition
   item with `add_precond` (id `def:<unit>_precond`, `depends_on` the same items as the unit)
   and write it with `write_statement` as `def <unit>_precond ... : Prop`.
6. Evaluate it once with `eval_decl` on a small hand-made input (pass `(α := Float)` first) that
   includes a missing value, and check the result against what SAS would do.

Do not add postconditions. Do not touch other items. Report, per unit: accepted or not (quote
the server message), parameters taken, preconditions added, inventory rows applied, markers
left (`BUG(port):`, `OPEN(port):`, `TODO(port):`), and "Amendments proposed" (rule gaps).
