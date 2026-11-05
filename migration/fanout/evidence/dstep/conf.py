import polars as pl
J='/Users/cristophersalvi/GitHub/sas-migration/judge/'
def best12(x):
    if x is None: return ''
    s=f"{x:.10f}".rstrip('0').rstrip('.')
    return s
def metrics(df, thr, pred_col=None):
    if pred_col is None:
        df=df.with_columns(predicted=pl.col('pd_logistic')>=thr)
        pred_col='predicted'
    cm=df.group_by(['default_flag',pred_col],maintain_order=True).len()
    def cell(d,p):
        return cm.filter((pl.col('default_flag')==d)&(pl.col(pred_col)==p))['len'].sum()
    TP,TN,FP,FN=cell(1,True),cell(0,False),cell(0,True),cell(1,False)
    acc=(TP+TN)/(TP+TN+FP+FN) if TP+TN+FP+FN>0 else None
    prec=TP/(TP+FP) if TP+FP>0 else None
    rec=TP/(TP+FN) if TP+FN>0 else None
    f1=2*(prec*rec)/(prec+rec) if (prec is not None and rec is not None and prec+rec>0) else None
    spec=TN/(TN+FP) if TN+FP>0 else None
    return [thr,acc,prec,rec,f1,spec], (TP,TN,FP,FN)
sets={'real':J+'reference','a':J+'scenarios/edge_metrics_a','b':J+'scenarios/edge_metrics_b','c':J+'scenarios/edge_metrics_c'}
refs={'real':J+'reference','a':J+'reference/scenarios/edge_metrics_a','b':J+'reference/scenarios/edge_metrics_b','c':J+'reference/scenarios/edge_metrics_c'}
for k,d in sets.items():
    for nm in ['risk_scores_validation.csv','risk_scores_train.csv']:
        v=pl.read_csv(f'{d}/{nm}',infer_schema_length=0)
        print(k,nm,v.height,'default_flag values',sorted(v['default_flag'].unique().to_list()),'empty pd',(v['pd_logistic'].is_null()|(v['pd_logistic']=='')).sum())
    v=pl.read_csv(f'{d}/risk_scores_validation.csv').with_columns(pl.col('default_flag').cast(pl.Int64))
    ref=open(f'{refs[k]}/threshold_analysis.csv').read().strip().split('\n')[1:]
    ok=True
    for thr,line in zip([0.3,0.4,0.5,0.6,0.7],ref):
        row,c=metrics(v,thr)
        mine=','.join(best12(x) for x in row)
        if mine!=line: ok=False; print('  DIFF',thr,mine,'|',line,c)
    print(k,'threshold_analysis match (10-dec approx of BEST12):',ok)
# train model_summary
for nm,col in [('risk_scores_train.csv','train'),('risk_scores_validation.csv','valid')]:
    v=pl.read_csv(J+'reference/'+nm)
    row,c=metrics(v,None,'pred_logistic') if False else metrics(v.with_columns(pl.col('pred_logistic')==1),0,'pred_logistic')
    print(col,c,[f"{x:.4f}" for x in row[2:4]+[row[4],row[1]]])
print(open(J+'reference/model_summary.csv').read())
