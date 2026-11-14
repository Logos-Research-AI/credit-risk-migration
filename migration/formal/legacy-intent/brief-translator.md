# SAS to Lean: translate the original pipeline into the Logos blueprint `sas-credit-risk-spec`

## What this is for

A SAS credit-risk pipeline was ported to Python. We are now verifying that port formally. Three
teams work separately:

1. You translate the **SAS original** to Lean.
2. Another session translates the **Python port** to Lean. You never see it or its work.
3. A third session proves or disproves that the two Lean translations behave the same.

Step 3 is only worth something if steps 1 and 2 are independent. If both translators leaned
toward the same convenient Lean, the proof would be trivial and would say nothing about the real
code. So your one job is fidelity: the Lean must do what SAS does on this code, including what
SAS does that looks wrong. Do not tidy, simplify, reorder or fix anything.

Your Lean is the specification the port is judged against, so a mistake here either hides a
real defect or invents a false one.

## What you may read

- This workspace: the four `.sas` scripts, `MODEL_CARD.md`, `README.md`, `data/`,
  `judge/reference/` (real outputs of the unmodified SAS run, plus four edge scenarios),
  `judge/scenarios/` (the edge inputs), `judge/run_sas.py` (runs SAS on SAS OnDemand),
  `experiments/` (raw SAS programs and logs from earlier experiments), `foundation/`.
- The migration kit at `/Users/cristophersalvi/GitHub/logos-migration-kit`.
- SAS documentation on the web.
- Two Logos blueprints: `sas-credit-risk-spec` (yours) and `credit-risk-foundation` (shared).

Nothing else. `CLAUDE.md` in this workspace states the isolation rules; every subagent you start
must be given them.

## Target

All Lean lives in the Logos blueprint `sas-credit-risk-spec`, through the `logos-mcp` tools.
Create it if it does not exist. Never keep Lean in local files. Leave the blueprint's trust
layers at their default (Judging). SAS has no parser on the server, so add each unit with
`add_code`, giving the file and line range.

Before anything else, check that the shared foundation is visible from your blueprint:
`grep` for `Tabular.RealLike` must find it. If it does not, stop and tell me: I have to add
`credit-risk-foundation` to the profile first.

## The shared foundation (read `foundation/foundation.pdf` first)

It fixes types only: the number class `Tabular.RealLike`, cells, rows and tables. It decides no
SAS behaviour; that is yours to state, from evidence. Rules that follow from it:

- Write every definition once, for an arbitrary `{α : Type} [Tabular.RealLike α]`. Never
  mention `ℝ` or `Float` in a code item.
- A dataset that crosses a stage boundary (a CSV hand-off file) is a `Tabular.Table α`, with the
  SAS column names and column order. Inside a stage, use whatever is faithful.
- Keep the arithmetic exactly as written: same operations, same order, same grouping.
  `a / b * c` stays `a / b * c`. The equivalence proof distinguishes "same operations" from
  "mathematically equal", and only you can preserve that information.
- Convention 1 of the foundation: every division, `log`, `sqrt` and `exp` is either guarded as
  SAS guards it (a SAS division by zero gives missing, and so on) or covered by a precondition.
- If the foundation is missing something you need, or forces an unfaithful translation, stop
  and tell me. Do not redefine or work around a shared type.

## Scope of this pass

In: everything that is deterministic given its inputs. The DATA steps, PROC SQL, PROC SORT,
PROC RANK, the `%confusion_metrics` macro, scoring from a fitted model, the risk score, grades
and recommendations, KS, deciles, lift, PSI, calibration, the summaries, and the statistics
PROC LOGISTIC computes from already-fitted probabilities (ROC association, Hosmer-Lemeshow
grouping).

Out, for a later pass: the model fit itself (stepwise selection and the optimiser), PROC
IMPORT's type guessing, printed formats, and listing-only output (PROC PRINT, MEANS, FREQ,
CONTENTS, SGPLOT). Treat each as an explicit input: the fitted model (selected variables and
coefficients) is a parameter of the units that use it, the imported table is a parameter of the
first step, and the 70/30 split is a parameter (PROC SURVEYSELECT's draw is not reproducible).

For a built-in PROC there is no source to translate: the Lean encodes what SAS does. Each such
rule needs evidence: the SAS documentation, an experiment in `experiments/`, or a reference
output it reproduces. Where you have none and cannot get it by running SAS, do not guess: make
the behaviour an explicit parameter of the unit and list it as open.

## Process: the migration kit, adapted

Follow the kit's README and `CLAUDE.md` (standing rules, adversarial separate reviewers,
rulebook read-only inside loops, recurring failures go upstream to the rules). The target is
unusual, so these adaptations apply:

| Kit step | Here |
|---|---|
| 00 feasibility | Skip. The decision is made. |
| 00b judge | The judge is **differential evaluation**: run the Lean on real rows and compare with what SAS printed in `judge/reference/` (and its scenarios). See below. Validate the comparison script on planted mismatches before trusting it. |
| 01 dependency map, manifest | `migration/manifest.tsv`: one row per unit with file, line range, blueprint item id, upstream units. A unit is one DATA step, PROC step or macro, in source order. No depmap script is needed. |
| Rulebook | `migration/RULEBOOK.md`, from the kit template. §0 is the foundation, read-only. Every rule that states a SAS behaviour (missing-value comparisons and arithmetic, `SUM()`/`MIN()`/`MAX()`, `ROUND`, Boolean assignment, `RETAIN`, BY-group order, PROC SQL joins and `CALCULATED`, PROC RANK ties and groups, sort stability) cites its evidence. |
| 02 gap inventory | The gap is everything SAS leaves implicit that Lean makes you state: missing values, row order, ties, numeric versus character, length and truncation, out-of-domain arguments, PROC defaults. Sweep by grep, one row per site. |
| 03 stress test | Run it on the three units that exercise the most inventory rows: the bakeoff and the pilot, as the kit describes. |
| 04 translate | Implementer, two adversarial reviewers, fixer, per unit. The reviewers' standing question: does this Lean do anything the SAS does not, or omit anything it does? A unit is done when its statement is accepted in the blueprint (`get_status`), not when a file exists. |
| 05 survey build | Dissolved into step 04: `write_statement` compiles and judges each unit as it is written. |
| Steps 5 and 6 | Differential evaluation of every unit that can be evaluated, burned down to zero unexplained differences. |
| 06 post-parity | Replaced by the intent properties, below. |
| `settings.json` | Already installed in `.claude/`. It denies reading the other side. Do not edit it. |

The kit's sign-off gates: run through them without stopping, and record at each one what a
sign-off would have reviewed (in `migration/gates.md`). Stop only where this prompt says STOP,
or where a kit rule says a decision is mine and you cannot make a conservative choice.

Start no more than four subagents at once against the blueprint; if the server reports
conflicts, go serial. Models: reviewers and rulebook work on the session model; implementers
and fixers may use a smaller one.

### Differential evaluation

`eval_decl` runs an accepted code item on inputs you choose. Facts already checked:

- Pass the number type as a named argument: `(α := Float) (some 2.5)`.
- A call takes any number of cases, each a Lean term; there is no fixed cap. Start with
  batches of a few hundred and grow them while calls stay fast. Generate the terms with a script from sampled
  CSV rows; never type them by hand.
- A `Float` prints with six decimals only. For an exact comparison evaluate a helper that
  returns `Float.toBits`, and compare bits.
- The reference CSVs hold printed values (`BEST12.` and fixed formats), not full doubles. So
  compare flags, counts, categories and missing-ness exactly, and continuous values to the
  printed precision. Where that is too coarse to settle a question, run SAS with
  `judge/run_sas.py` and print with a wider format.

Sample to cover the inventory, not at random: for every inventory row, at least one input that
reaches it. The four edge scenarios exist because the real data never reaches missing-value
comparisons, grade F, rank ties or a non-zero PSI.

A difference is a defect in the Lean until shown otherwise. Never adjust the Lean to match
without finding the SAS rule that explains it and recording that rule.

## Blueprint shape

The blueprint should read like the SAS code. One code item per unit, named after the dataset it
creates or the step it performs, in source order, with dependencies following the data flow.
Add a precondition (`add_precond`) to each unit that needs one: what the unit requires of its
input for the Lean to be faithful (domains, column presence, non-emptiness).

Do not add postconditions during translation. A code item is a definition; the theorems come
next.

## Last step: intent properties. STOP here.

When every in-scope unit is accepted and the differential evaluation is clean, draft the
**intent properties**: what each part of the pipeline was meant to guarantee, taken from
`MODEL_CARD.md`, the comments in the SAS code and the findings section of `judge/README.md`.
Examples of the kind wanted: every scored row with a present probability gets a grade; the
grade bands neither overlap nor leave gaps; a risk flag is set only when its variable is
present and beyond its threshold; PSI is zero exactly when the two score distributions agree
on the bins; every eligible applicant receives a probability.

Write them as a plain list in `migration/intent-properties.md`: the property in one sentence,
the unit it belongs to, the source of the intent (file and line), and whether you expect it to
hold of the SAS code as written. Expecting it to fail is a finding, not a problem. Do not
formalise them yet. Then stop and report.

## Final report

Counts from `get_status`; the manifest with every unit's state; the open parameters and
UNKNOWN rows with the question each needs answered; the differential-evaluation receipt (units
evaluated, cases run, differences found and how each was resolved); the rulebook amendments
made along the way; and the intent-property list.
