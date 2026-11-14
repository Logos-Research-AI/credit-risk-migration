import polars as pl, math
J='/Users/cristophersalvi/GitHub/sas-migration/judge/'
refs={'real':J+'reference','a':J+'reference/scenarios/edge_metrics_a','b':J+'reference/scenarios/edge_metrics_b','c':J+'reference/scenarios/edge_metrics_c'}
def best8(x):
    # BEST8.: fit into 8 chars
    for d in range(7,-1,-1):
        s=f"{x:.{d}f}"
        if len(s)<=8: return float(s), s
for k,d in refs.items():
    t=pl.read_csv(f'{d}/printed_cumulative_lift.csv',infer_schema_length=0)
    defs=t['defaults'].cast(pl.Int64); cnt=t['total_count'].cast(pl.Int64)
    tot=defs.sum(); n=cnt.sum(); rate=tot/n
    b8,s8=best8(rate)
    print(k,'total_defaults',tot,'n',n,'rate',repr(rate),'BEST8',s8)
    cd=defs.cum_sum(); cc=cnt.cum_sum()
    for i in range(t.height):
        r=cd[i]/cc[i]
        full=r/rate; b=r/b8
        f1=f"{full:.2f}"; f2=f"{b:.2f}"
        # distance to rounding boundary in units of 0.01
        frac=(full*100)%1
        flag='' if f1==f2 else ' <-- DIFFERS'
        print(f"  {t['decile'][i]} ref={t['cum_lift'][i]} full={full:.8f}->{f1} best8={b:.8f}->{f2} dist_to_half={abs(frac-0.5):.5f}{flag}")
    # cum_capture
    for i in range(t.height):
        cr=cd[i]/tot
        s=f"{cr*100:.2f}%"
        if s!=t['cum_capture_rate'][i] and not (t['cum_capture_rate'][i]=='100.0%' and s=='100.00%'): print('  capture diff',i,s,t['cum_capture_rate'][i])
