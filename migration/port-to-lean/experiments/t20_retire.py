"""T20 (2026-11-16): the scripts of update-after-verification.md section 4 call keywords or a
function the port no longer has. Each is a record of the port before the update; its recorded
output stays. This script marks each one retired: a note and an early exit at the top, naming the
generators that test the same units on the current port. b3_gen.py is not retired: only its
proc_rank_apply_groups suite is taken out of the list it writes.
Run once from migration/port-to-lean; running it again changes nothing.
"""

from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
MARK = "RETIRED 2026-11-16"
RETIRE = {
    "experiments/inv02_stage_edges.py": "export_train_medians, fix_train_medians, medians, fix_psi_bins; "
    "the stage edges are now in diffeval/units/t6_gen.py, t11_gen.py, t16_gen.py",
    "experiments/inv01_unit_edges.py": "sas_compat.proc_rank_apply_groups",
    "experiments/e05_frames_numpy.py": "sas_compat.proc_rank_apply_groups",
    "diffeval/units/b6_gen.py": "fix_psi_bins; see t12_gen.py to t16_gen.py",
    "diffeval/units/b7_gen.py": "fix_income_truncation, export_train_medians; see t2_gen.py, t3_gen.py, t4_gen.py, "
    "t5t9_gen.py, t6_gen.py",
    "diffeval/units/b8_gen.py": "fix_train_medians, medians; see t7_gen.py, t8_gen.py, t9_gen.py, t11_gen.py",
    "diffeval/units/c7927_gen.py": "fix_train_medians, medians; see t5t9_gen.py, t8_gen.py",
    "diffeval/units/r3_gen.py": "fix_psi_bins in the slice of step 06; see t14_gen.py, t15_gen.py",
    "diffeval/units/runs_r2_gen.py": "export_train_medians, fix_income_truncation, fix_train_medians, medians, "
    "fix_psi_bins; see t6_gen.py, t11_gen.py, t16_gen.py, t18_gen.py",
}

for rel, why in RETIRE.items():
    p = HERE / rel
    text = p.read_text()
    if MARK in text:
        print("already", rel)
        continue
    head = (
        f"# {MARK}: this script is a record of the port before the update of 2026-11-16 and no longer\n"
        f"# runs: it calls {why}.\n"
        "# Its recorded outputs describe the port as it was then.\n"
        "import sys as _sys\n\n"
        f'_sys.exit("{MARK}: " + __file__ + " calls keywords the port no longer has; see the note at its top")\n\n'
    )
    # a module docstring, if any, must stay first for `from __future__` lines after it: put the guard
    # after the last `from __future__` line, else at the very top
    lines = text.split("\n")
    at = 0
    for i, ln in enumerate(lines):
        if ln.startswith("from __future__"):
            at = i + 1
    if at == 0:
        new = head + text
    else:
        new = "\n".join(lines[:at]) + "\n\n" + head + "\n".join(lines[at:])
    p.write_text(new)
    print("retired", rel)

b3 = HERE / "diffeval/units/b3_gen.py"
t = b3.read_text()
old = "    for mk in (suite_ratio, suite_rank, suite_apply, suite_merge):"
new = (
    "    # 2026-11-16: suite_apply (proc_rank_apply_groups) is left out: the function was removed from\n"
    "    # the port and its item from the blueprint (T15)\n"
    "    for mk in (suite_ratio, suite_rank, suite_merge):"
)
if old in t:
    b3.write_text(t.replace(old, new))
    print("b3: suite_apply taken out")
else:
    print("b3: already")
