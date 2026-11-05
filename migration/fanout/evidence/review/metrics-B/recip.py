import polars as pl, csv
from decimal import Decimal, ROUND_HALF_UP
print(pl.__version__)
J='/Users/cristophersalvi/GitHub/sas-migration/judge/'
def pct(x):
    for dd in (2,1,0):
        s=str(Decimal(repr(x*100)).quantize(Decimal(1).scaleb(-dd),ROUND_HALF_UP))+'%'
        if len(s)<=6: return s
def fx(x,d): return str(Decimal(repr(x)).quantize(Decimal(1).scaleb(-d),ROUND_HALF_UP))
bad=0; mind=1
for r in ['reference','reference/scenarios/edge_metrics_a','reference/scenarios/edge_metrics_b','reference/scenarios/edge_metrics_c']:
    t=pl.read_csv(J+r+'/printed_cumulative_lift.csv',infer_schema=False)
    df=pl.DataFrame({'cd':t['cum_defaults'].cast(pl.Float64),'cc':t['cum_count'].cast(pl.Float64)})
    T=float(df['cd'][-1]); N=float(df['cc'][-1]); rate=float(f'{T/N:.6f}')
    for k in (1,3):
        g=df.with_columns(cap=pl.col('cd')/T, lift=(pl.col('cd')/pl.col('cc'))/rate, recip=pl.col('cd')*(1/T))
        if k==3: g=pl.concat([df[:3],df[3:]]).with_columns(cap=pl.col('cd')/T, lift=(pl.col('cd')/pl.col('cc'))/rate, recip=pl.col('cd')*(1/T))
        for i in range(10):
            a=pct(g['cap'][i]); b=t['cum_capture_rate'][i]; c=pct(g['recip'][i]); l=fx(g['lift'][i],2)
            exact=float(df['cd'][i])/T
            if a!=b or c!=b or l!=t['cum_lift'][i]: bad+=1; print('BAD',r,i,a,b,c,l)
            if g['cap'][i]!=exact: print('ulp diff',r,i,g['cap'][i],exact)
            fr=abs((exact*10000)%1-0.5); mind=min(mind,fr)
print('bad',bad,'min dist to half (in 0.01% units)',mind)
