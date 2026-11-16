"""Run one experiment .sas on the SAS server and keep its log next to it.
Usage (from judge/): uv run python ../migration/legacy-to-port/experiments/x10_run.py <file.sas>"""

import sys
from pathlib import Path

import saspy

src = Path(sys.argv[1])
sas = saspy.SASsession(cfgname="oda_eu", results="TEXT")
try:
    ver = sas.sasver
    res = sas.submit(src.read_text())
finally:
    sas.endsas()
src.with_suffix(".log").write_text(f"{src.stem.split('_')[0].upper()} RUN saspy={saspy.__version__} profile=oda_eu sasver={ver}\n" + res["LOG"])
print(sum(ln.startswith("ERROR") for ln in res["LOG"].splitlines()), "ERROR lines;", len(res["LOG"].splitlines()), "log lines")
