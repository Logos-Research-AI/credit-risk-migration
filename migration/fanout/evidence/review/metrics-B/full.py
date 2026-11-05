import polars as pl, numpy as np, math, csv
from decimal import Decimal, ROUND_HALF_UP
J='/Users/cristophersalvi/GitHub/sas-migration/judge/'
INP={'real':(J+'reference',J+'reference'),'a':(J+'scenarios/edge_metrics_a',J+'reference/scenarios/edge_metrics_a'),
     'b':(J+'scenarios/edge_metrics_b',J+'reference/scenarios/edge_metrics_b'),'c':(J+'scenarios/edge_metrics_c',J+'reference/scenarios/edge_metrics_c')}
def fx(x,d):
    if x is None: return ''
    return str(Decimal(repr(float(x))).quantize(Decimal(1).scaleb(-d), ROUND_HALF_UP))
def pct(x,w=8,d=2):
    if x is None: return ''
    for dd in range(d,-1,-1):
        s=str(Decimal(repr(x*100)).quantize(Decimal(1).scaleb(-dd),ROUND_HALF_UP))+'%'
        if len(s)<=w-2: return s
    return s
def best12(x):
    if x is None: return ''
    x=float(x)
    if x==0: return '0'
    if abs(x)<1e-5:
        # E-notation filling 12 chars
        for m in range(10,0,-1):
            s=f"{x:.{m}E}"
            mant,e=s.split('E'); e=int(e)
            mant=mant.rstrip('0').rstrip('.') 
            out=f"{mant}E{e}"
            if len(out)<=12: return out
    ilen=len(str(int(abs(x))))+(1 if x<0 else 0)
    s=f"{x:.{max(0,11-ilen)}f}"
    if '.' in s: s=s.rstrip('0').rstrip('.')
    return s
def rank_groups(x,k,desc=False):
    v=np.asarray(x,dtype=float)
    if desc: v=-v
    order=np.argsort(v,kind='stable'); n=len(v)
    sv=v[order]; ranks=np.empty(n)
    i=0
    while i<n:
        j=i
        while j+1<n and sv[j+1]==sv[i]: j+=1
        ranks[order[i:j+1]]=(i+1+j+1)/2
        i=j+1
    return np.floor(ranks*k/(n+1)).astype(int)
def cmp(name,got,ref):
    with open(ref) as f: rr=list(csv.reader(f))
    bad=0
    if got[0]!=rr[0]: print('  HEADER',name,got[0],rr[0]); bad+=1
    gs=sorted(map(tuple,got[1:])); rs=sorted(map(tuple,rr[1:]))
    if gs!=rs:
        for g,r in zip(got[1:],rr[1:]):
            if list(g)!=list(r): print('  DIFF',name,g,r); bad+=1
        if len(got)!=len(rr): print('  NROWS',len(got),len(rr)); bad+=1
    return bad
tot=0
for k,(ind,refd) in INP.items():
    va=pl.read_csv(ind+'/risk_scores_validation.csv',infer_schema=False).select(default_flag=pl.col('default_flag').cast(pl.Float64),pd=pl.col('pd_logistic').cast(pl.Float64))
    tr=pl.read_csv(ind+'/risk_scores_train.csv',infer_schema=False).select(pd=pl.col('pd_logistic').cast(pl.Float64))
    y=va['default_flag'].to_numpy(); p=va['pd'].to_numpy(); n=len(y)
    # threshold
    rows=[['threshold','accuracy','precision','recall','f1_score','specificity']]
    for t in (0.3,0.4,0.5,0.6,0.7):
        pr=(p>=t)
        TP=int(((y==1)&pr).sum()); TN=int(((y==0)&~pr).sum()); FP=int(((y==0)&pr).sum()); FN=int(((y==1)&~pr).sum())
        acc=(TP+TN)/(TP+TN+FP+FN) if TP+TN+FP+FN>0 else None
        prec=TP/(TP+FP) if TP+FP>0 else None
        rec=TP/(TP+FN) if TP+FN>0 else None
        f1=2*(prec*rec)/(prec+rec) if prec is not None and rec is not None and prec+rec>0 else None
        spec=TN/(TN+FP) if TN+FP>0 else None
        rows.append([best12(v) for v in (t,acc,prec,rec,f1,spec)])
    tot+=cmp(k+' threshold',rows,refd+'/threshold_analysis.csv')
    # decile
    dec=rank_groups(p,10,True)
    D=y.sum(); M=y.mean()
    tot_def=float(D); rate=tot_def/n; r8=float(f'{rate:.6f}')
    drows=[['decile','total_count','defaults','default_rate','avg_pd','min_pd','max_pd','capture_rate','lift']]
    crows=[drows[0]+['cum_defaults','cum_count','cum_capture_rate','cum_lift']]
    cd=cc=0
    for g in sorted(set(dec)):
        m=dec==g; tc=int(m.sum()); de=float(y[m].sum()); dr=de/tc
        cap=de/tot_def; lift=dr/(D/n)
        base=[str(g+1),str(tc),best12(de),pct(dr),fx(p[m].sum()/tc,4),fx(p[m].min(),4),fx(p[m].max(),4),pct(cap),fx(lift,2)]
        drows.append(base)
        cd+=de; cc+=tc
        crows.append(base+[best12(cd),best12(cc),pct(cd/tot_def),fx((cd/cc)/r8,2)])
    tot+=cmp(k+' decile',drows,refd+'/decile_analysis.csv')
    tot+=cmp(k+' cumlift',crows,refd+'/printed_cumulative_lift.csv')
    # calibration
    pb=rank_groups(p,20,False)
    cr=[['pred_bin','mean_predicted','mean_actual','bin_count']]
    for g in sorted(set(pb)):
        m=pb==g; c=int(m.sum())
        cr.append([str(g),fx(p[m].sum()/c,4),fx(y[m].sum()/c,4),str(c)])
    tot+=cmp(k+' calib',cr,refd+'/calibration_plot.csv')
    # psi
    tb=rank_groups(tr['pd'].to_numpy(),10); vb=rank_groups(p,10)
    nt=len(tb); nv=len(vb)
    pr=[['score_bin','train_pct','valid_pct','psi_component']]; S=0.0
    for g in sorted(set(tb)&set(vb)):
        a=(tb==g).sum()/nt; b=(vb==g).sum()/nv; comp=(a-b)*math.log(a/b); S+=comp
        pr.append([str(g),best12(a),best12(b),best12(comp)])
    tot+=cmp(k+' psi',pr,refd+'/printed_psi_calculation.csv')
    print(k,'done; PSI',fx(S,4),'rate',rate,'r8',r8, 'D',D)
print('total bad',tot)
