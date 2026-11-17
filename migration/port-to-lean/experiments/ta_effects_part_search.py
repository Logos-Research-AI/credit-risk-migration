"""T-A 2026-11-17: which slice of the training file of tc_gen's scenario `effects` (90 rows) gives a
train.run that ends with a final model with effects, on at most 55 rows (the 90-row step-08 input
did not elaborate on the server). Prints (start, stop, final.names, n_obs)."""
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "diffeval" / "units"))
sys.path.insert(0, str(HERE.parent / "diffeval"))
import tc_gen as tc  # noqa: E402
from credit_risk import sas_compat as sc  # noqa: E402

src = tc.scenario_dir("effects")
d = sc.proc_import_csv(src / "model_features_train.csv", guessingrows=None)
for a, b in ((0, 55), (10, 60), (20, 70), (30, 80), (35, 90), (40, 90), (0, 45), (45, 90), (5, 55), (25, 75)):
    with tempfile.TemporaryDirectory(dir=tc.DATA) as td:
        td = Path(td)
        d[a:b].write_csv(td / "model_features_train.csv")
        shutil.copy(src / "model_features_validation.csv", td / "model_features_validation.csv")
        r = tc.real_run(td, True)
        if r["raised"]:
            print(a, b, "raised:", r["raised"][:90])
        else:
            L = r["locals"]
            print(a, b, L["final"].names, int(L["n_obs"]))
