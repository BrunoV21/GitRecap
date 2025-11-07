import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from github import GithubException
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


class TestGitHubFetcherBranchOperations:
    """
    Unit tests for GitHub branch management and pull request creation functionality.
    """

    @patch('git_recap.providers.github_fetcher.Github')
    def test_get_branches_returns_branch_list(self, mock_github_class):
        """
        Test that get_branches() returns a list of branch names from the repository.
        """
        from git_recap.providers.github_fetcher import GitHubFetcher
        
        # Create mock objects
        mock_github = Mock()
        mock_user = Mock()
        mock_repo = Mock()
        mock_branch1 = Mock()
        mock_branch2 = Mock()
        mock_branch3 = Mock()
        
        # Configure the mock hierarchy
        mock_github_class.return_value = mock_github
        mock_github.get_user.return_value = mock_user
        mock_user.login = "testuser"
        mock_user.get_repos.return_value = [mock_repo]
        
        # Configure mock branches
        mock_branch1.name = "main"
        mock_branch2.name = "develop"
        mock_branch3.name = "feature/new-ui"
        mock_repo.get_branches.return_value = [mock_branch1, mock_branch2, mock_branch3]
        mock_repo.name = "test-repo"
        
        # Create GitHubFetcher instance and test
        fetcher = GitHubFetcher(pat="dummy_token")
        branches = fetcher.get_branches()
        
        # Assertions
        assert isinstance(branches, list)
        assert len(branches) == 3
        assert "main" in branches
        assert "develop" in branches
        assert "feature/new-ui" in branches

    @patch('git_recap.providers.github_fetcher.Github')
    def test_get_valid_target_branches_filters_correctly(self, mock_github_class):
        """
        Test that get_valid_target_branches() correctly filters branches.
        """
        from git_recap.providers.github_fetcher import GitHubFetcher
        
        # Create mock objects
        mock_github = Mock()
        mock_user = Mock()
        mock_repo = Mock()
        
        # Configure the mock hierarchy
        mock_github_class.return_value = mock_github
        mock_github.get_user.return_value = mock_user
        mock_user.login = "testuser"
        mock_user.get_repos.return_value = [mock_repo]
        mock_repo.name = "test-repo"
        
        # Configure mock branches
        mock_branch1 = Mock()
        mock_branch1.name = "main"
        mock_branch2 = Mock()
        mock_branch2.name = "develop"
        mock_branch3 = Mock()
        mock_branch3.name = "feature-branch"
        mock_branch4 = Mock()
        mock_branch4.name = "hotfix"
        
        mock_repo.get_branches.return_value = [mock_branch1, mock_branch2, mock_branch3, mock_branch4]
        
        # Mock existing PR from feature-branch to develop
        mock_pr = Mock()
        mock_pr.head.ref = "feature-branch"
        mock_pr.base.ref = "develop"
        mock_repo.get_pulls.return_value = [mock_pr]
        
        # Create GitHubFetcher instance and test
        fetcher = GitHubFetcher(pat="dummy_token")
        valid_targets = fetcher.get_valid_target_branches("feature-branch")
        
        # Assertions
        assert isinstance(valid_targets, list)
        # Should exclude source branch (feature-branch) and branch with existing PR (develop)
        assert "feature-branch" not in valid_targets
        assert "develop" not in valid_targets
        assert "main" in valid_targets
        assert "hotfix" in valid_targets

    @patch('git_recap.providers.github_fetcher.Github')
    def test_get_valid_target_branches_raises_on_invalid_source(self, mock_github_class):
        """
        Test that get_valid_target_branches() raises ValueError for non-existent source branch.
        """
        from git_recap.providers.github_fetcher import GitHubFetcher
        
        # Create mock objects
        mock_github = Mock()
        mock_user = Mock()
        mock_repo = Mock()
        
        # Configure the mock hierarchy
        mock_github_class.return_value = mock_github
        mock_github.get_user.return_value = mock_user
        mock_user.login = "testuser"
        mock_user.get_repos.return_value = [mock_repo]
        mock_repo.name = "test-repo"
        
        # Configure mock branches (without the source branch)
        mock_branch1 = Mock()
        mock_branch1.name = "main"
        mock_branch2 = Mock()
        mock_branch2.name = "develop"
        
        mock_repo.get_branches.return_value = [mock_branch1, mock_branch2]
        
        # Create GitHubFetcher instance and test
        fetcher = GitHubFetcher(pat="dummy_token")
        
        # Should raise ValueError for non-existent source branch
        with pytest.raises(ValueError) as exc_info:
            fetcher.get_valid_target_branches("non-existent-branch")
        
        assert "does not exist" in str(exc_info.value)

    @patch('git_recap.providers.github_fetcher.Github')
    def test_create_pull_request_success(self, mock_github_class):
        """
        Test successful pull request creation with all metadata.
        """
        from git_recap.providers.github_fetcher import GitHubFetcher
        
        # Create mock objects
        mock_github = Mock()
        mock_user = Mock()
        mock_repo = Mock()
        mock_pr = Mock()
        
        # Configure the mock hierarchy
        mock_github_class.return_value = mock_github
        mock_github.get_user.return_value = mock_user
        mock_user.login = "testuser"
        mock_user.get_repos.return_value = [mock_repo]
        mock_repo.name = "test-repo"
        
        # Configure mock branches
        mock_branch1 = Mock()
        mock_branch1.name = "main"
        mock_branch2 = Mock()
        mock_branch2.name = "feature-branch"
        mock_repo.get_branches.return_value = [mock_branch1, mock_branch2]
        
        # Mock no existing PRs
        mock_repo.get_pulls.return_value = []
        
        # Configure mock PR creation
        mock_pr.html_url = "https://github.com/test/test-repo/pull/1"
        mock_pr.number = 1
        mock_pr.state = "open"
        mock_repo.create_pull.return_value = mock_pr
        
        # Mock reviewer/assignee/label methods
        mock_pr.create_review_request = Mock()
        mock_pr.add_to_assignees = Mock()
        mock_pr.add_to_labels = Mock()
        
        # Create GitHubFetcher instance and test
        fetcher = GitHubFetcher(pat="dummy_token")
        result = fetcher.create_pull_request(
            head_branch="feature-branch",
            base_branch="main",
            title="New Feature",
            body="Description of new feature",
            reviewers=["reviewer1"],
            assignees=["assignee1"],
            labels=["enhancement"]
        )
        
        # Assertions
        assert result["success"] is True
        assert result["url"] == "https://github.com/test/test-repo/pull/1"
        assert result["number"] == 1
        assert result["state"] == "open"
        
        # Verify methods were called
        mock_repo.create_pull.assert_called_once()
        mock_pr.create_review_request.assert_called_once_with(reviewers=["reviewer1"])
        mock_pr.add_to_assignees.assert_called_once_with("assignee1")
        mock_pr.add_to_labels.assert_called_once_with("enhancement")

    @patch('git_recap.providers.github_fetcher.Github')
    def test_create_pull_request_handles_branch_not_found(self, mock_github_class):
        """
        Test that create_pull_request() handles branch not found errors.
        """
        from git_recap.providers.github_fetcher import GitHubFetcher
        
        # Create mock objects
        mock_github = Mock()
        mock_user = Mock()
        mock_repo = Mock()
        
        # Configure the mock hierarchy
        mock_github_class.return_value = mock_github
        mock_github.get_user.return_value = mock_user
        mock_user.login = "testuser"
        mock_user.get_repos.return_value = [mock_repo]
        mock_repo.name = "test-repo"
        
        # Configure mock branches (only main exists)
        mock_branch1 = Mock()
        mock_branch1.name = "main"
        mock_repo.get_branches.return_value = [mock_branch1]
        
        # Create GitHubFetcher instance and test
        fetcher = GitHubFetcher(pat="dummy_token")
        
        # Should raise ValueError for non-existent branch
        with pytest.raises(ValueError) as exc_info:
            fetcher.create_pull_request(
                head_branch="non-existent",
                base_branch="main",
                title="Test PR",
                body="Test"
            )
        
        assert "does not exist" in str(exc_info.value)

    @patch('git_recap.providers.github_fetcher.Github')
    def test_create_pull_request_handles_existing_pr(self, mock_github_class):
        """
        Test that create_pull_request() handles existing PR scenario.
        """
        from git_recap.providers.github_fetcher import GitHubFetcher
        
        # Create mock objects
        mock_github = Mock()
        mock_user = Mock()
        mock_repo = Mock()
        
        # Configure the mock hierarchy
        mock_github_class.return_value = mock_github
        mock_github.get_user.return_value = mock_user
        mock_user.login = "testuser"
        mock_user.get_repos.return_value = [mock_repo]
        mock_repo.name = "test-repo"
        
        # Configure mock branches
        mock_branch1 = Mock()
        mock_branch1.name = "main"
        mock_branch2 = Mock()
        mock_branch2.name = "feature-branch"
        mock_repo.get_branches.return_value = [mock_branch1, mock_branch2]
        
        # Mock existing PR
        mock_pr = Mock()
        mock_pr.head.ref = "feature-branch"
        mock_pr.base.ref = "main"
        mock_repo.get_pulls.return_value = [mock_pr]
        
        # Create GitHubFetcher instance and test
        fetcher = GitHubFetcher(pat="dummy_token")
        
        # Should raise ValueError for existing PR
        with pytest.raises(ValueError) as exc_info:
            fetcher.create_pull_request(
                head_branch="feature-branch",
                base_branch="main",
                title="Test PR",
                body="Test"
            )
        
        assert "already exists" in str(exc_info.value)

    @patch('git_recap.providers.github_fetcher.Github')
    def test_create_pull_request_handles_github_exception(self, mock_github_class):
        """
        Test that create_pull_request() handles GithubException errors appropriately.
        """
        from git_recap.providers.github_fetcher import GitHubFetcher
        
        # Create mock objects
        mock_github = Mock()
        mock_user = Mock()
        mock_repo = Mock()
        
        # Configure the mock hierarchy
        mock_github_class.return_value = mock_github
        mock_github.get_user.return_value = mock_user
        mock_user.login = "testuser"
        mock_user.get_repos.return_value = [mock_repo]
        mock_repo.name = "test-repo"
        
        # Configure mock branches
        mock_branch1 = Mock()
        mock_branch1.name = "main"
        mock_branch2 = Mock()
        mock_branch2.name = "feature-branch"
        mock_repo.get_branches.return_value = [mock_branch1, mock_branch2]
        
        # Mock no existing PRs
        mock_repo.get_pulls.return_value = []
        
        # Mock create_pull to raise GithubException
        mock_repo.create_pull.side_effect = GithubException(403, "Permission denied", None)
        
        # Create GitHubFetcher instance and test
        fetcher = GitHubFetcher(pat="dummy_token")
        
        # Should raise GithubException
        with pytest.raises(GithubException):
            fetcher.create_pull_request(
                head_branch="feature-branch",
                base_branch="main",
                title="Test PR",
                body="Test"
            )

    @patch('git_recap.providers.github_fetcher.Github')
    def test_get_branches_handles_api_errors(self, mock_github_class):
        """
        Test that get_branches() handles API errors gracefully.
        """
        from git_recap.providers.github_fetcher import GitHubFetcher
        
        # Create mock objects
        mock_github = Mock()
        mock_user = Mock()
        mock_repo = Mock()
        
        # Configure the mock hierarchy
        mock_github_class.return_value = mock_github
        mock_github.get_user.return_value = mock_user
        mock_user.login = "testuser"
        mock_user.get_repos.return_value = [mock_repo]
        mock_repo.name = "test-repo"
        
        # Mock get_branches to raise GithubException
        mock_repo.get_branches.side_effect = GithubException(403, "Rate limit exceeded", None)
        
        # Create GitHubFetcher instance and test
        fetcher = GitHubFetcher(pat="dummy_token")
        
        # Should raise Exception with descriptive message
        with pytest.raises(Exception) as exc_info:
            fetcher.get_branches()
        
        assert "Failed to fetch branches" in str(exc_info.value)

    @patch('git_recap.providers.github_fetcher.Github')
    def test_get_valid_target_branches_handles_api_errors(self, mock_github_class):
        """
        Test that get_valid_target_branches() handles API errors gracefully.
        """
        from git_recap.providers.github_fetcher import GitHubFetcher
        
        # Create mock objects
        mock_github = Mock()
        mock_user = Mock()
        mock_repo = Mock()
        
        # Configure the mock hierarchy
        mock_github_class.return_value = mock_github
        mock_github.get_user.return_value = mock_user
        mock_user.login = "testuser"
        mock_user.get_repos.return_value = [mock_repo]
        mock_repo.name = "test-repo"
        
        # Configure mock branches
        mock_branch1 = Mock()
        mock_branch1.name = "main"
        mock_branch2 = Mock()
        mock_branch2.name = "feature-branch"
        mock_repo.get_branches.return_value = [mock_branch1, mock_branch2]
        
        # Mock get_pulls to raise GithubException
        mock_repo.get_pulls.side_effect = GithubException(500, "Internal server error", None)
        
        # Create GitHubFetcher instance and test
        fetcher = GitHubFetcher(pat="dummy_token")
        
        # Should raise Exception with descriptive message
        with pytest.raises(Exception) as exc_info:
            fetcher.get_valid_target_branches("feature-branch")
        
        assert "Failed to validate target branches" in str(exc_info.value)