"""
Excel Import and Export Handler Module
Handles parsing, validation, sample template generation, and database ingestion for Interns and Tasks.
"""

import io
import os
import pandas as pd
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime, date, timedelta
from database import add_intern, add_task, assign_task, get_all_interns, get_all_tasks, get_assigned_tasks, get_reviews


def create_sample_excel_template() -> bytes:
    """Generate a formatted sample Excel file in memory with Interns and Tasks sheets."""
    interns_data = [
        {
            "Intern Code": "INT-2024-101",
            "Name": "Vikram Sethi",
            "Email": "vikram.sethi@example.com",
            "Department": "Software Engineering",
            "Domain": "Full Stack Development",
            "Mentor": "Dr. Priya Nair",
            "Assigned Task Code": "TSK-201",
            "Deadline Days": 14
        },
        {
            "Intern Code": "INT-2024-102",
            "Name": "Sneha Roy",
            "Email": "sneha.roy@example.com",
            "Department": "Data Science & AI",
            "Domain": "Machine Learning & AI",
            "Mentor": "Dr. Rajesh Iyer",
            "Assigned Task Code": "TSK-202",
            "Deadline Days": 21
        },
        {
            "Intern Code": "INT-2024-103",
            "Name": "Arjun Kapoor",
            "Email": "arjun.kapoor@example.com",
            "Department": "Cloud & Infrastructure",
            "Domain": "Cloud Infrastructure",
            "Mentor": "Vikram Sen",
            "Assigned Task Code": "TSK-203",
            "Deadline Days": 14
        },
        {
            "Intern Code": "INT-2024-104",
            "Name": "Meera Joshi",
            "Email": "meera.joshi@example.com",
            "Department": "Product Analytics",
            "Domain": "Data Science",
            "Mentor": "Dr. Priya Nair",
            "Assigned Task Code": "TSK-204",
            "Deadline Days": 14
        }
    ]

    tasks_data = [
        {
            "Task Code": "TSK-201",
            "Title": "Microservice Architecture with FastApi and Redis Caching",
            "Domain": "Full Stack Development",
            "Description": "Build a scalable microservice using FastAPI that manages catalog inventory and uses Redis for caching frequently queried items.",
            "Requirements": "- CRUD API endpoints with Pydantic validation\n- Redis caching layer with TTL\n- Asynchronous database operations (SQLAlchemy / asyncpg)\n- Pytest unit and integration test suite\n- Dockerfile and README documentation",
            "Rubric": "- Code Quality & Typing: 25%\n- Caching & Performance: 25%\n- Test Coverage: 25%\n- Documentation: 25%",
            "Deadline Days": 14
        },
        {
            "Task Code": "TSK-202",
            "Title": "NLP Sentiment Analysis & Topic Extraction Model",
            "Domain": "Machine Learning & AI",
            "Description": "Develop an NLP model to classify customer feedback into sentiment categories and automatically extract dominant topics using Hugging Face Transformers or spaCy.",
            "Requirements": "- Text preprocessing pipeline (tokenization, stop words, lemmatization)\n- Fine-tuned transformer or TF-IDF + LogisticRegression baseline\n- Topic modeling using LDA or BERTopic\n- Model evaluation report with Confusion Matrix and F1-score\n- Streamlit interactive demo",
            "Rubric": "- Model Accuracy & Rigor: 35%\n- Preprocessing Pipeline: 25%\n- Code Architecture: 20%\n- Interactive Demo: 20%",
            "Deadline Days": 21
        },
        {
            "Task Code": "TSK-203",
            "Title": "Kubernetes Cluster Deployment & Monitoring Setup",
            "Domain": "Cloud Infrastructure",
            "Description": "Create Kubernetes manifests (Deployment, Service, Ingress, ConfigMap) for a multi-tier web application and integrate Prometheus metrics and Grafana alerts.",
            "Requirements": "- K8s deployment with liveness and readiness probes\n- Horizontal Pod Autoscaler (HPA) definition\n- Ingress routing with TLS termination\n- Helm chart packaging\n- Step-by-step verification guide in README",
            "Rubric": "- Manifest Reliability: 35%\n- Autoscaling & Resilience: 30%\n- Helm Packaging: 20%\n- Documentation: 15%",
            "Deadline Days": 14
        },
        {
            "Task Code": "TSK-204",
            "Title": "Financial Risk & Anomaly Detection Pipeline",
            "Domain": "Data Science",
            "Description": "Build an anomaly detection engine for financial transaction streams using Isolation Forest or Autoencoders, reporting anomalous patterns on a dynamic dashboard.",
            "Requirements": "- Feature engineering on transaction logs (velocity, amounts, location shift)\n- Isolation Forest or One-Class SVM anomaly model\n- Threshold tuning and ROC-AUC assessment\n- Streamlit dashboard highlighting flagged transactions with risk scores",
            "Rubric": "- Feature Engineering: 30%\n- Model Performance: 30%\n- Code Modularity: 20%\n- Dashboard & UX: 20%",
            "Deadline Days": 14
        }
    ]

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_interns = pd.DataFrame(interns_data)
        df_tasks = pd.DataFrame(tasks_data)
        df_interns.to_excel(writer, sheet_name="Interns", index=False)
        df_tasks.to_excel(writer, sheet_name="Tasks", index=False)

    return output.getvalue()


def parse_and_validate_excel(file_content: bytes) -> Dict[str, Any]:
    """
    Parse uploaded Excel file bytes, validate schemas, and extract interns and tasks.
    Returns a dictionary with parsed records, validation messages, and errors.
    """
    results: Dict[str, Any] = {
        "success": False,
        "interns": [],
        "tasks": [],
        "assignments": [],
        "warnings": [],
        "errors": []
    }

    try:
        excel_file = pd.ExcelFile(io.BytesIO(file_content))
        sheet_names = excel_file.sheet_names
    except Exception as e:
        results["errors"].append(f"Failed to read Excel file: {str(e)}")
        return results

    # Normalize sheet names lookup
    sheet_map = {s.strip().lower(): s for s in sheet_names}

    # Helper column normalizer
    def norm_col(col_name: str) -> str:
        return str(col_name).strip().lower().replace("_", " ").replace("-", " ")

    # 1. Parse Tasks if present
    task_sheet_candidates = ["tasks", "task", "task list", "projects"]
    task_sheet_name = None
    for cand in task_sheet_candidates:
        if cand in sheet_map:
            task_sheet_name = sheet_map[cand]
            break

    tasks_dict = {}  # code -> task_id or info
    if task_sheet_name:
        try:
            df_tasks = excel_file.parse(task_sheet_name)
            col_lookup = {norm_col(c): c for c in df_tasks.columns}
            
            code_col = col_lookup.get("task code") or col_lookup.get("task id") or col_lookup.get("code") or col_lookup.get("id")
            title_col = col_lookup.get("title") or col_lookup.get("task title") or col_lookup.get("name")
            domain_col = col_lookup.get("domain") or col_lookup.get("department") or col_lookup.get("category")
            desc_col = col_lookup.get("description") or col_lookup.get("task description") or col_lookup.get("details")
            reqs_col = col_lookup.get("requirements") or col_lookup.get("deliverables") or col_lookup.get("scope")
            rubric_col = col_lookup.get("rubric") or col_lookup.get("criteria") or col_lookup.get("evaluation")
            days_col = col_lookup.get("deadline days") or col_lookup.get("deadline (days)") or col_lookup.get("days")

            if not code_col or not title_col:
                results["warnings"].append(f"Tasks sheet '{task_sheet_name}' is missing required columns (Task Code, Title).")
            else:
                for idx, row in df_tasks.iterrows():
                    code = str(row.get(code_col, "")).strip()
                    title = str(row.get(title_col, "")).strip()
                    if not code or code == "nan" or not title or title == "nan":
                        continue
                    
                    domain = str(row.get(domain_col, "")) if domain_col else ""
                    desc = str(row.get(desc_col, "")) if desc_col else ""
                    reqs = str(row.get(reqs_col, "")) if reqs_col else ""
                    rubric = str(row.get(rubric_col, "")) if rubric_col else ""
                    days_raw = row.get(days_col, 14) if days_col else 14
                    try:
                        days = int(days_raw) if pd.notnull(days_raw) else 14
                    except (ValueError, TypeError):
                        days = 14

                    task_entry = {
                        "task_code": code,
                        "title": title,
                        "domain": "" if domain == "nan" else domain,
                        "description": "" if desc == "nan" else desc,
                        "requirements": "" if reqs == "nan" else reqs,
                        "rubric": "" if rubric == "nan" else rubric,
                        "deadline_days": days
                    }
                    results["tasks"].append(task_entry)
                    tasks_dict[code.lower()] = task_entry
        except Exception as e:
            results["errors"].append(f"Error parsing Tasks sheet: {str(e)}")

    # 2. Parse Interns sheet
    intern_sheet_candidates = ["interns", "intern", "students", "candidates", "intern details"]
    intern_sheet_name = None
    for cand in intern_sheet_candidates:
        if cand in sheet_map:
            intern_sheet_name = sheet_map[cand]
            break
            
    # If no sheet matched "Interns", but there's a sheet that wasn't Tasks, try the first sheet
    if not intern_sheet_name:
        for s in sheet_names:
            if s != task_sheet_name:
                intern_sheet_name = s
                break

    if intern_sheet_name:
        try:
            df_interns = excel_file.parse(intern_sheet_name)
            col_lookup = {norm_col(c): c for c in df_interns.columns}

            code_col = col_lookup.get("intern code") or col_lookup.get("intern id") or col_lookup.get("id") or col_lookup.get("roll no") or col_lookup.get("code")
            name_col = col_lookup.get("name") or col_lookup.get("intern name") or col_lookup.get("full name")
            email_col = col_lookup.get("email") or col_lookup.get("email address") or col_lookup.get("mail")
            dept_col = col_lookup.get("department") or col_lookup.get("dept") or col_lookup.get("college")
            domain_col = col_lookup.get("domain") or col_lookup.get("track") or col_lookup.get("role")
            mentor_col = col_lookup.get("mentor") or col_lookup.get("guide") or col_lookup.get("supervisor")
            assigned_task_col = col_lookup.get("assigned task code") or col_lookup.get("task code") or col_lookup.get("task id") or col_lookup.get("assigned task")
            deadline_col = col_lookup.get("deadline days") or col_lookup.get("due date") or col_lookup.get("days")

            if not code_col or not name_col or not email_col:
                results["errors"].append(f"Interns sheet '{intern_sheet_name}' is missing mandatory columns: Intern Code, Name, Email.")
            else:
                for idx, row in df_interns.iterrows():
                    code = str(row.get(code_col, "")).strip()
                    name = str(row.get(name_col, "")).strip()
                    email = str(row.get(email_col, "")).strip()

                    if not code or code == "nan" or not name or name == "nan" or not email or email == "nan":
                        continue

                    dept = str(row.get(dept_col, "")) if dept_col else ""
                    domain = str(row.get(domain_col, "")) if domain_col else ""
                    mentor = str(row.get(mentor_col, "")) if mentor_col else ""
                    assigned_task = str(row.get(assigned_task_col, "")).strip() if assigned_task_col else ""
                    deadline_raw = row.get(deadline_col, None) if deadline_col else None

                    intern_entry = {
                        "intern_code": code,
                        "name": name,
                        "email": email,
                        "department": "" if dept == "nan" else dept,
                        "domain": "" if domain == "nan" else domain,
                        "mentor": "" if mentor == "nan" else mentor,
                        "assigned_task_code": "" if assigned_task == "nan" else assigned_task,
                        "deadline_info": deadline_raw
                    }
                    results["interns"].append(intern_entry)
        except Exception as e:
            results["errors"].append(f"Error parsing Interns sheet: {str(e)}")
    else:
        results["errors"].append("Could not find an Interns sheet in the uploaded Excel workbook.")

    results["success"] = len(results["errors"]) == 0 and (len(results["interns"]) > 0 or len(results["tasks"]) > 0)
    return results


def import_excel_to_database(parsed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Commit parsed Excel records into SQLite database.
    Performs upserts for interns and tasks, and links assignments if specified.
    """
    summary = {
        "interns_imported": 0,
        "tasks_imported": 0,
        "assignments_created": 0,
        "errors": []
    }

    task_code_to_id = {}
    # 1. Import Tasks
    for t in parsed_data.get("tasks", []):
        try:
            t_id = add_task(
                task_code=t["task_code"],
                title=t["title"],
                domain=t.get("domain", ""),
                description=t.get("description", ""),
                requirements=t.get("requirements", ""),
                rubric=t.get("rubric", ""),
                deadline_days=t.get("deadline_days", 14)
            )
            task_code_to_id[t["task_code"].upper()] = t_id
            summary["tasks_imported"] += 1
        except Exception as e:
            summary["errors"].append(f"Failed to import task {t.get('task_code')}: {str(e)}")

    # Fetch existing tasks to resolve any references
    existing_tasks = get_all_tasks()
    for et in existing_tasks:
        task_code_to_id[et["task_code"].upper()] = et["id"]

    # 2. Import Interns
    for i in parsed_data.get("interns", []):
        try:
            i_id = add_intern(
                intern_code=i["intern_code"],
                name=i["name"],
                email=i["email"],
                department=i.get("department", ""),
                domain=i.get("domain", ""),
                mentor=i.get("mentor", "")
            )
            summary["interns_imported"] += 1

            # Check if an assigned task code is provided
            assigned_task_code = i.get("assigned_task_code", "").upper()
            if assigned_task_code and assigned_task_code in task_code_to_id:
                t_id = task_code_to_id[assigned_task_code]
                
                # Determine due date
                due_d = None
                deadline_info = i.get("deadline_info")
                if pd.notnull(deadline_info):
                    try:
                        if isinstance(deadline_info, (int, float)):
                            due_d = (date.today() + timedelta(days=int(deadline_info))).isoformat()
                        else:
                            # Try parsing string date
                            parsed_date = pd.to_datetime(deadline_info)
                            due_d = parsed_date.strftime("%Y-%m-%d")
                    except Exception:
                        due_d = (date.today() + timedelta(days=14)).isoformat()
                        
                assign_task(i_id, t_id, due_date=due_d, notes="Imported via Excel spreadsheet")
                summary["assignments_created"] += 1
        except Exception as e:
            summary["errors"].append(f"Failed to import intern {i.get('intern_code')}: {str(e)}")

    return summary


def export_database_to_excel() -> bytes:
    """Export complete current database state to an Excel workbook in memory."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Interns
        interns = get_all_interns()
        if interns:
            df_i = pd.DataFrame(interns)
            df_i.to_excel(writer, sheet_name="Interns", index=False)
        else:
            pd.DataFrame(columns=["intern_code", "name", "email", "domain", "mentor"]).to_excel(writer, sheet_name="Interns", index=False)

        # Tasks
        tasks = get_all_tasks()
        if tasks:
            df_t = pd.DataFrame(tasks)
            df_t.to_excel(writer, sheet_name="Tasks", index=False)
        else:
            pd.DataFrame(columns=["task_code", "title", "domain", "description", "requirements", "rubric"]).to_excel(writer, sheet_name="Tasks", index=False)

        # Assignments
        assignments = get_assigned_tasks()
        if assignments:
            df_a = pd.DataFrame(assignments)
            # Remove heavy redundant text columns for clean report
            cols = [c for c in df_a.columns if c not in ["task_description", "task_requirements", "task_rubric"]]
            df_a[cols].to_excel(writer, sheet_name="Assignments", index=False)

        # Reviews
        reviews = get_reviews()
        if reviews:
            df_r = pd.DataFrame(reviews)
            cols = [c for c in df_r.columns if c not in ["ai_analysis_json", "ai_analysis"]]
            df_r[cols].to_excel(writer, sheet_name="Reviews", index=False)

    return output.getvalue()
