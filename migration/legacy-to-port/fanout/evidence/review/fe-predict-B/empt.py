import polars as pl
R='/Users/cristophersalvi/GitHub/sas-migration/'
for p in ['data/cs-test.csv','judge/scenarios/edge_predict/cs-test.csv','data/cs-training.csv']:
    d=pl.read_csv(R+p,infer_schema=False)
    print(p,d.height)
    for c in d.columns:
        e=d.filter(pl.col(c).is_null()|(pl.col(c)=='')|(pl.col(c)=='NA')).height
        if e: print('   ',c,e)
for p in ['judge/reference/test_predictions.csv','judge/reference/scenarios/edge_predict/test_predictions.csv','judge/reference/kaggle_submission.csv','judge/reference/scenarios/edge_predict/kaggle_submission.csv']:
    d=pl.read_csv(R+p,infer_schema=False)
    print(p,d.height, {c:d[c].null_count() for c in d.columns if d[c].null_count()})
    print('  E-cells', {c:d.filter(pl.col(c).str.contains('E')).height for c in d.columns if d.filter(pl.col(c).str.contains('E',literal=True)).height})
    if 'interest_rate' in d.columns:
        print(d.group_by('risk_grade','recommendation','interest_rate').len().sort('risk_grade'))
        print('pred on null pd', d.filter(pl.col('pd_logistic').is_null())['pred_logistic'].value_counts())
