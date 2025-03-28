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
        authors: Optional[List[str]]=None
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
        
    @abstractmethod
    def fetch_commits(self) -> List[str]:
        pass

    @abstractmethod
    def fetch_pull_requests(self) -> List[str]:
        pass

    @abstractmethod
    def fetch_issues(self) -> List[str]:
        pass

    def get_authored_messages(self, limit: Optional[int]=None) -> List[str]:
        """
        Aggregates all messages from commits, pull requests, issues,
        and code reviews authored by the user, returning a limited list.
        """
        if limit:
            self.limit = limit
        messages = []
        # messages.extend(self.fetch_commits())
        messages.extend(self.fetch_pull_requests())
        # messages.extend(self.fetch_issues())
        return messages
    
    @staticmethod
    def convert_timestamps_to_str(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Converts the timestamp field from datetime to string format for each entry in the list.
        """
        for entry in entries:
            if isinstance(entry.get("timestamp"), datetime):
                entry["timestamp"] = entry["timestamp"].isoformat()
        return entries