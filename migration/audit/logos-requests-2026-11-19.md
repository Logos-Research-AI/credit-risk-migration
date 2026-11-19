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
