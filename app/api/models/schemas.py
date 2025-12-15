from pydantic import BaseModel, model_validator, Field
from typing import Dict, Self, Optional, Any, List
import ulid
import re

class ChatRequest(BaseModel):
    session_id: str = ""
    message: str
    model_params: Optional[Dict[str, Any]] = None

    @model_validator(mode="after")
    def set_session_id(self) -> Self:
        if not self.session_id:
            self.session_id = ulid.ulid()
        return self


# --- Branch Listing ---
class BranchListResponse(BaseModel):
    branches: List[str] = Field(..., description="List of branch names in the repository.")
    
    @model_validator(mode='after')
    def sort_branches(self):
        """Sort branches with main/master at the top, then alphabetically."""
        priority_branches = []
        other_branches = []
        
        for branch in self.branches:
            if branch.lower() in ('main', 'master'):
                priority_branches.append(branch)
            else:
                other_branches.append(branch)
        
        # Sort priority branches (main, master) and other branches separately
        priority_branches.sort(key=lambda x: (x.lower() != 'main', x.lower()))
        other_branches.sort()
        
        self.branches = priority_branches + other_branches
        return self


# --- Valid Target Branches ---
class ValidTargetBranchesRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier.")
    repo: str = Field(..., description="Repository name.")
    source_branch: str = Field(..., description="Source branch name.")

class ValidTargetBranchesResponse(BaseModel):
    valid_target_branches: List[str] = Field(..., description="List of valid target branch names.")
    
    @model_validator(mode='after')
    def sort_branches(self):
        """Sort branches with main/master at the top, then alphabetically."""
        priority_branches = []
        other_branches = []
        
        for branch in self.valid_target_branches:
            if branch.lower() in ('main', 'master'):
                priority_branches.append(branch)
            else:
                other_branches.append(branch)
        
        # Sort priority branches (main, master) and other branches separately
        priority_branches.sort(key=lambda x: (x.lower() != 'main', x.lower()))
        other_branches.sort()
        
        self.valid_target_branches = priority_branches + other_branches
        return self


# --- Pull Request Creation ---
class CreatePullRequestRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier.")
    repo: str = Field(..., description="Repository name.")
    source_branch: str = Field(..., description="Source branch name.")
    target_branch: str = Field(..., description="Target branch name.")
    body: str = Field(..., description="Body of the pull request. This field is required.")
    draft: Optional[bool] = Field(False, description="Whether to create the PR as a draft.")
    reviewers: Optional[List[str]] = Field(None, description="List of reviewer usernames.")
    assignees: Optional[List[str]] = Field(None, description="List of assignee usernames.")
    labels: Optional[List[str]] = Field(None, description="List of label names.")
    description: Optional[str]=None
    title: Optional[str]=None

    @model_validator(mode="after")
    def get_title_description(self)->Self:
        title, description = self.extract_title_and_description(self.body)
        if self.title is None:
            self.title = title
        if self.description is None:
            self.description = description

        return self

    @staticmethod
    def extract_title_and_description(pr_text: str):
        """
        Extracts the PR title and description from a markdown-formatted PR text.
        
        Expected format:
        Title: <title text>

        ## Summary
        ...
        """

        # Use regex to find the title (first line starting with 'Title:')
        title_match = re.search(r'^\s*Title:\s*(.+?)\s*$', pr_text, re.MULTILINE)

        # Everything after the title is the description
        description_match = re.search(r'^\s*Title:.*?\n+(.*)', pr_text, re.DOTALL)

        title = title_match.group(1).strip() if title_match else ""
        description = description_match.group(1).strip() if description_match else ""

        return title, description



# --- Pull Request Diff ---
class GetPullRequestDiffRequest(BaseModel):
    session_id: str = Field(..., description="Session identifier.")
    repo: str = Field(..., description="Repository name.")
    source_branch: str = Field(..., description="Source branch name.")
    target_branch: str = Field(..., description="Target branch name.")

class GetPullRequestDiffResponse(BaseModel):
    commits: List[dict] = Field(..., description="List of commit dicts in the diff.")

class CreatePullRequestResponse(BaseModel):
    url: str = Field(..., description="URL of the created pull request.")
    number: int = Field(..., description="Pull request number.")
    state: str = Field(..., description="State of the pull request (e.g., open, closed).")
    success: bool = Field(..., description="Whether the pull request was created successfully.")
    # Optionally, include the generated description if LLM was used
    generated_description: Optional[str] = Field(None, description="LLM-generated PR description, if applicable.")


# --- Utility: Commit List for PR Description Generation ---
class CommitMessagesForPRDescriptionRequest(BaseModel):
    commit_messages: List[str] = Field(..., description="List of commit messages to summarize.")
    session_id: str = Field(..., description="Session identifier.")

class PRDescriptionResponse(BaseModel):
    description: str = Field(..., description="LLM-generated pull request description.")


# --- Authors Endpoint Schemas ---
class AuthorInfo(BaseModel):
    """Individual author information"""
    name: str = Field(..., description="Author's name")
    email: str = Field(..., description="Author's email address")


class GetAuthorsRequest(BaseModel):
    """Request model for fetching authors"""
    session_id: str = Field(..., description="Session identifier")
    repo_names: Optional[List[str]] = Field(
        default=[],
        description="List of repository names to fetch authors from. Empty list fetches from all repositories."
    )


class GetAuthorsResponse(BaseModel):
    """Response model containing list of authors"""
    authors: List[AuthorInfo] = Field(..., description="List of unique authors")
    total_count: int = Field(..., description="Total number of unique authors")
    repo_count: int = Field(..., description="Number of repositories processed")