"""Python side of step 10 (def:train_run_10_score_valid): lines 611-635 of port/credit_risk/train.py executed as they are."""
import sys, textwrap
from pathlib import Path
import polars as pl
HERE = Path(__file__).resolve().parent
PORT = HERE.parents[3] / "port"
sys.path.insert(0, str(PORT))
from credit_risk import sas_compat
SRC = (PORT / "credit_risk" / "train.py").read_text().splitlines()
SEG = textwrap.dedent("\n".join(SRC[610:635]))
def step10(intercept, coefficients, final, model_features_validation):
    ns = dict(pl=pl, sas_compat=sas_compat, intercept=intercept, coefficients=coefficients, final=final,
              model_features_validation=model_features_validation)
    exec(SEG, ns)
    return ns["logit_scored_valid"]
if __name__ == "__main__":
    print(SEG)
