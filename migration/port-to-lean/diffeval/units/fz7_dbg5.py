"""usage: fz7_dbg5.py gen <seed> -> work/fz7_dbg5.<seed>.in.json (list of eval inputs) + .exp.json (canon) ;
         fz7_dbg5.py cmp <seed> -> compares work/fz7_dbg5.<seed>.out.txt (one line per input)"""
import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
args = sys.argv[1:]; sys.argv = [sys.argv[0]]
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import fz7_metrics_gen as g
import polars as pl, compare as cmp, leanterm as lt
W = HERE.parent / "work"
mode, s = args[0], int(args[1])
if mode == "gen":
    V = g.V_of(s)
    best = {}
    o = g.sc.sas_best
    def wb(x, w):
        r = o(x, w); best.setdefault(None if x is None else cmp.fbits(float(x)), r); return r
    g.sc.sas_best = wb
    ns = dict(vars(g.mc)); ns.update(logit_scored_valid=V, logit_scored_train=g.T_of(s), valid_exists=V.height > 0)
    g.ex(g.CA, ns); g.ex(g.CB, ns)
    g.sc.sas_best = o
    Vs = ns["logit_scored_valid"].select("default_flag", "pd_logistic")
    f2 = lambda d: d.with_columns(pl.col("decile").cast(pl.Float64)) if "decile" in d.columns else d
    sb = ", ".join(f"({'none' if k is None else f'some {k}'}, {lt.lean_str(v)})" for k, v in best.items())
    pf = ", ".join(f"({lt.lean_str(v)}, {cmp.fbits(float(v))})" for v in sorted({v for v in best.values() if v}))
    pre = (f"let SB : List (Option UInt64 × String) := [{sb}]; let PF : List (String × UInt64) := [{pf}]; "
           'let sb := fun (x : Option Float) (_ : Int) => (match SB.lookup (x.map Float.toBits) with | some s => s | none => "?"); '
           "let pf := fun (s : String) => Float.ofBits ((PF.lookup s).getD 1); ")
    Vl = lt.lean_frame(Vs)
    vex = "true" if V.height > 0 else "false"
    ins = [f"(let V := {Vl}; let r := metrics_run_04_deciles V; r.1)", f"(let V := {Vl}; let r := metrics_run_04_deciles V; r.2)",
           f"({pre}let V := {Vl}; let r := metrics_run_04_deciles V; metrics_run_05_cumulative_lift sb pf r.1 r.2 {vex})",
           f"({pre}metrics_run_05_cumulative_lift sb pf {lt.lean_frame(f2(ns['decile_data']))} {lt.lean_frame(f2(ns['decile_analysis']))} {vex})"]
    exp = [g.canon(ns["decile_data"]), g.canon(ns["decile_analysis"]), g.canon(ns["cumulative_lift"]), g.canon(ns["cumulative_lift"])]
    json.dump(ins, open(W / f"fz7_dbg5.{s}.in.json", "w")); json.dump(exp, open(W / f"fz7_dbg5.{s}.exp.json", "w"))
    print(sum(map(len, ins)))
    print(ns["cumulative_lift"])
else:
    exp = json.load(open(W / f"fz7_dbg5.{s}.exp.json"))
    outs = (W / f"fz7_dbg5.{s}.out.txt").read_text().splitlines()
    for i, (e, l) in enumerate(zip(exp, outs)):
        toks = json.loads(l)
        got = cmp.decode_tokens("frame", toks)
        d = cmp.diff(e, got)
        print(i, "EQUAL" if not d else d[:12])
