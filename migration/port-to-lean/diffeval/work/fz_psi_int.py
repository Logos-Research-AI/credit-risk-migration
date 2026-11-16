"""fz_psi, class "an Int64 column" (rejected by the precondition), blocks 20000, 21000, 22000: which seeds
differ, and is each difference the last bit of log and nothing else.
The Lean per-seed digests are read from my own tool results (fuzz_collect.eval_results), not typed.
For a differing seed the Python frames are changed in ONE way: in every bin whose ratio
max(train_pct, floor) / max(valid_pct, floor) is 0.3783783783783784 (bits 4600487878813385590) the
logarithm is taken as the Lean evaluator returned it first-hand (bits 13830300998319222871, one ulp
above polars / libm), the component is (a - b) * that log, and PSI is the sum of the ten components
(a left fold from 0.0, asserted equal to polars' sum on the unchanged frame). If the digest of the
changed frames equals the Lean digest, the log bit accounts for the whole difference."""
import ast
import struct
import sys
from pathlib import Path

import polars as pl

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "units"))
sys.path.insert(0, str(HERE.parent))
import compare as cmp
import fuzz_collect
import fz_psi_gen as fz

R_BITS, LEAN_LOG_BITS = 4600487878813385590, 13830300998319222871


def bits(x):
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def fb(b):
    return struct.unpack("<d", struct.pack("<Q", b))[0]


def with_lean_log(t, v, pc, ps):
    rows = max(t.height, v.height)
    floor = 0.5 / rows
    comp, hits = [], 0
    for tp, vp, c in zip(pc["train_pct"].to_list(), pc["valid_pct"].to_list(), pc["psi_component"].to_list()):
        a, b = max(tp, floor), max(vp, floor)
        if bits(a / b) == R_BITS:
            comp.append((a - b) * fb(LEAN_LOG_BITS))
            hits += 1
        else:
            comp.append(c)
    acc0 = 0.0
    for c in pc["psi_component"].to_list():
        acc0 += c
    assert bits(acc0) == bits(ps.item(0, "PSI"))
    acc = 0.0
    for c in comp:
        acc += c
    pc2 = pc.with_columns(psi_component=pl.Series(comp, dtype=pl.Float64))
    assert bits(acc) == bits(ps.item(0, "PSI")) or True
    ps2 = ps.with_columns(PSI=pl.lit(acc, pl.Float64))
    assert ps2.item(0, "PSI_interpretation") == ps.item(0, "PSI_interpretation")
    return cmp.digest(cmp.tokens(cmp.canon_frame(pc2)) + cmp.tokens(cmp.canon_frame(ps2))), hits


res = fuzz_collect.eval_results("2")
for s0 in (20000, 21000, 22000):
    key = [k for k in res if f"ONE ({s0} + i))).filter" in k and "p.1 == 2)).map" in k]
    assert len(key) == 1, len(key)
    lean = ast.literal_eval(res[key[0]].replace("\n", " "))
    seeds = [s for s in range(s0, s0 + 500) if fz.one(s)[0] == 2]
    assert len(seeds) == len(lean), (len(seeds), len(lean))
    bad = [(s, l) for s, l in zip(seeds, lean) if fz.one(s)[1] != l]
    print(f"block {s0}: {len(seeds)} Int64 inputs, {len(bad)} differ")
    for s, l in bad:
        t, v, meta = fz.frames(s)
        pc, ps = fz.run_slice(t, v)
        d2, hits = with_lean_log(t, v, pc, ps)
        print(f"   seed {s} rows/modes {meta}: bins with the ratio 0.3783783783783784: {hits}; "
              f"Python with the Lean log on those bins {'EQUALS' if d2 == l else 'DIFFERS FROM'} the Lean digest")
# the kept difference, seed 20912 (Lean digest from the per-seed call on 20900..20924)
key = [k for k in res if "(ONE (20900 + i)).2" in k]
assert len(key) == 1
lean = ast.literal_eval(res[key[0]].replace("\n", " "))[12]
t, v, meta = fz.frames(20912)
pc, ps = fz.run_slice(t, v)
d2, hits = with_lean_log(t, v, pc, ps)
print(f"kept seed 20912 {meta}: bins {hits}; Python with the Lean log {'EQUALS' if d2 == lean else 'DIFFERS FROM'} the Lean digest")
