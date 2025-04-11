
# Git Recap Python Package

The `git_recap` Python package provides core functionality for fetching and processing Git activity data from multiple providers.

## Package Structure

```
git_recap/
├── __init__.py
├── fetcher.py
├── utils.py
└── providers/
    ├── __init__.py
    ├── base_fetcher.py
    ├── github_fetcher.py
    ├── gitlab_fetcher.py
    └── azure_fetcher.py
```

## Core Modules

### `fetcher.py`
Main entry point that:
- Parses command line arguments
- Initializes provider-specific fetchers
- Aggregates results from multiple providers
- Handles error cases and validation

### `providers/` 
Provider-specific implementations following the base fetcher interface:

#### `base_fetcher.py`
Abstract base class defining the common interface:
```python
class BaseFetcher(ABC):
    @abstractmethod
    def get_authored_messages(self) -> List[Dict]:
        """Fetch all authored messages within date range"""
        
    @abstractmethod
    def validate_credentials(self) -> bool:
        """Verify authentication credentials"""
```

#### Provider Implementations:
- `github_fetcher.py`: GitHub integration via PyGitHub
- `gitlab_fetcher.py`: GitLab integration via python-gitlab
- `azure_fetcher.py`: Azure DevOps integration via azure-devops

### `utils.py`
Helper functions including:
- `parse_entries_to_txt()`: Formats raw entries into readable text
- `validate_dates()`: Ensures proper date range formatting
- `filter_by_author()`: Filters messages by specified authors

## Installation

Install from PyPI:
```bash
pip install git-recap
```

Or install from source:
```bash
git clone https://github.com/yourusername/git_recap.git
cd git_recap
pip install .
```

## Basic Usage

### Programmatic Usage
```python
from datetime import datetime, timedelta
from git_recap.providers import GitHubFetcher
from git_recap.utils import parse_entries_to_txt

# Initialize fetcher
fetcher = GitHubFetcher(
    pat="your_github_pat",
    start_date=datetime.now() - timedelta(days=7),
    end_date=datetime.now(),
    repos=["repo1", "repo2"],
    authors=["user1"]
)

# Fetch and format messages
messages = fetcher.get_authored_messages()
summary = parse_entries_to_txt(messages)
print(summary)
```

### Command Line Interface
```bash
git-recap --provider github \
          --pat YOUR_PAT \
          --start-date 2023-01-01 \
          --end-date 2023-01-31 \
          --repos repo1 repo2 \
          --authors user1
```

## Extending the Package

To add support for a new Git provider:

1. Create a new fetcher class inheriting from `BaseFetcher`
2. Implement all required abstract methods
3. Add provider-specific logic for:
   - Authentication
   - Repository listing
   - Message fetching
   - Error handling

Example skeleton:
```python
from git_recap.providers.base_fetcher import BaseFetcher

class NewProviderFetcher(BaseFetcher):
    def __init__(self, pat: str, **kwargs):
        super().__init__(pat, **kwargs)
        # Initialize provider client
        
    def get_authored_messages(self) -> List[Dict]:
        # Implementation here
        pass
        
    def validate_credentials(self) -> bool:
        # Implementation here
        pass
```

## Testing
Run tests with:
```bash
python -m pytest tests/
```

Key test files:
- `tests/test_parser.py`: Tests for message parsing
- `tests/test_dummy_parser.py`: Mock provider tests

## Dependencies
- PyGithub (for GitHub integration)
- python-gitlab (for GitLab integration)
- azure-devops (for Azure DevOps integration)