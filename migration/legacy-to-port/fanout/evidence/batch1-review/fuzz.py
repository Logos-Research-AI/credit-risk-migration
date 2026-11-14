import polars as pl, numpy as np
d=pl.read_csv('reference/risk_scores_train.csv',infer_schema_length=None)
y=d['default_flag'].to_numpy(); p=d['pd_logistic'].to_numpy()
ev=np.sort(p[y==1]); ne=np.sort(p[y==0]); N=len(ev)*len(ne)
def stat(eps,rel=False):
    e=eps*ev if rel else eps
    lo=np.searchsorted(ne,ev-e,side='left'); hi=np.searchsorted(ne,ev+e,side='right')
    T=(hi-lo).sum(); C=lo.sum(); D=N-C-T
    return T, round(100*C/N,6), round(100*D/N,6), 100*T/N
print('target T=280 C=85.922064 D=14.077895')
for eps in [1e-12,1e-11,5e-11,1e-10,2e-10,5e-10,1e-9,2e-9,5e-9,1e-8]:
    print('abs',eps,stat(eps))
for eps in [1e-12,1e-11,1e-10,1e-9,1e-8,1e-7]:
    print('rel',eps,stat(eps,True))
for eps in [1.02e-8,1.05e-8,1.1e-8,1.2e-8,1.5e-8]:
    print('abs',eps,stat(eps))
def rstat(k):
    q=np.round(p/k)*k; e=np.sort(q[y==1]); n=np.sort(q[y==0])
    lo=np.searchsorted(n,e,'left'); hi=np.searchsorted(n,e,'right'); T=(hi-lo).sum(); C=lo.sum()
    return T, round(100*C/N,6), round(100*(N-C-T)/N,6)
for k in [1e-8,2e-8,1e-7/8]:
    print('round exported',k,rstat(k))
