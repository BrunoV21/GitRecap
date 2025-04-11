
# Git Recap Python Package

The `git_recap` Python package provides core functionality for fetching and processing Git activity data from multiple providers (GitHub, GitLab, Azure DevOps).

## Package Structure

```
git_recap/
├── __init__.py            # Package initialization
├── fetcher.py             # Main entry point
├── providers/             # Provider implementations
│   ├── __init__.py
│   ├── base_fetcher.py    # Abstract base class
│   ├── github_fetcher.py  # GitHub provider
│   ├── gitlab_fetcher.py  # GitLab provider
│   └── azure_fetcher.py   # Azure DevOps provider
└── utils.py               # Utility functions
```

## Core Components

### `BaseFetcher` (base_fetcher.py)
Abstract base class defining the provider interface:

```python
class BaseFetcher(ABC):
    @abstractmethod
    def fetch_commits(self, since: datetime, until: datetime) -> List[Commit]:
        """Fetch commits between date range"""
    
    @abstractmethod
    def fetch_pull_requests(self, since: datetime, until: datetime) -> List[PullRequest]:
        """Fetch PRs between date range"""
    
    @abstractmethod
    def fetch_issues(self, since: datetime, until: datetime) -> List[Issue]:
        """Fetch issues between date range"""
    
    def get_authored_messages(self, since: datetime, until: datetime) -> Dict[str, List]:
        """Aggregate all activity types"""
```

### Provider Implementations

#### GitHubFetcher
- Uses PyGithub library
- Supports both OAuth and PAT authentication
- Implements all abstract methods from BaseFetcher

#### GitLabFetcher  
- Uses python-gitlab library
- Supports personal access tokens
- Includes GitLab-specific API handling

#### AzureFetcher
- Uses azure-devops library
- Handles Azure DevOps API quirks
- Supports organization/project filtering

## Utility Functions

### `parse_entries_to_txt()`
Converts raw activity data into formatted text output:

```python
def parse_entries_to_txt(entries: Dict[str, List]) -> str:
    """Formats activity data into human-readable text
    
    Args:
        entries: Dictionary of activity types to lists of items
        
    Returns:
        Formatted text output grouped by day and activity type
    """
```

## Installation

Install from PyPI:

```bash
pip install git-recap
```

Or install from source:

```bash
git clone https://github.com/your-repo/git-recap.git
cd git-recap
pip install -e .
```

## Usage Examples

Basic usage with GitHub:

```python
from git_recap.providers.github_fetcher import GitHubFetcher
from datetime import datetime, timedelta

fetcher = GitHubFetcher(token="your_github_token")
since = datetime.now() - timedelta(days=7)
until = datetime.now()

activity = fetcher.get_authored_messages(since, until)
print(activity)
```

See [examples/fetch_github.py](examples/fetch_github.py) for more complete examples.

## Dependencies

Core package dependencies:
- `pygithub>=1.55` (GitHub support)
- `python-gitlab>=3.0.0` (GitLab support)  
- `azure-devops>=6.0.0` (Azure DevOps support)
- `python-dateutil` (Date handling)