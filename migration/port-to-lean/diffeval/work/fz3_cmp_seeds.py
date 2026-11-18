import json, re, sys
pyf, a, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
py = json.load(open(pyf))
nums = [int(x) for x in re.findall(r"\d+", out)]
bad = 0
for i in range(len(nums) // 2):
    s = a + i
    e = py[str(s)]
    iw, ow = nums[2 * i], nums[2 * i + 1]
    ok_i, ok_o = iw == e["iw"], ow == e["ow"]
    if not (ok_i and ok_o):
        bad += 1
        print("seed", s, e["cls"], "input digest", "ok" if ok_i else f"DIFF py {e['iw']} lean {iw}", "| output", "ok" if ok_o else f"DIFF py {e['ow']} lean {ow}", e["ex"])
print("compared", len(nums) // 2, "seeds; differing", bad)
