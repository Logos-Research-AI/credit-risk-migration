# RETIRED 2026-11-16: this script is a record of the port before the update of 2026-11-16 and no longer
# runs as a script (its helper functions are still imported by later generators): it calls sas_compat.proc_rank_apply_groups.
# Its recorded outputs describe the port as it was then.
import sys as _sys

if __name__ == "__main__":  # retired as a script; its helpers may still be imported
    _sys.exit("RETIRED 2026-11-16: " + __file__ + " calls keywords the port no longer has; see the note at its top")

"""INV01: unit-level edge cases behind migration/inventory.tsv (labels U01..U44). Run: uv run python migration/experiments/inv01_unit_edges.py"""
import math, warnings, numpy as np, polars as pl, sys
from pathlib import Path
from credit_risk import sas_compat as sc
S=Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__import__("tempfile").mkdtemp())
def show(t,v): print(f"[{t}]", v)
df=pl.DataFrame({"age":[25.0,None,float('nan'),45.0]})
r=df.with_columns(g=pl.when(pl.col("age")<30).then(1).when(pl.col("age")<40).then(2).otherwise(5))
show("U01 then(1) dtype / null age / NaN age", (r.schema, r["g"].to_list()))
show("U02 pl.lit(105000), lit(100.0)-15, lit(1)-Int64flag", pl.select(a=pl.lit(105000), b=pl.lit(100.0)-15).schema)
f=pl.DataFrame({"x":[1.0,None,2.0,float('nan')]})
show("U03 is_in null/NaN value, set w/o null", f.with_columns(s=pl.col("x").is_in(pl.Series([1.0,3.0]).implode()))["s"].to_list())
show("U03b is_in set with null", f.with_columns(s=pl.col("x").is_in(pl.Series([1.0,None]).implode()))["s"].to_list())
show("U03c filter sel / ~sel heights", (f.with_columns(s=pl.col("x").is_in(pl.Series([1.0]).implode())).filter(pl.col("s")).height, f.with_columns(s=pl.col("x").is_in(pl.Series([1.0]).implode())).filter(~pl.col("s")).height))
g=pl.DataFrame({"u":[None,float('nan'),250.0,-0.0,float('inf')]})
show("U04 sas_min(u,200) / sas_max(0.0,u)", g.select(a=sc.sas_min(pl.col("u"),pl.lit(200.0)), b=sc.sas_max(pl.lit(0.0),pl.col("u"))).to_dict(as_series=False))
h=pl.DataFrame({"p":[None,0.05,0.3,float('nan')]})
show("U05 lt(p,.1) ge(p,.5) gt(p,0) le(p,.1) eq(p,null)", h.select(lt=sc.lt(pl.col("p"),0.1),ge=sc.ge(pl.col("p"),0.5),gt=sc.gt(pl.col("p"),0),le=sc.le(pl.col("p"),0.1),eq=sc.eq(pl.col("p"),pl.lit(None,pl.Float64))).to_dict(as_series=False))
show("U05b flag(p>=.1), plain p>=.1", h.select(f=sc.flag(pl.col("p")>=0.1), c=pl.col("p")>=0.1, lg=sc.sas_log(pl.col("p")-0.05)).to_dict(as_series=False))
d=pl.DataFrame({"a":[1.0,0.0,None,-1.0,1e308,3.0],"b":[0.0,0.0,2.0,0.0,1e-308,None]})
show("U06 div a/b, plain a/b", d.select(q=sc.div(pl.col("a"),pl.col("b")), p=pl.col("a")/pl.col("b")).to_dict(as_series=False))
show("U06b div(col, lit None) / div(col, lit 0.0) / div(int col, 0 height)", d.select(q=sc.div(pl.col("a"),pl.lit(None,pl.Float64)), z=sc.div(pl.col("a"),pl.lit(0.0,pl.Float64))).to_dict(as_series=False))
try: show("U06c div on empty frame", d.head(0).select(q=sc.div(pl.col("a"), 0)).shape)
except Exception as e: show("U06c", repr(e))
try: show("U06d div(100*COUNT, COUNT.sum()) on empty", pl.DataFrame({"COUNT":pl.Series([],dtype=pl.Int64)}).with_columns(P=sc.div(100*pl.col("COUNT"),pl.col("COUNT").sum())).shape)
except Exception as e: show("U06d", repr(e))
e=pl.DataFrame({"x":[1000.0,-1000.0,None,float('nan'),709.0,710.0]})
show("U07 sas_exp / 1/(1+sas_exp(-x)) / 1/(1+(-x).exp())", e.select(a=sc.sas_exp(pl.col("x")), b=1/(1+sc.sas_exp(-pl.col("x"))), c=1/(1+(-pl.col("x")).exp())).to_dict(as_series=False))
rr=pl.DataFrame({"x":[-0.3,0.5,1.5,2.5,-2.5,None,float('nan'),float('inf'),0.49999999999999994,4503599627370496.5]})
show("U08 sas_round", [repr(v) for v in rr.select(sc.sas_round(pl.col("x")))["x"].to_list()])
ss=pl.DataFrame({"a":[None,1.0,None],"b":[None,None,2.0],"c":[None,3.0,None]})
show("U09 sas_sum all-null / partial", ss.select(s=sc.sas_sum(pl.col("a"),pl.col("b"),pl.col("c")))["s"].to_list())
x=pl.Series("x",[0.3,None,0.1,0.3,float('nan'),0.2])
show("U10 proc_rank_groups(k=3) asc/desc with null+NaN+tie", (sc.proc_rank_groups(x,3).to_list(), sc.proc_rank_groups(x,3,descending=True).to_list(), sc.proc_rank_groups(x,3).dtype))
show("U10b all-null / empty", (sc.proc_rank_groups(pl.Series("x",[None,None],dtype=pl.Float64),10).to_list(), sc.proc_rank_groups(pl.Series("x",[],dtype=pl.Float64),10).to_list()))
ref=pl.Series("r",[0.1,0.2,0.3,0.4,None,0.5,0.6])
show("U11 apply_groups", sc.proc_rank_apply_groups(ref, pl.Series("x",[0.05,0.25,None,float('nan'),0.9,0.3]),3).to_list())
for nm,rf in (("all-null ref",pl.Series("r",[None],dtype=pl.Float64)),("NaN in ref",pl.Series("r",[0.1,float('nan'),0.3]))):
    try: show("U11b "+nm, sc.proc_rank_apply_groups(rf, pl.Series("x",[0.05,0.2,float('nan'),None,5.0]),3).to_list())
    except Exception as ex: show("U11b "+nm, repr(ex))
rng=np.random.default_rng(0); v=np.concatenate([rng.standard_normal(200000)*10.0**rng.integers(-150,150,200000), rng.random(100000)])
show("U12 x**2 == x*x for all (python float)", all(float(t)**2==float(t)*float(t) for t in v))
ok=True
for n in list(range(1,300))+[1000,4097,70000]:
    a=rng.random(n); ok &= (a.mean()==a.sum()/n)
show("U13 ndarray.mean()==sum()/n bitwise", ok)
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always"); show("U13b empty mean", (np.asarray([],dtype=np.float64).mean(), [str(i.message) for i in w]))
for nm,fn in (("solve singular",lambda: np.linalg.solve(np.zeros((2,2)),np.ones(2))),("inv singular",lambda: np.linalg.inv(np.zeros((2,2)))),("math.exp(710)",lambda: math.exp(710.0)),("math.log(0)",lambda: math.log(0)),("math.sqrt(-1)",lambda: math.sqrt(-1.0)),("math.sqrt(nan)",lambda: math.sqrt(float('nan'))),("math.floor(nan)",lambda: math.floor(float('nan'))),("int(nan)",lambda:int(np.float64('nan'))),("int(2.7)",lambda:int(np.float64(2.7))),("1.0/0.0 py",lambda: 1.0/0.0),("(1.0/0)",lambda: 1.0/0),("np.float64(1)/0",lambda: np.float64(1.0)/0),("math.floor(inf)",lambda: math.floor(float('inf'))),("math.exp(-800)",lambda: math.exp(-800.0))):
    try: show("U14 "+nm, fn())
    except Exception as ex: show("U14 "+nm, repr(ex))
# merge
m=sc.merge_one_to_one(pl.DataFrame({"A":[1.0],"X":["a"]}), pl.DataFrame({"K":[0.5,0.5,0.5],"A":[9.0,8.0,7.0]}), pl.DataFrame({"X":["z"]}))
show("U15 merge_one_to_one", (m.to_dict(as_series=False), m.schema))
show("U15b merge with 0-col frame / none", (sc.merge_one_to_one(pl.DataFrame(), pl.DataFrame({"a":[1]})).shape, sc.merge_one_to_one().shape))
# pairs
y=pl.Series([1.0,0.0,1.0,0.0,None,2.0,1.0,0.0]); s=pl.Series([0.9,0.1,float('nan'),0.5,0.3,0.4,0.5+5e-9,None])
show("U16 _pairs with NaN score, y=2, tie fuzz", sc._pairs(y,s))
show("U16b roc degenerate (one class)", sc.roc_association(pl.Series([1.0,1.0]),pl.Series([0.2,0.3])))
show("U16c roc label frame schema", sc.roc_association(pl.Series([1.0,1.0]),pl.Series([0.2,0.3]),"L").schema)
show("U16d roc NaN y", sc.roc_association(pl.Series([1.0,float('nan'),0.0]),pl.Series([0.2,0.3,0.1])))
# hl
show("U17 hl empty", sc.hosmer_lemeshow(pl.Series([],dtype=pl.Float64),pl.Series([],dtype=pl.Float64))[1:])
for nm,(yy,pp) in {"NaN p":([1.0,0.0,1.0],[0.2,float('nan'),0.3]),"NaN y":([1.0,float('nan'),0.0],[0.2,0.3,0.4]),"p=0":([0.0,1.0,0.0],[0.0,0.5,0.6]),"y=0.5":([0.5,1.0],[0.2,0.4]),"inf p":([0.0,1.0],[float('inf'),0.3])}.items():
    try:
        t=sc.hosmer_lemeshow(pl.Series(yy),pl.Series(pp)); show("U17 "+nm, (t[0].to_dict(as_series=False),t[1:]))
    except Exception as ex: show("U17 "+nm, repr(ex))
show("U17b _hl_groups", (sc._hl_groups([1]*25,25,10), sc._hl_groups([3,3,3,1],10,10), sc._hl_groups([5],5,10)))
try: sc._hl_groups([1],1,0)
except Exception as ex: show("U17c g=0", repr(ex))
# classification_table
X=np.column_stack([np.ones(6),np.array([0.,1,2,3,4,5])]); Y=np.array([0.,0,1,0,1,1])
for nm,pdv in {"ok":np.array([.1,.2,.4,.5,.7,.9]),"p=0":np.array([0.,.2,.4,.5,.7,.9]),"p=1":np.array([.1,.2,.4,.5,.7,1.0]),"nan":np.array([.1,np.nan,.4,.5,.7,.9])}.items():
    try:
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always"); t=sc.classification_table(Y,X,pd=pdv); show("U18 "+nm,(t.shape,t.schema.dtypes()[:3],t.row(0),[str(i.message) for i in w]))
    except Exception as ex: show("U18 "+nm, repr(ex))
try: sc.classification_table(Y,X)
except Exception as ex: show("U18 none", repr(ex))
try: show("U18 swapped (X,y,pd)", sc.classification_table(X,Y,np.array([.1,.2,.4,.5,.7,.9])).shape)
except Exception as ex: show("U18 swapped", repr(ex))
try: sc.classification_table(Y[:0],X[:0],pd=Y[:0])
except Exception as ex: show("U18 empty", repr(ex))
# cum_sum nulls, group null key, sort
c=pl.DataFrame({"k":[2.0,None,1.0,None,2.0],"v":[1.0,None,2.0,3.0,None]})
show("U19 cum_sum with nulls", c.select(pl.col("v").cum_sum())["v"].to_list())
gg=c.group_by("k",maintain_order=True).agg(n=pl.len().cast(pl.Int64), s=sc.sql_sum(pl.col("v")), m=sc.sql_mean(pl.col("v")), raw=pl.col("v").sum())
show("U19b group null key + sql_sum all-null group", gg.to_dict(as_series=False)); show("U19c sort nulls first", gg.sort("k",maintain_order=True)["k"].to_list())
show("U19d select-ctx sql_sum on empty / all-null", (c.head(0).select(sc.sql_sum(pl.col("v"))).to_dict(as_series=False), c.select(sc.sql_sum(pl.col("v").filter(pl.col("v")>99))).to_dict(as_series=False), c.select(a=pl.col("v").filter(pl.col("v")>99).sum()).to_dict(as_series=False)))
show("U20 polars NaN>0, NaN>=0.5, NaN==NaN", pl.DataFrame({"x":[float('nan')]}).select(a=pl.col("x")>0,b=pl.col("x")>=0.5,c=pl.col("x")==pl.col("x")).row(0))
a=pl.DataFrame({"score_bin":pl.Series([0,None,1],dtype=pl.Int64),"t":[.5,.2,.3]}); b=pl.DataFrame({"score_bin":pl.Series([None,0,0],dtype=pl.Int64),"v":[.4,.3,.3]})
j=a.join(b,on="score_bin",how="left",maintain_order="left",nulls_equal=True); show("U21 join nulls_equal + dup right keys", (j.to_dict(as_series=False), j.n_chunks()))
show("U21b inner", a.join(b,on="score_bin",how="inner",maintain_order="left",nulls_equal=True).to_dict(as_series=False))
try: show("U21c join Int32 key vs Float64 key", pl.DataFrame({"k":pl.Series([1,2],dtype=pl.Int32)}).join(pl.DataFrame({"k":[1.0],"m":[5.0]}),on="k",how="left").to_dict(as_series=False))
except Exception as ex: show("U21c", repr(ex)[:200])
try: show("U21d join Int32 key vs Int64 key", pl.DataFrame({"k":pl.Series([1,2],dtype=pl.Int32)}).join(pl.DataFrame({"k":[1],"m":[5.0]}),on="k",how="left").to_dict(as_series=False))
except Exception as ex: show("U21d", repr(ex)[:200])
show("U22 _named names", (sc._e(100).meta.output_name(raise_if_undetermined=False), sc.sas_max(pl.lit(0.0),pl.col("z")).meta.output_name(), sc.div(pl.col("a")*pl.col("b"),100).meta.output_name(), sc._is_scalar(pl.col("a").sum()), sc._is_scalar(pl.lit(1.0)), sc._is_scalar(pl.col("a")), sc._is_scalar(pl.len())))
show("U23 median even/NaN", pl.DataFrame({"g":[1,1,1,1],"v":[1.0,2.0,4.0,float('nan')]}).group_by("g",maintain_order=True).agg(pl.col("v").median()).to_dict(as_series=False))
show("U24 int/int polars + guards on zero counts", pl.DataFrame({"TP":[0],"FP":[0],"FN":[3],"TN":[4]}).with_columns(p=pl.when((pl.col("TP")+pl.col("FP"))>0).then(pl.col("TP")/(pl.col("TP")+pl.col("FP"))).otherwise(None), r=pl.col("TP")/(pl.col("TP")+pl.col("FN")), z=pl.col("TP")/(pl.col("TP")+pl.col("FP"))).to_dict(as_series=False))
show("U25 n*(n-1)/2 int true-div, 100.0*a/p", (10*(9)/2, type(7/2), 100.0*3/7))
show("U26 max_horizontal(col, eps).log()", pl.DataFrame({"v":[0.0,None,0.5]}).select(pl.max_horizontal(pl.col("v"),1e-4).log()).to_series().to_list())
show("U27 filter by Series mask", pl.DataFrame({"a":[1,2,3]}).filter(pl.Series([True,False,True]))["a"].to_list())
try: pl.DataFrame({"a":[1,2,3]}).filter(pl.Series([True,False]))
except Exception as ex: show("U27b", repr(ex)[:120])
show("U28 all_horizontal is_not_null with NaN", pl.DataFrame({"a":[1.0,None,float('nan')],"b":[1.0,1.0,1.0]}).select(pl.all_horizontal(pl.col("a","b").is_not_null())).to_series().to_list())
show("U29 concat schema mismatch?", pl.concat([pl.DataFrame({"a":[1.0]}),pl.DataFrame({"a":[None]}).cast(pl.Float64)],how="vertical").to_dict(as_series=False))
show("U30 item on select agg of empty frame", pl.DataFrame({"a":pl.Series([],dtype=pl.Float64)}).select(g=sc.sql_sum(sc.flag(pl.col("a")==0))).item(0,"g"))
show("U31 _into_float", [__import__("credit_risk.metrics_calculation",fromlist=["x"])._into_float(v) for v in (None, 0, 2811, 0.066712345678, 123456789, float('nan'))])
k=pl.DataFrame({"default_flag":[0.0,None,1.0,None,0.0],"pd_logistic":[0.1,0.2,0.3,0.4,None]})
show("U32 cum_good/cum_bad with null default_flag; totals", (k.with_columns(cg=sc.flag(pl.col("default_flag")==0).cum_sum(), cb=(1-sc.flag(pl.col("default_flag")==0)).cum_sum()).select("cg","cb").to_dict(as_series=False), k.select(good=sc.sql_sum(sc.flag(pl.col("default_flag")==0)), bad=sc.sql_sum(sc.flag(pl.col("default_flag")==1))).row(0), k.select(good=sc.sql_sum(sc.flag(pl.col("default_flag")==0))).schema))
from credit_risk import metrics_calculation as mcm
cf,cm,mt=mcm.confusion_metrics(0.25,"x",k)
show("U33 confusion_metrics with null default_flag/pd", (cm.to_dict(as_series=False), mt.to_dict(as_series=False), mt.schema.dtypes()))
show("U33b confusion_metrics on empty frame", mcm.confusion_metrics(0.25,"x",k.head(0))[2].to_dict(as_series=False))
show("U34 select-ctx sum/mean vs default_flag nulls", k.select(s=sc.sql_sum(pl.col("default_flag")), m=sc.sql_mean(pl.col("default_flag"))).row(0))
show("U35 100*Int64 col dtype; 1-Int64; Int64+1; float col*100; 2*f-1", pl.DataFrame({"c":pl.Series([1,2],dtype=pl.Int64),"f":[0.5,None]}).select(a=100*pl.col("c"), b=1-pl.col("c"), c2=pl.col("c")+1, d=pl.col("f")*100, e=2*pl.col("f")-1, s=pl.col("c").sum(), cs=pl.col("c").cum_sum()).schema)
show("U36 sort two keys nulls first stable", pl.DataFrame({"d":[1.0,None,0.0,None],"p":[1,0,1,1],"i":[0,1,2,3]}).sort(["d","p"],maintain_order=True)["i"].to_list())
show("U37 sort pd: null first, NaN last, ties stable", pl.DataFrame({"p":[0.2,None,float('nan'),0.2,0.1],"i":[0,1,2,3,4]}).sort("p",maintain_order=True)["i"].to_list())
show("U38 ks eq(null max): all rows kept", pl.DataFrame({"ks":[None,None],"p":[.1,.2]},schema={"ks":pl.Float64,"p":pl.Float64}).filter(sc.eq(pl.col("ks"),pl.lit(None,pl.Float64))).height)
show("U39 py max ties / max(n0,1)", (max(0,1), max(3,1)))
show("U40 str(int) / name[:20] / float(int)", (str(686727936), "flag_multiple_delinquencies"[:20], float(686727936)))
import numpy as np
show("U41 np int arr * 0.5 / int; int(np.int64 sum)", (((np.array([1,2])+0.5*(np.array([3,4])-np.array([1,2])))/max(2,1)).tolist(), int(np.array([1,2]).sum())))
show("U42 Series.rank ties avg, desc", (pl.Series([0.3,0.1,0.3,None]).rank("average").to_list(), pl.Series([0.3,0.1,0.3,None]).rank("average",descending=True).to_list()))
show("U43 group_by without maintain_order then sort (unique keys)", pl.DataFrame({"g":[2,0,1,2,0],"v":[5.0,1.0,3.0,4.0,2.0]}).group_by("g").agg(lo=pl.col("v").min()).sort("g").to_dict(as_series=False))
show("U44 pl.col(*names).is_not_null() in all_horizontal", pl.DataFrame({"a":[1.0,None],"b":[None,2.0],"c":[1.0,1.0]}).select(pl.all_horizontal(pl.col(*["a","c"],"b").is_not_null())).to_series().to_list())
