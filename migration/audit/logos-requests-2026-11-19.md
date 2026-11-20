# Requests to Logos, 2026-11-19

From running Logos MCP (Staging) on a full verification and migration (about 500 items across
four blueprints, Nov 2026). Ordered by the wall-clock time each would save.

## 1. Refresh a profile through the API, and recompile what it touches

Today a profile refresh is an operation in the Logos UI only. Every time a requirement or a
legacy definition changed, the run stopped until the owner could refresh (hours, several times).

A refresh also clears nothing: proofs that read through the profile keep "proved" against the old
copy. After one refresh, 5 of 37 "proved" proofs no longer compiled; we found them only by
resubmitting every proof by hand.

Asked:
- an MCP tool to refresh a blueprint's profile (or an option to keep it in sync automatically);
- on refresh, mark the items that read a changed declaration as cleared (as an edit in the same
  blueprint does), or recompile them and report which fail.

## 2. Batch operations

Each call costs about 17 s at the median (`check_decl`), more under load. A routine resubmission
of 30 cleared items from their drafts is 60-90 calls. Asked: batch versions of `submit_statement`,
`submit_solution` and `check_decl` (a list of items, one result per item), and a way to recompile
every proof of a blueprint in one call.

## 3. `eval_decl` refusals lose their message

When the server refuses an `eval_decl` call, the client sees only an output-schema error
("Structured content does not match the tool's output schema ... data/success must be equal to
constant"), so the reason is lost. Many formalized code items were refused for a reason we could
not see; the same declarations run when called from another item. Details, calls and inputs:
`migration/port-to-lean/diffeval/eval_decl-errors-2026-11-18.md`. Also: a tactic block (`by ...`)
in an input never elaborates.

## 4. Reading large items

`get_items` refuses an item over about 30 KB (`response_too_large`); our longest proofs are 33-35
KB. `read_scratch` with line ranges works around it. Asked: the same paging on `get_items`.

## 5. Source references (resolved)

`update_item_source` on Staging refused file and line spans until 2026-11-18 (server build without
PR 6076); it now accepts them. Listed so the fix is confirmed on the other servers.

## 6. Measured: Lean-compiling calls queue on the server (added 2026-11-19)

From 13,000 Logos calls in our agents' transcripts (Nov 15-19, Staging), median latency by the
number of OUR OWN Lean-compiling calls in flight at the moment of the call:

| call | alone | 2-3 in flight | 4-7 | 8+ |
|---|---|---|---|---|
| submit_statement | 14 s | 29 s | 37 s | 61 s |
| write_statement | 10 s | 17 s | 35 s | 74 s |
| check_decl | 7 s | 11 s | 16 s | 26 s |

Latency does not depend on the size of the input. Calls that compile no Lean (get_items,
read_scratch, edit_solution_draft, get_status) stay at 1-3 s whatever the load. Total throughput
of compiling calls stops growing above about 4 in flight: the server appears to compile about 4
at a time for us and queue the rest. A call alone still costs 7-14 s, which looks like loading
the blueprint's environment on every call.

Asked: (a) how many compiles run in parallel per user / blueprint, and can it be raised;
(b) keep a blueprint's compiled environment warm between calls; (c) the batch calls of item 2.

## 7. Added 2026-11-20, from the credit-risk close and two formalisation test runs (Staging)

7a. **Edits on a shared solution draft conflict.** `edit_solution` and `edit_solution_draft` both
    refused an edit without `expected_revision` ("Scratch revision conflict. Read the current draft
    and retry explicitly."), and `edit_solution_draft` requires it in its schema, while the
    server's own instructions say a revisionless edit applies to the latest draft. With several
    agents each editing a different helper of one draft, edits keep colliding. Asked: apply
    revisionless edits to the latest draft as documented, or better, apply any edit whose
    `old_string` is unique without a conflict; otherwise correct the documentation.
7b. **Diagnostics of one declaration.** Each edit returns every other declaration's "contains
    `sorry`" error with its code (about 11 KB per edit on a 1,100-line draft). Asked: an option to
    return diagnostics for a line range or named declarations only.
7c. **Find a declaration in a draft.** A `read_scratch` lookup by declaration name returning its
    current line range and text (drafts of 1,100+ lines move while others edit).
7d. **Proof check without the proof text.** `get_items` with `proof_lean` on three proved items
    was 144 KB and refused (`response_too_large`). Asked: a per-item `proof_has_sorry` / axioms
    flag, or a size-bounded summary.
7e. **Quote matching on accents.** `add_item` refused a PDF quote containing P̃ (the text layer
    splits the tilde); only `[...]` matched. Asked: normalise combining accents (NFC/NFKD).
7f. **A clear refusal on remote servers.** `upload_source_file` could fail with an explicit
    "remote server: use begin_source_upload", so a client can tell where the server is.
7g. **`check_decl` schema mismatch.** The published schema takes `decl` (a string); the server
    asks for `decls` (a list) and then refuses a list as a string. Every call failed (reported
    by several agents, 2026-11-19/20).
7h. **Long submissions time out on the client.** `submit_solution` of an 8,300-line proof timed
    out on the client on every try (with 503s in between), though the server finished; the
    client cannot see the compile result. Asked: an asynchronous submit with a job id, or a
    longer timeout, and the accepted revision in `get_items`.
7i. **`get_status` count.** It reported 369 items and 368 statements formalized with nothing left
    to write; every one of the 369 ids, fetched one by one, is formalized or proved.

## 8. The blueprint as the agents' shared record (2026-11-20)

The owner wants the blueprint, not local Markdown files, to be where translators, reviewers,
fuzzers and provers read and write what they need to coordinate. Today an item holds its texts,
Lean, code, dependencies, state and one scratch draft. Everything else lives in files the kit
writes beside the blueprint, some of it repeating what the blueprint already holds. What we
would need to move it onto the blueprint:

- **8a. Item notes that do not clear Lean.** Editing statement_text or proof_text clears the
  item's Lean and its dependents, so it cannot carry working notes. We need a per-item notes
  thread (author, role, time) for review verdicts, fuzz results with their receipt, translator
  notes, open questions and their answers.
- **8b. Labels on items, queryable.** "reviewed", "fuzzed (N cases, 0 differences)",
  "owner ruling R12", "carrier": set by an agent, filtered in get_status/get_items, so a
  script can ask "which translated items are not yet reviewed".
- **8c. Blueprint-level documents.** The rulebook (decided language rules with evidence), the
  plan (units, waves, dependencies), the boundary of the claim and the owner's rulings: one
  shared, versioned text per blueprint that every agent of that blueprint reads.
- **8d. A change feed.** "What changed since revision N": items stated, proved, cleared (and by
  which edit), notes added. Agents coordinate on it instead of polling get_status.
- **8e. Bulk item creation.** Creating 102 planned items took one agent 18 minutes and 159
  calls (add_code, update_item_source, connect per item).
- **8f. More than one declaration per code item** (a prelude unit with several small defs is
  refused: "only one is allowed"), or a way to group them; one item per tiny declaration
  nearly doubled the agents of a COBOL translation.
- **8g. Proof state follows its dependencies.** Two contracts stayed TheoremProved while a
  lemma their proofs use was TheoremStated after a definition edit cleared it.
- **8h. Per-agent drafts on one item** (repeats 7a in another form): agents proving parts of
  one long proof need their own drafts, merged by the item's owner.
- **8i. What the Python subset of LogosEmbeddings covers.** A port written inside the subset the
  deterministic translator handles would need no hand translation and no translation checks.
  Which constructs and libraries does it accept (pandas, polars, numpy, decimal, csv, datetime),
  and does it run on Staging with Judging and Fuzzing on?
- **8j. Code items with source locations in several files.** A batch job's item spans its JCL
  and the PROC it calls; a setup step spans nine JCL files. add_code/update_item_source accept
  locations in one file only ("its locations must all be in one file"), so these items cannot
  carry their sources on the blueprint.
- **8k. The accepted Lean of a cleared item, or a restore call.** A change to a shared
  definition clears the accepted Lean of every item that depends on it (get_items returns null).
  Only the last draft survives, and it can be a rejected one. Re-accepting the dependents then
  needs a copy taken before the change. Lean must not leave the blueprint, so the kit now writes
  each dependent's accepted Lean as its own draft just before the change. Wanted: the item's
  revision history (accepted Lean by revision), or restore(item, revision) that resubmits it
  against the new dependencies.
