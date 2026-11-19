import sys, json, collections
sys.path.insert(0, "diffeval/units")
import fz5_s10_gen as g
e = json.load(open("diffeval/work/fz5_s10.cexpect.json"))
print("kept", sum(x[2] for x in e), "of 2100")
C = collections.Counter(); raised = []
for s in range(2100):
    c = g.build(s)
    if c["icpt"] is None and c["fin"] and not c["coefs"]:
        raised.append(s); continue
    C["kept"] += 1
    C["mode%d" % c["mode"]] += 1
    C["final none"] += (not c["fin"])
    C["n=0"] += (c["n"] == 0); C["n=1"] += (c["n"] == 1); C["no column"] += (not c["cols"])
    C["icpt none & final some (coefs>0)"] += (c["icpt"] is None and c["fin"])
    if c["fin"]:
        res, df = g.run_py(c)
        pd_ = res.get_column("pd_logistic").to_list()
        C["rows scored"] += len(pd_); C["pd null"] += sum(v is None for v in pd_); C["pd==0.5"] += sum(v == 0.5 for v in pd_)
        C["pd==1.0"] += sum(v == 1.0 for v in pd_)
        C["pd just below .5 (0.49999999999999994)"] += sum(v == 0.49999999999999994 for v in pd_)
        C["pred=1"] += sum(res.get_column("pred_logistic").to_list().count(1) for _ in [0]) if res.schema["pred_logistic"] == g.pl.Int64 else 0
print(dict(C)); print("python-raised (not sent):", len(raised), raised[:8])
