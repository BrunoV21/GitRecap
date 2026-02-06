# LocalFetcher Implementation Summary

**Date:** 2025-02-06

## Overview

The `LocalFetcher` class has been successfully implemented to enable GitRecap to work with local git repositories directly on your machine, without requiring remote platforms like GitHub, GitLab, Azure DevOps, or URL-based cloning.

## Implementation Details

### Files Created

1. **`git_recap/providers/local_fetcher.py`** (391 lines)
   - New `LocalFetcher` class extending `BaseFetcher`
   - Implements all required abstract methods from `BaseFetcher`
   - Uses subprocess to execute git commands directly on local repository paths
   - Supports date filtering, author filtering, and branch operations

### Files Modified

1. **`git_recap/providers/__init__.py`**
   - Added import: `from git_recap.providers.local_fetcher import LocalFetcher`
   - Added `"LocalFetcher"` to `__all__` exports list

2. **`app/api/services/fetcher_service.py`**
   - Added import: `LocalFetcher` to provider imports
   - Updated `store_fetcher()` function to handle `"Local"` provider type
   - New logic: `elif provider == "Local": fetchers[session_id] = LocalFetcher(repo_path=pat)`

3. **`app/api/models/schemas.py`**
   - Added new `LocalRepoRequest` model with `path: str` field for local repository path

4. **`app/api/server/routes.py`**
   - Added `LocalRepoRequest` to schema imports
   - Added new endpoint: `@router.post("/local-repo")` with `local_repository()` handler
   - Endpoint creates LLM session and stores LocalFetcher instance

5. **`git_recap/fetcher.py`**
   - Added import: `from git_recap.providers.local_fetcher import LocalFetcher`
   - Updated CLI to support `--provider local` option
   - Added `--repo-path` argument for specifying local repository path
   - PAT is not required for local provider

6. **`examples/fetch_local.py`** (124 lines)
   - Created comprehensive example file demonstrating LocalFetcher usage
   - Includes examples for basic usage, author filtering, date ranges, and more

7. **`tests/test_local_fetcher.py`** (498 lines)
   - Created comprehensive test suite with 25 test cases
   - Tests cover initialization, commit fetching, author retrieval, branch operations, and edge cases
   - All tests passing

## Features

### Core Functionality

- **Repository Validation**: Validates that the provided path is a valid git repository
- **Commit Fetching**: Fetches commits with support for:
  - Date range filtering (`start_date`, `end_date`)
  - Author filtering (`authors` parameter)
  - Repository filtering (`repo_filter` parameter)
- **Author Retrieval**: Retrieves unique authors from commit history
- **Branch Operations**: Lists both local and remote branches
- **Current Author**: Retrieves the current git user configuration

### API Integration

- **New Endpoint**: `POST /local-repo`
  - Accepts `LocalRepoRequest` with repository path
  - Creates LLM session and stores LocalFetcher instance
  - Integrates with existing endpoints (authors, commits, etc.)

### CLI Support

- **New Provider**: `--provider local`
- **New Argument**: `--repo-path` (required for local provider)
- **Optional PAT**: PAT is not required for local provider

## Usage Examples

### Python API

```python
from datetime import datetime, timedelta
from git_recap.providers.local_fetcher import LocalFetcher

# Initialize the fetcher with a path to your local git repository
fetcher = LocalFetcher(
    repo_path="/path/to/your/local/repository",
    start_date=datetime.now() - timedelta(days=30),
    end_date=datetime.now()
)

# Fetch commits
commits = fetcher.fetch_commits()
print(f"Found {len(commits)} commits")

# Get repository name
print(f"Repository: {fetcher.repos_names}")

# Get all authors
authors = fetcher.get_authors([])
print(f"Found {len(authors)} unique authors")

# Get authored messages
messages = fetcher.get_authored_messages()
```

### CLI

```bash
# Fetch commits from local repository
python -m git_recap.fetcher \
    --provider local \
    --repo-path /path/to/your/local/repository \
    --start-date 2025-01-01 \
    --end-date 2025-01-31 \
    --limit 10
```

### API Endpoint

```bash
# Connect to a local repository via API
curl -X POST http://localhost:8000/local-repo \
    -H "Content-Type: application/json" \
    -d '{"path": "/path/to/your/local/repository"}'
```

## Technical Details

### Git Command Execution

The `LocalFetcher` uses `subprocess.run()` to execute git commands directly on the local repository:

- **Commit Fetching**: Uses `git log` with custom format (`--pretty=format:%H|%an|%ad|%s`)
- **Author Retrieval**: Uses `git log` with author and committer formats
- **Branch Listing**: Uses `git branch` for local and remote branches
- **Current Author**: Uses `git config user.name` and `git config user.email`

### Date Filtering

- Supports timezone-aware datetime objects
- Converts to ISO format for git commands
- Filters commits within specified date range

### Author Filtering

- Supports multiple author names
- Uses git's `--author` flag for filtering
- Can be combined with date filtering

### Error Handling

- Handles subprocess timeouts gracefully
- Returns empty list on git command failures
- Validates repository path on initialization (can be disabled for testing)

## Testing

### Test Coverage

- **25 test cases** covering all major functionality
- **Test categories**:
  - Initialization tests
  - Commit fetching tests
  - Pull request tests (returns empty list)
  - Author retrieval tests
  - Branch operation tests
  - Edge case handling
  - Integration tests

### Running Tests

```bash
# Run all LocalFetcher tests
python -m pytest tests/test_local_fetcher.py -v

# Run specific test class
python -m pytest tests/test_local_fetcher.py::TestLocalFetcherFetchCommits -v
```

## Limitations

### Platform-Specific Features

The following features are not supported for local repositories:

- **Pull Requests**: Returns empty list (PRs are platform-specific)
- **Issues**: Returns empty list (issues are platform-specific)
- **Releases**: Raises `NotImplementedError`
- **PR Target Branch Validation**: Raises `NotImplementedError`
- **PR Creation**: Raises `NotImplementedError`

### Single Repository

Unlike other fetchers that can work with multiple repositories, `LocalFetcher` works with a single local repository path.

## Integration Points

### Existing Endpoints

The `LocalFetcher` integrates with existing endpoints through the common `BaseFetcher` interface:

- `/authors` - Get authors from local repository
- `/commits` - Get commits from local repository
- `/messages` - Get all authored messages (commits, PRs, issues)

### Session Management

Uses existing session_id pattern for storing fetcher instances in the fetcher service.

## Future Enhancements

Potential improvements for the `LocalFetcher`:

1. **Worktree Support**: Add support for git worktrees
2. **Submodule Support**: Add support for git submodules
3. **Tag Support**: Add support for fetching tags
4. **Diff Support**: Add support for fetching commit diffs
5. **Branch Comparison**: Add support for comparing branches
6. **Merge Detection**: Detect merge commits and handle them differently

## CLI Usage

The GitRecap CLI provides an LLM-friendly command-line interface for fetching and summarizing git commits from local repositories. It's designed to be easily used by LLMs and automated tools.

### Installation

After installing the package, the CLI is available as `git-recap`:

```bash
pip install git-recap
```

### Basic Usage

```bash
# Get commits from current directory (last 7 days)
git-recap .

# Get commits from multiple repositories
git-recap /path/to/repo1 /path/to/repo2
```

### Command-Line Arguments

#### Positional Arguments

- **`paths`** (required, one or more)
  - One or more paths to local git repositories
  - Each path must be a valid git repository (contains .git directory)
  - Can be absolute or relative paths
  - Multiple paths can be provided

#### Optional Arguments

- **`--author AUTHOR`**
  - Filter commits by author name
  - Partial matching is supported (e.g., "John" matches "John Doe")
  - If not specified, commits from all authors are included

- **`--start-date START_DATE`**
  - Start date for filtering commits (inclusive)
  - Format: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`
  - If not specified, defaults to 7 days before current date

- **`--end-date END_DATE`**
  - End date for filtering commits (inclusive)
  - Format: `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS`
  - If not specified, defaults to current date and time

- **`--output OUTPUT, -o OUTPUT`**
  - Output file path to save the summary
  - If not specified, results are printed to stdout
  - The file will be created or overwritten if it exists

- **`--help, -h`**
  - Show help message and exit

### Usage Examples

#### Filter by Author

```bash
# Get commits by a specific author
git-recap . --author "John Doe"

# Partial matching works too
git-recap /path/to/repo --author "Jane"
```

#### Filter by Date Range

```bash
# Get commits from a specific date range
git-recap . --start-date "2025-01-01" --end-date "2025-01-31"

# Get commits from a specific date onwards
git-recap . --start-date "2025-01-01"

# Get commits up to a specific date
git-recap . --end-date "2025-01-31"
```

#### Save to File

```bash
# Save summary to a file
git-recap . --output summary.txt

# Combine filters and save to file
git-recap /path/to/repo1 /path/to/repo2 --author "Jane" --start-date "2025-01-01" --output commits.txt
```

#### Multiple Repositories

```bash
# Fetch from multiple repositories
git-recap /path/to/repo1 /path/to/repo2 /path/to/repo3

# Combine with filters
git-recap /path/to/repo1 /path/to/repo2 --author "John" --start-date "2025-01-01" --end-date "2025-01-31"
```

### Output Format

The CLI outputs commits grouped by date in the following format:

```
2025-01-15:
 - [Commit] in my-repo: Added new feature for user authentication
 - [Commit] in my-repo: Fixed bug in login flow

2025-01-14:
 - [Commit] in my-repo: Updated documentation
 - [Commit] in my-repo: Refactored database queries
```

Each entry includes:
- **Date**: The date of the commits (YYYY-MM-DD)
- **Type**: The entry type (e.g., "Commit")
- **Repository**: The repository name
- **Message**: The commit message

### LLM-Friendly Features

The CLI is designed to be easily used by LLMs and automated tools:

1. **Clear Help Text**: The `--help` output provides comprehensive information about all arguments and usage examples
2. **Structured Output**: The output format is consistent and easy to parse
3. **Error Messages**: Clear error messages are printed to stderr for debugging
4. **Exit Codes**: Returns 0 for success, 1 for errors
5. **Flexible Input**: Supports multiple repository paths and various filtering options

### Error Handling

The CLI provides helpful error messages for common issues:

- **Invalid repository path**: "Error: Path does not exist: /path/to/repo"
- **Not a git repository**: "Error: Not a git repository: /path/to/repo"
- **Invalid date format**: "Invalid date format: 'invalid-date'. Use ISO format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS"
- **No commits found**: "No commits found matching the specified criteria."

### Running the CLI

After installation, you can run the CLI in two ways:

```bash
# Using the installed command
git-recap . --author "John Doe"

# Or using Python module
python -m git_recap.cli . --author "John Doe"
```

### Integration with LLMs

The CLI is particularly useful for LLM integration:

1. **Predictable Output**: The structured output format is easy for LLMs to parse and understand
2. **Flexible Filtering**: Multiple filtering options allow LLMs to request specific data
3. **File Output**: The `--output` flag allows LLMs to save results to files for further processing
4. **Help Documentation**: The comprehensive help text enables LLMs to understand available options

Example LLM prompt:
```
Please fetch all commits from the current directory made by "John Doe" in January 2025 and save the results to a file called "january_commits.txt".
```

The LLM can translate this to:
```bash
git-recap . --author "John Doe" --start-date "2025-01-01" --end-date "2025-01-31" --output january_commits.txt
```

## Conclusion

The `LocalFetcher` implementation successfully extends GitRecap to work with local git repositories, providing a comprehensive set of features for fetching commits, authors, and branch information. The implementation follows the existing patterns in the codebase and integrates seamlessly with the API, CLI, and service layer.

The new CLI tool provides an LLM-friendly interface that makes it easy for automated tools and AI assistants to interact with git repositories and extract structured commit information.

---
Co-authored by [Nova](https://www.compassap.ai/portfolio/nova.html)