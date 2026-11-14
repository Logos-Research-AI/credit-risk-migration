# The migration record

The method is three migrations run with the same kit, tied together by proof:

| Migration | Judge | Kit record |
|---|---|---|
| Legacy to port (SAS to Python) | run both programs, compare the output files | `legacy-to-port/` |
| Legacy to Lean | run the Lean on real rows, compare with what SAS produced | `legacy-to-lean/` |
| Port to Lean | run the Lean on real rows, compare with what the Python produced | `port-to-lean/` |

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
| 2. Legacy code verified: each requirement is a contract on the SAS; a disproof is a SAS bug, which is corrected | `legacy-to-lean/`, `proofs/legacy-meets-requirements/` | `sas-credit-risk-spec` (requirements pinned as profile) | every requirement is proved on the SAS |
| 3. Migration: the kit ports the corrected SAS | `legacy-to-port/` | none | the parity judge passes on every output file |
| 4. Equivalence: each Python output file is proved equal to the SAS one; a disproof is fixed in the Python | `port-to-lean/`, `proofs/port-equals-legacy/` | `py-credit-risk-port` (SAS blueprint pinned as profile) | every equivalence contract is proved |
| 5. Audit and write-up | `audit/` | none | signed off |

On this project stage 3, and one pass of stage 4, were done before stages 1 and 2.

## What is where

- `legacy-to-port/`, `legacy-to-lean/`, `port-to-lean/`: one kit record per migration (rulebook,
  inventory, manifest, reviews, evaluation). The two Lean ones also hold the translator's brief
  and are copied from the translator's workspace (`SOURCE.md` says at which commit).
- `requirements/`: `requirements.md` with the owner's rulings, the formaliser's brief, its report.
- `proofs/legacy-meets-requirements/`, `proofs/port-equals-legacy/`: the contracts to prove
  (`informal-spec.md`), the prover's and coding agent's briefs, and what came back (`reports/`,
  `changes.md`).
- `audit/`: the orchestrator's audit, and later the write-up.
- `foundation/`: the types every blueprint shares (`credit-risk-foundation`).
- `workspaces/` (git-ignored): one folder per independent session, built by `workspaces.sh`.
  A session is started inside its workspace and told "Read PROMPT.md and carry it out".
- `guard.py`: the hook installed in every workspace. It blocks any tool call that touches a
  file of the project outside the workspace, or opens a blueprint the workspace must not see.
  This is what keeps the two translations independent.

Records written before 2026-11-14 cite paths as they were then: the legacy files and
`credit_risk/` at the repository root, the legacy-to-port record directly in `migration/`, and
workspaces named `sas` and `python` under `sas-migration-formal/`.

## Sessions

| Workspace | Does | Sees |
|---|---|---|
| `requirements` | formalises the requirements, proves them consistent | the documentation only |
| `legacy` | migrates the SAS to Lean, with the kit | the SAS, its outputs, the documentation |
| `port` | migrates the port to Lean, with the kit | the Python only |
| `prover` | states and proves or disproves the contracts | both workspaces (read only), both blueprints |

The coding agent, which fixes code on the prover's findings, works in the project itself.
