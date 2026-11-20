"""Fidelity pass 2026-11-20 (label stale-compositions): def:run_py_py (predict.run) as a whole against
the CURRENT Python (port HEAD 4a757fb: the fourth diff's keep_sas_names in :447-469 included).

  cd migration/port-to-lean && PYTHONPATH=../../port uv run --project ../../port python diffeval/units/fz10_run_py_py_gen.py
      -> diffeval/work/fz10_run_py_py.{json,inputs.json,fuzz.json}

The generator of 2026-11-16 (diffeval/units/fz_run_py_py_gen.py, port-translator-3), executed unchanged
except: seeds 2_000_000.. (104 blocks of 25 = 2,600 seeds), suite fz10_run_py_py, receipt metadata
(fuzzer, generator, blueprint 5365851c), and its fixed note about the 2026-11-16 differing blocks left
out. The Python side is the REAL predict.run at HEAD on written files (cs-test.csv, income_medians,
model.json, model_coefficients.csv), write_sas_csv recorded; the cases now include, through the
pool of column names (AGE upper, all upper, all lower, a second "AGE" column), the case-blind keep of
sas_compat.keep_sas_names.
Carrier def:zz_carrier_p as in 2026-11-16. ON 2026-11-20 NO zz_carrier_* ITEM EXISTS on 5365851c and
eval_decl refuses def:run_py_py itself (call-level refusal): the suite is generated and its Python
side run, the Lean side is NOT evaluated.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRCF = HERE / "fz_run_py_py_gen.py"
src = SRCF.read_text()
REPL = [
    ("SEED0, CH, NCH = 30000, 25, 104", "SEED0, CH, NCH = 2_000_000, 25, 104"),
    ('st = Suite("fz_run_py_py")', 'st = Suite("fz10_run_py_py", generator="port-to-lean/diffeval/units/fz10_run_py_py_gen.py")'),
    ('fuzz = {"fuzzer": "port-translator-3", "generator": "diffeval/units/fz_run_py_py_gen.py", "units"',
     'fuzz = {"fuzzer": "port-translator (stale-compositions 2026-11-20)", "generator": "diffeval/units/fz10_run_py_py_gen.py", '
     '"blueprint": "5365851c-5549-44b7-9207-4bd4c422031d", "units"'),
    ('''                "; the 3 differing blocks are seeds 30930, 31316, 31393: last bit of exp (recorded limit, RULEBOOK 6), "
                "shown by experiments/fz_run_py_py_exp_last_bit.py"}}}''', '''}}}'''),
    ('(HERE.parent / "work" / "fz_run_py_py.fuzz.json")', '(HERE.parent / "work" / "fz10_run_py_py.fuzz.json")'),
    ('st.notes = {U: "fuzz 2026-11-16"}', 'st.notes = {U: "fidelity pass 2026-11-20 (stale-compositions)"}'),
]
for a, b in REPL:
    assert src.count(a) == 1, a
    src = src.replace(a, b)
mod = types.ModuleType("fz10_run_py_py_impl")
mod.__file__ = str(SRCF)  # HERE inside resolves to diffeval/units
sys.modules["fz10_run_py_py_impl"] = mod
exec(compile(src, str(SRCF), "exec"), mod.__dict__)

if __name__ == "__main__":
    mod.main()
