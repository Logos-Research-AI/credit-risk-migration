"""T20: the final port run end to end on legacy/data, stage after stage, each stage reading what the
stage before wrote (feature engineering -> train -> predict -> metrics). Prints, for every file
written, its rows and sha256. Then the stops: each stage on a folder without its input.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/t20_e2e.py [stage ...]
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import shutil
import sys
import time
from pathlib import Path

from credit_risk import feature_engineering as fe
from credit_risk import metrics_calculation as mc
from credit_risk import predict as pr
from credit_risk import train as tr

HERE = Path(__file__).resolve().parent
PTL = HERE.parent
DATA = PTL.parent.parent / "legacy" / "data"
OUT = HERE / "work" / "t20_e2e"
SPLIT = PTL / "inputs" / "split_ids.csv"


def quiet(fn):
    buf = io.StringIO()
    t0 = time.time()
    try:
        with contextlib.redirect_stdout(buf):
            fn()
        res = "completed"
    except Exception as e:  # noqa: BLE001
        res = f"stopped: {type(e).__name__}: {e}"
    return res, time.time() - t0, [ln for ln in buf.getvalue().splitlines() if ln.startswith("ERROR")]


def listing(d: Path, before: set[str]) -> None:
    for p in sorted(d.iterdir()):
        if p.is_file():
            b = p.read_bytes()
            new = "" if p.name in before else " (new)"
            print(f"    {p.name}\t{b.count(b'\n')} lines\t{hashlib.sha256(b).hexdigest()[:16]}{new}")


def main() -> None:
    want = set(sys.argv[1:]) or {"fe", "train", "predict", "metrics"}
    if "fe" in want:
        shutil.rmtree(OUT, ignore_errors=True)
    OUT.mkdir(parents=True, exist_ok=True)
    stages = [
        ("fe", lambda: fe.run(DATA, OUT, split_ids=SPLIT)),
        ("train", lambda: tr.run(OUT, OUT)),
        ("predict", lambda: pr.run(OUT, OUT, data_dir=DATA, income_medians=OUT / "income_medians.csv")),
        ("metrics", lambda: mc.run(OUT, OUT)),
    ]
    for name, fn in stages:
        if name not in want:
            continue
        before = {p.name for p in OUT.iterdir()}
        res, dt, errs = quiet(fn)
        print(f"{name}: {res} in {dt:.0f}s")
        listing(OUT, before)
    empty = HERE / "work" / "t20_e2e_empty"
    for name, fn in [
        ("fe on a folder without cs-training.csv", lambda: fe.run(empty, empty / "o", split_ids=SPLIT)),
        ("train on a folder without the feature files", lambda: tr.run(empty, empty / "o")),
        ("predict without medians and model", lambda: pr.run(empty, empty / "o", data_dir=DATA, income_medians=empty / "income_medians.csv")),
        ("metrics without the score files", lambda: mc.run(empty, empty / "o")),
    ]:
        if name.split()[0] not in want:
            continue
        shutil.rmtree(empty, ignore_errors=True)
        empty.mkdir(parents=True)
        res, dt, errs = quiet(fn)
        left = sorted(p.name for p in (empty / "o").iterdir()) if (empty / "o").exists() else []
        print(f"{name}: {res}; files written {left}; {errs}")


if __name__ == "__main__":
    main()
