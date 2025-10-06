from github import Github
from datetime import datetime
from typing import List, Dict, Any, Optional
from git_recap.providers.base_fetcher import BaseFetcher

class GitHubFetcher(BaseFetcher):
    """
    Fetcher implementation for GitHub repositories.

    Supports fetching commits, pull requests, issues, and releases.
    """

    def __init__(self, pat: str, start_date=None, end_date=None, repo_filter=None, authors=None):
        super().__init__(pat, start_date, end_date, repo_filter, authors)
        self.github = Github(self.pat)
        self.user = self.github.get_user()
        self.repos = self.user.get_repos(affiliation="owner,collaborator,organization_member")
        self.authors.append(self.user.login)

    @property
    def repos_names(self) -> List[str]:
        return [repo.name for repo in self.repos]

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
        for repo in self.repos:
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
        # Retrieve repos where you're owner, a collaborator, or an organization member.
        for repo in self.repos:
            if self.repo_filter and repo.name not in self.repo_filter:
                continue
            pulls = repo.get_pulls(state='all')
            for i, pr in enumerate(pulls, start=1):
                if pr.user.login not in self.authors:
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

    def fetch_releases(self) -> List[Dict[str, Any]]:
        """
        Fetch releases for all repositories accessible to the user.

        Returns:
            List[Dict[str, Any]]: List of releases, each as a structured dictionary with:
                - tag_name: str
                - name: str
                - repo: str
                - author: str
                - published_at: datetime
                - created_at: datetime
                - draft: bool
                - prerelease: bool
                - body: str
                - assets: List[Dict[str, Any]] (each with name, size, download_url, content_type, etc.)
        """
        releases = []
        for repo in self.repos:
            if self.repo_filter and repo.name not in self.repo_filter:
                continue
            try:
                for rel in repo.get_releases():
                    # Compose asset list
                    assets = []
                    for asset in rel.get_assets():
                        assets.append({
                            "name": asset.name,
                            "size": asset.size,
                            "download_url": asset.browser_download_url,
                            "content_type": asset.content_type,
                            "created_at": asset.created_at,
                            "updated_at": asset.updated_at,
                        })
                    release_entry = {
                        "tag_name": rel.tag_name,
                        "name": rel.title if hasattr(rel, "title") else rel.name,
                        "repo": repo.name,
                        "author": rel.author.login if rel.author else None,
                        "published_at": rel.published_at,
                        "created_at": rel.created_at,
                        "draft": rel.draft,
                        "prerelease": rel.prerelease,
                        "body": rel.body,
                        "assets": assets,
                    }
                    releases.append(release_entry)
            except Exception:
                # If fetching releases fails for a repo, skip it (could be permissions or no releases)
                continue
        return releases

    def open_pr(
        self,
        repo_name: str,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str,
        draft: bool = False,
        reviewers: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new pull request on GitHub.

        Args:
            repo_name (str): Name of the repository.
            head_branch (str): The name of the branch where your changes are implemented (source).
            base_branch (str): The name of the branch you want the changes pulled into (target).
            title (str): Title of the pull request.
            body (str): Body/description of the pull request (supports markdown).
            draft (bool): Whether to create the PR as a draft.
            reviewers (List[str], optional): List of GitHub usernames to request review from.
            assignees (List[str], optional): List of GitHub usernames to assign to the PR.
            labels (List[str], optional): List of label names to add to the PR.

        Returns:
            Dict[str, Any]: Information about the created pull request (number, url, etc.).
        """
        print(f"Listing branches for repository '{repo_name}'...")
        repo = None
        for r in self.repos:
            if r.name == repo_name:
                repo = r
                break
        if not repo:
            raise ValueError(f"Repository '{repo_name}' not found or not accessible.")

        branches = [b.name for b in repo.get_branches()]
        print(f"Available branches: {branches}")
        if head_branch not in branches:
            raise ValueError(f"Source branch '{head_branch}' not found in repository '{repo_name}'.")
        if base_branch not in branches:
            raise ValueError(f"Target branch '{base_branch}' not found in repository '{repo_name}'.")

        print(f"Checking for existing pull requests from '{head_branch}' to '{base_branch}'...")
        existing_prs = repo.get_pulls(state="open", head=f"{repo.owner.login}:{head_branch}", base=base_branch)
        for pr in existing_prs:
            if pr.head.ref == head_branch and pr.base.ref == base_branch:
                print(f"Pull request already exists: #{pr.number} {pr.html_url}")
                return {"number": pr.number, "url": pr.html_url, "already_exists": True}

        print(f"Creating pull request: {title}")
        try:
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head_branch,
                base=base_branch,
                draft=draft
            )
        except Exception as e:
            print(f"Error creating pull request: {e}")
            raise

        # Optionally add reviewers, assignees, and labels
        if reviewers:
            try:
                pr.create_review_request(reviewers=reviewers)
                print(f"Requested reviewers: {reviewers}")
            except Exception as e:
                print(f"Could not add reviewers: {e}")
        if assignees:
            try:
                pr.add_to_assignees(*assignees)
                print(f"Added assignees: {assignees}")
            except Exception as e:
                print(f"Could not add assignees: {e}")
        if labels:
            try:
                pr.add_to_labels(*labels)
                print(f"Added labels: {labels}")
            except Exception as e:
                print(f"Could not add labels: {e}")

        print(f"Pull request created: #{pr.number} {pr.html_url}")
        return {
            "number": pr.number,
            "url": pr.html_url,
            "already_exists": False
        }