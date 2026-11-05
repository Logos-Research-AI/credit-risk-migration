import polars as pl
from decimal import Decimal, ROUND_HALF_UP
R='/Users/cristophersalvi/GitHub/sas-migration/'
def b12(x):
    if x==0: return '0'
    if abs(x)<1e-5: return None
    d=Decimal(f"{x:.15g}"); ilen=len(str(int(abs(x))))
    q=d.quantize(Decimal(1).scaleb(-max(0,11-ilen)),rounding=ROUND_HALF_UP)
    s=format(q,'f')
    if '.' in s: s=s.rstrip('0').rstrip('.')
    return s
raw=pl.read_csv(R+'data/cs-training.csv',infer_schema=False).select(pl.col('').cast(pl.Int64).alias('row_id'),pl.col('RevolvingUtilizationOfUnsecuredLines').cast(pl.Float64).alias('r'),pl.col('DebtRatio').cast(pl.Float64).alias('d'))
ref=pl.concat([pl.read_csv(R+f'judge/reference/model_features_{p}.csv',infer_schema=False).select(pl.col('row_id').cast(pl.Int64),'utilization_debt_interaction') for p in ['train','validation']])
j=ref.join(raw,on='row_id')
ie=rc=n=0
for rid,s,r,d in j.iter_rows():
    p=(r*100)*(d*100); a=p/100; b=p*(1/100)
    sa,sb=b12(a),b12(b)
    if sa is None: continue
    n+=1; ie+=sa!=s; rc+=sb!=s
print('cells',n,'IEEE+A18 mismatches',ie,'recip+A18 mismatches',rc)
