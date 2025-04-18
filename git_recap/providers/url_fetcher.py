import os
import re
import shutil
import subprocess
from pathlib import Path
import tempfile
from typing import List, Dict, Any, Optional
from datetime import datetime
from git_recap.providers.base_fetcher import BaseFetcher


class URLFetcher(BaseFetcher):
    """Fetcher implementation for generic Git repository URLs."""
    
    GIT_URL_PATTERN = re.compile(
        r'^(?:http|https|git|ssh)://'  # Protocol
        r'(?:\S+@)?'  # Optional username
        r'([^/]+)'  # Domain
        r'(?:[:/])([^/]+/[^/]+?)(?:\.git)?$'  # Repo path
    )
    
    def __init__(
        self,
        url: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        repo_filter: Optional[List[str]] = None,
        authors: Optional[List[str]] = None
    ):
        super().__init__(
            pat="",  # No PAT needed for URL fetcher
            start_date=start_date,
            end_date=end_date,
            repo_filter=repo_filter,
            authors=authors
        )
        self.url = self._normalize_url(url)
        self.temp_dir = None
        self._validate_url()
        self._clone_repo()

    def _normalize_url(self, url: str) -> str:
        """Normalize the Git URL to ensure consistent format."""
        url = url.strip()
        if not url.endswith('.git'):
            url += '.git'
        if not any(url.startswith(proto) for proto in ('http://', 'https://', 'git://', 'ssh://')):
            url = f'https://{url}'
        return url

    def _validate_url(self) -> None:
        """Validate the Git repository URL using git ls-remote."""
        if not self.GIT_URL_PATTERN.match(self.url):
            raise ValueError(f"Invalid Git repository URL format: {self.url}")
            
        try:
            result = subprocess.run(
                ["git", "ls-remote", self.url],
                capture_output=True,
                text=True,
                check=True,
                timeout=10  # Add timeout to prevent hanging
            )
            if not result.stdout.strip():
                raise ValueError(f"URL {self.url} points to an empty repository")
        except subprocess.TimeoutExpired:
            raise ValueError(f"Timeout while validating URL {self.url}")
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Invalid Git repository URL: {self.url}. Error: {e.stderr}") from e

    def _clone_repo(self) -> None:
        """Clone the repository to a temporary directory with all branches."""
        self.temp_dir = tempfile.mkdtemp(prefix="gitrecap_")
        try:
            # First clone with --no-checkout to save bandwidth
            subprocess.run(
                ["git", "clone", "--no-checkout", self.url, self.temp_dir],
                check=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Fetch all branches
            subprocess.run(
                ["git", "-C", self.temp_dir, "fetch", "--all"],
                check=True,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Verify the cloned repository has at least one commit
            verify_result = subprocess.run(
                ["git", "-C", self.temp_dir, "rev-list", "--count", "--all"],
                capture_output=True,
                text=True,
                check=True
            )
            if int(verify_result.stdout.strip()) == 0:
                raise ValueError("Cloned repository has no commits")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("Repository cloning timed out")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone repository: {e.stderr}") from e
        except Exception as e:
            self.clear()
            raise RuntimeError(f"Unexpected error during cloning: {str(e)}") from e

    @property
    def repos_names(self) -> List[str]:
        """Return list of repository names (single item for URL fetcher)."""
        if not self.temp_dir:
            return []
        
        match = self.GIT_URL_PATTERN.match(self.url)
        if not match:
            return []
            
        repo_name = match.group(2).split('/')[-1]
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
            
        return [repo_name]

    def _get_all_branches(self) -> List[str]:
        """Get list of all remote branches in the repository."""
        if not self.temp_dir:
            return []
            
        try:
            result = subprocess.run(
                ["git", "-C", self.temp_dir, "branch", "-r", "--format=%(refname:short)"],
                capture_output=True,
                text=True,
                check=True
            )
            branches = [b.strip() for b in result.stdout.splitlines() if b.strip()]
            # Filter out HEAD reference if present
            return [b for b in branches if not b.endswith('/HEAD')]
        except subprocess.CalledProcessError:
            return []

    def _run_git_log(self, extra_args: List[str] = None) -> List[Dict[str, Any]]:
        """Run git log command with common arguments and parse output."""
        if not self.temp_dir:
            return []

        args = [
            "git",
            "-C", self.temp_dir,
            "log",
            "--pretty=format:%H|%an|%ad|%s",
            "--date=iso",
            "--all"  # Include all branches and tags
        ]

        if self.start_date:
            args.extend(["--since", self.start_date.isoformat()])
        if self.end_date:
            args.extend(["--until", self.end_date.isoformat()])
        if self.authors:
            authors_filter = "|".join(self.authors)
            args.extend(["--author", authors_filter])
        if extra_args:
            args.extend(extra_args)

        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                check=True,
                timeout=120  # Increased timeout for large repositories
            )
            return self._parse_git_log(result.stdout)
        except subprocess.TimeoutExpired:
            return []
        except subprocess.CalledProcessError:
            return []

    def _parse_git_log(self, log_output: str) -> List[Dict[str, Any]]:
        """Parse git log output into structured data."""
        entries = []
        for line in log_output.splitlines():
            if not line.strip():
                continue
                
            try:
                sha, author, date_str, message = line.split("|", 3)
                timestamp = datetime.fromisoformat(date_str)
                
                if self.start_date and timestamp < self.start_date:
                    continue
                if self.end_date and timestamp > self.end_date:
                    continue

                entries.append({
                    "type": "commit",
                    "repo": self.repos_names[0],
                    "message": message,
                    "sha": sha,
                    "author": author,
                    "timestamp": timestamp
                })
            except ValueError:
                continue  # Skip malformed log entries
                
        return entries

    def fetch_commits(self) -> List[Dict[str, Any]]:
        """Fetch commits from all branches in the cloned repository."""
        return self._run_git_log()

    def fetch_pull_requests(self) -> List[Dict[str, Any]]:
        """Fetch pull requests (not implemented for generic Git URLs)."""
        return []

    def fetch_issues(self) -> List[Dict[str, Any]]:
        """Fetch issues (not implemented for generic Git URLs)."""
        return []

    def clear(self) -> None:
        """Clean up temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass  # Ensure we don't raise during cleanup
            finally:
                self.temp_dir = None