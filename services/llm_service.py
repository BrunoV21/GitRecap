"""
LLM service utilities for managing language model instances and message processing.

This module provides core functionality for:
- Creating and managing LLM sessions
- Trimming message history to fit within token limits
- Streaming LLM responses
- Generating quirky remarks for engaging user interactions
"""

import os
import random
import asyncio
from typing import List, Dict, Any, Optional, Tuple, AsyncGenerator
from datetime import datetime, timedelta
import ulid
import logging

from aicore.llm.config import LlmConfig
from aicore.llm import LLM
from aicore.const import STREAM_END_TOKEN

logger = logging.getLogger(__name__)

# In-memory store mapping session_id to LLM instance
llm_instances: Dict[str, LLM] = {}

# Session expiration tracking
session_expiration_tasks: Dict[str, asyncio.Task] = {}

# Default configuration
MAX_HISTORY_TOKENS = int(os.getenv("MAX_HISTORY_TOKENS", "16000"))
SESSION_EXPIRATION_MINUTES = 5


async def set_llm(config: Optional[LlmConfig] = None) -> str:
    """
    Create a new LLM session with custom configuration.
    
    Args:
        config: Optional LLM configuration. If None, uses default configuration.
        
    Returns:
        str: Generated session ID for the new LLM instance.
        
    Raises:
        Exception: If LLM initialization fails.
    """
    try:
        session_id = ulid.ulid()
        
        if config is None:
            config = LlmConfig()
        
        llm_instances[session_id] = LLM(config)
        
        # Schedule session expiration
        schedule_session_expiration(session_id)
        
        logger.info(f"Created LLM session: {session_id}")
        return session_id
    except Exception as e:
        logger.error(f"Failed to create LLM session: {str(e)}")
        raise Exception(f"Failed to initialize LLM: {str(e)}")


def get_llm(session_id: str) -> LLM:
    """
    Retrieve the LLM instance for the provided session_id.
    
    Args:
        session_id: The session identifier.
    
    Returns:
        LLM: The LLM instance associated with the session_id.
    
    Raises:
        ValueError: If no LLM instance is found for the given session_id.
    """
    llm = llm_instances.get(session_id)
    if not llm:
        logger.error(f"LLM session not found: {session_id}")
        raise ValueError(f"LLM session not found: {session_id}")
    return llm


def trim_messages(
    messages: List[Dict[str, Any]], 
    tokenizer_fn: callable, 
    max_tokens: int = MAX_HISTORY_TOKENS
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Trim message history to fit within token limits by removing oldest messages.
    
    This function ensures the message history stays within the specified token limit
    by iteratively removing the oldest messages until the total token count is acceptable.
    
    Args:
        messages: List of message dictionaries to trim.
        tokenizer_fn: Function to count tokens in a message.
        max_tokens: Maximum allowed tokens (default: MAX_HISTORY_TOKENS).
    
    Returns:
        Tuple[List[Dict[str, Any]], bool]: A tuple containing:
            - The trimmed list of messages
            - A boolean indicating whether any trimming occurred (True if messages were removed)
    
    Example:
        >>> messages = [{"message": "old"}, {"message": "new"}]
        >>> trimmed, was_trimmed = trim_messages(messages, tokenizer, 1000)
        >>> if was_trimmed:
        ...     print("Messages were trimmed due to token limits")
    """
    if not messages:
        return messages, False
    
    original_length = len(messages)
    
    # Calculate total tokens
    total_tokens = sum(tokenizer_fn(msg.get("message", "")) for msg in messages)
    
    # If within limits, return original messages
    if total_tokens <= max_tokens:
        logger.debug(f"Messages within token limit: {total_tokens}/{max_tokens} tokens")
        return messages, False
    
    logger.info(f"Trimming messages: {total_tokens} tokens exceeds limit of {max_tokens}")
    
    # Remove oldest messages until within limit
    trimmed_messages = messages.copy()
    while total_tokens > max_tokens and len(trimmed_messages) > 1:
        removed_message = trimmed_messages.pop(0)
        removed_tokens = tokenizer_fn(removed_message.get("message", ""))
        total_tokens -= removed_tokens
        logger.debug(f"Removed message with {removed_tokens} tokens. Remaining: {total_tokens} tokens")
    
    was_trimmed = len(trimmed_messages) < original_length
    
    if was_trimmed:
        logger.info(f"Trimmed {original_length - len(trimmed_messages)} messages. Final count: {len(trimmed_messages)}")
    
    return trimmed_messages, was_trimmed


async def run_concurrent_tasks(
    llm: LLM,
    message: List[str],
    system_prompt: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Stream LLM responses chunk by chunk.
    
    This function handles the streaming of LLM-generated content, yielding
    individual chunks as they become available.
    
    Args:
        llm: The LLM instance to use for generation.
        message: List of message strings to send to the LLM.
        system_prompt: Optional system prompt to guide the LLM's behavior.
    
    Yields:
        str: Individual chunks of the LLM response, followed by STREAM_END_TOKEN.
    
    Example:
        >>> async for chunk in run_concurrent_tasks(llm, ["Hello"], "You are helpful"):
        ...     if chunk == STREAM_END_TOKEN:
        ...         break
        ...     print(chunk, end="")
    """
    try:
        logger.debug(f"Starting LLM streaming with {len(message)} messages")
        
        async for chunk in llm.stream(
            messages=message,
            system_prompt=system_prompt
        ):
            yield chunk
        
        yield STREAM_END_TOKEN
        logger.debug("LLM streaming completed")
        
    except Exception as e:
        logger.error(f"Error during LLM streaming: {str(e)}")
        yield f"Error: {str(e)}"
        yield STREAM_END_TOKEN


def get_random_quirky_remarks(remarks_list: List[str], n: int = 10) -> List[str]:
    """
    Select random quirky remarks for engaging LLM responses.
    
    Args:
        remarks_list: List of available quirky remarks.
        n: Number of remarks to select (default: 10).
    
    Returns:
        List[str]: Randomly selected quirky remarks.
    
    Example:
        >>> remarks = ["Remark 1", "Remark 2", "Remark 3"]
        >>> selected = get_random_quirky_remarks(remarks, 2)
        >>> len(selected)
        2
    """
    if not remarks_list:
        logger.warning("Empty remarks list provided")
        return []
    
    n = min(n, len(remarks_list))
    selected = random.sample(remarks_list, n)
    logger.debug(f"Selected {n} quirky remarks")
    return selected


def schedule_session_expiration(session_id: str) -> None:
    """
    Schedule automatic session cleanup after expiration time.
    
    This function creates an asyncio task that will expire the session
    after SESSION_EXPIRATION_MINUTES minutes of inactivity.
    
    Args:
        session_id: The session identifier to schedule for expiration.
    """
    async def expire_after_delay():
        await asyncio.sleep(SESSION_EXPIRATION_MINUTES * 60)
        expire_session(session_id)
    
    # Cancel existing expiration task if present
    if session_id in session_expiration_tasks:
        session_expiration_tasks[session_id].cancel()
    
    # Schedule new expiration task
    task = asyncio.create_task(expire_after_delay())
    session_expiration_tasks[session_id] = task
    
    logger.info(f"Scheduled session expiration for {session_id} in {SESSION_EXPIRATION_MINUTES} minutes")


def expire_session(session_id: str) -> None:
    """
    Remove the LLM instance and associated resources for the given session_id.
    
    This function is called during session expiration to clean up resources
    including the LLM instance, fetcher, and WebSocket connections.
    
    Args:
        session_id: The session identifier whose resources should be removed.
    """
    from services.fetcher_service import expire_fetcher
    from server.websockets import close_websocket_connection
    
    # Remove LLM instance
    llm = llm_instances.pop(session_id, None)
    if llm:
        logger.info(f"Expired LLM session: {session_id}")
    
    # Remove expiration task
    task = session_expiration_tasks.pop(session_id, None)
    if task and not task.done():
        task.cancel()
    
    # Clean up fetcher
    try:
        expire_fetcher(session_id)
    except Exception as e:
        logger.warning(f"Error expiring fetcher for session {session_id}: {str(e)}")
    
    # Close WebSocket connection
    try:
        close_websocket_connection(session_id)
    except Exception as e:
        logger.warning(f"Error closing WebSocket for session {session_id}: {str(e)}")


def simulate_llm_response(prompt: str) -> List[str]:
    """
    Simulate an LLM response for testing purposes.
    
    This function provides a simple mock response for health checks
    and testing without requiring a full LLM initialization.
    
    Args:
        prompt: The input prompt (not used in simulation).
    
    Returns:
        List[str]: A simulated response as a list of words.
    
    Example:
        >>> response = simulate_llm_response("test")
        >>> " ".join(response)
        'This is a simulated LLM response for testing purposes.'
    """
    return ["This", "is", "a", "simulated", "LLM", "response", "for", "testing", "purposes."]