"""
AI Service Module for Internship Management & Review System
Supports Gemini API, OpenAI API, and an intelligent Heuristic Analyzer fallback.
Explains tasks in plain language and evaluates GitHub repositories against assigned requirements.
"""

import os
import re
import json
import requests
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()


def get_ai_config() -> Dict[str, Any]:
    """Retrieve current AI configuration and provider status."""
    gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""
    openai_key = os.getenv("OPENAI_API_KEY") or ""
    provider = os.getenv("AI_PROVIDER", "auto").lower()

    active_provider = "offline_heuristic"
    if provider == "gemini" and gemini_key:
        active_provider = "gemini"
    elif provider == "openai" and openai_key:
        active_provider = "openai"
    elif provider == "auto":
        if gemini_key:
            active_provider = "gemini"
        elif openai_key:
            active_provider = "openai"

    return {
        "gemini_available": bool(gemini_key),
        "openai_available": bool(openai_key),
        "active_provider": active_provider,
        "gemini_key_preview": f"{gemini_key[:4]}...{gemini_key[-4:]}" if len(gemini_key) > 8 else ("Configured" if gemini_key else "Not Set"),
        "openai_key_preview": f"{openai_key[:4]}...{openai_key[-4:]}" if len(openai_key) > 8 else ("Configured" if openai_key else "Not Set")
    }


# -------------------------------------------------------------
# LLM Providers (Gemini / OpenAI via REST)
# -------------------------------------------------------------

def _call_gemini_api(prompt: str, system_instruction: str = "", api_key: Optional[str] = None) -> Optional[str]:
    """Call Google Gemini 1.5 Flash API via REST endpoint."""
    key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        return None

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    payload: Dict[str, Any] = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system_instruction}\n\n{prompt}" if system_instruction else prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 2048
        }
    }
    headers = {"Content-Type": "application/json"}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=25)
        if resp.status_code == 200:
            data = resp.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
    except Exception:
        pass
    return None


def _call_openai_api(prompt: str, system_instruction: str = "", api_key: Optional[str] = None) -> Optional[str]:
    """Call OpenAI API (gpt-4o-mini / gpt-4o) via REST."""
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        return None

    url = "https://api.openai.com/v1/chat/completions"
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": "gpt-4o-mini",
        "messages": messages,
        "temperature": 0.3,
        "max_tokens": 2048
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=25)
        if resp.status_code == 200:
            data = resp.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
    except Exception:
        pass
    return None


def _call_active_llm(prompt: str, system_instruction: str = "") -> Tuple[Optional[str], str]:
    """Call whichever LLM is configured, returning response and provider name."""
    cfg = get_ai_config()
    provider = cfg["active_provider"]
    
    if provider == "gemini":
        res = _call_gemini_api(prompt, system_instruction)
        if res:
            return res, "Google Gemini 1.5 Flash"
    elif provider == "openai":
        res = _call_openai_api(prompt, system_instruction)
        if res:
            return res, "OpenAI GPT-4o-mini"
            
    return None, "offline_heuristic"


# -------------------------------------------------------------
# Feature 3: Task Explanation & AI Assistant
# -------------------------------------------------------------

def explain_task_in_simple_terms(task: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a simple, clear, natural language explanation of the task,
    including a roadmap, tech stack, deliverables, and scoring tips.
    """
    title = task.get("title", "")
    domain = task.get("domain", "")
    desc = task.get("description", "")
    reqs = task.get("requirements", "")
    rubric = task.get("rubric", "")

    # Try LLM first
    prompt = f"""
Please analyze this internship task and explain it in clear, encouraging, plain English suitable for an intern.

Task Title: {title}
Domain: {domain}
Description: {desc}
Requirements: {reqs}
Rubric: {rubric}

Return your explanation in clean markdown covering:
1. 💡 **What is this project in simple words?** (Explain the high-level concept without jargon)
2. 🌍 **Why is this important?** (Real-world business or industry impact)
3. 🗺️ **Step-by-Step Implementation Roadmap** (Phase 1, Phase 2, Phase 3, Phase 4)
4. 🛠️ **Recommended Tech Stack & Tools** (Libraries, databases, frameworks)
5. ✅ **Key Deliverables Checklist** (Exact items you must submit)
6. 🏆 **Tips to Score an A+** (Common pitfalls to avoid and standout features)
"""
    system_inst = "You are a friendly, expert software engineering mentor helping college interns understand their assigned technical projects."

    llm_resp, provider_used = _call_active_llm(prompt, system_inst)
    if llm_resp:
        return {
            "success": True,
            "provider": provider_used,
            "markdown_explanation": llm_resp,
            "is_ai_generated": True
        }

    # Heuristic fallback explanation
    roadmap_phases = [
        ("Phase 1: Project Setup & Architecture", "Set up Git repository, initialize virtual environment, choose folder structure, and install core libraries."),
        ("Phase 2: Core Logic Implementation", "Implement primary components, data models, endpoints, or ML algorithms based on the task description."),
        ("Phase 3: Verification & Unit Testing", "Write automated tests, verify boundary cases, handle errors gracefully, and benchmark performance."),
        ("Phase 4: Documentation & Final Polish", "Create an exemplary README with architecture diagrams, setup instructions, and demo screenshots.")
    ]

    fallback_md = f"""### 💡 What is this project in simple words?
**{title}** is an applied engineering project in **{domain}**.

In simple terms: {desc}

---

### 🌍 Why does this matter in the real world?
Building this demonstrates your ability to design robust solutions for real business needs. Companies look for engineers who can structure code cleanly, handle errors gracefully, and document their work so other engineers can collaborate easily.

---

### 🗺️ Step-by-Step Implementation Roadmap
"""
    for phase, detail in roadmap_phases:
        fallback_md += f"- **{phase}**: {detail}\n"

    reqs_text = reqs if reqs else "- Review the task instructions carefully."
    rubric_text = rubric if rubric else "- Code Quality: 25%\n- Requirement Completion: 25%\n- Testing & Validation: 25%\n- Documentation: 25%"

    fallback_md += f"""
---

### 🛠️ Key Task Requirements Checklist
Based on the task specification:
{reqs_text}

---

### 🏆 Rubric & Scoring Criteria
{rubric_text}

---

### 💡 Pro-Tips for Success
- **Commit Early & Often**: Don't upload a massive single commit at the deadline. Show progressive development with descriptive commit messages.
- **Write a Great README**: Mentors evaluate READMEs first. Include installation commands, environment variables, and usage examples.
- **Add Tests**: Even 4–5 well-crafted unit tests will place your submission in the top tier!
"""

    return {
        "success": True,
        "provider": "Built-in Mentor Engine (Offline Heuristic)",
        "markdown_explanation": fallback_md,
        "is_ai_generated": False
    }


def chat_with_task_assistant(task: Dict[str, Any], chat_history: List[Dict[str, str]], user_message: str) -> str:
    """Answer intern questions interactively about the specific task."""
    title = task.get("title", "")
    domain = task.get("domain", "")
    desc = task.get("description", "")
    reqs = task.get("requirements", "")

    system_inst = f"""You are an AI Internship Mentor. You are assisting an intern with their specific task:
Task: '{title}' ({domain})
Description: {desc}
Requirements: {reqs}

Answer the intern's questions clearly, concisely, and helpfully with code snippets where helpful. Guide them to learn rather than doing the entire assignment for them."""

    formatted_prompt = ""
    for msg in chat_history[-6:]:  # last 3 turns
        role = "Intern" if msg.get("role") == "user" else "Mentor"
        formatted_prompt += f"{role}: {msg.get('content')}\n"
    formatted_prompt += f"Intern: {user_message}\nMentor:"

    llm_resp, _ = _call_active_llm(formatted_prompt, system_inst)
    if llm_resp:
        return llm_resp.strip()

    # Rule-based fallback answers
    q_lower = user_message.lower()
    if "start" in q_lower or "how to begin" in q_lower or "setup" in q_lower:
        return f"To start on **{title}**, first initialize your GitHub repository. Then create a `.gitignore`, a `README.md`, and set up your virtual environment (`python -m venv .venv`). Next, write down the data models or endpoints required: {reqs[:120]}..."
    elif "test" in q_lower or "pytest" in q_lower:
        return "For testing, create a `tests/` directory with files named `test_*.py`. Use `pytest` to assert status codes, function outputs, and edge cases. For instance: `def test_basic_behavior(): assert function() is not None`."
    elif "readme" in q_lower or "documentation" in q_lower:
        return "An A+ README should have: (1) Project Title & One-line Summary, (2) Features list, (3) Architecture overview, (4) Prerequisites and Installation commands, (5) How to run the application, and (6) How to execute test suites."
    elif "git" in q_lower or "commit" in q_lower or "branch" in q_lower:
        return "Make sure to make atomic commits with clear messages (e.g., `feat: implement user registration endpoint`, `test: add unit tests for validation`). Avoid uploading `venv/`, `.env`, or compiled bytecode."
    else:
        return f"Regarding your question on **{title}**: A great approach is to break it down against the requirements ({reqs[:100]}...). Make sure each requirement is represented by modular functions and tested. Feel free to ask about specific libraries, architecture patterns, or debugging!"


# -------------------------------------------------------------
# Feature 5: Evidence-Based Repository Review & Grading
# -------------------------------------------------------------

def analyze_repository_against_task(task: Dict[str, Any], repo_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evidence-based evaluation of a GitHub repository against assigned task requirements.
    Analyzes files present, README quality, commit cadence, tests, and code structure.
    """
    if not repo_data.get("success"):
        return {
            "success": False,
            "error": repo_data.get("error", "Repository inspection failed"),
            "overall_score": 0,
            "letter_grade": "F"
        }

    task_title = task.get("title", "")
    task_desc = task.get("description", "")
    task_reqs = task.get("requirements", "")
    task_rubric = task.get("rubric", "")

    # Extract repository facts
    overview = repo_data.get("overview", {})
    commits = repo_data.get("commits", [])
    file_paths = repo_data.get("file_paths", [])
    readme = repo_data.get("readme", {})
    dep_files = repo_data.get("dependency_files", {})
    test_files = repo_data.get("test_files", [])
    workflows = repo_data.get("workflow_files", [])
    sample_code = repo_data.get("sample_code_files", {})

    # 1. Fact Gathering & Heuristic Scoring
    evidence_found: List[str] = []
    deficiencies: List[str] = []
    recommendations: List[str] = []

    # Category 1: Requirement Coverage (max 30)
    score_reqs = 0
    if len(file_paths) > 2:
        score_reqs += 10
        evidence_found.append(f"Repository contains structured project files ({len(file_paths)} files detected).")
    else:
        deficiencies.append("Repository has very few project files or is virtually empty.")

    # Check for domain-relevant files
    domain_lower = task.get("domain", "").lower()
    has_code = len(sample_code) > 0
    if has_code:
        score_reqs += 12
        sampled_names = list(sample_code.keys())[:3]
        evidence_found.append(f"Implementation files detected: {', '.join(sampled_names)}.")
    else:
        deficiencies.append("No primary source code files found matching standard programming extensions.")

    # Check dependencies
    if dep_files:
        score_reqs += 8
        dep_names = list(dep_files.keys())
        evidence_found.append(f"Dependency/build manifests found: {', '.join(dep_names)}.")
    else:
        deficiencies.append("Missing dependency manifest (e.g., requirements.txt, package.json, or Dockerfile).")
        recommendations.append("Add a requirements.txt or package.json declaring exact package versions.")

    score_reqs = min(30, score_reqs)

    # Category 2: Code Quality & Architecture (max 25)
    score_code = 0
    if has_code:
        score_code += 12
        # Check modularity (multiple directories or modular files)
        has_subdirs = any("/" in p for p in file_paths)
        if has_subdirs:
            score_code += 7
            evidence_found.append("Codebase demonstrates modular directory structure separation.")
        else:
            recommendations.append("Refactor flat file structure into modular packages (e.g. app/api, app/models, app/services).")

        # Check for config/env separation
        if ".env.example" in file_paths or ".gitignore" in file_paths:
            score_code += 6
            evidence_found.append("Standard project hygiene observed (.gitignore or .env.example present).")
        else:
            recommendations.append("Include a .gitignore and .env.example to ensure secrets and caches are never committed.")
    else:
        deficiencies.append("Unable to evaluate code quality due to absence of source files.")

    score_code = min(25, score_code)

    # Category 3: Documentation & Setup (max 20)
    score_doc = 0
    if readme.get("found"):
        score_doc += 8
        evidence_found.append(f"Found repository documentation ({readme.get('path')}).")
        length = readme.get("length", 0)
        content_lower = readme.get("content", "").lower()
        if length > 300:
            score_doc += 6
            evidence_found.append(f"README provides descriptive context ({length} characters).")
        else:
            deficiencies.append("README is minimal and lacks detailed architecture and setup instructions.")

        # Check for setup instructions
        if any(kw in content_lower for kw in ["install", "pip", "npm", "docker", "run", "usage"]):
            score_doc += 6
            evidence_found.append("README includes setup/installation instructions.")
        else:
            recommendations.append("Add step-by-step installation and execution instructions in README.md.")
    else:
        deficiencies.append("No README.md documentation file found in the repository root.")
        recommendations.append("Create a comprehensive README.md with project title, architecture, prerequisites, and how-to-run guide.")

    score_doc = min(20, score_doc)

    # Category 4: Testing & Verification (max 15)
    score_test = 0
    if test_files:
        score_test += 12
        evidence_found.append(f"Automated test files identified: {', '.join(test_files[:3])}.")
        if workflows:
            score_test += 3
            evidence_found.append(f"CI/CD workflow configured: {', '.join(workflows)}.")
    else:
        deficiencies.append("No automated test suite detected (no test_*.py or tests/ directory).")
        recommendations.append("Add automated unit tests (e.g., using pytest or unittest) to verify core logic.")

    score_test = min(15, score_test)

    # Category 5: Git & Project Hygiene (max 10)
    score_git = 0
    commit_count = len(commits)
    if commit_count >= 5:
        score_git += 7
        evidence_found.append(f"Good continuous commit history ({commit_count}+ recent commits).")
    elif commit_count >= 1:
        score_git += 4
        evidence_found.append(f"Repository has {commit_count} commits recorded.")
        if commit_count <= 2:
            recommendations.append("Adopt an incremental commit practice rather than large bulk commits.")
    
    if workflows:
        score_git += 3
    elif ".gitignore" in file_paths:
        score_git += 2

    score_git = min(10, score_git)

    # Calculate Total Score
    total_score = float(score_reqs + score_code + score_doc + score_test + score_git)
    total_score = max(10.0, min(100.0, total_score))

    # Grade
    if total_score >= 90:
        grade = "A+"
    elif total_score >= 80:
        grade = "A"
    elif total_score >= 70:
        grade = "B"
    elif total_score >= 60:
        grade = "C"
    else:
        grade = "Needs Revision"

    heuristic_report = {
        "overall_score": total_score,
        "letter_grade": grade,
        "category_scores": {
            "requirement_coverage": score_reqs,
            "code_quality": score_code,
            "documentation": score_doc,
            "testing": score_test,
            "git_hygiene": score_git
        },
        "max_category_scores": {
            "requirement_coverage": 30,
            "code_quality": 25,
            "documentation": 20,
            "testing": 15,
            "git_hygiene": 10
        },
        "evidence_found": evidence_found,
        "deficiencies": deficiencies,
        "recommendations": recommendations,
        "repo_summary": {
            "owner": repo_data.get("owner"),
            "repo": repo_data.get("repo"),
            "branch": repo_data.get("branch"),
            "total_files": len(file_paths),
            "commits_reviewed": len(commits),
            "language": overview.get("primary_language", "Undetermined")
        }
    }

    # Attempt LLM enhancement for deeper evidence synthesis if API key is present
    llm_prompt = f"""
You are an expert technical evaluator reviewing an intern's GitHub repository against assigned task requirements.

TASK DETAILS:
- Title: {task_title}
- Domain: {task.get('domain')}
- Description: {task_desc}
- Requirements: {task_reqs}
- Rubric: {task_rubric}

REPOSITORY INSPECTION DATA:
- Repository: {repo_data.get('owner')}/{repo_data.get('repo')} (Branch: {repo_data.get('branch')})
- Primary Language: {overview.get('primary_language')}
- Total Files Found: {len(file_paths)}
- File List Sample: {file_paths[:40]}
- README Found: {readme.get('found')}, Length: {readme.get('length')} chars
- README Snippet: {readme.get('content', '')[:1000]}
- Dependencies Found: {list(dep_files.keys())}
- Test Files Found: {test_files}
- Sample Source Files: {list(sample_code.keys())}
- Recent Commits: {[c.get('message') for c in commits[:5]]}

Based on this evidence, produce an evaluation JSON object with:
1. "overall_score": number between 0 and 100
2. "letter_grade": "A+", "A", "B", "C", or "Needs Revision"
3. "category_scores": {{"requirement_coverage": int (0-30), "code_quality": int (0-25), "documentation": int (0-20), "testing": int (0-15), "git_hygiene": int (0-10)}}
4. "strengths": list of 3-5 specific positive findings with evidence from the files found
5. "deficiencies": list of 2-4 gaps where requirements were missing or incomplete
6. "actionable_recommendations": list of 3-5 concrete next steps for the intern
7. "executive_summary": 2-3 sentences synthesizing the review

Respond with ONLY valid JSON.
"""
    system_inst = "You are a rigorous, fair software engineering evaluation system. Always ground your assessment in the concrete file evidence provided."

    llm_text, provider_name = _call_active_llm(llm_prompt, system_inst)
    if llm_text:
        try:
            # Extract JSON block
            json_match = re.search(r"\{.*\}", llm_text, re.DOTALL)
            if json_match:
                parsed_llm = json.loads(json_match.group(0))
                # Validate keys
                if "overall_score" in parsed_llm and "category_scores" in parsed_llm:
                    return {
                        "success": True,
                        "provider": provider_name,
                        "overall_score": float(parsed_llm.get("overall_score", total_score)),
                        "letter_grade": parsed_llm.get("letter_grade", grade),
                        "category_scores": parsed_llm.get("category_scores", heuristic_report["category_scores"]),
                        "max_category_scores": heuristic_report["max_category_scores"],
                        "evidence_found": parsed_llm.get("strengths", evidence_found),
                        "deficiencies": parsed_llm.get("deficiencies", deficiencies),
                        "recommendations": parsed_llm.get("actionable_recommendations", recommendations),
                        "executive_summary": parsed_llm.get("executive_summary", ""),
                        "repo_summary": heuristic_report["repo_summary"],
                        "is_ai_generated": True
                    }
        except Exception:
            pass

    # Use comprehensive heuristic report
    exec_sum = f"The submission for '{task_title}' was evaluated. "
    if total_score >= 80:
        exec_sum += "The codebase demonstrates good alignment with requirements, proper structure, and clear engineering effort."
    elif total_score >= 60:
        exec_sum += "Core components are partially present, but improvements in test coverage, documentation, and specific deliverables are required."
    else:
        exec_sum += "The repository is missing key required deliverables or lacks adequate code implementation and documentation."

    heuristic_report["executive_summary"] = exec_sum
    heuristic_report["provider"] = "Automated Evidence-Based Heuristic Reviewer"
    heuristic_report["is_ai_generated"] = False
    heuristic_report["success"] = True
    return heuristic_report
