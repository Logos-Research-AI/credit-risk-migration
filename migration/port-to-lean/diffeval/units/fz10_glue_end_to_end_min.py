import json, shutil, importlib.util
spec = importlib.util.spec_from_file_location("g", "diffeval/units/fz10_glue_end_to_end_gen.py"); g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
x = g.gen(9001)
lines = x["train"].rstrip("\n").split("\n"); head, body = lines[0], lines[1:]
EXT = f"{len(body)+1},0,1e200,40,0,1e200,5000,1e80,0,1,0,1"
body = body + [EXT]
d = g.WORK / "fz10_min"
def test(rows):
    shutil.rmtree(d, ignore_errors=True); d.mkdir(parents=True)
    rows = [f"{i+1}," + r.split(",", 1)[1] for i, r in enumerate(rows)]
    n = len(rows); ext_id = n  # the extreme row is kept last
    (d/"cs-training.csv").write_text("\n".join([head] + rows) + "\n"); (d/"cs-test.csv").write_text(x["test"])
    nt = (7*n+9)//10
    (d/"split.csv").write_text("row_id\n" + "".join(f"{i}\n" for i in [ext_id] + list(range(1, nt))))
    res = g.run_case(d, d/"split.csv", d/"o", "min")
    return res.get("G4") is False and "pd_logistic" in str(res.get("G4_diff", {}).get("what")), res
assert test(body)[0]
others = body[:-1]
chunk = len(others) // 2
while chunk >= 1:
    i = 0
    while i < len(others):
        cand = others[:i] + others[i+chunk:]
        if len(cand) >= 2 and test(cand + [EXT])[0]:
            others = cand
        else:
            i += chunk
    chunk //= 2
ok, res = test(others + [EXT])
print(len(others) + 1)
print((d/"cs-training.csv").read_text()); print((d/"split.csv").read_text())
print(json.dumps(res.get("G4_diff"), default=str)[:3000])
print(open(d/"o"/"model.json").read())
