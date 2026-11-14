import polars as pl, numpy as np, sys
for s in ['reference','reference/scenarios/edge_metrics_a','reference/scenarios/edge_metrics_b','reference/scenarios/edge_metrics_c']:
    src = 'reference/risk_scores_validation.csv' if s=='reference' else s.replace('reference/','')+'/risk_scores_validation.csv'
    d=pl.read_csv(src,infer_schema_length=None)
    n=d.height; nd=d['pd_logistic'].n_unique()
    print('==',s,'rows',n,'distinct pd',nd,'dup rows',n-nd,'null pd',d['pd_logistic'].null_count(),'null y',d['default_flag'].null_count(), 'y vals', d['default_flag'].unique().to_list())
    d=d.sort('pd_logistic',maintain_order=True)
    y=d['default_flag'].to_numpy()
    G=(y==0).sum(); B=(y==1).sum()
    cg=np.cumsum(y==0); cb=np.cumsum(y!=0)
    ks=np.abs(cg/G-cb/B)
    m=ks.max(); idx=np.where(ks==m)[0]
    p=d['pd_logistic'].to_numpy()
    print(' max',m,'rows at max',len(idx),'cutoff',p[idx],'tie-run size at cutoff',[(p==p[i]).sum() for i in idx])
    # is max at end of tie run?
    for i in idx:
        run=np.where(p==p[i])[0]; print('  run',run.min(),run.max(),'i',i, 'ks over run max/min',ks[run].max(),ks[run].min())
    # alt order: reverse within ties
    d2=pl.read_csv(src,infer_schema_length=None).reverse().sort('pd_logistic',maintain_order=True)
    y2=d2['default_flag'].to_numpy(); ks2=np.abs(np.cumsum(y2==0)/G-np.cumsum(y2!=0)/B)
    print(' reversed-input max',ks2.max(), 'cutoffs', d2['pd_logistic'].to_numpy()[ks2==ks2.max()])
