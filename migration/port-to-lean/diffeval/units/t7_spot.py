"""T7 spot check: the small scenarios of t7_gen.py as one short eval input (run by the translator
itself, independently of the full run).
  PYTHONPATH=../../port uv run --project ../../port python diffeval/units/t7_spot.py
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import t7_gen as g  # noqa: E402

PICK = ["fix_Q27_emptytest/header_only", "fix_Q27_emptytest/crlf_header_only", "fix_Q27_emptytest_badheader/blank_line",
        "fix_Q27_emptytest_badheader/eleven_names", "fix_Q27_emptytest_badheader/duplicate_name_only",
        "fix_round5/test_header_only_age_upper", "fix_Q27_test", "fix_Q27"]
recs = [(n, g.pyrun(d)) for n, d in g.scenario_dirs() if n in PICK]
with tempfile.TemporaryDirectory() as t:
    recs.append(("hand/absent_file", g.pyrun(Path(t))))
    for name, text in g.HAND.items():
        d = Path(t) / name.replace("/", "_")
        d.mkdir()
        (d / "cs-test.csv").write_bytes(text.encode())
        recs.append((name, g.pyrun(d)))
s = g.Suite("t7_spot")
s.item, s.decl, s.carrier = "def:zz_carrier_p", "zz_carrier_p", "identity"
g.build_input(s, recs)
s.write()
