import polars as pl, numpy as np, compare as C, struct, json
raw = pl.read_csv("../data/cs-training.csv", infer_schema=False).rename({"": "row_id"})
ref = pl.concat([pl.read_csv(f"reference/model_features_{s}.csv", infer_schema=False) for s in ("train","validation")])
d = ref.select("row_id","utilization_debt_interaction").join(raw.select("row_id","RevolvingUtilizationOfUnsecuredLines","DebtRatio"), on="row_id")
rows=[]
for rid, refs, r, dd in d.iter_rows():
    u=float(r)*100; v=float(dd)*100
    a=(u*v)/100; b=(u*v)*0.01
    if "E" in refs: continue
    if C.sas_best12(a)!=refs or C.sas_best12(b)!=refs: rows.append((rid,r,dd,refs))
print(len(rows)); json.dump(rows[:40], open("/private/tmp/claude-501/-Users-cristophersalvi-GitHub-sas-migration/ecd11bde-e598-42bd-9cd4-9898388e98b1/scratchpad/udi_rows.json","w"))
