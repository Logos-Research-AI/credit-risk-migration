import polars as pl, glob, sys
for f in sorted(glob.glob('/Users/cristophersalvi/GitHub/sas-migration/judge/reference/**/*.csv', recursive=True)+glob.glob('/Users/cristophersalvi/GitHub/sas-migration/judge/scenarios/**/*.csv', recursive=True)):
    if 'cs-t' in f: continue
    raw = open(f).read()
    df = pl.read_csv(f, infer_schema=False)
    em = {c: df[c].is_null().sum() for c in df.columns if df[c].is_null().sum()}
    q = '"' in raw
    print(f.split('judge/')[1], df.height, 'empties', em, 'QUOTES' if q else '')
