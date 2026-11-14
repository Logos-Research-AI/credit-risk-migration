"""Print the suite-specific part of a suite's inputs (after the fixed KIT/GEN/LETS preamble)."""
import json
import sys
from pathlib import Path

for call in json.loads((Path(__file__).parent / "work" / f"{sys.argv[1]}.inputs.json").read_text()):
    for t in call["inputs"]:
        k = t.find("| _, _ => none : Option Float)) x y; ")
        print(json.dumps(t[k + 37:] if k >= 0 else t, ensure_ascii=False))
