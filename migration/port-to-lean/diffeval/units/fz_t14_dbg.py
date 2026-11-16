"""Fuzz pass, T14 units: one digest PER SEED for a window of seeds (to find which seed of a failed
case differs), and the comparison with the tool results of the session record.

  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_t14_dbg.py gen 05 <start> <count> [parts]
      -> prints the eval input (work/fz_dbg_<unit>_<start>.txt) and saves the expected digests
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz_t14_dbg.py check 05 <start>
      -> the seeds whose Lean digest differs from the Python digest
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
mode, unit, start = sys.argv[1], sys.argv[2], int(sys.argv[3])
rest = sys.argv[4:]
import fz_t14_gen as f  # noqa: E402
import compare as cmp  # noqa: E402
import kit  # noqa: E402
from suite import WORK  # noqa: E402

t14 = f.t14
base = WORK / f"fz_dbg_{unit}_{start}"
if mode == "gen":
    count = int(rest[0])
    parts = len(rest) > 1
    seeds = list(range(start, start + count))
    best: dict = {}
    exp = []
    for s in seeds:
        if unit == "05":
            dd, da = f.gen05(s)
            out, b = t14.run05(dd, da)
            best.update(b)
            fr = [dd, da, out]
        else:
            df = f.gen04(s)
            ns = t14.run_slice(t14.S04, {"logit_scored_valid": df})
            fr = [df, ns["decile_data"], ns["decile_analysis"]]
        toks = [cmp.tokens(t14.canon(x)) for x in fr]
        exp.append([s] + ([cmp.digest(t) for t in toks] if parts else [cmp.digest([y for t in toks for y in t])]))
    if unit == "05":
        lets = f.l05(f.tables(best))
        old = "tR dd ++ tR da ++ tR (metrics_run_05_cumulative_lift sb pf dd da))"
        new = "[dg (tR dd), dg (tR da), dg (tR (metrics_run_05_cumulative_lift sb pf dd da))])" if parts else "[dg (" + old[:-1] + ")])"
    else:
        lets = f.L04
        old = "tR fr ++ tR r.1 ++ tR r.2)"
        new = "[dg (tR fr), dg (tR r.1), dg (tR r.2)])" if parts else "[dg (" + old[:-1] + ")])"
    assert old in lets
    txt = "(" + kit.KIT_NOTABLE + kit.GEN + lets.replace(old, new) + f"(List.range' {start} {count}).flatMap mk)"
    base.with_suffix(".txt").write_text(txt)
    base.with_suffix(".exp.json").write_text(json.dumps(exp))
    i = txt.index("let T :") if unit == "05" else txt.index("let mk")
    print(len(txt), "chars; from the tables on:\n" + txt[i:])
else:
    import fuzz_collect  # noqa: E402

    res = fuzz_collect.eval_results("12")
    txt = base.with_suffix(".txt").read_text()
    exp = json.loads(base.with_suffix(".exp.json").read_text())
    if txt not in res:
        raise SystemExit("not run (or mistyped)")
    got = [int(x) for x in res[txt].strip("[] ").replace(",", " ").split()]
    k = len(exp[0]) - 1
    assert len(got) == k * len(exp), (len(got), len(exp))
    bad = [(e[0], [j for j in range(k) if got[i * k + j] != e[1 + j]]) for i, e in enumerate(exp) if got[i * k:(i + 1) * k] != e[1:]]
    print(f"{len(exp)} seeds, {len(bad)} differ:", bad)
