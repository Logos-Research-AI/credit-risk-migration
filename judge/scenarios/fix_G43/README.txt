PSI floor (round 3, ruling G43): the share given to an empty bin is 0.5 / max(n_train, n_validation)
at full precision. 21 training rows (scores 610 to 810 in steps of 10), 3 validation rows (scores 605, 625,
715): eight of the ten bins are empty on the validation side. The floor is 0.5 / 21 = 0.0238095238...;
as an 8-character text it was 0.02381.
Expected PSI with the full-precision floor: 1.8973448869682932; with the floor 0.02381: 1.8973281774659636.
Run: metrics_calculation.sas with these stage inputs (printed_psi_calculation.csv has the components).
