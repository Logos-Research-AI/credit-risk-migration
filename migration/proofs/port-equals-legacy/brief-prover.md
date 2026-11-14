# Prove or disprove that the Python port behaves as the SAS original

## What this is for

A SAS credit-risk pipeline was ported to Python. Two separate teams translated each side to
Lean, independently, into two Logos blueprints:

- `sas-credit-risk-spec`: the SAS original. It is now in a profile pinned to the blueprint below,
  so its declarations are in scope there. Read-only.
- `py-credit-risk-port`: the Python port. You work here.

Both are built on `credit-risk-foundation` (number class `Tabular.RealLike`, tables).

Your job is to state and prove, or disprove, the contracts listed in `informal-spec.md`. They
restate what the original migration committed to in writing (its judge contract, rulebook, gap
inventory and bug-fix records) as statements about the Python items. A disproof with a concrete input is as good a result as a proof. A proof obtained by
weakening a statement is worthless, and the audit that follows is designed to find it.

Read `informal-spec.md` in full before anything else. This prompt only says how to carry it out.

## What you may read

- `informal-spec.md` here.
- The SAS side: `../legacy` (the `.sas` scripts,
  `migration/RULEBOOK.md`, `manifest.tsv`, `open-items.md`, `intent-properties.md`,
  `judge/scenarios/`).
- The Python side: `../port` (`credit_risk/`,
  `migration/RULEBOOK.md`, `manifest.tsv`, `inputs/scenarios/`, `migration/diffeval/` for how
  that team built Lean terms from data).
- The three blueprints, through the `logos-mcp` tools.

Write only in this folder and in the blueprint `py-credit-risk-port`. All Lean lives in the
blueprint: never save Lean to a local file, not even as a copy or a scratch.

## Rules that the audit checks

1. **Never change an existing item.** No edit, removal, rename or re-submission of any item that
   exists today, in any blueprint. The audit checks every item for change. If a
   definition looks wrong, that is a finding to report, not something to fix.
2. **Never reword a contract.** The informal text of each contract comes from
   `informal-spec.md` (section 1 gives the form and the only parameter links allowed, sections 3
   to 8 the instances). The Lean statement must say exactly that. If you believe a contract
   is wrong or cannot be stated, skip it and report why.
3. **Strength, in order** (section 1): for every number type; else at `ℝ`, naming the operations
   whose order differs; else disproved. Record which. Never go from "for every number type" to
   `ℝ` without first showing why the generic statement fails or cannot be proved, with the
   expression that differs.
4. **No empty proofs.** For every contract, show its hypotheses can be met: give one concrete
   input that satisfies all of them (evaluated at `Float`, or as a small lemma). A contract whose
   hypotheses nothing satisfies is reported as vacuous, not proved.
5. **Every assumption is listed.** A contract that uses a parameter link marked *assumption* or
   *conditional* in section 1 says so in its text. No other hypothesis may be added.
6. No `axiom`, `sorry`, `native_decide` or `unsafe` in any accepted proof.

## First check. STOP if it fails.

Open `py-credit-risk-port`. Then:

- `grep` for `credit_cleaned` and `Sas.lt`: both must be found, coming from the profile. If not,
  the profile is not pinned: stop and tell me.
- `get_status` must still report every statement formalized, and `check_decl` on
  `confusion_metrics` must resolve. Both sides declare that name. If the Python blueprint no
  longer compiles, or the name is ambiguous in a way you cannot avoid by qualification inside
  your own statements, stop and tell me: the SAS side will be renamed.

## How to work

Contracts are postconditions on Python items: `add_postcond`, with the informal text from the
specification, then `write_statement`, then `write_solution`. Helper lemmas go inside the proof file of
the contract that needs them, never as new items.

Work in this order:

1. **Confirm the pairings by evaluation.** For each row of section 5, evaluate both sides on
   the same inputs at `Float` and compare, before writing any statement. `eval_decl` runs only a
   declaration written in the item's own Lean, and needs a printable result; a Python frame does
   not print. So add temporary carrier items named `zz_…` whose Lean defines the comparison you
   need (for instance a function returning whether `Pl.toTable (py_step f)` and
   `sas_unit (Pl.toTable f)` agree, or the bits of both). Remove every `zz_…` item before you
   finish. Compare numbers through `Float.toBits`: a `Float` prints six decimals only.
   Use the edge scenarios on both sides, and inputs with missing values in every column a unit
   reads. Record the outcome per pairing in `pairings.md`. A mismatch is a witness for a
   disproof; keep the smallest input that shows it.
2. Helper contracts (section 4).
3. Step contracts (section 5), each in its two parts: on the domain, and without the domain
   condition. Part (b) is not optional; it is where untested inputs are examined.
4. Stage contracts (section 3).
5. Flag contracts (section 6), closed rows (section 7), intent contracts (section 8).

For a contract expected to fail, use `negate`, prove the negation with the witness, and flag the
item false. The witness and one sentence on what differs go in the negation's text. That is where
findings live: in the blueprint, on the item they concern.

When a mismatch looks like a translation error rather than a difference between SAS and Python
(the Lean does not do what its source does), do not prove anything about it. Record the unit,
the input, what each of the Lean and the source gives, and move on.

Work through the list without stopping for sign-off. Stop only at the first check above, or if
the specification itself turns out to be unworkable (for example the conversion `Pl.toTable` loses
something every contract needs). A contract you cannot settle is left stated and unproved, with
a note; do not let it block the others.

Use subagents for independent contracts, at most four at once against the blueprint, each given
rules 1 to 6 verbatim. Have a separate reviewer, who did not write it, check every accepted
statement against the specification's text before its proof is started: does the Lean say exactly the
contract, with no extra hypothesis and no weaker conclusion?

## Final report

`report.md` in this folder, and the same in your last message:

- Per contract: item, kind (stage, step, helper, intent), result (proved for every number type;
  proved at ℝ; proved conditional; disproved; vacuous; not settled; skipped), assumptions used,
  and for a disproof the witness.
- The findings, most serious first: each a difference between SAS and Python, or a property the
  code fails, with the input that shows it and whether differential testing on the real data
  could have reached it.
- Suspected translation errors, with evidence.
- Pairs of preconditions where one side accepts an input the other rejects.
- Counts from `get_status`, and confirmation that no `zz_…` item remains.
