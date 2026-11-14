import polars as pl
J='/Users/cristophersalvi/GitHub/sas-migration/judge/'
for k,d in [('real','reference'),('a','scenarios/edge_metrics_a'),('b','scenarios/edge_metrics_b'),('c','scenarios/edge_metrics_c')]:
    v=pl.read_csv(J+d+'/risk_scores_validation.csv',infer_schema=False)
    p=v['pd_logistic'].cast(pl.Float64)
    print(k,[int((p==t).sum()) for t in (0.3,0.4,0.5,0.6,0.7)], 'max',p.max(), 'n>=0.6',int((p>=0.6).sum()),'n>=0.7',int((p>=0.7).sum()))
    # first-appearance order of calibration bins
