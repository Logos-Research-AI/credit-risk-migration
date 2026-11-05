# Gap inventory fan-out: review and audit record (prompt 02)

## Receipt
`wc -l migration/inventory.tsv` → `194 migration/inventory.tsv`: header + 193 rows, covering
462/462 sweep sites (`inventory_fanout.py merge` checks coverage; `finalize` derives
each status from the verdict files).

## Classification (7 shards, Opus)
| Shard | Rows | Sites |
|---|---|---|
| cmp-fe-predict | 35 | 68 |
| cmp-train-metrics | 18 | 58 (+S462) |
| arith | 51 | 80 |
| proc | 34 | 71 |
| dstep | 23 | 44 |
| modelstat-fit | 6 | required tables |
| modelstat-classify | 6 | 6 + required tables |

## Skeptic review (6 Opus reviewers, 2 independent per batch)
| Batch | Rows | Round 1 (CONFIRMED / EVIDENCE_DEFECT / RULEBOOK_CONFLICT / REFUTED) |
|---|---|---|
| fe-predict A / B | 81 | 71/6/4/0, 72/5/4/0 |
| train A / B | 50 | 44/5/1/0, 41/8/1/0 |
| metrics A / B | 42 | 30/10/1/1, 29/9/4/0 |

By row (worst verdict): 132 both CONFIRMED, 32 EVIDENCE_DEFECT, 8 RULEBOOK_CONFLICT, 1 REFUTED
(PSI division, polars `col / scalar`). The 33 flagged rows were revised once by their
classifiers; 8 consistency fixes were added. All 41 changed rows went back to the reviewers
that flagged them (or reviewer A of the batch): **41 confirmed, 0 contested**, so no row
became UNKNOWN through review.

## Joint audit (2 Opus auditors: audit.audit-fp.tsv, audit.audit-tm.tsv)
31 conflicts: 14 (FE/predict) + 17 (train/metrics).
- Inventory side: applied by a Sonnet fixer (51 rows, `fanout/audit-fixes.tsv`) and by the
  orchestrator on 8 batch-1 rows (TM-02, TM-07, TM-08, TM-09, FP-04, FP-14).
- Rulebook side: queued as A19–A31 in `rulebook-amendments.md` (A20 replaces A10).
- Batch-1 rows (DEV-006: one reviewer each at the first gate) got a full skeptic read in the
  audit: 6 defects found and fixed, none semantic in the FE/predict half.

## Experiments run by the orchestrator on ODA
- X03: PROC SQL INTO stores BEST8. text (A9).
- X04: SAS divides like IEEE (A13 stands); BEST12. rounds half up from 15 significant digits (A18).

## Open
- UNKNOWN: `train.sas printed_hl_partition.csv`, question Q2 (judge tolerance on HL Totals).
