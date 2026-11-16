"""x27: what train.sas writes when the validation part, or the training part, has one class.

Each case runs in a NEW session of SAS OnDemand (profile oda_eu), so no table of an earlier
case is in WORK: the real feature_engineering.sas, then the real train.sas (only the two path
macros redirected, as judge/run_sas.py does), then an observation block.

Rows: the first rows of legacy/data/cs-training.csv with the outcome column rewritten.
  SPLIT60  60 rows, outcomes as in the file: only to learn which row ids the split (seed 42)
           puts in the validation part (feature_engineering.sas only)
  A4       4 rows, outcomes 1,0,1,0: the validation part is one row
  B60      60 rows, defaulters in the training part only (validation: no defaulter)
  D60      60 rows, the validation part all defaulters, the training part mixed
  C60      60 rows, defaulters in the validation part only (training: one class)
  E60      60 rows, no defaulter at all

Usage (from migration/legacy-to-lean):
    uv run --with saspy python experiments/x27_one_class_roc_run.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LEGACY = HERE.parents[2] / "legacy"
NAME = "x27_one_class_roc"
TABLES = ["model_features_train", "model_features_validation", "logit_scored_train", "model_coefficients",
          "confusion_matrix_train", "training_metrics", "logit_scored_valid_temp", "logit_scored_valid",
          "confusion_matrix", "validation_metrics", "risk_scores_train", "risk_scores_validation",
          "roc_train", "roc_valid", "risk_scores_train_clean", "risk_scores_validation_clean",
          "final_model_output", "model_summary"]
FILES = ["risk_scores_train.csv", "risk_scores_validation.csv", "final_model_output.csv",
         "model_summary.csv", "model_coefficients.csv"]


def redirect(src: str, data_dir: str, out_dir: str) -> str:
    src, n1 = re.subn(r"%let\s+data_path\s*=\s*[^;]*;", f"%let data_path = {data_dir};", src)
    src, n2 = re.subn(r"%let\s+output_path\s*=\s*[^;]*;", f"%let output_path = {out_dir};", src)
    assert n2 == 1 and n1 <= 1
    return src


def base_rows(n: int) -> tuple[str, list[list[str]]]:
    lines = (LEGACY / "data" / "cs-training.csv").read_text().splitlines()
    return lines[0], [ln.split(",") for ln in lines[1:n + 1]]


def with_outcomes(header: str, rows: list[list[str]], y: dict[int, int]) -> list[str]:
    out = [header]
    for r in rows:
        r = list(r)
        r[1] = str(y[int(r[0])])
        out.append(",".join(r))
    return out


def observe(tag: str, out_dir: str) -> str:
    code = [f"/* ================= X27 SUBMISSION {tag}_OBSERVE ================= */\n",
            "%macro x27_tab(t);\n"
            "    %local dsid n nv;\n"
            "    %if %sysfunc(exist(work.&t)) %then %do;\n"
            "        %let dsid = %sysfunc(open(work.&t));\n"
            "        %let n = %sysfunc(attrn(&dsid, nlobs)); %let nv = %sysfunc(attrn(&dsid, nvars));\n"
            "        %let dsid = %sysfunc(close(&dsid));\n"
            f"        %put X27 {tag} TABLE &t exists rows=&n vars=&nv;\n"
            "    %end;\n"
            f"    %else %put X27 {tag} TABLE &t DOES NOT EXIST;\n"
            "%mend;\n"]
    code += [f"%x27_tab({t})\n" for t in TABLES]
    code.append("%macro x27_file(f);\n"
                f"    %if %sysfunc(fileexist({out_dir}/&f)) %then %do;\n"
                f"        data _null_; infile \"{out_dir}/&f\" lrecl=5000 obs=3 length=len; input;\n"
                "            l = len; t = substr(_infile_, 1, min(len, 600));\n"
                f"            put \"X27 {tag} FILE &f line \" _n_ \"len=\" l \"[\" t +(-1) \"]\"; length t $600; run;\n"
                "    %end;\n"
                f"    %else %put X27 {tag} FILE &f DOES NOT EXIST;\n"
                "%mend;\n")
    code += [f"%x27_file({f})\n" for f in FILES]
    code.append(f"""%macro x27_show;
    %if %sysfunc(exist(work.roc_train)) %then %do;
        title "x27 {tag} work.roc_train"; proc print data=work.roc_train; run;
        data _null_; set work.roc_train; put "X27 {tag} roc_train " ROCModel= "Area hex=" Area hex16. " " Area= best32.; run;
    %end;
    %if %sysfunc(exist(work.roc_valid)) %then %do;
        title "x27 {tag} work.roc_valid"; proc print data=work.roc_valid; run;
        data _null_; set work.roc_valid; put "X27 {tag} roc_valid " ROCModel= "Area hex=" Area hex16. " " Area= best32.; run;
    %end;
    %if %sysfunc(exist(work.model_summary)) %then %do;
        title "x27 {tag} work.model_summary"; proc contents data=work.model_summary varnum; run;
        proc print data=work.model_summary; run;
        data _null_; set work.model_summary;
            put "X27 {tag} model_summary " (_all_)(=);
            put "X27 {tag} model_summary Train_AUC hex=" Train_AUC hex16. " Valid_AUC hex=" Valid_AUC hex16.;
        run;
    %end;
    %if %sysfunc(exist(work.training_metrics)) %then %do;
        data _null_; set work.training_metrics; put "X27 {tag} training_metrics " (_all_)(=); run;
    %end;
    %if %sysfunc(exist(work.validation_metrics)) %then %do;
        data _null_; set work.validation_metrics; put "X27 {tag} validation_metrics " (_all_)(=); run;
    %end;
    %if %sysfunc(exist(work.risk_scores_train)) %then %do;
        data _null_; set work.risk_scores_train;
            put "X27 {tag} risk_scores_train " row_id= default_flag= "pd hex=" pd_logistic hex16. " " pd_logistic= best32.; run;
    %end;
    %if %sysfunc(exist(work.risk_scores_validation)) %then %do;
        data _null_; set work.risk_scores_validation;
            put "X27 {tag} risk_scores_validation " row_id= default_flag= "pd hex=" pd_logistic hex16. " " pd_logistic= best32.; run;
    %end;
    %if %sysfunc(exist(work.credit_validation)) %then %do;
        data _null_; set work.credit_validation; put "X27 {tag} credit_validation " row_id= default_flag=; run;
    %end;
    %if %sysfunc(exist(work.credit_train)) %then %do;
        data _null_; set work.credit_train; put "X27 {tag} credit_train " row_id= default_flag=; run;
    %end;
%mend;
%x27_show
""")
    return "".join(code)


def run_case(saspy, tag: str, lines: list[str], scripts: list[str]) -> tuple[str, str, str]:
    (HERE / f"{NAME}_{tag}.csv").write_text("\n".join(lines) + "\n")
    sas = saspy.SASsession(cfgname="oda_eu", results="TEXT")
    log, lst, progs = [], [], []
    try:
        first = sas.submit("%put X27WORK=%sysfunc(pathname(work));")["LOG"]
        work = next(l.split("=", 1)[1].strip() for l in first.splitlines() if l.startswith("X27WORK="))
        d, o = f"{work}/x27_data", f"{work}/x27_out"
        sas.submit(f'options dlcreatedir; libname _mk "{d}"; libname _mk "{o}"; libname _mk clear;'
                   f'ods listing gpath="{work}";')
        res = sas.upload(str(HERE / f"{NAME}_{tag}.csv"), f"{d}/cs-training.csv", overwrite=True)
        if not res.get("Success"):
            raise RuntimeError(f"upload failed: {res}")
        for s in scripts:
            progs.append(f"/* ================= X27 SUBMISSION {tag}_{s} (paths redirected) ================= */\n"
                         + redirect((LEGACY / s).read_text(), d, o))
        progs.append(observe(tag, o))
        for p in progs:
            res = sas.submit(p)
            log.append(res["LOG"])
            lst.append(res["LST"])
        if "train.sas" in scripts:
            r = sas.download(str(HERE / f"{NAME}_{tag}_model_summary.csv"), f"{o}/model_summary.csv")
            log.append(f"X27 {tag} DOWNLOAD model_summary.csv success={r.get('Success')}\n")
    finally:
        sas.endsas()
    return "".join(progs), "\n".join(log), "\n".join(lst)


def main() -> int:
    import saspy
    header, rows60 = base_rows(60)
    y_file = {int(r[0]): int(r[1]) for r in rows60}
    both = ["feature_engineering.sas", "train.sas"]
    sas_all, log_all, lst_all = [], [f"X27 RUN saspy={saspy.__version__} (uv run --with saspy, not pinned to the judge's) "
                                     f"python={sys.version.split()[0]} profile=oda_eu; one new session per case\n"], []

    def keep(res):
        sas_all.append(res[0]); log_all.append(res[1]); lst_all.append(res[2])

    try:
        res = run_case(saspy, "SPLIT60", with_outcomes(header, rows60, y_file), ["feature_engineering.sas"])
        keep(res)
        valid_ids = sorted(int(m) for m in re.findall(r"^X27 SPLIT60 credit_validation row_id=(\d+)", res[1], re.M))
        train_ids = sorted(set(y_file) - set(valid_ids))
        log_all.append(f"X27 SPLIT60 validation ids ({len(valid_ids)}): {valid_ids}\n")
        if len(valid_ids) != 18:
            raise RuntimeError(f"unexpected split: {valid_ids}")
        header4, rows4 = base_rows(4)
        keep(run_case(saspy, "A4", with_outcomes(header4, rows4, {1: 1, 2: 0, 3: 1, 4: 0}), both))
        mixed_train = {i: (1 if k % 4 == 0 else 0) for k, i in enumerate(train_ids)}
        keep(run_case(saspy, "B60", with_outcomes(header, rows60, {**mixed_train, **{i: 0 for i in valid_ids}}), both))
        keep(run_case(saspy, "D60", with_outcomes(header, rows60, {**mixed_train, **{i: 1 for i in valid_ids}}), both))
        mixed_valid = {i: (1 if k % 3 == 0 else 0) for k, i in enumerate(valid_ids)}
        keep(run_case(saspy, "C60", with_outcomes(header, rows60, {**{i: 0 for i in train_ids}, **mixed_valid}), both))
        keep(run_case(saspy, "E60", with_outcomes(header, rows60, {i: 0 for i in y_file}), both))
    finally:
        (HERE / f"{NAME}.sas").write_text(
            "/* x27: generated by x27_one_class_roc_run.py; one new session per case; each SUBMISSION block is\n"
            "   submitted on its own, in order, after the case's input file is uploaded as cs-training.csv. */\n"
            + "".join(sas_all))
        (HERE / f"{NAME}.log").write_text("\n".join(log_all))
        (HERE / f"{NAME}.lst").write_text("\n".join(lst_all))
        for ln in "\n".join(log_all).splitlines():
            if ln.startswith("X27") and " credit_train " not in ln and " risk_scores_train " not in ln:
                print(ln[:330])
            elif ln.startswith("ERROR"):
                print("   ", ln[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
