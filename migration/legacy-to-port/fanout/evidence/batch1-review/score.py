import polars as pl, numpy as np
import math
class chi2:
    @staticmethod
    def sf(s,df): return math.erfc(math.sqrt(s/2))
d=pl.read_csv('reference/model_features_train.csv',infer_schema_length=None)
y=d['default_flag'].to_numpy().astype(float)
def fit(cols):
    X=np.column_stack([np.ones(len(y))]+[d[c].to_numpy().astype(float) for c in cols])
    b=np.zeros(X.shape[1])
    for _ in range(100):
        p=1/(1+np.exp(-X@b)); W=p*(1-p)
        H=X.T@(X*W[:,None]); g=X.T@(y-p)
        s=np.linalg.solve(H,g); b+=s
        if np.max(np.abs(s))<1e-10: break
    p=1/(1+np.exp(-X@b)); return X,p
def score(X,p,c):
    z=d[c].to_numpy().astype(float); W=p*(1-p)
    Xa=np.column_stack([X,z]); I=Xa.T@(Xa*W[:,None]); U=Xa.T@(y-p)
    try:
        s=U@np.linalg.solve(I,U)
    except Exception as e: s=str(e)
    U2=z@(y-p); V=z@(z*W)-(X.T@(z*W))@np.linalg.solve(X.T@(X*W[:,None]),X.T@(z*W))
    return s,U2,V
model=['financial_health','flag_multiple_delinquencies','flag_high_debt_ratio','has_serious_delinquency']
X,p=fit(model)
for c in ['flag_serious_delinquency','age','total_risk_flags']:
    print(c,score(X,p,c))
# Step 1 p-value underflow check
X,p=fit([])
cands=['financial_health','has_delinquency','flag_multiple_delinquencies','total_late_payments','total_risk_flags','has_serious_delinquency','flag_serious_delinquency','num_late_90_plus']
for c in cands:
    s=score(X,p,c)[0]; print(c, s, chi2.sf(s,1))
