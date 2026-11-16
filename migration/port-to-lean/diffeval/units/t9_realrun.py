"""port-translator-9 (T10, T17, T18): one real run of feature engineering, train and predict on
legacy/data; the locals of train.run and predict.run are captured at return (profile hook) and the
frames that steps 12 (train) and 07/08 (predict) read and produce are saved as parquet under
diffeval/work/t9/. Nothing of the port is copied."""
import contextlib, io, sys, time, pickle
from pathlib import Path
import polars as pl
HERE = Path(__file__).resolve().parent
PTL = HERE.parents[1]
ROOT = PTL.parents[1]
from credit_risk import feature_engineering as fe, train as tr, predict as pr, sas_compat as sc

W = PTL / "diffeval" / "work" / "t9"
OUT = W / "out"
OUT.mkdir(parents=True, exist_ok=True)
DATA = ROOT / "legacy" / "data"

def capture(mod, fn):
    rec = {}
    def prof(frame, event, arg):
        if event in ("return",) and frame.f_code is mod.run.__code__:
            rec.update(frame.f_locals)
    sys.setprofile(prof)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            fn()
    finally:
        sys.setprofile(None)
    return rec

t = time.time()
with contextlib.redirect_stdout(io.StringIO()):
    fe.run(DATA, OUT, split_ids=PTL / "inputs" / "split_ids.csv")
print("fe", time.time() - t, sorted(p.name for p in OUT.iterdir()), flush=True)
t = time.time()
L = capture(tr, lambda: tr.run(OUT, OUT))
print("train", time.time() - t, sorted(p.name for p in OUT.iterdir()), flush=True)
for n in ("logit_scored_train", "logit_scored_valid", "risk_scores_train", "risk_scores_validation"):
    L[n].write_parquet(W / f"train_{n}.parquet")
    print(n, L[n].shape, L[n].schema, flush=True)
t = time.time()
L = capture(pr, lambda: pr.run(OUT, OUT, data_dir=DATA, income_medians=OUT / "income_medians.csv"))
print("predict", time.time() - t, sorted(p.name for p in OUT.iterdir()), flush=True)
for n in ("test_scored", "test_predictions", "kaggle_submission", "test_predictions_full"):
    L[n].write_parquet(W / f"predict_{n}.parquet")
    print(n, L[n].shape, L[n].schema, flush=True)
print("age_name", repr(L["age_name"]))
