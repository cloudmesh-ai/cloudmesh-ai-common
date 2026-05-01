import subprocess
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from cloudmesh.ai.common.io import console

class GitHubError(Exception):
    """Exception raised for errors in GitHub CLI operations."""
    pass

class GitHubBase:
    """Base class for GitHub CLI operations."""
    
    def _run(self, args: List[str]) -> Any:
        """Executes a gh command and returns the result with rate limit handling."""
        max_retries = 2
        retry_delay = 3600 # 60 minutes
        
        for attempt in range(max_retries):
            try:
                # Use GH_NO_PROMPT=1 to prevent gh from hanging on interactive prompts
                env = os.environ.copy()
                env["GH_NO_PROMPT"] = "1"
                
                result = subprocess.run(
                    ["gh"] + args,
                    capture_output=True,
                    text=True,
                    check=True,
                    env=env,
                    timeout=30 # Prevent indefinite hangs
                )
                stdout = result.stdout.strip()
                if not stdout:
                    return None
                
                # Try to parse as JSON if it looks like it
                if stdout.startswith(("{", "[")):
                    try:
                        return json.loads(stdout)
                    except json.JSONDecodeError:
                        return stdout
                return stdout
            except subprocess.CalledProcessError as e:
                stderr = e.stderr or ""
                if "rate limit exceeded" in stderr.lower() or "HTTP 403" in stderr:
                    if attempt < max_retries - 1:
                        console.warning(f"GitHub API rate limit exceeded. Retrying in {retry_delay // 60} minutes...")
                        time.sleep(retry_delay)
                        continue
                raise GitHubError(f"GitHub CLI command failed: {stderr or e}")
            except FileNotFoundError:
                raise GitHubError("GitHub CLI ('gh') not found. Please install it.")
        return None

class GitHubRepo(GitHubBase):
    """Operations for a specific GitHub repository."""
    
    def __init__(self, gh: 'GitHub', repo_name: str):
        self.gh = gh
        self.repo_name = repo_name

    def get(self) -> Optional[Dict]:
        """Gets general repository information."""
        return self._run(["api", f"repos/{self.repo_name}"])

    def list_repos(self, limit: int = 1000, json_fields: Optional[str] = None) -> List[Dict]:
        """Lists repositories for the owner of this repo (not typically used this way)."""
        # This is usually done via GitHub.repo(owner).list()
        return []

    def get_pull_requests_count(self) -> int:
        """Returns the number of open pull requests."""
        res = self._run(["api", f"repos/{self.repo_name}/pulls", "--jq", "length"])
        return int(res) if res and str(res).isdigit() else 0

    def get_branches_count(self) -> int:
        """Returns the number of branches."""
        res = self._run(["api", f"repos/{self.repo_name}/branches", "--jq", "length"])
        return int(res) if res and str(res).isdigit() else 0

    def get_tags_count(self) -> int:
        """Returns the number of tags."""
        res = self._run(["api", f"repos/{self.repo_name}/tags", "--jq", "length"])
        return int(res) if res and str(res).isdigit() else 0

    def get_latest_commit_date(self) -> Optional[str]:
        """Returns the date of the latest commit."""
        res = self._run(["api", f"repos/{self.repo_name}/commits", "--jq", ".[0].commit.committer.date"])
        return res.strip('"') if res else None

    def get_contributors_count(self) -> int:
        """Returns the number of contributors."""
        res = self._run(["api", f"repos/{self.repo_name}/contributors", "--jq", "length"])
        return int(res) if res and str(res).isdigit() else 0

    def get_latest_release(self) -> Optional[str]:
        """Returns the latest release tag name."""
        res = self._run(["release", "view", "-R", self.repo_name, "--json", "tagName"])
        if isinstance(res, dict):
            return res.get("tagName")
        return None

    def get_size(self) -> Optional[int]:
        """Returns the repository size in KB."""
        data = self.get()
        if isinstance(data, dict):
            return data.get("size")
        return None

class GitHubUser(GitHubBase):
    """Operations for a GitHub user."""
    
    def __init__(self, gh: 'GitHub', username: str):
        self.gh = gh
        self.username = username

    def list_repos(self, limit: int = 1000, json_fields: Optional[str] = None, include_username: bool = True) -> List[Dict]:
        """Lists repositories for the user."""
        args = ["repo", "list"]
        if include_username:
            args.append(self.username)
        args.extend(["--limit", str(limit)])
        if json_fields:
            args.extend(["--json", json_fields])
        
        res = self._run(args)
        return res if isinstance(res, list) else []

    def get_orgs(self) -> List[str]:
        """Lists organizations the user belongs to with pagination."""
        all_orgs = []
        page = 1
        while True:
            res = self._run(["api", f"user/orgs?per_page=100&page={page}", "--jq", ".[].login"])
            if not res:
                break
            
            if isinstance(res, str):
                lines = res.splitlines()
                if not lines:
                    break
                all_orgs.extend(lines)
            elif isinstance(res, list):
                if not res:
                    break
                all_orgs.extend(res)
            else:
                break
            
            # If we got fewer than 100, we've reached the last page
            if isinstance(res, str) and len(res.splitlines()) < 100:
                break
            if isinstance(res, list) and len(res) < 100:
                break
                
            page += 1
            
        return all_orgs

class GitHubOrg(GitHubBase):
    """Operations for a GitHub organization."""
    
    def __init__(self, gh: 'GitHub', org_name: str):
        self.gh = gh
        self.org_name = org_name

    def list_repos(self, limit: int = 1000, json_fields: Optional[str] = None) -> List[Dict]:
        """Lists repositories for the organization."""
        args = ["repo", "list", self.org_name, "--limit", str(limit)]
        if json_fields:
            args.extend(["--json", json_fields])
        
        res = self._run(args)
        return res if isinstance(res, list) else []

    def get_info(self) -> Optional[Dict]:
        """Gets organization information."""
        return self._run(["api", f"orgs/{self.org_name}"])

    def get_public_repos_count(self) -> int:
        """Returns the number of public repositories in the organization."""
        res = self._run(["api", f"orgs/{self.org_name}", "--jq", ".public_repos"])
        return int(res) if res and str(res).isdigit() else 0

class GitHub(GitHubBase):
    """Main entry point for GitHub CLI operations."""
    
    def repo(self, name: str) -> GitHubRepo:
        """Returns a GitHubRepo object for the given repository name."""
        return GitHubRepo(self, name)

    def user(self, username: str) -> GitHubUser:
        """Returns a GitHubUser object for the given username."""
        return GitHubUser(self, username)

    def org(self, org_name: str) -> GitHubOrg:
        """Returns a GitHubOrg object for the given organization name."""
        return GitHubOrg(self, org_name)

    def get_authenticated_user(self) -> Optional[str]:
        """Returns the login of the currently authenticated user."""
        return self._run(["api", "user", "-q", ".login"])

# Singleton instance for easy access
gh = GitHub()