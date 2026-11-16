import sys
sys.argv=["x"]; sys.path.insert(0,"diffeval/units"); sys.path.insert(0,"diffeval")
import fz_train_05_13_gen as g
from credit_risk import sas_compat as sc
a=b=n0=0
for s in range(g.S05, g.S05+g.N05):
    if not g.equal_len(s): continue
    df=g.frame(s); r=sc.association_table(df["default_flag"], df["pd_logistic"])
    a+= r.c is not None; n0+= df.height==0
c=d=0
for s in range(g.S13, g.S13+g.N13):
    if not (g.equal_len(s) and g.equal_len(s+g.D)): continue
    c+=1
    r1=sc.roc_association(g.frame(s)["default_flag"], g.frame(s)["pd_logistic"]); r2=sc.roc_association(g.frame(s+g.D)["default_flag"], g.frame(s+g.D)["pd_logistic"])
    d+= (r1.area is not None) + (r2.area is not None)
print("05A: statistics present", a, "frames with no row", n0, "| 13: frames with an area", d, "of", 2*c)
