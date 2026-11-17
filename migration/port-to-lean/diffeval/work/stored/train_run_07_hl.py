    hl_table, hl_chisq, hl_df, hl_p = sas_compat.hosmer_lemeshow(
        fit_scored.get_column("default_flag"), fit_scored.get_column("pd_logistic")
    )
    printed_hl_partition = pl.DataFrame(
        {
            "Group": [str(v) for v in hl_table.get_column("Group").to_list()],
            "Total": [sas_compat.fmt_wd(v, 8, 0) for v in hl_table.get_column("Total").to_list()],
            "EventsObserved": [
                sas_compat.fmt_wd(v, 8, 0) for v in hl_table.get_column("EventsObserved").to_list()
            ],
            "EventsExpected": [
                sas_compat.fmt_wd(v, 8, 2) for v in hl_table.get_column("EventsExpected").to_list()
            ],
            "NoneventsObserved": [
                sas_compat.fmt_wd(v, 8, 0) for v in hl_table.get_column("NoneventsObserved").to_list()
            ],
            "NoneventsExpected": [
                sas_compat.fmt_wd(v, 8, 2) for v in hl_table.get_column("NoneventsExpected").to_list()
            ],
        }
    )
    if final_effects:
        sas_compat.write_sas_csv(printed_hl_partition, output_dir / "printed_hl_partition.csv", formats={})
    printed_hosmer_lemeshow = pl.DataFrame(
        {
            "ChiSq": [sas_compat.fmt_wd(hl_chisq, 10, 4)],
            "DF": [str(hl_df)],
            "ProbChiSq": [sas_compat.sas_pvalue(hl_p)],
            "NGroups": [str(hl_table.height)],
        }
    )
    if final_effects:
        sas_compat.write_sas_csv(
            printed_hosmer_lemeshow, output_dir / "printed_hosmer_lemeshow.csv", formats={}
        )
