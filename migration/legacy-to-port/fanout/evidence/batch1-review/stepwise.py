import polars as pl, numpy as np, math
d=pl.read_csv('reference/model_features_train.csv',infer_schema_length=None)
y=d['default_flag'].to_numpy().astype(float)
C="""credit_utilization_capped debt_ratio_capped num_late_30_59 num_late_60_89 num_late_90_plus
total_late_payments has_delinquency has_serious_delinquency age monthly_income log_monthly_income
num_credit_lines num_real_estate_loans log_num_credit_lines num_dependents income_per_dependent credit_lines_per_person
flag_high_utilization flag_very_high_utilization flag_high_debt_ratio flag_very_high_debt_ratio
flag_recent_late_payments flag_serious_delinquency flag_multiple_delinquencies flag_low_income
flag_many_dependents flag_few_credit_lines total_risk_flags credit_util_category debt_category age_category
financial_health age_income_interaction utilization_debt_interaction MonthlyIncome_missing Dependents_missing""".split()
assert len(C)==36
Z={c:d[c].to_numpy().astype(float) for c in C}
sf=lambda s: math.erfc(math.sqrt(max(s,0)/2))
def fit(cols):
    X=np.column_stack([np.ones(len(y))]+[Z[c] for c in cols]); b=np.zeros(X.shape[1])
    for _ in range(200):
        p=1/(1+np.exp(-X@b)); W=p*(1-p); H=X.T@(X*W[:,None]); s=np.linalg.solve(H,X.T@(y-p)); b+=s
        if np.max(np.abs(s))<1e-10: break
    p=1/(1+np.exp(-X@b)); W=p*(1-p); H=X.T@(X*W[:,None])
    return X,b,p,W,np.linalg.inv(H)
model=[]; last_removed=None; step=0; path=[]; minrel_ok=1; maxrel_alias=0
TH=1e-8
while True:
    X,b,p,W,Hinv=fit(model)
    # removal
    if model:
        wald=[(b[i+1]**2/Hinv[i+1,i+1],c) for i,c in enumerate(model)]
        w,c=min(wald)
        if sf(w)>0.05:
            model.remove(c); step+=1; path.append((step,'',c,round(w,4),sf(w))); last_removed=c; continue
    XW=X*W[:,None]; A=X.T@XW
    best=None; info=[]
    for c in C:
        if c in model: continue
        z=Z[c]; v=X.T@(z*W); V=z@(z*W)-v@np.linalg.solve(A,v); rel=V/(z@(z*W))
        if rel<TH:
            maxrel_alias=max(maxrel_alias,rel); info.append(c); continue
        minrel_ok=min(minrel_ok,rel)
        U=z@(y-p); s=U*U/V
        if best is None or s>best[0]: best=(s,c)
    if best is None or sf(best[0])>=0.05 or best[1]==last_removed:
        print('stop after step',step,'best',best, sf(best[0]) if best else None,'aliased now',info); break
    model.append(best[1]); step+=1; path.append((step,best[1],'',round(best[0],4),sf(best[0]))); last_removed=None
    if step>60: break
print('min rel residual among non-aliased',minrel_ok,'max rel among aliased',maxrel_alias)
ref=pl.read_csv('reference/stepwise_summary.csv',infer_schema=False)
ok=True
for (st,e,r,chi,pv),row in zip(path,ref.iter_rows(named=True)):
    m=(e[:20]==(row['EffectEntered'] or '')) and (r[:20]==(row['EffectRemoved'] or ''))
    refchi=row['ScoreChiSq'] if e else row['WaldChiSq']
    print(st,e[:20],r[:20],chi,refchi,'OK' if m else 'DIVERGE'); ok&=m
print('len',len(path),ref.height,'all match',ok and len(path)==ref.height)
# residual chi-square DF at end
X,b,p,W,Hinv=fit(model); out=[c for c in C if c not in model]
Zo=np.column_stack([Z[c] for c in out]); A=X.T@(X*W[:,None])
R=Zo-X@np.linalg.solve(A,X.T@(Zo*W[:,None]))
M=R.T@(R*W[:,None]); ev=np.linalg.eigvalsh(M/np.outer(np.sqrt(np.diag(M)),np.sqrt(np.diag(M))))
print('outside',len(out),'rank',np.sum(ev>1e-9),'smallest eig',ev[:5])
U=Zo.T@(y-p); print('residual chi2', U@np.linalg.lstsq(M,U,rcond=1e-10)[0])
sc=np.sqrt((Zo*Zo*W[:,None]).sum(0)); Rn=R/sc; Mn=Rn.T@(Rn*W[:,None]); Un=U/sc
ev,Q=np.linalg.eigh(Mn); print('normalized eig',ev[:5])
keep=ev>1e-8; print('rank',keep.sum())
print('residual chi2 (pinv)', Un@(Q[:,keep]@np.diag(1/ev[keep])@Q[:,keep].T)@Un)
for k in range(3):
    v=Q[:,k]; print('null vec',[ (out[i],round(v[i],3)) for i in np.argsort(-abs(v))[:6] if abs(v[i])>1e-3])
