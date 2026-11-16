"""E10 (2026-11-16): scenarios whose README says 'Valid files' on which feature_engineering.run stops:
the counters of the real run (profile hook on the locals of run).
  PYTHONPATH=../../port uv run --project ../../port python experiments/e10_valid_stops.py > experiments/e10_valid_stops.out.txt
"""
import contextlib, io, sys, tempfile
from pathlib import Path
from credit_risk import feature_engineering as fe
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
for name in ("fix2/valid_unusual", "fix2/q14_negative_real", "fix2/good", "fix_G34/income_zero"):
    rec = {}
    def prof(fr, ev, arg):
        if ev in ("return", "exception") and fr.f_code is fe.run.__code__:
            rec.update(fr.f_locals)
    with tempfile.TemporaryDirectory() as d:
        sys.setprofile(prof)
        err = None
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                fe.run(ROOT / "judge/scenarios" / name, Path(d), split_ids=HERE.parent / "inputs/split_ids.csv")
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
        finally:
            sys.setprofile(None)
    ic = rec.get("input_check")
    bad = ic.filter(ic["bad_row"] == 1)["VAR1"].to_list() if ic is not None else None
    print(f"{name}: {err or 'completed'}; columns_ok={rec.get('columns_ok')} bad_rows={rec.get('bad_rows')} duplicate_ids={rec.get('duplicate_ids')} known_incomes={rec.get('known_incomes')}; ids of the bad rows: {bad}")
    if bad:
        lines = (ROOT / "judge/scenarios" / name / "cs-training.csv").read_text().split("\n")
        for b in bad[:6]:
            print("    line:", next(x for x in lines[1:] if x.split(",")[0] == str(int(b))))
