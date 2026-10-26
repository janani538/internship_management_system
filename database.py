"""
Database Module for AI-Powered Internship Management System
Handles SQLite schema creation, data access, transactions, and KPI queries.
"""

import os
import sqlite3
import json
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

DEFAULT_DB_PATH = os.getenv("DATABASE_PATH", "internship_system.db")


def get_db_path() -> str:
    """Get the current database path from environment or default."""
    return os.getenv("DATABASE_PATH", DEFAULT_DB_PATH)


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """Establish a thread-safe connection to SQLite with row dictionary factory."""
    path = db_path or get_db_path()
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """Create all necessary tables and indexes if they do not exist."""
    path = db_path or get_db_path()
    conn = get_connection(path)
    cur = conn.cursor()

    # 1. Interns Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS interns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        intern_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        department TEXT,
        domain TEXT,
        mentor TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Tasks Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        domain TEXT,
        description TEXT,
        requirements TEXT,
        rubric TEXT,
        deadline_days INTEGER DEFAULT 14,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 3. Intern Tasks (Assignments)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS intern_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        intern_id INTEGER NOT NULL REFERENCES interns(id) ON DELETE CASCADE,
        task_id INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
        status TEXT DEFAULT 'Assigned',
        assigned_date DATE,
        due_date DATE,
        completion_date DATE,
        notes TEXT,
        UNIQUE(intern_id, task_id)
    );
    """)

    # 4. Submissions Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        intern_task_id INTEGER NOT NULL REFERENCES intern_tasks(id) ON DELETE CASCADE,
        github_url TEXT NOT NULL,
        branch TEXT DEFAULT 'main',
        commit_hash TEXT,
        notes TEXT,
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'Submitted'
    );
    """)

    # 5. Reviews Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        submission_id INTEGER REFERENCES submissions(id) ON DELETE SET NULL,
        intern_task_id INTEGER NOT NULL REFERENCES intern_tasks(id) ON DELETE CASCADE,
        reviewer TEXT NOT NULL,
        review_type TEXT DEFAULT 'Milestone Review',
        scheduled_at TIMESTAMP,
        completed_at TIMESTAMP,
        score REAL,
        grade TEXT,
        status TEXT DEFAULT 'Scheduled',
        feedback TEXT,
        ai_analysis_json TEXT,
        meeting_link TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 6. Email Logs Table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS email_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient TEXT NOT NULL,
        subject TEXT NOT NULL,
        template_type TEXT,
        body_preview TEXT,
        status TEXT,
        simulated INTEGER DEFAULT 1,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Helpful Indexes
    cur.execute("CREATE INDEX IF NOT EXISTS idx_intern_code ON interns(intern_code);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_task_code ON tasks(task_code);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_intern_task_status ON intern_tasks(status);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_submissions_task ON submissions(intern_task_id);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_reviews_task ON reviews(intern_task_id);")

    conn.commit()
    conn.close()


# -------------------------------------------------------------
# Intern CRUD Operations
# -------------------------------------------------------------

def add_intern(intern_code: str, name: str, email: str, department: str = "", domain: str = "", mentor: str = "") -> int:
    """Add a new intern or update if code exists."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO interns (intern_code, name, email, department, domain, mentor)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(intern_code) DO UPDATE SET
            name = excluded.name,
            email = excluded.email,
            department = excluded.department,
            domain = excluded.domain,
            mentor = excluded.mentor;
    """, (intern_code.strip(), name.strip(), email.strip(), department.strip(), domain.strip(), mentor.strip()))
    conn.commit()
    intern_id = cur.lastrowid
    conn.close()
    return intern_id


def get_all_interns() -> List[Dict[str, Any]]:
    """Retrieve all interns with assigned tasks counts."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT i.*, 
               COUNT(it.id) as assigned_tasks_count,
               SUM(CASE WHEN it.status = 'Completed' THEN 1 ELSE 0 END) as completed_tasks_count
        FROM interns i
        LEFT JOIN intern_tasks it ON i.id = it.intern_id
        GROUP BY i.id
        ORDER BY i.intern_code ASC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_intern_by_id(intern_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single intern by id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM interns WHERE id = ?", (intern_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_intern(intern_id: int, name: str, email: str, department: str, domain: str, mentor: str) -> None:
    """Update intern details."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE interns 
        SET name = ?, email = ?, department = ?, domain = ?, mentor = ?
        WHERE id = ?
    """, (name, email, department, domain, mentor, intern_id))
    conn.commit()
    conn.close()


def delete_intern(intern_id: int) -> None:
    """Delete an intern and cascaded records."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM interns WHERE id = ?", (intern_id,))
    conn.commit()
    conn.close()


# -------------------------------------------------------------
# Task CRUD Operations
# -------------------------------------------------------------

def add_task(task_code: str, title: str, domain: str, description: str, requirements: str, rubric: str, deadline_days: int = 14) -> int:
    """Add a new task or update if code exists."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO tasks (task_code, title, domain, description, requirements, rubric, deadline_days)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(task_code) DO UPDATE SET
            title = excluded.title,
            domain = excluded.domain,
            description = excluded.description,
            requirements = excluded.requirements,
            rubric = excluded.rubric,
            deadline_days = excluded.deadline_days;
    """, (task_code.strip(), title.strip(), domain.strip(), description.strip(), requirements.strip(), rubric.strip(), int(deadline_days)))
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return task_id


def get_all_tasks() -> List[Dict[str, Any]]:
    """Retrieve all tasks."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.*, COUNT(it.id) as assigned_count
        FROM tasks t
        LEFT JOIN intern_tasks it ON t.id = it.task_id
        GROUP BY t.id
        ORDER BY t.task_code ASC
    """)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_task_by_id(task_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve a single task by ID."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_task(task_id: int, title: str, domain: str, description: str, requirements: str, rubric: str, deadline_days: int) -> None:
    """Update task details."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE tasks 
        SET title = ?, domain = ?, description = ?, requirements = ?, rubric = ?, deadline_days = ?
        WHERE id = ?
    """, (title, domain, description, requirements, rubric, int(deadline_days), task_id))
    conn.commit()
    conn.close()


def delete_task(task_id: int) -> None:
    """Delete a task and cascaded assignments."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


# -------------------------------------------------------------
# Task Assignment Operations
# -------------------------------------------------------------

def assign_task(intern_id: int, task_id: int, due_date: Optional[str] = None, notes: str = "") -> int:
    """Assign a task to an intern. If due_date is None, calculate from task deadline_days."""
    conn = get_connection()
    cur = conn.cursor()
    assigned_date = date.today().isoformat()
    
    if not due_date:
        task = get_task_by_id(task_id)
        days = task["deadline_days"] if task and task.get("deadline_days") else 14
        due_date = (date.today() + timedelta(days=days)).isoformat()
        
    cur.execute("""
        INSERT INTO intern_tasks (intern_id, task_id, status, assigned_date, due_date, notes)
        VALUES (?, ?, 'Assigned', ?, ?, ?)
        ON CONFLICT(intern_id, task_id) DO UPDATE SET
            status = 'Assigned',
            assigned_date = excluded.assigned_date,
            due_date = excluded.due_date,
            notes = excluded.notes;
    """, (intern_id, task_id, assigned_date, due_date, notes))
    conn.commit()
    assigned_id = cur.lastrowid
    conn.close()
    return assigned_id


def get_assigned_tasks(intern_id: Optional[int] = None, task_id: Optional[int] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get assigned tasks with full details of intern and task."""
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT it.id as assignment_id, it.status as assignment_status, it.assigned_date, it.due_date, it.completion_date, it.notes as assignment_notes,
               i.id as intern_id, i.intern_code, i.name as intern_name, i.email as intern_email, i.domain as intern_domain, i.mentor as intern_mentor,
               t.id as task_id, t.task_code, t.title as task_title, t.domain as task_domain, t.description as task_description,
               t.requirements as task_requirements, t.rubric as task_rubric,
               (SELECT COUNT(*) FROM submissions s WHERE s.intern_task_id = it.id) as submission_count,
               (SELECT COUNT(*) FROM reviews r WHERE r.intern_task_id = it.id) as review_count,
               (SELECT MAX(r.score) FROM reviews r WHERE r.intern_task_id = it.id AND r.status = 'Completed') as latest_score
        FROM intern_tasks it
        JOIN interns i ON it.intern_id = i.id
        JOIN tasks t ON it.task_id = t.id
        WHERE 1=1
    """
    params = []
    if intern_id:
        query += " AND it.intern_id = ?"
        params.append(intern_id)
    if task_id:
        query += " AND it.task_id = ?"
        params.append(task_id)
    if status and status != "All":
        query += " AND it.status = ?"
        params.append(status)
        
    query += " ORDER BY it.due_date ASC, it.id DESC"
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_assignment_by_id(assignment_id: int) -> Optional[Dict[str, Any]]:
    """Get a single assignment by assignment_id."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT it.id as assignment_id, it.status as assignment_status, it.assigned_date, it.due_date, it.completion_date, it.notes as assignment_notes,
               i.id as intern_id, i.intern_code, i.name as intern_name, i.email as intern_email, i.domain as intern_domain, i.mentor as intern_mentor,
               t.id as task_id, t.task_code, t.title as task_title, t.domain as task_domain, t.description as task_description,
               t.requirements as task_requirements, t.rubric as task_rubric
        FROM intern_tasks it
        JOIN interns i ON it.intern_id = i.id
        JOIN tasks t ON it.task_id = t.id
        WHERE it.id = ?
    """, (assignment_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def update_assignment_status(assignment_id: int, new_status: str, completion_date: Optional[str] = None) -> None:
    """Update assignment status."""
    conn = get_connection()
    cur = conn.cursor()
    if new_status == "Completed" and not completion_date:
        completion_date = date.today().isoformat()
    cur.execute("""
        UPDATE intern_tasks
        SET status = ?, completion_date = ?
        WHERE id = ?
    """, (new_status, completion_date, assignment_id))
    conn.commit()
    conn.close()


# -------------------------------------------------------------
# Submission Operations
# -------------------------------------------------------------

def add_submission(intern_task_id: int, github_url: str, branch: str = "main", notes: str = "") -> int:
    """Record a GitHub submission and update assignment status to Submitted."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO submissions (intern_task_id, github_url, branch, notes, status)
        VALUES (?, ?, ?, ?, 'Submitted')
    """, (intern_task_id, github_url.strip(), branch.strip(), notes.strip()))
    sub_id = cur.lastrowid
    
    # Update assignment status to Submitted if not already Completed
    cur.execute("""
        UPDATE intern_tasks
        SET status = 'Submitted'
        WHERE id = ? AND status NOT IN ('Completed')
    """, (intern_task_id,))
    
    conn.commit()
    conn.close()
    return sub_id


def get_submissions(intern_task_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieve submissions with intern and task context."""
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT s.*, 
               it.intern_id, it.task_id, it.status as assignment_status,
               i.intern_code, i.name as intern_name, i.email as intern_email,
               t.task_code, t.title as task_title
        FROM submissions s
        JOIN intern_tasks it ON s.intern_task_id = it.id
        JOIN interns i ON it.intern_id = i.id
        JOIN tasks t ON it.task_id = t.id
        WHERE 1=1
    """
    params = []
    if intern_task_id:
        query += " AND s.intern_task_id = ?"
        params.append(intern_task_id)
        
    query += " ORDER BY s.submitted_at DESC"
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_latest_submission(intern_task_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent submission for an assignment."""
    subs = get_submissions(intern_task_id)
    return subs[0] if subs else None


# -------------------------------------------------------------
# Review Operations
# -------------------------------------------------------------

def schedule_review(intern_task_id: int, reviewer: str, review_type: str, scheduled_at: str, meeting_link: str = "", submission_id: Optional[int] = None) -> int:
    """Schedule a project review."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO reviews (intern_task_id, submission_id, reviewer, review_type, scheduled_at, status, meeting_link)
        VALUES (?, ?, ?, ?, ?, 'Scheduled', ?)
    """, (intern_task_id, submission_id, reviewer.strip(), review_type.strip(), scheduled_at, meeting_link.strip()))
    rev_id = cur.lastrowid
    
    # Mark assignment as Under Review
    cur.execute("""
        UPDATE intern_tasks
        SET status = 'Under Review'
        WHERE id = ? AND status != 'Completed'
    """, (intern_task_id,))
    
    conn.commit()
    conn.close()
    return rev_id


def complete_review(review_id: int, score: float, grade: str, feedback: str, ai_analysis: Optional[Dict[str, Any]] = None, task_status_update: str = "Completed") -> None:
    """Mark a review as completed with score, grade, feedback, and analysis."""
    conn = get_connection()
    cur = conn.cursor()
    completed_at = datetime.now().isoformat()
    ai_json = json.dumps(ai_analysis) if ai_analysis else None
    
    cur.execute("""
        UPDATE reviews
        SET completed_at = ?, score = ?, grade = ?, feedback = ?, ai_analysis_json = ?, status = 'Completed'
        WHERE id = ?
    """, (completed_at, float(score), grade, feedback, ai_json, review_id))
    
    # Update linked intern task status
    cur.execute("SELECT intern_task_id FROM reviews WHERE id = ?", (review_id,))
    row = cur.fetchone()
    if row and task_status_update:
        intern_task_id = row["intern_task_id"]
        comp_date = date.today().isoformat() if task_status_update == "Completed" else None
        cur.execute("""
            UPDATE intern_tasks
            SET status = ?, completion_date = ?
            WHERE id = ?
        """, (task_status_update, comp_date, intern_task_id))
        
    conn.commit()
    conn.close()


def save_ai_automated_review(intern_task_id: int, submission_id: int, reviewer: str, score: float, grade: str, feedback: str, ai_analysis: Dict[str, Any], review_type: str = "Automated AI Review") -> int:
    """Directly insert a completed automated AI review."""
    conn = get_connection()
    cur = conn.cursor()
    now_str = datetime.now().isoformat()
    ai_json = json.dumps(ai_analysis) if ai_analysis else None
    
    cur.execute("""
        INSERT INTO reviews (intern_task_id, submission_id, reviewer, review_type, scheduled_at, completed_at, score, grade, status, feedback, ai_analysis_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Completed', ?, ?)
    """, (intern_task_id, submission_id, reviewer, review_type, now_str, now_str, float(score), grade, feedback, ai_json))
    review_id = cur.lastrowid
    
    # If score >= 70, mark assignment as Completed or keep In Review / Needs Revision
    task_status = "Completed" if score >= 70 else "Needs Revision"
    comp_date = date.today().isoformat() if score >= 70 else None
    cur.execute("""
        UPDATE intern_tasks
        SET status = ?, completion_date = ?
        WHERE id = ?
    """, (task_status, comp_date, intern_task_id))
    
    conn.commit()
    conn.close()
    return review_id


def get_reviews(intern_task_id: Optional[int] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve reviews with intern and task details."""
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT r.*,
               i.intern_code, i.name as intern_name, i.email as intern_email, i.domain as intern_domain,
               t.task_code, t.title as task_title,
               s.github_url, s.branch
        FROM reviews r
        JOIN intern_tasks it ON r.intern_task_id = it.id
        JOIN interns i ON it.intern_id = i.id
        JOIN tasks t ON it.task_id = t.id
        LEFT JOIN submissions s ON r.submission_id = s.id
        WHERE 1=1
    """
    params = []
    if intern_task_id:
        query += " AND r.intern_task_id = ?"
        params.append(intern_task_id)
    if status and status != "All":
        query += " AND r.status = ?"
        params.append(status)
        
    query += " ORDER BY r.created_at DESC"
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    
    # Parse ai_analysis_json
    for r in rows:
        if r.get("ai_analysis_json"):
            try:
                r["ai_analysis"] = json.loads(r["ai_analysis_json"])
            except Exception:
                r["ai_analysis"] = None
        else:
            r["ai_analysis"] = None
            
    conn.close()
    return rows


# -------------------------------------------------------------
# Email Logs Operations
# -------------------------------------------------------------

def log_email(recipient: str, subject: str, template_type: str, body_preview: str, status: str, simulated: bool = True, error_message: Optional[str] = None) -> int:
    """Log an email event (simulated or sent)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO email_logs (recipient, subject, template_type, body_preview, status, simulated, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (recipient, subject, template_type, body_preview[:1000], status, 1 if simulated else 0, error_message))
    conn.commit()
    log_id = cur.lastrowid
    conn.close()
    return log_id


def get_email_logs(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieve recent email logs."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM email_logs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


# -------------------------------------------------------------
# KPIs & Reporting
# -------------------------------------------------------------

def get_system_kpis() -> Dict[str, Any]:
    """Calculate key performance indicators across the internship system."""
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT COUNT(*) as c FROM interns")
    total_interns = cur.fetchone()["c"]
    
    cur.execute("SELECT COUNT(*) as c FROM tasks")
    total_tasks = cur.fetchone()["c"]
    
    cur.execute("SELECT COUNT(*) as c FROM intern_tasks")
    total_assignments = cur.fetchone()["c"]
    
    cur.execute("SELECT status, COUNT(*) as c FROM intern_tasks GROUP BY status")
    status_counts = {r["status"]: r["c"] for r in cur.fetchall()}
    
    cur.execute("SELECT COUNT(*) as c FROM submissions")
    total_submissions = cur.fetchone()["c"]
    
    cur.execute("SELECT COUNT(*) as c FROM reviews WHERE status = 'Completed'")
    completed_reviews = cur.fetchone()["c"]
    
    cur.execute("SELECT COUNT(*) as c FROM reviews WHERE status = 'Scheduled'")
    scheduled_reviews = cur.fetchone()["c"]
    
    cur.execute("SELECT AVG(score) as avg_s FROM reviews WHERE status = 'Completed' AND score IS NOT NULL")
    avg_score = cur.fetchone()["avg_s"]
    avg_score = round(avg_score, 1) if avg_score is not None else 0.0
    
    # Overdue assignments (due_date < today AND status != 'Completed')
    today_str = date.today().isoformat()
    cur.execute("""
        SELECT COUNT(*) as c FROM intern_tasks 
        WHERE due_date < ? AND status NOT IN ('Completed')
    """, (today_str,))
    overdue_count = cur.fetchone()["c"]
    
    conn.close()
    return {
        "total_interns": total_interns,
        "total_tasks": total_tasks,
        "total_assignments": total_assignments,
        "status_counts": status_counts,
        "total_submissions": total_submissions,
        "completed_reviews": completed_reviews,
        "scheduled_reviews": scheduled_reviews,
        "avg_score": avg_score,
        "overdue_count": overdue_count
    }


# -------------------------------------------------------------
# Sample Data Seeder
# -------------------------------------------------------------

def seed_sample_data(force: bool = False) -> None:
    """Seed the database with rich, realistic data if empty or forced."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM interns")
    count = cur.fetchone()["c"]
    conn.close()
    
    if count > 0 and not force:
        return  # already seeded
        
    # Sample Interns
    sample_interns = [
        ("INT-2024-001", "Aarav Sharma", "aarav.sharma@example.com", "Engineering", "Full Stack Development", "Dr. Priya Nair"),
        ("INT-2024-002", "Diya Patel", "diya.patel@example.com", "AI & Research", "Machine Learning & AI", "Dr. Rajesh Iyer"),
        ("INT-2024-003", "Rohan Mehta", "rohan.mehta@example.com", "DevOps & Cloud", "Cloud Infrastructure", "Vikram Sen"),
        ("INT-2024-004", "Ananya Verma", "ananya.verma@example.com", "Data Analytics", "Data Science", "Dr. Priya Nair"),
        ("INT-2024-005", "Kabir Das", "kabir.das@example.com", "Engineering", "Full Stack Development", "Vikram Sen"),
    ]
    
    intern_ids = []
    for code, name, email, dept, domain, mentor in sample_interns:
        i_id = add_intern(code, name, email, dept, domain, mentor)
        intern_ids.append(i_id)
        
    # Sample Tasks
    sample_tasks = [
        (
            "TSK-101",
            "REST API Development with Authentication & SQLite",
            "Full Stack Development",
            "Build a secure RESTful API using FastAPI or Flask that supports JWT authentication, user registration, role-based access, and CRUD operations on project items. Store data in SQLite.",
            "- Implement /api/register and /api/login with JWT token issuance\n- Role-based authorization middleware\n- CRUD endpoints for Items with input validation\n- Unit tests covering endpoints with pytest\n- Comprehensive README with setup commands and cURL examples",
            "- Architecture & Clean Code: 25%\n- Authentication & Security: 25%\n- Testing & Validation: 25%\n- Documentation & API Spec: 25%",
            14
        ),
        (
            "TSK-102",
            "Customer Churn Prediction Pipeline with Scikit-Learn",
            "Machine Learning & AI",
            "Develop an end-to-end machine learning pipeline to predict customer churn based on historical telemetry and subscription data. Include data preprocessing, model selection, hyperparameter tuning, and a Streamlit inference dashboard.",
            "- Data cleaning and exploratory analysis notebook\n- Preprocessing pipeline with scikit-learn ColumnTransformer\n- Model training and comparison (RandomForest, XGBoost, LogisticRegression)\n- Evaluation metrics: ROC-AUC, Precision-Recall, Confusion Matrix\n- Interactive Streamlit app for real-time customer risk prediction",
            "- Pipeline Architecture: 30%\n- Model Evaluation & Rigor: 30%\n- Code Quality & Modularity: 20%\n- Dashboard & Presentation: 20%",
            21
        ),
        (
            "TSK-103",
            "Containerized CI/CD Deployment with GitHub Actions & Docker",
            "Cloud Infrastructure",
            "Create a multi-stage Dockerfile for a microservice and set up a GitHub Actions workflow that executes linting, unit tests, security scanning (Trivy), and automated container build.",
            "- Multi-stage Dockerfile optimizing image size (< 150MB)\n- docker-compose.yml for local multi-service testing\n- GitHub Actions workflow (.github/workflows/ci.yml)\n- Automated test and lint gates (flake8/black)\n- Healthcheck endpoint and container restart policies",
            "- Docker Best Practices: 35%\n- CI/CD Pipeline Automation: 35%\n- Security & Linting: 15%\n- Documentation & Verifiability: 15%",
            14
        ),
        (
            "TSK-104",
            "Interactive E-Commerce Sales Performance Dashboard",
            "Data Science",
            "Build an interactive executive sales analytics dashboard using Python and Streamlit or Plotly. Enable filtering by region, date range, and product category with dynamic forecast visualizations.",
            "- Interactive date, region, and category filters\n- Key KPI metrics cards (Revenue, Margin, Units, AOV)\n- Trend lines and seasonality breakdown using Plotly\n- Moving average and 30-day forecast projection\n- Export filtered reports to CSV",
            "- Visualization Quality & UX: 35%\n- Data Handling & Performance: 25%\n- Code Organization: 20%\n- Business Insights: 20%",
            14
        )
    ]
    
    task_ids = []
    for code, title, domain, desc, reqs, rubric, days in sample_tasks:
        t_id = add_task(code, title, domain, desc, reqs, rubric, days)
        task_ids.append(t_id)
        
    # Assign tasks to interns
    assignments = [
        # (intern_index, task_index, status, due_delta_days, sample_repo)
        (0, 0, "Submitted", 5, "https://github.com/octocat/Hello-World"),
        (1, 1, "In Progress", 10, None),
        (2, 2, "Assigned", 14, None),
        (3, 3, "Completed", -2, "https://github.com/psf/requests"),
        (4, 0, "Under Review", 3, "https://github.com/tiangolo/fastapi"),
    ]
    
    for i_idx, t_idx, status, delta, repo in assignments:
        i_id = intern_ids[i_idx]
        t_id = task_ids[t_idx]
        due_d = (date.today() + timedelta(days=delta)).isoformat()
        assign_id = assign_task(i_id, t_id, due_d, f"Cohort 2024 Assignment")
        update_assignment_status(assign_id, status)
        
        # Add sample submission if repo provided
        if repo:
            sub_id = add_submission(assign_id, repo, "main", "Completed initial implementation and verified all unit tests.")
            if status == "Completed":
                # Add sample review
                ai_mock_report = {
                    "overall_score": 92.0,
                    "letter_grade": "A+",
                    "category_scores": {
                        "requirement_coverage": 28,
                        "code_quality": 24,
                        "documentation": 18,
                        "testing": 13,
                        "git_hygiene": 9
                    },
                    "strengths": [
                        "Comprehensive README with clear setup steps and architecture diagram.",
                        "Clean modular code structure with strong separation of concerns.",
                        "Unit test suite covers core endpoints and edge cases."
                    ],
                    "deficiencies": [
                        "Could add load testing or rate-limiting middleware for production hardening."
                    ],
                    "recommendations": [
                        "Integrate flake8 or ruff into GitHub Actions for automated lint enforcement.",
                        "Consider adding OpenAPI schema export in the documentation."
                    ]
                }
                save_ai_automated_review(
                    intern_task_id=assign_id,
                    submission_id=sub_id,
                    reviewer="AI Continuous Reviewer & Dr. Priya Nair",
                    score=92.0,
                    grade="A+",
                    feedback="Exceptional execution. The codebase demonstrates high software engineering maturity, good test coverage, and clear documentation.",
                    ai_analysis=ai_mock_report,
                    review_type="Automated AI & Mentor Review"
                )
            elif status == "Under Review":
                # Schedule a review
                review_time = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d 15:00")
                schedule_review(
                    intern_task_id=assign_id,
                    reviewer="Vikram Sen",
                    review_type="Milestone Code Review",
                    scheduled_at=review_time,
                    meeting_link="https://meet.google.com/xyz-abcd-uvw",
                    submission_id=sub_id
                )


if __name__ == "__main__":
    init_db()
    seed_sample_data()
    print("Database initialized and sample data seeded successfully.")
