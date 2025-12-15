from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict

from models.schemas import (
    BranchListResponse,
    ValidTargetBranchesRequest,
    ValidTargetBranchesResponse,
    CreatePullRequestRequest,
    CreatePullRequestResponse,
    GetPullRequestDiffRequest,
    GetPullRequestDiffResponse,
    GetAuthorsRequest,
    GetAuthorsResponse,
    AuthorInfo,
    ActionsResponse,
    GetCurrentAuthorResponse,
    CloneRequest
)

from services.llm_service import set_llm, get_llm, trim_messages
from services.fetcher_service import store_fetcher, get_fetcher
from git_recap.utils import parse_entries_to_txt, parse_releases_to_txt
from aicore.llm.config import LlmConfig
from datetime import datetime, timezone
import requests
import os

router = APIRouter()


GITHUB_ACCESS_TOKEN_URL = 'https://github.com/login/oauth/access_token'


@router.post("/clone-repo")
async def clone_repository(request: CloneRequest):
    """
    Endpoint for cloning a repository from a URL.
    
    Args:
        request: CloneRequest containing the repository URL
        
    Returns:
        dict: Contains session_id for subsequent operations
        
    Raises:
        HTTPException: 400 for invalid URL, 500 for cloning failure
    """
    try:
        response = await create_llm_session()
        session_id = response.get("session_id")
        store_fetcher(session_id, request.url, "URL")
        return {"session_id": session_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clone repository: {str(e)}")


@router.get("/external-signup")
async def external_signup(app: str, accessToken: str, provider: str):
    """
    Handle external OAuth signup flow.
    
    Args:
        app: Application name
        accessToken: OAuth access token or authorization code
        provider: Provider name (e.g., "github")
        
    Returns:
        dict: Contains session_id, token, and provider information
        
    Raises:
        HTTPException: 400 for unsupported provider or token errors
    """
    if provider.lower() != "github":
        raise HTTPException(status_code=400, detail="Unsupported provider")

    params = {
        "client_id": os.getenv("VITE_GITHUB_CLIENT_ID"),
        "client_secret": os.getenv("VITE_GITHUB_CLIENT_SECRET"),
        "code": accessToken
    }
    
    headers = {
        "Accept": "application/json",
        "Accept-Encoding": "application/json"
    }
    
    response = requests.get(GITHUB_ACCESS_TOKEN_URL, params=params, headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail="Error fetching token from GitHub")
    
    githubUserData = response.json()
    token = githubUserData.get("access_token")
    if not token:
        raise HTTPException(status_code=400, detail="Failed to retrieve access token")
    
    response = await create_llm_session()
    response["token"] = token
    response["provider"] = provider
    return await store_fetcher_endpoint(response)


@router.post("/pat")
async def store_fetcher_endpoint(request: Request):
    """
    Endpoint to store the PAT associated with a session.
    
    Args:
        request: Contains JSON payload with 'session_id' and 'pat'
        
    Returns:
        dict: Contains session_id and username
        
    Raises:
        HTTPException: 400 if PAT is missing
    """
    if isinstance(request, Request):
        payload = await request.json()
    else:
        payload = request
    
    provider = payload.get("provider", "GitHub")
    token = payload.get("pat") or payload.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Missing required field: pat")
    
    response = await create_llm_session()  
    session_id = response.get("session_id")
    username = store_fetcher(session_id, token, provider)
    return {"session_id": session_id, "username": username}


async def create_llm_session(request: Optional[LlmConfig] = None):
    """
    Create a new LLM session with custom configuration.
    
    Args:
        request: Optional LLM configuration
        
    Returns:
        dict: Contains session_id and success message
        
    Raises:
        HTTPException: 500 if session creation fails
    """
    try:
        session_id = await set_llm(request)
        return {
            "session_id": session_id,
            "message": "LLM session created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repos")
async def get_repos(session_id: str):
    """
    Return a list of repositories for the given session_id.
    
    Args:
        session_id: The session identifier
        
    Returns:
        dict: Contains list of repository names
        
    Raises:
        HTTPException: 404 if session not found
    """
    fetcher = get_fetcher(session_id)
    return {"repos": fetcher.repos_names}


@router.get("/actions", response_model=ActionsResponse)
async def get_actions(
    session_id: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    repo_filter: Optional[List[str]] = Query(None),
    authors: Optional[List[str]] = Query(None)
):
    """
    Get actions for the specified session with optional filters.
    
    Returns a structured response including the actions list, user-facing
    informational message (if trimming occurred), and metadata about the
    trimming operation.
    
    Args:
        session_id: The session identifier
        start_date: Optional start date filter
        end_date: Optional end date filter
        repo_filter: Optional list of repositories to filter
        authors: Optional list of authors to filter
        
    Returns:
        ActionsResponse: Structured response with actions, message, and metadata
        
    Raises:
        HTTPException: 404 if session not found
    """
    if repo_filter is not None:
        repo_filter = sum([repo.split(",") for repo in repo_filter], [])
    if authors is not None:
        authors = sum([author.split(",") for author in authors], [])
    fetcher = get_fetcher(session_id)
    
    start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc) if start_date else None
    end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc) if end_date else None

    if start_dt:
        fetcher.start_date = start_dt
    if end_dt:
        fetcher.end_dt = end_dt
    if repo_filter is not None:
        fetcher.repo_filter = repo_filter
    if authors is not None:
        fetcher.authors = authors

    llm = get_llm(session_id)
    actions = fetcher.get_authored_messages()
    
    # Store original count before trimming
    original_count = len(actions)
    
    # Apply token limit trimming
    trimmed_actions = trim_messages(actions, llm.tokenizer)
    
    # Calculate how many items were removed
    trimmed_count = original_count - len(trimmed_actions)
    
    # Generate user-facing message if trimming occurred
    message = None
    if trimmed_count > 0:
        message = (
            f"We're running the free version with a maximum token limit for contextual input. "
            f"To stay within this limit, we automatically trimmed {trimmed_count} older Git "
            f"actionable{'s' if trimmed_count != 1 else ''} from the context. "
            f"We hope you understand!"
        )
    
    # Parse actions to text format
    actions_txt = parse_entries_to_txt(trimmed_actions)
    
    # Return structured response
    return ActionsResponse(
        actions=actions_txt,
        message=message,
        trimmed_count=trimmed_count,
        total_count=original_count
    )


@router.get("/release_notes")
async def get_release_notes(
    session_id: str,
    repo_filter: Optional[List[str]] = Query(None),
    num_old_releases: int = Query(..., ge=1)
):
    """
    Generate release notes for the latest release of a single repository.
    
    Args:
        session_id: The session identifier
        repo_filter: Must contain exactly one repository name
        num_old_releases: Number of previous releases to include for context
        
    Returns:
        dict: Contains actions and release notes text
        
    Raises:
        HTTPException: 400 for invalid input, 404 for session not found, 500 for errors
    """
    if repo_filter is None or len(repo_filter) != 1:
        raise HTTPException(status_code=400, detail="repo_filter must be a list containing exactly one repository name.")
    repo = repo_filter[0]

    try:
        fetcher = get_fetcher(session_id)
    except HTTPException:
        raise

    try:
        releases = fetcher.fetch_releases()
    except NotImplementedError:
        raise HTTPException(status_code=400, detail="Release fetching is not supported for this provider.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching releases: {str(e)}")

    releases_txt = parse_releases_to_txt(releases[:num_old_releases])
    repo_releases = [r for r in releases if r.get("repo") == repo]
    n_releases = len(repo_releases)
    if n_releases < 1:
        raise HTTPException(status_code=400, detail="Not enough releases found for the specified repository (need at least 1).")
    if num_old_releases < 1 or num_old_releases >= n_releases:
        raise HTTPException(
            status_code=400,
            detail=f"num_old_releases must be at least 1 and less than the number of releases available ({n_releases}) for this repository."
        )

    try:
        repo_releases.sort(key=lambda r: r.get("published_at") or r.get("created_at"), reverse=True)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to sort releases by date.")

    latest_release = repo_releases[0]

    release_date = latest_release.get("published_at") or latest_release.get("created_at")
    if not release_date:
        raise HTTPException(status_code=500, detail="Latest release does not have a valid date.")
    if isinstance(release_date, datetime):
        start_date_iso = release_date.astimezone(timezone.utc).isoformat()
    else:
        try:
            dt = datetime.fromisoformat(release_date)
            start_date_iso = dt.astimezone(timezone.utc).isoformat()
        except Exception:
            raise HTTPException(status_code=500, detail="Release date is not a valid ISO format.")

    fetcher.start_date = datetime.fromisoformat(start_date_iso)
    fetcher.end_dt = None
    fetcher.repo_filter = [repo]

    llm = get_llm(session_id)
    actions = fetcher.get_authored_messages()
    actions = trim_messages(actions, llm.tokenizer)
    actions_txt = parse_entries_to_txt(actions)

    return {"actions": "\n\n".join([actions_txt, releases_txt])}


@router.get("/branches", response_model=BranchListResponse)
async def get_branches(session_id: str, repo: str):
    """
    Get all branches for a given repository in the current session.
    
    Args:
        session_id: The session identifier
        repo: Repository name
        
    Returns:
        BranchListResponse: Contains list of branch names
        
    Raises:
        HTTPException: 400 if not supported, 404 if session not found, 500 for errors
    """
    fetcher = get_fetcher(session_id)
    try:
        fetcher.repo_filter = [repo]
        branches = fetcher.get_branches()
    except NotImplementedError:
        raise HTTPException(status_code=400, detail="Branch listing is not supported for this provider.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch branches: {str(e)}")
    return BranchListResponse(branches=branches)


@router.post("/valid-target-branches", response_model=ValidTargetBranchesResponse)
async def get_valid_target_branches(req: ValidTargetBranchesRequest):
    """
    Get all valid target branches for a given source branch in a repository.
    
    Args:
        req: ValidTargetBranchesRequest containing session_id, repo, and source_branch
        
    Returns:
        ValidTargetBranchesResponse: Contains list of valid target branch names
        
    Raises:
        HTTPException: 400 for validation errors, 404 if session not found, 500 for errors
    """
    fetcher = get_fetcher(req.session_id)
    try:
        fetcher.repo_filter = [req.repo]
        valid_targets = fetcher.get_valid_target_branches(req.source_branch)
    except NotImplementedError:
        raise HTTPException(status_code=400, detail="Target branch validation is not supported for this provider.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate target branches: {str(e)}")
    return ValidTargetBranchesResponse(valid_target_branches=valid_targets)


@router.post("/create-pull-request", response_model=CreatePullRequestResponse)
async def create_pull_request(req: CreatePullRequestRequest):
    """
    Create a pull request between two branches with optional metadata.
    
    Args:
        req: CreatePullRequestRequest containing all PR details
        
    Returns:
        CreatePullRequestResponse: Contains PR URL, number, state, and success status
        
    Raises:
        HTTPException: 400 for validation errors, 404 if session not found, 500 for errors
    """
    fetcher = get_fetcher(req.session_id)
    fetcher.repo_filter = [req.repo]
    if not req.description or not req.description.strip():
        raise HTTPException(status_code=400, detail="Description is required for pull request creation.")
    try:
        result = fetcher.create_pull_request(
            head_branch=req.source_branch,
            base_branch=req.target_branch,
            title=req.title or f"Merge {req.source_branch} into {req.target_branch}",
            body=req.description,
            draft=req.draft or False,
            reviewers=req.reviewers,
            assignees=req.assignees,
            labels=req.labels,
        )
    except NotImplementedError:
        raise HTTPException(status_code=400, detail="Pull request creation is not supported for this provider.")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create pull request: {str(e)}")
    return CreatePullRequestResponse(
        url=result.get("url"),
        number=result.get("number"),
        state=result.get("state"),
        success=result.get("success", False),
        generated_description=None
    )


@router.post("/get-pull-request-diff")
async def get_pull_request_diff(req: GetPullRequestDiffRequest):
    """
    Get the diff between two branches for pull request preview.
    
    Args:
        req: GetPullRequestDiffRequest containing session_id, repo, source_branch, and target_branch
        
    Returns:
        dict: Contains formatted commit actions between branches
        
    Raises:
        HTTPException: 400 if not supported or GitHub only, 404 if session not found, 500 for errors
    """
    fetcher = get_fetcher(req.session_id)
    fetcher.repo_filter = [req.repo]
    provider = type(fetcher).__name__.lower()
    if "github" not in provider:
        raise HTTPException(status_code=400, detail="Pull request diff is only supported for GitHub provider.")
    try:
        commits = fetcher.fetch_branch_diff_commits(req.source_branch, req.target_branch)
    except NotImplementedError:
        raise HTTPException(status_code=400, detail="Branch diff is not supported for this provider.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch pull request diff: {str(e)}")
    return {"actions": parse_entries_to_txt(commits)}


@router.post("/authors", response_model=GetAuthorsResponse)
async def get_authors(request: GetAuthorsRequest):
    """
    Retrieve list of unique authors from specified repositories.
    
    Args:
        request: GetAuthorsRequest containing session_id and optional repo_names
    
    Returns:
        GetAuthorsResponse with list of authors and metadata
    
    Raises:
        HTTPException: 404 if session not found, 500 for fetcher errors
    """
    try:
        fetcher = get_fetcher(request.session_id)
        
        if not fetcher:
            raise HTTPException(
                status_code=404,
                detail=f"Session {request.session_id} not found or expired"
            )
        
        authors_data = fetcher.get_authors(request.repo_names or [])
        
        authors = [
            AuthorInfo(name=author["name"], email=author["email"])
            for author in authors_data
        ]
        
        response = GetAuthorsResponse(
            authors=authors,
            total_count=len(authors),
            repo_count=len(request.repo_names) if request.repo_names else 0
        )
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching authors: {str(e)}"
        )


@router.get("/current-author", response_model=GetCurrentAuthorResponse)
async def get_current_author(session_id: str = Query(..., description="Session identifier")):
    """
    Retrieve the current authenticated user's information from the fetcher.
    
    Args:
        session_id: The session identifier
        
    Returns:
        GetCurrentAuthorResponse: Contains optional author information (name and email)
        
    Raises:
        HTTPException: 404 if session not found, 500 for errors
    """
    try:
        fetcher = get_fetcher(session_id)
        
        if not fetcher:
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found or expired"
            )
        
        try:
            author_info = fetcher.get_current_author()
        except NotImplementedError:
            author_info = None
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error retrieving current author: {str(e)}"
            )
        
        return GetCurrentAuthorResponse(author=author_info)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching current author: {str(e)}"
        )