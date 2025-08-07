import json
import os
import uuid
from typing import Dict, List, Optional
from fastapi import HTTPException
import asyncio
import random

from aicore.logger import _logger
from aicore.config import Config
from aicore.llm import Llm
from aicore.llm.config import LlmConfig
from services.prompts import SELECT_QUIRKY_REMARK_SYSTEM, SYSTEM, quirky_remarks

# --- Release Notes Prompt Template (should match the one in prompts.py and websockets.py) ---
RELEASE_NOTES_PROMPT = """
Given the following list of commit messages and metadata, generate a structured release notes document suitable for end users and developers. Group related changes, highlight breaking changes, and use clear section headers. Do not include dates unless specifically requested. Be concise and professional.

{COMMITS}
"""

def get_random_quirky_remarks(remarks_list, n=5):
    """
    Returns a list of n randomly selected quirky remarks.
    
    Args:
        remarks_list (list): The full list of quirky remarks.
        n (int): Number of remarks to select (default is 5).
        
    Returns:
        list: Randomly selected quirky remarks.
    """
    return random.sample(remarks_list, min(n, len(remarks_list)))

# LLM session storage
llm_sessions: Dict[str, Llm] = {}

async def initialize_llm_session(session_id: str, config: Optional[LlmConfig] = None) -> Llm:
    """
    Initialize or retrieve an LLM session.
    
    Args:
        session_id: The session identifier.
        config: Optional custom LLM configuration.
        
    Returns:
        An initialized LLM instance.
    """
    if session_id in llm_sessions:
        return llm_sessions[session_id]
    
    # Initialize LLM based on whether custom config is provided.
    if config:
        # Convert Pydantic model to dict and use for LLM initialization.
        config_dict = config.dict(exclude_none=True)
        llm = Llm.from_config(config_dict)
    else:
        config = Config.from_environment()
        llm = Llm.from_config(config.llm)
    llm.session_id = session_id
    llm_sessions[session_id] = llm
    return llm

async def set_llm(config: Optional[LlmConfig] = None) -> str:
    """
    Set a custom LLM configuration and return a new session ID.
    
    Args:
        config: The LLM configuration to use.
        
    Returns:
        A new session ID linked to the configured LLM.
    """
    try:
        # Generate a unique session ID.
        session_id = str(uuid.uuid4())
        
        # Initialize the LLM with the provided configuration.
        await initialize_llm_session(session_id, config)
        
        # Schedule session expiration exactly 5 minutes after session creation.
        asyncio.create_task(schedule_session_expiration(session_id))
        
        return session_id
    except Exception as e:
        print(f"Error setting custom LLM: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to set custom LLM: {str(e)}")
    
def get_llm(session_id: str) -> Optional[Llm]:
    """
    Retrieve the LLM instance associated with the given session_id.
    
    Args:
        session_id: The session identifier.
        
    Returns:
        The LLM instance if found.
        
    Raises:
        HTTPException: If the session is not found.
    """
    if session_id not in llm_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return llm_sessions.get(session_id)
    
def trim_messages(messages, tokenizer_fn, max_tokens: Optional[int] = None):
    """
    Trim messages to ensure that the total token count does not exceed max_tokens.
    
    Args:
        messages: List of messages.
        tokenizer_fn: Function to tokenize messages.
        max_tokens: Maximum allowed tokens.
    
    Returns:
        Trimmed list of messages.
    """
    max_tokens = max_tokens or int(os.environ.get("MAX_HISTORY_TOKENS", 16000))
    while messages and sum(len(tokenizer_fn(str(msg))) for msg in messages) > max_tokens:
        messages.pop(0)  # Remove from the beginning
    return messages
    
async def run_concurrent_tasks(llm, message):
    """
    Run concurrent tasks for the LLM and logger.
    
    Args:
        llm: The LLM instance.
        message: Message to process.
    
    Yields:
        Chunks of logs from the logger.
    """
    QUIRKY_SYSTEM = SELECT_QUIRKY_REMARK_SYSTEM.format(
        examples=json.dumps(get_random_quirky_remarks(quirky_remarks), indent=4)
    )
    asyncio.create_task(llm.acomplete(message, system_prompt=[SYSTEM, QUIRKY_SYSTEM]))
    asyncio.create_task(_logger.distribute())
    # Stream logger output while LLM is running.
    while True:        
        async for chunk in _logger.get_session_logs(llm.session_id):
            yield chunk  # Yield each chunk directly

def simulate_llm_response(message: str) -> List[str]:
    """
    Simulate LLM response by breaking a dummy response into chunks.
    
    Args:
        message: Input message.
        
    Returns:
        List of response chunks.
    """
    response = (
        f"This is a simulated response to: '{message}'. In a real implementation, this would be the actual output "
        "from your LLM model. The response would be generated in chunks and streamed back to the client as they become available."
    )
    
    # Break into chunks of approximately 10 characters.
    chunks = []
    for i in range(0, len(response), 10):
        chunks.append(response[i:i+10])
    
    return chunks

# --- Release Notes LLM Orchestration ---
async def generate_release_notes_llm(llm: Llm, commits_txt: str) -> str:
    """
    Generate release notes using the LLM given a plain text list of commits.
    Args:
        llm: The LLM instance.
        commits_txt: The plain text list of commits/messages.
    Returns:
        The generated release notes as a string.
    """
    prompt = RELEASE_NOTES_PROMPT.format(COMMITS=commits_txt)
    # In a real implementation, you would stream or await the LLM's response.
    # For now, just return a dummy string.
    # response = await llm.acomplete([prompt])
    # return response
    return f"[RELEASE NOTES PLACEHOLDER]\n\n{commits_txt}"

def cleanup_llm_sessions():
    """Clean up all LLM sessions."""
    llm_sessions.clear()

async def schedule_session_expiration(session_id: str):
    """
    Schedule the expiration of a session exactly 5 minutes after its creation.
    
    Args:
        session_id: The session identifier.
    """
    # Wait for 5 minutes (300 seconds) before expiring the session.
    await asyncio.sleep(300)
    await expire_session(session_id)

async def expire_session(session_id: str):
    """
    Expire a session by removing it from storage and cleaning up associated resources.
    
    Args:
        session_id: The session identifier.
    """
    # Remove the expired session from storage.
    llm_sessions.pop(session_id, None)

    # Expire any associated fetcher in fetcher_service.
    from services.fetcher_service import expire_fetcher
    expire_fetcher(session_id)

    # Expire any active websocket connections associated with session_id.
    from server.websockets import close_websocket_connection
    close_websocket_connection(session_id)