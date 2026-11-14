# Standing rules for every agent in this workspace (read first)

ISOLATION (overrides convenience). You translate or review a SAS-to-Lean translation. A separate
team translates a Python port of the same code and a third proves the two equivalent; that only
means something if the translations are independent. So: never read or search
`/Users/cristophersalvi/GitHub/sas-migration` or `/Users/cristophersalvi/GitHub/sas-migration-formal/python`;
never look for the Python port anywhere (disk or web); never open or search any Logos blueprint
other than `sas-credit-risk-spec` (id `a490bc52-8080-49b4-a6f3-8d3c4d29754a`) and
`credit-risk-foundation`. `judge/README.md` mentions the port in places: use it only for what
it says about SAS.

Workspace: `/Users/cristophersalvi/GitHub/sas-migration-formal/sas`. You may read the four `.sas`
scripts, `MODEL_CARD.md`, `README.md`, `judge/reference/`, `judge/scenarios/`, `experiments/`,
`foundation/`, and `migration/` (RULEBOOK.md, inventory.tsv, manifest.tsv, evidence/sas-docs.md).

Tools: the MCP server named `logos-mcp` only (never the "claude.ai Logos MCP" servers). Load
what you need with ToolSearch, e.g.
`select:mcp__logos-mcp__get_items,mcp__logos-mcp__get_lean,mcp__logos-mcp__write_statement,mcp__logos-mcp__edit_statement,mcp__logos-mcp__read_scratch,mcp__logos-mcp__check_decl,mcp__logos-mcp__eval_decl,mcp__logos-mcp__add_precond,mcp__logos-mcp__get_status`.
Every call takes `blueprint_id = a490bc52-8080-49b4-a6f3-8d3c4d29754a`.

`migration/RULEBOOK.md` is read-only. If a rule is wrong or missing, do not edit it and do not
work around it: say so in your report under "Amendments proposed". Never keep Lean in local
files. Never change blueprint settings. Never add, remove or edit an item you were not assigned.
Never edit the SAS files, `judge/`, `experiments/` or `.claude/`.
