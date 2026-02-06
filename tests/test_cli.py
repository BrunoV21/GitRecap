"""
Unit tests for GitRecap CLI module.

Tests cover argument parsing, happy path execution, and error handling.
"""

import unittest
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
from io import StringIO
import sys

from git_recap.cli import (
    parse_date,
    create_parser,
    filter_entries_by_author,
    fetch_from_repos,
    main
)


class TestParseDate(unittest.TestCase):
    """Test the parse_date function."""

    def test_parse_date_with_time(self):
        """Test parsing date with time component."""
        result = parse_date("2025-01-15T14:30:00")
        expected = datetime(2025, 1, 15, 14, 30, 0)
        self.assertEqual(result, expected)

    def test_parse_date_without_time(self):
        """Test parsing date without time component."""
        result = parse_date("2025-01-15")
        expected = datetime(2025, 1, 15, 0, 0, 0)
        self.assertEqual(result, expected)

    def test_parse_date_invalid_format(self):
        """Test parsing invalid date format raises error."""
        from argparse import ArgumentTypeError
        with self.assertRaises(ArgumentTypeError):
            parse_date("invalid-date")


class TestCreateParser(unittest.TestCase):
    """Test the argument parser creation."""

    def setUp(self):
        """Set up test parser."""
        self.parser = create_parser()

    def test_parser_has_required_arguments(self):
        """Test parser has all required arguments."""
        # Test with minimal arguments
        args = self.parser.parse_args(["."])
        self.assertEqual(args.paths, ["."])
        self.assertIsNone(args.author)
        self.assertIsNone(args.start_date)
        self.assertIsNone(args.end_date)
        self.assertIsNone(args.output)

    def test_parser_with_author(self):
        """Test parser accepts author argument."""
        args = self.parser.parse_args([".", "--author", "John Doe"])
        self.assertEqual(args.author, "John Doe")

    def test_parser_with_dates(self):
        """Test parser accepts date arguments."""
        args = self.parser.parse_args([
            ".",
            "--start-date", "2025-01-01",
            "--end-date", "2025-01-31"
        ])
        self.assertEqual(args.start_date, datetime(2025, 1, 1))
        self.assertEqual(args.end_date, datetime(2025, 1, 31))

    def test_parser_with_output(self):
        """Test parser accepts output argument."""
        args = self.parser.parse_args([".", "--output", "summary.txt"])
        self.assertEqual(args.output, "summary.txt")

    def test_parser_with_multiple_paths(self):
        """Test parser accepts multiple repository paths."""
        args = self.parser.parse_args(["/path/to/repo1", "/path/to/repo2", "/path/to/repo3"])
        self.assertEqual(args.paths, ["/path/to/repo1", "/path/to/repo2", "/path/to/repo3"])

    def test_parser_with_short_output_flag(self):
        """Test parser accepts short output flag."""
        args = self.parser.parse_args([".", "-o", "summary.txt"])
        self.assertEqual(args.output, "summary.txt")


class TestFilterEntriesByAuthor(unittest.TestCase):
    """Test the filter_entries_by_author function."""

    def setUp(self):
        """Set up test entries."""
        self.entries = [
            {"author": "John Doe", "message": "Commit 1"},
            {"author": "Jane Smith", "message": "Commit 2"},
            {"author": "John Doe", "message": "Commit 3"},
            {"author": "Bob Johnson", "message": "Commit 4"},
        ]

    def test_filter_by_full_name(self):
        """Test filtering by full author name."""
        result = filter_entries_by_author(self.entries, "John Doe")
        self.assertEqual(len(result), 2)
        self.assertTrue(all(e["author"] == "John Doe" for e in result))

    def test_filter_by_partial_name(self):
        """Test filtering by partial author name."""
        result = filter_entries_by_author(self.entries, "John")
        self.assertEqual(len(result), 3)
        self.assertTrue(all("John" in e["author"] for e in result))

    def test_filter_case_insensitive(self):
        """Test filtering is case insensitive."""
        result = filter_entries_by_author(self.entries, "john doe")
        self.assertEqual(len(result), 2)

    def test_filter_no_matches(self):
        """Test filtering with no matches."""
        result = filter_entries_by_author(self.entries, "Unknown Author")
        self.assertEqual(len(result), 0)

    def test_filter_empty_entries(self):
        """Test filtering empty entries list."""
        result = filter_entries_by_author([], "John Doe")
        self.assertEqual(len(result), 0)


class TestFetchFromRepos(unittest.TestCase):
    """Test the fetch_from_repos function."""

    @patch('git_recap.cli.LocalFetcher')
    def test_fetch_from_single_repo(self, mock_fetcher_class):
        """Test fetching from a single repository."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_commits.return_value = [
            {"author": "John Doe", "message": "Commit 1"}
        ]
        mock_fetcher_class.return_value = mock_fetcher

        result = fetch_from_repos(["/path/to/repo"])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["author"], "John Doe")
        mock_fetcher_class.assert_called_once_with(
            repo_path="/path/to/repo",
            authors=None,
            start_date=None,
            end_date=None,
            validate_repo=True
        )

    @patch('git_recap.cli.LocalFetcher')
    def test_fetch_from_multiple_repos(self, mock_fetcher_class):
        """Test fetching from multiple repositories."""
        mock_fetcher1 = MagicMock()
        mock_fetcher1.fetch_commits.return_value = [
            {"author": "John Doe", "message": "Commit 1"}
        ]
        mock_fetcher2 = MagicMock()
        mock_fetcher2.fetch_commits.return_value = [
            {"author": "Jane Smith", "message": "Commit 2"}
        ]
        mock_fetcher_class.side_effect = [mock_fetcher1, mock_fetcher2]

        result = fetch_from_repos(["/path/to/repo1", "/path/to/repo2"])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["author"], "John Doe")
        self.assertEqual(result[1]["author"], "Jane Smith")

    @patch('git_recap.cli.LocalFetcher')
    def test_fetch_with_authors_filter(self, mock_fetcher_class):
        """Test fetching with authors filter."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_commits.return_value = []
        mock_fetcher_class.return_value = mock_fetcher

        fetch_from_repos(["/path/to/repo"], authors=["John Doe"])
        mock_fetcher_class.assert_called_once_with(
            repo_path="/path/to/repo",
            authors=["John Doe"],
            start_date=None,
            end_date=None,
            validate_repo=True
        )

    @patch('git_recap.cli.LocalFetcher')
    def test_fetch_with_date_filter(self, mock_fetcher_class):
        """Test fetching with date filter."""
        mock_fetcher = MagicMock()
        mock_fetcher.fetch_commits.return_value = []
        mock_fetcher_class.return_value = mock_fetcher

        start_date = datetime(2025, 1, 1)
        end_date = datetime(2025, 1, 31)
        fetch_from_repos(["/path/to/repo"], start_date=start_date, end_date=end_date)
        mock_fetcher_class.assert_called_once_with(
            repo_path="/path/to/repo",
            authors=None,
            start_date=start_date,
            end_date=end_date,
            validate_repo=True
        )

    @patch('git_recap.cli.LocalFetcher')
    def test_fetch_handles_invalid_repo(self, mock_fetcher_class):
        """Test fetching handles invalid repository gracefully."""
        mock_fetcher_class.side_effect = ValueError("Invalid repository")

        with patch('sys.stderr', new_callable=StringIO):
            result = fetch_from_repos(["/invalid/repo"])
        self.assertEqual(len(result), 0)

    @patch('git_recap.cli.LocalFetcher')
    def test_fetch_handles_exception(self, mock_fetcher_class):
        """Test fetching handles unexpected exceptions."""
        mock_fetcher_class.side_effect = Exception("Unexpected error")

        with patch('sys.stderr', new_callable=StringIO):
            result = fetch_from_repos(["/path/to/repo"])
        self.assertEqual(len(result), 0)


class TestMain(unittest.TestCase):
    """Test the main function."""

    @patch('git_recap.cli.fetch_from_repos')
    @patch('git_recap.cli.parse_entries_to_txt')
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_basic_usage(self, mock_stdout, mock_parse, mock_fetch):
        """Test main function with basic usage."""
        mock_fetch.return_value = [
            {
                "author": "John Doe",
                "message": "Commit 1",
                "timestamp": datetime(2025, 1, 15),
                "repo": "test-repo",
                "type": "commit"
            }
        ]
        mock_parse.return_value = "2025-01-15:\n - [Commit] in test-repo: Commit 1"

        with patch('sys.argv', ['git-recap', '.']):
            exit_code = main()
        
        self.assertEqual(exit_code, 0)
        self.assertIn("Commit 1", mock_stdout.getvalue())

    @patch('git_recap.cli.fetch_from_repos')
    @patch('git_recap.cli.parse_entries_to_txt')
    @patch('git_recap.cli.Path')
    def test_main_with_output_file(self, mock_path, mock_parse, mock_fetch):
        """Test main function with output file."""
        mock_fetch.return_value = [
            {
                "author": "John Doe",
                "message": "Commit 1",
                "timestamp": datetime(2025, 1, 15),
                "repo": "test-repo",
                "type": "commit"
            }
        ]
        mock_parse.return_value = "2025-01-15:\n - [Commit] in test-repo: Commit 1"
        mock_output_path = MagicMock()
        mock_path.return_value = mock_output_path

        with patch('sys.argv', ['git-recap', '.', '--output', 'summary.txt']):
            exit_code = main()
        
        self.assertEqual(exit_code, 0)
        mock_output_path.write_text.assert_called_once()

    @patch('git_recap.cli.fetch_from_repos')
    def test_main_no_commits_found(self, mock_fetch):
        """Test main function when no commits found."""
        mock_fetch.return_value = []

        with patch('sys.argv', ['git-recap', '.']):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                exit_code = main()
        
        self.assertEqual(exit_code, 0)
        self.assertIn("No commits found", mock_stderr.getvalue())

    @patch('git_recap.cli.fetch_from_repos')
    @patch('git_recap.cli.parse_entries_to_txt')
    @patch('git_recap.cli.Path')
    def test_main_creates_parent_directories(self, mock_path, mock_parse, mock_fetch):
        """Test main function creates parent directories."""
        mock_fetch.return_value = [
            {
                "author": "John Doe",
                "message": "Commit 1",
                "timestamp": datetime(2025, 1, 15),
                "repo": "test-repo",
                "type": "commit"
            }
        ]
        mock_parse.return_value = "2025-01-15:\n - [Commit] in test-repo: Commit 1"
        
        mock_output_path = MagicMock()
        mock_path.return_value = mock_output_path

        with patch('sys.argv', ['git-recap', '.', '--output', 'subdir/summary.txt']):
            exit_code = main()
        
        self.assertEqual(exit_code, 0)
        mock_output_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
        mock_output_path.write_text.assert_called_once()

    @patch('git_recap.cli.fetch_from_repos')
    @patch('git_recap.cli.parse_entries_to_txt')
    @patch('git_recap.cli.Path')
    def test_main_file_write_error(self, mock_path, mock_parse, mock_fetch):
        """Test main function handles file write errors."""
        mock_fetch.return_value = [
            {
                "author": "John Doe",
                "message": "Commit 1",
                "timestamp": datetime(2025, 1, 15),
                "repo": "test-repo",
                "type": "commit"
            }
        ]
        mock_parse.return_value = "2025-01-15:\n - [Commit] in test-repo: Commit 1"
        mock_output_path = MagicMock()
        mock_output_path.write_text.side_effect = IOError("Permission denied")
        mock_path.return_value = mock_output_path

        with patch('sys.argv', ['git-recap', '.', '--output', 'summary.txt']):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                exit_code = main()
        
        self.assertEqual(exit_code, 1)
        self.assertIn("Error writing to file", mock_stderr.getvalue())


if __name__ == '__main__':
    unittest.main()