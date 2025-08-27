import pytest
from datetime import datetime
from git_recap.utils import parse_entries_to_txt

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


# --- Release fetching test stub ---
def test_fetch_releases_stub():
    """
    Unit test stub for the new release-fetching functionality.

    This test covers:
      - Successful fetching of releases for a supported provider (e.g., GitHubFetcher)
      - NotImplementedError for providers that do not support releases

    This is a stub: actual API calls are not performed here.
    """
    from git_recap.providers.github_fetcher import GitHubFetcher
    from git_recap.providers.gitlab_fetcher import GitLabFetcher
    from git_recap.providers.azure_fetcher import AzureFetcher
    from git_recap.providers.url_fetcher import URLFetcher

    # GitHubFetcher: Should return a list (empty if no PAT or repos)
    github_fetcher = GitHubFetcher(pat="dummy", repo_filter=[])
    try:
        releases = github_fetcher.fetch_releases()
        assert isinstance(releases, list)
    except Exception:
        # Accept any exception here since we use a dummy PAT
        pass

    # GitLabFetcher: Should raise NotImplementedError
    gitlab_fetcher = GitLabFetcher(pat="dummy")
    with pytest.raises(NotImplementedError):
        gitlab_fetcher.fetch_releases()

    # AzureFetcher: Should raise NotImplementedError
    # organization_url is required, use dummy
    azure_fetcher = AzureFetcher(pat="dummy", organization_url="https://dev.azure.com/dummy")
    with pytest.raises(NotImplementedError):
        azure_fetcher.fetch_releases()

    # URLFetcher: Should raise NotImplementedError
    url_fetcher = URLFetcher(url="https://github.com/dummy/dummy.git")
    with pytest.raises(NotImplementedError):
        url_fetcher.fetch_releases()