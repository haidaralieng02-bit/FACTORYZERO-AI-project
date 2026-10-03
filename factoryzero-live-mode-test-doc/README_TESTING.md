# FactoryZero AI — Corrected Live Mode Test Pack v2

## Purpose
This pack is specifically designed to test FactoryZero AI Live Mode with three
clearly separated machine conditions.

Machine ID: `MOTOR-REAL-001`
Machine Name: `Production Drive Motor 001`

## Test 1 — NORMAL 🟢
File: `01_MOTOR_REAL_001_NORMAL.csv`
Incident ID: `LIVE-NORMAL-001`

Expected:
- temperature comfortably below 80 °C
- vibration below 4.5 mm/s
- current below 27 A
- stable RPM
- no serious threshold breaches

## Test 2 — SLIGHT PROBLEM 🟡
File: `02_MOTOR_REAL_001_SLIGHT_PROBLEM.csv`
Incident ID: `LIVE-SLIGHT-002`

Expected:
- temperature approximately 70–77 °C
- vibration approximately 4.6–6.3 mm/s
- current approximately 27–30 A
- developing negative trends
- maintenance investigation / warning rather than critical condition

## Test 3 — SERIOUS PROBLEM 🔴
File: `03_MOTOR_REAL_001_SERIOUS_PROBLEM.csv`
Incident ID: `LIVE-SERIOUS-003`

Expected:
- temperature approximately 85–94 °C
- vibration approximately 8.2–11.2 mm/s
- current approximately 33–37 A
- declining RPM
- multiple clear threshold breaches
- serious/urgent maintenance attention

## Documents
Upload ALL files in `maintenance_documents/` for every test.

## Recommended testing order
1. NORMAL
2. SLIGHT PROBLEM
3. SERIOUS PROBLEM

After each run, check:
- Dashboard machine status
- Telemetry findings
- Hypotheses
- Evidence/citations
- Maintenance plan
- Production impact
- Verification
- Final Report

These datasets are synthetic and are for software testing only.
They are NOT real industrial measurements and must not be used for real operational decisions.
