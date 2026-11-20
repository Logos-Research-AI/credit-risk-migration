"""Fidelity pass 2026-11-20, third attempt (label stale-compositions): how many seeds of suite fz10_run reach the
seeded draw of the split (feature_engineering._split_draw, port HEAD 4a757fb) in the CURRENT Python.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_stale_drawcount.py

Wraps feature_engineering._split_draw with a counter (the real function still runs) and replays the seeds
1_000_000..1_002_399 exactly as fz10_run_gen does (same frames, same split files, the real run). Prints, for
the kept seeds whose run completes: how many took the draw, how many used the file as given, and the
draw sizes (len(input_ids), n_train) seen, plus the draws where the drawn ids differ from the first n_train
sorted ids (a draw that is not the identity on the pool).
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fz10_run_gen  # noqa: E402,F401
import fz_run_gen as g  # noqa: E402
from credit_risk import feature_engineering as fe  # noqa: E402

calls: list = []
_orig = fe._split_draw


def counted(input_ids, n_train, seed=42):
    r = _orig(input_ids, n_train, seed)
    calls.append((len(input_ids), n_train, r != sorted(input_ids)[:n_train]))
    return r


fe._split_draw = counted
stat = Counter()
sizes = Counter()
for seed in range(1_000_000, 1_002_400):
    df, sp = g.mk(seed), g.split(seed)
    calls.clear()
    r = g.pyrun(g.csv_text(df), "row_id\n" + "".join(f"{int(i)}\n" for i in sp), df)
    if not r["held"] or r["raised"] is not None:
        continue
    ok = g.precond(df, r["stop"], sp)
    if r["stop"]:
        stat["stop"] += 1
        continue
    key = ("kept " if ok else "rejected ") + ("draw" if calls else "file as given")
    stat[key] += 1
    if calls:
        sizes[calls[0][:2]] += 1
        stat[key + (" (not the first n_train sorted ids)" if calls[0][2] else " (equals the first n_train sorted ids)")] += 1
print(dict(stat))
print("draw sizes (len(input_ids), n_train):", dict(sorted(sizes.items())))
