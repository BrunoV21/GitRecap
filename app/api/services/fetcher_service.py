from typing import Dict, Optional
from fastapi import HTTPException
from git_recap.providers.base_fetcher import BaseFetcher
from git_recap.fetcher import GitHubFetcher, AzureFetcher, GitLabFetcher

# In-memory store mapping session_id to PAT
fetchers: Dict[str, BaseFetcher] = {}

def store_fetcher(session_id: str, pat: str, provider :Optional[str]="GitHub") -> None:
    """
    Store the provided PAT associated with the given session_id.
    
    Args:
        session_id: The session identifier that ties the PAT to an active session.
        pat: The Personal Access Token to be stored.
    
    Raises:
        HTTPException: If the session_id or pat is invalid.
    """
    if not session_id or not pat:
        raise HTTPException(status_code=400, detail="Invalid session_id or PAT")
    
    # Optionally, perform any additional validation or encryption here
    if provider == "GitHub":
        fetchers[session_id] = GitHubFetcher(pat=pat)
    elif provider == "Azure Devops":
        fetchers[session_id] = AzureFetcher(pat=pat)
    elif provider == "GitLab":
        fetchers[session_id] = GitLabFetcher(pat=pat)

def get_fetcher(session_id: str) -> BaseFetcher:
    """
    Retrieve the stored PAT for the provided session_id.
    
    Args:
        session_id: The session identifier.
    
    Returns:
        The stored PAT string.
    
    Raises:
        HTTPException: If no PAT is found for the given session_id.
    """
    fetcher = fetchers.get(session_id)
    if not fetcher:
        raise HTTPException(status_code=404, detail="Session not found")
    return fetcher