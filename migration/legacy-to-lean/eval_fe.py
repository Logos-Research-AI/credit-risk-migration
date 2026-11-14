"""Differential evaluation of the feature-engineering chain (credit_raw_clean -> credit_cleaned
-> income_medians -> credit_imputed -> credit_features, and the predict.sas twins) against the
reference CSVs SAS wrote. Usage: python3 migration/eval_fe.py <sink_item> <sink_decl> [n]"""
import csv, random, sys, statistics, collections
sys.path.insert(0, "migration")
from diffeval import *

RAW = ["VAR1","SeriousDlqin2yrs","RevolvingUtilizationOfUnsecuredL","age","NumberOfTime30-59DaysPastDueNotW","DebtRatio",
       "MonthlyIncome","NumberOfOpenCreditLinesAndLoans","NumberOfTimes90DaysLate","NumberRealEstateLoansOrLines",
       "NumberOfTime60-89DaysPastDueNotW","NumberOfDependents"]

def raw_rows(path, inc_len):
    out = {}
    with open(path) as f:
        r = csv.reader(f); next(r)
        for v in r:
            v = list(v); v[6] = v[6][:inc_len] if inc_len else v[6]; v[11] = v[11][:2]
            out[v[0]] = v
    return out

def raw_term(v, test=False):
    cols = []
    for n, x in zip(RAW, v):
        if test and n == "SeriousDlqin2yrs": cols.append((n, "s", ""))   # all-blank column
        elif n in ("MonthlyIncome", "NumberOfDependents"): cols.append((n, "s", x))
        else: cols.append((n, "n", x))
    return lean_row(cols)

def group(age):
    return 1 if age < 30 else 2 if age < 40 else 3 if age < 50 else 4 if age < 60 else 5

def medians(raw):
    g = collections.defaultdict(list)
    for v in raw.values():
        if v[6] != "NA": g[group(float(v[3]))].append(float(v[6]))
    def med(xs):
        xs = sorted(xs); n = len(xs)
        return xs[n//2] if n % 2 else xs[n//2-1] + (xs[n//2] - xs[n//2-1]) / 2
    return {k: med(x) for k, x in g.items()}

def med_term(m):
    return lean_table([lean_row([("age_group","n",str(k)),("median_income","n",repr(v))]) for k, v in sorted(m.items())])

def main():
    sink, decl = sys.argv[1], sys.argv[2]; n = int(sys.argv[3]) if len(sys.argv) > 3 else 400
    mcp = Mcp(); random.seed(11); report = []
    for label, rawpath, inc_len, refs, chain, key in [
        ("train", "data/cs-training.csv", 5, ["judge/reference/model_features_train.csv", "judge/reference/model_features_validation.csv"],
         "credit_features (α := Float) (credit_imputed (α := Float) (fun t => t) (credit_cleaned (α := Float) (credit_raw_clean (α := Float) {raw})) {med})", False),
    ]:
        raw = raw_rows(rawpath, inc_len); m = medians(raw)
        ref = {}
        for p in refs:
            for r in csv.DictReader(open(p)): ref[r["row_id"]] = r
        ids = list(ref)
        # cover the inventory: extremes and missing first, then random
        def score(i):
            v = raw[i]; return (v[6] == "NA") + (v[11] == "NA") + (float(v[2]) > 1) + (float(v[5]) > 5) + (float(v[3]) < 22) + (v[6] == "0") + (float(v[8]) > 0)
        special = sorted(ids, key=score, reverse=True)[: n // 4]
        pick = special + random.sample(ids, n - len(special))
        bad = 0; cells = 0; examples = []
        for k in range(0, len(pick), 100):
            chunk = pick[k:k+100]
            expr = f"{VIEW} ({chain.format(raw=lean_table([raw_term(raw[i]) for i in chunk]), med=med_term(m))})"
            outs, ms = run(mcp, sink, [expr], decl)
            got = parse_view(outs[0])
            assert len(got) == len(chunk), (len(got), len(chunk))
            for i, g in zip(chunk, got):
                r = ref[i]
                assert list(g.keys()) == list(r.keys()), (list(g.keys()), list(r.keys()))
                for c in r:
                    cells += 1
                    if not close_printed(g[c], r[c]):
                        bad += 1
                        if len(examples) < 15: examples.append((i, c, g[c], r[c]))
        report.append((label, len(pick), cells, bad, examples))
    for label, rows, cells, bad, ex in report:
        print(f"{label}: rows={rows} cells={cells} differences={bad}")
        for e in ex: print("   ", e)

if __name__ == "__main__":
    main()
