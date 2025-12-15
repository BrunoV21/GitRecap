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
        self.repo_path = None
        self._clone_repo()

    def _normalize_url(self, url: str) -> str:
        """Normalize the Git URL to ensure consistent format."""
        url = url.strip()
        if not url.endswith('.git') and "_git" not in url:
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
                timeout=10
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
        self.repo_path = self.temp_dir
        try:
            subprocess.run(
                ["git", "clone", "--no-checkout", self.url, self.temp_dir],
                check=True,
                capture_output=True,
                text=True,
                timeout=300
            )

            subprocess.run(
                ["git", "-C", self.temp_dir, "fetch", "--all"],
                check=True,
                capture_output=True,
                text=True,
                timeout=300
            )

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
            repo_name = self.url.split('/')[-1]
            return [repo_name]

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
            "--all"
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
                timeout=120
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
                continue

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

    def fetch_releases(self) -> List[Dict[str, Any]]:
        """
        Fetch releases for the repository.
        Not implemented for generic Git URLs.
        Raises:
            NotImplementedError: Always, since release fetching is not supported for URLFetcher.
        """
        raise NotImplementedError("Release fetching is not supported for generic Git URLs (URLFetcher).")

    def get_branches(self) -> List[str]:
        """
        Get all branches in the repository.
        
        Returns:
            List[str]: List of branch names.
        
        Raises:
            NotImplementedError: Always, since branch listing is not yet implemented for URLFetcher.
        """
        raise NotImplementedError("Branch listing is not yet implemented for generic Git URLs (URLFetcher).")

    def get_valid_target_branches(self, source_branch: str) -> List[str]:
        """
        Get branches that can receive a pull request from the source branch.
        
        Args:
            source_branch (str): The source branch name.
        
        Returns:
            List[str]: List of valid target branch names.
        
        Raises:
            NotImplementedError: Always, since PR target validation is not supported for URLFetcher.
        """
        raise NotImplementedError("Pull request target branch validation is not supported for generic Git URLs (URLFetcher).")

    def create_pull_request(
        self,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str,
        draft: bool = False,
        reviewers: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a pull request between two branches.
        
        Args:
            head_branch: Source branch for the PR.
            base_branch: Target branch for the PR.
            title: PR title.
            body: PR description.
            draft: Whether to create as draft PR (default: False).
            reviewers: List of reviewer usernames (optional).
            assignees: List of assignee usernames (optional).
            labels: List of label names (optional).
        
        Returns:
            Dict[str, Any]: Dictionary containing PR metadata or error information.
        
        Raises:
            NotImplementedError: Always, since PR creation is not supported for URLFetcher.
        """
        raise NotImplementedError("Pull request creation is not supported for generic Git URLs (URLFetcher).")

    def get_authors(self, repo_names: List[str]) -> List[Dict[str, str]]:
        """
        Retrieve unique authors from cloned repository using git log.
        
        Args:
            repo_names: Not used for URL fetcher (single repo only).
        
        Returns:
            List of unique author dictionaries with name and email.
        """
        authors_set = set()
        
        try:
            if not hasattr(self, 'repo_path') or not os.path.exists(self.repo_path):
                print("Repository not cloned yet")
                return []
            
            cmd = [
                'git', '-C', self.repo_path, 'log',
                '--all',
                '--format=%an|%ae'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.strip().split('\n'):
                if '|' in line:
                    name, email = line.split('|', 1)
                    authors_set.add((name.strip(), email.strip()))
            
            cmd_committer = [
                'git', '-C', self.repo_path, 'log',
                '--all',
                '--format=%cn|%ce'
            ]
            
            result_committer = subprocess.run(
                cmd_committer,
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result_committer.stdout.strip().split('\n'):
                if '|' in line:
                    name, email = line.split('|', 1)
                    authors_set.add((name.strip(), email.strip()))
            
            authors_list = [
                {"name": name, "email": email}
                for name, email in sorted(authors_set)
            ]
            
            return authors_list
        
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {e}")
            return []
        except Exception as e:
            print(f"Error in get_authors: {e}")
            return []

    def clear(self) -> None:
        """Clean up temporary directory."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception:
                pass
            finally:
                self.temp_dir = None
                self.repo_path = None