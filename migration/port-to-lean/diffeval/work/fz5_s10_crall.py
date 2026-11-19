"""Seeds where the Python step 10 changes if exp is correctly rounded (Decimal, 60 digits): do they equal the seeds where Lean differs?"""
import sys, types, math
from decimal import Decimal, getcontext
getcontext().prec = 60
sys.path.insert(0, "diffeval/units")
import polars as pl
import fz5_s10_gen as g
import fz5_s10_py as p
from credit_risk import sas_compat as sc
def cr(x):
    if x is None: return None
    if x != x or x in (float("inf"), float("-inf")): return math.exp(x) if x == x and x < 0 else (x if x == x else x)
    if x > 709.78271289338397: return float("inf")
    return float(Decimal(x).exp())      # correctly rounded to double (60 digits, ties negligible)
def sas_exp_cr(x):
    v = sc._e(x).cast(pl.Float64).map_elements(cr, return_dtype=pl.Float64)
    return sc._named(x, pl.when(v.is_finite()).then(v))
shim = types.SimpleNamespace(sas_exp=sas_exp_cr, flag=sc.flag, ge=sc.ge)
def step_cr(c):
    ns = dict(pl=pl, sas_compat=shim, intercept=c["icpt"], coefficients=dict(c["coefs"]), final=g.FIN if c["fin"] else None, model_features_validation=g.to_df(c))
    exec(p.SEG, ns); return ns["logit_scored_valid"]
diff = []
for s in range(0, 2100):
    c = g.build(s)
    if c["icpt"] is None and c["fin"] and not c["coefs"]: continue
    a, _ = g.run_py(c); b = step_cr(c)
    if not a.equals(b, null_equal=True):
        diff.append(s)
print("seeds where Python's exp (libm of this machine) differs from the correctly rounded exp in the output:", diff)
