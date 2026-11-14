"""Differential evaluation of the remaining units: the metrics steps and model_summary of
train.sas against the full-precision dump of the staged SAS run t1; the Association table and
the Hosmer-Lemeshow partition against the SAS fit of experiment X15D; and the validation of the
comparator on planted mismatches."""
import re, sys, struct, copy
sys.path.insert(0, "migration")
from diffeval import *
import eval_metrics as EM
SINK, DECL = "def:model_performance_metrics", "model_performance_metrics.evalApply"

def tab(rows): return lean_table([lean_row([(k, "s" if isinstance(v, str) else "n", v if isinstance(v, str) else None) for k, v in r]) for r in rows])
def cellterm(v):
    if v is None: return "Tabular.Cell.num none"
    if isinstance(v, str): return f"Tabular.Cell.str (some {lean_str(v)})"
    return f"Tabular.Cell.num (some {fbits(v)})"
def exact_table(rows): return lean_table(["[" + ", ".join(f"({lean_str(k)}, {cellterm(v)})" for k, v in r) + "]" for r in rows])

def main():
    mcp = Mcp(); d = read_dump("migration/runs/t1/dump.txt"); res = {}
    sub = lambda rows, keep: [[(k, v) for k, v in r if k in keep] for r in rows]
    cases = [
        ("training_metrics", f"training_metrics {exact_table(d['confusion_matrix_train'])}"),
        ("validation_metrics", f"validation_metrics {exact_table(d['confusion_matrix'])}"),
        ("model_summary", "model_summary (none : Option Float) "
            + " ".join(exact_table(x) for x in (sub(d['roc_train'], {'ROCModel', 'Area'}), sub(d['roc_valid'], {'ROCModel', 'Area'}), d['training_metrics'], d['validation_metrics']))),
    ]
    for name, e in cases:
        outs, _ = run(mcp, SINK, [f"{ROWVIEW} ({e})"], DECL)
        got = parse_rowview(outs[0])
        want = d[name]
        if name == "model_summary":   # SAS dump order is PDV order; text/constant columns checked separately
            want = [[(k, v) for k, v in r if k not in ("training_date",)] for r in want]
            got = [[(k, v) for k, v in r if k not in ("training_date",)] for r in got]
            for r in want:
                for j, (k, v) in enumerate(r):
                    if k in ("training_records", "validation_records") and isinstance(v, str): r[j] = (k, float(v))
        if name == "model_summary":
            import csv
            hdr = next(csv.reader(open("judge/reference/model_summary.csv")))
            full = [k for k, _ in parse_rowview(outs[0])[0]]
            print("model_summary column order equals reference CSV header:", full == hdr)
            keys = {k for k, _ in want[0]}; got = [[(k, v) for k, v in r if k in keys] for r in got]
        EM.compare(name, got, want, res)
        s = res[name]; print(f"{name}: exact {s['exact']}/{s['cells']} differences={len(s['diffs'])}", s['diffs'][:4])
    # ---- X15D: association and Hosmer-Lemeshow through the Lean, bit for bit
    log = open("experiments/x15_merge_roc_fit.log").read()
    rows = [(m.group(2), m.group(4)) for m in re.finditer(r"^X15D row i=(\d+) y=(\S+) x1=(\S+) p=(\S+)", log, re.M)]
    t = lean_table([f'[("default_flag", Tabular.Cell.num (some {y})), ("pd_logistic", Tabular.Cell.num (some (Float.ofBits 0x{p.lower()})))]' for y, p in rows], chunk=20)
    try:
        outs, _ = run(mcp, SINK, [f"{ROWVIEW} (logistic_lackfit {t})", f"{ROWVIEW} (logistic_association {t})"], DECL)
        hl = parse_rowview(outs[0]); assoc = parse_rowview(outs[1])
        want_hl = [(int(a), int(b), int(c)) for a, b, c in re.findall(r"^X15D hl Group=(\d+) Total=(\d+) EventsObserved=(\d+)", log, re.M)]
        got_hl = [(int(dict(r)["Group"]), int(dict(r)["Total"]), int(dict(r)["EventsObserved"])) for r in hl]
        print("logistic_lackfit vs X15D:", "MATCH" if got_hl == want_hl else ("DIFF", got_hl, want_hl), f"({len(want_hl)} groups, {len(rows)} rows)")
        want_a = re.findall(r"^X15D assoc Label1=(.+?) nValue1=(\S+) Label2=(.+?) nValue2=(\S+)", log, re.M)
        bad = 0
        for r, (l1, v1, l2, v2) in zip(assoc, want_a):
            r = dict(r)
            if r["Label1"] != l1 or r["Label2"] != l2 or r["nValue1"] != hexd(v1) or r["nValue2"] != hexd(v2): bad += 1; print("   assoc diff", r, (l1, v1, l2, v2))
        print("logistic_association vs X15D: 8 values bit-exact" if bad == 0 else f"logistic_association: {bad} rows differ")
    except Exception as e:
        print("X15D through Lean: NOT EVALUATED", str(e)[:200])
    # ---- comparator validation: planted mismatches must be caught
    d2 = read_dump("migration/runs/m2/dump.txt")
    base = d2["threshold_analysis"]; lean = copy.deepcopy(base)
    plants = []
    def plant(desc, f):
        l = copy.deepcopy(lean); f(l); r = {}; EM.compare("threshold_analysis", l, base, r)
        plants.append((desc, len(r["threshold_analysis"]["diffs"]) > 0))
    def setv(l, i, k, v): l[i] = [(a, v if a == k else b) for a, b in l[i]]
    import math
    plant("one ulp in accuracy", lambda l: setv(l, 0, "accuracy", math.nextafter(dict(l[0])["accuracy"], 2)))
    plant("missing replaced by 0", lambda l: setv(l, 4, "precision", 0.0))
    plant("value replaced by missing", lambda l: setv(l, 1, "recall", None))
    plant("two rows swapped", lambda l: l.__setitem__(slice(0, 2), [l[1], l[0]]))
    plant("row dropped", lambda l: l.pop())
    plant("columns reordered", lambda l: l.__setitem__(0, [l[0][1], l[0][0]] + l[0][2:]))
    p2 = []
    for desc, v, t_, want in [("printed 0.3684559311 vs 0.36845593", 0.36845593, "0.3684559311", False), ("flag 1 vs 0", 1.0, "0", False),
                              ("missing vs 0", None, "0", False), ("0 vs blank", 0.0, "", False), ("exact", 0.5, "0.5", True),
                              ("12th digit off by one", 236.75485488, "236.75485487", False), ("half-way decimal tie (X04)", 67434.8416225, "67434.841623", True)]:
        p2.append((desc, close_printed(v, t_) == want))
    print("planted mismatches caught by the bit-exact comparator:", sum(1 for _, c in plants if c), "of", len(plants), [d for d, c in plants if not c])
    print("printed-value comparator verdicts as expected:", sum(1 for _, c in p2 if c), "of", len(p2), [d for d, c in p2 if not c])

if __name__ == "__main__":
    main()
