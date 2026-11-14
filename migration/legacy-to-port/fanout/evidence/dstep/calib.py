import polars as pl, math
J='/Users/cristophersalvi/GitHub/sas-migration/judge/'
sets={'real':(J+'reference',J+'reference'),'a':(J+'scenarios/edge_metrics_a',J+'reference/scenarios/edge_metrics_a'),'b':(J+'scenarios/edge_metrics_b',J+'reference/scenarios/edge_metrics_b'),'c':(J+'scenarios/edge_metrics_c',J+'reference/scenarios/edge_metrics_c')}
def f84(x): return f"{x:.4f}"
for k,(i,r) in sets.items():
    v=pl.read_csv(f'{i}/risk_scores_validation.csv')
    n=v.height
    v=v.with_columns(rk=pl.col('pd_logistic').rank('average')).with_columns(pred_bin=(pl.col('rk')*20/(n+1)).floor().cast(pl.Int64))
    agg=v.group_by('pred_bin',maintain_order=True).agg(sp=pl.col('pd_logistic').sum(),sd=pl.col('default_flag').sum(),bin_count=pl.len())
    unsorted=agg['pred_bin'].to_list()[:5]
    agg=agg.sort('pred_bin',maintain_order=True).with_columns(mean_predicted=pl.col('sp')/pl.col('bin_count'),mean_actual=pl.col('sd')/pl.col('bin_count')).select('pred_bin','mean_predicted','mean_actual','bin_count')
    mine=[f"{a},{f84(b)},{f84(c)},{d}" for a,b,c,d in agg.iter_rows()]
    ref=open(f'{r}/calibration_plot.csv').read().strip().split('\n')
    print(k,'rows',len(mine),'ref rows',len(ref)-1,'header',ref[0],'match',mine==ref[1:],'ref bins',[l.split(',')[0] for l in ref[1:]][:25],'group_by first-appearance order',unsorted)
    if mine!=ref[1:]:
        for a,b in zip(mine,ref[1:]):
            if a!=b: print('  ',a,'|',b)
