# Implementer brief: translate ONE SAS program to Python/polars

The same prompt is used in the Step 2 pilot and the Step 3 fan-out. You translate exactly one
file. Your output is judged later, byte for byte, against SAS's outputs. Follow the rules;
don't improve the code.

## Read first, in this order

1. `migration/RULEBOOK.md` (v1.3), the whole document. It is the law. Its §2 table gives the
   ONE canonical translation of every construct it lists.
2. Every row of `migration/inventory.tsv` whose `file` column is your `.sas` file. Each row
   decides one site: the target translation is binding, and the evidence column says why. Grep
   for the symbols you are translating.
3. Your SAS source at the repo root.
4. `judge/README.md` "Contract": your outputs (file names, columns, column order, formats) must
   match it. Look at the reference outputs in `judge/reference/*.csv`, but never copy values
   from them.
5. `credit_risk/sas_compat.py`: the helper API. Call it; never re-implement a helper. Its
   bodies may still be stubs, which is fine: code against the signatures and docstrings. If you
   need a helper that does not exist, do not write it. Mark the site
   `TODO(port): needs sas_compat.<name>(...) — <what it must do>` and list it in your report.

## Write `credit_risk/<name>.py`

- Structure-preserving (RULEBOOK §0). Keep the same steps in the same order, and the same
  intermediate dataset names, lower-cased (`work.credit_features` → `credit_features`). A short
  comment `# <file>.sas:<lines>` heads each step.
- Entry point and CLI exactly as in RULEBOOK §4 (stage signatures, A27).
- **Cite the rule behind every nontrivial choice** in a trailing or preceding comment: `# R§2
  <construct>` for a rulebook row, `# INV <symbol>` for an inventory row, plus the amendment id
  where useful. Where neither the rulebook nor the inventory decides a site, do not invent
  policy. Write the most conservative translation and flag it inline:
  `# TODO(port): rulebook silent — <question>`.
- Markers exactly as in RULEBOOK §3: `TODO(port):`, `PERF(port):`, `BUG(port):` (bug-for-bug
  reproductions with a one-line repro).
- Listing-only procedures become the one-line comment the rulebook prescribes.
- End the file with the trailer `# PORT STATUS: confidence=[high|medium|low] todos=[N]`.
  N must equal `grep -c 'TODO(port)' <file>`: recount mechanically.

## Referee (in-loop, RULEBOOK §0)

Run these until all three are clean, from the repo root (or the worktree root you were given):

- `uv run ruff format credit_risk/<name>.py`
- `uv run ruff check credit_risk/<name>.py`
- `uv run pyright credit_risk/<name>.py`

pyright is strict. The only escape hatch is
`# type: ignore[<code>]  # TODO(port): <why>` (RULEBOOK §3). Do NOT run the pipeline, the
judge, or SAS.

Touch no file other than `credit_risk/<name>.py`. No git commands.

## Report (at most 200 words)

- The referee results.
- The `TODO(port)` count (grep output).
- Every place the rulebook was silent or ambiguous, with the rule section.
- Every helper you needed that is missing.
