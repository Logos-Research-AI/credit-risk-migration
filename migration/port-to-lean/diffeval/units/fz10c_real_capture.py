"""Fidelity pass 2026-11-20 (third attempt, label train-c): capture the inputs and results of steps 08 and 11 of
the REAL train.run (port HEAD 4a757fb) on the feature files made from legacy/data.

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10c_real_capture.py

Input directory: work/fz10_trainb_real (fe.run(legacy/data, ..., split_ids=inputs/split_ids.csv), made by
fz10_trainb_real_gen.py). train.run(that, <scratch out>) runs under a line tracer that copies the locals of `run`
when it reaches the first line of each slice and when it leaves its last line (as r3_gen.traced).
Writes work/fz10c_real.pkl: {"s08": (in, out), "s11": (in, out)} restricted to the names the slices read/write.
"""
from __future__ import annotations

import contextlib
import io
import pickle
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from credit_risk import train as tr  # noqa: E402

W = HERE.parent / "work"
IND = W / "fz10_trainb_real"
SRC = Path(tr.__file__).read_text().splitlines()


def line_of(pred) -> int:
    return next(i + 1 for i, l in enumerate(SRC) if pred(l))


A08 = line_of(lambda l: l.strip() == "x_final = np.column_stack(")
B08 = line_of(lambda l: 'output_dir / "printed_classification.csv"' in l) + 1
A11 = line_of(lambda l: l.strip() == "confusion_matrix = (")
B11 = line_of(lambda l: ".head(min(confusion_matrix.height, 1))" in l) + 1
SL = {"s08": (A08, B08), "s11": (A11, B11)}
KEEP = {"s08": ["fit_mask", "fit_frame", "final", "final_names", "n_obs", "y_train", "logit_scored_train",
                "x_final", "pd_train", "ctable_made", "ctable", "printed_classification"],
        "s11": ["logit_scored_valid", "confusion_matrix", "confusion_matrix_read", "validation_metrics"]}


def main() -> None:
    snap: dict = {}

    def local(frame, event, arg):
        if event in ("line", "return"):
            for k, (a, b) in SL.items():
                if (k, "in") not in snap and event == "line" and frame.f_lineno >= a:
                    snap[k, "in"] = {n: frame.f_locals.get(n) for n in KEEP[k]}
                if (k, "in") in snap and (k, "out") not in snap and (event == "return" or frame.f_lineno > b):
                    snap[k, "out"] = {n: frame.f_locals.get(n) for n in KEEP[k]}
        return local

    def glob(frame, event, arg):
        return local if frame.f_code is tr.run.__code__ else None

    t0 = time.time()
    with tempfile.TemporaryDirectory() as out, contextlib.redirect_stdout(io.StringIO()):
        sys.settrace(glob)
        try:
            tr.run(IND, Path(out))
        finally:
            sys.settrace(None)
        printed = {p.name: p.read_text() for p in Path(out).glob("printed_c*.csv")}
    res = {k: (snap[k, "in"], snap[k, "out"]) for k in SL}
    res["lines"] = SL
    res["printed"] = printed
    (W / "fz10c_real.pkl").write_bytes(pickle.dumps(res))
    print("lines", SL, "seconds", round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
