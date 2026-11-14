# Formal verification of the migration

The migration kit's record is in `migration/`. This folder is the formal-verification part of
it: the legacy code is proved to meet the documented requirements, and the port is proved equal
to the legacy code. All Lean lives in Logos blueprints, never in files here.

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
  `informal-spec.md`), and what came back (`reports/`, `changes.md`).
- `workspaces/` (git-ignored): one folder per independent session, built by `workspaces.sh`.
  A session is started inside its workspace and told "Read PROMPT.md and carry it out".
- `guard.py`: the hook installed in every workspace. It blocks any tool call that touches a
  file of the project outside the workspace, or opens a blueprint the workspace must not see.
  This is what keeps the two translations independent.

## Sessions

| Workspace | Does | Sees |
|---|---|---|
| `requirements` | formalises the requirements, proves them consistent | the documentation only |
| `sas` | translates the SAS to Lean | the SAS, its outputs, the documentation |
| `python` | translates the port to Lean | the Python only |
| `prover` | states and proves or disproves the contracts | both workspaces (read only), both blueprints |

The coding agent, which fixes code on the prover's findings, works in the project itself.
