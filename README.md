# credit-risk-migration

The migration of a SAS credit-risk scoring pipeline to Python, with formal verification.

| Folder | What it is |
|---|---|
| `legacy/` | The SAS program being migrated, with its documentation (`MODEL_CARD.md`, `README.md`), data and outputs |
| `port/` | The Python port (`credit_risk`, polars) |
| `judge/` | The parity judge: runs both programs and compares their output files |
| `migration/` | The record: three kit migrations, the requirements, the proofs, the audit. Start at `migration/README.md` |

## Where `legacy/` comes from

`legacy/` is a copy of the repository `credit-risk-sas` at its only commit (`9f40a81`, tagged
`legacy-original` here). That repository is never changed by the migration. Corrections the
proofs require are made in `legacy/` here, so `git diff legacy-original HEAD -- legacy` (after
allowing for the move into `legacy/`) shows exactly what verification changed in the SAS. At
present nothing has been changed.

## Checking parity

    bash migration/legacy-to-port/parity/run_contract.sh out/parity

Every line must end in PASS.

## Method

The migration follows `logos-migration-kit`. All Lean lives in Logos blueprints
(`credit-risk-foundation`, `sas-credit-risk-spec`, `py-credit-risk-port`,
`credit-risk-requirements`), never in this repository.
