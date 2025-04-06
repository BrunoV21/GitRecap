# Git Recap

Git Recap is a modular Python tool that aggregates and formats user-authored messages from repositories hosted on GitHub, Azure DevOps, and GitLab. It fetches commit messages, pull requests (along with their associated commits), and issues, then consolidates and sorts these events into a clear, chronological summary. This summary is output as a plain text string that can serve as context for large language models or other analysis tools.

## Features

- **Multi-Platform Support:**  
  Retrieve messages from:
  - GitHub (via [PyGitHub](https://pygithub.readthedocs.io/en/stable/))
  - Azure DevOps (via [azure-devops Python API](https://github.com/microsoft/azure-devops-python-api))
  - GitLab (via [python-gitlab](https://python-gitlab.readthedocs.io/))
  
- **Flexible Date Filtering:**  
  Specify start and end dates (automatically converted to UTC if no timezone info is provided) to restrict the range of events.

- **Author Filtering:**  
  Optionally specify one or more authors. By default, the authenticated user is used.

- **Output Schema:**  
  Each fetched event is stored in a standardized dictionary format with keys such as:
  - `type` (commit, commit_from_pr, pull_request, issue)
  - `repo`
  - `message`
  - `timestamp`
  - Additional keys like `sha`, `pr_title`, and `pr_number` for context

- **Chronological Aggregation:**  
  All events are merged and sorted in chronological order.  
  A helper function then parses the JSON output into a plain text summary grouped by day, making it ideal as context for LLMs.

## File Structure

```
git_recap/
├── README.md
├── requirements.txt
└── src
    ├── __init__.py
    ├── fetcher.py
    └── providers
         ├── __init__.py
         ├── base_fetcher.py
         ├── github_fetcher.py
         ├── azure_fetcher.py
         └── gitlab_fetcher.py
```

- **fetcher.py:**  
  Contains the main entry point which parses command-line arguments (provider, PAT, dates, repo filters, etc.) and invokes the appropriate provider fetcher.

- **providers/base_fetcher.py:**  
  Defines the abstract base class with common functionality such as date filtering and aggregating messages.

- **providers/github_fetcher.py:**  
  Implements GitHub-specific logic for fetching commits, pull requests (including their commits), and issues.

- **providers/azure_fetcher.py & providers/gitlab_fetcher.py:**  
  Implement similar logic for Azure DevOps and GitLab respectively.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/git_recap.git
   cd git_recap
   ```

2. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the main script with the required parameters. For example:

### GitHub
```bash
python src/fetcher.py --provider github --pat YOUR_GITHUB_PAT --start-date 2025-03-07T00:00:00 --end-date 2025-03-15T23:59:59 --repos Repo1 Repo2
```

### Azure DevOps
```bash
python src/fetcher.py --provider azure --pat YOUR_AZURE_PAT --organization-url https://dev.azure.com/YOURORG --start-date 2025-03-07T00:00:00 --end-date 2025-03-15T23:59:59 --repos Repo1 Repo2
```

### GitLab
```bash
python src/fetcher.py --provider gitlab --pat YOUR_GITLAB_PAT --gitlab-url https://gitlab.example.com --start-date 2025-03-07T00:00:00 --end-date 2025-03-15T23:59:59 --repos Repo1 Repo2
```

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the terms of the [MIT License](LICENSE).

## Acknowledgements

- [PyGitHub](https://pygithub.readthedocs.io/en/stable/)
- [Azure DevOps Python API](https://github.com/microsoft/azure-devops-python-api)
- [python-gitlab](https://python-gitlab.readthedocs.io/)