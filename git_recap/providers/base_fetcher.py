from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

class BaseFetcher(ABC):
    def __init__(
        self,
        pat: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        repo_filter: Optional[List[str]] = None,
        authors: Optional[List[str]] = None
    ):
        self.pat = pat
        if start_date is not None:
            self.start_date = start_date if start_date.tzinfo is not None else start_date.replace(tzinfo=timezone.utc)
        else:
            self.start_date = None

        if end_date is not None:
            self.end_date = end_date if end_date.tzinfo is not None else end_date.replace(tzinfo=timezone.utc)
        else:
            self.end_date = None

        self.repo_filter = repo_filter or []
        self.limit = -1
        self.authors = [] if authors is None else authors

    @property
    @abstractmethod
    def repos_names(self) -> List[str]:
        """
        Return the list of repository names accessible to this fetcher.

        Returns:
            List[str]: List of repository names.
        """
        pass

    @abstractmethod
    def fetch_commits(self) -> List[Dict[str, Any]]:
        """
        Fetch commit entries for the configured repositories and authors.

        Returns:
            List[Dict[str, Any]]: List of commit entries.
        """
        pass

    @abstractmethod
    def fetch_pull_requests(self) -> List[Dict[str, Any]]:
        """
        Fetch pull request entries for the configured repositories and authors.

        Returns:
            List[Dict[str, Any]]: List of pull request entries.
        """
        pass

    @abstractmethod
    def fetch_issues(self) -> List[Dict[str, Any]]:
        """
        Fetch issue entries for the configured repositories and authors.

        Returns:
            List[Dict[str, Any]]: List of issue entries.
        """
        pass

    @abstractmethod
    def fetch_releases(self) -> List[Dict[str, Any]]:
        """
        Fetch releases for all repositories accessible to this fetcher.

        Returns:
            List[Dict[str, Any]]: List of releases, each as a structured dictionary.
                The dictionary should include at least:
                  - tag_name: str
                  - name: str
                  - repo: str
                  - author: str
                  - published_at: datetime
                  - created_at: datetime
                  - draft: bool
                  - prerelease: bool
                  - body: str
                  - assets: List[Dict[str, Any]] (if available)
        Raises:
            NotImplementedError: If the provider does not support release fetching.
        """
        raise NotImplementedError("Release fetching is not implemented for this provider.")

    @abstractmethod
    def open_pr(
        self,
        repo_name: str,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str,
        draft: bool = False,
        reviewers: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new pull request in the provider.

        Args:
            repo_name (str): Name of the repository.
            head_branch (str): The name of the branch where your changes are implemented (source).
            base_branch (str): The name of the branch you want the changes pulled into (target).
            title (str): Title of the pull request.
            body (str): Body/description of the pull request (supports markdown).
            draft (bool): Whether to create the PR as a draft.
            reviewers (List[str], optional): List of usernames to request review from.
            assignees (List[str], optional): List of usernames to assign to the PR.
            labels (List[str], optional): List of label names to add to the PR.

        Returns:
            Dict[str, Any]: Information about the created pull request (number, url, etc.).
        Raises:
            NotImplementedError: If the provider does not support PR creation.
        """
        raise NotImplementedError("Pull request creation is not implemented for this provider.")

    def get_authored_messages(self) -> List[Dict[str, Any]]:
        """
        Aggregates all commit, pull request, and issue entries into a single list,
        ensuring no duplicate commits (based on SHA) are present, and then sorts
        them in chronological order based on their timestamp.

        Returns:
            List[Dict[str, Any]]: Aggregated and sorted list of entries.
        """
        commit_entries = self.fetch_commits()
        pr_entries = self.fetch_pull_requests()
        try:
            issue_entries = self.fetch_issues()
        except Exception:
            issue_entries = []

        all_entries = pr_entries + commit_entries + issue_entries

        # For commit-related entries, remove duplicates (if any) based on SHA.
        unique_entries = {}
        for entry in all_entries:
            if entry.get("type") in ["commit", "commit_from_pr"]:
                sha = entry.get("sha")
                if sha in unique_entries:
                    continue
                unique_entries[sha] = entry
            else:
                # For pull requests and issues, we can create a unique key.
                key = f"{entry['type']}_{entry['repo']}_{entry['timestamp']}"
                unique_entries[key] = entry

        final_entries = list(unique_entries.values())
        # Sort all entries by their timestamp.
        final_entries.sort(key=lambda x: x["timestamp"])
        return self.convert_timestamps_to_str(final_entries)

    @staticmethod
    def convert_timestamps_to_str(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Converts the timestamp field from datetime to string format for each entry in the list.

        Args:
            entries (List[Dict[str, Any]]): List of entries with possible datetime timestamps.

        Returns:
            List[Dict[str, Any]]: Entries with timestamps as ISO-formatted strings.
        """
        for entry in entries:
            if isinstance(entry.get("timestamp"), datetime):
                entry["timestamp"] = entry["timestamp"].isoformat()
        return entries