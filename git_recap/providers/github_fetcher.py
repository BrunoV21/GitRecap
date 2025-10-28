from github import Github
from github import GithubException
from datetime import datetime
from typing import List, Dict, Any, Optional
from git_recap.providers.base_fetcher import BaseFetcher
import logging

logger = logging.getLogger(__name__)


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

    def fetch_branch_diff_commits(self, source_branch: str, target_branch: str) -> List[Dict[str, Any]]:
        entries = []
        processed_commits = set()
        for repo in self.repos:
            if self.repo_filter and repo.name not in self.repo_filter:
                continue
            try:
                comparison = repo.compare(target_branch, source_branch)
                for commit in comparison.commits:
                    commit_date = commit.commit.author.date
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
            except GithubException as e:
                logger.error(f"Failed to compare branches in {repo.name}: {str(e)}")
                continue
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

    def get_branches(self) -> List[str]:
        """
        Get all branches in the repository.
        Returns:
            List[str]: List of branch names.
        Raises:
            Exception: If API rate limits are exceeded or authentication fails.
        """
        logger.debug("Fetching branches from all accessible repositories")
        try:
            branches = []
            for repo in self.repos:
                if self.repo_filter and repo.name not in self.repo_filter:
                    continue
                logger.debug(f"Fetching branches for repository: {repo.name}")
                repo_branches = repo.get_branches()
                for branch in repo_branches:
                    branches.append(branch.name)
            logger.debug(f"Successfully fetched {len(branches)} branches")
            return branches
        except GithubException as e:
            if e.status == 403:
                logger.error(f"Rate limit exceeded or authentication failed: {str(e)}")
                raise Exception(f"Failed to fetch branches: Rate limit exceeded or authentication failed - {str(e)}")
            elif e.status == 401:
                logger.error(f"Authentication failed: {str(e)}")
                raise Exception(f"Failed to fetch branches: Authentication failed - {str(e)}")
            else:
                logger.error(f"GitHub API error while fetching branches: {str(e)}")
                raise Exception(f"Failed to fetch branches: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while fetching branches: {str(e)}")
            raise Exception(f"Failed to fetch branches: {str(e)}")

    def get_valid_target_branches(self, source_branch: str) -> List[str]:
        """
        Get branches that can receive a pull request from the source branch.
        Validates that the source branch exists, filters out branches with existing
        open PRs from source, excludes the source branch itself, and optionally
        checks if source is ahead of target.
        Args:
            source_branch (str): The source branch name.
        Returns:
            List[str]: List of valid target branch names.
        Raises:
            ValueError: If source branch does not exist.
            Exception: If API errors occur during validation.
        """
        logger.debug(f"Validating target branches for source branch: {source_branch}")
        try:
            all_branches = self.get_branches()
            if source_branch not in all_branches:
                logger.error(f"Source branch '{source_branch}' does not exist")
                raise ValueError(f"Source branch '{source_branch}' does not exist")
            valid_targets = []
            for repo in self.repos:
                if self.repo_filter and repo.name not in self.repo_filter:
                    continue
                logger.debug(f"Processing repository: {repo.name}")
                repo_branches = [branch.name for branch in repo.get_branches()]
                # Get existing open PRs from source branch
                try:
                    open_prs = repo.get_pulls(state='open', head=source_branch)
                except GithubException as e:
                    logger.error(f"GitHub API error while getting PRs: {str(e)}")
                    raise Exception(f"Failed to validate target branches: {str(e)}")
                existing_pr_targets = set()
                for pr in open_prs:
                    existing_pr_targets.add(pr.base.ref)
                    logger.debug(f"Found existing PR from {source_branch} to {pr.base.ref}")
                for branch_name in repo_branches:
                    if branch_name == source_branch:
                        logger.debug(f"Excluding source branch: {branch_name}")
                        continue
                    if branch_name in existing_pr_targets:
                        logger.debug(f"Excluding branch with existing PR: {branch_name}")
                        continue
                    # Optionally check if source is ahead of target (performance cost)
                    valid_targets.append(branch_name)
                    logger.debug(f"Valid target branch: {branch_name}")
            logger.debug(f"Found {len(valid_targets)} valid target branches")
            return valid_targets
        except ValueError:
            raise
        except GithubException as e:
            logger.error(f"GitHub API error while validating target branches: {str(e)}")
            raise Exception(f"Failed to validate target branches: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while validating target branches: {str(e)}")
            raise Exception(f"Failed to validate target branches: {str(e)}")

    def create_pull_request(
        self,
        head_branch: str,
        base_branch: str,
        title: str,
        body: str,
        draft: bool = False,
        reviewers: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a pull request between two branches with optional metadata.
        Args:
            head_branch: Source branch for the PR.
            base_branch: Target branch for the PR.
            title: PR title.
            body: PR description.
            draft: Whether to create as draft PR (default: False).
            reviewers: List of reviewer usernames (optional).
            assignees: List of assignee usernames (optional).
            labels: List of label names (optional).
        Returns:
            Dict[str, Any]: Dictionary containing PR metadata or error information.
        Raises:
            ValueError: If branches don't exist or PR already exists.
        """
        logger.info(f"Creating pull request from {head_branch} to {base_branch}")
        try:
            all_branches = self.get_branches()
            if head_branch not in all_branches:
                logger.error(f"Head branch '{head_branch}' does not exist")
                raise ValueError(f"Head branch '{head_branch}' does not exist")
            if base_branch not in all_branches:
                logger.error(f"Base branch '{base_branch}' does not exist")
                raise ValueError(f"Base branch '{base_branch}' does not exist")
            for repo in self.repos:
                if self.repo_filter and repo.name not in self.repo_filter:
                    continue
                logger.debug(f"Checking for existing PRs in repository: {repo.name}")
                try:
                    existing_prs = repo.get_pulls(state='open', head=head_branch, base=base_branch)
                except GithubException as e:
                    logger.error(f"GitHub API error while getting PRs: {str(e)}")
                    raise
                if hasattr(existing_prs, "totalCount") and existing_prs.totalCount > 0:
                    logger.error(f"Pull request already exists from {head_branch} to {base_branch}")
                    raise ValueError(f"Pull request already exists from {head_branch} to {base_branch}")
                elif isinstance(existing_prs, list) and len(existing_prs) > 0:
                    logger.error(f"Pull request already exists from {head_branch} to {base_branch}")
                    raise ValueError(f"Pull request already exists from {head_branch} to {base_branch}")
                logger.info(f"Creating pull request in repository: {repo.name}")
                try:
                    pr = repo.create_pull(
                        title=title,
                        body=body,
                        head=head_branch,
                        base=base_branch,
                        draft=draft
                    )
                    logger.info(f"Pull request created successfully: {pr.html_url}")
                    if reviewers and len(reviewers) > 0:
                        try:
                            logger.debug(f"Adding reviewers: {reviewers}")
                            pr.create_review_request(reviewers=reviewers)
                            logger.info(f"Successfully added reviewers: {reviewers}")
                        except GithubException as e:
                            logger.warning(f"Failed to add reviewers: {str(e)}")
                    if assignees and len(assignees) > 0:
                        try:
                            logger.debug(f"Adding assignees: {assignees}")
                            pr.add_to_assignees(*assignees)
                            logger.info(f"Successfully added assignees: {assignees}")
                        except GithubException as e:
                            logger.warning(f"Failed to add assignees: {str(e)}")
                    if labels and len(labels) > 0:
                        try:
                            logger.debug(f"Adding labels: {labels}")
                            pr.add_to_labels(*labels)
                            logger.info(f"Successfully added labels: {labels}")
                        except GithubException as e:
                            logger.warning(f"Failed to add labels: {str(e)}")
                    return {
                        "url": pr.html_url,
                        "number": pr.number,
                        "state": pr.state,
                        "success": True
                    }
                except GithubException as e:
                    if e.status == 404:
                        logger.error(f"Branch not found: {str(e)}")
                        raise ValueError(f"Branch not found: {str(e)}")
                    elif e.status == 403:
                        logger.error(f"Permission denied: {str(e)}")
                        raise GithubException(e.status, f"Permission denied: {str(e)}", e.headers)
                    elif e.status == 422:
                        logger.error(f"Merge conflict or validation error: {str(e)}")
                        raise ValueError(f"Merge conflict or validation error: {str(e)}")
                    else:
                        logger.error(f"GitHub API error: {str(e)}")
                        raise
            logger.error("No repository found to create pull request")
            raise ValueError("No repository found to create pull request")
        except (ValueError, GithubException):
            raise
        except Exception as e:
            logger.error(f"Unexpected error while creating pull request: {str(e)}")
            raise Exception(f"Failed to create pull request: {str(e)}")