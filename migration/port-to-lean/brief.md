# Python to Lean: translate the port into the Logos blueprint `py-credit-risk-port`

> **Paths.** This brief was written when each translator worked in a folder of its own. You now
> work from the project root, as the agent `port-translator`, and a hook enforces what you may touch.
> Read the paths below as follows: `migration/…` means `migration/port-to-lean/…` (your kit record);
> `credit_risk/`, `pyproject.toml` and `uv.lock` are in `port/`; `data/` is `legacy/data/`; `inputs/scenarios/` is `judge/scenarios/` and `inputs/split_ids.csv` is `migration/port-to-lean/inputs/split_ids.csv`; `foundation/` means `migration/foundation/`. "This workspace" means those places.
> There is no `settings.json` of your own to mind.

## What this is for

The Python package `credit_risk/` is a port of a SAS credit-risk pipeline. We are now verifying
that port formally. Three teams work separately:

1. Another session translates the **SAS original** to Lean. You never see it or its work.
2. You translate the **Python port** to Lean.
3. A third session proves or disproves that the two Lean translations behave the same.

Step 3 is only worth something if steps 1 and 2 are independent. If both translators leaned
toward the same convenient Lean, the proof would be trivial and would say nothing about the real
code. So your one job is fidelity: the Lean must do what this Python code does when it runs,
including what looks wrong. Do not tidy, simplify, reorder or fix anything.

The code is full of comments and docstrings saying what SAS does. Those are the port authors'
claims, and they are exactly what is being verified. Never translate a comment. Translate the
code, and settle any doubt by running it.

## What you may read

- This workspace: `credit_risk/`, `pyproject.toml`, `uv.lock`, `data/` (the raw CSVs),
  `inputs/split_ids.csv` (the 70/30 split, an input of the port), `inputs/scenarios/` (edge-case
  inputs), `foundation/`.
- The migration kit at `/Users/cristophersalvi/GitHub/logos-migration-kit`.
- The source and documentation of the libraries the port uses (polars, numpy, scipy), in the
  environment `uv` builds and on the web.
- Two Logos blueprints: `py-credit-risk-port` (yours) and `credit-risk-foundation` (shared).

Nothing else. `CLAUDE.md` in this workspace states the isolation rules; every subagent you start
must be given them.

## Target

All Lean lives in the Logos blueprint `py-credit-risk-port`, through the `logos-mcp` tools.
Create it if it does not exist, set its language to Python with `configure_blueprint`, run
`index_codebase` on `credit_risk/`, and add the in-scope part with `add_code_targets`. Never
keep Lean in local files. Leave the trust layers at their default (Judging).

Before anything else, check that the shared foundation is visible from your blueprint:
`grep` for `Tabular.RealLike` must find it. If it does not, stop and tell me: I have to add
`credit-risk-foundation` to the profile first.

## The shared foundation (read `foundation/foundation.pdf` first)

It fixes types only: the number class `Tabular.RealLike`, cells, rows and tables. It decides no
Python behaviour; that is yours to state, from evidence. Rules that follow from it:

- Write every definition once, for an arbitrary `{α : Type} [Tabular.RealLike α]`. Never
  mention `ℝ` or `Float` in a code item. A Python `float` and the numbers in a polars or numpy
  column are `α`; integers in numeric columns are casts into `α`.
- A data frame that crosses a stage boundary (a CSV file read or written) is a
  `Tabular.Table α`, with the column names and order the code produces. Inside a function, use
  whatever is faithful.
- Keep the arithmetic exactly as written: same operations, same order, same grouping.
  `a / b * c` stays `a / b * c`. The equivalence proof distinguishes "same operations" from
  "mathematically equal", and only you can preserve that information.
- Convention 1 of the foundation: every division, `log`, `sqrt` and `exp` is either guarded as
  the code guards it or covered by a precondition. Where the code tests a result for finiteness
  or NaN, apply `RealLike.isFinite` or `RealLike.isNaN` to the same value at the same point.
- If the foundation is missing something you need, or forces an unfaithful translation, stop
  and tell me. Do not redefine or work around a shared type.

## Scope of this pass

In: everything that is deterministic given its inputs. The four `run` functions with file
access abstracted away, `confusion_metrics`, and the `sas_compat` helpers they use for
comparisons, arithmetic, aggregation, merging, ranking, ROC association, Hosmer-Lemeshow
grouping and the classification table.

Out, for a later pass: the model fit (`fit_logistic`, `stepwise_logistic` and what they call),
CSV type inference (`proc_import_csv`, `input_best32`), and printed formats (`sas_best`,
`fmt_*`, `sas_d8`, `sas_d12_3`, `sas_pvalue`, `write_sas_csv` and their helpers). Treat each as
an explicit input: the fitted model is a parameter of the code that uses it, and the table a
CSV read returns is a parameter.

File access: a `run` function becomes a function from its input tables (and flags) to the list
of `(file name, table)` pairs it writes, in the order it writes them. The format map handed to
the CSV writer is not part of the result.

The off-by-default flags (`fix_psi_bins` and the others) stay as Boolean parameters, with both
branches translated. The third team needs both.

Library calls have no source in this repo: the Lean encodes what polars or numpy does on that
call, with those arguments. Each such rule needs evidence: the library's documentation or
source, and a run on inputs that reach the case (nulls, NaN, ties, empty groups, sort
stability). Where you cannot establish the behaviour, do not guess: make it an explicit
parameter of the unit and list it as open.

## Process: the migration kit, adapted

Follow the kit's README and `CLAUDE.md` (standing rules, adversarial separate reviewers,
rulebook read-only inside loops, recurring failures go upstream to the rules). The target is
unusual, so these adaptations apply:

| Kit step | Here |
|---|---|
| 00 feasibility | Skip. The decision is made. |
| 00b judge | The judge is **differential evaluation**: run the Lean and the Python on the same inputs and compare. See below. Validate the comparison script on planted mismatches before trusting it. |
| 01 dependency map, manifest | `index_codebase` gives the map. `migration/manifest.tsv`: one row per unit with file, line range, blueprint item id, upstream units. |
| Rulebook | `migration/RULEBOOK.md`, from the kit template. §0 is the foundation, read-only. Every rule that states a library behaviour (polars null propagation, `when/then/otherwise`, `fill_null`, horizontal min/max/sum, casts, joins and their row order, `group_by` order, sort stability, rank methods, numpy NaN handling) cites its evidence. |
| 02 gap inventory | The gap is everything Python and polars leave implicit that Lean makes you state: null versus NaN, integer versus float columns, row order after joins and group-bys, ties, out-of-domain arguments, exceptions raised. Sweep by grep, one row per site. |
| 03 stress test | Run it on the three units that exercise the most inventory rows: the bakeoff and the pilot, as the kit describes. |
| 04 translate | Implementer, two adversarial reviewers, fixer, per unit. The reviewers' standing question: does this Lean do anything the Python does not, or omit anything it does? A unit is done when its statement is accepted in the blueprint (`get_status`), not when a file exists. |
| 05 survey build | Dissolved into step 04: `write_statement` compiles and judges each unit as it is written. |
| Steps 5 and 6 | Differential evaluation of every unit that can be evaluated, burned down to zero unexplained differences. |
| 06 post-parity | Not applicable. |
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
  batches of a few hundred and grow them while calls stay fast. Generate the terms with a script from the same
  rows you feed the Python; never type them by hand.
- A `Float` prints with six decimals only. For an exact comparison evaluate a helper that
  returns `Float.toBits`, and compare with the bits of the Python double
  (`struct.unpack('<Q', struct.pack('<d', x))`).
- You have the running code, so compare exactly: call the Python function, or the slice of
  `run` the unit covers, on the sampled inputs and compare bit for bit. `exp` and `log` may
  differ in the last bit between Lean's runtime and numpy; record such cases, do not chase them.

Sample to cover the inventory, not at random: for every inventory row, at least one input that
reaches it. `inputs/scenarios/` holds edge inputs that reach nulls, ties and the rarer branches;
build more where a row has none.

A difference is a defect in the Lean until shown otherwise. Never adjust the Lean to match
without finding the library rule that explains it and recording that rule.

## Blueprint shape

The blueprint should read like the package. Keep the items `index_codebase` produces, named
after the functions. A `run` function is long: if translating it as one definition makes it
hard to review, split it into consecutive line ranges with `add_code`, each a named step that
the `run` item composes in source order. Dependencies follow the calls.

Add a precondition (`add_precond`) to each unit that needs one: what the unit requires of its
input for the Lean to be faithful (domains, column presence, the cases where the Python would
raise).

Do not add postconditions. A code item is a definition; the theorems are the third team's.

## Last step: freeze. STOP here.

When every in-scope unit is accepted and the differential evaluation is clean, stop. From that
point the statements must not change: the SAS translation is revealed to the third team only
after this one is fixed, and I will record the state of every item.

## Final report

Counts from `get_status`; the manifest with every unit's state; the open parameters and
UNKNOWN rows with the question each needs answered; the differential-evaluation receipt (units
evaluated, cases run, differences found and how each was resolved); and the rulebook
amendments made along the way.
