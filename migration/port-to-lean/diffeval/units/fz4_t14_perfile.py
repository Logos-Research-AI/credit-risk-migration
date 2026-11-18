import sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fz4_t14_gen as g
import compare as cmp
fz, td = g.fz, g.td
a, n = int(sys.argv[1]), int(sys.argv[2])
t0 = (HERE.parent / "work" / "fz4_t14.in0.txt").read_text()
i = t0.index("(let X : List Nat")
call = ('train_run_14_final_and_summary (Tabular.Cell.str (some "TODAY")) (MC (s * 8 + 7)) (MET (s * 8 + 3) "train") '
        '(MET (s * 8 + 4) "valid") (RS (s * 8 + 5)) (RS (s * 8 + 6)) (ROC (s * 8 + 1) "Training Set" false) '
        '(ROC (s * 8 + 2) "Validation Set" false) (H s 9100 2 == 0)')
lean = t0[:i] + ("(let ONE2 := fun (s : Nat) => (let o := " + call + "; o.map (fun (p : String × Tabular.Table Float) => dg (tS p.1 ++ tA p.2))); "
                 f"(List.range' {a} {n}).map ONE2)")
out = []
for s in range(a, a + n):
    _, w, _ = td.run_slice("s14", g.env14(s))
    row = []
    for name, df in w:
        if "training_date" in df.columns:
            df = df.with_columns(training_date=g.pl.lit("TODAY", dtype=g.pl.String))
        row.append(cmp.digest(cmp.tok_str(name) + cmp.tokens(cmp.canon_table(df))))
    out.append(row)
    for name, df in w:
        print(s, name, df.shape, df.columns[:12])
(HERE.parent / "work" / "fz4_t14_pf.in.txt").write_text(lean)
print(out)
