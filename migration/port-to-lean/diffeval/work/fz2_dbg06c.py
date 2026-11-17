import sys, json
sys.path.insert(0, "diffeval")
import fuzz_collect as fc
got = fc.eval_results("10")
key = [k for k in got if k.endswith("(tk (U6 300006 ++ U6 301212 ++ U6 301515 ++ U6 303397 ++ U6 300445)))")]
lean = json.loads(got[key[-1]])
py = json.load(open("diffeval/work/fz2_dbg06b.tokens.json"))
pos = 0
for s in ["300006", "301212", "301515", "303397", "300445"]:
    p = py[s]; l = lean[pos:pos + len(p)]; pos += len(p)
    d = [i for i in range(len(p)) if p[i] != l[i]]
    print(s, len(p), "diff at", d)
    for i in d[:1]:
        a = max(0, i - 24)
        print("  py  ", "".join(chr(c) if 32 <= c < 127 else "|" for c in p[a:i + 8]))
        print("  lean", "".join(chr(c) if 32 <= c < 127 else "|" for c in l[a:i + 8]))
print(pos, len(lean))
