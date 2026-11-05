import csv, sys, collections
sys.path.insert(0,'/Users/cristophersalvi/GitHub/sas-migration/judge')
from compare import sas_best12
def e12(x):
    if x!=0 and abs(x)<1e-5:
        exp=int(f"{abs(x):e}".split('e')[1])
        for _ in range(2):
            es=f"E{exp}"; w=12-len(es)-(x<0)
            s=f"{abs(x)/10**exp:.{w-2}f}"
            if s.startswith('10'): exp+=1; continue
            break
        return ('-' if x<0 else '')+s.rstrip('0').rstrip('.')+es
    return sas_best12(x)
R='/Users/cristophersalvi/GitHub/sas-migration/judge/reference/'
for f in ['test_predictions.csv','kaggle_submission.csv','scenarios/edge_predict/test_predictions.csv','scenarios/edge_predict/kaggle_submission.csv','model_features_train.csv','model_features_validation.csv']:
    rows=list(csv.reader(open(R+f))); h=rows[0]; bad=collections.Counter(); n=0
    for r in rows[1:]:
        for c,v in zip(h,r):
            if c in ('risk_grade','recommendation'): continue
            if c=='interest_rate':
                ok = v==f"{round(float(v[:-1]),2):.2f}%"
            elif v=='': ok=True
            else: ok = e12(float(v))==v
            n+=1
            if not ok: bad[c]+=1
    print(f, n, dict(bad))
