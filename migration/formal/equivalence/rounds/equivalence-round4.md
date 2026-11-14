# Round 4: the tie constant, and five restatements

`informal-spec.md` in this folder is now version 2.2. Read its header and section 9, which is
your work list; sections 1 (the `best8` link) and 4 (H10) changed by one clause each. `PROMPT.md`
and the earlier round briefs still hold.

## First check. STOP if it fails.

From `def:roc_association`, `check_decl Sas.rocTops` must show the corrected constant,
`3184525836262887 / 302231454903657293676544`, not `10536712127723509e-24`. If it still shows the
old one, the profile has not been refreshed: stop and tell me.

Then `get_status`: refreshing the profile may have cleared proofs that depend on SAS definitions.
List what lost its proof.

## What to do

1. Re-prove whatever the refresh cleared. Verdicts are not expected to change.
2. Settle the ten contracts section 9 lists as open.
3. Restate the contracts section 9 lists as restated, text first, with the judge on.
4. Touch nothing else.

## Report

`report-round4.md`: per contract touched, the result; the table of the fourteen stage files; counts
from `get_status`. Update `findings-for-code.md` only if something is newly disproved. Also clean
up what round 3 reported as stale in your own items: the out-of-date remarks in the texts of H8,
H10 and S25(b), the commented-out lemmas in proof files where removing them does not clear a
proof, and the stale proof edge from ST1 train to S5(a) if it can be removed safely.
