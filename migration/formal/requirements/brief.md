# Formalise the documented requirements into the Logos blueprint `credit-risk-requirements`

## What this is for

A credit-risk pipeline exists as a SAS program and is being verified and migrated. Before any
code is judged, its **documentation** is turned into formal requirements. Those requirements
then become the yardstick: the SAS code will be proved to meet them, or corrected until it does,
and only then migrated.

Your job is the first step: formalise `requirements.md` in Lean, in a new Logos blueprint
`credit-risk-requirements`, and prove the requirements **consistent**.

The documentation is the authority. You never see the code, and must not look for it: a
requirement bent toward what the code happens to do is worthless.

## What you may read

- This folder: `requirements.md` (the requirements, with the owner's rulings), `MODEL_CARD.md` and
  `README.md` (the documents they come from), `foundation/` (the shared types).
- The Logos blueprints `credit-risk-requirements` (yours) and `credit-risk-foundation` (shared).

Nothing else: no file outside this folder (a hook blocks it), no other
blueprint. The README names four `.sas` scripts; do not look for them.

## Target

All Lean lives in the blueprint, through the Logos tools; never save Lean to a local file, not
even as scratch. Trust layer: Judging, the default. This is not a code blueprint: every item is a
definition or a theorem added with `add_item`, with the requirement's text as its informal text.

Use the shared foundation (`foundation/foundation.pdf`): tables are `Tabular.Table`, numbers are
the real numbers. Check first that `Tabular.RealLike` is visible from your blueprint; if not,
stop and tell me.

## What to build

1. **The pipeline as an interface.** One definition: what a pipeline *is*, as far as the
   requirements can see it. A structure whose fields are functions between the tables of
   section 5 of `requirements.md`: feature engineering (raw training table and a split to the two
   feature tables), scoring (a feature table to a score table), test scoring (raw test table and
   the training data to the test predictions), and metrics (two score tables to the metrics
   tables). Keep it as small as the requirements allow. It must not assume how any step is
   computed: a later team will plug the real SAS program into this structure.
2. **The input conditions** of section 3, as one definition.
3. **One definition per requirement** Q1 to Q26 (not the withdrawn Q17): a property of a
   pipeline, quantified over every input that meets the input conditions. Name each after its
   number. Where a requirement needs a notion the documents use without defining (median, the
   cumulative distributions of KS, the bin shares of PSI, AUC), define it once, as its own item,
   in the standard mathematical way, and say so in the item's text.
4. **The whole specification**: one definition, the conjunction of all requirements.
5. **Consistency**: one theorem, proved: there is a pipeline that satisfies the whole
   specification. Any pipeline will do, however artificial; the point is that the requirements do
   not contradict each other. Also prove that the input conditions can be met.

## Rules

- State each requirement as `requirements.md` words it, with its rulings. Do not strengthen,
  weaken or tidy it. If a requirement cannot be stated, or two of them contradict each other so
  that consistency cannot be proved, **stop and report**: that is a finding about the
  documentation, and its owner must rule on it. Do not resolve it yourself.
- If a requirement is ambiguous in a way the rulings do not settle, state the reading you took in
  the item's text and list it in your report.
- No `axiom`, `sorry`, `native_decide` or `unsafe` in an accepted proof.
- Have a separate reviewer, who did not write it, check every statement against
  `requirements.md` before the consistency proof is started.

## Report

`report.md` in this folder, and the same in your last message: the items with their state; every
reading you had to take; anything in the documentation that could not be formalised as written;
what the consistency witness is and what it does not show; the counts from `get_status`.
