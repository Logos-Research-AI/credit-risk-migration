# Common brief for every agent in this workspace

Workspace: /Users/cristophersalvi/GitHub/sas-migration-formal/python (Python package `credit_risk/`,
a port of a SAS pipeline). We translate the Python to Lean 4 in the Logos blueprint
`py-credit-risk-port`, id `b41b22d4-720d-4290-b593-39ceab961986`, through the `logos-mcp` MCP tools
(load them with ToolSearch, e.g. `select:mcp__claude_ai_Logos_MCP_Staging__get_items,mcp__claude_ai_Logos_MCP_Staging__get_lean,mcp__claude_ai_Logos_MCP_Staging__write_statement,mcp__claude_ai_Logos_MCP_Staging__edit_statement,mcp__claude_ai_Logos_MCP_Staging__read_scratch,mcp__claude_ai_Logos_MCP_Staging__eval_decl,mcp__claude_ai_Logos_MCP_Staging__get_status,mcp__claude_ai_Logos_MCP_Staging__check_decl,mcp__claude_ai_Logos_MCP_Staging__add_code,mcp__claude_ai_Logos_MCP_Staging__add_precond,mcp__claude_ai_Logos_MCP_Staging__connect`).
Use only the `mcp__claude_ai_Logos_MCP_Staging__*` tools (since 2026-11-12 the local `logos-mcp` server is discontinued).

ISOLATION (mandatory, overrides convenience):
- Never read `/Users/cristophersalvi/GitHub/sas-migration` or
  `/Users/cristophersalvi/GitHub/sas-migration-formal/sas`. Never look for the SAS code or its outputs
  anywhere. Never open or search any Logos blueprint other than `py-credit-risk-port` and
  `credit-risk-foundation`.
- Comments and docstrings in the Python say what SAS does. They are claims, not your source.
  Translate / judge what the Python code does when it runs.
- The shared types are in `foundation/foundation.tex` (`Tabular.RealLike`, `Cell`, `Row`, `Table`).
  Never redefine or work around them.
- Never keep Lean in local files. Never edit `.claude/settings.json`, `CLAUDE.md`, `PROMPT.md`,
  `migration/RULEBOOK.md`. Never run git commands that change the repository.
- Never edit the items `def:ExprOrNum` (polars prelude `Pl`) or `def:FloatArray_` (numpy prelude
  `Np`): changing them clears every dependent item. If you think a prelude rule is wrong or
  missing, say so in your report with the evidence.

Read first: `migration/RULEBOOK.md` (whole), then the Lean of the preludes with
`get_items(item_ids=["def:ExprOrNum"], fields=["statement_lean"])` and the same for
`def:FloatArray_`. Python environment: `uv run python ...` from the workspace root (polars 2.1.0,
numpy 2.5.4). Put throwaway scripts in the scratchpad directory
`/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration-formal-python/aa9ba63a-dfbb-4dbd-bc0a-805359ea00aa/scratchpad`.

Evaluating Lean exactly: read `migration/diffeval/README.md` and use its helpers (`leanterm.py`,
`kit.py`, `suite.py`, `compare.py`). `eval_decl` resolves `decl` ONLY among the declarations of the
item it evaluates, but the input terms may mention anything that item depends on. So evaluate
units through the carrier item: `eval_decl(item_id="def:zz_carrier", decl="zz_carrier", inputs=[...])`
where each input is a term of type `List Int` built from the unit's result with the kit's digest /
token lambdas (README modes `digest` and `tokens`; use `def:zz_carrier` / `zz_carrier` wherever the
README says `def:FloatArray_` / `Np.cumsumInt`; `zz_carrier` is the identity, so results are the
values themselves, not running sums: tell `compare.py`/`suite.py` accordingly or adapt the call).
The carrier must depend on the unit: if `eval_decl` cannot see your unit, call
`connect(item_id="def:zz_carrier", depends_on=["def:<your unit>"])` and, if that cleared the
carrier, re-submit it unchanged: `write_statement("def:zz_carrier", "-- migration/diffeval/carrier.py:12-13 (harness only; removed before the freeze)\ndef zz_carrier (xs : List Int) : List Int := xs")`.
Pass the number type as `(α := Float)`; build floats with `(Float.ofBits N)`; never print a Float
(6 decimals only). Never add helper declarations to a unit just to evaluate it.


UPDATE 2026-11-12 (re-translation after commit 7927af7). The blueprint now also holds `thm:`,
`neg:` and `def:wf_*` items that belong to another team: never read, write, edit or remove them.
`write_code` / `write_statement` on a unit clears the Lean of its dependents (the result lists
them in `cleared`); that is expected: do NOT restore cleared items other than the ones your brief
names (the orchestrator restores the rest at the end). The carrier `def:zz_carrier` no longer
exists: use the carrier item your brief names (same identity function, same use). Judging is on:
`write_code` the new source of a unit first, then `write_statement` its Lean.
