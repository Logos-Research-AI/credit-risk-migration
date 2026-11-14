import sys, json
row = json.loads(sys.stdin.read())
assert len(row) == 7 and all("\t" not in f and "\n" not in f for f in row)
open("/Users/cristophersalvi/GitHub/sas-migration/migration/inventory.modelstat-fit.tsv", "a").write("\t".join(row) + "\n")
