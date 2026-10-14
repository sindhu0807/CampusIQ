# CampusIQ — Student Performance Analytics Platform

CampusIQ is a Flask-based student performance analytics platform that
helps educational institutions understand student performance, identify
at-risk students, and provide data-driven recommendations.

## Features

- Student performance tracking
- Academic risk assessment
- Attendance and examination score analysis
- Performance score calculation
- Student risk classification
- Student segmentation
- Explainable risk assessments
- Personalized intervention recommendations
- Dashboard analytics
- Student data import using CSV
- Analysis history
- User authentication
- Automated unit testing

## Technology Stack

### Backend
- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- PyMySQL

### Frontend
- HTML
- CSS
- JavaScript
- Bootstrap (if included in the templates)

### Testing
- pytest

## Project Structure

```text
CampusIQ/
├── app.py
├── config.py
├── requirements.txt
├── .env
├── .env.example
├── README.md
│
├── agents/
│   ├── __init__.py
│   ├── agents.py
│   ├── explainability.py
│   └── interventions.py
│
├── analytics/
│   ├── __init__.py
│   ├── scoring.py
│   ├── risk.py
│   └── segmentation.py
│
├── database/
│   ├── __init__.py
│   ├── db.py
│   └── models.py
│
├── data/
│   ├── __init__.py
│   ├── generate_data.py
│   └── import_data.py
│
├── static/
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/
│
└── tests/
    ├── __init__.py
    ├── test_risk.py
    └── test_scoring.py