"""
GitHub Repository Analyzer Module
Extracts repository metadata, commit logs, directory structures, and key code files via GitHub REST API.
"""

import os
import re
import base64
import requests
from typing import Dict, Any, Optional, List, Tuple
from dotenv import load_dotenv

load_dotenv()


def parse_github_url(url: str) -> Optional[Tuple[str, str, Optional[str]]]:
    """
    Parse a GitHub URL to extract owner, repo name, and optional branch.
    Examples:
      - https://github.com/octocat/Hello-World -> ('octocat', 'Hello-World', None)
      - https://github.com/octocat/Hello-World/tree/dev -> ('octocat', 'Hello-World', 'dev')
      - git@github.com:octocat/Hello-World.git -> ('octocat', 'Hello-World', None)
      - octocat/Hello-World -> ('octocat', 'Hello-World', None)
    """
    if not url:
        return None

    cleaned = url.strip()
    # Remove .git suffix
    if cleaned.endswith(".git"):
        cleaned = cleaned[:-4]

    # Pattern 1: HTTPS URL with optional tree/branch
    match_https = re.search(r"github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?", cleaned)
    if match_https:
        owner = match_https.group(1)
        repo = match_https.group(2)
        branch = match_https.group(3)
        return owner, repo, branch

    # Pattern 2: SSH URL
    match_ssh = re.search(r"git@github\.com:([^/]+)/([^/]+)", cleaned)
    if match_ssh:
        return match_ssh.group(1), match_ssh.group(2), None

    # Pattern 3: owner/repo shorthand
    match_short = re.match(r"^([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+)$", cleaned)
    if match_short:
        return match_short.group(1), match_short.group(2), None

    return None


def get_github_headers() -> Dict[str, str]:
    """Generate headers with optional GITHUB_TOKEN authentication."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Internship-Management-Reviewer/1.0"
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_repository_overview(owner: str, repo: str) -> Tuple[bool, Dict[str, Any], Optional[str]]:
    """Fetch basic repository metadata."""
    url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = get_github_headers()
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            return True, {
                "name": data.get("name"),
                "full_name": data.get("full_name"),
                "owner": data.get("owner", {}).get("login"),
                "description": data.get("description") or "No description provided",
                "default_branch": data.get("default_branch", "main"),
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "open_issues": data.get("open_issues_count", 0),
                "primary_language": data.get("language") or "Undetermined",
                "updated_at": data.get("updated_at"),
                "html_url": data.get("html_url"),
                "size_kb": data.get("size", 0)
            }, None
        elif resp.status_code == 404:
            return False, {}, f"Repository '{owner}/{repo}' was not found. Please verify that the repository exists and is public."
        elif resp.status_code == 403:
            msg = resp.json().get("message", "API rate limit exceeded")
            return False, {}, f"GitHub API rate limit exceeded ({msg}). Add GITHUB_TOKEN in .env or wait an hour."
        else:
            return False, {}, f"GitHub API returned HTTP {resp.status_code}: {resp.text[:200]}"
    except requests.exceptions.RequestException as e:
        return False, {}, f"Network connection error to GitHub: {str(e)}"


def fetch_recent_commits(owner: str, repo: str, branch: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch recent commits on the repository."""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page={limit}"
    if branch:
        url += f"&sha={branch}"
    headers = get_github_headers()
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            commits = resp.json()
            results = []
            for c in commits:
                results.append({
                    "sha": c.get("sha", "")[:7],
                    "message": c.get("commit", {}).get("message", "").split("\n")[0],
                    "author": c.get("commit", {}).get("author", {}).get("name", "Unknown"),
                    "date": c.get("commit", {}).get("author", {}).get("date", "")
                })
            return results
    except Exception:
        pass
    return []


def fetch_repository_tree(owner: str, repo: str, branch: str) -> List[Dict[str, Any]]:
    """Fetch recursive file tree."""
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
    headers = get_github_headers()
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code == 200:
            tree = resp.json().get("tree", [])
            return [{"path": item.get("path"), "type": item.get("type"), "size": item.get("size", 0)} for item in tree]
    except Exception:
        pass
    return []


def fetch_file_content(owner: str, repo: str, file_path: str, branch: str = "main") -> Optional[str]:
    """Fetch raw or base64 content of a file."""
    headers = get_github_headers()
    # Try raw content endpoint first (less API quota usage)
    raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
    try:
        resp = requests.get(raw_url, headers={"User-Agent": "Internship-Management-Reviewer/1.0"}, timeout=10)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass

    # Try API endpoint
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
    try:
        resp = requests.get(api_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("encoding") == "base64" and data.get("content"):
                return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    except Exception:
        pass

    return None


def inspect_repository(github_url: str, specified_branch: Optional[str] = None) -> Dict[str, Any]:
    """
    Comprehensive repository inspector.
    Fetches metadata, commit history, file tree, README, dependencies, and key sample source files.
    """
    parsed = parse_github_url(github_url)
    if not parsed:
        return {
            "success": False,
            "error": f"Invalid GitHub repository URL: '{github_url}'. Expected format: https://github.com/owner/repository",
            "url": github_url
        }

    owner, repo, url_branch = parsed
    branch = specified_branch or url_branch

    # 1. Fetch Overview
    success, overview, error_msg = fetch_repository_overview(owner, repo)
    if not success:
        return {
            "success": False,
            "error": error_msg,
            "owner": owner,
            "repo": repo,
            "url": github_url
        }

    active_branch = branch or overview.get("default_branch", "main")

    # 2. Fetch Commits
    commits = fetch_recent_commits(owner, repo, active_branch, limit=10)

    # 3. Fetch Tree
    tree_items = fetch_repository_tree(owner, repo, active_branch)
    file_paths = [item["path"] for item in tree_items if item.get("type") == "blob"]
    dir_paths = [item["path"] for item in tree_items if item.get("type") == "tree"]

    # 4. Locate and fetch README
    readme_candidates = ["README.md", "readme.md", "README.rst", "README.txt", "README"]
    readme_path = None
    readme_content = ""
    for candidate in readme_candidates:
        if candidate in file_paths:
            readme_path = candidate
            content = fetch_file_content(owner, repo, candidate, active_branch)
            if content:
                readme_content = content
                break

    # 5. Locate Dependency / Config Files
    dependency_files = {}
    dep_candidates = [
        "requirements.txt", "pyproject.toml", "setup.py", "Pipfile",
        "package.json", "Dockerfile", "docker-compose.yml",
        ".env.example", "Makefile", "pom.xml"
    ]
    for dep in dep_candidates:
        if dep in file_paths:
            content = fetch_file_content(owner, repo, dep, active_branch)
            if content:
                dependency_files[dep] = content[:1500]  # first 1.5KB

    # 6. Locate Test Files
    test_files = [p for p in file_paths if "test" in p.lower() or p.endswith("_test.py") or p.startswith("test_")]

    # 7. Locate CI/CD workflows
    workflow_files = [p for p in file_paths if p.startswith(".github/workflows/") and (p.endswith(".yml") or p.endswith(".yaml"))]

    # 8. Sample key source code files
    code_extensions = (".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".cpp", ".c", ".html", ".css", ".sql")
    source_files = [p for p in file_paths if p.endswith(code_extensions) and not p.startswith(".")]
    
    sample_code_files = {}
    # Prioritize non-test main files
    priority_sources = [p for p in source_files if p not in test_files][:5]
    for s_path in priority_sources:
        content = fetch_file_content(owner, repo, s_path, active_branch)
        if content:
            sample_code_files[s_path] = content[:3000]  # sample first 3KB

    # If test file exists, sample one test file
    sample_test_code = {}
    if test_files:
        t_sample_path = test_files[0]
        content = fetch_file_content(owner, repo, t_sample_path, active_branch)
        if content:
            sample_test_code[t_sample_path] = content[:2000]

    return {
        "success": True,
        "owner": owner,
        "repo": repo,
        "branch": active_branch,
        "overview": overview,
        "commits": commits,
        "file_count": len(file_paths),
        "dir_count": len(dir_paths),
        "file_paths": file_paths[:200],  # list up to 200 files
        "readme": {
            "found": bool(readme_path),
            "path": readme_path,
            "content": readme_content[:5000],  # first 5KB
            "length": len(readme_content)
        },
        "dependency_files": dependency_files,
        "test_files": test_files,
        "workflow_files": workflow_files,
        "sample_code_files": sample_code_files,
        "sample_test_code": sample_test_code
    }
