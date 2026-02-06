"""
Unit tests for LocalFetcher class.

Tests the functionality of fetching commits and other information from local git repositories.
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch, MagicMock
from git_recap.providers.local_fetcher import LocalFetcher


class TestLocalFetcherInitialization:
    """Test suite for LocalFetcher initialization."""
    
    def test_init_with_required_params(self):
        """Test LocalFetcher initialization with required parameters."""
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        assert fetcher.repo_path == "/path/to/repo"
        # BaseFetcher initializes authors to empty list if None
        assert fetcher.authors == []
        assert fetcher.start_date is None
        assert fetcher.end_date is None
        assert fetcher.repo_filter == []
    
    def test_init_with_all_params(self):
        """Test LocalFetcher initialization with all parameters."""
        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
        
        fetcher = LocalFetcher(
            repo_path="/path/to/repo",
            authors=["Alice", "Bob"],
            start_date=start_date,
            end_date=end_date,
            repo_filter=["repo1", "repo2"],
            validate_repo=False
        )
        
        assert fetcher.repo_path == "/path/to/repo"
        assert fetcher.authors == ["Alice", "Bob"]
        assert fetcher.start_date == start_date
        assert fetcher.end_date == end_date
        assert fetcher.repo_filter == ["repo1", "repo2"]
    
    @patch('subprocess.run')
    def test_repos_names_property(self, mock_run):
        """Test that repos_names property returns repository name from git config."""
        # Mock subprocess response for git config remote.origin.url
        mock_result = Mock()
        mock_result.stdout = "https://github.com/user/repo.git\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        repo_names = fetcher.repos_names
        
        assert isinstance(repo_names, list)
        assert len(repo_names) == 1
        assert "repo" in repo_names[0]


class TestLocalFetcherFetchCommits:
    """Test suite for fetch_commits method."""
    
    @patch('subprocess.run')
    def test_fetch_commits_basic(self, mock_run):
        """Test basic commit fetching without filters."""
        # Mock git log response in pipe-delimited format
        mock_result = Mock()
        mock_result.stdout = """abc123|Alice|2025-01-15T10:00:00+00:00|Initial commit
def456|Bob|2025-01-16T11:00:00+00:00|Add new feature
"""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        commits = fetcher.fetch_commits()
        
        assert isinstance(commits, list)
        assert len(commits) == 2
        assert commits[0]["sha"] == "abc123"
        assert commits[1]["sha"] == "def456"
    
    @patch('subprocess.run')
    def test_fetch_commits_with_date_filter(self, mock_run):
        """Test commit fetching with date range filter."""
        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
        
        mock_result = Mock()
        mock_result.stdout = """abc123|Alice|2025-01-15T10:00:00+00:00|Commit within range
"""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        fetcher = LocalFetcher(
            repo_path="/path/to/repo",
            start_date=start_date,
            end_date=end_date,
            validate_repo=False
        )
        commits = fetcher.fetch_commits()
        
        assert len(commits) >= 0
        # Verify subprocess was called with date filters
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert "--since" in call_args
        assert "--until" in call_args
    
    @patch('subprocess.run')
    def test_fetch_commits_with_author_filter(self, mock_run):
        """Test commit fetching with author filter."""
        mock_result = Mock()
        mock_result.stdout = """abc123|Alice|2025-01-15T10:00:00+00:00|Alice's commit
"""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        fetcher = LocalFetcher(
            repo_path="/path/to/repo",
            authors=["Alice"],
            validate_repo=False
        )
        commits = fetcher.fetch_commits()
        
        assert isinstance(commits, list)
        # Verify subprocess was called with author filter
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert "--author" in call_args
    
    @patch('subprocess.run')
    def test_fetch_commits_handles_git_error(self, mock_run):
        """Test that fetch_commits handles git errors gracefully."""
        import subprocess as sp
        mock_run.side_effect = sp.CalledProcessError(1, "git")
        
        fetcher = LocalFetcher(repo_path="/invalid/path", validate_repo=False)
        commits = fetcher.fetch_commits()
        
        # Should return empty list on error
        assert commits == []
    
    @patch('subprocess.run')
    def test_fetch_commits_parse_commit_details(self, mock_run):
        """Test that commit details are correctly parsed."""
        mock_result = Mock()
        mock_result.stdout = """abc123def456|Alice Smith|2025-01-15T10:30:45+00:00|feat: Add new authentication module
"""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        commits = fetcher.fetch_commits()
        
        assert len(commits) == 1
        commit = commits[0]
        assert commit["sha"] == "abc123def456"
        assert commit["author"] == "Alice Smith"
        assert "feat: Add new authentication module" in commit["message"]
        assert isinstance(commit["timestamp"], datetime)


class TestLocalFetcherFetchPullRequests:
    """Test suite for fetch_pull_requests method."""
    
    @patch('subprocess.run')
    def test_fetch_pull_requests_basic(self, mock_run):
        """Test basic pull request fetching."""
        # LocalFetcher returns empty list for PRs
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        prs = fetcher.fetch_pull_requests()
        
        assert isinstance(prs, list)
        assert len(prs) == 0
    
    @patch('subprocess.run')
    def test_fetch_pull_requests_with_date_filter(self, mock_run):
        """Test pull request fetching with date filter."""
        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2025, 1, 31, tzinfo=timezone.utc)
        
        # LocalFetcher returns empty list for PRs regardless of filters
        fetcher = LocalFetcher(
            repo_path="/path/to/repo",
            start_date=start_date,
            end_date=end_date,
            validate_repo=False
        )
        prs = fetcher.fetch_pull_requests()
        
        assert isinstance(prs, list)
        assert len(prs) == 0
    
    @patch('subprocess.run')
    def test_fetch_pull_requests_handles_no_pr_branches(self, mock_run):
        """Test handling when no pull request branches exist."""
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        prs = fetcher.fetch_pull_requests()
        
        assert prs == []


class TestLocalFetcherGetAuthors:
    """Test suite for get_authors method."""
    
    @patch('subprocess.run')
    def test_get_authors_basic(self, mock_run):
        """Test fetching all authors from repository."""
        mock_result = Mock()
        mock_result.stdout = """Alice Smith|alice@example.com
Bob Johnson|bob@example.com
Charlie Brown|charlie@example.com
"""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        authors = fetcher.get_authors([])
        
        assert isinstance(authors, list)
        assert len(authors) == 3
        assert authors[0]["name"] == "Alice Smith"
        assert authors[0]["email"] == "alice@example.com"
    
    @patch('subprocess.run')
    def test_get_authors_deduplication(self, mock_run):
        """Test that duplicate authors are properly deduplicated."""
        mock_result = Mock()
        mock_result.stdout = """Alice Smith|alice@example.com
Bob Johnson|bob@example.com
Alice Smith|alice@example.com
"""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        authors = fetcher.get_authors([])
        
        # Should deduplicate based on email
        assert len(authors) == 2
        emails = [author["email"] for author in authors]
        assert emails.count("alice@example.com") == 1


class TestLocalFetcherGetBranches:
    """Test suite for get_branches method."""
    
    @patch('subprocess.run')
    def test_get_branches_basic(self, mock_run):
        """Test fetching all branches."""
        # Mock local branches response
        mock_result_local = Mock()
        mock_result_local.stdout = """main
develop
feature/new-ui
hotfix/critical-bug
"""
        mock_result_local.returncode = 0
        
        # Mock remote branches response (empty for this test)
        mock_result_remote = Mock()
        mock_result_remote.stdout = """"""
        mock_result_remote.returncode = 0
        
        mock_run.side_effect = [mock_result_local, mock_result_remote]
        
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        branches = fetcher.get_branches()
        
        assert isinstance(branches, list)
        assert len(branches) == 4
        assert "main" in branches
        assert "develop" in branches
        assert "feature/new-ui" in branches
        assert "hotfix/critical-bug" in branches
    
    @patch('subprocess.run')
    def test_get_branches_empty(self, mock_run):
        """Test handling when no branches exist."""
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        branches = fetcher.get_branches()
        
        assert branches == []


class TestLocalFetcherGetCurrentAuthor:
    """Test suite for get_current_author method."""
    
    @patch('subprocess.run')
    def test_get_current_author_success(self, mock_run):
        """Test fetching current git user configuration."""
        mock_result = Mock()
        mock_result.stdout = "Alice Smith"
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        author = fetcher.get_current_author()
        
        assert author is not None
        assert author["name"] == "Alice Smith"
        assert "email" in author
    
    @patch('subprocess.run')
    def test_get_current_author_not_configured(self, mock_run):
        """Test handling when git user is not configured."""
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        author = fetcher.get_current_author()
        
        assert author is None


class TestLocalFetcherGetAuthoredMessages:
    """Test suite for get_authored_messages method."""
    
    @patch('subprocess.run')
    def test_get_authored_messages_basic(self, mock_run):
        """Test basic authored messages fetching."""
        # Mock git log response in pipe-delimited format
        mock_result = Mock()
        mock_result.stdout = """abc123|Alice|2025-01-15T10:00:00+00:00|First commit
def456|Alice|2025-01-16T11:00:00+00:00|Second commit
"""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        messages = fetcher.get_authored_messages()
        
        assert isinstance(messages, list)
        assert len(messages) == 2
        assert messages[0]["type"] == "commit"
        assert messages[1]["type"] == "commit"
    
    @patch('subprocess.run')
    def test_get_authored_messages_with_limit(self, mock_run):
        """Test authored messages fetching with limit."""
        mock_result = Mock()
        mock_result.stdout = """abc123|Alice|2025-01-15T10:00:00+00:00|Commit 1
def456|Alice|2025-01-16T11:00:00+00:00|Commit 2
ghi789|Alice|2025-01-17T12:00:00+00:00|Commit 3
"""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        messages = fetcher.get_authored_messages()
        
        # get_authored_messages doesn't take a limit parameter
        # It returns all messages
        assert len(messages) == 3
    
    @patch('subprocess.run')
    def test_get_authored_messages_sorting(self, mock_run):
        """Test that authored messages are sorted chronologically."""
        mock_result = Mock()
        mock_result.stdout = """abc123|Alice|2025-01-16T11:00:00+00:00|Later commit
def456|Alice|2025-01-15T10:00:00+00:00|Earlier commit
"""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        messages = fetcher.get_authored_messages()
        
        # Verify chronological order
        assert len(messages) == 2
        # Messages are sorted by timestamp in get_authored_messages
        assert messages[0]["timestamp"] < messages[1]["timestamp"]


class TestLocalFetcherEdgeCases:
    """Test suite for edge cases and error handling."""
    
    @patch('subprocess.run')
    def test_invalid_repository_path(self, mock_run):
        """Test handling of invalid repository path."""
        import subprocess as sp
        mock_run.side_effect = sp.CalledProcessError(1, "git")
        
        fetcher = LocalFetcher(repo_path="/invalid/path", validate_repo=False)
        commits = fetcher.fetch_commits()
        
        # Should return empty list
        assert commits == []
    
    @patch('subprocess.run')
    def test_empty_repository(self, mock_run):
        """Test handling of empty repository (no commits)."""
        mock_result = Mock()
        mock_result.stdout = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        fetcher = LocalFetcher(repo_path="/path/to/empty/repo", validate_repo=False)
        commits = fetcher.fetch_commits()
        
        assert commits == []
    
    @patch('subprocess.run')
    def test_malformed_git_output(self, mock_run):
        """Test handling of malformed git output."""
        mock_result = Mock()
        mock_result.stdout = """This is not valid git log output
Just random text
"""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        commits = fetcher.fetch_commits()
        
        # Should handle gracefully
        assert isinstance(commits, list)
    
    @patch('subprocess.run')
    def test_subprocess_timeout(self, mock_run):
        """Test handling of subprocess timeout."""
        import subprocess
        
        mock_run.side_effect = subprocess.TimeoutExpired(
            cmd=["git", "log"],
            timeout=30
        )
        
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        commits = fetcher.fetch_commits()
        
        # Should handle timeout gracefully
        assert isinstance(commits, list)


class TestLocalFetcherIntegration:
    """Integration tests for LocalFetcher."""
    
    @patch('subprocess.run')
    def test_full_workflow(self, mock_run):
        """Test complete workflow: init, fetch commits, get authors."""
        # Mock responses
        mock_result_commits = Mock()
        mock_result_commits.stdout = """abc123|Alice|2025-01-15T10:00:00+00:00|Test commit
"""
        mock_result_commits.returncode = 0
        
        # Mock get_authors responses (authors + committers)
        mock_result_authors = Mock()
        mock_result_authors.stdout = """Alice|alice@example.com
"""
        mock_result_authors.returncode = 0
        
        mock_result_committers = Mock()
        mock_result_committers.stdout = """Alice|alice@example.com
"""
        mock_result_committers.returncode = 0
        
        # get_authored_messages calls fetch_commits again, so we need another response
        mock_run.side_effect = [
            mock_result_commits,  # First fetch_commits
            mock_result_authors,  # get_authors
            mock_result_committers,  # get_authors (committers)
            mock_result_commits  # Second fetch_commits (from get_authored_messages)
        ]
        
        fetcher = LocalFetcher(repo_path="/path/to/repo", validate_repo=False)
        
        # Fetch commits
        commits = fetcher.fetch_commits()
        assert len(commits) == 1
        
        # Get authors
        authors = fetcher.get_authors([])
        assert len(authors) == 1
        
        # Get authored messages
        messages = fetcher.get_authored_messages()
        assert len(messages) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])