#!/usr/bin/env python3
"""
GitRecap CLI - LLM-Friendly Command Line Interface

This CLI tool fetches and summarizes git commit history from local repositories.
It's designed to be easily used by LLMs and automated tools with clear, structured output.

Usage Examples:
    # Get commits from current directory (last 7 days)
    git-recap .

    # Get commits from multiple repositories
    git-recap /path/to/repo1 /path/to/repo2

    # Filter by author
    git-recap . --author "John Doe"

    # Filter by date range
    git-recap . --start-date "2025-01-01" --end-date "2025-01-31"

    # Save output to file
    git-recap . --output summary.txt

    # Combine filters
    git-recap /path/to/repo1 /path/to/repo2 --author "Jane Smith" --start-date "2025-01-01" --output commits.txt
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from git_recap.providers.local_fetcher import LocalFetcher
from git_recap.utils import parse_entries_to_txt


def parse_date(date_string: str) -> datetime:
    """
    Parse date string in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS).
    
    Args:
        date_string: Date string to parse
        
    Returns:
        datetime: Parsed datetime object
        
    Raises:
        argparse.ArgumentTypeError: If date format is invalid
    """
    try:
        # Try parsing with time first
        return datetime.fromisoformat(date_string)
    except ValueError:
        # Try parsing as date only (YYYY-MM-DD)
        try:
            return datetime.strptime(date_string, "%Y-%m-%d")
        except ValueError:
            raise argparse.ArgumentTypeError(
                f"Invalid date format: '{date_string}'. "
                f"Use ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"
            )


def create_parser() -> argparse.ArgumentParser:
    """
    Create and configure the argument parser for the CLI.
    
    Returns:
        argparse.ArgumentParser: Configured parser with all arguments
    """
    parser = argparse.ArgumentParser(
        prog='git-recap',
        description=(
            'GitRecap CLI - Fetch and summarize git commits from local repositories.\n\n'
            'This tool aggregates commit history from multiple local git repositories, '
            'filters by author and date range, and outputs structured text summaries. '
            'Designed for easy integration with LLMs and automated workflows.'
        ),
        epilog=(
            'Examples:\n'
            '  git-recap .                                    # Current directory, last 7 days\n'
            '  git-recap /path/to/repo1 /path/to/repo2        # Multiple repositories\n'
            '  git-recap . --author "John Doe"               # Filter by author\n'
            '  git-recap . --start-date "2025-01-01"         # From specific date\n'
            '  git-recap . --output summary.txt               # Save to file\n'
            '  git-recap . --author "Jane" --start-date "2025-01-01" --end-date "2025-01-31" --output commits.txt'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'paths',
        nargs='+',
        help=(
            'One or more paths to local git repositories. '
            'Each path must be a valid git repository (contains .git directory). '
            'Can be absolute or relative paths. Multiple paths can be provided.'
        )
    )
    
    parser.add_argument(
        '--author',
        type=str,
        help=(
            'Filter commits by author name. '
            'Partial matching is supported (e.g., "John" matches "John Doe"). '
            'If not specified, commits from all authors are included.'
        )
    )
    
    parser.add_argument(
        '--start-date',
        type=parse_date,
        help=(
            'Start date for filtering commits (inclusive). '
            'Format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS. '
            'If not specified, defaults to 7 days before current date.'
        )
    )
    
    parser.add_argument(
        '--end-date',
        type=parse_date,
        help=(
            'End date for filtering commits (inclusive). '
            'Format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS. '
            'If not specified, defaults to current date and time.'
        )
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help=(
            'Output file path to save the summary. '
            'If not specified, results are printed to stdout. '
            'The file will be created or overwritten if it exists.'
        )
    )
    
    return parser


def filter_entries_by_author(
    entries: List[Dict[str, Any]], 
    author: str
) -> List[Dict[str, Any]]:
    """
    Filter entries by author name (case-insensitive partial match).
    
    Args:
        entries: List of commit entries
        author: Author name to filter by
        
    Returns:
        List[Dict[str, Any]]: Filtered entries matching the author
    """
    author_lower = author.lower()
    return [
        entry for entry in entries 
        if author_lower in entry.get('author', '').lower()
    ]


def fetch_from_repos(
    repo_paths: List[str],
    authors: Optional[List[str]] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Fetch commits from multiple local repositories.
    
    Args:
        repo_paths: List of repository paths
        authors: Optional list of author names to filter by
        start_date: Optional start date for filtering
        end_date: Optional end date for filtering
        
    Returns:
        List[Dict[str, Any]]: Aggregated list of commit entries from all repos
    """
    all_entries = []
    
    for repo_path in repo_paths:
        try:
            print(f"Fetching from: {repo_path}", file=sys.stderr)
            fetcher = LocalFetcher(
                repo_path=repo_path,
                authors=authors,
                start_date=start_date,
                end_date=end_date,
                validate_repo=True
            )
            entries = fetcher.fetch_commits()
            all_entries.extend(entries)
            print(f"  Found {len(entries)} commits", file=sys.stderr)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"Unexpected error processing {repo_path}: {e}", file=sys.stderr)
            continue
    
    return all_entries


def main() -> int:
    """
    Main entry point for the CLI.
    
    Returns:
        int: Exit code (0 for success, 1 for error)
    """
    parser = create_parser()
    args = parser.parse_args()
    
    # Set default date range if not provided
    if not args.start_date and not args.end_date:
        # Default: last 7 days
        from datetime import timedelta
        args.end_date = datetime.now()
        args.start_date = args.end_date - timedelta(days=7)
    elif not args.start_date:
        # Only end date provided, start from 7 days before end
        from datetime import timedelta
        args.start_date = args.end_date - timedelta(days=7)
    elif not args.end_date:
        # Only start date provided, use current time as end
        args.end_date = datetime.now()
    
    # Prepare authors list
    authors = [args.author] if args.author else None
    
    # Fetch commits from all repositories
    entries = fetch_from_repos(
        repo_paths=args.paths,
        authors=authors,
        start_date=args.start_date,
        end_date=args.end_date
    )
    
    # Check if we found any entries
    if not entries:
        print("No commits found matching the specified criteria.", file=sys.stderr)
        return 0
    
    # Convert entries to text format
    output_text = parse_entries_to_txt(entries)
    
    # Output to file or stdout
    if args.output:
        try:
            output_path = Path(args.output)
            # Create parent directories if they don't exist
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output_text, encoding='utf-8')
            print(f"Summary saved to: {args.output}", file=sys.stderr)
        except Exception as e:
            print(f"Error writing to file {args.output}: {e}", file=sys.stderr)
            return 1
    else:
        print(output_text)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())