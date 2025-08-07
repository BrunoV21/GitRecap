from typing import Dict, Optional, List, Any
from fastapi import HTTPException
from git_recap.providers.base_fetcher import BaseFetcher
from git_recap.providers import GitHubFetcher, AzureFetcher, GitLabFetcher, URLFetcher
import ulid

# In-memory store mapping session_id to its respective fetcher instance
fetchers: Dict[str, BaseFetcher] = {}

def store_fetcher(session_id: str, pat: str, provider: Optional[str] = "GitHub") -> None:
    """
    Store the provided PAT associated with the given session_id.

    Args:
        session_id: The session identifier tied to the active session.
        pat: The Personal Access Token to be stored (or URL for URL provider).
        provider: The provider identifier (default is "GitHub"). 
                 Can be "Azure Devops", "GitLab", or "URL".

    Raises:
        HTTPException: If the session_id or PAT/URL is invalid or unsupported provider.
    """
    if not session_id or not pat:
        raise HTTPException(status_code=400, detail="Invalid session_id or PAT/URL")
    try:
        if provider == "GitHub":
            fetchers[session_id] = GitHubFetcher(pat=pat)
        elif provider == "Azure Devops":
            # For Azure, organization_url should be handled at a higher layer if needed
            fetchers[session_id] = AzureFetcher(pat=pat, organization_url="")
        elif provider == "GitLab":
            fetchers[session_id] = GitLabFetcher(pat=pat)
        elif provider == "URL":
            fetchers[session_id] = URLFetcher(url=pat)
        else:
            raise HTTPException(status_code=400, detail="Unsupported provider")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize {provider} fetcher: {str(e)}"
        )

def get_fetcher(session_id: str) -> BaseFetcher:
    """
    Retrieve the stored fetcher instance for the provided session_id.

    Args:
        session_id: The session identifier.

    Returns:
        The fetcher instance associated with the session_id.

    Raises:
        HTTPException: If no fetcher is found for the given session_id.
    """
    fetcher = fetchers.get(session_id)
    if not fetcher:
        raise HTTPException(status_code=404, detail="Session not found")
    return fetcher

def expire_fetcher(session_id: str) -> None:
    """
    Remove the fetcher associated with the given session_id.

    This function is used for cleaning up resources by expiring the stored fetcher instance
    when its corresponding session is expired.

    Args:
        session_id: The session identifier whose associated fetcher should be removed.
    """
    fetcher = fetchers.pop(session_id, None)
    if fetcher and hasattr(fetcher, 'clear'):
        fetcher.clear()

def generate_session_id() -> str:
    """
    Generate a new unique session ID.

    Returns:
        str: A new ULID-based session identifier.
    """
    return ulid.ulid()

# --- Release Notes Support ---
def fetch_commits_for_release_notes(
    session_id: str,
    start_date: Optional[Any] = None,
    end_date: Optional[Any] = None,
    repo_filter: Optional[List[str]] = None,
    authors: Optional[List[str]] = None
) -> List[dict]:
    """
    Fetch commit entries for release notes generation.

    Args:
        session_id: The session identifier.
        start_date: Optional start date filter (string or datetime).
        end_date: Optional end date filter (string or datetime).
        repo_filter: Optional list of repositories.
        authors: Optional list of authors.

    Returns:
        List of commit entries (dicts).
    """
    fetcher = get_fetcher(session_id)
    if start_date:
        fetcher.start_date = start_date
    if end_date:
        fetcher.end_date = end_date
    if repo_filter is not None:
        fetcher.repo_filter = repo_filter
    if authors is not None:
        fetcher.authors = authors
    # Prefer fetch_commits if available, fallback to get_authored_messages
    if hasattr(fetcher, "fetch_commits"):
        return fetcher.fetch_commits()
    else:
        return fetcher.get_authored_messages()