from datetime import datetime, timezone
from git_recap.providers.base_fetcher import BaseFetcher

class DummyFetcher(BaseFetcher):
    def __init__(self, pat, start_date=None, end_date=None, repo_filter=None, authors=None):
        # Call BaseFetcher with provided parameters.
        # Note: authors is expected by your updated BaseFetcher.
        super().__init__(pat, start_date, end_date, repo_filter, authors)
        # For testing, if no authors are provided, we default to a dummy author.
        if authors is None:
            self.authors = ["dummy_author"]

    def fetch_commits(self):
        return [{
            "type": "commit",
            "repo": "DummyRepo",
            "message": "Dummy commit message",
            "timestamp": datetime(2025, 3, 15, 12, 0, tzinfo=timezone.utc),
            "sha": "dummysha1"
        }]

    def fetch_pull_requests(self):
        return [{
            "type": "pull_request",
            "repo": "DummyRepo",
            "message": "Dummy PR message",
            "timestamp": datetime(2025, 3, 15, 13, 0, tzinfo=timezone.utc),
            "pr_number": 1
        }]

    def fetch_issues(self):
        return [{
            "type": "issue",
            "repo": "DummyRepo",
            "message": "Dummy issue message",
            "timestamp": datetime(2025, 3, 15, 14, 0, tzinfo=timezone.utc)
        }]

    def convert_timestamps_to_str(self, entries):
        # Dummy implementation for tests: convert datetime to ISO string.
        for entry in entries:
            if isinstance(entry["timestamp"], datetime):
                entry["timestamp"] = entry["timestamp"].isoformat()
        return entries
    
    @property
    def repos_names(self):
        ...

def test_get_authored_messages():
    # Create a dummy fetcher with a date range covering March 2025.
    fetcher = DummyFetcher(
        pat="dummy",
        start_date=datetime(2025, 3, 1, tzinfo=timezone.utc),
        end_date=datetime(2025, 3, 31, tzinfo=timezone.utc),
        repo_filter=["DummyRepo"],
        authors=["dummy_author"]
    )
    messages = fetcher.get_authored_messages()
    # Expecting 3 entries: one commit, one PR, and one issue.
    assert len(messages) == 3

    # Check that messages are sorted chronologically
    timestamps = [msg["timestamp"] for msg in messages]
    assert timestamps == sorted(timestamps)

    # Ensure that commit and PR messages are present
    types = {msg["type"] for msg in messages}
    assert "commit" in types
    assert "pull_request" in types
    assert "issue" in types