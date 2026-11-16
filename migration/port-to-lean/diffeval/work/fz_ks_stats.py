import sys
sys.argv=["x"]; sys.path.insert(0,"diffeval/units"); sys.path.insert(0,"diffeval")
import fz_metrics_run_02_ks_gen as g
import math
st=dict(nonnull=0, zeros_both=0, nanpd=0, nullpd=0, ties=0, allnull_keep_zero=0)
for s in range(g.BASE, g.BASE+2500):
    df=g.frame(s)
    if df.height==0: continue
    _,ks=g.python(df)
    pd=df["pd_logistic"].to_list()
    nn=[x for x in pd if x is not None]
    zb=any(x==0 and math.copysign(1,x)<0 for x in nn) and any(x==0 and math.copysign(1,x)>0 for x in nn)
    st["nonnull"]+= ks["KS_Statistic"][0] is not None
    st["zeros_both"]+=zb
    st["allnull_keep_zero"]+= zb and ks["KS_Statistic"][0] is None
    st["nanpd"]+=any(x!=x for x in nn); st["nullpd"]+=len(nn)<len(pd); st["ties"]+=len(set(map(repr,pd)))<len(pd)
print(st)
