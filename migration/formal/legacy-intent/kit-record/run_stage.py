"""Run one ORIGINAL .sas script on SAS OnDemand on stage inputs of our choosing, and dump the
work data sets it builds in full precision (HEX16.), for differential evaluation of the Lean.
Same conventions as judge/run_sas.py (path macros redirected to a fresh folder; nothing else in
the script is changed); the dump is appended after the script.
Usage: uv run --project judge python migration/run_stage.py <run-id> <script.sas> <inputs-dir> ds1 ds2 ...
Output: migration/runs/<run-id>/{log.txt, lst.txt, dump.txt}"""
import re, sys, time
from pathlib import Path
import saspy

ROOT = Path(__file__).resolve().parent.parent

def main():
    run_id, script, indir, *datasets = sys.argv[1:]
    out = ROOT / "migration" / "runs" / run_id
    out.mkdir(parents=True, exist_ok=False)
    src = (ROOT / script).read_text()
    sas = saspy.SASsession(cfgname="oda_eu", results="TEXT")
    try:
        log = sas.submit("%put JUDGEHOME=%sysget(HOME);")["LOG"]
        home = next(l.split("=", 1)[1].strip() for l in log.splitlines() if l.startswith("JUDGEHOME="))
        root = f"{home}/sasmig/runs/lean-{run_id}-{time.strftime('%Y%m%dT%H%M%S')}"
        d, o, g = f"{root}/data", f"{root}/output", f"{root}/graphs"
        sas.submit(f'options dlcreatedir; libname _mk "{home}/sasmig"; libname _mk "{home}/sasmig/runs"; '
                   f'libname _mk "{root}"; libname _mk "{d}"; libname _mk "{o}"; libname _mk "{g}"; libname _mk clear;')
        sas.submit(f'ods listing gpath="{g}";')
        for p in sorted(Path(indir).glob("*.csv")):
            dest = d if p.name.startswith("cs-") else o
            r = sas.upload(str(p), f"{dest}/{p.name}", overwrite=True)
            if not r.get("Success"): raise RuntimeError(f"upload {p}: {r}")
        src = re.sub(r"%let\s+data_path\s*=\s*[^;]*;", f"%let data_path = {d};", src)
        src = re.sub(r"%let\s+output_path\s*=\s*[^;]*;", f"%let output_path = {o};", src)
        res = sas.submit(src)
        (out / "log.txt").write_text(res["LOG"]); (out / "lst.txt").write_text(res["LST"])
        dump = "".join(
            f'data _null_; file "{root}/dump_{ds}.txt" lrecl=32767; set work.{ds}; put "DUMP {ds} " (_all_) (=); run;\n'
            f'data _null_; file "{root}/dumpx_{ds}.txt" lrecl=32767; set work.{ds}; put "DUMPX {ds} " (_numeric_) (=hex16.); run;\n'
            for ds in datasets)
        sas.submit(dump)
        lines = []
        for ds in datasets:
            for pre in ("dump", "dumpx"):
                loc = out / f"{pre}_{ds}.txt"
                r = sas.download(str(loc), f"{root}/{pre}_{ds}.txt")
                if r.get("Success"): lines += loc.read_text().splitlines(); loc.unlink()
        extra = Path(indir) / "extra.sas"
        if extra.exists():
            res2 = sas.submit(extra.read_text())
            lines += [l for l in res2["LOG"].splitlines() if l.startswith("DUMP")]
        (out / "dump.txt").write_text("\n".join(lines))
        errs = [l for l in res["LOG"].splitlines() if l.startswith("ERROR")]
        print(run_id, "ERRORS:", errs[:5])
    finally:
        sas.endsas()

if __name__ == "__main__":
    main()
