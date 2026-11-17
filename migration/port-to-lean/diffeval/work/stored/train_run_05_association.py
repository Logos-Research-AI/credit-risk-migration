    assoc = sas_compat.association_table(
        fit_scored.get_column("default_flag"), fit_scored.get_column("pd_logistic")
    )
    printed_association = pl.DataFrame(
        {
            "Label1": ["Percent Concordant", "Percent Discordant", "Percent Tied", "Pairs"],
            "cValue1": [
                sas_compat.fmt_wd(assoc.concordant_pct, 9, 1),
                sas_compat.fmt_wd(assoc.discordant_pct, 9, 1),
                sas_compat.fmt_wd(assoc.tied_pct, 9, 1),
                str(assoc.pairs),
            ],
            "nValue1": [
                sas_compat.sas_d12_3(assoc.concordant_pct),
                sas_compat.sas_d12_3(assoc.discordant_pct),
                sas_compat.sas_d12_3(assoc.tied_pct),
                sas_compat.sas_d12_3(float(assoc.pairs)),
            ],
            "Label2": ["Somers' D", "Gamma", "Tau-a", "c"],
            "cValue2": [
                sas_compat.fmt_wd(assoc.somers_d, 5, 3),
                sas_compat.fmt_wd(assoc.gamma, 5, 3),
                sas_compat.fmt_wd(assoc.tau_a, 5, 3),
                sas_compat.fmt_wd(assoc.c, 5, 3),
            ],
            "nValue2": [
                sas_compat.sas_d12_3(assoc.somers_d),
                sas_compat.sas_d12_3(assoc.gamma),
                sas_compat.sas_d12_3(assoc.tau_a),
                sas_compat.sas_d12_3(assoc.c),
            ],
        }
    )
    # SAS makes no Association, Odds Ratios or Hosmer-Lemeshow table for a final model with the
    # intercept only (small-inputs.md (d)): the four files below are written when it has a variable
    if final_effects:
        sas_compat.write_sas_csv(printed_association, output_dir / "printed_association.csv", formats={})
