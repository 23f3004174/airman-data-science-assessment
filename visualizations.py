import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
import os

# Ensure charts directory exists
os.makedirs('charts', exist_ok=True)

# Load datasets
sorties = pd.read_csv('data/sorties.csv')
aircraft = pd.read_csv('data/aircraft.csv')
cadets = pd.read_csv('data/cadets.csv')
instructors = pd.read_csv('data/instructors.csv')
toga_study = pd.read_csv('data/toga_study.csv')
payments = pd.read_csv('data/payments.csv')
risk_scores = pd.read_csv('data/risk_scores.csv')

# 1. Aircraft Utilization
# Calculate utilization: actual flown hours / total available hours * 100
# First, merge sorties with aircraft to get flown hours
sorties['actual_duration'] = (pd.to_datetime(sorties['actual_end']) - pd.to_datetime(sorties['actual_start'])).dt.total_seconds() / 3600  # hours
aircraft_util = sorties.groupby('aircraft_id')['actual_duration'].sum().reset_index()
aircraft_util = aircraft_util.merge(aircraft[['aircraft_id', 'total_available_hours']], on='aircraft_id')
aircraft_util['utilization'] = (aircraft_util['actual_duration'] / aircraft_util['total_available_hours']) * 100
aircraft_util = aircraft_util.merge(aircraft[['aircraft_id', 'registration']], on='aircraft_id')

fig = px.bar(aircraft_util, x='registration', y='utilization', title='Aircraft Utilization (%)', labels={'utilization': 'Utilization (%)', 'registration': 'Aircraft Registration'})
fig.update_layout(xaxis_tickangle=-45)
fig.write_image('charts/aircraft_utilization.png')

# 2. Cancellation Reasons
cancel_reasons = sorties[sorties['status'] == 'cancelled']['cancel_reason'].value_counts().reset_index()
cancel_reasons.columns = ['reason', 'count']

fig = px.pie(cancel_reasons, values='count', names='reason', title='Cancellation Reasons')
fig.write_image('charts/cancellation_reasons.png')

# 3. Cadet Progress
cadets['progress'] = (cadets['total_flown_hours'] / cadets['total_required_hours']) * 100

fig = px.bar(cadets, x='name', y='progress', title='Cadet Progress (%)', labels={'progress': 'Progress (%)', 'name': 'Cadet Name'})
fig.update_layout(xaxis_tickangle=-45)
fig.write_image('charts/cadet_progress.png')

# 4. Study Readiness
# Assuming study readiness is avg_quiz_score or a calculated score
study_readiness = toga_study.groupby('cadet_id')['avg_quiz_score'].mean().reset_index()
study_readiness = study_readiness.merge(cadets[['cadet_id', 'name']], on='cadet_id')

fig = px.bar(study_readiness, x='name', y='avg_quiz_score', title='Study Readiness (Avg Quiz Score)', labels={'avg_quiz_score': 'Avg Quiz Score', 'name': 'Cadet Name'})
fig.update_layout(xaxis_tickangle=-45)
fig.write_image('charts/study_readiness.png')

# 5. Payment Risk
# Assuming payment risk is outstanding_amount / invoiced_amount * 100
payments['payment_risk'] = (payments['outstanding_amount'] / payments['invoiced_amount']) * 100
payments = payments.merge(cadets[['cadet_id', 'name']], on='cadet_id')

fig = px.bar(payments, x='name', y='payment_risk', title='Payment Risk (%)', labels={'payment_risk': 'Payment Risk (%)', 'name': 'Cadet Name'})
fig.update_layout(xaxis_tickangle=-45)
fig.write_image('charts/payment_risk.png')

# 6. Cadet Risk Scores
fig = px.histogram(risk_scores, x='risk_score', nbins=20, title='Cadet Risk Scores Distribution', labels={'risk_score': 'Risk Score'})
fig.write_image('charts/cadet_risk_scores.png')

# 7. Flight vs Study Progress
# Merge cadets with toga_study for average study progress
study_progress = toga_study.groupby('cadet_id').agg({'chapters_completed': 'sum', 'total_chapters': 'sum'}).reset_index()
study_progress['study_progress'] = (study_progress['chapters_completed'] / study_progress['total_chapters']) * 100
flight_study = cadets[['cadet_id', 'name', 'total_flown_hours', 'total_required_hours']].merge(study_progress[['cadet_id', 'study_progress']], on='cadet_id')
flight_study['flight_progress'] = (flight_study['total_flown_hours'] / flight_study['total_required_hours']) * 100

fig = px.scatter(flight_study, x='flight_progress', y='study_progress', text='name', title='Flight vs Study Progress', labels={'flight_progress': 'Flight Progress (%)', 'study_progress': 'Study Progress (%)'})
fig.update_traces(textposition='top center')
fig.write_image('charts/flight_vs_study_progress.png')

print("All charts saved to charts/ folder.")