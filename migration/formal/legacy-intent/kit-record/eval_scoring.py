"""Differential evaluation of the scoring chains of train.sas and predict.sas, row by row,
against the CSVs SAS wrote, using the fitted model SAS produced on the reference features
(full-precision coefficients from migration/runs/t1/dump.txt)."""
import csv, random, re, sys, collections
sys.path.insert(0, "migration")
from diffeval import *
import eval_fe as FE

M_SINK, M_DECL = "def:model_performance_metrics", "model_performance_metrics.evalApply"
P_SINK, P_DECL = "def:test_predictions_full", "test_predictions_full.evalApply"
STR = {"risk_grade", "recommendation"}

def model_term():
    names = [m.group(1) for m in re.finditer(r"^DUMP model_coefficients Variable=(\S+)", open("migration/runs/t1/dump.txt").read(), re.M)]
    ests = [m.group(1) for m in re.finditer(r"^DUMPX model_coefficients DF=\S+ Estimate=(\S+)", open("migration/runs/t1/dump.txt").read(), re.M)]
    hdr = next(csv.reader(open("judge/reference/model_features_train.csv")))
    terms = []
    for n, e in zip(names[1:], ests[1:]):
        full = [h for h in hdr if h.startswith(n)]
        assert len(full) == 1, (n, full)
        terms.append(f'("{full[0]}", Float.ofBits 0x{e.lower()})')
    return f"(Sas.Model.mk (Float.ofBits 0x{ests[0].lower()}) [{', '.join(terms)}])"

def cmp_rows(got, ref_rows, stats, pct=("interest_rate",)):
    for g, r in zip(got, ref_rows):
        if [k for k, _ in g] != list(r.keys()):
            stats["diffs"].append(("COLUMNS", [k for k, _ in g], list(r.keys()))); return
        for k, v in g:
            stats["cells"] += 1
            t = r[k]
            ok = (v == t or (v == "" and t == "")) if isinstance(v, str) else close_printed(v, t, "pct" if k in pct else "best12")
            if isinstance(v, str) and not ok and v is not None: ok = (v == t)
            if not ok: stats["diffs"].append((r.get("row_id"), k, v, t))

def pick(ref, n, seed):
    random.seed(seed); ids = list(ref)
    def edge(i):
        try: pd = float(ref[i]["pd_logistic"])
        except ValueError: return -1.0
        frac = (250 * (1 - pd)) % 1
        return min(abs(frac - 0.5), abs(pd - 0.5) * 10)
    special = sorted(ids, key=edge)[: n // 3]
    return special + random.sample(ids, n - len(special))

def run_chunks(mcp, sink, decl, mk_expr, items, chunk):
    out = []
    for k in range(0, len(items), chunk):
        outs, _ = run(mcp, sink, [mk_expr(items[k:k+chunk])], decl)
        out += parse_rowview(outs[0])
    return out

def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    mcp = Mcp(); MODEL = model_term(); report = {}
    INV = "(fun (x : Float) => 1 / (1 + Float.exp (-x)))"
    # ---- train.sas: validation chain, training chain, final_model_output
    for label, feat, refp, chain in [
        ("validation chain -> risk_scores_validation.csv", "judge/reference/model_features_validation.csv", "judge/reference/risk_scores_validation.csv",
         "risk_scores_validation_clean (risk_scores_validation (logit_scored_valid (logit_scored_valid_temp {m} {t})))"),
        ("training chain -> risk_scores_train.csv (invLink := 1/(1+exp(-x)))", "judge/reference/model_features_train.csv", "judge/reference/risk_scores_train.csv",
         "risk_scores_train_clean (risk_scores_train (logit_scored_train (logit_scored_train_output {m} " + INV + " {t})))"),
        ("training chain -> final_model_output.csv", "judge/reference/model_features_train.csv", "judge/reference/final_model_output.csv",
         "final_model_output (risk_scores_train (logit_scored_train (logit_scored_train_output {m} " + INV + " {t})))"),
    ]:
        feats = {r["row_id"]: r for r in csv.DictReader(open(feat))}
        ref = {r["row_id"]: r for r in csv.DictReader(open(refp))}
        ids = pick(ref, n, 5)
        mk = lambda ch: f"{ROWVIEW} ({chain.format(m=MODEL, t=lean_table([lean_row([(k, 'n', v) for k, v in feats[i].items()]) for i in ch]))})"
        got = run_chunks(mcp, M_SINK, M_DECL, mk, ids, 40)
        st = report.setdefault(label, dict(rows=len(ids), cells=0, diffs=[])); cmp_rows(got, [ref[i] for i in ids], st)
    # ---- predict.sas: real test set and the edge scenario
    for label, rawp, refdir in [("predict chain -> test_predictions.csv", "data/cs-test.csv", "judge/reference"),
                                ("predict chain, edge_predict scenario", "judge/scenarios/edge_predict/cs-test.csv", "judge/reference/scenarios/edge_predict")]:
        raw = FE.raw_rows(rawp, None); med = FE.med_term(FE.medians(raw))
        ref = {r["row_id"]: r for r in csv.DictReader(open(f"{refdir}/test_predictions.csv"))}
        kag = {r["row_id"]: r for r in csv.DictReader(open(f"{refdir}/kaggle_submission.csv"))}
        ids = pick(ref, n, 9)
        miss = [i for i in ref if ref[i]["pd_logistic"] in ("", ".")]
        ids = (random.sample(miss, min(len(miss), n // 4)) + ids)[:n]
        base = "test_predictions (test_scored (test_scored_temp {m} (test_features (test_imputed (fun t => t) (test_cleaned (test_raw_clean {t})) {med}))))"
        for sub, wrap, refd in [("", "test_predictions_full", ref), (" (kaggle_submission)", "kaggle_submission", kag)]:
            mk = lambda ch: f"{ROWVIEW} ({wrap} ({base.format(m=MODEL, med=med, t=lean_table([FE.raw_term(raw[i], test=True) for i in ch]))}))"
            got = run_chunks(mcp, P_SINK, P_DECL, mk, ids, 60)
            st = report.setdefault(label + sub, dict(rows=len(ids), cells=0, diffs=[])); cmp_rows(got, [refd[i] for i in ids], st)
            st["missing_pd_rows"] = sum(1 for i in ids if ref[i]["pd_logistic"] in ("", "."))
    for label, st in report.items():
        print(f"{label}: rows={st['rows']} cells={st['cells']} differences={len(st['diffs'])}" + (f" (rows with missing pd: {st['missing_pd_rows']})" if 'missing_pd_rows' in st else ""))
        kinds = collections.Counter(d[1] for d in st["diffs"] if d[0] != "COLUMNS")
        if kinds: print("   by column:", dict(kinds))
        for d in st["diffs"][:8]: print("   ", str(d)[:260])

if __name__ == "__main__":
    main()
