import polars as pl, re, sys
R="/Users/cristophersalvi/GitHub/sas-migration/"
files={"train(ref=edge copy)":R+"data/cs-training.csv","test(ref)":R+"data/cs-test.csv","test(edge_predict)":R+"judge/scenarios/edge_predict/cs-test.csv"}
num=re.compile(r'^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$')
for name,p in files.items():
    df=pl.read_csv(p,infer_schema=False)
    print("==",name,df.height)
    for c in df.columns:
        s=df[c]
        empty=s.is_null().sum()+(s=="").sum()
        na=(s=="NA").sum()
        nonnum=sum(1 for v in s.drop_nulls().to_list() if v!="" and not num.match(v))
        print(f"  {c[:40]:40s} empty={empty} NA={na} nonnum={nonnum}")
