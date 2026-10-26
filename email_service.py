"""
Email Service Module
Generates rich HTML/text email previews and supports safe simulated or live SMTP email delivery.
Ensures no real emails are sent without explicit user permission.
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from database import log_email

load_dotenv()


def get_smtp_config() -> Dict[str, Any]:
    """Retrieve SMTP configuration from environment."""
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", 587))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    use_tls = os.getenv("SMTP_USE_TLS", "True").lower() in ("true", "1", "yes")
    from_email = os.getenv("SMTP_FROM_EMAIL", "").strip() or user or "notifications@internship-system.local"
    from_name = os.getenv("SMTP_FROM_NAME", "Internship Review System").strip()
    simulation_mode = os.getenv("EMAIL_SIMULATION_MODE", "True").lower() in ("true", "1", "yes")

    is_configured = bool(host and user and password)

    return {
        "host": host,
        "port": port,
        "user": user,
        "is_configured": is_configured,
        "password_masked": "********" if password else "Not Set",
        "use_tls": use_tls,
        "from_email": from_email,
        "from_name": from_name,
        "simulation_mode": simulation_mode
    }


# -------------------------------------------------------------
# Template Generators
# -------------------------------------------------------------

def generate_task_assignment_email(intern: Dict[str, Any], task: Dict[str, Any], due_date: str) -> Dict[str, str]:
    """Generate HTML and plain text for task assignment notification."""
    intern_name = intern.get("name", "Intern")
    intern_email = intern.get("email", "")
    task_code = task.get("task_code", "TSK-000")
    task_title = task.get("title", "")
    task_desc = task.get("description", "")
    task_reqs = task.get("requirements", "")
    domain = task.get("domain", "")

    subject = f"[{task_code}] New Task Assigned: {task_title}"

    plain_text = f"""Hello {intern_name},

A new project task has been assigned to you.

Task Code: {task_code}
Title: {task_title}
Domain: {domain}
Due Date: {due_date}

Description:
{task_desc}

Requirements:
{task_reqs}

Please access the Internship Portal to review details, chat with the AI Task Assistant, and submit your GitHub repository when ready.

Best regards,
Internship Management Team
"""

    reqs_html = "".join([f"<li>{r.strip('- ')}</li>" for r in task_reqs.split("\n") if r.strip()])
    if not reqs_html:
        reqs_html = "<li>Refer to the task guidelines on the portal.</li>"

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; margin: 0; padding: 20px; }}
  .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
  .header {{ background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #ffffff; padding: 28px 24px; }}
  .header h1 {{ margin: 0 0 8px 0; font-size: 22px; font-weight: 700; }}
  .badge {{ display: inline-block; background: rgba(255,255,255,0.2); color: #ffffff; font-size: 12px; font-weight: 600; padding: 4px 10px; border-radius: 20px; }}
  .content {{ padding: 28px 24px; }}
  .card {{ background: #f1f5f9; border-left: 4px solid #2563eb; border-radius: 6px; padding: 16px; margin: 20px 0; }}
  .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }}
  .meta-item {{ font-size: 13px; color: #64748b; }}
  .meta-value {{ font-size: 14px; font-weight: 600; color: #0f172a; }}
  ul {{ padding-left: 20px; color: #334155; }}
  li {{ margin-bottom: 6px; }}
  .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px 24px; font-size: 12px; color: #94a3b8; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <span class="badge">{domain}</span>
    <h1>New Task Assigned</h1>
    <div style="font-size: 14px; opacity: 0.9;">Internship Program 2024</div>
  </div>
  <div class="content">
    <p>Dear <strong>{intern_name}</strong>,</p>
    <p>You have been assigned a new project task. Please review the specifications below and plan your milestones accordingly.</p>
    
    <div class="card">
      <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; color: #2563eb; font-weight: 700; margin-bottom: 4px;">{task_code}</div>
      <div style="font-size: 18px; font-weight: 700; color: #0f172a; margin-bottom: 12px;">{task_title}</div>
      <div class="meta-grid">
        <div class="meta-item">Due Date:<br><span class="meta-value" style="color: #dc2626;">{due_date}</span></div>
        <div class="meta-item">Mentor:<br><span class="meta-value">{intern.get('mentor', 'Assigned Mentor')}</span></div>
      </div>
      <p style="margin: 8px 0 0 0; font-size: 13px; color: #475569;">{task_desc}</p>
    </div>

    <h3 style="font-size: 15px; color: #0f172a; margin-bottom: 8px;">Key Deliverables & Scope:</h3>
    <ul>
      {reqs_html}
    </ul>

    <p style="font-size: 13px; color: #64748b; margin-top: 24px;">
      💡 <em>Tip: You can use the built-in <strong>AI Task Assistant</strong> on the portal to get a step-by-step roadmap or ask technical questions.</em>
    </p>
  </div>
  <div class="footer">
    Continuous Project Review System • Confidential & Intended for {intern_email}
  </div>
</div>
</body>
</html>
"""
    return {"subject": subject, "plain_text": plain_text, "html": html, "recipient": intern_email}


def generate_review_scheduled_email(intern: Dict[str, Any], task: Dict[str, Any], review: Dict[str, Any]) -> Dict[str, str]:
    """Generate email notification for scheduled project review."""
    intern_name = intern.get("name", "Intern")
    intern_email = intern.get("email", "")
    task_title = task.get("title", "")
    reviewer = review.get("reviewer", "Project Mentor")
    review_type = review.get("review_type", "Milestone Review")
    scheduled_at = review.get("scheduled_at", "TBD")
    meeting_link = review.get("meeting_link", "https://meet.google.com")

    subject = f"[{review_type}] Review Scheduled: {task_title}"

    plain_text = f"""Hello {intern_name},

Your {review_type} for '{task_title}' has been scheduled.

Review Details:
- Date & Time: {scheduled_at}
- Reviewer: {reviewer}
- Meeting Link: {meeting_link}

Preparation Checklist:
1. Ensure your latest code is committed and pushed to your submitted GitHub repository.
2. Have a working local demonstration or live deployment ready.
3. Prepare a brief 5-minute walkthrough of your architecture and tests.

Best regards,
Internship Evaluation Committee
"""

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; margin: 0; padding: 20px; }}
  .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; }}
  .header {{ background: linear-gradient(135deg, #059669, #047857); color: #ffffff; padding: 28px 24px; }}
  .header h1 {{ margin: 0 0 8px 0; font-size: 22px; }}
  .content {{ padding: 28px 24px; }}
  .highlight-box {{ background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 18px; margin: 20px 0; }}
  .row {{ display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 14px; }}
  .label {{ color: #065f46; font-weight: 600; }}
  .val {{ font-weight: 700; color: #064e3b; }}
  .button {{ display: inline-block; background: #059669; color: #ffffff !important; text-decoration: none; padding: 12px 24px; border-radius: 6px; font-weight: 600; margin-top: 12px; }}
  .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px 24px; font-size: 12px; color: #94a3b8; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div style="font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; opacity: 0.9;">Review Notification</div>
    <h1>{review_type} Scheduled</h1>
  </div>
  <div class="content">
    <p>Dear <strong>{intern_name}</strong>,</p>
    <p>Your upcoming project review for <strong>{task_title}</strong> has been scheduled.</p>

    <div class="highlight-box">
      <div class="row"><span class="label">📅 Scheduled At:</span><span class="val">{scheduled_at}</span></div>
      <div class="row"><span class="label">👤 Reviewer:</span><span class="val">{reviewer}</span></div>
      <div class="row"><span class="label">📌 Review Type:</span><span class="val">{review_type}</span></div>
      <div style="text-align: center; margin-top: 16px;">
        <a href="{meeting_link}" class="button" target="_blank">Join Review Meeting</a>
      </div>
    </div>

    <h3 style="font-size: 15px; margin-top: 24px;">Preparation Checklist:</h3>
    <ul>
      <li>Ensure your latest code changes are pushed to your GitHub repository.</li>
      <li>Verify your unit tests are passing.</li>
      <li>Be prepared to explain your design choices and demonstrate working features.</li>
    </ul>
  </div>
  <div class="footer">
    Continuous Project Review System • Confidential & Intended for {intern_email}
  </div>
</div>
</body>
</html>
"""
    return {"subject": subject, "plain_text": plain_text, "html": html, "recipient": intern_email}


def generate_evaluation_feedback_email(intern: Dict[str, Any], task: Dict[str, Any], review: Dict[str, Any]) -> Dict[str, str]:
    """Generate evaluation scorecard and feedback email."""
    intern_name = intern.get("name", "Intern")
    intern_email = intern.get("email", "")
    task_title = task.get("title", "")
    score = review.get("score", 0.0)
    grade = review.get("grade", "N/A")
    feedback = review.get("feedback", "No written feedback provided.")
    reviewer = review.get("reviewer", "Project Evaluator")
    ai_analysis = review.get("ai_analysis") or {}

    subject = f"[Review Results] {task_title} - Grade: {grade} ({score}/100)"

    cat_scores = ai_analysis.get("category_scores", {})
    strengths = ai_analysis.get("evidence_found") or ai_analysis.get("strengths") or []
    recs = ai_analysis.get("recommendations") or []

    strengths_text = "\n".join([f"- {s}" for s in strengths[:3]])
    recs_text = "\n".join([f"- {r}" for r in recs[:3]])

    plain_text = f"""Hello {intern_name},

Your project submission for '{task_title}' has been reviewed.

Evaluation Summary:
- Overall Score: {score}/100
- Grade: {grade}
- Evaluator: {reviewer}

Evaluator Feedback:
{feedback}

Key Strengths Identified:
{strengths_text if strengths_text else "- Satisfactory submission."}

Recommendations for Improvement:
{recs_text if recs_text else "- Keep following best engineering practices."}

Best regards,
Internship Evaluation Committee
"""

    badge_color = "#059669" if score >= 80 else ("#d97706" if score >= 60 else "#dc2626")

    score_bars_html = ""
    for cat, val in cat_scores.items():
        cat_name = cat.replace("_", " ").title()
        score_bars_html += f"""
        <div style="margin-bottom: 8px;">
          <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom: 2px;">
            <span style="color:#475569;">{cat_name}</span>
            <span style="font-weight:600; color:#0f172a;">{val} pts</span>
          </div>
        </div>
        """

    strengths_html = "".join([f"<li>{s}</li>" for s in strengths[:3]]) or "<li>Core deliverables verified.</li>"
    recs_html = "".join([f"<li>{r}</li>" for r in recs[:3]]) or "<li>Continue refining testing and documentation.</li>"

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; background-color: #f8fafc; margin: 0; padding: 20px; }}
  .container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; }}
  .header {{ background: linear-gradient(135deg, #1e293b, #0f172a); color: #ffffff; padding: 28px 24px; text-align: center; }}
  .score-badge {{ display: inline-block; background: {badge_color}; color: #ffffff; font-size: 26px; font-weight: 800; padding: 8px 20px; border-radius: 30px; margin: 12px 0 6px 0; }}
  .content {{ padding: 28px 24px; }}
  .feedback-box {{ background: #f8fafc; border-left: 4px solid #3b82f6; padding: 14px 18px; border-radius: 4px; margin: 16px 0; font-style: italic; color: #334155; }}
  .section-title {{ font-size: 14px; font-weight: 700; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 20px; margin-bottom: 8px; }}
  ul {{ padding-left: 20px; color: #475569; }}
  li {{ margin-bottom: 6px; font-size: 13px; }}
  .footer {{ background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px 24px; font-size: 12px; color: #94a3b8; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div style="font-size: 12px; letter-spacing: 1px; text-transform: uppercase; opacity: 0.8;">Continuous Review Report</div>
    <div class="score-badge">{grade} • {score}/100</div>
    <div style="font-size: 14px; opacity: 0.9;">{task_title}</div>
  </div>
  <div class="content">
    <p>Dear <strong>{intern_name}</strong>,</p>
    <p>Your project evaluation has been completed by <strong>{reviewer}</strong>.</p>

    <div class="feedback-box">
      "{feedback}"
    </div>

    {score_bars_html}

    <div class="section-title" style="color: #059669;">✅ Key Strengths Observed:</div>
    <ul>
      {strengths_html}
    </ul>

    <div class="section-title" style="color: #2563eb;">🎯 Actionable Recommendations:</div>
    <ul>
      {recs_html}
    </ul>
  </div>
  <div class="footer">
    Continuous Project Review System • Confidential & Intended for {intern_email}
  </div>
</div>
</body>
</html>
"""
    return {"subject": subject, "plain_text": plain_text, "html": html, "recipient": intern_email}


# -------------------------------------------------------------
# Dispatcher & Safety Wrapper
# -------------------------------------------------------------

def send_email_message(
    recipient: str,
    subject: str,
    html_content: str,
    plain_content: str,
    template_type: str = "Notification",
    allow_live_send: bool = False
) -> Tuple[bool, str]:
    """
    Dispatch or simulate email sending.
    Default: Safely logs and simulates without contacting SMTP server.
    Only dispatches live if allow_live_send is explicitly True AND simulation_mode is disabled.
    """
    smtp_cfg = get_smtp_config()
    is_simulation = smtp_cfg["simulation_mode"] or not allow_live_send

    if is_simulation:
        # Safe simulation mode
        preview_snip = f"Subject: {subject}\nTo: {recipient}\n\n{plain_content[:300]}..."
        log_email(
            recipient=recipient,
            subject=subject,
            template_type=template_type,
            body_preview=preview_snip,
            status="Simulated (Safe Mode)",
            simulated=True
        )
        return True, f"✅ Email simulated successfully! (Safe Simulation Mode active - no live email sent. Recipient: {recipient})"

    # User explicitly allowed live send and simulation mode is off
    if not smtp_cfg["is_configured"]:
        err_msg = "Cannot send live email: SMTP credentials (SMTP_HOST, SMTP_USER, SMTP_PASSWORD) are not configured."
        log_email(
            recipient=recipient,
            subject=subject,
            template_type=template_type,
            body_preview=plain_content[:300],
            status="Failed",
            simulated=False,
            error_message=err_msg
        )
        return False, err_msg

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{smtp_cfg['from_name']} <{smtp_cfg['from_email']}>"
        msg["To"] = recipient

        msg.attach(MIMEText(plain_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        if smtp_cfg["use_tls"]:
            server = smtplib.SMTP(smtp_cfg["host"], smtp_cfg["port"], timeout=15)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(smtp_cfg["host"], smtp_cfg["port"], timeout=15)

        server.login(smtp_cfg["user"], os.getenv("SMTP_PASSWORD", ""))
        server.sendmail(smtp_cfg["from_email"], [recipient], msg.as_string())
        server.quit()

        log_email(
            recipient=recipient,
            subject=subject,
            template_type=template_type,
            body_preview=plain_content[:300],
            status="Sent",
            simulated=False
        )
        return True, f"✅ Live email successfully sent to {recipient} via {smtp_cfg['host']}!"

    except Exception as e:
        err_msg = f"SMTP transmission failed: {str(e)}"
        log_email(
            recipient=recipient,
            subject=subject,
            template_type=template_type,
            body_preview=plain_content[:300],
            status="Failed",
            simulated=False,
            error_message=err_msg
        )
        return False, err_msg


def test_smtp_connection() -> Tuple[bool, str]:
    """Test SMTP handshake and authentication without sending an email."""
    cfg = get_smtp_config()
    if not cfg["is_configured"]:
        return False, "SMTP is not fully configured. Please provide SMTP_HOST, SMTP_USER, and SMTP_PASSWORD in .env."

    try:
        if cfg["use_tls"]:
            server = smtplib.SMTP(cfg["host"], cfg["port"], timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(cfg["host"], cfg["port"], timeout=10)

        server.login(cfg["user"], os.getenv("SMTP_PASSWORD", ""))
        server.quit()
        return True, f"Successfully connected and authenticated with {cfg['host']}:{cfg['port']}!"
    except Exception as e:
        return False, f"SMTP Connection Test Failed: {str(e)}"
