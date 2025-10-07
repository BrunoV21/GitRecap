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
    def get_branches(self) -> List[str]:
        """
        Get all branches in the repository.
        
        Returns:
            List[str]: List of branch names.
        
        Raises:
            NotImplementedError: Subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses must implement get_branches() to return all repository branches")

    @abstractmethod
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
            NotImplementedError: Subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses must implement get_valid_target_branches() to return valid PR target branches for the given source branch")

    @abstractmethod
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
        Create a pull request between two branches with optional metadata.
        
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
            NotImplementedError: Subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses must implement create_pull_request() to create a pull request with the specified parameters")

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