# Formal verification of the migration

The method is three migrations run with the same kit, tied together by proof:

| Migration | Judge | Kit record |
|---|---|---|
| SAS to Python (the port) | run both programs, compare the output files | `migration/` |
| SAS to Lean | run the Lean on real rows, compare with what SAS produced | `legacy-intent/kit-record/` |
| Python to Lean | run the Lean on real rows, compare with what the Python produced | `equivalence/kit-record/` |

Each follows the kit's steps: rulebook, gap inventory, stress test, then per unit an implementer,
two adversarial reviewers and a fixer. When the target is Lean the steps are adapted, not
shortened: the Lean lives in a Logos blueprint, never in files here, so a unit is built when
Logos accepts it, and the judge evaluates the Lean (`eval_decl`) on real numbers. The two
translators' briefs give the step-by-step adaptation.

What is not a migration: the requirements, the contracts and their proofs, the fixes that follow
a disproof, and the audit. The proofs show that the legacy code meets the documented
requirements and that the port equals the legacy code.

## Stages

| Stage | Folder | Blueprint | Done when |
|---|---|---|---|
| 1. Requirements: the documentation as formal requirements | `requirements/` | `credit-risk-requirements` | the requirements are proved consistent |
| 2. Legacy code verified: each requirement is a contract on the SAS; a disproof is a SAS bug, which is corrected | `legacy-intent/` | `sas-credit-risk-spec` (requirements pinned as profile) | every requirement is proved on the SAS |
| 3. Migration: the kit ports the corrected SAS | `migration/` (the kit's record) | none | the parity judge passes on every output file |
| 4. Equivalence: each Python output file is proved equal to the SAS one; a disproof is fixed in the Python | `equivalence/` | `py-credit-risk-port` (SAS blueprint pinned as profile) | every equivalence contract is proved |
| 5. Audit and write-up | `audit/` | none | signed off |

On this project stage 3, and one pass of stage 4, were done before stages 1 and 2.

## What is where

- `foundation/`: the types every blueprint shares (`credit-risk-foundation`).
- Each stage folder: the briefs given to its sessions, its specification (`requirements.md`,
  `informal-spec.md`), what came back (`reports/`, `changes.md`), and for the two Lean
  migrations the translator's kit record (`kit-record/`, copied from its workspace).
- `workspaces/` (git-ignored): one folder per independent session, built by `workspaces.sh`.
  A session is started inside its workspace and told "Read PROMPT.md and carry it out".
- `guard.py`: the hook installed in every workspace. It blocks any tool call that touches a
  file of the project outside the workspace, or opens a blueprint the workspace must not see.
  This is what keeps the two translations independent.

## Sessions

| Workspace | Does | Sees |
|---|---|---|
| `requirements` | formalises the requirements, proves them consistent | the documentation only |
| `sas` | migrates the SAS to Lean, with the kit | the SAS, its outputs, the documentation |
| `python` | migrates the port to Lean, with the kit | the Python only |
| `prover` | states and proves or disproves the contracts | both workspaces (read only), both blueprints |

The coding agent, which fixes code on the prover's findings, works in the project itself.
