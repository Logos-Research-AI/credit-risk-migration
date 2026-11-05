import polars as pl, numpy as np, math
def rank_groups(x, k, desc):
    s = pl.Series(x)
    r = (-s if desc else s).rank(method='average').to_numpy()
    n = len(x)
    return np.floor(r*k/(n+1)).astype(int)
scen={'real':('reference','reference'),'a':('scenarios/edge_metrics_a','reference/scenarios/edge_metrics_a'),'b':('scenarios/edge_metrics_b','reference/scenarios/edge_metrics_b'),'c':('scenarios/edge_metrics_c','reference/scenarios/edge_metrics_c')}
for name,(src,ref) in scen.items():
    v=pl.read_csv(f'{src}/risk_scores_validation.csv',infer_schema_length=None)
    t=pl.read_csv(f'{src}/risk_scores_train.csv',infer_schema_length=None)
    g=rank_groups(v['pd_logistic'].to_numpy(),10,True)
    dv=v.with_columns(decile=pl.Series(g))
    da=dv.group_by('decile',maintain_order=True).agg(total_count=pl.len(),defaults=pl.col('default_flag').sum(),min_pd=pl.col('pd_logistic').min(),max_pd=pl.col('pd_logistic').max()).sort('decile').with_columns(pl.col('decile')+1)
    r=pl.read_csv(f'{ref}/decile_analysis.csv',infer_schema=False)
    ok=(da['total_count'].cast(str).to_list()==r['total_count'].to_list()) and (da['defaults'].cast(str).to_list()==r['defaults'].to_list())
    print(name,'decile counts match:',ok, r.columns)
    if not ok: print(da); print(r)
    # PSI
    def bins(df):
        b=rank_groups(df['pd_logistic'].to_numpy(),10,False); n=len(b)
        return pl.DataFrame({'score_bin':b}).group_by('score_bin',maintain_order=True).agg((pl.len()/n).alias('pct'))
    a=bins(t).rename({'pct':'train_pct'}); bb=bins(v).rename({'pct':'valid_pct'})
    j=a.join(bb,on='score_bin',how='inner').sort('score_bin')
    j=j.with_columns(psi=(pl.col('train_pct')-pl.col('valid_pct'))*(pl.col('train_pct')/pl.col('valid_pct')).log())
    rp=pl.read_csv(f'{ref}/printed_psi_calculation.csv',infer_schema=False)
    print(' PSI',j['psi'].sum(), 'bins',j.height,'ref rows',rp.height, 'train bins',a.height,'valid bins',bb.height)
    print(' ref psi', rp.columns, rp.head(12).to_dicts() if name!='real' else rp['psi_component'].to_list() if 'psi_component' in rp.columns else rp)
    print(' mine', j.to_dicts())
    # calibration groups=20
    c=rank_groups(v['pd_logistic'].to_numpy(),20,False)
    cc=pl.DataFrame({'b':c}).group_by('b').len().sort('b')['len'].cast(str).to_list()
    rc=pl.read_csv(f'{ref}/calibration_plot.csv',infer_schema=False)
    print(' calib match', cc==rc['bin_count'].to_list())
