# Methodology for Airman Cadet Risk Scoring
The risk score is an explainable, weighted aggregate of operational, study and financial risk factors.

## Feature weights
- Flight progress shortfall: 27%
- Study progress shortfall: 18%
- Quiz performance gap: 20%
- Inactivity: 12%
- Payment risk: 13%
- Cancellation frequency: 6%
- Average delay impact: 4%

## Formula
The cadet risk score is computed from scaled deviations from expected performance targets. Each feature is converted to a risk contribution and summed to a 0-100 scale.

## Assumptions
- Flight progress below 60% and study progress below 70% indicate operational risk.
- Payment outstanding above 25% of invoiced amount increases continuity risk.
- Repeated cancellations and high delays are leading indicators of training instability.

## Fairness and limitations
- This model does not use personal demographic data; it focuses on training and payment signals only.
- It is intentionally conservative to promote intervention rather than punitive action.
- Validation should include manual review of top-risk cadets and comparison to actual training outcomes.
