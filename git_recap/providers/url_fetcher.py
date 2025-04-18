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
        self.url = url
        self.temp_dir = None
        self._validate_url()
        self._clone_repo()

    def _validate_url(self) -> None:
        """Validate the Git repository URL using git ls-remote."""
        try:
            result = subprocess.run(
                ["git", "ls-remote", self.url],
                capture_output=True,
                text=True,
                check=True
            )
            if not result.stdout.strip():
                raise ValueError(f"URL {self.url} points to an empty repository")
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Invalid Git repository URL: {self.url}") from e

    def _clone_repo(self) -> None:
        """Clone the repository to a temporary directory."""
        self.temp_dir = tempfile.mkdtemp(prefix="gitrecap_")
        try:
            subprocess.run(
                ["git", "clone", self.url, self.temp_dir],
                check=True,
                capture_output=True
            )
        except subprocess.CalledProcessError as e:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            raise RuntimeError(f"Failed to clone repository: {e.stderr}") from e

    @property
    def repos_names(self) -> List[str]:
        """Return list of repository names (single item for URL fetcher)."""
        if not self.temp_dir:
            return []
        
        url_parts = re.split(r'[:/]', self.url)
        repo_name = url_parts[-1] if url_parts else ""
        
        # Remove .git extension if present
        if repo_name.endswith(".git"):
            repo_name = repo_name[:-4]
            
        return [repo_name]

    def _run_git_log(self, extra_args: List[str] = None) -> List[Dict[str, Any]]:
        """Run git log command with common arguments and parse output."""
        if not self.temp_dir:
            return []

        args = [
            "git",
            "-C", self.temp_dir,
            "log",
            "--pretty=format:%H|%an|%ad|%s",
            "--date=iso"
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
                check=True
            )
            return self._parse_git_log(result.stdout)
        except subprocess.CalledProcessError:
            return []

    def _parse_git_log(self, log_output: str) -> List[Dict[str, Any]]:
        """Parse git log output into structured data."""
        entries = []
        for line in log_output.splitlines():
            if not line.strip():
                continue
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
        return entries

    def fetch_commits(self) -> List[Dict[str, Any]]:
        """Fetch commits from the cloned repository."""
        return self._run_git_log()

    def fetch_pull_requests(self) -> List[Dict[str, Any]]:
        """Fetch pull requests (not implemented for generic Git URLs)."""
        # Generic Git URLs don't have a standard way to fetch PRs
        return []

    def fetch_issues(self) -> List[Dict[str, Any]]:
        """Fetch issues (not implemented for generic Git URLs)."""
        # Generic Git URLs don't have a standard way to fetch issues
        return []

    def clear(self) -> None:
        """Clean up temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = None
