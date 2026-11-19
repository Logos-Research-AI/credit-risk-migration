"""NO LEAN EVALUATION (eval_decl cannot print a Pl.Frame and the blueprint has no carrier item; see fz5_hl_model.py).
Python transcription of the stored Lean of def:train_run_06_coefficients_odds (statement_lean read 2026-11-18), compared with the REAL
train.py lines on the seeds of fz5_s06_gen (kept = precondition true). Also: precondition vs Python raising, and x**2 vs x*x.
  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz5_s06_model.py [N]"""
import json, math, sys
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fz5_s06_gen as g
from fz5_s06_gen import enc, fb, cmp, sc

def strcol(xs):  # Lean: empty -> Pl.Col.null 0, else Pl.Col.str
    return [6, 0] if not xs else [4, len(xs)] + [t for x in xs for t in [1] + g.tS(x)]

def model(c):
    fin = c["hasfit"]
    mv = [] if not fin else ["Intercept"]
    me = [] if not fin else ["e" + enc(c["icpt"])]
    df, sd, wd, pr, oe, oest, olo, oup = [], [], [], [], [], [], [], []
    p2args = []
    for idx, name in [(0, "Intercept")] + list(zip(c["fidx"], c["effects"])):
        if not fin:
            continue
        if idx in c["lo"]:
            if idx != 0:
                mv.append(name[:20]); me.append("e" + enc(0.0))
            df.append("0"); sd.append(""); wd.append(""); pr.append("")
            continue
        b = c["betaL"][idx]
        cv = c["rows"][idx][idx]
        se = math.sqrt(cv) if cv == cv else float("nan")   # Lean sqrt of NaN
        w = (b / se) ** 2 if se != 0 else None
        p2args.append(b / se)
        wb = (b / se) ** 2
        df.append("1")
        if idx != 0:
            mv.append(name[:20]); me.append("e" + enc(b)); oe.append(name[:20])
            oest.append("o" + enc(math.exp(b)) + "/8/3")
            olo.append("o" + enc(math.exp(b - sc.Z975 * se)) + "/8/3")
            oup.append("o" + enc(math.exp(b + sc.Z975 * se)) + "/8/3")
        sd.append("e" + enc(se)); wd.append("w" + enc(wb) + "/10/4"); pr.append("p" + enc(wb / (1 + 3.0)))
    names = ["Variable", "DF", "Estimate", "StdErr", "WaldChiSq", "ProbChiSq", "_ESTTYPE_"]
    cols = [mv, df, me, sd, wd, pr, ["MLE"] * len(mv)]
    t = [len(names)]
    for n, col in zip(names, cols):
        t += g.tS(n) + strcol(col)
    files = []
    if c["effects"]:
        files.append(("printed_odds_ratios.csv", [oe, oest, olo, oup]))
    t += [len(files)]
    for nm, cols4 in files:
        t += g.tS(nm)
        nrows = len(cols4[0])
        t += [nrows]
        for r in range(nrows):
            t += [4]
            for n, col in zip(["Effect", "OddsRatioEst", "LowerCL", "UpperCL"], cols4):
                t += g.tS(n) + [2, 1] + g.tS(col[r])
    return t, p2args

def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    diffs, cnt, p2diff = [], Counter(), []
    for s in range(N):
        c = g.case(s)
        res, err = g.py_run(c)
        p = g.pre(c)
        if p and err: cnt["PRE_TRUE_PY_RAISES"] += 1; diffs.append((s, "pre true, python raises " + err)); continue
        if not p and res is not None: cnt["narrowing"] += 1
        if not p: cnt["excluded"] += 1; continue
        cnt["kept"] += 1
        mt, args = model(c)
        pt = g.toks(res)
        if mt != pt: diffs.append((s, "tokens differ")); 
        for a in args:
            if math.isfinite(a) and (a ** 2 if abs(a) < 1e154 else a * a) != a * a: p2diff.append((s, a))
    print(dict(cnt)); print("diffs", len(diffs), diffs[:10]); print("x**2 != x*x:", len(p2diff), p2diff[:5])
main()
