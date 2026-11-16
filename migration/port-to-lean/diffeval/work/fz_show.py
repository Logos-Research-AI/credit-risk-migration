import json, sys
d = json.load(open(f"diffeval/work/{sys.argv[1]}.inputs.json"))
x = d[0]["inputs"][int(sys.argv[2])]
k = x.index(sys.argv[3]) if len(sys.argv) > 3 else 0
print(x[k:])
