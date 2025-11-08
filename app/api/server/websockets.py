from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
import json
from typing import Literal, Optional
import asyncio

from services.prompts import (
    PR_DESCRIPTION_SYSTEM,
    SELECT_QUIRKY_REMARK_SYSTEM,
    SYSTEM,
    RELEASE_NOTES_SYSTEM,
    quirky_remarks,
)
from services.llm_service import (
    get_random_quirky_remarks,
    run_concurrent_tasks,
    get_llm,
)
from aicore.const import SPECIAL_TOKENS, STREAM_END_TOKEN

router = APIRouter()

# WebSocket connection storage
active_connections = {}
active_histories = {}

TRIGGER_PROMPT = """
Consider the following history of actionables from Git and return me the summary with N = '{N}' bullet points:

{ACTIONS}
"""

TRIGGER_RELEASE_PROMPT = """
Consider the following history of actionables from Git and the previous Release Notes (if available).
Generate me the next Release Notes based on the new Git Actionables matching the format of the previous releases:

{ACTIONS}
"""

TRIGGER_PULL_REQUEST_PROMPT = """
You will now receive a list of commit messages between two branches.
Using the system instructions provided above, generate a clear, concise, and professional **Pull Request Description** summarizing all changes from branch `{SRC}` to be merged into `{TARGET}`.

Commits:
{COMMITS}

Please follow these steps:
1. Read and analyze the commit messages.
2. Identify and group related changes under appropriate markdown headers (e.g., Features, Bug Fixes, Improvements, Documentation, Tests).
3. Write a short **summary paragraph** explaining the overall purpose of this pull request.
4. Format the final output as a complete markdown-formatted PR description, ready to paste into GitHub.

Begin your response directly with the formatted PR description—no extra commentary or explanation.
"""


@router.websocket("/ws/{session_id}/{action_type}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: Optional[str] = None,
    action_type: Literal["recap", "release", "pull_request"] = "recap"
):
    """
    WebSocket endpoint for real-time LLM operations.
    
    Handles three action types:
    - recap: Generate commit summaries with quirky remarks
    - release: Generate release notes based on git history
    - pull_request: Generate PR descriptions from commit diffs
    
    Args:
        websocket: WebSocket connection instance
        session_id: Session identifier for LLM and fetcher management
        action_type: Type of operation to perform
        
    Raises:
        HTTPException: If action_type is invalid
    """
    await websocket.accept()

    # Select appropriate system prompt based on action type
    if action_type == "recap":
        QUIRKY_SYSTEM = SELECT_QUIRKY_REMARK_SYSTEM.format(
            examples=json.dumps(get_random_quirky_remarks(quirky_remarks), indent=4)
        )
        system = [SYSTEM, QUIRKY_SYSTEM]
    elif action_type == "release":
        system = RELEASE_NOTES_SYSTEM
    elif action_type == "pull_request":
        system = PR_DESCRIPTION_SYSTEM
    else:
        raise HTTPException(status_code=404, detail="Invalid action type")

    # Store the active WebSocket connection
    active_connections[session_id] = websocket

    # Initialize LLM session
    llm = get_llm(session_id)

    try:
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            msg_json = json.loads(message)
            message_content = msg_json.get("actions")
            N = msg_json.get("n", 5)
            src_branch = msg_json.get("src")
            target_branch = msg_json.get("target")

            # Validate inputs
            assert int(N) <= 15, "N must be <= 15"
            assert message_content, "Message content is required"
            
            # Build history/prompt based on action type
            if action_type == "recap":
                history = [
                    TRIGGER_PROMPT.format(
                        N=N,
                        ACTIONS=message_content
                    )
                ]
            elif action_type == "release":
                history = [
                    TRIGGER_RELEASE_PROMPT.format(ACTIONS=message_content)
                ]
            elif action_type == "pull_request":
                history = [
                    TRIGGER_PULL_REQUEST_PROMPT.format(
                        SRC=src_branch,
                        TARGET=target_branch,
                        COMMITS=message_content)
                ]

            # Stream LLM response back to client
            response = []
            async for chunk in run_concurrent_tasks(
                llm,
                message=history,
                system_prompt=system
            ):
                if chunk == STREAM_END_TOKEN:
                    await websocket.send_text(json.dumps({"chunk": chunk}))
                    break
                elif chunk in SPECIAL_TOKENS:
                    continue
                await websocket.send_text(json.dumps({"chunk": chunk}))
                response.append(chunk)

            # Store response in history for potential follow-up
            history.append("".join(response))

    except WebSocketDisconnect:
        # Clean up connection on disconnect
        if session_id in active_connections:
            del active_connections[session_id]
    except AssertionError as e:
        # Handle validation errors
        if session_id in active_connections:
            await websocket.send_text(json.dumps({"error": f"Validation error: {str(e)}"}))
            del active_connections[session_id]
    except Exception as e:
        # Handle unexpected errors
        if session_id in active_connections:
            await websocket.send_text(json.dumps({"error": str(e)}))
            del active_connections[session_id]


def close_websocket_connection(session_id: str):
    """
    Clean up and close the active WebSocket connection associated with the given session_id.
    
    This function is called during session expiration to ensure proper cleanup
    of WebSocket resources.
    
    Args:
        session_id: The session identifier whose WebSocket connection should be closed
    """
    websocket = active_connections.pop(session_id, None)
    if websocket:
        asyncio.create_task(websocket.close())