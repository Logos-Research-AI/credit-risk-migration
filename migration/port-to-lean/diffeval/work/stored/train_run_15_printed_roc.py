    roc_cols = ["Area", "StdErr", "LowerArea", "UpperArea", "SomersD", "Gamma", "TauA"]
    printed_roc_train = pl.DataFrame(
        {
            "ROCModel": roc_train.get_column("ROCModel").to_list(),
            **{c: [sas_compat.sas_d8(v) for v in roc_train.get_column(c).to_list()] for c in roc_cols},
        }
    )
    sas_compat.write_sas_csv(printed_roc_train, output_dir / "printed_roc_train.csv", formats={})
    printed_roc_validation = pl.DataFrame(
        {
            "ROCModel": roc_valid.get_column("ROCModel").to_list(),
            **{c: [sas_compat.sas_d8(v) for v in roc_valid.get_column(c).to_list()] for c in roc_cols},
        }
    )
    if roc_valid_created:  # the judge's export of a table that does not exist writes no file
        sas_compat.write_sas_csv(
            printed_roc_validation, output_dir / "printed_roc_validation.csv", formats={}
        )
    sas_compat.write_sas_csv(confusion_matrix_train, output_dir / "printed_confusion_train.csv", formats={})
    sas_compat.write_sas_csv(confusion_matrix, output_dir / "printed_confusion_validation.csv", formats={})
