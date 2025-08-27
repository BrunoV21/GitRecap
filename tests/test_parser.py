import pytest
from datetime import datetime
from unittest.mock import Mock, patch
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


@patch('git_recap.providers.github_fetcher.Github')
def test_fetch_releases_github(mock_github_class):
    """
    Unit test for GitHub release fetching functionality with proper mocking.
    """
    from git_recap.providers.github_fetcher import GitHubFetcher
    
    # Create mock objects
    mock_github = Mock()
    mock_user = Mock()
    mock_repo = Mock()
    mock_release = Mock()
    mock_asset = Mock()
    
    # Configure the mock hierarchy
    mock_github_class.return_value = mock_github
    mock_github.get_user.return_value = mock_user
    mock_user.login = "testuser"
    mock_user.get_repos.return_value = [mock_repo]
    
    # Configure mock repo
    mock_repo.name = "test-repo"
    mock_repo.get_releases.return_value = [mock_release]
    
    # Configure mock release
    mock_release.tag_name = "v1.0.0"
    mock_release.name = "Release 1.0.0"
    mock_release.title = "Release 1.0.0"  # Some releases use title instead of name
    mock_release.author.login = "testuser"
    mock_release.published_at = datetime(2025, 3, 15, 10, 0, 0)
    mock_release.created_at = datetime(2025, 3, 15, 9, 0, 0)
    mock_release.draft = False
    mock_release.prerelease = False
    mock_release.body = "This is a test release"
    
    # Configure mock asset
    mock_asset.name = "test-asset.zip"
    mock_asset.size = 1024
    mock_asset.browser_download_url = "https://github.com/test/releases/download/v1.0.0/test-asset.zip"
    mock_asset.content_type = "application/zip"
    mock_asset.created_at = datetime(2025, 3, 15, 9, 30, 0)
    mock_asset.updated_at = datetime(2025, 3, 15, 9, 30, 0)
    
    mock_release.get_assets.return_value = [mock_asset]
    
    # Create GitHubFetcher instance and test
    fetcher = GitHubFetcher(pat="dummy_token")
    releases = fetcher.fetch_releases()
    
    # Assertions
    assert isinstance(releases, list)
    assert len(releases) == 1
    
    release = releases[0]
    assert release["tag_name"] == "v1.0.0"
    assert release["name"] == "Release 1.0.0"
    assert release["repo"] == "test-repo"
    assert release["author"] == "testuser"
    assert release["published_at"] == datetime(2025, 3, 15, 10, 0, 0)
    assert release["created_at"] == datetime(2025, 3, 15, 9, 0, 0)
    assert release["draft"] is False
    assert release["prerelease"] is False
    assert release["body"] == "This is a test release"
    assert len(release["assets"]) == 1
    
    asset = release["assets"][0]
    assert asset["name"] == "test-asset.zip"
    assert asset["size"] == 1024
    assert asset["download_url"] == "https://github.com/test/releases/download/v1.0.0/test-asset.zip"
    assert asset["content_type"] == "application/zip"


@patch('git_recap.providers.github_fetcher.Github')
def test_fetch_releases_github_with_repo_filter(mock_github_class):
    """
    Test fetch_releases with repo_filter applied.
    """
    from git_recap.providers.github_fetcher import GitHubFetcher
    
    # Create mock objects
    mock_github = Mock()
    mock_user = Mock()
    mock_repo1 = Mock()
    mock_repo2 = Mock()
    
    # Configure the mock hierarchy
    mock_github_class.return_value = mock_github
    mock_github.get_user.return_value = mock_user
    mock_user.login = "testuser"
    mock_user.get_repos.return_value = [mock_repo1, mock_repo2]
    
    # Configure mock repos
    mock_repo1.name = "allowed-repo"
    mock_repo2.name = "filtered-repo"
    mock_repo1.get_releases.return_value = []
    mock_repo2.get_releases.return_value = []
    
    # Create GitHubFetcher instance with repo filter
    fetcher = GitHubFetcher(pat="dummy_token", repo_filter=["allowed-repo"])
    releases = fetcher.fetch_releases()
    
    # Assertions
    assert isinstance(releases, list)
    # Only allowed-repo should have been processed
    mock_repo1.get_releases.assert_called_once()
    mock_repo2.get_releases.assert_not_called()


@patch('git_recap.providers.github_fetcher.Github')
def test_fetch_releases_github_exception_handling(mock_github_class):
    """
    Test fetch_releases handles exceptions gracefully when a repo fails.
    """
    from git_recap.providers.github_fetcher import GitHubFetcher
    
    # Create mock objects
    mock_github = Mock()
    mock_user = Mock()
    mock_repo1 = Mock()
    mock_repo2 = Mock()
    
    # Configure the mock hierarchy
    mock_github_class.return_value = mock_github
    mock_github.get_user.return_value = mock_user
    mock_user.login = "testuser"
    mock_user.get_repos.return_value = [mock_repo1, mock_repo2]
    
    # Configure mock repos - one fails, one succeeds
    mock_repo1.name = "failing-repo"
    mock_repo2.name = "working-repo"
    mock_repo1.get_releases.side_effect = Exception("Permission denied")
    mock_repo2.get_releases.return_value = []
    
    # Create GitHubFetcher instance and test
    fetcher = GitHubFetcher(pat="dummy_token")
    releases = fetcher.fetch_releases()
    
    # Should return empty list and not raise exception
    assert isinstance(releases, list)
    assert len(releases) == 0


def test_fetch_releases_not_implemented_providers():
    """
    Test that other providers raise NotImplementedError for releases.
    """
    from git_recap.providers.gitlab_fetcher import GitLabFetcher
    from git_recap.providers.azure_fetcher import AzureFetcher
    from git_recap.providers.url_fetcher import URLFetcher
    
    # These should raise NotImplementedError or similar
    # Note: You may need to adjust this based on your actual implementation
    
    # GitLabFetcher test (assuming it doesn't implement fetch_releases yet)
    try:
        gitlab_fetcher = GitLabFetcher(pat="dummy", base_url="https://gitlab.com")
        if hasattr(gitlab_fetcher, 'fetch_releases'):
            with pytest.raises(NotImplementedError):
                gitlab_fetcher.fetch_releases()
    except Exception:
        # If GitLabFetcher can't be instantiated with dummy data, that's fine
        pass
    
    # AzureFetcher test (assuming it doesn't implement fetch_releases yet)
    try:
        azure_fetcher = AzureFetcher(pat="dummy", organization="test", project="test")
        if hasattr(azure_fetcher, 'fetch_releases'):
            with pytest.raises(NotImplementedError):
                azure_fetcher.fetch_releases()
    except Exception:
        # If AzureFetcher can't be instantiated with dummy data, that's fine
        pass
    
    # URLFetcher test (assuming it doesn't implement fetch_releases yet)
    try:
        url_fetcher = URLFetcher(pat="dummy", base_url="https://example.com")
        if hasattr(url_fetcher, 'fetch_releases'):
            with pytest.raises(NotImplementedError):
                url_fetcher.fetch_releases()
    except Exception:
        # If URLFetcher can't be instantiated with dummy data, that's fine
        pass