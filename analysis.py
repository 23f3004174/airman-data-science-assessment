import os
from datetime import timedelta
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Ensure output directories exist
os.makedirs('reports', exist_ok=True)
os.makedirs('charts', exist_ok=True)
os.makedirs('data', exist_ok=True)

ALLOWED_STATUSES = {'completed', 'cancelled', 'delayed'}


def load_data():
    sorties = pd.read_csv('data/sorties.csv', parse_dates=['scheduled_start', 'scheduled_end', 'actual_start', 'actual_end'])
    aircraft = pd.read_csv('data/aircraft.csv')
    cadets = pd.read_csv('data/cadets.csv', parse_dates=['enrollment_date'])
    instructors = pd.read_csv('data/instructors.csv')
    toga_study = pd.read_csv('data/toga_study.csv', parse_dates=['last_active_date'])
    payments = pd.read_csv('data/payments.csv', parse_dates=['last_payment_date'])
    return {
        'sorties': sorties,
        'aircraft': aircraft,
        'cadets': cadets,
        'instructors': instructors,
        'toga_study': toga_study,
        'payments': payments,
    }


def compute_actual_duration(df):
    actual = df[['actual_start', 'actual_end']].notna().all(axis=1)
    duration = (df.loc[actual, 'actual_end'] - df.loc[actual, 'actual_start']).dt.total_seconds() / 3600
    df.loc[actual, 'actual_duration_hours'] = duration
    df.loc[~actual, 'actual_duration_hours'] = np.nan
    return df


def validate_data(data):
    report = []
    sorties = data['sorties']
    aircraft = data['aircraft']
    cadets = data['cadets']
    instructors = data['instructors']
    toga_study = data['toga_study']
    payments = data['payments']

    def add(issue, subset, severity, correction, assumptions):
        report.append({
            'issue': issue,
            'affected_rows': int(len(subset)),
            'severity': severity,
            'correction_logic': correction,
            'assumptions': assumptions,
        })

    # Missing values
    for name, df in [('sorties', sorties), ('aircraft', aircraft), ('cadets', cadets), ('instructors', instructors), ('toga_study', toga_study), ('payments', payments)]:
        missing = df.isna().any(axis=1)
        if missing.any():
            add(
                issue=f'Missing values in {name}',
                subset=df[missing],
                severity='Medium',
                correction='Review and impute or flag missing fields; keep ledger rows for study and payment only if key identifiers are complete.',
                assumptions='Cadet and aircraft identifiers are required; missing optional dates or comments are accepted as operational gaps.'
            )

    # Duplicate IDs
    for name, column, df in [
        ('sorties', 'sortie_id', sorties),
        ('aircraft', 'aircraft_id', aircraft),
        ('cadets', 'cadet_id', cadets),
        ('instructors', 'instructor_id', instructors),
    ]:
        dup = df[df.duplicated(subset=[column], keep=False)]
        if len(dup) > 0:
            add(
                issue=f'Duplicate {column} in {name}',
                subset=dup,
                severity='High',
                correction='Remove duplicate records or consolidate duplicate identifiers before analysis.',
                assumptions='Identifiers must be unique to ensure accurate assignment of hours and risk scores.'
            )

    # Invalid status values
    invalid_status = sorties[~sorties['status'].isin(ALLOWED_STATUSES)]
    if len(invalid_status) > 0:
        add(
            issue='Invalid sortie status values',
            subset=invalid_status,
            severity='High',
            correction='Map invalid status values to known categories or exclude them from operational metrics.',
            assumptions='Only completed, cancelled, and delayed statuses are used in Skynet analytics.'
        )

    # Date validations
    bad_schedules = sorties[sorties['scheduled_end'] < sorties['scheduled_start']]
    if len(bad_schedules) > 0:
        add(
            issue='Invalid scheduled delivery windows',
            subset=bad_schedules,
            severity='High',
            correction='Correct scheduled end times to follow scheduled start times; inspect scheduling data ingestion.',
            assumptions='Sortie scheduling must preserve chronological order.'
        )
    bad_actual = sorties[sorties['actual_end'] < sorties['actual_start']]
    if len(bad_actual) > 0:
        add(
            issue='Invalid actual flight times',
            subset=bad_actual,
            severity='High',
            correction='Correct actual end times or flag incomplete flight logs for follow-up.',
            assumptions='Actual flight logs should preserve chronology if recorded.'
        )

    # Negative values
    negative_delay = sorties[sorties['delay_minutes'] < 0]
    if len(negative_delay) > 0:
        add(
            issue='Negative delay minutes',
            subset=negative_delay,
            severity='Medium',
            correction='Set negative delays to zero or interpret as early departures if confirmed.',
            assumptions='Delay minutes should be zero or positive unless early departure is explicitly documented.'
        )
    negative_payment = payments[(payments['invoiced_amount'] < 0) | (payments['paid_amount'] < 0) | (payments['outstanding_amount'] < 0)]
    if len(negative_payment) > 0:
        add(
            issue='Negative payment or outstanding amounts',
            subset=negative_payment,
            severity='High',
            correction='Review invoices and payments; negative balances likely come from data entry or refunds.',
            assumptions='Financial values must be non-negative for payment risk analytics.'
        )

    # Incorrect delay calculations
    valid_delay = sorties[sorties['actual_start'].notna() & sorties['scheduled_start'].notna()]
    computed_delay = ((valid_delay['actual_start'] - valid_delay['scheduled_start']).dt.total_seconds() / 60).round().astype('Int64')
    mismatch = valid_delay[valid_delay['delay_minutes'] != computed_delay]
    if len(mismatch) > 0:
        add(
            issue='Incorrect delay calculations in sorties',
            subset=mismatch,
            severity='Medium',
            correction='Recompute delay_minutes from scheduled and actual start times.',
            assumptions='Delay is the difference between actual and scheduled start, expressed in minutes.'
        )

    # Completed sorties missing actual times
    incomplete_completed = sorties[(sorties['status'] == 'completed') & (sorties[['actual_start', 'actual_end']].isna().any(axis=1))]
    if len(incomplete_completed) > 0:
        add(
            issue='Completed sorties missing actual times',
            subset=incomplete_completed,
            severity='High',
            correction='Confirm flight logs or reclassify record if the sortie was not actually completed.',
            assumptions='Completed flights require both actual start and actual end recorded.'
        )

    # Cancelled sorties with actual times
    cancelled_with_actual = sorties[(sorties['status'] == 'cancelled') & sorties[['actual_start', 'actual_end']].notna().any(axis=1)]
    if len(cancelled_with_actual) > 0:
        add(
            issue='Cancelled sorties recorded with actual flight times',
            subset=cancelled_with_actual,
            severity='Medium',
            correction='Review cancellation classification and remove actual times if the flight was not conducted.',
            assumptions='Cancelled sorties should not have actual flight timestamps unless the record is a partial or rebooked sortie.'
        )

    # Invalid payment calculations
    invalid_payment_calc = payments[payments['invoiced_amount'] != (payments['paid_amount'] + payments['outstanding_amount'])]
    if len(invalid_payment_calc) > 0:
        add(
            issue='Invalid payment reconciliation',
            subset=invalid_payment_calc,
            severity='High',
            correction='Align invoiced, paid, and outstanding amounts to ensure ledger consistency.',
            assumptions='Outstanding amount should equal invoiced minus paid for active cadets.'
        )

    # Study progress > 100%
    over_progress = toga_study[toga_study['chapters_completed'] > toga_study['total_chapters']]
    if len(over_progress) > 0:
        add(
            issue='Study progress exceeds 100%',
            subset=over_progress,
            severity='Medium',
            correction='Cap chapter completion at total chapters or verify subject completion data.',
            assumptions='Subject progress should not exceed 100% without explicit extra-credit justification.'
        )

    # Downtime > available hours
    downtime_issues = aircraft[aircraft['maintenance_downtime_hours'] > aircraft['total_available_hours']]
    if len(downtime_issues) > 0:
        add(
            issue='Aircraft downtime exceeds available hours',
            subset=downtime_issues,
            severity='High',
            correction='Verify maintenance logs and adjust total available hours or downtime entries.',
            assumptions='A single aircraft cannot be unavailable for more hours than its operating window.'
        )

    # Flown hours > required hours
    overflown = cadets[cadets['total_flown_hours'] > cadets['total_required_hours']]
    if len(overflown) > 0:
        add(
            issue='Cadet flown hours exceed required hours',
            subset=overflown,
            severity='Low',
            correction='Retain as planned overflight or normalize progress metrics above 100%.',
            assumptions='Some cadets may exceed required minimum hours during training due to practice or re-routes.'
        )

    return pd.DataFrame(report)


def enrich_sorties(sorties):
    sorties = compute_actual_duration(sorties.copy())
    sorties['delay_calculated'] = np.nan
    valid = sorties['scheduled_start'].notna() & sorties['actual_start'].notna()
    sorties.loc[valid, 'delay_calculated'] = ((sorties.loc[valid, 'actual_start'] - sorties.loc[valid, 'scheduled_start']).dt.total_seconds() / 60).round()
    return sorties


def compute_metrics(data):
    sorties = enrich_sorties(data['sorties'])
    aircraft = data['aircraft']
    cadets = data['cadets']
    instructors = data['instructors']
    toga_study = data['toga_study']
    payments = data['payments']

    # Operational metrics
    completed = sorties[sorties['status'] == 'completed']
    delayed = sorties[sorties['status'] == 'delayed']
    cancelled = sorties[sorties['status'] == 'cancelled']
    actual_flights = sorties[sorties['actual_duration_hours'].notna()]

    aircraft_hours = actual_flights.groupby('aircraft_id')['actual_duration_hours'].sum().reset_index()
    aircraft_util = aircraft_hours.merge(aircraft[['aircraft_id', 'registration', 'total_available_hours']], on='aircraft_id')
    # Safe utilization calculation
    aircraft_util['utilization_pct'] = np.where(
        aircraft_util['total_available_hours'] != 0,
        (aircraft_util['actual_duration_hours'] / aircraft_util['total_available_hours']) * 100,
        0
    )

    base_hours = actual_flights.groupby('base_id')['actual_duration_hours'].sum().reset_index()
    base_ship = actual_flights.groupby('base_id').size().reset_index(name='sorties_count')
    base_util = base_hours.merge(base_ship, on='base_id')

    instructor_hours = actual_flights.groupby('instructor_id')['actual_duration_hours'].sum().reset_index()
    instructor_util = instructor_hours.merge(instructors[['instructor_id', 'name', 'total_duty_hours']], on='instructor_id')
    # Safe utilization calculation
    instructor_util['utilization_pct'] = np.where(
        instructor_util['total_duty_hours'] != 0,
        (instructor_util['actual_duration_hours'] / instructor_util['total_duty_hours']) * 100,
        0
    )

    workload = instructor_util[['instructor_id', 'name', 'actual_duration_hours']].copy()
    workload['workload_category'] = pd.cut(workload['actual_duration_hours'], bins=[-1, 80, 110, 1000], labels=['Underloaded', 'Balanced', 'Overloaded'])
    underutilized_aircraft = aircraft_util[aircraft_util['utilization_pct'] < 50]

    maintenance_impact = aircraft.copy()
    # Safe maintenance downtime calculation
    maintenance_impact['downtime_pct'] = np.where(
        maintenance_impact['total_available_hours'] != 0,
        (maintenance_impact['maintenance_downtime_hours'] / maintenance_impact['total_available_hours']) * 100,
        0
    )

    dispatch_reliability = ((len(completed) + len(delayed)) / len(sorties)) * 100 if len(sorties) > 0 else 0
    completion_rate = (len(completed) / len(sorties)) * 100 if len(sorties) > 0 else 0
    cancellation_rate = (len(cancelled) / len(sorties)) * 100 if len(sorties) > 0 else 0
    average_delay = actual_flights['delay_minutes'].fillna(0).mean() if len(actual_flights) > 0 else 0
    
    # Safe handling for cancellation reasons (may be empty)
    if len(cancelled) > 0:
        # value_counts returns Series, reset_index creates DataFrame with cancel_reason and count columns
        top_cancellations = cancelled['cancel_reason'].value_counts().reset_index(name='count')
        # Rename explicitly: first column is the cancel_reason, second is count
        top_cancellations = top_cancellations.rename(columns={'cancel_reason': 'reason'})
        # Ensure count is numeric
        top_cancellations['count'] = pd.to_numeric(top_cancellations['count'], errors='coerce').fillna(0).astype(int)
        top_cancellations = top_cancellations[['reason', 'count']]
    else:
        top_cancellations = pd.DataFrame({'reason': ['No cancellations'], 'count': [0]})
    delay_lesson = actual_flights.groupby('lesson_type')['delay_minutes'].mean().reset_index().sort_values(by='delay_minutes', ascending=False)
    delay_base = actual_flights.groupby('base_id')['delay_minutes'].mean().reset_index().sort_values(by='delay_minutes', ascending=False)
    instructor_delay = actual_flights.groupby('instructor_id')['delay_minutes'].mean().reset_index().merge(instructors[['instructor_id', 'name']], on='instructor_id')

    # Training analytics with safe division
    cadets = cadets.copy()
    # Safe progress calculation
    cadets['progress_pct'] = np.where(
        cadets['total_required_hours'] != 0,
        (cadets['total_flown_hours'] / cadets['total_required_hours']) * 100,
        0
    )
    cadets['remaining_hours'] = cadets['total_required_hours'] - cadets['total_flown_hours']
    cadets['remaining_hours'] = cadets['remaining_hours'].apply(lambda x: max(x, 0))
    cadets['train_rate_hours_per_month'] = cadets.apply(
        lambda row: row['total_flown_hours'] / max((pd.Timestamp('2026-05-15') - row['enrollment_date']).days / 30, 1), axis=1)
    cadets_at_risk = cadets[cadets['progress_pct'] < 60].sort_values('progress_pct')

    lesson_risk = actual_flights.groupby('lesson_type').agg(
        avg_delay=('delay_minutes', 'mean'),
        cancellations=('status', lambda x: (x == 'cancelled').sum()),
        count=('sortie_id', 'count')
    ).reset_index().sort_values(by='avg_delay', ascending=False)

    instructor_bottleneck = actual_flights.groupby('instructor_id').agg(
        sortie_count=('sortie_id', 'count'),
        avg_delay=('delay_minutes', 'mean'),
        total_hours=('actual_duration_hours', 'sum')
    ).reset_index().merge(instructors[['instructor_id', 'name']], on='instructor_id')

    # TOGA intelligence with safe calculations
    toga = toga_study.copy()
    # Safe study progress calculation
    toga['progress_pct'] = np.where(
        toga['total_chapters'] != 0,
        (toga['chapters_completed'] / toga['total_chapters']) * 100,
        0
    )
    subject_progress = toga.groupby('subject').agg(
        avg_progress=('progress_pct', 'mean'),
        avg_quiz=('avg_quiz_score', 'mean')
    ).reset_index().sort_values(by='avg_progress')
    cadet_study = toga.groupby('cadet_id').agg(
        subject_count=('subject', 'count'),
        avg_quiz=('avg_quiz_score', 'mean'),
        avg_progress=('progress_pct', 'mean'),
        last_active=('last_active_date', 'max'),
        practice_tests=('practice_tests_attempted', 'sum')
    ).reset_index().merge(cadets[['cadet_id', 'name']], on='cadet_id')
    cadet_study['days_inactive'] = (pd.Timestamp('2026-05-15') - cadet_study['last_active']).dt.days
    cadet_study['inactivity_risk'] = pd.cut(cadet_study['days_inactive'], bins=[-1, 14, 30, 1000], labels=['Low', 'Medium', 'High'])
    
    # Safe study readiness calculation with division-by-zero protection
    max_practice_tests = max(cadet_study['practice_tests'].max(), 1)
    cadet_study['study_readiness'] = (
        cadet_study['avg_quiz'] * 0.35 +
        cadet_study['avg_progress'] * 0.45 +
        (cadet_study['practice_tests'] / max_practice_tests) * 20
    )
    cadet_study['study_readiness'] = cadet_study['study_readiness'].clip(0, 100)

    weak_subjects = toga[(toga['progress_pct'] < 70) | (toga['avg_quiz_score'] < 70)]
    weak_subjects = weak_subjects.groupby('cadet_id').apply(lambda df: ', '.join(sorted(df['subject'].unique()))).reset_index(name='weak_subjects')
    cadet_study = cadet_study.merge(weak_subjects, on='cadet_id', how='left')
    cadet_study['weak_subjects'] = cadet_study['weak_subjects'].fillna('None')

    # Finance analytics with safe division
    payments = payments.copy()

    # Safe percentage calculations
    payments['payment_completion_pct'] = np.where(
        payments['invoiced_amount'] > 0,
        (payments['paid_amount'] / payments['invoiced_amount']) * 100,
        0
    )

    payments['payment_risk_pct'] = np.where(
        payments['invoiced_amount'] > 0,
        (payments['outstanding_amount'] / payments['invoiced_amount']) * 100,
        0
    )

    # Merge cadet progress safely
    payments = payments.merge(
        cadets[['cadet_id', 'name', 'progress_pct']],
        on='cadet_id',
        how='left'
    )

    # Convert payment date safely
    payments['last_payment_date'] = pd.to_datetime(
        payments['last_payment_date'],
        errors='coerce'
    )

    # Days since last payment
    payments['days_since_payment'] = (
        pd.Timestamp.today() - payments['last_payment_date']
    ).dt.days.fillna(0)

    # Payment risk score
    payments['payment_risk_score'] = (
        (payments['payment_risk_pct'] * 0.6) +
        np.where(payments['days_since_payment'] > 45, 25, 0) +
        np.where(payments['progress_pct'] < 60, 15, 0)
    ).clip(0, 100)

    # Risk level classification
    payments['payment_risk_level'] = payments['payment_risk_score'].apply(
        lambda x: 'High'
        if x >= 70
        else ('Medium' if x >= 40 else 'Low')
    )

    # Training continuity relationship
    payments['training_continuity_risk'] = payments.apply(
        lambda row:
            'Training Delay Likely'
            if row['payment_risk_score'] >= 70 and row['progress_pct'] < 60
            else (
                'Needs Monitoring'
                if row['payment_risk_score'] >= 40
                else 'Stable'
            ),
        axis=1
    )

    # Revenue leakage indicators
    payments['revenue_leakage_flag'] = payments.apply(
        lambda row:
            'Potential Leakage'
            if (
                row['outstanding_amount'] > 100000 or
                row['days_since_payment'] > 60
            )
            else 'Normal',
        axis=1
    )

    # Risk reason generator
    def generate_reason(row):
        reasons = []

        if row['payment_risk_pct'] > 40:
            reasons.append('High outstanding')

        if row['days_since_payment'] > 45:
            reasons.append('Old last payment date')

        if row['progress_pct'] < 60:
            reasons.append('Slow training progress')

        if not reasons:
            return 'Low financial risk'

        return ' + '.join(reasons)

    payments['risk_reason'] = payments.apply(generate_reason, axis=1)

    # Overall outstanding amount
    outstanding_total = payments['outstanding_amount'].sum()

    # Final finance risk summary
    payment_risk_summary = payments[[
        'cadet_id',
        'name',
        'outstanding_amount',
        'payment_completion_pct',
        'payment_risk_pct',
        'payment_risk_score',
        'payment_risk_level',
        'training_continuity_risk',
        'revenue_leakage_flag',
        'risk_reason'
    ]].sort_values(
        by='payment_risk_score',
        ascending=False
    )

    # Display top high-risk cadets
    payment_risk_summary.head(10)

    # Cadet risk scoring
    cancellations_per_cadet = sorties[sorties['status'] == 'cancelled'].groupby('cadet_id').size().rename('cancel_count').reset_index()
    delay_per_cadet = actual_flights.groupby('cadet_id')['delay_minutes'].mean().rename('avg_delay').reset_index()
    cadet_risk = cadets[['cadet_id', 'name', 'progress_pct']].merge(cadet_study[['cadet_id', 'avg_quiz', 'avg_progress', 'days_inactive', 'study_readiness', 'weak_subjects']], on='cadet_id')
    cadet_risk = cadet_risk.merge(payments[['cadet_id', 'payment_risk_pct', 'outstanding_amount']], on='cadet_id')
    cadet_risk = cadet_risk.merge(cancellations_per_cadet, on='cadet_id', how='left').merge(delay_per_cadet, on='cadet_id', how='left')
    cadet_risk['cancel_count'] = cadet_risk['cancel_count'].fillna(0)
    cadet_risk['avg_delay'] = cadet_risk['avg_delay'].fillna(0)

    cadet_risk['flight_risk'] = np.where(cadet_risk['progress_pct'] < 60, (60 - cadet_risk['progress_pct']) * 0.8, 0)
    cadet_risk['study_risk'] = np.where(cadet_risk['avg_progress'] < 70, (70 - cadet_risk['avg_progress']) * 0.6, 0)
    cadet_risk['quiz_risk'] = np.where(cadet_risk['avg_quiz'] < 75, (75 - cadet_risk['avg_quiz']) * 0.55, 0)
    cadet_risk['inactivity_risk_score'] = np.where(cadet_risk['days_inactive'] > 14, (cadet_risk['days_inactive'] - 14) * 0.45, 0)
    cadet_risk['payment_risk_score'] = cadet_risk['payment_risk_pct'] * 0.4
    cadet_risk['cancel_risk_score'] = cadet_risk['cancel_count'] * 2.5
    cadet_risk['delay_risk_score'] = np.where(cadet_risk['avg_delay'] > 20, (cadet_risk['avg_delay'] - 20) * 0.3, 0)

    cadet_risk['risk_score'] = (
        cadet_risk['flight_risk'] * 0.27 +
        cadet_risk['study_risk'] * 0.18 +
        cadet_risk['quiz_risk'] * 0.2 +
        cadet_risk['inactivity_risk_score'] * 0.12 +
        cadet_risk['payment_risk_score'] * 0.13 +
        cadet_risk['cancel_risk_score'] * 0.06 +
        cadet_risk['delay_risk_score'] * 0.04
    )
    cadet_risk['risk_score'] = cadet_risk['risk_score'].clip(0, 100).round(1)
    cadet_risk['risk_level'] = pd.cut(cadet_risk['risk_score'], bins=[-1, 39, 69, 100], labels=['Low', 'Medium', 'High'])

    drivers = []
    for _, row in cadet_risk.iterrows():
        reasons = []
        if row['progress_pct'] < 60:
            reasons.append('Low flight progress')
        if row['avg_progress'] < 70:
            reasons.append('Weak study progress')
        if row['avg_quiz'] < 75:
            reasons.append('Below-target quiz score')
        if row['days_inactive'] > 30:
            reasons.append('Inactivity risk')
        if row['payment_risk_pct'] > 25:
            reasons.append('High outstanding payment')
        if row['cancel_count'] >= 2:
            reasons.append('Repeated cancellations')
        if row['avg_delay'] > 30:
            reasons.append('High average delay')
        drivers.append(', '.join(reasons) if reasons else 'No dominant risk driver')
    cadet_risk['top_risk_drivers'] = drivers

    metrics = {
        'aircraft_util': aircraft_util,
        'base_util': base_util,
        'instructor_util': instructor_util,
        'workload': workload,
        'underutilized_aircraft': underutilized_aircraft,
        'maintenance_impact': maintenance_impact,
        'dispatch_reliability': dispatch_reliability,
        'completion_rate': completion_rate,
        'cancellation_rate': cancellation_rate,
        'average_delay': average_delay,
        'top_cancellations': top_cancellations,
        'delay_lesson': delay_lesson,
        'delay_base': delay_base,
        'instructor_delay': instructor_delay,
        'cadets': cadets,
        'cadets_at_risk': cadets_at_risk,
        'lesson_risk': lesson_risk,
        'instructor_bottleneck': instructor_bottleneck,
        'subject_progress': subject_progress,
        'cadet_study': cadet_study,
        'payments': payments,
        'outstanding_total': outstanding_total,
        'payment_risk_summary': payment_risk_summary,
        'cadet_risk': cadet_risk,
    }
    return metrics


def save_risk_scores(cadet_risk):
    risk_export = cadet_risk[['cadet_id', 'name', 'risk_score', 'risk_level', 'top_risk_drivers']]
    risk_export.to_csv('data/risk_scores.csv', index=False)
    return risk_export


def create_charts(metrics):
    """Create Plotly visualizations with safe handling for empty data and missing dependencies."""
    aircraft_util = metrics['aircraft_util']
    top_cancellations = metrics['top_cancellations'].copy()
    cadets = metrics['cadets']
    cadet_study = metrics['cadet_study']
    payments = metrics['payments']
    cadet_risk = metrics['cadet_risk']

    try:
        # Ensure count column is numeric
        if 'count' in top_cancellations.columns:
            top_cancellations['count'] = pd.to_numeric(top_cancellations['count'], errors='coerce').fillna(0).astype(int)
        
        # Guard against empty datasets
        if len(aircraft_util) == 0:
            print("Warning: No aircraft utilization data to chart.")
        else:
            fig = px.bar(aircraft_util, x='registration', y='utilization_pct', title='Aircraft Utilization (%)', labels={'utilization_pct': 'Utilization (%)', 'registration': 'Aircraft Registration'})
            fig.update_layout(xaxis_tickangle=-45, yaxis=dict(range=[0, 120]))
            fig.write_image('charts/aircraft_utilization.png')

        if len(top_cancellations) > 0 and 'count' in top_cancellations.columns and top_cancellations['count'].sum() > 0:
            fig = px.pie(top_cancellations, values='count', names='reason', title='Cancellation Reasons')
            fig.write_image('charts/cancellation_reasons.png')
        else:
            print("Warning: No cancellation data to chart.")

        if len(cadets) > 0:
            fig = px.bar(cadets.sort_values('progress_pct'), x='name', y='progress_pct', title='Cadet Progress (%)', labels={'progress_pct': 'Progress (%)', 'name': 'Cadet Name'})
            fig.update_layout(xaxis_tickangle=-45)
            fig.write_image('charts/cadet_progress.png')

        if len(cadet_study) > 0:
            fig = px.bar(cadet_study.sort_values('study_readiness'), x='name', y='study_readiness', title='Study Readiness Score', labels={'study_readiness': 'Study Readiness', 'name': 'Cadet Name'})
            fig.update_layout(xaxis_tickangle=-45)
            fig.write_image('charts/study_readiness.png')

        if len(payments) > 0:
            fig = px.bar(payments.sort_values('payment_risk_pct', ascending=False), x='name', y='payment_risk_pct', title='Payment Risk (%)', labels={'payment_risk_pct': 'Payment Risk (%)', 'name': 'Cadet Name'})
            fig.update_layout(xaxis_tickangle=-45)
            fig.write_image('charts/payment_risk.png')

        if len(cadet_risk) > 0:
            fig = px.histogram(cadet_risk, x='risk_score', nbins=20, title='Cadet Risk Scores Distribution', labels={'risk_score': 'Risk Score'})
            fig.write_image('charts/cadet_risk_scores.png')

        if len(cadet_study) > 0:
            flight_vs_study = cadet_study.merge(metrics['cadets'][['cadet_id', 'progress_pct']], on='cadet_id')
            if len(flight_vs_study) > 0:
                fig = px.scatter(flight_vs_study, x='progress_pct', y='avg_progress', text='name', title='Flight vs Study Progress', labels={'progress_pct': 'Flight Progress (%)', 'avg_progress': 'Study Progress (%)'})
                fig.update_traces(textposition='top center')
                fig.write_image('charts/flight_vs_study_progress.png')
    except ValueError as e:
        if 'kaleido' in str(e):
            print("Warning: Kaleido not installed. Skipping PNG charts. Install with: pip install kaleido")
        else:
            raise


def generate_reports(data, metrics, validation_report, risk_export):
    sorties = data['sorties']
    aircraft = data['aircraft']
    cadets = data['cadets']
    instructors = data['instructors']
    toga_study = data['toga_study']
    payments = data['payments']

    with open('reports/data_quality_report.md', 'w', encoding='utf-8') as f:
        f.write('# Data Quality Report\n')
        f.write('This report documents validation checks run over the AIRMAN training datasets.\n\n')
        for _, row in validation_report.iterrows():
            f.write(f'## {row.issue}\n')
            f.write(f'- Affected rows: {row.affected_rows}\n')
            f.write(f'- Severity: {row.severity}\n')
            f.write(f'- Correction logic: {row.correction_logic}\n')
            f.write(f'- Assumptions: {row.assumptions}\n\n')

    with open('reports/skynet_operations_analysis.md', 'w', encoding='utf-8') as f:
        f.write('# Skynet Operations Analysis\n')
        f.write('Operational analytics for AIRMAN Skynet are derived from sortie execution, aircraft availability and instructor workload.\n\n')
        f.write(f'- Overall dispatch reliability: {metrics["dispatch_reliability"]:.1f}%\n')
        f.write(f'- Completion rate: {metrics["completion_rate"]:.1f}%\n')
        f.write(f'- Cancellation rate: {metrics["cancellation_rate"]:.1f}%\n')
        f.write(f'- Average operational delay: {metrics["average_delay"]:.1f} minutes\n')
        f.write('\n')
        f.write('## Aircraft Utilization\n')
        for _, row in metrics['aircraft_util'].sort_values('utilization_pct', ascending=False).iterrows():
            f.write(f'- {row.registration}: {row.utilization_pct:.1f}% utilization over available hours.\n')
        f.write('\n')
        f.write('## Maintenance Impact\n')
        for _, row in metrics['maintenance_impact'].sort_values('downtime_pct', ascending=False).iterrows():
            f.write(f'- {row.aircraft_id} has {row.downtime_pct:.1f}% downtime share, affecting dispatch availability.\n')
        f.write('\n')
        f.write('## Cancellation and Delay Patterns\n')
        cancellations_df = metrics['top_cancellations'].head(4)
        if len(cancellations_df) > 0 and 'reason' in cancellations_df.columns and 'count' in cancellations_df.columns:
            for _, row in cancellations_df.iterrows():
                f.write(f'- {row["reason"]}: {row["count"]} cancellations.\n')
        f.write('\n')
        f.write('## Base and Lesson Delay Trends\n')
        top_base_delay = metrics['delay_base'].head(3)
        for _, row in top_base_delay.iterrows():
            f.write(f'- {row.base_id} has the highest average delay at {row.delay_minutes:.1f} minutes.\n')
        top_lesson_delay = metrics['delay_lesson'].head(3)
        for _, row in top_lesson_delay.iterrows():
            f.write(f'- {row.lesson_type} shows average delay of {row.delay_minutes:.1f} minutes.\n')

    with open('reports/training_progress_analysis.md', 'w', encoding='utf-8') as f:
        f.write('# Training Progress Analysis\n')
        f.write('This review assesses cadet completion progress, flight pacing and training risk.\n\n')
        f.write(f'- {len(metrics["cadets_at_risk"])} cadets are below 60% flight progress and require targeted support.\n')
        f.write('## Cadet Progress Summary\n')
        for _, row in metrics['cadets'].sort_values('progress_pct').head(5).iterrows():
            f.write(f'- {row.name}: {row.progress_pct:.1f}% complete, {row.remaining_hours} hours remaining.\n')
        f.write('\n')
        f.write('## Lesson Types with the Highest Delays\n')
        for _, row in metrics['lesson_risk'].head(3).iterrows():
            f.write(f'- {row.lesson_type} average delay {row.avg_delay:.1f} minutes across {row.count} sorties.\n')
        f.write('\n')
        f.write('## Instructor Bottlenecks\n')
        top_instructors = metrics['instructor_bottleneck'].sort_values('total_hours', ascending=False).head(3)
        for _, row in top_instructors.iterrows():
            f.write(f'- {row.name}: {row.total_hours:.1f} flight hours, average delay {row.avg_delay:.1f} minutes.\n')

    with open('reports/toga_study_intelligence.md', 'w', encoding='utf-8') as f:
        f.write('# TOGA Study Intelligence\n')
        f.write('This report uses study progress and quiz outcomes to identify cadet readiness and intervention needs.\n\n')
        f.write('## Overall Study Health\n')
        for _, row in metrics['subject_progress'].head(4).iterrows():
            f.write(f'- {row.subject}: average progress {row.avg_progress:.1f}%, average quiz score {row.avg_quiz:.1f}%.\n')
        f.write('\n')
        f.write('## High-Risk Cadets for Study Inactivity\n')
        inactive = metrics['cadet_study'][metrics['cadet_study']['inactivity_risk'] == 'High']
        for _, row in inactive.iterrows():
            f.write(f'- {row.name}: last active {row.days_inactive} days ago, readiness score {row.study_readiness:.1f}.\n')
        f.write('\n')
        f.write('## Suggested Actions\n')
        f.write('- Prioritize cadets with low study readiness for structured TOGA coaching and peer review sessions.\n')
        f.write('- Use weak subject tags to assign personalized revision plans in Aerodynamics, Air Law or Navigation.\n')

    with open('reports/finance_risk_analysis.md', 'w', encoding='utf-8') as f:
        f.write('# Finance and Operational Risk Analysis\n')
        f.write('This report connects payment behavior to likely disruptions in training continuity.\n\n')
        f.write(f'- Total outstanding amount across active cadets: INR {metrics["outstanding_total"]:,}.\n')
        f.write(f'- Payment completion average: {metrics["payments"]["payment_completion_pct"].mean():.1f}%.\n')
        f.write('\n')
        f.write('## Top Payment Risk Cadets\n')
        for _, row in metrics['payment_risk_summary'].head(5).iterrows():
            f.write(f'- {row.name}: INR {row.outstanding_amount:,.0f} outstanding ({row.payment_risk_pct:.1f}%), Payment Risk: {row.payment_risk_level}, Training Continuity: {row.training_continuity_risk}.\n')
            f.write(f'  Risk Reason: {row.risk_reason}\n')
        f.write('\n')
        f.write('## Payment Risk Metrics\n')
        f.write(f'- Average payment completion rate: {metrics["payments"]["payment_completion_pct"].mean():.1f}%\n')
        f.write(f'- High-risk cadets (payment risk ≥ 70): {len(metrics["payment_risk_summary"][metrics["payment_risk_summary"]["payment_risk_level"] == "High"])}\n')
        f.write(f'- Medium-risk cadets (payment risk 40-69): {len(metrics["payment_risk_summary"][metrics["payment_risk_summary"]["payment_risk_level"] == "Medium"])}\n')
        f.write(f'- Cadets flagged for revenue leakage: {len(metrics["payment_risk_summary"][metrics["payment_risk_summary"]["revenue_leakage_flag"] == "Potential Leakage"])}\n')
        f.write('\n')
        f.write('## Training Continuity Insights\n')
        continuity_at_risk = metrics['payment_risk_summary'][metrics['payment_risk_summary']['training_continuity_risk'] == 'Training Delay Likely']
        if len(continuity_at_risk) > 0:
            f.write(f'- {len(continuity_at_risk)} cadets show signs of training delay likelihood due to payment and progress issues.\n')
        else:
            f.write('- No cadets show immediate training delay risk from payment or progress metrics.\n')
        f.write('- Training continuity risk is elevated when cadets have both high outstanding balances and low flight progress.\n')
        f.write('- Monitoring payment compliance and study engagement together improves prediction of training disruption.\n')

    with open('reports/methodology.md', 'w', encoding='utf-8') as f:
        f.write('# Methodology for Airman Cadet Risk Scoring\n')
        f.write('The risk score is an explainable, weighted aggregate of operational, study and financial risk factors.\n\n')
        f.write('## Feature weights\n')
        f.write('- Flight progress shortfall: 27%\n')
        f.write('- Study progress shortfall: 18%\n')
        f.write('- Quiz performance gap: 20%\n')
        f.write('- Inactivity: 12%\n')
        f.write('- Payment risk: 13%\n')
        f.write('- Cancellation frequency: 6%\n')
        f.write('- Average delay impact: 4%\n\n')
        f.write('## Formula\n')
        f.write('The cadet risk score is computed from scaled deviations from expected performance targets. Each feature is converted to a risk contribution and summed to a 0-100 scale.\n\n')
        f.write('## Assumptions\n')
        f.write('- Flight progress below 60% and study progress below 70% indicate operational risk.\n')
        f.write('- Payment outstanding above 25% of invoiced amount increases continuity risk.\n')
        f.write('- Repeated cancellations and high delays are leading indicators of training instability.\n\n')
        f.write('## Fairness and limitations\n')
        f.write('- This model does not use personal demographic data; it focuses on training and payment signals only.\n')
        f.write('- It is intentionally conservative to promote intervention rather than punitive action.\n')
        f.write('- Validation should include manual review of top-risk cadets and comparison to actual training outcomes.\n')

    with open('reports/executive_insights.md', 'w', encoding='utf-8') as f:
        f.write('# Executive Insights for AIRMAN Training Intelligence\n')
        f.write('This summary highlights the top operational, training and finance signals for Skynet and TOGA.\n\n')
        f.write('## Top Operational Insights\n')
        f.write(f'- Dispatch reliability is {metrics["dispatch_reliability"]:.1f}%, indicating most sorties are executed or delayed rather than cancelled.\n')
        f.write('- Several aircraft have utilization below 50%, suggesting a reserve capacity that can be optimized with better maintenance scheduling.\n')
        f.write('\n')
        f.write('## Training Insights\n')
        f.write(f'- {len(metrics["cadets_at_risk"])} cadets are under 60% flight completion and should be prioritized for additional simulator and cross-country blocks.\n')
        f.write('- Lesson types such as instrument flying and cross-country contribute the largest average delay.\n')
        f.write('\n')
        f.write('## TOGA Personalization Opportunities\n')
        f.write('- Weak subjects should drive personalized TOGA content bundles in Aerodynamics, Air Law and Navigation.\n')
        f.write('- Inactivity risk cadets should receive automated reminders and focused practice tests.\n')
        f.write('\n')
        f.write('## Finance Risks\n')
        f.write('- Total outstanding training fees are material and correlate with lower training progress for several cadets.\n')
        f.write('- High outstanding payment ratios alongside low completion progress are strong continuity risk signals.\n')
        f.write('\n')
        f.write('## Product Recommendations\n')
        f.write('- Use Skynet to monitor underutilized aircraft and redirect maintenance slots toward heavier bases.\n')
        f.write('- Use TOGA readiness scores to trigger coach interventions and personalized test packs.\n')
        f.write('\n')
        f.write('## Data Quality Concerns\n')
        if not validation_report.empty:
            f.write('- Several records require cleansing for delays, cancellations and study progress values.\n')
        else:
            f.write('- No major data quality concerns were detected in the current dataset.\n')
        f.write('\n')
        f.write('## Additional data to collect\n')
        f.write('- Weather impacts per sortie, flight instructor feedback scores, and simulation hours would improve risk models.\n')
        f.write('- Cadet wellbeing and attendance logs would support a richer training continuity view.\n')
        f.write('\n')
        f.write('## Final recommendation\n')
        f.write('- Prioritize the top 10% highest-risk cadets for immediate intervention, while using underutilized aircraft capacity to accelerate on-track trainees.\n')


def run():
    data = load_data()
    validation_report = validate_data(data)
    metrics = compute_metrics(data)
    risk_export = save_risk_scores(metrics['cadet_risk'])
    create_charts(metrics)
    generate_reports(data, metrics, validation_report, risk_export)
    print('Analysis complete. Reports, charts, and risk scores have been generated.')


if __name__ == '__main__':
    run()
