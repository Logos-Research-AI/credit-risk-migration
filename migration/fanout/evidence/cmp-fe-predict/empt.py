import polars as pl
J="/Users/cristophersalvi/GitHub/sas-migration/judge/reference/"
for f in ["model_features_train.csv","model_features_validation.csv","test_predictions.csv","scenarios/edge_predict/test_predictions.csv","scenarios/edge_predict/model_features_train.csv","final_model_output.csv","scenarios/edge_predict/final_model_output.csv"]:
    df=pl.read_csv(J+f,infer_schema=False)
    e={c:df[c].is_null().sum() for c in df.columns if df[c].is_null().sum()>0}
    print(f,df.height,e)
