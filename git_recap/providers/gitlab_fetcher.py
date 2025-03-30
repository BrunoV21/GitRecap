import gitlab
from datetime import datetime
from typing import List, Dict, Any
from git_recap.providers.base_fetcher import BaseFetcher

class GitLabFetcher(BaseFetcher):
    def __init__(self, pat: str, url: str = 'https://gitlab.com', start_date=None, end_date=None, repo_filter=None, authors=None):
        super().__init__(pat, start_date, end_date, repo_filter, authors)
        self.gl = gitlab.Gitlab(url, private_token=self.pat)
        self.gl.auth()
        # Instead of only owned projects, retrieve projects where you're a member.
        self.projects = self.gl.projects.list(membership=True, all=True)
        # Default to the authenticated user's username if no authors are provided.
        if authors is None:
            self.authors = [self.gl.user.username]
        else:
            self.authors = authors

    @property
    def repos_names(self)->List[str]:
        "to be implemented later"
        return [project.name for project in self.projects]

    def _filter_by_date(self, date_str: str) -> bool:
        date_obj = datetime.fromisoformat(date_str)
        if self.start_date and date_obj < self.start_date:
            return False
        if self.end_date and date_obj > self.end_date:
            return False
        return True

    def _stop_fetching(self, date_str: str) -> bool:
        date_obj = datetime.fromisoformat(date_str)
        if self.start_date and date_obj < self.start_date:
            return True
        return False

    def fetch_commits(self) -> List[Dict[str, Any]]:
        entries = []
        processed_commits = set()
        for project in self.projects:
            if self.repo_filter and project.name not in self.repo_filter:
                continue
            for author in self.authors:
                try:
                    commits = project.commits.list(author=author)
                except Exception:
                    continue
                for commit in commits:
                    commit_date = commit.committed_date
                    if self._filter_by_date(commit_date):
                        sha = commit.id
                        if sha not in processed_commits:
                            entry = {
                                "type": "commit",
                                "repo": project.name,
                                "message": commit.message.strip(),
                                "timestamp": commit_date,
                                "sha": sha,
                            }
                            entries.append(entry)
                            processed_commits.add(sha)
        return entries

    def fetch_pull_requests(self) -> List[Dict[str, Any]]:
        entries = []
        processed_pr_commits = set()
        for project in self.projects:
            if self.repo_filter and project.name not in self.repo_filter:
                continue
            # Fetch merge requests (GitLab's pull requests)
            merge_requests = project.mergerequests.list(state='all', all=True)
            for mr in merge_requests:
                if mr.author['username'] not in self.authors:
                    continue
                mr_date = mr.created_at
                if not self._filter_by_date(mr_date):
                    continue
                mr_entry = {
                    "type": "pull_request",
                    "repo": project.name,
                    "message": mr.title,
                    "timestamp": mr_date,
                    "pr_number": mr.iid,
                }
                entries.append(mr_entry)
                try:
                    mr_commits = mr.commits()
                except Exception:
                    mr_commits = []
                for mr_commit in mr_commits:
                    commit_date = mr_commit['created_at']
                    if self._filter_by_date(commit_date):
                        sha = mr_commit['id']
                        if sha in processed_pr_commits:
                            continue
                        mr_commit_entry = {
                            "type": "commit_from_pr",
                            "repo": project.name,
                            "message": mr_commit['message'].strip(),
                            "timestamp": commit_date,
                            "sha": sha,
                            "pr_title": mr.title,
                        }
                        entries.append(mr_commit_entry)
                        processed_pr_commits.add(sha)
                if self._stop_fetching(mr_date):
                    break
        return entries

    def fetch_issues(self) -> List[Dict[str, Any]]:
        entries = []
        for project in self.projects:
            if self.repo_filter and project.name not in self.repo_filter:
                continue
            issues = project.issues.list(assignee_id=self.gl.user.id)
            for issue in issues:
                issue_date = issue.created_at
                if self._filter_by_date(issue_date):
                    entry = {
                        "type": "issue",
                        "repo": project.name,
                        "message": issue.title,
                        "timestamp": issue_date,
                    }
                    entries.append(entry)
                if self._stop_fetching(issue_date):
                    break
        return entries