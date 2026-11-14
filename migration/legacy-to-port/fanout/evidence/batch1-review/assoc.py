import polars as pl, numpy as np
d=pl.read_csv('reference/risk_scores_train.csv',infer_schema_length=None)
y=d['default_flag'].to_numpy(); 
def assoc(p,y,label):
    ev=np.sort(p[y==1]); ne=np.sort(p[y==0])
    # for each event, count nonevents with lower p (concordant), equal (tied)
    lo=np.searchsorted(ne,ev,side='left'); hi=np.searchsorted(ne,ev,side='right')
    C=lo.sum(); T=(hi-lo).sum(); N=len(ev)*len(ne); D=N-C-T
    n=len(p)
    print(label,'pairs',N,'C%',100*C/N,'D%',100*D/N,'T%',100*T/N,'Tpairs',T,'SomersD',(C-D)/N,'Gamma',(C-D)/(C+D),'Tau-a',(C-D)/(n*(n-1)/2),'c',(C+0.5*T)/N)
p=d['pd_logistic'].to_numpy()
assoc(p,y,'exported')
assoc(np.round(p/0.002)*0.002,y,'bin0.002')
# refit final model fully converged
cols=['credit_utilization_capped','debt_ratio_capped','has_delinquency','has_serious_delinquency','log_monthly_income','num_real_estate_loans','num_dependents','income_per_dependent','credit_lines_per_person','flag_high_utilization','flag_very_high_utilization','flag_very_high_debt_ratio','flag_recent_late_payments','flag_multiple_delinquencies','flag_few_credit_lines','credit_util_category','financial_health','age_income_interaction']
X=np.column_stack([np.ones(len(y))]+[d[c].to_numpy().astype(float) for c in cols]); yf=y.astype(float)
b=np.zeros(X.shape[1])
for _ in range(100):
    q=1/(1+np.exp(-X@b)); W=q*(1-q); s=np.linalg.solve(X.T@(X*W[:,None]),X.T@(yf-q)); b+=s
    if np.max(np.abs(s))<1e-10: break
eta=X@b; q=1/(1+np.exp(-eta))
print('max|q-p|',np.abs(q-p).max())
assoc(q,y,'fullprec')
assoc(eta,y,'eta')
for k in [1e-6,1e-7,1e-8,1e-9,1e-10, 1e-5]:
    assoc(np.round(q/k)*k,y,f'round{k}')
ev=np.sort(q[y==1]); ne=np.sort(q[y==0]); N=len(ev)*len(ne)
for eps in [1e-8,1.05e-8,1.1e-8]:
    lo=np.searchsorted(ne,ev-eps,'left'); hi=np.searchsorted(ne,ev+eps,'right'); T=(hi-lo).sum(); C=lo.sum()
    print('fullprec fuzz',eps,T,100*C/N,100*(N-C-T)/N,100*T/N)
