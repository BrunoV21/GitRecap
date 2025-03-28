import pytest
from datetime import datetime
from git_recap.utils import parse_entries_to_txt  # assuming you placed the parser function in utils.py

def test_parse_entries_to_txt():
    # Example list of entries
    entries = [
        {
            "type": "commit_from_pr",
            "repo": "AiCore",
            "message": "feat: update TODOs for ObservabilityDashboard",
            "timestamp": "2025-03-14T00:17:02+00:00",
            "sha": "dummysha1",
            "pr_title": "Unified ai integration error monitoring"
        },
        {
            "type": "commit",
            "repo": "AiCore",
            "message": "Merge pull request #5 from somebranch",
            "timestamp": "2025-03-15T21:47:12+00:00",
            "sha": "dummysha2"
        },
        {
            "type": "pull_request",
            "repo": "AiCore",
            "message": "Unified ai integration error monitoring",
            "timestamp": "2025-03-15T21:47:13+00:00",
            "pr_number": 5
        },
        {
            "type": "issue",
            "repo": "AiCore",
            "message": "Issue: error when launching app",
            "timestamp": "2025-03-15T23:00:00+00:00",
        },
    ]
    txt = parse_entries_to_txt(entries)
    
    # Check that day headers are present
    assert "2025-03-14:" in txt
    assert "2025-03-15:" in txt
    
    # Check that key message parts appear
    assert "Feat: Update TodoS for Observabilitydashboard" in txt or "update TODOs" in txt
    assert "Unified ai integration error monitoring" in txt
    assert "Merge pull request" in txt
    assert "Issue: error when launching app" in txt

    # Check that individual timestamps and sha are not in the final output
    assert "dummysha1" not in txt
    assert "dummysha2" not in txt
    assert "T00:17:02" not in txt  # individual timestamp should not be printed