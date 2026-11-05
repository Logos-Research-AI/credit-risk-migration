import polars as pl, numpy as np, math
J='/Users/cristophersalvi/GitHub/sas-migration/judge/'
def d8(x):
    if x==0: return '0'
    ax=abs(x); dec=max(4, 3-1-math.floor(math.log10(ax)))
    return f"{x:.{dec}f}"
for k,(d,r) in {'real':('reference','reference'),'a':('scenarios/edge_metrics_a','reference/scenarios/edge_metrics_a'),'b':('scenarios/edge_metrics_b','reference/scenarios/edge_metrics_b'),'c':('scenarios/edge_metrics_c','reference/scenarios/edge_metrics_c')}.items():
    v=pl.read_csv(J+d+'/risk_scores_validation.csv',infer_schema=False)
    y=v['default_flag'].cast(pl.Float64).to_numpy(); p=v['pd_logistic'].cast(pl.Float64).to_numpy()
    e=np.sort(p[y==1]); ne=np.sort(p[y==0]); n1=len(e); n0=len(ne)
    below=np.searchsorted(ne,e,'left'); le=np.searchsorted(ne,e,'right'); tie_e=le-below
    V10=(below+0.5*tie_e)/n0
    above=n1-np.searchsorted(e,ne,'right'); ge=n1-np.searchsorted(e,ne,'left'); tie_n=ge-above
    V01=(above+0.5*tie_n)/n1
    C=below.sum(); T=tie_e.sum(); P=n1*n0; D=P-C-T; N=n1+n0
    A=(C+T/2)/P
    se=math.sqrt(np.var(V10,ddof=1)/n1+np.var(V01,ddof=1)/n0)
    z=1.959963985
    vals=[A,se,A-z*se,A+z*se,(C-D)/P,(C-D)/(C+D),(C-D)/(N*(N-1)/2)]
    got=','.join(['Logistic Model']+[f"{x:.4f}" if i!=1 else d8(x) for i,x in enumerate(vals)])
    ref=open(J+r+'/printed_roc_metrics.csv').read().splitlines()[1]
    print(k,got==ref,got,ref,'T',T,'raw',['%.8f'%x for x in vals])
