"""x26: is ruling G54 enough? With MonthlyIncome and NumberOfDependents imported as NUMERIC
columns (no NA in them), does every value written in at most 12 characters come through
`input(MonthlyIncome, best32.)` / `input(NumberOfDependents, best32.)` unchanged?

One session of SAS OnDemand (profile oda_eu):
  TRAIN  the real feature_engineering.sas, whole (only its two path macros redirected), on a
         valid training file built here; then work.credit_raw (as PROC IMPORT delivered it) is
         compared with work.credit_raw_clean (after the two INPUT calls), stored doubles in hex.
  TEST   the statements of predict.sas, verbatim: the header copy and %import_test (lines from
         `%let test_lines = 0;` to the `%import_test` call) and the step `data
         work.test_raw_clean`, on a test file with the same values; work.test_raw compared with
         work.test_raw_clean. (predict.sas as a whole needs a fitted model; the statements
         between the import and test_raw_clean are the input check, which changes no table.)

Values (class in the map file x26_g54_12chars_values.csv, one line per row id):
  I<i>K<k>   i integer digits, k decimal digits, i + (k + 1 if k > 0) <= 12: every (i, k),
             random digits, the last decimal digit not 0
  Z<k>_<z>   0.00...0ddd: k decimal digits of which the first z are zeros (small values)
  EDGE       0, 999999999999, 10^n, 10^-n, all nines in every (i, k), 1 then zeros then 1
  P11        .ddddddddddd : eleven decimals written WITHOUT the leading zero (12 characters as
             written; 13 with the zero) - listed apart, see the report
  dependents: whole numbers of 1 to 12 digits and the edges
  six rows have a blank income or a blank dependents (the columns stay numeric)

The table of hex values is written by SAS to a CSV and downloaded; this script then compares
each stored double with Python's correctly rounded float of the text written in the file.

Usage (from migration/legacy-to-lean):
    uv run --with saspy python experiments/x26_g54_12chars_run.py
"""
import random
import re
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEGACY = HERE.parents[2] / "legacy"
NAME = "x26_g54_12chars"
H = (",SeriousDlqin2yrs,RevolvingUtilizationOfUnsecuredLines,age,NumberOfTime30-59DaysPastDueNotWorse,"
     "DebtRatio,MonthlyIncome,NumberOfOpenCreditLinesAndLoans,NumberOfTimes90DaysLate,"
     "NumberRealEstateLoansOrLines,NumberOfTime60-89DaysPastDueNotWorse,NumberOfDependents")
PER_CLASS = 120


def hexd(x: float) -> str:
    return struct.pack(">d", x).hex().upper()


def incomes(rng: random.Random) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []

    def digits(n: int, first_nonzero: bool = False, last_nonzero: bool = False) -> str:
        s = [str(rng.randint(0, 9)) for _ in range(n)]
        if n and first_nonzero:
            s[0] = str(rng.randint(1, 9))
        if n and last_nonzero:
            s[-1] = str(rng.randint(1, 9))
        return "".join(s)

    for i in range(1, 13):
        for k in range(0, 12):
            if i + (k + 1 if k else 0) > 12:
                continue
            cls = f"I{i}K{k}"
            for _ in range(PER_CLASS):
                ip = digits(i, first_nonzero=(i > 1))
                out.append((cls, ip + ("." + digits(k, last_nonzero=True) if k else "")))
            nines = "9" * i + ("." + "9" * k if k else "")
            out.append(("EDGE", nines))
            one = "1" + "0" * (i - 1)
            out.append(("EDGE", one + ("." + "0" * (k - 1) + "1" if k else "")))
    for k in range(1, 11):
        for z in range(0, k):
            for _ in range(20):
                out.append((f"Z{k}_{z}", "0." + "0" * z + digits(k - z, first_nonzero=True, last_nonzero=True)))
        out.append(("EDGE", "0." + "0" * (k - 1) + "1"))
        out.append(("EDGE", "0." + "9" * k))
    out += [("EDGE", t) for t in ("0", "1", "2500", "2499.9999999", "2499.999999", "999999999999",
                                  "100000000000", "0.0000000001", "0.0000000099", "0.1", "0.3",
                                  "99999999999.9", "9.9999999999", "1.0000000001", "123456789012",
                                  "12345678901.5", "0.5", "5400.1234567")]
    for _ in range(200):
        out.append(("P11", "." + digits(11, last_nonzero=True)))
    return out


def dependents(rng: random.Random) -> list[str]:
    out = ["0", "1", "2", "3", "10", "999999999999", "100000000000", "123456789012", "999999999998"]
    for n in range(1, 13):
        for _ in range(60):
            out.append(str(rng.randint(10 ** (n - 1) if n > 1 else 0, 10 ** n - 1)))
        out.append("9" * n)
        out.append("1" + "0" * (n - 1))
    return out


def build() -> tuple[list[str], list[str], list[tuple[int, str, str, str]]]:
    rng = random.Random(26)
    inc, dep = incomes(rng), dependents(rng)
    rows_train, rows_test, values = [H], [H], []
    for n, (cls, text) in enumerate(inc, start=1):
        d = dep[(n - 1) % len(dep)]
        t = text
        if n % 4000 == 7:
            t = ""            # blank income: the column stays numeric
        if n % 4000 == 11:
            d = ""            # blank dependents
        values.append((n, cls if t else "BLANK", t, d))
        y = 1 if n % 9 == 0 else 0
        rows_train.append(f"{n},{y},0.5,45,0,0.3,{t},5,0,1,0,{d}")
        rows_test.append(f"{n},,0.5,45,0,0.3,{t},5,0,1,0,{d}")
    return rows_train, rows_test, values


def redirect(src: str, data_dir: str, out_dir: str) -> str:
    src, n1 = re.subn(r"%let\s+data_path\s*=\s*[^;]*;", f"%let data_path = {data_dir};", src)
    src, n2 = re.subn(r"%let\s+output_path\s*=\s*[^;]*;", f"%let output_path = {out_dir};", src)
    assert n1 == 1 and n2 == 1
    return src


def compare_block(tag: str, raw: str, clean: str, out_csv: str) -> str:
    return f"""/* ================= X26 SUBMISSION {tag}_COMPARE ================= */
title "x26 {tag} work.{raw}";
proc contents data=work.{raw} varnum; run;
data work.x26_{tag};
    merge work.{raw}(keep=VAR1 MonthlyIncome NumberOfDependents
                     rename=(VAR1=id0 MonthlyIncome=inc0 NumberOfDependents=dep0))
          work.{clean}(keep=VAR1 MonthlyIncome NumberOfDependents);
    length ti td $1;
    ti = vtype(inc0); td = vtype(dep0);
    inc_changed = not (inc0 = MonthlyIncome);
    dep_changed = not (dep0 = NumberOfDependents);
    id_differs = not (id0 = VAR1);
    if inc_changed or dep_changed or id_differs then
        put "X26 {tag} CHANGED " id0= VAR1= "income before=" inc0 hex16. " after=" MonthlyIncome hex16.
            " (" inc0 best32. " -> " MonthlyIncome best32. ") dependents before=" dep0 hex16.
            " after=" NumberOfDependents hex16.;
run;
proc sql noprint;
    select count(*), sum(inc_changed), sum(dep_changed), sum(id_differs),
           sum(missing(inc0)), sum(missing(dep0)), min(ti), max(ti), min(td), max(td)
    into :n trimmed, :ni trimmed, :nd trimmed, :nid trimmed, :mi trimmed, :md trimmed,
         :ti1 trimmed, :ti2 trimmed, :td1 trimmed, :td2 trimmed
    from work.x26_{tag};
quit;
%put X26 {tag} SUMMARY rows=&n income_changed=&ni dependents_changed=&nd id_differs=&nid income_missing=&mi dependents_missing=&md income_type=&ti1.&ti2 dependents_type=&td1.&td2;
data _null_;
    set work.x26_{tag};
    file "{out_csv}" lrecl=200;
    if _n_ = 1 then put 'id,inc_raw,inc_clean,dep_raw,dep_clean';
    put id0 +(-1) ',' inc0 hex16. ',' MonthlyIncome hex16. ',' dep0 hex16. ',' NumberOfDependents hex16.;
run;
"""


def analyse(tag: str, values, hex_csv: Path) -> list[str]:
    exp = {n: (cls, t, d) for n, cls, t, d in values}
    lines, bad_raw, bad_clean, by_cls = [], [], [], {}
    for ln in hex_csv.read_text().splitlines()[1:]:
        i, ir, ic, dr, dc = [x.strip() for x in ln.split(",")]
        cls, t, d = exp[int(i)]
        ei = hexd(float(t)) if t else None
        ed = hexd(float(d)) if d else None
        c = by_cls.setdefault(cls.split("_")[0] if cls.startswith("Z") else cls, [0, 0, 0])
        c[0] += 1
        if (ei is None and ir.strip(". ") != "") or (ei is not None and ir != ei) or \
           (ed is None and dr.strip(". ") != "") or (ed is not None and dr != ed):
            bad_raw.append((i, cls, t, d, ir, dr))
            c[1] += 1
        if ir != ic or dr != dc:
            bad_clean.append((i, cls, t, d, ir, ic, dr, dc))
            c[2] += 1
    lines.append(f"X26 {tag} PYTHON rows={len(exp)} import_not_nearest_double={len(bad_raw)} changed_by_input={len(bad_clean)}")
    for cls in sorted(by_cls):
        n, a, b = by_cls[cls]
        if a or b:
            lines.append(f"X26 {tag} PYTHON class={cls} rows={n} import_not_nearest_double={a} changed_by_input={b}")
    for r in bad_raw[:15]:
        lines.append(f"X26 {tag} PYTHON import differs id={r[0]} class={r[1]} income=[{r[2]}] dependents=[{r[3]}] stored={r[4]} {r[5]}")
    for r in bad_clean[:40]:
        lines.append(f"X26 {tag} PYTHON changed id={r[0]} class={r[1]} income=[{r[2]}] {r[4]}->{r[5]} dependents=[{r[3]}] {r[6]}->{r[7]}")
    return lines


def main() -> int:
    import saspy
    train, test, values = build()
    (HERE / f"{NAME}_train.csv").write_text("\n".join(train) + "\n")
    (HERE / f"{NAME}_test.csv").write_text("\n".join(test) + "\n")
    (HERE / f"{NAME}_values.csv").write_text(
        "id,class,income_text,dependents_text\n" + "".join(f"{n},{c},{t},{d}\n" for n, c, t, d in values))
    sas = saspy.SASsession(cfgname="oda_eu", results="TEXT")
    header = (f"X26 RUN saspy={saspy.__version__} (uv run --with saspy, not pinned to the judge's) "
              f"python={sys.version.split()[0]} profile=oda_eu sasver={sas.sasver} rows={len(values)}\n")
    log, lst, progs = [header], [], []
    try:
        first = sas.submit("%put X26WORK=%sysfunc(pathname(work));")["LOG"]
        work = next(l.split("=", 1)[1].strip() for l in first.splitlines() if l.startswith("X26WORK="))
        d1, o1, d2 = f"{work}/x26_train_data", f"{work}/x26_train_out", f"{work}/x26_test_data"
        sas.submit(f'options dlcreatedir; libname _mk "{d1}"; libname _mk "{o1}"; libname _mk "{d2}"; libname _mk clear;'
                   f'ods listing gpath="{work}";')
        for local, remote in ((f"{NAME}_train.csv", f"{d1}/cs-training.csv"), (f"{NAME}_test.csv", f"{d2}/cs-test.csv")):
            res = sas.upload(str(HERE / local), remote, overwrite=True)
            if not res.get("Success"):
                raise RuntimeError(f"upload failed: {res}")
        progs.append("/* ================= X26 SUBMISSION TRAIN_SCRIPT (feature_engineering.sas, paths redirected) ================= */\n"
                     + redirect((LEGACY / "feature_engineering.sas").read_text(), d1, o1))
        progs.append("%put X26 TRAIN TOTALS columns_ok=&columns_ok bad_rows=&bad_rows duplicate_ids=&duplicate_ids known_incomes=&known_incomes;\n"
                     + compare_block("TRAIN", "credit_raw", "credit_raw_clean", f"{o1}/x26_train_hex.csv"))
        p = (LEGACY / "predict.sas").read_text()
        a = p.index("%let test_lines = 0;")
        b = p.index("%import_test\n", a) + len("%import_test\n")
        c = p.index("data work.test_raw_clean;")
        e = p.index("run;", c) + len("run;\n")
        progs.append("/* ================= X26 SUBMISSION TEST_STATEMENTS (predict.sas, verbatim) ================= */\n"
                     + f"%let data_path = {d2};\n"
                     + "/* predict.sas, from `%let test_lines = 0;` to the `%import_test` call */\n" + p[a:b]
                     + "/* predict.sas, the step test_raw_clean */\n" + p[c:e])
        progs.append(compare_block("TEST", "test_raw", "test_raw_clean", f"{o1}/x26_test_hex.csv"))
        (HERE / f"{NAME}.sas").write_text(
            "/* x26: generated by x26_g54_12chars_run.py; each SUBMISSION block is submitted on its own, in order,\n"
            "   in one session, after the two input files (x26_g54_12chars_train.csv, _test.csv) are uploaded. */\n"
            + "".join(progs))
        for prog in progs:
            res = sas.submit(prog)
            log.append(res["LOG"])
            lst.append(res["LST"])
        for f in ("x26_train_hex.csv", "x26_test_hex.csv"):
            res = sas.download(str(HERE / f"{NAME}_{f[4:]}"), f"{o1}/{f}")
            if not res.get("Success"):
                raise RuntimeError(f"download failed: {res}")
    finally:
        sas.endsas()
        tail = []
        for tag, f in (("TRAIN", "train_hex.csv"), ("TEST", "test_hex.csv")):
            pth = HERE / f"{NAME}_{f}"
            if pth.exists():
                tail += analyse(tag, values, pth)
        log.append("\n".join(tail) + "\n")
        (HERE / f"{NAME}.log").write_text("\n".join(log))
        (HERE / f"{NAME}.lst").write_text("\n".join(lst))
        for ln in "\n".join(log).splitlines():
            if ln.startswith(("X26", "ERROR")):
                print(ln[:260])
    return 0


if __name__ == "__main__":
    sys.exit(main())
