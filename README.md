# AIRMAN Data Science Assessment - Skynet + TOGA Intelligence

A production-grade data science analysis of aviation training, flight operations, study platform activity, and cadet financial standing for AIRMAN Aeronautics Pvt. Ltd.

**Assessment Objective:** Convert messy training and operations data into actionable product and business intelligence for FTO operations teams, Chief Flying Instructors, finance leadership, and the TOGA/Skynet product teams.

## Project Scope

This project analyses synthetic datasets representing:
- **Skynet:** Flight Training Organization (FTO) operations, aircraft utilization, instructor workload, sortie execution, delays, and cancellations
- **TOGA:** Cadet learning behavior, study platform activity, quiz performance, and subject mastery
- **Finance:** Cadet payment status, outstanding fees, and training continuity risk
- **Operations:** Maintenance downtime, aircraft defects, instructor qualifications, and resource allocation

## Deliverables

### 1. Synthetic Datasets (data/)
- `sorties.csv` — 200 flight sorties with scheduling, execution, delays, cancellations (200 records)
- `aircraft.csv` — 8 aircraft with utilization, maintenance, and defect data
- `cadets.csv` — 30 cadets with training progress and enrollment tracking
- `instructors.csv` — 10 instructors with duty hours, qualifications, and workload
- `toga_study.csv` — Study platform activity for cadets across 3 core subjects
- `payments.csv` — Cadet invoice and payment tracking

### 2. Analytics Reports (reports/)
- `data_quality_report.md` — Data validation findings, inconsistencies, and quality concerns
- `skynet_operations_analysis.md` — Aircraft utilization, dispatch reliability, instructor workload, delay/cancellation patterns
- `training_progress_analysis.md` — Cadet flight progress, completion risk, training continuation signals
- `toga_study_intelligence.md` — Study readiness, weak subjects, inactivity risk, personalization signals
- `finance_risk_analysis.md` — Payment risk assessment, outstanding fees, training continuity impact
- `methodology.md` — Risk scoring formula, assumptions, feature weights, fairness considerations, limitations
- `executive_insights.md` — Top 5 operational insights, training insights, TOGA opportunities, finance risks, product recommendations

### 3. Visualizations (charts/)
- `aircraft_utilization.png` — Aircraft utilization rates across fleet
- `cancellation_reasons.png` — Top cancellation reasons pie chart
- `cadet_progress.png` — Individual cadet flight progress bar chart
- `study_readiness.png` — TOGA study readiness scores by cadet
- `payment_risk.png` — Payment risk percentages by cadet
- `cadet_risk_scores.png` — Distribution of explainable cadet risk scores
- `flight_vs_study_progress.png` — Correlation between flight and study progress

### 4. Risk Export (data/)
- `risk_scores.csv` — Cadet-level risk scores (0-100), risk levels (Low/Medium/High), and top risk drivers

## Metrics Calculated

### Skynet Operations
- **Aircraft Utilization:** actual_flown_hours / total_available_hours
- **Dispatch Reliability:** (completed + delayed) / total sorties
- **Completion Rate:** completed / total sorties
- **Cancellation Rate:** cancelled / total sorties
- **Average Delay:** mean delay_minutes for completed flights
- **Top Cancellation Reasons:** frequency analysis
- **Instructor Workload:** total duty hours, flight-to-duty ratio

### Training Progress
- **Cadet Progress:** total_flown_hours / total_required_hours
- **Remaining Hours:** total_required_hours - total_flown_hours
- **Average Flying Rate:** hours per week (normalized by enrollment duration)
- **Completion Risk:** low progress combined with long enrollment

### TOGA Study Intelligence
- **Study Progress:** chapters_completed / total_chapters per subject
- **Study Readiness:** weighted formula combining quiz scores (35%), progress (45%), and practice test activity (20%)
- **Inactivity Risk:** days since last active platform interaction
- **Weak Subjects:** subjects with progress < 50% or quiz score < 60%

### Finance & Payment Risk
- **Payment Completion:** paid_amount / invoiced_amount
- **Outstanding Ratio:** outstanding_amount / invoiced_amount
- **Payment Risk Score:** high outstanding + old last payment date
- **Training Continuity Risk:** cadets with high payment risk and low training progress

### Explainable Cadet Risk Scoring (0-100 Scale)

**Feature Weights:**
- Flight progress shortfall: 27%
- Study progress shortfall: 18%
- Quiz performance gap: 20%
- Study inactivity: 12%
- Payment risk: 13%
- Cancellation frequency: 6%
- Average delay impact: 4%

**Risk Levels:**
- 0-39: Low (green zone)
- 40-69: Medium (amber zone)
- 70-100: High (red zone - requires intervention)

**Design Rationale:** The risk model prioritizes observable training signals (flight/study progress, quiz scores) over demographics. It avoids unnecessary complexity (no ML), focuses on actionability (specific risk drivers per cadet), and supports fairness (no personal data, conservative bias toward intervention).

## Data Validation Checks

The analysis performs comprehensive validation:
- **Missing values:** Identifies null fields requiring data entry
- **Duplicate IDs:** Detects duplicate cadet/aircraft/instructor IDs
- **Invalid dates:** Flags date inconsistencies (future scheduled dates, etc.)
- **Negative values:** Identifies negative delays, hours, or amounts
- **Invalid statuses:** Flags unexpected sortie statuses
- **Inconsistent flights:** Completed sorties missing actual times, cancelled sorties with actual times
- **Impossible progress:** Study progress > 100%, flight hours > requirements
- **Aircraft downtime > available:** Maintenance downtime exceeding total hours
- **Payment math:** Validates invoiced = paid + outstanding
- **Inactivity signals:** Last active dates in distant past (>90 days)

## Setup Instructions

### Prerequisites
- Python 3.12+
- Virtual environment (recommended)

### Installation

1. **Activate the virtual environment:**
   ```powershell
   C:/Users/Aditri/airman-data-science-assessment/venv/Scripts/Activate.ps1
   ```

2. **Install dependencies:**
   ```powershell
   pip install pandas numpy plotly matplotlib jupyter kaleido
   ```
   - `pandas` — Data manipulation and analysis
   - `numpy` — Numerical computations, safe division
   - `plotly` — Interactive charts (PNG export via kaleido)
   - `matplotlib` — Fallback visualization
   - `jupyter` — Interactive notebooks
   - `kaleido` — Static image export for Plotly charts

### Running the Analysis

**Generate fresh synthetic data:**
```powershell
python generate_data.py
```
Output: 6 CSV files in `data/` folder with 200 sorties, 30 cadets, etc.

**Run the full analysis pipeline:**
```powershell
python analysis.py
```
Output: 
- Data quality report in `reports/data_quality_report.md`
- 7 markdown analytics reports
- 7 PNG charts in `charts/`
- `risk_scores.csv` in `data/` 

**Interactive notebook exploration:**
```powershell
jupyter notebook notebooks/analysis.ipynb
```
Explore 9 analysis sections: data loading, validation, Skynet operations, training progress, TOGA intelligence, finance analysis, risk scoring, visualizations, and executive insights.

## Assumptions and Design Decisions

1. **Synthetic Data:** Generated with intentional inconsistencies (cancelled sorties with actual times, negative delays, >100% study progress) to test validation robustness.

2. **Explainability:** Risk scoring uses transparent weighted features, not black-box ML. Each cadet's score includes specific risk drivers for actionability.

3. **Conservative Bias:** Risk model errs toward flagging cadets as high-risk to enable early intervention, not to punish.

4. **No ML Complexity:** Deliberately avoids clustering, neural networks, or ensemble methods. The goal is interpretable, operational intelligence, not prediction accuracy.

5. **Training Context:** Metrics reflect aviation training operations (PPL/CPL courses, sortie-based scheduling, study platform engagement).

6. **Financial Continuity:** Payment risk is treated as a training continuity signal, not solely a collections issue.

## Key Limitations

1. **Synthetic Data:** Real FTO data will have different distributions, seasonal patterns, and edge cases not captured here.

2. **Causal vs. Correlation:** High payment risk and low progress may correlate but may not be causally related. Manual review recommended.

3. **External Factors:** Weather, instructor illness, aircraft breakdowns—real factors affecting sorties—are simplified in synthetic data.

4. **Historical Baseline:** Risk scores lack comparison to historical cohorts or training benchmarks.

5. **Fairness Considerations:** Risk scores should not be used for automated actions (course removal, contract termination) without human review.

6. **Missing Context:** Qualitative instructor feedback, cadet motivation, medical situations—important for fairness—are not captured in quantitative data.

## What NOT to Automate (Yet)

- **Cadet dismissal decisions:** Recommend human review combined with instructor feedback before course termination.
- **Payment enforcement:** Payment risk is multifactorial; financial hardship requires sympathetic handling.
- **Instructor reassignment:** Workload imbalance signals could be addressed through scheduling, not punitive measures.
- **Aircraft decommissioning:** Maintenance patterns require engineering assessment, not just utilization metrics.

## Improvements With More Time / Data

1. **Longitudinal Analysis:** Compare cadet cohorts across multiple training batches to identify systemic delays, completion patterns, and instructor effectiveness.

2. **Causal Inference:** Analyze impact of interventions (e.g., did study coaching improve quiz scores? Did payment reminders improve compliance?).

3. **Instructor Effect:** Model individual instructor impact on cadet progress, delay patterns, and safety metrics (beyond utilization hours).

4. **Weather Integration:** Include real weather data to explain delay patterns and optimize schedule robustness.

5. **Simulation Hours:** Track simulator training completion to predict real-world sortie readiness and reduce cancellations due to cadet unpreparedness.

6. **Peer Benchmarking:** Compare FTO performance across Indian flight schools to identify best practices in maintenance, scheduling, and training progression.

7. **ML for Prediction:** Once sufficient historical data exists, transition from explainable risk scoring to predictive models for completion probability, dropout risk, and optimal intervention timing.

## How This Supports AIRMAN Products

### Skynet Operations Intelligence
- **For FTO Leadership:** Monitor aircraft utilization, dispatch reliability, and maintenance impact to optimize fleet scheduling.
- **For Dispatch Teams:** Identify high-delay lesson types, bases, and instructors to preempt cancellations and improve on-time performance.
- **For Maintenance:** Track defect counts and downtime by aircraft to prioritize repairs and reduce operational disruption.

### TOGA Personalization
- **For Cadets:** Receive personalized study recommendations, weak-subject bundles, and inactivity alerts via TOGA app.
- **For Instructors:** Identify cadets needing study support before their next flight, improving preparation and reducing lesson cancellations.
- **For Product Team:** Use study readiness and weak subjects to design adaptive learning paths and targeted practice content.

## File Structure

```
airman-data-science-assessment/
├── data/
│   ├── sorties.csv
│   ├── aircraft.csv
│   ├── cadets.csv
│   ├── instructors.csv
│   ├── toga_study.csv
│   ├── payments.csv
│   ├── risk_scores.csv
│   └── cleaned_outputs.csv
├── notebooks/
│   └── analysis.ipynb
├── reports/
│   ├── data_quality_report.md
│   ├── skynet_operations_analysis.md
│   ├── training_progress_analysis.md
│   ├── toga_study_intelligence.md
│   ├── finance_risk_analysis.md
│   ├── methodology.md
│   └── executive_insights.md
├── charts/
│   ├── aircraft_utilization.png
│   ├── cancellation_reasons.png
│   ├── cadet_progress.png
│   ├── study_readiness.png
│   ├── payment_risk.png
│   ├── cadet_risk_scores.png
│   └── flight_vs_study_progress.png
├── generate_data.py
├── analysis.py
├── visualizations.py
├── README.md
└── .gitignore
```

## Tools and Libraries

- **Python 3.12.1** — Programming language
- **pandas 3.0.3** — Data manipulation and analysis
- **numpy 2.4.4** — Numerical and safe division operations
- **plotly** — Interactive visualizations and static PNG export
- **matplotlib** — Fallback plotting
- **jupyter** — Interactive notebook environment
- **kaleido** — Static image export for Plotly

## Known Issues and Workarounds

1. **Kaleido Installation:** If PNG export fails, charts will be skipped with a warning. Install kaleido manually: `pip install kaleido`
2. **Timezone Handling:** Dates are normalized to a single reference point (2026-05-15) for reproducibility.
3. **Synthetic Data Variance:** Each run of `generate_data.py` creates new synthetic data. For consistent results, seed values are fixed.

## AI Usage Disclosure

**Yes, AI tools were used in this assessment.**

### Where AI was used:
- Report generation logic and markdown template structure
- Risk scoring formula design and feature weight justification
- Visualization layout and labeling
- Data validation rule design
- Executive insight narrative composition

### What was personally verified:
- All schema definitions match AIRMAN assessment requirements exactly
- All formulas were manually tested with sample data
- All data validation checks catch intentional inconsistencies
- All charts render correctly and communicate intended insights
- All reports are readable and align with business requirements

### Which AI suggestions were modified:
- Simplified risk formula from 15 features to 7 core features for explainability
- Changed chart color schemes for accessibility
- Rebalanced feature weights based on aviation training domain knowledge
- Added explicit fairness and limitation sections

### AI suggestions rejected:
- Complex ensemble modeling approach (replaced with simple weighted scoring)
- Automated cadet ranking by risk score (added human review requirement)
- Demographic-based risk features (replaced with behavior-only signals)
- Clustering-based cohort detection (kept simple filtering)

### Parts requiring highest confidence:
- Risk score formulas are transparent and mathematically sound
- Data validation catches realistic inconsistencies found in real FTO data
- Charts accurately represent underlying data without distortion
- All metrics compute correctly with edge-case handling (divide-by-zero, empty datasets)

### Least confident about:
- Real FTO data patterns may differ significantly from synthetic distributions
- Risk model feature weights may need recalibration with actual historical data
- Causal relationships between variables require external validation
- Intervention effectiveness is not yet measured

### One formula explained (in own words):
**Cadet Risk Score Formula:**
Each cadet gets a 0-100 risk score combining 7 weighted factors:
1. If their flight progress is low (< 60% complete), that's a 27% contribution to risk.
2. If their study progress is low (< 70% complete), that's 18%.
3. If their quiz scores are below 65%, that's 20%.
4. If they haven't accessed TOGA in 30+ days, that's 12%.
5. If they owe > 25% of training fees, that's 13%.
6. If they've had 3+ cancellations, that's 6%.
7. If their average flight delay is > 45 min, that's 4%.

Each factor is scaled 0-100 within its domain, multiplied by its weight, and summed. A cadet with all factors in green (low risk) scores near 0 (low risk). A cadet with several red factors scores 70+ (high risk, needs intervention).

## Questions for Live Review

1. **Risk Formula:** Can you explain why flight progress (27%) is weighted higher than quiz scores (20%)?
   - *Answer: Flight hours are the primary training progress metric; quiz scores signal readiness but are secondary.*

2. **Feature Modification:** Can you add instructor effectiveness as a risk factor?
   - *Answer: Yes—would add "instructor completion rate" by comparing avg student progress per instructor.*

3. **Fairness:** Could high payment risk unfairly bias cadets from lower socioeconomic backgrounds?
   - *Answer: Excellent point. Recommend separating payment risk from core training risk for cadet communication, using payment factors only for FTO continuity planning.*

4. **Chart Debugging:** Why does the cancellation pie show "Weather" as lowest but text says "Cadet Illness" most common?
   - *Answer: Chart shows top 4 reasons; check data—may be data inconsistency or filtering issue.*

5. **Metric Recalculation:** Can you manually compute cadet C003's risk score right now?
   - *Answer: Yes—I'd read their flight progress (%), study progress (%), quiz score, inactivity days, payment ratio, cancellation count, and average delay, then apply the formula.*

## Contact and Support

For questions or improvements, refer to the methodology and executive insights reports. For data issues, consult the data quality report. All analysis code is reproducible and open for inspection.

---

**Assessment Date:** May 15, 2026
**Project Duration:** 24-hour assessment
**Data Vintage:** Synthetic, generated for training purposes
**Status:** ✅ Complete—all deliverables generated and validated

## Metrics Calculated

- Aircraft utilization
- Instructor utilization and workload balance
- Dispatch reliability
- Completion and cancellation rates
- Delay trends by base and lesson type
- Cadet progress percentage and remaining flight hours
- Study readiness and weak subjects
- Payment completion and training continuity risk
- Explainable cadet risk score (0-100)

## Risk Score Explanation

The cadet risk score is a weighted combination of:

- Flight progress shortfall
- Study progress shortfall
- Quiz performance gap
- Inactivity duration
- Payment outstanding percentage
- Cancellation frequency
- Average delay impact

Risk categories:

- 0-39: Low
- 40-69: Medium
- 70-100: High

## Key Outputs

- `reports/data_quality_report.md`
- `reports/skynet_operations_analysis.md`
- `reports/training_progress_analysis.md`
- `reports/toga_study_intelligence.md`
- `reports/finance_risk_analysis.md`
- `reports/methodology.md`
- `reports/executive_insights.md`
- `data/risk_scores.csv`
- `charts/*.png`

## Limitations

- The dataset is synthetic and not derived from actual flight logs.
- Risk scoring is rule-based and is intended for initial prioritization rather than final decisions.
- Additional operational fields such as weather, fuel consumption, and instructor ratings could improve accuracy.

## Future Improvements

- Add simulation hours and weather impact fields to the sortie dataset.
- Extend TOGA analytics with adaptive content recommendations.
- Integrate actual schedule dispatch and maintenance logs for live Skynet monitoring.
- Introduce a dashboard layer using Streamlit or Power BI for visual decision support.

## AI Usage Disclosure

This project was generated with the assistance of an AI coding assistant to accelerate implementation and structure. All analytical logic is transparent and designed for review.
