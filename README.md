# Pathfinder AI — Personalized Career Content Generator

A responsive Flask and SQLite career-guidance application for students. It creates consistent professional content, suggested career paths, a skill-gap snapshot, a learning roadmap, and interview practice from a single student profile.

## Features

- Secure student registration and login with Werkzeug password hashing and session cookies.
- Editable academic, skill, interest, goal, domain, and optional resume-text profile.
- Gemini structured JSON generation using a server-side API key, with a working profile-specific demo mode when no key is configured.
- Dashboard, resume/LinkedIn/portfolio/interview formats, skill-gap chart and CSV, tracked roadmap progress, and PDF export.
- Input length limits, server-side validation, parameterized SQLite queries, CSRF checks on form submissions, and no API secret in browser code.

## Run locally

Use Python 3.10 or later.

### Windows PowerShell

```powershell
cd career-content-generator
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `.env` and set a random `FLASK_SECRET_KEY`. For Gemini-powered responses, add your `GEMINI_API_KEY`; leave it blank to use demo mode. Then run:

```powershell
python app.py
```

Open http://127.0.0.1:5000. Register an account, complete your profile, and choose **Generate my plan**.

If PowerShell prevents virtual-environment activation, run the interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

### macOS / Linux

```bash
cd career-content-generator
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
# Set FLASK_SECRET_KEY (and optionally GEMINI_API_KEY) in .env
python app.py
```

The SQLite database is created automatically at `database/career_generator.sqlite3` (override with `DATABASE_PATH`). The `.env` file is local configuration and must not be committed. Do not use the development secret or Flask debug server for a public deployment; set a strong secret, disable debug mode, and use a production WSGI server.

## Sample profile for testing

Register with any name/email and a password of at least eight characters. For a sample profile, use:

- Degree: B.Tech
- Branch: Computer Science
- Semester: Semester 5
- Interests: Data visualization, machine learning, solving real-world problems
- Technical skills: Python, SQL, Excel
- Programming languages: Python, Java
- Career goal: Become a data analyst and build useful insights from data
- Preferred domain: Data Science & Analytics
- Skill level: Beginner

Generating with no Gemini key uses demo mode and does not require external API access. With a configured key, the profile is sent to Google Gemini over HTTPS to create recommendations.

## Project layout

```text
career-content-generator/
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── database/
│   ├── __init__.py
│   └── db.py
├── services/
│   ├── __init__.py
│   ├── ai_service.py
│   ├── career_service.py
│   └── pdf_service.py
├── templates/
├── static/
│   ├── css/style.css
│   └── js/main.js
└── README.md
```

Chart.js is loaded from its public CDN on the skill analysis page. The remaining app features work without that chart asset. The Gemini key is only used by the Flask backend.
