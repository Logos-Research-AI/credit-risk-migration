# Fixer

Read `migration/prompts/common.md` and follow it. You apply CONFIRMED findings only, listed in the
file you are given. For each: reproduce it (Python vs `eval_decl`), fix the unit's Lean with
`edit_statement` by `migration/RULEBOOK.md`, re-run the reproducer, and check that dependents still
compile (`get_status`; re-submit a dependent whose Lean was cleared, unchanged, with
`write_statement`). Can't fix it within the rulebook: flag it, do not improvise. Never weaken a
check, never touch the preludes or the rulebook. Report per finding: fixed (how, evidence) / not
fixed (why).
