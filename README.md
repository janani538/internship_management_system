# 🎓 AI-Powered Internship Management & Continuous Project Review System

A full-featured Python + Streamlit web platform designed for managing technical internship cohorts, tracking project milestones, delivering AI-powered task explanations, continuously reviewing intern GitHub repositories against rubrics, scheduling evaluations, and managing email notifications safely.

---

## 🌟 Key Features

1. **Excel Data Import & Export Hub**:
   - Ingest intern rosters and project requirements directly from Excel spreadsheets (`.xlsx`, `.xls`).
   - Automated schema validation with error feedback.
   - One-click **Sample Template Download** and **Demonstration Data Seeder**.
   - Export full cohort database (Interns, Tasks, Assignments, Reviews) back into Excel.

2. **Intern & Task Management**:
   - Complete CRUD directory for interns with search by name, code, domain, or mentor.
   - Task catalog with customizable requirement checklists and evaluation rubrics.
   - Lifecycle assignment tracking: `Assigned` ➔ `In Progress` ➔ `Submitted` ➔ `Under Review` ➔ `Completed` / `Needs Revision`.

3. **AI Task Assistant & Interactive Mentor**:
   - Explains complex technical tasks in plain, accessible English (ELI5).
   - Generates phased implementation roadmaps, recommended tech stacks, deliverables checklists, and tips to score an A+.
   - Interactive Q&A chat for interns to ask questions about code structure, libraries, and debugging.
   - Dual-tier support: Powered by Google Gemini / OpenAI when configured, or an intelligent built-in heuristic engine when operating offline.

4. **GitHub Submission Portal**:
   - Intern submission interface to submit repository URLs, branch names, and notes.
   - URL validation and automated submission tracking with SQLite persistence.

5. **Evidence-Based Repository Review & Grading**:
   - Connects to public GitHub repositories via GitHub REST API.
   - Gathers factual evidence: file counts, directory tree, README depth, dependency manifests (`requirements.txt`, `package.json`, etc.), test files, CI/CD workflows, and recent commit history.
   - Evaluates evidence against the specific task rubric and computes categorized scores:
     - **Requirement Coverage** (max 30 pts)
     - **Code Quality & Architecture** (max 25 pts)
     - **Documentation & Setup Instructions** (max 20 pts)
     - **Testing & Verification** (max 15 pts)
     - **Git & Project Hygiene** (max 10 pts)
   - Outputs letter grades (`A+`, `A`, `B`, `C`, `Needs Revision`), concrete strengths found, gaps/deficiencies, and actionable recommendations.

6. **Review Scheduler & History**:
   - Schedule milestone, mid-term, or final code reviews with date/time pickers and meeting links.
   - Complete historical audit log of all reviews and scorecards.
   - Update and finalize reviews with mentor remarks.

7. **Configurable Email Previews & Safe SMTP Dispatch**:
   - Generates responsive HTML and plain-text emails for:
     - Task Assignment Notifications
     - Review Scheduled Announcements
     - Evaluation Feedback & Scorecards
   - **Simulation Mode Active by Default (`EMAIL_SIMULATION_MODE=True`)**: Safely logs and previews email events in SQLite without transmitting live emails.
   - Supports live SMTP delivery (TLS/SSL) with user confirmation.

8. **Robust SQLite Persistence**:
   - Relational schema (`interns`, `tasks`, `intern_tasks`, `submissions`, `reviews`, `email_logs`) stored in `internship_system.db`.

9. **Security & Secrets Isolation**:
   - Zero hardcoded credentials. All API keys and SMTP passwords are read via `python-dotenv`.

---

## 🏗️ Architecture & File Structure

```
internship_management_system/
├── app.py                     # Streamlit application entry point & user interface
├── database.py                # SQLite schema, CRUD operations, transactions, and seeder
├── excel_handler.py           # Excel parser, validator, template generator, and exporter
├── github_analyzer.py         # GitHub API client, tree fetcher, and code inspector
├── ai_service.py              # LLM client (Gemini/OpenAI) + Heuristic evaluation engine
├── email_service.py           # Email templates (HTML/Text), safety simulation, & SMTP sender
├── test_system.py             # Comprehensive automated end-to-end test suite
├── requirements.txt           # Python package dependencies
├── .env.example               # Environment variables template
├── .env                       # Local secrets configuration (ignored in git)
├── .gitignore                 # Standard Python, virtualenv, and SQLite exclusions
├── sample_data/
│   ├── generate_sample.py     # Script to generate sample Excel workbook
│   └── sample_interns_tasks.xlsx # Pre-generated sample Excel workbook for immediate testing
└── README.md                  # Project documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- Python 3.10+ installed.

### 2. Environment Setup
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Automated Tests
```powershell
.\.venv\Scripts\python.exe test_system.py
```
This tests:
- Database initialization and sample seeding
- Intern and task CRUD operations
- Excel parsing, validation, and export
- AI Task Assistant and mentor chat
- GitHub URL parsing and live repo inspection
- Evidence-based grading and review storage
- Review scheduler and completion
- Email template rendering and safe simulation dispatch

### 4. Launch the Streamlit App
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```
Open your browser to `http://localhost:8501`.

---

## ⚙️ Configuration & Secrets (`.env`)

Copy `.env.example` to `.env`:

```ini
# Google Gemini API Key (Recommended for AI explanations & deep repo analysis)
# Get a free key at: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_gemini_key_here

# OpenAI API Key (Alternative)
# OPENAI_API_KEY=your_openai_key_here

# GitHub Token (Optional: Increases rate limit from 60 req/hr to 5,000 req/hr)
# GITHUB_TOKEN=ghp_your_token_here

# SMTP Configuration (Optional: By default, simulation mode prevents real emails)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_USE_TLS=True
SMTP_FROM_EMAIL=
EMAIL_SIMULATION_MODE=True
```

> **Note on AI Keys**: If no API key is provided, the application automatically uses its built-in **Heuristic Evaluation Engine**. It analyzes repository files, commit logs, test presence, and README content to generate factual, evidence-grounded scorecards out of the box!

> **Note on Email Sending**: The application defaults to `EMAIL_SIMULATION_MODE=True`. To prevent unintended emails, live SMTP dispatch only occurs when this flag is `False` **and** the user explicitly checks the confirmation checkbox in the UI.

---

## 🧪 Verification & Features Tested

All 9 requirements were thoroughly tested and verified:
1. `test_system.py` passed with 8/8 test phases with zero errors.
2. Verified live inspection on `octocat/Hello-World`.
3. Verified Streamlit server starts and responds with HTTP 200 on port 8501.
