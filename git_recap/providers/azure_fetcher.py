from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from datetime import datetime
from typing import List, Dict, Any
from git_recap.providers.base_fetcher import BaseFetcher

class AzureFetcher(BaseFetcher):
    """
    Fetcher implementation for Azure DevOps repositories.

    Supports fetching commits, pull requests, and issues.
    Release fetching is not supported and will raise NotImplementedError.
    """

    def __init__(self, pat: str, organization_url: str, start_date=None, end_date=None, repo_filter=None, authors=None):
        """
        Initialize the AzureFetcher.

        Args:
            pat (str): Personal Access Token for Azure DevOps.
            organization_url (str): The Azure DevOps organization URL.
            start_date (datetime, optional): Start date for filtering entries.
            end_date (datetime, optional): End date for filtering entries.
            repo_filter (List[str], optional): List of repository names to filter.
            authors (List[str], optional): List of author identifiers (e.g., email or unique id).
        """
        super().__init__(pat, start_date, end_date, repo_filter, authors)
        self.organization_url = organization_url
        credentials = BasicAuthentication('', self.pat)
        self.connection = Connection(base_url=self.organization_url, creds=credentials)
        self.core_client = self.connection.clients.get_core_client()
        self.git_client = self.connection.clients.get_git_client()
        self.repos = self.get_repos()
        # Azure DevOps doesn't provide an affiliation filter;
        # we'll iterate over all repos in each project.
        if authors is None:
            self.authors = []

    def get_repos(self):
        """
        Retrieve all repositories in all projects for the organization.
        Returns:
            List of repository objects.
        """
        projects = self.core_client.get_projects().value
        # Get all repositories in each project
        repos = [self.git_client.get_repositories(project.id) for project in projects]
        return repos

    @property
    def repos_names(self) -> List[str]:
        """
        Return the list of repository names.

        Returns:
            List[str]: List of repository names.
        """
        # To be implemented if needed for UI or listing.
        ...

    def _filter_by_date(self, date_obj: datetime) -> bool:
        """
        Check if a datetime object is within the configured date range.

        Args:
            date_obj (datetime): The datetime to check.

        Returns:
            bool: True if within range, False otherwise.
        """
        if self.start_date and date_obj < self.start_date:
            return False
        if self.end_date and date_obj > self.end_date:
            return False
        return True

    def _stop_fetching(self, date_obj: datetime) -> bool:
        """
        Determine if fetching should stop based on the date.

        Args:
            date_obj (datetime): The datetime to check.

        Returns:
            bool: True if should stop, False otherwise.
        """
        if self.start_date and date_obj < self.start_date:
            return True
        return False

    def fetch_commits(self) -> List[Dict[str, Any]]:
        """
        Fetch commits for all repositories and authors.

        Returns:
            List[Dict[str, Any]]: List of commit entries.
        """
        entries = []
        processed_commits = set()
        for repo in self.repos:
            if self.repo_filter and repo.name not in self.repo_filter:
                continue
            for author in self.authors:
                try:
                    commits = self.git_client.get_commits(
                        project=repo.id,
                        repository_id=repo.id,
                        search_criteria={"author": author}
                    )
                except Exception:
                    continue
                for commit in commits:
                    # Azure DevOps returns a commit with an 'author' property.
                    commit_date = commit.author.date  # assumed datetime
                    if self._filter_by_date(commit_date):
                        sha = commit.commit_id
                        if sha not in processed_commits:
                            entry = {
                                "type": "commit",
                                "repo": repo.name,
                                "message": commit.comment.strip(),
                                "timestamp": commit_date,
                                "sha": sha,
                            }
                            entries.append(entry)
                            processed_commits.add(sha)
                    if self._stop_fetching(commit_date):
                        break
        return entries

    def fetch_pull_requests(self) -> List[Dict[str, Any]]:
        """
        Fetch pull requests and their associated commits for all repositories and authors.

        Returns:
            List[Dict[str, Any]]: List of pull request and commit_from_pr entries.
        """
        entries = []
        processed_pr_commits = set()
        projects = self.core_client.get_projects().value
        for project in projects:
            repos = self.git_client.get_repositories(project.id)
            for repo in repos:
                if self.repo_filter and repo.name not in self.repo_filter:
                    continue
                try:
                    pull_requests = self.git_client.get_pull_requests(
                        repository_id=repo.id,
                        search_criteria={}
                    )
                except Exception:
                    continue
                for pr in pull_requests:
                    # Check that the PR creator is one of our authors.
                    if pr.created_by.unique_name not in self.authors:
                        continue
                    pr_date = pr.creation_date  # type: datetime
                    if not self._filter_by_date(pr_date):
                        continue

                    pr_entry = {
                        "type": "pull_request",
                        "repo": repo.name,
                        "message": pr.title,
                        "timestamp": pr_date,
                        "pr_number": pr.pull_request_id,
                    }
                    entries.append(pr_entry)

                    try:
                        pr_commits = self.git_client.get_pull_request_commits(
                            project=project.id,
                            repository_id=repo.id,
                            pull_request_id=pr.pull_request_id
                        )
                    except Exception:
                        pr_commits = []
                    for pr_commit in pr_commits:
                        commit_date = pr_commit.author.date
                        if self._filter_by_date(commit_date):
                            sha = pr_commit.commit_id
                            if sha in processed_pr_commits:
                                continue
                            pr_commit_entry = {
                                "type": "commit_from_pr",
                                "repo": repo.name,
                                "message": pr_commit.comment.strip(),
                                "timestamp": commit_date,
                                "sha": sha,
                                "pr_title": pr.title,
                            }
                            entries.append(pr_commit_entry)
                            processed_pr_commits.add(sha)
                    if self._stop_fetching(pr_date):
                        break
        return entries

    def fetch_issues(self) -> List[Dict[str, Any]]:
        """
        Fetch issues (work items) assigned to the configured authors.

        Returns:
            List[Dict[str, Any]]: List of issue entries.
        """
        entries = []
        wit_client = self.connection.clients.get_work_item_tracking_client()
        # Query work items for each author using a simplified WIQL query.
        for author in self.authors:
            wiql = f"SELECT [System.Id], [System.Title], [System.CreatedDate] FROM WorkItems WHERE [System.AssignedTo] CONTAINS '{author}'"
            try:
                query_result = wit_client.query_by_wiql(wiql).work_items
            except Exception:
                continue
            for item_ref in query_result:
                work_item = wit_client.get_work_item(item_ref.id)
                created_date = datetime.fromisoformat(work_item.fields["System.CreatedDate"])
                if self._filter_by_date(created_date):
                    entry = {
                        "type": "issue",
                        "repo": "N/A",
                        "message": work_item.fields["System.Title"],
                        "timestamp": created_date,
                    }
                    entries.append(entry)
                if self._stop_fetching(created_date):
                    break
        return entries

    def fetch_releases(self) -> List[Dict[str, Any]]:
        """
        Fetch releases for Azure DevOps repositories.

        Not implemented for Azure DevOps.

        Raises:
            NotImplementedError: Always, since release fetching is not supported for AzureFetcher.
        """
        # If Azure DevOps release fetching is supported in the future, implement logic here.
        raise NotImplementedError("Release fetching is not supported for Azure DevOps (AzureFetcher).")