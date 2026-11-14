import polars as pl
for d in ['reference', 'reference/scenarios/edge_predict']:
    for s in ['train', 'validation']:
        df = pl.read_csv(f'/Users/cristophersalvi/GitHub/sas-migration/judge/{d}/model_features_{s}.csv', infer_schema=False)
        bad = {c: (df[c].is_not_null() & df[c].cast(pl.Float64, strict=False).is_null()).sum() for c in df.columns}
        bad = {k: v for k, v in bad.items() if v}
        print(d, s, df.shape, 'non-numeric', bad, 'empties', sum(df[c].is_null().sum() for c in df.columns),
              'default_flag values', sorted(df['default_flag'].unique().to_list()))
