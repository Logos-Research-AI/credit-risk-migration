# Round 5: witnesses for the stage contracts, and three restatements

`informal-spec.md` in this folder is now version 2.3. Read its header, the new "Witness
contracts" part of section 3, the two guarantees added to step frames in section 2, and section
9, your work list. `PROMPT.md` and the earlier round briefs still hold.

1. **W1 to W4.** One new contract item per stage, on the stage's `def:` item. The statement is an
   existence: an input and parameters such that every hypothesis of that stage's contracts holds.
   Write the hypotheses out exactly as the stage contracts have them (the same Lean, conjoined),
   so that nobody has to trust that two lists agree. Prove it at the real numbers on a concrete
   small input; no `Float` evaluation counts here. Where one stage's files have different
   hypothesis lists (ST2 with and without `invLink`; ST3 with and without the row bounds), take
   the union.
2. **S12(a), S12(b), S18(b).** Restate with the guarantees of section 2 and prove.
3. Touch nothing else.

`report-round5.md`: the result per item, and the counts from `get_status`. Update
`findings-for-code.md` only if something is newly disproved.
