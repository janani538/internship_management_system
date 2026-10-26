"""
End-to-End System Test Suite
Verifies all 9 features of the AI-Powered Internship Management and Project Review System.
"""

import os
import sys
import json
from datetime import datetime, date, timedelta

# Reconfigure stdout for utf-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Import project modules
import database as db
import excel_handler as eh
import github_analyzer as gh
import ai_service as ai
import email_service as em


def test_database_and_seeder():
    print("--- [Test 1/8] Database Initialization & Seeding ---")
    db.init_db()
    db.seed_sample_data(force=True)
    
    kpis = db.get_system_kpis()
    assert kpis["total_interns"] >= 5, f"Expected at least 5 interns, got {kpis['total_interns']}"
    assert kpis["total_tasks"] >= 4, f"Expected at least 4 tasks, got {kpis['total_tasks']}"
    assert kpis["total_assignments"] >= 5, f"Expected at least 5 assignments, got {kpis['total_assignments']}"
    print(f"✅ DB initialized and seeded: {kpis['total_interns']} interns, {kpis['total_tasks']} tasks, {kpis['total_assignments']} assignments.")


def test_intern_and_task_management():
    print("--- [Test 2/8] Intern & Task CRUD Operations ---")
    # Add new intern
    test_code = "INT-TEST-999"
    i_id = db.add_intern(test_code, "Test Student", "test.student@example.com", "QA", "Testing Domain", "Dr. Tester")
    intern = db.get_intern_by_id(i_id)
    assert intern is not None and intern["intern_code"] == test_code
    
    # Add new task
    t_code = "TSK-TEST-999"
    t_id = db.add_task(t_code, "Automated Test Task", "Testing Domain", "Test description", "- Req 1", "- Rubric 1", 10)
    task = db.get_task_by_id(t_id)
    assert task is not None and task["task_code"] == t_code

    # Assign task
    assign_id = db.assign_task(i_id, t_id, due_date="2026-12-31", notes="Integration test assignment")
    assigned = db.get_assignment_by_id(assign_id)
    assert assigned["intern_code"] == test_code
    assert assigned["task_code"] == t_code

    # Update status
    db.update_assignment_status(assign_id, "In Progress")
    updated = db.get_assignment_by_id(assign_id)
    assert updated["assignment_status"] == "In Progress"
    print("✅ Intern & Task CRUD and assignment flow passed.")


def test_excel_import_export():
    print("--- [Test 3/8] Excel Import and Export ---")
    # Generate template
    excel_bytes = eh.create_sample_excel_template()
    assert len(excel_bytes) > 1000, "Generated Excel bytes too small"

    # Parse template
    parsed = eh.parse_and_validate_excel(excel_bytes)
    assert parsed["success"] is True, f"Failed to parse sample Excel: {parsed['errors']}"
    assert len(parsed["interns"]) > 0, "No interns parsed from sample"
    assert len(parsed["tasks"]) > 0, "No tasks parsed from sample"

    # Import to DB
    summary = eh.import_excel_to_database(parsed)
    assert summary["interns_imported"] > 0, "No interns imported"
    assert summary["tasks_imported"] > 0, "No tasks imported"

    # Export DB
    export_bytes = eh.export_database_to_excel()
    assert len(export_bytes) > 1000, "Exported DB Excel bytes too small"
    print(f"✅ Excel parser, validator, importer ({summary['interns_imported']} interns, {summary['tasks_imported']} tasks), and exporter passed.")


def test_ai_task_assistant():
    print("--- [Test 4/8] AI Task Assistant & Explanation ---")
    tasks = db.get_all_tasks()
    first_task = tasks[0]
    
    explanation = ai.explain_task_in_simple_terms(first_task)
    assert explanation["success"] is True
    assert len(explanation["markdown_explanation"]) > 100
    print(f"✅ Task explanation generated using: {explanation['provider']}")

    # Test interactive mentor chat
    chat_reply = ai.chat_with_task_assistant(first_task, [], "How do I write unit tests for this project?")
    assert len(chat_reply) > 20, "Expected meaningful chat reply"
    print(f"✅ Mentor chat response verified ({len(chat_reply)} characters).")


def test_github_analyzer_and_submission():
    print("--- [Test 5/8] GitHub URL Parsing & Repository Inspection ---")
    # URL parsing
    test_url = "https://github.com/octocat/Hello-World"
    parsed = gh.parse_github_url(test_url)
    assert parsed == ("octocat", "Hello-World", None), f"Failed to parse URL: {parsed}"

    # Repository inspection
    inspection = gh.inspect_repository(test_url)
    assert inspection["success"] is True, f"Inspection failed: {inspection.get('error')}"
    assert inspection["owner"] == "octocat"
    assert inspection["repo"] == "Hello-World"
    assert inspection["file_count"] > 0
    print(f"✅ Repository {inspection['owner']}/{inspection['repo']} inspected ({inspection['file_count']} files, README found: {inspection['readme']['found']}).")

    # Add submission
    assignments = db.get_assigned_tasks()
    assign_id = assignments[0]["assignment_id"]
    sub_id = db.add_submission(assign_id, test_url, "master", "Test submission")
    assert sub_id > 0
    print("✅ Intern submission saved to database.")
    return inspection, assignments[0], sub_id


def test_evidence_based_ai_evaluation(repo_inspection, assignment, submission_id):
    print("--- [Test 6/8] Evidence-Based Code Evaluation & Grading ---")
    task_info = db.get_task_by_id(assignment["task_id"])
    
    evaluation = ai.analyze_repository_against_task(task_info, repo_inspection)
    assert evaluation["success"] is True, f"Evaluation failed: {evaluation.get('error')}"
    assert "overall_score" in evaluation
    assert "letter_grade" in evaluation
    assert "category_scores" in evaluation
    assert len(evaluation["evidence_found"]) > 0
    
    print(f"✅ AI Evaluation complete: Score {evaluation['overall_score']:.1f}/100, Grade: {evaluation['letter_grade']}")
    print(f"   Category breakdown: {evaluation['category_scores']}")
    print(f"   Evidence items: {len(evaluation['evidence_found'])} strengths, {len(evaluation['deficiencies'])} deficiencies")

    # Save to review history
    rev_id = db.save_ai_automated_review(
        intern_task_id=assignment["assignment_id"],
        submission_id=submission_id,
        reviewer="AI Continuous Reviewer (Test)",
        score=evaluation["overall_score"],
        grade=evaluation["letter_grade"],
        feedback="Test automated review execution",
        ai_analysis=evaluation
    )
    assert rev_id > 0
    print("✅ Automated review persisted to review history.")


def test_review_scheduler():
    print("--- [Test 7/8] Review Scheduler & History ---")
    assignments = db.get_assigned_tasks()
    target = assignments[0]
    
    review_dt = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d 14:00")
    rev_id = db.schedule_review(
        intern_task_id=target["assignment_id"],
        reviewer="Dr. Priya Nair",
        review_type="Milestone Code Review",
        scheduled_at=review_dt,
        meeting_link="https://meet.google.com/test-meet"
    )
    assert rev_id > 0

    # Retrieve reviews
    reviews = db.get_reviews(intern_task_id=target["assignment_id"])
    assert any(r["id"] == rev_id for r in reviews)
    
    # Complete the review
    db.complete_review(rev_id, 88.0, "A", "Good live presentation and handled technical questions well.")
    completed_rev = [r for r in db.get_reviews() if r["id"] == rev_id][0]
    assert completed_rev["status"] == "Completed"
    assert completed_rev["score"] == 88.0
    print("✅ Review scheduling, retrieval, and completion verified.")


def test_email_previews_and_simulation():
    print("--- [Test 8/8] Email Previews & Safe Simulation Mode ---")
    interns = db.get_all_interns()
    tasks = db.get_all_tasks()
    
    # 1. Task assignment template
    mail_assign = em.generate_task_assignment_email(interns[0], tasks[0], "2026-11-15")
    assert "html" in mail_assign and "plain_text" in mail_assign
    assert len(mail_assign["html"]) > 200

    # 2. Review scheduled template
    rev_info = {"reviewer": "Dr. Priya Nair", "review_type": "Milestone Review", "scheduled_at": "Nov 10, 2:00 PM", "meeting_link": "https://meet.google.com/abc"}
    mail_sched = em.generate_review_scheduled_email(interns[0], tasks[0], rev_info)
    assert "html" in mail_sched and "plain_text" in mail_sched

    # 3. Evaluation feedback template
    eval_info = {"score": 90.0, "grade": "A+", "reviewer": "AI Evaluator", "feedback": "Superb work!", "ai_analysis": {"category_scores": {"code": 25}}}
    mail_eval = em.generate_evaluation_feedback_email(interns[0], tasks[0], eval_info)
    assert "html" in mail_eval and "plain_text" in mail_eval

    # 4. Safe Simulation Sending (Safety check: Never sends real email)
    success, msg = em.send_email_message(
        recipient=interns[0]["email"],
        subject=mail_assign["subject"],
        html_content=mail_assign["html"],
        plain_content=mail_assign["plain_text"],
        template_type="Task Assignment",
        allow_live_send=False  # Keep simulation mode
    )
    assert success is True
    assert "simulated successfully" in msg.lower()

    # Verify email was logged to SQLite
    logs = db.get_email_logs(limit=5)
    assert len(logs) > 0
    assert logs[0]["simulated"] == 1
    print(f"✅ All 3 email templates generated, simulation safety verified, and email event logged in SQLite.")


def main():
    print("==================================================================")
    print("🚀 Starting AI Internship Management System Automated Test Suite")
    print("==================================================================")
    test_database_and_seeder()
    test_intern_and_task_management()
    test_excel_import_export()
    test_ai_task_assistant()
    repo_inspect, assign, sub_id = test_github_analyzer_and_submission()
    test_evidence_based_ai_evaluation(repo_inspect, assign, sub_id)
    test_review_scheduler()
    test_email_previews_and_simulation()
    print("==================================================================")
    print("🎉 ALL 8 TEST PHASES PASSED WITH ZERO ERRORS!")
    print("==================================================================")


if __name__ == "__main__":
    main()
