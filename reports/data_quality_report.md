# Data Quality Report
This report documents validation checks run over the AIRMAN training datasets.

## Missing values in sorties
- Affected rows: 198
- Severity: Medium
- Correction logic: Review and impute or flag missing fields; keep ledger rows for study and payment only if key identifiers are complete.
- Assumptions: Cadet and aircraft identifiers are required; missing optional dates or comments are accepted as operational gaps.

## Negative delay minutes
- Affected rows: 18
- Severity: Medium
- Correction logic: Set negative delays to zero or interpret as early departures if confirmed.
- Assumptions: Delay minutes should be zero or positive unless early departure is explicitly documented.

## Incorrect delay calculations in sorties
- Affected rows: 17
- Severity: Medium
- Correction logic: Recompute delay_minutes from scheduled and actual start times.
- Assumptions: Delay is the difference between actual and scheduled start, expressed in minutes.

## Completed sorties missing actual times
- Affected rows: 10
- Severity: High
- Correction logic: Confirm flight logs or reclassify record if the sortie was not actually completed.
- Assumptions: Completed flights require both actual start and actual end recorded.

## Cancelled sorties recorded with actual flight times
- Affected rows: 2
- Severity: Medium
- Correction logic: Review cancellation classification and remove actual times if the flight was not conducted.
- Assumptions: Cancelled sorties should not have actual flight timestamps unless the record is a partial or rebooked sortie.

## Study progress exceeds 100%
- Affected rows: 5
- Severity: Medium
- Correction logic: Cap chapter completion at total chapters or verify subject completion data.
- Assumptions: Subject progress should not exceed 100% without explicit extra-credit justification.

