# Reviewer brief: adversarial review of ONE translated file

You are one of two independent reviewers of a Python/polars translation of one SAS program.
You don't see the other reviewer's findings. Assume the translation is wrong, and find where.
You **touch nothing**: no edits, no git, no SAS, no pipeline or judge runs.

## Context

- `migration/RULEBOOK.md` (v1.3): the law.
- `migration/inventory.tsv`: the rows for your `.sas` file are binding per-site decisions.
- The SAS source at the repo root.
- `judge/README.md` "Contract": required outputs.
- `credit_risk/sas_compat.py`: helper API.

You may run small Python checks against `judge/reference/` data to test a claim, e.g. a polars
expression on a reference CSV. Run them from `judge/` with `uv run python`, with scratch
scripts under your own scratch folder.

## What to hunt

1. **Semantics.** Statements where the translation computes something different from SAS:
   missing values, order, division, rounding, printing, column order, row order, file names.
2. **Rule adherence (standing question).** Did the implementer follow the rulebook and the
   inventory? Cite the section or inventory row for EVERY deviation, even one that happens to
   give the right answer. A translation that is right because the implementer quietly ignored
   a rule is a failed review.
3. **Silences.** Places the implementer flagged as rulebook-silent: is the rulebook really
   silent, and is the conservative choice right?
4. **Bookkeeping.**
   - Every SAS step is present, in order.
   - Listing-only steps carry the prescribed comment.
   - The markers use the right format.
   - The trailer's `todos=` equals `grep -c 'TODO(port)'`.

## Findings file: `<the path given in your prompt>`

Header, tab-separated:
```
id	severity	location	finding	cites	fix
```

- `severity` is one of:
  - `wrong-output`: changes a judged file;
  - `rule-violation`;
  - `latent`: wrong only on inputs not judged yet;
  - `nit`.
- `location` is `credit_risk/<file>.py:<line>`.
- `cites`: the rulebook section, the inventory row (file + symbol), or the SAS line that proves
  it. **Required**: a finding without a citation is discarded.
- `fix`: the concrete change.

## Reply (at most 150 words)

The counts by severity, and the three most serious findings.
