import sys, textwrap
from pathlib import Path
import polars as pl
from credit_risk import metrics_calculation as mc, sas_compat as sc
import struct
bits=lambda x: None if x is None else struct.unpack("<Q",struct.pack("<d",float(x)))[0]
src=textwrap.dedent("".join(Path(mc.__file__).read_text().splitlines(keepends=True)[155:196]))
def run(flags,pds):
    ns=dict(vars(mc)); ns["logit_scored_valid"]=pl.DataFrame({"default_flag":pl.Series(flags,dtype=pl.Float64),"pd_logistic":pl.Series(pds,dtype=pl.Float64)})
    exec(src,ns); k=ns["ks_statistic"]
    return k, [bits(x) for x in k["KS_Statistic"].to_list()], [bits(x) for x in k["KS_Cutoff"].to_list()], ns["logit_scored_valid"]["pd_logistic"].to_list()
print(run([0,0],[0.0,-0.0]))
print(run([0,0],[-0.0,0.0]))
print(run([0,1,0,1],[0.0,-0.0,0.5,0.5]))
print(run([0,1],[float("nan"),0.5]))
print(run([0,0],[float("nan"),0.5]))
print(sc.sas_best(5,8), sc.sas_best(5.0,8), sc.sas_best(123456789,8), sc.sas_best(123456789.0,8), sc.sas_best(2**60+1,8), sc.sas_best(float(2**60+1),8))
