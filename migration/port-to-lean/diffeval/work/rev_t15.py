"""Review of T15 by port-translator-2: three extra inputs for def:metrics_run_06_psi
(frames with other columns, one of them already named score_bin; infinities and zeros of both signs)."""
import sys, textwrap
from pathlib import Path
import polars as pl
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import compare as cmp, kit, leanterm as lt
from credit_risk import metrics_calculation as mc
lines = Path(mc.__file__).read_text().splitlines(keepends=True)
assert lines[324].lstrip().startswith("# metrics_calculation.sas:332-346 psi_cuts") and lines[400].strip() == ")"
SL = compile(textwrap.dedent("".join(lines[324:401])), "slice", "exec")
nan, inf = float("nan"), float("inf")
def run(t, v):
    ns = dict(vars(mc)); ns.update(logit_scored_train=t, logit_scored_valid=v); exec(SL, ns)
    return ns["psi_calculation"], ns["psi_summary"]
C = [
 ("other columns, score_bin already present (String), inf and signed zeros",
  pl.DataFrame({"score_bin": ["x"] * 10, "credit_risk_score": [inf, -inf, 700.0, 650.0, -0.0, 0.0, 720.0, 5e-324, 1e308, 650.0], "cnt": [1.5] * 10}),
  pl.DataFrame({"cnt": [2.0] * 7, "train_pct": [9.0] * 7, "credit_risk_score": pl.Series([inf, 0.0, -0.0, nan, None, 700.0, 1e308], dtype=pl.Float64, nan_to_null=False)})),
 ("3 / 7, every validation score above the training scores",
  pl.DataFrame({"credit_risk_score": [600.0, 700.0, 800.0]}), pl.DataFrame({"credit_risk_score": [801.0, 900.0, 800.5, 1000.0, 801.0, 850.0, inf]})),
 ("13 / 2, validation below and null",
  pl.DataFrame({"row_id": [float(i) for i in range(13)], "credit_risk_score": [float(500 + 37 * ((5 * i) % 13)) for i in range(13)]}),
  pl.DataFrame({"credit_risk_score": [None, 1.0]}, schema={"credit_risk_score": pl.Float64})),
]
lets, body, exp = "", [], []
for i, (name, t, v) in enumerate(C):
    pc, ps = run(t, v)
    print(name, pc.rows(), ps.rows())
    lets += lt.lean_frame_let(f"t{i}", t) + lt.lean_frame_let(f"v{i}", v)
    body.append(f"(let r := metrics_run_06_psi t{i} v{i}; [dg (tR r.1), dg (tR r.2)])")
    exp += [cmp.digest(cmp.tokens(cmp.canon_frame(pc))), cmp.digest(cmp.tokens(cmp.canon_frame(ps)))]
term = f"({kit.KIT_NOTABLE}{lets}{' ++ '.join(body)})"
(HERE / "rev_t15.in.txt").write_text(term)
(HERE / "rev_t15.expected.txt").write_text(repr(exp))
print(len(term)); print(exp)
