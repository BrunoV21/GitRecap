from fastapi import APIRouter, HTTPException, Request

from models.schemas import ChatRequest
from services.llm_service import initialize_llm_session, set_llm
from services.fetcher_service import store_fetcher, get_fetcher
from aicore.llm.config import LlmConfig
from typing import Optional
import requests
import os

router = APIRouter()

GITHUB_ACCESS_TOKEN_URL = 'https://github.com/login/oauth/access_token'

@router.get("/external-signup")
async def external_signup(app: str, accessToken: str, provider: str):
    if provider.lower() != "github":
        raise HTTPException(status_code=400, detail="Unsupported provider")

    # Build the URL to exchange the code for a token
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
    final_response = await store_fetcher_endpoint(response)
    session_id = final_response.get("session_id")    
    # Here you can further process the token, create a user session, etc.
    return {"session_id": session_id}

@router.post("/pat")
async def store_fetcher_endpoint(request: Request):
    """
    Endpoint to store the PAT associated with a session.
    Expects JSON payload with 'session_id' and 'pat'
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
    response["token"] = token    
    session_id = response.get("session_id")
    store_fetcher(session_id, token, provider)
    return {"session_id": session_id}

@router.post("/llm")
async def create_llm_session(
    request: Optional[LlmConfig] = None
):
    """
    Create a new LLM session with custom configuration
    
    Returns a session ID that can be used in subsequent chat requests
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
    In a real implementation, you might use the stored PAT (or session data)
    to query the code host for the actual list of repositories.
    """
    fetcher = get_fetcher(session_id)
    return {"repos": fetcher.repos_names}

@router.post("/chat")
async def chat(
    chat_request: ChatRequest
):
    try:
        llm = await initialize_llm_session(chat_request.session_id)
        response = await llm.acomplete(chat_request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))