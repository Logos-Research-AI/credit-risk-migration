import sys, traceback, tempfile, contextlib, io
from pathlib import Path
sys.path.insert(0, "diffeval/units"); sys.path.insert(0, "diffeval")
sys.argv = ["x"]
import fz2_train_run_gen as g
from credit_risk import train
s = int(sys.argv[1]) if len(sys.argv) > 1 else 70168
ft, fv = g.frames(70168)
print(ft.height, fv.height, fv.get_column("default_flag").to_list(), ft.get_column("default_flag").null_count())
with tempfile.TemporaryDirectory() as td:
    ind = Path(td); ft.write_csv(ind / "model_features_train.csv"); fv.write_csv(ind / "model_features_validation.csv")
    try:
        with contextlib.redirect_stdout(io.StringIO()) as buf:
            train.run(ind, ind / "o")
    except Exception:
        tb = traceback.format_exc().splitlines()
        print("\n".join(l for l in tb if "train.py" in l or "Error" in l)[:1500])
        print(buf.getvalue()[-600:])
