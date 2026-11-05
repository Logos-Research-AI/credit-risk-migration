# Inventory evidence scripts

Copied from the session scratchpad, which is not durable. Inventory rows cite them as
`scratchpad/fan/<shard>/<script>`, `scratchpad/invB/<script>` (batch 1, review 2) or
`scratchpad/<script>`. Those paths map to:

| Cited as | Lives at |
|---|---|
| `scratchpad/fan/<shard>/<script>` | `migration/fanout/evidence/<shard>/<script>` |
| `scratchpad/invB/<script>` | `migration/fanout/evidence/batch1-review/<script>` |
| `scratchpad/divcheck.py`, `scratchpad/assoc_cand.py` | `migration/fanout/evidence/` |

Run them from `judge/` with `uv run python <path>`. Most read `judge/reference/` with relative
paths. Generated candidate folders (CSV outputs) were not copied: rerun the script that
produced them.
