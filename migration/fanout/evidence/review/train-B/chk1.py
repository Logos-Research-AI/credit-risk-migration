import sys; sys.path.insert(0,'/Users/cristophersalvi/GitHub/sas-migration/judge')
import polars as pl
from compare import sas_best12
R='/Users/cristophersalvi/GitHub/sas-migration/judge/reference/'
for tag in ['train','validation']:
    d=pl.read_csv(R+f'risk_scores_{tag}.csv',infer_schema=False)
    g=pl.col('risk_grade')
    rec=pl.when(g.is_in(['A','B'])).then(pl.lit('Approve')).when(g=='C').then(pl.lit('Review')).otherwise(pl.lit('Decline'))
    br=pl.lit(0.05)
    ir=pl.when(g=='A').then(br).when(g=='B').then(br+0.02).when(g=='C').then(br+0.04).when(g=='D').then(br+0.07).when(g=='E').then(br+0.10).otherwise(br+0.15)
    x=d.with_columns(rec2=rec, ir2=ir.map_elements(lambda v: f'{100*v:.2f}%',return_dtype=pl.String))
    print(tag,'rec mism',(x['rec2']!=x['recommendation']).sum(),'ir mism',(x['ir2']!=x['interest_rate']).sum(), 'base_rate', x['base_rate'].unique().to_list(), x['base_score'].unique().to_list(), x['score_range'].unique().to_list())
    # pred from pd
    pd_=x['pd_logistic'].cast(pl.Float64)
    print(' pred mism', ((pd_>=0.5).cast(pl.Int64).cast(pl.String)!=x['pred_logistic']).sum())
    cm=(x.with_columns(pl.col('default_flag').cast(pl.Int64),pl.col('pred_logistic').cast(pl.Int64))
        .group_by(['default_flag','pred_logistic'],maintain_order=True).agg(COUNT=pl.len())
        .sort(['default_flag','pred_logistic'],maintain_order=True))
    cm=cm.with_columns(PERCENT=100*pl.col('COUNT')/pl.col('COUNT').sum())
    ref=pl.read_csv(R+f'printed_confusion_{tag}.csv',infer_schema=False)
    out=[[str(a),str(b),str(c),sas_best12(p)] for a,b,c,p in cm.iter_rows()]
    print(' cm text equal', out==[list(r) for r in ref.iter_rows()], out)
    # alt: COUNT/N*100
    print(' alt', [sas_best12(c/cm['COUNT'].sum()*100) for c in cm['COUNT']])
    t={(a,b):c for a,b,c,_ in cm.iter_rows()}
    TP,TN,FP,FN=t.get((1,1),0),t.get((0,0),0),t.get((0,1),0),t.get((1,0),0)
    p=TP/(TP+FP); r=TP/(TP+FN); f=2*(p*r)/(p+r); a=(TP+TN)/(TP+TN+FP+FN)
    print(' metrics',[f'{v:.4f}' for v in (p,r,f,a)], p, r, f, a)
f=pl.read_csv(R+'final_model_output.csv',infer_schema=False)
t=pl.read_csv(R+'risk_scores_train.csv',infer_schema=False)
print('fmo == subset', f.equals(t.select(f.columns)), [c for c in t.columns if c in f.columns]==f.columns)
print(pl.read_csv(R+'model_summary.csv',infer_schema=False).row(0))
