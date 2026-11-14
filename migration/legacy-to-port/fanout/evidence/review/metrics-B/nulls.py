import polars as pl, glob
J='/Users/cristophersalvi/GitHub/sas-migration/judge/'
files=sorted(glob.glob(J+'reference/risk_scores_*.csv')+glob.glob(J+'scenarios/*/risk_scores_*.csv')+glob.glob(J+'reference/scenarios/*/risk_scores_*.csv'))
for f in files:
    df=pl.read_csv(f,infer_schema=False)
    out=[]
    for c in ['default_flag','pd_logistic']:
        s=df[c]
        nempty=(s.is_null()|(s.str.strip_chars()=='')|(s=='.')).sum()
        vals=sorted(s.unique().to_list())[:5] if c=='default_flag' else None
        num=s.cast(pl.Float64,strict=False)
        out.append(f"{c}: empty={nempty} nonnum={num.is_null().sum()} {vals or ''} min={num.min()} max={num.max()}")
    y=df['default_flag'].cast(pl.Float64)
    print(f.replace(J,''), df.height, 'defaults',int(y.sum()), '|', ' ; '.join(out), 'cols',df.width)
