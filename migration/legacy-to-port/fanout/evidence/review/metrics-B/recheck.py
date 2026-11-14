B='/Users/cristophersalvi/GitHub/sas-migration/migration/fanout/'
rows=[l.rstrip('\n').split('\t') for l in open(B+'recheck.metrics-B.tsv')][1:]
assert len(rows)==9
V={
1:("CONFIRMED","judge/reference/listings/metrics_calculation.sas.log:1186-1192","Fixed. TauA range is now 0.0298..0.0892, and one D8. helper covers all seven columns, matching the export code. The new lst:39-41 and train.sas.lst:1334-1336 citations check out (train.sas has no roccontrast and prints the same table). My independent recompute still matches all 4 files byte-for-byte."),
2:("CONFIRMED","metrics_calculation.sas:125","Fixed. :125 is now correctly named S462. MISSING_NEVER holds on all 12 metrics input files, and the exact-threshold counts are confirmed. Residual note only: the signature should follow the macro row (threshold, suffix, logit_scored_valid)."),
3:("CONFIRMED","migration/fanout/evidence/arith/met.py:6-9","Fixed. 20 rows = 5 thresholds x 4 sets, and there is one polars form. MISSING_NEVER is correct: the denominator is 45000/3000. Trivial: 'below' should read 'above'."),
4:("CONFIRMED","judge/compare.py:160,276","Fixed. :160 is fill_null('') and :276 is the exact-token rule. The reached empty/'0' cells are verified."),
5:("CONFIRMED","migration/fanout/evidence/arith/met.py:6-9","Fixed. The count is 20, and it uses the single polars form shared with the comparison row. A zero divisor is reached and correctly guarded."),
6:("CONFIRMED","metrics_calculation.sas:148-149","Fixed. The count is 20. TP+FN = 3018/323/332/353 is verified, so recall is never missing."),
7:("CONFIRMED","metrics_calculation.sas:150","Fixed. It now uses sas_compat.gt per A2, identical to the comparison row, and the count is 20. Missing-p and p=r=0 both give an empty f1 in the references."),
8:("CONFIRMED","metrics_calculation.sas:152-153","Fixed. The count is 20. Non-defaults are 41982/2677/2668/2647, so specificity is never missing."),
9:("CONFIRMED","metrics_calculation.sas:75-77","Fixed. It states the in-place PROC SORT, so the bins are already ascending, with the explicit sort kept as a guard. sum/count means now match the other calibration rows. It reproduces all 4 references (my full.py)."),
}
with open(B+'review.metrics-B.recheck.tsv','w') as f:
    f.write('file\tsymbol\tsource_construct\tverdict\tcited_line\treason\n')
    for i,r in enumerate(rows,1):
        v,c,w=V[i]; f.write('\t'.join([r[0],r[1],r[2],v,c,w])+'\n')
