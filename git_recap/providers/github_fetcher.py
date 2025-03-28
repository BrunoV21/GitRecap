from github import Github
from datetime import datetime
from typing import List, Dict, Any
from git_recap.providers.base_fetcher import BaseFetcher

class GitHubFetcher(BaseFetcher):
    def __init__(self, pat: str, start_date=None, end_date=None, repo_filter=None, authors=None):
        super().__init__(pat, start_date, end_date, repo_filter, authors)
        self.github = Github(self.pat)
        self.user = self.github.get_user()
        self.authors.append(self.user.login)

    def _stop_fetching(self, date_obj: datetime) -> bool:
        if self.start_date and date_obj < self.start_date:
            return True
        return False

    def _filter_by_date(self, date_obj: datetime) -> bool:
        if self.start_date and date_obj < self.start_date:
            return False
        if self.end_date and date_obj > self.end_date:
            return False
        return True

    def fetch_commits(self) -> List[Dict[str, Any]]:
        entries = []
        processed_commits = set()
        repos = self.user.get_repos()
        for repo in repos:
            if self.repo_filter and repo.name not in self.repo_filter:
                continue
            for author in self.authors:
                commits = repo.get_commits(author=author)
                for i, commit in enumerate(commits, start=1):
                    commit_date = commit.commit.author.date
                    if self._filter_by_date(commit_date):
                        sha = commit.sha
                        if sha not in processed_commits:
                            entry = {
                                "type": "commit",
                                "repo": repo.name,
                                "message": commit.commit.message.strip(),
                                "timestamp": commit_date,
                                "sha": sha,
                            }
                            entries.append(entry)
                            processed_commits.add(sha)
                    if self._stop_fetching(commit_date):
                        break
        return entries

    def fetch_pull_requests(self) -> List[Dict[str, Any]]:
        entries = []
        # Maintain a local set to skip duplicate commits already captured in a PR.
        processed_pr_commits = set()
        repos = self.user.get_repos()
        for repo in repos:
            if self.repo_filter and repo.name not in self.repo_filter:
                continue
            pulls = repo.get_pulls(state='all')
            for i, pr in enumerate(pulls, start=1):
                if pr.user.login not in  self.authors:
                    continue
                pr_date = pr.updated_at  # alternatively, use pr.created_at
                if not self._filter_by_date(pr_date):
                    continue

                # Add the pull request itself.
                pr_entry = {
                    "type": "pull_request",
                    "repo": repo.name,
                    "message": pr.title,
                    "timestamp": pr_date,
                    "pr_number": pr.number,
                }
                entries.append(pr_entry)

                # Now, add commits associated with this pull request.
                pr_commits = pr.get_commits()
                for pr_commit in pr_commits:
                    commit_date = pr_commit.commit.author.date
                    if self._filter_by_date(commit_date):
                        sha = pr_commit.sha
                        if sha in processed_pr_commits:
                            continue
                        pr_commit_entry = {
                            "type": "commit_from_pr",
                            "repo": repo.name,
                            "message": pr_commit.commit.message.strip(),
                            "timestamp": commit_date,
                            "sha": sha,
                            "pr_title": pr.title,
                        }
                        entries.append(pr_commit_entry)
                        processed_pr_commits.add(sha)
                if self._stop_fetching(pr_date):
                    break
        return entries

    def fetch_issues(self) -> List[Dict[str, Any]]:
        entries = []
        issues = self.user.get_issues()
        for i, issue in enumerate(issues, start=1):
            issue_date = issue.created_at
            if self._filter_by_date(issue_date):
                entry = {
                    "type": "issue",
                    "repo": issue.repository.name,
                    "message": issue.title,
                    "timestamp": issue_date,
                }
                entries.append(entry)
            if self._stop_fetching(issue_date):
                break
        return entries

    def get_authored_messages(self) -> List[Dict[str, Any]]:
        """
        Aggregates all commit, pull request, and issue entries into a single list,
        ensuring no duplicate commits (based on SHA) are present, and then sorts
        them in chronological order based on their timestamp.
        """
        commit_entries = self.fetch_commits()
        pr_entries = self.fetch_pull_requests()
        issue_entries = self.fetch_issues()

        all_entries = pr_entries + commit_entries + issue_entries

        # For commit-related entries, remove duplicates (if any) based on SHA.
        unique_entries = {}
        for entry in all_entries:
            if entry.get("type") in ["commit", "commit_from_pr"]:
                sha = entry.get("sha")
                if sha in unique_entries:
                    continue
                unique_entries[sha] = entry
            else:
                # For pull requests and issues, we can create a unique key.
                key = f"{entry['type']}_{entry['repo']}_{entry['timestamp']}"
                unique_entries[key] = entry

        final_entries = list(unique_entries.values())
        # Sort all entries by their timestamp.
        final_entries.sort(key=lambda x: x["timestamp"])
        return self.convert_timestamps_to_str(final_entries)