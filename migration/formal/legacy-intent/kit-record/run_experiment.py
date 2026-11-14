"""Submit one SAS program to SAS OnDemand (same saspy profile as judge/run_sas.py) and save
its log and listing next to it. Usage (from the workspace root):
    uv run --project judge python migration/run_experiment.py experiments/x10_name.sas
Observation only: the program is submitted verbatim."""
import sys
from pathlib import Path
import saspy

def main() -> int:
    paths = [Path(p) for p in sys.argv[1:]]
    sas = saspy.SASsession(cfgname="oda_eu", results="TEXT")
    try:
        for p in paths:
            res = sas.submit(p.read_text())
            p.with_suffix(".log").write_text(res["LOG"])
            if res["LST"].strip():
                p.with_suffix(".lst").write_text(res["LST"])
            errs = [l for l in res["LOG"].splitlines() if l.startswith("ERROR")]
            print(p.name, "ERRORS:", len(errs))
            for e in errs[:10]:
                print("   ", e)
    finally:
        sas.endsas()
    return 0

if __name__ == "__main__":
    sys.exit(main())
