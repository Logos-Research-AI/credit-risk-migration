# Fixer brief: apply CONFIRMED review findings to ONE translated file

You receive a list of **confirmed** findings for one file. Each was either reported by both
reviewers, or ruled confirmed by the arbiter.

## How to fix

- Apply each confirmed finding exactly. Apply nothing else: no refactors and no improvements.
- If a finding cannot be applied as written, because it conflicts with the rulebook or with
  another finding or is technically impossible, do not improvise. Mark the site
  `# TODO(port): unresolved review finding <id> — <why>` and list it in your report.
- Read the same context as the implementer (`migration/briefs/IMPLEMENTER.md`). The rulebook
  and the inventory rows still bind.

## Referee and trailer

- Run until clean: `uv run ruff format <file>`, `uv run ruff check <file>`,
  `uv run pyright <file>`.
- Recount the trailer: `grep -c 'TODO(port)' <file>` must equal `todos=` in the
  `# PORT STATUS` trailer. The grep is the receipt.

Touch only your file. No git.

## Reply (at most 120 words)

For each finding id: applied, or flagged (with why). Then the referee results and the grep count.
