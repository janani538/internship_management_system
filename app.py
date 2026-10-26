"""
AI-Powered Internship Management & Continuous Project Review System
Main Streamlit Application
"""

import os
import json
from datetime import datetime, date, timedelta
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

# Import project modules
from database import (
    init_db, seed_sample_data, get_system_kpis,
    get_all_interns, get_intern_by_id, add_intern, update_intern, delete_intern,
    get_all_tasks, get_task_by_id, add_task, update_task, delete_task,
    assign_task, get_assigned_tasks, get_assignment_by_id, update_assignment_status,
    add_submission, get_submissions, get_latest_submission,
    schedule_review, complete_review, save_ai_automated_review, get_reviews,
    get_email_logs
)
from excel_handler import (
    create_sample_excel_template, parse_and_validate_excel,
    import_excel_to_database, export_database_to_excel
)
from github_analyzer import inspect_repository, parse_github_url
from ai_service import (
    get_ai_config, explain_task_in_simple_terms,
    chat_with_task_assistant, analyze_repository_against_task
)
from email_service import (
    get_smtp_config, generate_task_assignment_email,
    generate_review_scheduled_email, generate_evaluation_feedback_email,
    send_email_message, test_smtp_connection
)

load_dotenv()

# Streamlit Page Setup
st.set_page_config(
    page_title="AI Internship Review System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

def render_voice_over_player(text_to_speak: str, player_id: str = "voice_player", title: str = "AI Voice-Over Narration"):
    """Render a modern interactive text-to-speech audio voice-over player."""
    import re
    # Clean markdown and symbols for natural human speech
    clean_text = re.sub(r'[*#_`\[\]\(\)>~-]', ' ', text_to_speak)
    clean_text = ' '.join(clean_text.split())
    speech_payload = clean_text[:2500]

    html_code = f"""
    <div style="margin: 10px 0 16px 0; padding: 12px 18px; background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%); border: 1px solid #a7f3d0; border-radius: 10px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 4px rgba(0,0,0,0.03);">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 20px;">🔊</span>
            <span style="font-weight: 600; color: #065f46; font-size: 14px;">{title}</span>
        </div>
        <div style="display: flex; gap: 8px;">
            <button id="play_{player_id}" onclick="startSpeech_{player_id}()" style="background: #059669; color: white; border: none; padding: 6px 14px; border-radius: 6px; font-weight: 600; font-size: 13px; cursor: pointer; transition: background 0.2s;">▶ Play Voice</button>
            <button id="pause_{player_id}" onclick="pauseSpeech_{player_id}()" style="background: #e2e8f0; color: #334155; border: none; padding: 6px 12px; border-radius: 6px; font-weight: 600; font-size: 13px; cursor: pointer;">⏸ Pause</button>
            <button id="stop_{player_id}" onclick="stopSpeech_{player_id}()" style="background: #ffffff; color: #64748b; border: 1px solid #cbd5e1; padding: 6px 12px; border-radius: 6px; font-weight: 600; font-size: 13px; cursor: pointer;">⏹ Stop</button>
        </div>
    </div>
    <script>
    let synth = window.speechSynthesis;
    let utterance_{player_id} = null;

    function startSpeech_{player_id}() {{
        synth.cancel();
        const text = {json.dumps(speech_payload)};
        utterance_{player_id} = new SpeechSynthesisUtterance(text);
        utterance_{player_id}.rate = 1.0;
        utterance_{player_id}.pitch = 1.0;
        synth.speak(utterance_{player_id});
    }}

    function pauseSpeech_{player_id}() {{
        if (synth.speaking && !synth.paused) {{
            synth.pause();
        }} else if (synth.paused) {{
            synth.resume();
        }}
    }}

    function stopSpeech_{player_id}() {{
        synth.cancel();
    }}
    </script>
    """
    st.components.v1.html(html_code, height=62)


# Custom High-Aesthetic Styling
st.markdown("""
<style>
    /* Global Styles & Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Top Header Hero */
    .app-hero {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 50%, #06b6d4 100%);
        padding: 24px 30px;
        border-radius: 14px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.25);
    }
    .app-hero h1 {
        margin: 0;
        font-size: 26px;
        font-weight: 800;
        letter-spacing: -0.5px;
        color: #ffffff !important;
    }
    .app-hero p {
        margin: 6px 0 0 0;
        opacity: 0.92;
        font-size: 14px;
        font-weight: 400;
    }
    
    /* KPI Metric Cards */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }
    .kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .kpi-title {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        color: #64748b;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 800;
        color: #0f172a;
        line-height: 1.1;
    }
    .kpi-badge {
        display: inline-block;
        font-size: 11px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 12px;
        margin-top: 6px;
    }
    
    /* Status Badges */
    .badge-assigned { background: #e0f2fe; color: #0369a1; }
    .badge-in-progress { background: #fef3c7; color: #b45309; }
    .badge-submitted { background: #ede9fe; color: #6d28d9; }
    .badge-under-review { background: #ffedd5; color: #c2410c; }
    .badge-completed { background: #dcfce7; color: #15803d; }
    .badge-needs-revision { background: #fee2e2; color: #b91c1c; }
    
    /* Grade Badges */
    .grade-badge {
        font-size: 22px;
        font-weight: 800;
        padding: 6px 16px;
        border-radius: 8px;
        display: inline-block;
        text-align: center;
    }
    .grade-a { background: #dcfce7; color: #166534; border: 1px solid #86efac; }
    .grade-b { background: #e0f2fe; color: #075985; border: 1px solid #7dd3fc; }
    .grade-c { background: #fef3c7; color: #854d0e; border: 1px solid #fde047; }
    .grade-rev { background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5; }

    /* AI Chat Bubbles */
    .chat-user {
        background: #f1f5f9;
        border-radius: 12px 12px 2px 12px;
        padding: 12px 16px;
        margin: 8px 0;
        font-size: 14px;
        border: 1px solid #e2e8f0;
    }
    .chat-assistant {
        background: #eff6ff;
        border-left: 4px solid #3b82f6;
        border-radius: 2px 12px 12px 12px;
        padding: 14px 18px;
        margin: 8px 0;
        font-size: 14px;
        border-top: 1px solid #dbeafe;
        border-right: 1px solid #dbeafe;
        border-bottom: 1px solid #dbeafe;
    }
</style>
""", unsafe_allow_html=True)


# Initialize DB on load
@st.cache_resource
def bootstrap_system():
    init_db()
    seed_sample_data()
    return True

bootstrap_system()


# -------------------------------------------------------------
# Sidebar Navigation & System Diagnostics
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎓 Internship Portal")
    st.caption("AI-Powered Continuous Review System")
    
    menu = st.radio(
        "Navigation",
        [
            "📊 Dashboard & KPIs",
            "👥 Interns & Tasks",
            "📥 Excel Data Hub",
            "💡 AI Task Assistant",
            "🚀 GitHub Submission",
            "🔍 AI Code Review & Grading",
            "📅 Review Scheduler & History",
            "✉️ Email Previews & Dispatch",
            "⚙️ Settings & Secrets"
        ],
        index=0
    )

    st.markdown("---")
    
    # System Status Indicators in Sidebar
    ai_status = get_ai_config()
    smtp_status = get_smtp_config()

    st.markdown("**System Health & Mode**")
    
    # AI Indicator
    if ai_status["active_provider"] == "gemini":
        st.success("🤖 AI: Google Gemini (Active)")
    elif ai_status["active_provider"] == "openai":
        st.success("🤖 AI: OpenAI GPT (Active)")
    else:
        st.info("🧠 AI: Heuristic Mentor (Offline Ready)")

    # Email Indicator
    if smtp_status["simulation_mode"]:
        st.warning("🛡️ Email: Safe Simulation Mode")
    else:
        st.success("✉️ Email: Live SMTP Dispatch")

    st.caption("Database: SQLite Connected (`internship_system.db`)")


# -------------------------------------------------------------
# PAGE 1: 📊 DASHBOARD & KPIS
# -------------------------------------------------------------
if menu == "📊 Dashboard & KPIs":
    st.markdown("""
    <div class="app-hero">
        <h1>📊 Internship Program Dashboard</h1>
        <p>Continuous monitoring, automated code evaluations, and milestone progress tracking</p>
    </div>
    """, unsafe_allow_html=True)

    kpis = get_system_kpis()

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Interns", kpis["total_interns"])
    with col2:
        st.metric("Active Tasks", kpis["total_tasks"])
    with col3:
        st.metric("Submissions", kpis["total_submissions"])
    with col4:
        st.metric("Reviews Completed", kpis["completed_reviews"])
    with col5:
        st.metric("Cohort Avg Score", f"{kpis['avg_score']}/100" if kpis["avg_score"] > 0 else "N/A")

    if kpis["overdue_count"] > 0:
        st.warning(f"⚠️ **Attention Required**: {kpis['overdue_count']} assignment(s) are currently past their due date.")

    st.markdown("### 📈 Cohort Progress & Status Distribution")
    col_chart1, col_chart2 = st.columns(2)

    status_counts = kpis.get("status_counts", {})
    if status_counts:
        df_status = pd.DataFrame([{"Status": k, "Count": v} for k, v in status_counts.items()])
        with col_chart1:
            fig_pie = px.pie(
                df_status,
                names="Status",
                values="Count",
                title="Task Assignment Status Breakdown",
                color_discrete_sequence=px.colors.qualitative.Pastel,
                hole=0.45
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(margin=dict(t=40, b=10, l=10, r=10))
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        with col_chart1:
            st.info("No active assignments yet.")

    with col_chart2:
        reviews = get_reviews(status="Completed")
        if reviews:
            scores = [r["score"] for r in reviews if r.get("score") is not None]
            df_scores = pd.DataFrame({"Score": scores})
            fig_hist = px.histogram(
                df_scores,
                x="Score",
                nbins=10,
                title="Review Score Distribution",
                color_discrete_sequence=["#3b82f6"]
            )
            fig_hist.update_layout(xaxis_title="Score (0-100)", yaxis_title="Reviews Count", margin=dict(t=40, b=10, l=10, r=10))
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("No completed reviews yet to graph score distribution.")

    st.markdown("### 📋 Recent Review Activity & Upcoming Reviews")
    recent_reviews = get_reviews()[:8]
    if recent_reviews:
        display_data = []
        for r in recent_reviews:
            display_data.append({
                "Intern": f"{r['intern_name']} ({r['intern_code']})",
                "Task": r['task_title'],
                "Reviewer": r['reviewer'],
                "Type": r['review_type'],
                "Status": r['status'],
                "Score": f"{r['score']} ({r['grade']})" if r.get('score') is not None else "Pending",
                "Scheduled / Completed": r.get('completed_at') or r.get('scheduled_at') or r.get('created_at')
            })
        st.dataframe(pd.DataFrame(display_data), use_container_width=True, hide_index=True)
    else:
        st.info("No reviews recorded yet.")


# -------------------------------------------------------------
# PAGE 2: 👥 INTERNS & TASKS MANAGEMENT
# -------------------------------------------------------------
elif menu == "👥 Interns & Tasks":
    st.markdown("""
    <div class="app-hero">
        <h1>👥 Manage Interns & Project Tasks</h1>
        <p>Maintain intern roster, task catalog, and monitor individual assignment milestones</p>
    </div>
    """, unsafe_allow_html=True)

    tab_interns, tab_tasks, tab_assign = st.tabs(["👨‍🎓 Intern Directory", "📑 Task Catalog", "📌 Task Assignments"])

    # TAB 1: Intern Directory
    with tab_interns:
        col_hdr1, col_hdr2 = st.columns([3, 1])
        with col_hdr1:
            search_intern = st.text_input("🔍 Search Interns (by name, code, domain, or mentor):", "")
        with col_hdr2:
            st.write("")
            st.write("")
            show_add_intern = st.checkbox("➕ Add New Intern")

        if show_add_intern:
            with st.form("form_add_intern"):
                st.subheader("Register New Intern")
                f_code = st.text_input("Intern Code *", f"INT-2024-{len(get_all_interns()) + 101:03d}")
                f_name = st.text_input("Full Name *", "")
                f_email = st.text_input("Email Address *", "")
                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    f_dept = st.text_input("Department", "Engineering")
                    f_domain = st.selectbox("Technical Track / Domain", ["Full Stack Development", "Machine Learning & AI", "Cloud Infrastructure", "Data Science", "Cybersecurity", "Mobile Development"])
                with col_f2:
                    f_mentor = st.text_input("Assigned Mentor", "Dr. Priya Nair")
                
                btn_save_intern = st.form_submit_button("Save Intern Record")
                if btn_save_intern:
                    if f_code and f_name and f_email:
                        add_intern(f_code, f_name, f_email, f_dept, f_domain, f_mentor)
                        st.success(f"Intern {f_name} ({f_code}) added successfully!")
                        st.rerun()
                    else:
                        st.error("Please fill in all mandatory fields (Code, Name, Email).")

        all_interns = get_all_interns()
        if search_intern:
            q = search_intern.lower()
            all_interns = [i for i in all_interns if q in i["name"].lower() or q in i["intern_code"].lower() or q in i.get("domain", "").lower() or q in i.get("mentor", "").lower()]

        if all_interns:
            df_interns = pd.DataFrame(all_interns)
            st.dataframe(
                df_interns[["intern_code", "name", "email", "domain", "department", "mentor", "assigned_tasks_count", "completed_tasks_count"]],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No intern records found matching criteria.")

    # TAB 2: Task Catalog
    with tab_tasks:
        col_thdr1, col_thdr2 = st.columns([3, 1])
        with col_thdr1:
            search_task = st.text_input("🔍 Search Task Catalog:", "")
        with col_thdr2:
            st.write("")
            st.write("")
            show_add_task = st.checkbox("➕ Add New Task")

        if show_add_task:
            with st.form("form_add_task"):
                st.subheader("Define New Project Task")
                t_code = st.text_input("Task Code *", f"TSK-{len(get_all_tasks()) + 201:03d}")
                t_title = st.text_input("Task Title *", "")
                t_domain = st.selectbox("Track / Domain", ["Full Stack Development", "Machine Learning & AI", "Cloud Infrastructure", "Data Science", "Cybersecurity", "Mobile Development"])
                t_desc = st.text_area("Task Description & Background *", "")
                t_reqs = st.text_area("Key Deliverables / Requirements (bulleted)", "- Deliverable 1\n- Deliverable 2\n- Deliverable 3")
                t_rubric = st.text_area("Evaluation Rubric & Weightage", "- Code Quality & Architecture: 25%\n- Requirement Fulfillment: 25%\n- Testing & Coverage: 25%\n- Documentation & Setup: 25%")
                t_days = st.number_input("Standard Deadline (Days)", min_value=1, max_value=90, value=14)

                btn_save_task = st.form_submit_button("Create Task")
                if btn_save_task:
                    if t_code and t_title and t_desc:
                        add_task(t_code, t_title, t_domain, t_desc, t_reqs, t_rubric, t_days)
                        st.success(f"Task {t_code}: {t_title} added successfully!")
                        st.rerun()
                    else:
                        st.error("Please fill in Code, Title, and Description.")

        tasks = get_all_tasks()
        if search_task:
            tq = search_task.lower()
            tasks = [t for t in tasks if tq in t["title"].lower() or tq in t["task_code"].lower() or tq in t.get("domain", "").lower()]

        for t in tasks:
            with st.expander(f"📌 {t['task_code']}: {t['title']} ({t['domain']})"):
                st.write(f"**Description**: {t['description']}")
                st.markdown(f"**Requirements**:\n{t['requirements']}")
                st.markdown(f"**Evaluation Rubric**:\n{t['rubric']}")
                st.caption(f"Standard Deadline: {t['deadline_days']} days | Assigned to {t.get('assigned_count', 0)} intern(s)")

    # TAB 3: Task Assignments
    with tab_assign:
        st.subheader("Assign Tasks & Manage Lifecycle")
        
        with st.expander("➕ Assign Task to an Intern"):
            interns_list = get_all_interns()
            tasks_list = get_all_tasks()
            
            if interns_list and tasks_list:
                with st.form("form_assign_task"):
                    intern_options = {f"{i['name']} ({i['intern_code']}) - {i['domain']}": i["id"] for i in interns_list}
                    task_options = {f"{t['task_code']}: {t['title']} ({t['domain']})": t["id"] for t in tasks_list}
                    
                    sel_intern = st.selectbox("Select Intern", list(intern_options.keys()))
                    sel_task = st.selectbox("Select Task to Assign", list(task_options.keys()))
                    due_date_input = st.date_input("Due Date", date.today() + timedelta(days=14))
                    assign_notes = st.text_input("Assignment Notes", "Standard milestone assignment")
                    
                    btn_assign = st.form_submit_button("Confirm Task Assignment")
                    if btn_assign:
                        i_id = intern_options[sel_intern]
                        t_id = task_options[sel_task]
                        assign_task(i_id, t_id, due_date=due_date_input.isoformat(), notes=assign_notes)
                        st.success("Task assigned successfully!")
                        st.rerun()
            else:
                st.info("Ensure both interns and tasks exist before creating assignments.")

        st.markdown("#### Current Task Assignments")
        filter_status = st.selectbox("Filter by Status", ["All", "Assigned", "In Progress", "Submitted", "Under Review", "Completed", "Needs Revision"])
        assignments = get_assigned_tasks(status=filter_status)
        
        if assignments:
            df_ass = pd.DataFrame(assignments)
            cols_show = ["assignment_id", "intern_code", "intern_name", "task_code", "task_title", "assignment_status", "assigned_date", "due_date", "submission_count", "latest_score"]
            st.dataframe(df_ass[cols_show], use_container_width=True, hide_index=True)
            
            # Quick status update
            st.markdown("##### ⚡ Quick Status Update")
            col_u1, col_u2, col_u3 = st.columns([2, 2, 1])
            with col_u1:
                assign_dict = {f"ID #{a['assignment_id']} - {a['intern_name']} - {a['task_title']} ({a['assignment_status']})": a['assignment_id'] for a in assignments}
                sel_assign_str = st.selectbox("Select Assignment", list(assign_dict.keys()), key="quick_up_assign")
            with col_u2:
                new_st = st.selectbox("New Status", ["Assigned", "In Progress", "Submitted", "Under Review", "Completed", "Needs Revision"], key="quick_up_st")
            with col_u3:
                st.write("")
                st.write("")
                if st.button("Update Status"):
                    update_assignment_status(assign_dict[sel_assign_str], new_st)
                    st.success("Status updated!")
                    st.rerun()
        else:
            st.info("No assignments match the selected status.")


# -------------------------------------------------------------
# PAGE 3: 📥 EXCEL DATA HUB
# -------------------------------------------------------------
elif menu == "📥 Excel Data Hub":
    st.markdown("""
    <div class="app-hero">
        <h1>📥 Excel Data Import & Export Hub</h1>
        <p>Seamlessly import intern rosters and project requirements from spreadsheets or export complete cohort data</p>
    </div>
    """, unsafe_allow_html=True)

    tab_import, tab_export, tab_template = st.tabs(["📤 Upload & Import Excel", "💾 Export Database to Excel", "📄 Sample Templates & Seeder"])

    # TAB 1: Upload & Import
    with tab_import:
        st.subheader("Import Interns and Tasks from Excel Workbook")
        st.write("Upload an `.xlsx` or `.xls` spreadsheet. You can include both an **Interns** sheet and a **Tasks** sheet, or either.")

        uploaded_file = st.file_uploader("Choose Excel File", type=["xlsx", "xls"])
        if uploaded_file is not None:
            content = uploaded_file.read()
            parsed = parse_and_validate_excel(content)

            if parsed["errors"]:
                for err in parsed["errors"]:
                    st.error(f"❌ {err}")

            if parsed["warnings"]:
                for warn in parsed["warnings"]:
                    st.warning(f"⚠️ {warn}")

            if parsed["success"]:
                st.success(f"Validation Passed! Found **{len(parsed['interns'])}** intern(s) and **{len(parsed['tasks'])}** task(s).")
                
                col_prev1, col_prev2 = st.columns(2)
                with col_prev1:
                    if parsed["interns"]:
                        st.markdown("**Preview Interns to Import:**")
                        st.dataframe(pd.DataFrame(parsed["interns"]), use_container_width=True, hide_index=True)
                with col_prev2:
                    if parsed["tasks"]:
                        st.markdown("**Preview Tasks to Import:**")
                        st.dataframe(pd.DataFrame(parsed["tasks"]), use_container_width=True, hide_index=True)

                if st.button("🚀 Commit Import to Database", type="primary"):
                    summary = import_excel_to_database(parsed)
                    st.success(f"Successfully imported {summary['interns_imported']} interns, {summary['tasks_imported']} tasks, and created {summary['assignments_created']} assignments!")
                    st.rerun()

    # TAB 2: Export Database
    with tab_export:
        st.subheader("Export Current Cohort Records to Excel")
        st.write("Generates an organized multi-sheet Excel file containing all Interns, Tasks, Assignments, and Review records.")
        
        excel_bytes = export_database_to_excel()
        st.download_button(
            label="📥 Download Database as Excel (.xlsx)",
            data=excel_bytes,
            file_name=f"internship_system_export_{date.today().isoformat()}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # TAB 3: Templates & One-Click Demo Seeder
    with tab_template:
        st.subheader("Sample Excel Template & Instant Demonstration Seeder")
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.markdown("#### 1. Download Blank Sample Template")
            st.write("Download an officially formatted Excel template pre-filled with example schema and columns.")
            sample_template = create_sample_excel_template()
            st.download_button(
                label="📄 Download Sample Template (.xlsx)",
                data=sample_template,
                file_name="sample_interns_tasks.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with col_t2:
            st.markdown("#### 2. One-Click Demo Data Population")
            st.write("Instantly populate the SQLite database with 5 interns, 4 realistic software engineering tasks, assignments, and sample GitHub submissions.")
            if st.button("🔄 Populate / Reset Demonstration Data"):
                seed_sample_data(force=True)
                st.success("Demonstration data re-seeded successfully! Head to Dashboard or Interns to view.")
                st.rerun()


# -------------------------------------------------------------
# PAGE 4: 💡 AI TASK ASSISTANT
# -------------------------------------------------------------
elif menu == "💡 AI Task Assistant":
    st.markdown("""
    <div class="app-hero">
        <h1>💡 AI Mentor & Task Assistant</h1>
        <p>Explain complex project requirements in simple language, generate roadmaps, and get guidance</p>
    </div>
    """, unsafe_allow_html=True)

    tasks_list = get_all_tasks()
    if not tasks_list:
        st.info("No tasks available. Please create or import tasks first.")
    else:
        task_map = {f"{t['task_code']}: {t['title']} ({t['domain']})": t for t in tasks_list}
        selected_task_label = st.selectbox("Select Project Task to Explore:", list(task_map.keys()))
        current_task = task_map[selected_task_label]

        tab_explain, tab_chat = st.tabs(["📖 Simple English Explanation & Roadmap", "💬 Interactive Mentor Chat"])

        with tab_explain:
            st.markdown(f"### Task: **{current_task['title']}**")
            
            with st.spinner("Generating plain-English breakdown and roadmap..."):
                explanation_data = explain_task_in_simple_terms(current_task)

            # Voice-Over Narration Player
            render_voice_over_player(
                text_to_speak=explanation_data["markdown_explanation"],
                player_id=f"voice_task_{current_task['id']}",
                title=f"🔊 Listen to Voice-Over: {current_task['title']}"
            )
            
            st.caption(f"Provider: {explanation_data['provider']}")
            st.markdown(explanation_data["markdown_explanation"])

        with tab_chat:
            st.markdown(f"#### Ask questions about: *{current_task['title']}*")
            
            # Initialize chat history in session state
            chat_key = f"chat_{current_task['id']}"
            if chat_key not in st.session_state:
                st.session_state[chat_key] = [
                    {"role": "assistant", "content": f"Hi! I'm your AI Mentor for **{current_task['title']}**. How can I help you? You can ask me how to structure your code, what libraries to use, or how to write unit tests!"}
                ]

            # Display chat messages
            for message in st.session_state[chat_key]:
                if message["role"] == "user":
                    st.markdown(f"<div class='chat-user'><strong>You:</strong> {message['content']}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='chat-assistant'><strong>🤖 AI Mentor:</strong> {message['content']}</div>", unsafe_allow_html=True)

            # Chat input form
            with st.form("chat_form", clear_on_submit=True):
                user_query = st.text_input("Ask a question about this task:", placeholder="e.g. How do I write unit tests for the JWT endpoints?")
                send_chat = st.form_submit_button("Ask Mentor")
                if send_chat and user_query:
                    st.session_state[chat_key].append({"role": "user", "content": user_query})
                    with st.spinner("AI Mentor is typing..."):
                        bot_reply = chat_with_task_assistant(current_task, st.session_state[chat_key][:-1], user_query)
                    st.session_state[chat_key].append({"role": "assistant", "content": bot_reply})
                    st.rerun()


# -------------------------------------------------------------
# PAGE 5: 🚀 GITHUB SUBMISSION PORTAL
# -------------------------------------------------------------
elif menu == "🚀 GitHub Submission":
    st.markdown("""
    <div class="app-hero">
        <h1>🚀 Intern GitHub Submission Portal</h1>
        <p>Submit your project repository URLs for automated continuous review and mentor assessment</p>
    </div>
    """, unsafe_allow_html=True)

    assignments = get_assigned_tasks()
    if not assignments:
        st.info("No active assignments found. Please assign tasks to interns first.")
    else:
        st.subheader("Submit Your Repository")
        
        assign_options = {
            f"{a['intern_name']} ({a['intern_code']}) — {a['task_title']} [Status: {a['assignment_status']}]": a
            for a in assignments
        }
        sel_assign_label = st.selectbox("Select Your Assignment:", list(assign_options.keys()))
        selected_assignment = assign_options[sel_assign_label]

        with st.form("github_submission_form"):
            st.markdown(f"**Task Details**: {selected_assignment['task_title']} ({selected_assignment['task_domain']})")
            st.markdown(f"**Due Date**: `{selected_assignment['due_date']}`")

            github_url = st.text_input("GitHub Repository URL *", placeholder="https://github.com/username/repository", value="")
            branch = st.text_input("Branch Name", value="main")
            submission_notes = st.text_area("Submission Notes (What did you build, known limitations, instructions)", "Implemented core features, verified tests, and added README documentation.")

            btn_submit = st.form_submit_button("🚀 Submit Project Repository", type="primary")

            if btn_submit:
                if not github_url:
                    st.error("Please enter a GitHub repository URL.")
                else:
                    parsed = parse_github_url(github_url)
                    if not parsed:
                        st.error("Invalid GitHub URL format. Please enter a valid URL like: https://github.com/owner/repo")
                    else:
                        owner, repo, _ = parsed
                        sub_id = add_submission(selected_assignment["assignment_id"], github_url, branch, submission_notes)
                        st.success(f"🎉 Submission received successfully for {owner}/{repo}! Assignment marked as 'Submitted'.")
                        st.rerun()

        st.markdown("### 📋 Recent Submissions History")
        subs = get_submissions()
        if subs:
            df_subs = pd.DataFrame(subs)
            cols_to_show = ["id", "intern_code", "intern_name", "task_title", "github_url", "branch", "submitted_at", "status"]
            st.dataframe(df_subs[cols_to_show], use_container_width=True, hide_index=True)
        else:
            st.info("No submissions recorded yet.")


# -------------------------------------------------------------
# PAGE 6: 🔍 AI CODE REVIEW & GRADING
# -------------------------------------------------------------
elif menu == "🔍 AI Code Review & Grading":
    st.markdown("""
    <div class="app-hero">
        <h1>🔍 Continuous AI Code Review & Evidence Analysis</h1>
        <p>Inspect repository contents, verify code deliverables against task rubric, and produce evidence-grounded reports</p>
    </div>
    """, unsafe_allow_html=True)

    submissions = get_submissions()
    if not submissions:
        st.info("No submissions found yet. Submit a GitHub repository first from the 'GitHub Submission' page.")
    else:
        sub_map = {
            f"Sub #{s['id']}: {s['intern_name']} ({s['intern_code']}) — {s['task_title']} [{s['github_url']}]": s
            for s in submissions
        }
        selected_sub_label = st.selectbox("Select Project Submission to Evaluate:", list(sub_map.keys()))
        selected_sub = sub_map[selected_sub_label]

        # Fetch associated task details
        task_info = get_task_by_id(selected_sub["task_id"])

        col_meta1, col_meta2 = st.columns([3, 1])
        with col_meta1:
            st.markdown(f"**Intern**: {selected_sub['intern_name']} ({selected_sub['intern_email']})")
            st.markdown(f"**Task**: {selected_sub['task_title']}")
            st.markdown(f"**Repository**: [{selected_sub['github_url']}]({selected_sub['github_url']}) (Branch: `{selected_sub['branch']}`)")
        with col_meta2:
            st.write("")
            btn_run_review = st.button("⚡ Run AI Continuous Evaluation", type="primary")

        # Session state key for this review
        review_cache_key = f"review_result_{selected_sub['id']}"

        if btn_run_review or review_cache_key in st.session_state:
            if btn_run_review:
                with st.spinner("🔍 Fetching GitHub repository files, commits, and README..."):
                    repo_inspection = inspect_repository(selected_sub["github_url"], selected_sub["branch"])

                if not repo_inspection["success"]:
                    st.error(f"❌ Could not inspect repository: {repo_inspection.get('error')}")
                else:
                    with st.spinner("🤖 Analyzing repository contents against rubric and task requirements..."):
                        evaluation = analyze_repository_against_task(task_info, repo_inspection)
                        st.session_state[review_cache_key] = {
                            "evaluation": evaluation,
                            "inspection": repo_inspection
                        }

            if review_cache_key in st.session_state:
                eval_res = st.session_state[review_cache_key]["evaluation"]
                inspect_res = st.session_state[review_cache_key]["inspection"]

                st.markdown("---")
                st.subheader("📋 Evaluation Scorecard & Evidence Report")

                score = eval_res.get("overall_score", 0)
                grade = eval_res.get("letter_grade", "Needs Revision")

                # Scorecard Banner
                grade_class = "grade-a" if score >= 80 else ("grade-b" if score >= 70 else ("grade-c" if score >= 60 else "grade-rev"))
                
                col_score1, col_score2, col_score3 = st.columns([1, 2, 2])
                with col_score1:
                    st.markdown(f"""
                    <div style="text-align: center; padding: 16px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px;">
                        <div style="font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase;">Overall Score</div>
                        <div style="font-size: 42px; font-weight: 800; color: #0f172a;">{score:.0f}<span style="font-size: 20px; color: #94a3b8;">/100</span></div>
                        <div class="grade-badge {grade_class}">{grade}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_score2:
                    st.markdown("**Rubric Category Breakdown:**")
                    cat_scores = eval_res.get("category_scores", {})
                    max_cats = eval_res.get("max_category_scores", {"requirement_coverage": 30, "code_quality": 25, "documentation": 20, "testing": 15, "git_hygiene": 10})
                    for k, v in cat_scores.items():
                        mx = max_cats.get(k, 25)
                        pct = v / mx if mx else 0
                        label = k.replace('_', ' ').title()
                        st.write(f"• **{label}**: {v} / {mx} pts")
                        st.progress(min(1.0, max(0.0, pct)))

                with col_score3:
                    st.markdown("**Repository Metrics Discovered:**")
                    st.write(f"• Total Files: **{inspect_res.get('file_count', 0)}**")
                    st.write(f"• README Found: **{'✅ Yes (' + str(inspect_res.get('readme', {}).get('length', 0)) + ' chars)' if inspect_res.get('readme', {}).get('found') else '❌ Missing'}**")
                    st.write(f"• Test Files: **{len(inspect_res.get('test_files', []))}** ({', '.join(inspect_res.get('test_files', [])[:2]) if inspect_res.get('test_files') else 'None'})")
                    st.write(f"• Dependencies: **{', '.join(inspect_res.get('dependency_files', {}).keys()) or 'None'}**")
                    st.write(f"• Recent Commits Reviewed: **{len(inspect_res.get('commits', []))}**")

                if eval_res.get("executive_summary"):
                    st.info(f"**Executive Summary**: {eval_res['executive_summary']}")

                # Voice-Over Narration for Review
                voice_review_text = f"Evaluation result for {selected_sub['task_title']}. Overall score is {score:.0f} points out of 100, receiving a grade of {grade}. {eval_res.get('executive_summary', '')}. "
                if eval_res.get('evidence_found'):
                    voice_review_text += "Strengths identified include: " + ", ".join(eval_res['evidence_found'][:2]) + ". "
                if eval_res.get('recommendations'):
                    voice_review_text += "Key recommendations: " + ", ".join(eval_res['recommendations'][:2]) + "."
                render_voice_over_player(voice_review_text, player_id=f"voice_eval_{selected_sub['id']}", title=f"🔊 Listen to Evaluation Voice-Over ({grade} - {score:.0f}/100)")

                col_rep1, col_rep2 = st.columns(2)
                with col_rep1:
                    st.markdown("#### ✅ Concrete Evidence Found")
                    for s in eval_res.get("evidence_found", []):
                        st.markdown(f"- {s}")
                    
                    if eval_res.get("deficiencies"):
                        st.markdown("#### ⚠️ Identified Gaps / Missing Items")
                        for d in eval_res.get("deficiencies", []):
                            st.markdown(f"- {d}")

                with col_rep2:
                    st.markdown("#### 🎯 Actionable Recommendations for Intern")
                    for r in eval_res.get("recommendations", []):
                        st.markdown(f"- {r}")

                st.markdown("---")
                st.subheader("💾 Commit Review to Official History")
                with st.form(f"save_review_form_{selected_sub['id']}"):
                    rev_feedback = st.text_area("Official Mentor Feedback", f"Automated AI Review. Grade: {grade} ({score}/100). {eval_res.get('executive_summary', '')}")
                    reviewer_name = st.text_input("Reviewer Name", "AI Continuous Reviewer & Mentor")
                    save_btn = st.form_submit_button("Save and Record Review to Database", type="primary")

                    if save_btn:
                        save_ai_automated_review(
                            intern_task_id=selected_sub["intern_task_id"],
                            submission_id=selected_sub["id"],
                            reviewer=reviewer_name,
                            score=score,
                            grade=grade,
                            feedback=rev_feedback,
                            ai_analysis=eval_res
                        )
                        st.success("Review recorded into official history and assignment status updated!")
                        st.rerun()


# -------------------------------------------------------------
# PAGE 7: 📅 REVIEW SCHEDULER & HISTORY
# -------------------------------------------------------------
elif menu == "📅 Review Scheduler & History":
    st.markdown("""
    <div class="app-hero">
        <h1>📅 Project Review Scheduler & History</h1>
        <p>Coordinate milestone reviews, schedule video evaluations, and audit complete feedback records</p>
    </div>
    """, unsafe_allow_html=True)

    tab_sched, tab_hist = st.tabs(["🗓️ Schedule New Review", "📜 Review History & Scorecards"])

    # TAB 1: Schedule Review
    with tab_sched:
        st.subheader("Schedule Project Evaluation")
        assignments = get_assigned_tasks()
        
        if assignments:
            with st.form("schedule_review_form"):
                assign_dict = {
                    f"{a['intern_name']} ({a['intern_code']}) — {a['task_title']} [{a['assignment_status']}]": a
                    for a in assignments
                }
                sel_assign_str = st.selectbox("Select Intern & Task:", list(assign_dict.keys()))
                chosen_assign = assign_dict[sel_assign_str]

                col_sc1, col_sc2 = st.columns(2)
                with col_sc1:
                    reviewer = st.text_input("Reviewer / Mentor Name *", chosen_assign.get("intern_mentor") or "Dr. Priya Nair")
                    review_type = st.selectbox("Review Type", ["Milestone Code Review", "Mid-term Evaluation", "Final Project Defense", "Automated AI Review"])
                with col_sc2:
                    sched_date = st.date_input("Review Date", date.today() + timedelta(days=2))
                    sched_time = st.time_input("Review Time", datetime.strptime("14:30", "%H:%M").time())
                    meeting_link = st.text_input("Meeting Link", "https://meet.google.com/abc-defg-hij")

                btn_schedule = st.form_submit_button("Confirm Scheduled Review", type="primary")

                if btn_schedule:
                    combined_dt = f"{sched_date.isoformat()} {sched_time.strftime('%H:%M')}"
                    latest_sub = get_latest_submission(chosen_assign["assignment_id"])
                    sub_id = latest_sub["id"] if latest_sub else None
                    schedule_review(
                        intern_task_id=chosen_assign["assignment_id"],
                        reviewer=reviewer,
                        review_type=review_type,
                        scheduled_at=combined_dt,
                        meeting_link=meeting_link,
                        submission_id=sub_id
                    )
                    st.success(f"Review scheduled for {chosen_assign['intern_name']} on {combined_dt}!")
                    st.rerun()
        else:
            st.info("No active assignments available to schedule reviews for.")

    # TAB 2: Review History
    with tab_hist:
        st.subheader("Historical Review Log & Evidence Reports")
        filter_rev_status = st.selectbox("Filter Review Status", ["All", "Scheduled", "Completed"])
        all_reviews = get_reviews(status=filter_rev_status)

        if all_reviews:
            for r in all_reviews:
                with st.expander(f"Review #{r['id']} — {r['intern_name']} ({r['intern_code']}) | {r['task_title']} — {r['status']}"):
                    col_r1, col_r2 = st.columns([2, 1])
                    with col_r1:
                        st.write(f"**Review Type**: {r['review_type']}")
                        st.write(f"**Reviewer**: {r['reviewer']}")
                        st.write(f"**Scheduled At**: {r.get('scheduled_at') or 'N/A'}")
                        if r.get("completed_at"):
                            st.write(f"**Completed At**: {r['completed_at']}")
                        if r.get("meeting_link"):
                            st.write(f"**Meeting Link**: [Join Call]({r['meeting_link']})")
                        st.write(f"**Feedback**: {r.get('feedback') or 'No feedback text.'}")

                    with col_r2:
                        if r.get("score") is not None:
                            st.metric("Score", f"{r['score']}/100", r.get("grade", ""))
                        if r.get("github_url"):
                            st.write(f"**Repository**: [{r['github_url']}]({r['github_url']})")

                    if r.get("ai_analysis"):
                        ai_data = r["ai_analysis"]
                        st.markdown("**Evidence-Based Analysis Breakdown:**")
                        cat_sc = ai_data.get("category_scores", {})
                        if cat_sc:
                            st.json(cat_sc)
                        if ai_data.get("evidence_found"):
                            st.markdown("*Strengths*: " + ", ".join(ai_data["evidence_found"][:3]))
                        if ai_data.get("recommendations"):
                            st.markdown("*Recommendations*: " + ", ".join(ai_data["recommendations"][:3]))

                    # If scheduled, allow marking as complete
                    if r["status"] == "Scheduled":
                        st.markdown("---")
                        st.markdown("##### Complete this Review")
                        with st.form(f"complete_review_{r['id']}"):
                            c_score = st.slider("Evaluation Score", 0.0, 100.0, 80.0, key=f"score_slider_{r['id']}")
                            c_grade = "A+" if c_score >= 90 else ("A" if c_score >= 80 else ("B" if c_score >= 70 else ("C" if c_score >= 60 else "Needs Revision")))
                            c_feedback = st.text_area("Evaluation Feedback", "Completed live code demonstration and reviewed task requirements.", key=f"fb_area_{r['id']}")
                            btn_comp = st.form_submit_button("Mark Review Completed")
                            if btn_comp:
                                complete_review(r["id"], c_score, c_grade, c_feedback)
                                st.success("Review marked as completed!")
                                st.rerun()
        else:
            st.info("No reviews match the selected filter.")


# -------------------------------------------------------------
# PAGE 8: ✉️ EMAIL NOTIFICATIONS & SMTP
# -------------------------------------------------------------
elif menu == "✉️ Email Previews & Dispatch":
    st.markdown("""
    <div class="app-hero">
        <h1>✉️ Email Notifications & SMTP Gateway</h1>
        <p>Generate responsive HTML notifications, preview messages, and safely dispatch or simulate emails</p>
    </div>
    """, unsafe_allow_html=True)

    smtp_cfg = get_smtp_config()
    
    # Simulation safety alert
    if smtp_cfg["simulation_mode"]:
        st.info("🛡️ **Safety Mode Active**: `EMAIL_SIMULATION_MODE=True`. All email actions will be logged and simulated safely. No actual emails will be sent.")
    else:
        st.warning("⚠️ **Live Dispatch Active**: Real emails will be sent via your configured SMTP host upon confirmation.")

    tab_compose, tab_logs = st.tabs(["✉️ Email Composer & Live Preview", "📑 Dispatch Audit Logs"])

    with tab_compose:
        interns = get_all_interns()
        tasks = get_all_tasks()

        if not interns or not tasks:
            st.info("Ensure interns and tasks exist to preview emails.")
        else:
            col_sel1, col_sel2 = st.columns(2)
            with col_sel1:
                template_choice = st.selectbox(
                    "Select Email Template:",
                    [
                        "1. Task Assignment Notification",
                        "2. Project Review Scheduled",
                        "3. Code Review & Evaluation Scorecard"
                    ]
                )
            with col_sel2:
                intern_dict = {f"{i['name']} ({i['email']})": i for i in interns}
                sel_intern_key = st.selectbox("Select Recipient Intern:", list(intern_dict.keys()))
                current_intern = intern_dict[sel_intern_key]

            # Generate preview content
            email_payload = None
            if "Task Assignment" in template_choice:
                task_dict = {f"{t['task_code']}: {t['title']}": t for t in tasks}
                sel_task_key = st.selectbox("Select Task:", list(task_dict.keys()))
                task_obj = task_dict[sel_task_key]
                due_str = (date.today() + timedelta(days=14)).isoformat()
                email_payload = generate_task_assignment_email(current_intern, task_obj, due_str)
                email_payload["template_type"] = "Task Assignment"

            elif "Review Scheduled" in template_choice:
                task_dict = {f"{t['task_code']}: {t['title']}": t for t in tasks}
                sel_task_key = st.selectbox("Select Task:", list(task_dict.keys()))
                task_obj = task_dict[sel_task_key]
                review_obj = {
                    "reviewer": current_intern.get("mentor") or "Dr. Priya Nair",
                    "review_type": "Milestone Code Review",
                    "scheduled_at": (datetime.now() + timedelta(days=2)).strftime("%A, %b %d at 3:00 PM"),
                    "meeting_link": "https://meet.google.com/xyz-intern-review"
                }
                email_payload = generate_review_scheduled_email(current_intern, task_obj, review_obj)
                email_payload["template_type"] = "Review Scheduled"

            elif "Scorecard" in template_choice:
                task_dict = {f"{t['task_code']}: {t['title']}": t for t in tasks}
                sel_task_key = st.selectbox("Select Task:", list(task_dict.keys()))
                task_obj = task_dict[sel_task_key]
                review_obj = {
                    "score": 92.0,
                    "grade": "A+",
                    "reviewer": current_intern.get("mentor") or "Dr. Priya Nair",
                    "feedback": "Outstanding work on this milestone! Clean code architecture and comprehensive unit tests.",
                    "ai_analysis": {
                        "category_scores": {"Requirements": 28, "Code Quality": 24, "Documentation": 18, "Testing": 13, "Git": 9},
                        "evidence_found": ["Modular architecture demonstrated", "Pytest suite covers edge cases", "Clear installation commands"],
                        "recommendations": ["Consider adding type hints", "Add GitHub Actions workflow"]
                    }
                }
                email_payload = generate_evaluation_feedback_email(current_intern, task_obj, review_obj)
                email_payload["template_type"] = "Evaluation Scorecard"

            if email_payload:
                render_voice_over_player(
                    text_to_speak=email_payload["plain_text"],
                    player_id="voice_email",
                    title="🔊 Listen to Email Voice-Over Narration"
                )

                st.markdown(f"**Subject:** `{email_payload['subject']}`")
                st.markdown(f"**Recipient:** `{email_payload['recipient']}`")

                tab_html, tab_plain = st.tabs(["🎨 Rendered HTML Email Preview", "📄 Plain-Text Version"])
                with tab_html:
                    st.components.v1.html(email_payload["html"], height=550, scrolling=True)
                with tab_plain:
                    st.text(email_payload["plain_text"])

                st.markdown("---")
                st.subheader("Dispatch Controls")

                col_disp1, col_disp2 = st.columns([2, 1])
                with col_disp1:
                    user_confirmed_live = st.checkbox(
                        "⚠️ I explicitly authorize sending this email to the actual recipient inbox.",
                        value=False,
                        help="Only check this if you have configured valid SMTP credentials and wish to dispatch a live message."
                    )
                with col_disp2:
                    btn_send_email = st.button("🚀 Send / Simulate Email", type="primary")

                if btn_send_email:
                    success, msg = send_email_message(
                        recipient=email_payload["recipient"],
                        subject=email_payload["subject"],
                        html_content=email_payload["html"],
                        plain_content=email_payload["plain_text"],
                        template_type=email_payload["template_type"],
                        allow_live_send=user_confirmed_live
                    )
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)

    with tab_logs:
        st.subheader("Email Audit & Simulation Log")
        logs = get_email_logs(limit=50)
        if logs:
            df_logs = pd.DataFrame(logs)
            st.dataframe(df_logs[["id", "recipient", "subject", "template_type", "status", "simulated", "created_at"]], use_container_width=True, hide_index=True)
        else:
            st.info("No email events recorded yet.")


# -------------------------------------------------------------
# PAGE 9: ⚙️ SETTINGS & SECRETS
# -------------------------------------------------------------
elif menu == "⚙️ Settings & Secrets":
    st.markdown("""
    <div class="app-hero">
        <h1>⚙️ System Settings & Environment Secrets</h1>
        <p>Verify environment configuration, manage credentials securely, and test service connectivity</p>
    </div>
    """, unsafe_allow_html=True)

    ai_cfg = get_ai_config()
    smtp_cfg = get_smtp_config()

    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.subheader("🤖 AI Service Configuration")
        st.write("The system supports Google Gemini, OpenAI, or an intelligent built-in heuristic engine.")
        
        st.write(f"• Active AI Engine: **{ai_cfg['active_provider'].upper()}**")
        st.write(f"• Google Gemini Key: `{ai_cfg['gemini_key_preview']}`")
        st.write(f"• OpenAI Key: `{ai_cfg['openai_key_preview']}`")
        
        st.markdown("""
        > **How to configure AI keys**:
        > 1. Get a free Gemini API key at [Google AI Studio](https://aistudio.google.com/app/apikey).
        > 2. Open the `.env` file in the project folder.
        > 3. Add: `GEMINI_API_KEY=your_key_here`
        > 4. If no key is set, the application operates smoothly with the built-in Heuristic Analyzer!
        """)

    with col_s2:
        st.subheader("✉️ SMTP Email Configuration")
        st.write("Configure your outgoing SMTP server for review notifications.")
        
        st.write(f"• SMTP Server: `{smtp_cfg['host']}:{smtp_cfg['port']}`")
        st.write(f"• User: `{smtp_cfg['user'] or 'Not Set'}`")
        st.write(f"• Password: `{smtp_cfg['password_masked']}`")
        st.write(f"• TLS Enabled: `{smtp_cfg['use_tls']}`")
        st.write(f"• Safe Simulation Mode: `{'ENABLED (No real emails sent)' if smtp_cfg['simulation_mode'] else 'DISABLED'}`")

        if st.button("🔌 Test SMTP Connection"):
            with st.spinner("Connecting to SMTP server..."):
                ok, res_msg = test_smtp_connection()
                if ok:
                    st.success(res_msg)
                else:
                    st.error(res_msg)

        st.markdown("""
        > **How to configure SMTP**:
        > 1. In `.env`, configure:
        >    - `SMTP_HOST=smtp.gmail.com`
        >    - `SMTP_PORT=587`
        >    - `SMTP_USER=your_email@gmail.com`
        >    - `SMTP_PASSWORD=your_app_password`
        >    - `EMAIL_SIMULATION_MODE=False` (Only if you wish to send live emails)
        """)

    st.markdown("---")
    st.subheader("🔒 GitHub API Rate Limit Configuration")
    gh_tok = os.getenv("GITHUB_TOKEN", "").strip()
    st.write(f"• GitHub Token Status: `{'Configured (5,000 req/hr)' if gh_tok else 'Unauthenticated (60 req/hr public limit)'}`")
    st.caption("You can add `GITHUB_TOKEN=ghp_...` in `.env` if you analyze high volumes of public repositories.")
