# Dream Education — Teacher Management Portal

A Django-based web application designed to support educational administration, student management, class scheduling, academic reporting, and integration with Google Sheets.

The project brings essential academic management workflows into a centralized web interface for teachers and administrators.

## Project Overview

Dream Education Teacher Portal is a Python/Django project developed to organize and streamline everyday education management activities.

The application includes teacher-facing and administrative interfaces, student records, scheduling functionality, and academic reporting features.

The V10 Clean release builds on the V9 user interface, adding subject-based student classification and customized PDF reports without redesigning the existing interface.

## Key Features

### Teacher and Administration Interfaces
- Teacher dashboard
- Administrative overview
- Login interface
- Student information and management forms

### Student Management
- Student records and details
- Student classification by type:
  - Math
  - Science
  - English
  - IELTS

### Scheduling and Academic Records
- Class scheduling calendar
- Student score entry
- Academic update forms

### PDF Reporting
- Customized PDF reports based on student type
- Dream Education logo included in generated reports

### Google Sheets Integration
- Google Sheets synchronization utilities
- Student type information included in synchronization
- Utilities for synchronizing schedules and student workbooks

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Python, Django |
| Frontend | HTML, CSS, Django Templates |
| Database | Django ORM |
| External Integration | Google Sheets |
| Reporting | PDF generation |
| Version Control | Git, GitHub |

## Project Structure

```text
teachers_portal/
├── config/
├── docs/
├── portal/
│   ├── management/
│   │   └── commands/
│   ├── migrations/
│   ├── utils/
│   └── models.py
├── static/
│   └── img/
├── templates/
│   ├── registration/
│   └── portal/
├── manage.py
├── requirements.txt
└── README.md
```

## Installation

### Prerequisites

- Python 3
- pip
- Git

### 1. Clone the repository

```bash
git clone https://github.com/ah2062001/Dream-Education.git
cd Dream-Education/teachers_portal
```

### 2. Create a virtual environment

For macOS or Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Apply database migrations

```bash
python manage.py migrate
```

### 5. Populate demonstration data (optional)

```bash
python manage.py seed_demo
```

Review the demonstration data command before running it.

### 6. Start the development server

```bash
python manage.py runserver
```

Open:

http://127.0.0.1:8000/

Additional configuration may be required depending on the Django settings and environment.

## Google Sheets Configuration

The project includes utilities for Google Sheets integration.

To configure the integration:

1. Obtain the appropriate Google service-account credentials.
2. Place the credentials in `credentials.json` alongside `manage.py`, as described in the V10 setup guide.
3. Configure access to the required spreadsheets.
4. Run the relevant synchronization utilities.

**Security:** Never commit real credentials, API keys, private student records, or production databases to GitHub.

## Version 10 Clean — Enhancements

The V10 Clean release introduces:

- Student Type dropdown with Math, Science, English, and IELTS
- Customized PDF reports depending on student type
- Dream Education logo in PDF reports
- Student type support in Google Sheets synchronization

The existing V9 user interface is retained.

## Future Improvements

Potential future development areas include:

- Expanded academic analytics and performance visualization
- Automated report generation
- Enhanced role-based access controls
- Deployment and continuous integration
- Automated testing

## Project Status

Development and portfolio documentation in progress.

## Author

**Ameer Hamza Hassan**

Electrical/Telecommunications Engineering | Computer Networks | Python & Backend Development

GitHub: https://github.com/ah2062001

## Disclaimer

This repository is intended to demonstrate the software architecture and development of an educational management application. Demonstration data should be fictional, and real student information and confidential credentials must not be published.
