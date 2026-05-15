import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Current date
current_date = pd.Timestamp('2026-05-15')

# Bases (matching assessment schema: B01, B02)
bases = ['B01', 'B02']

# Aircraft types (short codes per assessment schema)
aircraft_types = ['C172', 'PA28', 'DA40', 'SR20']

# Registration codes
registrations = ['VT-ABC', 'VT-XYZ', 'VT-DEF', 'VT-GHI', 'VT-JKL', 'VT-MNO', 'VT-PQR', 'VT-STU']

# Lesson types
lesson_types = ['Navigation', 'Circuit', 'General Handling', 'Instrument Flying', 'Cross-Country']

# Cancellation reasons
cancel_reasons = ['Weather', 'Aircraft Defect', 'Maintenance', 'Instructor Unavailable', 'Cadet Illness']

# Subjects for TOGA study (per assessment)
subjects = ['Meteorology', 'Navigation', 'Air Regulations']

# Generate aircraft.csv (8 aircraft per assessment)
aircraft_data = []
for i in range(1, 9):
    aircraft_data.append({
        'aircraft_id': f'A{i:03d}',
        'registration': registrations[i-1] if i <= len(registrations) else f'VT-{100+i}',
        'type': aircraft_types[(i-1) % len(aircraft_types)],
        'base_id': bases[(i-1) % len(bases)],
        'total_available_hours': random.randint(150, 200),
        'maintenance_downtime_hours': random.randint(20, 80),
        'defect_count': random.randint(0, 10)
    })
aircraft_df = pd.DataFrame(aircraft_data)
aircraft_df.to_csv('data/aircraft.csv', index=False)

# Generate cadets.csv (30 cadets per assessment)
cadets_data = []
cadet_names = ['Arjun Menon', 'Meera Iyer', 'Rahul Nair', 'Priya Sharma', 'Amit Desai', 
               'Anjali Singh', 'Rohan Verma', 'Neha Patel', 'Vikram Kumar', 'Zara Khan',
               'Aditya Gupta', 'Simran Malhotra', 'Aryan Saxena', 'Diya Yadav', 'Karan Reddy',
               'Pooja Nambiar', 'Sanjay Iyer', 'Tanvi Chopra', 'Varun Pillai', 'Isha Bhat',
               'Ravi Kumar', 'Sneha Das', 'Nikhil Sharma', 'Shreya Kapoor', 'Arun Naidu',
               'Divya Sinha', 'Manish Rao', 'Geetika Sharma', 'Harshit Jain', 'Oindrila Roy']
for i in range(1, 31):
    enrollment_date = current_date - timedelta(days=random.randint(30, 365))
    courses = ['PPL', 'CPL']
    total_required = random.randint(40, 200)
    total_flown = random.randint(0, min(total_required, total_required + 5))  # Limited inconsistency
    cadets_data.append({
        'cadet_id': f'C{i:03d}',
        'name': cadet_names[i-1] if i <= len(cadet_names) else f'Cadet {i}',
        'course': random.choice(courses),
        'home_base': random.choice(bases),
        'total_required_hours': total_required,
        'total_flown_hours': total_flown,
        'enrollment_date': enrollment_date.date()
    })
cadets_df = pd.DataFrame(cadets_data)
cadets_df.to_csv('data/cadets.csv', index=False)

# Generate instructors.csv (10 instructors per assessment)
instructors_data = []
instructor_names = ['Capt Rao', 'Capt Menon', 'Capt Sharma', 'Capt Verma', 'Capt Singh',
                    'Capt Patel', 'Capt Kumar', 'Capt Desai', 'Capt Nair', 'Capt Iyer']
for i in range(1, 11):
    instructors_data.append({
        'instructor_id': f'I{i:03d}',
        'name': instructor_names[i-1] if i <= len(instructor_names) else f'Instructor {i}',
        'base_id': bases[min(i-1, len(bases)-1)],
        'aircraft_qualified': aircraft_types[(i-1) % len(aircraft_types)],
        'total_duty_hours': random.randint(100, 200),
        'total_flight_hours': random.randint(50, 150)
    })
instructors_df = pd.DataFrame(instructors_data)
instructors_df.to_csv('data/instructors.csv', index=False)

# Generate sorties.csv (200 sorties per assessment)
sorties_data = []
for i in range(1, 201):
    cadet_id = random.choice(cadets_df['cadet_id'].tolist())
    instructor_id = random.choice(instructors_df['instructor_id'].tolist())
    aircraft_id = random.choice(aircraft_df['aircraft_id'].tolist())
    base_id = random.choice(bases)
    scheduled_start = current_date - timedelta(days=random.randint(1, 180))
    duration = random.randint(1, 3)  # hours
    scheduled_end = scheduled_start + timedelta(hours=duration)

    status = random.choices(['completed', 'cancelled'], weights=[0.75, 0.25])[0]
    delay_minutes = 0
    cancel_reason = None
    actual_start = None
    actual_end = None

    if status == 'completed':
        delay_minutes = random.randint(-10, 60)  # Some intentional negatives for validation
        actual_start = scheduled_start + timedelta(minutes=max(0, delay_minutes))
        actual_end = actual_start + timedelta(hours=duration)
        # 5% of completed missing actual times (data quality issue)
        if random.random() < 0.05:
            actual_start = None
            actual_end = None
    elif status == 'cancelled':
        cancel_reason = random.choice(cancel_reasons)
        # 10% of cancelled have actual flight times (inconsistency)
        if random.random() < 0.1:
            actual_start = scheduled_start
            actual_end = scheduled_start + timedelta(hours=random.randint(0, duration))

    sorties_data.append({
        'sortie_id': f'S{i:03d}',
        'cadet_id': cadet_id,
        'instructor_id': instructor_id,
        'aircraft_id': aircraft_id,
        'base_id': base_id,
        'scheduled_start': scheduled_start,
        'scheduled_end': scheduled_end,
        'actual_start': actual_start,
        'actual_end': actual_end,
        'status': status,
        'delay_minutes': delay_minutes,
        'cancel_reason': cancel_reason,
        'lesson_type': random.choice(lesson_types)
    })
sorties_df = pd.DataFrame(sorties_data)
sorties_df.to_csv('data/sorties.csv', index=False)

# Generate toga_study.csv
toga_data = []
for cadet in cadets_df['cadet_id']:
    for subject in subjects:
        total_chapters = random.randint(20, 30)
        completed = random.randint(5, min(total_chapters + 1, total_chapters + 3))  # Small chance of exceeding 100%
        avg_score = random.randint(40, 100)
        last_active = current_date - timedelta(days=random.randint(1, 90))
        practice_tests = random.randint(0, 10)
        toga_data.append({
            'cadet_id': cadet,
            'subject': subject,
            'chapters_completed': completed,
            'total_chapters': total_chapters,
            'avg_quiz_score': avg_score,
            'last_active_date': last_active.date(),
            'practice_tests_attempted': practice_tests
        })
toga_df = pd.DataFrame(toga_data)
toga_df.to_csv('data/toga_study.csv', index=False)

# Generate payments.csv
payments_data = []
for cadet in cadets_df['cadet_id']:
    invoiced = random.randint(50000, 300000)
    paid_pct = random.choice([0.3, 0.5, 0.7, 0.8, 0.9, 1.0])
    paid = int(invoiced * paid_pct)
    outstanding = invoiced - paid
    last_payment = current_date - timedelta(days=random.randint(5, 180)) if paid > 0 else None
    payments_data.append({
        'cadet_id': cadet,
        'invoiced_amount': invoiced,
        'paid_amount': paid,
        'outstanding_amount': outstanding,
        'last_payment_date': last_payment.date() if last_payment else None
    })
payments_df = pd.DataFrame(payments_data)
payments_df.to_csv('data/payments.csv', index=False)

print("All datasets generated and saved to data/ folder.")