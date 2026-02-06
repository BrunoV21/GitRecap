import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from git_recap.providers.base_fetcher import BaseFetcher


class LocalFetcher(BaseFetcher):
    """
    Fetcher implementation for local Git repositories.
    
    Works directly on a local git repository path without cloning.
    Supports fetching commits, authors, and branch information.
    """

    def __init__(
        self,
        repo_path: str,
        authors: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        repo_filter: Optional[List[str]] = None,
        validate_repo: bool = True
    ):
        """
        Initialize the LocalFetcher.
        
        Args:
            repo_path: Path to the local git repository
            authors: List of author names to filter by (optional)
            start_date: Start date for filtering commits (optional)
            end_date: End date for filtering commits (optional)
            repo_filter: List of repository names to filter (optional)
            validate_repo: Whether to validate the repository path (default: True)
        """
        super().__init__(pat=None, start_date=start_date, end_date=end_date, repo_filter=repo_filter, authors=authors)
        self.repo_path = repo_path
        if validate_repo:
            self._validate_repo()

    def _validate_repo(self) -> None:
        """
        Validate that the provided path is a valid git repository.
        
        Raises:
            ValueError: If the path is not a valid git repository.
        """
        if not os.path.exists(self.repo_path):
            raise ValueError(f"Path does not exist: {self.repo_path}")
        
        if not os.path.isdir(self.repo_path):
            raise ValueError(f"Path is not a directory: {self.repo_path}")
        
        git_dir = os.path.join(self.repo_path, '.git')
        if not os.path.exists(git_dir):
            raise ValueError(f"Not a git repository: {self.repo_path}")
        
        # Verify it's a valid git repo by running a simple command
        try:
            result = subprocess.run(
                ["git", "-C", self.repo_path, "rev-parse", "--git-dir"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
        except subprocess.TimeoutExpired:
            raise ValueError(f"Timeout while validating git repository: {self.repo_path}")
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Invalid git repository: {self.repo_path}. Error: {e.stderr}")

    @property
    def repos_names(self) -> List[str]:
        """
        Return the repository name.

        Returns:
            List[str]: List containing the repository name (single item).
        """
        repo_name = os.path.basename(self.repo_path)
        return [repo_name]

    def _run_git_log(self, extra_args: List[str] = None) -> List[Dict[str, Any]]:
        """
        Run git log command with common arguments and parse output.

        Args:
            extra_args (List[str], optional): Additional git log arguments.

        Returns:
            List[Dict[str, Any]]: Parsed commit entries.
        """
        args = [
            "git",
            "-C", self.repo_path,
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
        """
        Parse git log output into structured data.

        Args:
            log_output (str): Raw git log output.

        Returns:
            List[Dict[str, Any]]: Parsed commit entries.
        """
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
        """
        Fetch commits from the local repository.

        Returns:
            List[Dict[str, Any]]: List of commit entries.
        """
        return self._run_git_log()

    def fetch_pull_requests(self) -> List[Dict[str, Any]]:
        """
        Fetch pull requests (not applicable for local repositories).

        Returns:
            List[Dict[str, Any]]: Empty list (PRs are platform-specific).
        """
        return []

    def fetch_issues(self) -> List[Dict[str, Any]]:
        """
        Fetch issues (not applicable for local repositories).

        Returns:
            List[Dict[str, Any]]: Empty list (issues are platform-specific).
        """
        return []

    def fetch_releases(self) -> List[Dict[str, Any]]:
        """
        Fetch releases for the repository.
        Not applicable for local repositories.

        Raises:
            NotImplementedError: Always, since release fetching is not supported for LocalFetcher.
        """
        raise NotImplementedError(
            "Release fetching is not supported for local repositories (LocalFetcher)."
        )

    def get_branches(self) -> List[str]:
        """
        Get all branches in the local repository.

        Returns:
            List[str]: List of branch names (both local and remote).
        """
        try:
            # Get local branches
            result = subprocess.run(
                ["git", "-C", self.repo_path, "branch", "--format=%(refname:short)"],
                capture_output=True,
                text=True,
                check=True
            )
            branches = [b.strip() for b in result.stdout.splitlines() if b.strip()]

            # Get remote branches
            result_remote = subprocess.run(
                ["git", "-C", self.repo_path, "branch", "-r", "--format=%(refname:short)"],
                capture_output=True,
                text=True,
                check=True
            )
            remote_branches = [
                b.strip() for b in result_remote.stdout.splitlines() 
                if b.strip() and not b.endswith('/HEAD')
            ]

            return branches + remote_branches
        except subprocess.CalledProcessError:
            return []

    def get_valid_target_branches(self, source_branch: str) -> List[str]:
        """
        Get branches that can receive a pull request from the source branch.
        Not applicable for local repositories.

        Args:
            source_branch (str): The source branch name.

        Returns:
            List[str]: Empty list (PRs are platform-specific).

        Raises:
            NotImplementedError: Always, since PR validation is not supported for LocalFetcher.
        """
        raise NotImplementedError(
            "Pull request target branch validation is not supported for local repositories (LocalFetcher)."
        )

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
        Not applicable for local repositories.

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
            Dict[str, Any]: Empty dict (PRs are platform-specific).

        Raises:
            NotImplementedError: Always, since PR creation is not supported for LocalFetcher.
        """
        raise NotImplementedError(
            "Pull request creation is not supported for local repositories (LocalFetcher)."
        )

    def get_authors(self, repo_names: List[str]) -> List[Dict[str, str]]:
        """
        Retrieve unique authors from the local repository using git log.

        Args:
            repo_names: Not used for local fetcher (single repo only).

        Returns:
            List[Dict[str, str]]: List of unique author dictionaries with name and email.
        """
        authors_set = set()

        try:
            # Get authors from commit history
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

            # Also get committers
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

    def get_current_author(self) -> Optional[Dict[str, str]]:
        """
        Retrieve the current git user's information from local configuration.

        Returns:
            Optional[Dict[str, str]]: Dictionary with 'name' and 'email' keys,
                                     or None if not configured.
        """
        try:
            # Get user name
            result_name = subprocess.run(
                ["git", "-C", self.repo_path, "config", "user.name"],
                capture_output=True,
                text=True,
                check=True
            )
            user_name = result_name.stdout.strip()

            # Get user email
            result_email = subprocess.run(
                ["git", "-C", self.repo_path, "config", "user.email"],
                capture_output=True,
                text=True,
                check=True
            )
            user_email = result_email.stdout.strip()

            if user_name and user_email:
                return {
                    "name": user_name,
                    "email": user_email
                }
            return None
        except subprocess.CalledProcessError:
            return None
        except Exception as e:
            print(f"Error retrieving current author: {e}")
            return None