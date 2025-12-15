import gitlab
from datetime import datetime
from typing import List, Dict, Any, Optional
from git_recap.providers.base_fetcher import BaseFetcher

class GitLabFetcher(BaseFetcher):
    """
    Fetcher implementation for GitLab repositories.

    Supports fetching commits, merge requests (pull requests), issues, and authors.
    Release fetching is not supported and will raise NotImplementedError.
    """

    def __init__(
        self,
        pat: str,
        url: str = 'https://gitlab.com',
        start_date=None,
        end_date=None,
        repo_filter=None,
        authors=None
    ):
        """
        Initialize the GitLabFetcher.

        Args:
            pat (str): Personal Access Token for GitLab.
            url (str): The GitLab instance URL.
            start_date (datetime, optional): Start date for filtering entries.
            end_date (datetime, optional): End date for filtering entries.
            repo_filter (List[str], optional): List of repository names to filter.
            authors (List[str], optional): List of author usernames.
        """
        super().__init__(pat, start_date, end_date, repo_filter, authors)
        self.gl = gitlab.Gitlab(url, private_token=self.pat)
        self.gl.auth()
        # Retrieve projects where the user is a member.
        self.projects = self.gl.projects.list(membership=True, all=True)
        # Default to the authenticated user's username if no authors are provided.
        if authors is None:
            self.authors = [self.gl.user.username]
        else:
            self.authors = authors

    @property
    def repos_names(self) -> List[str]:
        """Return the list of repository names."""
        return [project.name for project in self.projects]

    def _filter_by_date(self, date_str: str) -> bool:
        """Check if a date string is within the configured date range."""
        date_obj = datetime.fromisoformat(date_str)
        if self.start_date and date_obj < self.start_date:
            return False
        if self.end_date and date_obj > self.end_date:
            return False
        return True

    def _stop_fetching(self, date_str: str) -> bool:
        """Determine if fetching should stop based on the date string."""
        date_obj = datetime.fromisoformat(date_str)
        if self.start_date and date_obj < self.start_date:
            return True
        return False

    def fetch_commits(self) -> List[Dict[str, Any]]:
        """
        Fetch commits for all projects and authors.

        Returns:
            List[Dict[str, Any]]: List of commit entries.
        """
        entries = []
        processed_commits = set()
        for project in self.projects:
            if self.repo_filter and project.name not in self.repo_filter:
                continue
            for author in self.authors:
                try:
                    commits = project.commits.list(author=author)
                except Exception:
                    continue
                for commit in commits:
                    commit_date = commit.committed_date
                    if self._filter_by_date(commit_date):
                        sha = commit.id
                        if sha not in processed_commits:
                            entry = {
                                "type": "commit",
                                "repo": project.name,
                                "message": commit.message.strip(),
                                "timestamp": commit_date,
                                "sha": sha,
                            }
                            entries.append(entry)
                            processed_commits.add(sha)
        return entries

    def fetch_pull_requests(self) -> List[Dict[str, Any]]:
        """
        Fetch merge requests (pull requests) and their associated commits for all projects and authors.

        Returns:
            List[Dict[str, Any]]: List of pull request and commit_from_pr entries.
        """
        entries = []
        processed_pr_commits = set()
        for project in self.projects:
            if self.repo_filter and project.name not in self.repo_filter:
                continue
            # Fetch merge requests (GitLab's pull requests)
            merge_requests = project.mergerequests.list(state='all', all=True)
            for mr in merge_requests:
                if mr.author['username'] not in self.authors:
                    continue
                mr_date = mr.created_at
                if not self._filter_by_date(mr_date):
                    continue
                mr_entry = {
                    "type": "pull_request",
                    "repo": project.name,
                    "message": mr.title,
                    "timestamp": mr_date,
                    "pr_number": mr.iid,
                }
                entries.append(mr_entry)
                try:
                    mr_commits = mr.commits()
                except Exception:
                    mr_commits = []
                for mr_commit in mr_commits:
                    commit_date = mr_commit['created_at']
                    if self._filter_by_date(commit_date):
                        sha = mr_commit['id']
                        if sha in processed_pr_commits:
                            continue
                        mr_commit_entry = {
                            "type": "commit_from_pr",
                            "repo": project.name,
                            "message": mr_commit['message'].strip(),
                            "timestamp": commit_date,
                            "sha": sha,
                            "pr_title": mr.title,
                        }
                        entries.append(mr_commit_entry)
                        processed_pr_commits.add(sha)
                if self._stop_fetching(mr_date):
                    break
        return entries

    def fetch_issues(self) -> List[Dict[str, Any]]:
        """
        Fetch issues assigned to the authenticated user for all projects.

        Returns:
            List[Dict[str, Any]]: List of issue entries.
        """
        entries = []
        for project in self.projects:
            if self.repo_filter and project.name not in self.repo_filter:
                continue
            issues = project.issues.list(assignee_id=self.gl.user.id)
            for issue in issues:
                issue_date = issue.created_at
                if self._filter_by_date(issue_date):
                    entry = {
                        "type": "issue",
                        "repo": project.name,
                        "message": issue.title,
                        "timestamp": issue_date,
                    }
                    entries.append(entry)
                if self._stop_fetching(issue_date):
                    break
        return entries

    def fetch_releases(self) -> List[Dict[str, Any]]:
        """
        Fetch releases for GitLab repositories.

        Not implemented for GitLabFetcher.

        Raises:
            NotImplementedError: Always, since release fetching is not supported for GitLabFetcher.
        """
        raise NotImplementedError("Release fetching is not supported for GitLab (GitLabFetcher).")

    def get_branches(self) -> List[str]:
        """
        Get all branches in the repository.
        
        Returns:
            List[str]: List of branch names.
        
        Raises:
            NotImplementedError: Always, since branch listing is not yet implemented for GitLabFetcher.
        """
        raise NotImplementedError("Branch listing is not yet implemented for GitLab (GitLabFetcher).")

    def get_valid_target_branches(self, source_branch: str) -> List[str]:
        """
        Get branches that can receive a pull request from the source branch.
        
        Validates that the source branch exists, filters out branches with existing
        open PRs from source, excludes the source branch itself, and optionally
        checks if source is ahead of target.
        
        Args:
            source_branch (str): The source branch name.
        
        Returns:
            List[str]: List of valid target branch names.
        
        Raises:
            NotImplementedError: Always, since PR target validation is not yet implemented for GitLabFetcher.
        """
        raise NotImplementedError("Pull request target branch validation is not yet implemented for GitLab (GitLabFetcher).")

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
        Create a pull request (merge request) between two branches with optional metadata.
        
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
            Dict[str, Any]: Dictionary containing PR metadata (url, number, state, success) or error information.
        
        Raises:
            NotImplementedError: Always, since PR creation is not yet implemented for GitLabFetcher.
        """
        raise NotImplementedError("Pull request (merge request) creation is not yet implemented for GitLab (GitLabFetcher).")

    def get_authors(self, repo_names: List[str]) -> List[Dict[str, str]]:
        """
        Retrieve unique authors from specified GitLab projects.
        
        Args:
            repo_names: List of project names/IDs.
                       Empty list fetches from all accessible projects.
        
        Returns:
            List of unique author dictionaries with name and email.
        """
        authors_set = set()
        
        try:
            # If no specific projects provided, get all accessible projects
            if not repo_names:
                projects = self.gl.projects.list(membership=True, all=True)
                repo_names = [project.path_with_namespace for project in projects]
            
            for repo_name in repo_names:
                try:
                    project = self.gl.projects.get(repo_name)
                    
                    # Fetch commits
                    commits = project.commits.list(all=True)
                    
                    for commit in commits:
                        author_name = commit.author_name or "Unknown"
                        author_email = commit.author_email or "unknown@example.com"
                        authors_set.add((author_name, author_email))
                        
                        # Also add committer if available
                        if hasattr(commit, 'committer_name') and commit.committer_name:
                            committer_name = commit.committer_name
                            committer_email = commit.committer_email or "unknown@example.com"
                            authors_set.add((committer_name, committer_email))
                
                except gitlab.exceptions.GitlabGetError as e:
                    print(f"Error fetching authors from {repo_name}: {e}")
                    continue
            
            # Convert set to list of dictionaries
            authors_list = [
                {"name": name, "email": email}
                for name, email in sorted(authors_set)
            ]
            
            return authors_list
        
        except Exception as e:
            print(f"Error in get_authors: {e}")
            return []