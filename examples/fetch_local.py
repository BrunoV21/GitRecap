"""
Example: Using LocalFetcher with a local git repository

This example demonstrates how to use the LocalFetcher to fetch commits
and other information from a local git repository on your machine.
"""

from datetime import datetime, timedelta
import os
from git_recap.providers.local_fetcher import LocalFetcher
from git_recap.utils import parse_entries_to_txt


def example_basic_usage():
    """Basic usage of LocalFetcher."""
    # Initialize the fetcher with a path to your local git repository
    repo_path = os.getcwd()
    print(f"{repo_path=}")
    
    fetcher = LocalFetcher(
        repo_path=repo_path,
        # start_date=datetime.now() - timedelta(days=360),
        # end_date=datetime.now()
    )
    
    # Get repository name
    print(f"Repository: {fetcher.repos_names}")
    
    # Fetch commits
    commits = fetcher.fetch_commits()
    print(f"\nFound {len(commits)} commits:")
    for commit in commits[:5]:  # Show first 5 commits
        print(f"  - {commit['timestamp']}: {commit['message'][:50]}...")

    print(parse_entries_to_txt(commits))
    
    # # Get all authored messages (commits)
    # messages = fetcher.get_authored_messages()
    # print(f"\nTotal authored messages: {len(messages)}")


def example_with_authors():
    """Filter commits by specific authors."""
    repo_path = "./"
    
    fetcher = LocalFetcher(
        repo_path=repo_path,
        authors=["John Doe", "Jane Smith"],  # Filter by author names
        start_date=datetime.now() - timedelta(days=7),
        end_date=datetime.now()
    )
    
    commits = fetcher.fetch_commits()
    print(f"Found {len(commits)} commits by specified authors")


def example_get_authors():
    """Get list of all authors in the repository."""
    repo_path = "./"
    
    fetcher = LocalFetcher(repo_path=repo_path)
    
    authors = fetcher.get_authors([])
    print(f"\nFound {len(authors)} unique authors:")
    for author in authors[:10]:  # Show first 10 authors
        print(f"  - {author['name']} ({author['email']})")


def example_get_branches():
    """Get list of all branches in the repository."""
    repo_path = "./"
    
    fetcher = LocalFetcher(repo_path=repo_path)
    
    branches = fetcher.get_branches()
    print(f"\nFound {len(branches)} branches:")
    for branch in branches[:10]:  # Show first 10 branches
        print(f"  - {branch}")


def example_get_current_author():
    """Get current git user configuration."""
    repo_path = "./"
    
    fetcher = LocalFetcher(repo_path=repo_path)
    
    author = fetcher.get_current_author()
    if author:
        print(f"\nCurrent git user: {author['name']} ({author['email']})")
    else:
        print("\nNo git user configured for this repository")


def example_date_range():
    """Fetch commits within a specific date range."""
    repo_path = "./"
    
    # Fetch commits from January 2025
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 1, 31)
    
    fetcher = LocalFetcher(
        repo_path=repo_path,
        start_date=start_date,
        end_date=end_date
    )
    
    commits = fetcher.fetch_commits()
    print(f"\nFound {len(commits)} commits in January 2025")


if __name__ == "__main__":
    # Note: Replace "./" with an actual path
    # to a git repository on your machine
    
    print("LocalFetcher Examples")
    print("=" * 50)
    
    # Uncomment the examples you want to run:
    
    example_basic_usage()
    # example_with_authors()
    # example_get_authors()
    # example_get_branches()
    # example_get_current_author()
    # example_date_range()
    
    print("\nTo run these examples, uncomment the function calls above")
    print("and replace the repository path with your actual path.")