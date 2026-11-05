import polars as pl, numpy as np
print(pl.__version__)
R='/Users/cristophersalvi/GitHub/sas-migration/'
d=pl.read_csv(R+'data/cs-test.csv',infer_schema=False)
cu=d['RevolvingUtilizationOfUnsecuredLines'].cast(pl.Float64)*100
dr=d['DebtRatio'].cast(pl.Float64)*100
p=(cu*dr)
a=(p/100).to_numpy(); b=np.divide(p.to_numpy(),100.0)
print('col/100 vs np.divide mismatches', (a!=b).sum())
df=pl.DataFrame({'cu':cu,'dr':dr}).with_columns(u=pl.col('cu')*pl.col('dr')/100)
print('expr mismatches', (df['u'].to_numpy()!=b).sum())
print('x*0.01 mismatches',(p.to_numpy()*0.01!=b).sum())
