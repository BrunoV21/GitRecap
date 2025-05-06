from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json
from typing import Optional
import logging
import asyncio
import ulid

from services.llm_service import initialize_llm_session, trim_messages, run_concurrent_tasks, get_llm
from aicore.const import SPECIAL_TOKENS, STREAM_END_TOKEN

router = APIRouter()

# WebSocket connection storage
active_connections = {}
active_histories = {}

logger = logging.getLogger(__name__)

TRIGGER_PROMPT = """
Consider the following history of actionables from Git and in return me the summary with N = '{N}' bullet points:

{ACTIONS}
"""

@router.websocket("/ws/{session_id}")
@router.websocket("/ws/test")  # Test-specific endpoint
async def websocket_endpoint(
    websocket: WebSocket, 
    session_id: Optional[str] = None
):
    await websocket.accept()
    
    # Store the connection
    if session_id is None:
        session_id = "test_session"  # Default session for testing
    
    active_connections[session_id] = websocket
    logger.info(f"New WebSocket connection established: {session_id}")

    try:
        # Initialize LLM
        llm = get_llm(session_id)

        while True:
            try:
                message = await websocket.receive_text()
                logger.debug(f"Received WebSocket message from {session_id}: {message[:200]}...")  # Log truncated message

                try:
                    msg_json = json.loads(message)
                    actions = msg_json.get("actions")
                    N = msg_json.get("n", 5)
                    
                    if not actions:
                        raise ValueError("Missing required field: actions")
                    if int(N) > 15:
                        raise ValueError("Parameter 'n' must be <= 15")
                    
                    history = [
                        TRIGGER_PROMPT.format(
                            N=N,
                            ACTIONS=actions
                        )
                    ]
                    
                    response = []
                    async for chunk in run_concurrent_tasks(llm, message=history):
                        if chunk == STREAM_END_TOKEN:
                            await websocket.send_text(json.dumps({"chunk": chunk}))
                            break
                        elif chunk in SPECIAL_TOKENS:
                            continue
                        
                        await websocket.send_text(json.dumps({"chunk": chunk}))
                        response.append(chunk)
                    
                    history.append("".join(response))
                    logger.debug(f"Completed processing for session {session_id}")
                
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON format: {str(e)}"
                    logger.warning(error_msg)
                    await websocket.send_text(json.dumps({"error": error_msg}))
                except ValueError as e:
                    error_msg = f"Validation error: {str(e)}"
                    logger.warning(error_msg)
                    await websocket.send_text(json.dumps({"error": error_msg}))
                except Exception as e:
                    error_msg = f"Processing error: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    await websocket.send_text(json.dumps({"error": error_msg}))
            
            except WebSocketDisconnect:
                raise  # Re-raise to be caught by outer handler
            except Exception as e:
                logger.error(f"Unexpected error in message loop: {str(e)}", exc_info=True)
                await websocket.send_text(json.dumps({"error": "Internal server error"}))
                break
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
        if session_id in active_connections:
            del active_connections[session_id]
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
        if session_id in active_connections:
            await websocket.send_text(json.dumps({"error": str(e)}))
            del active_connections[session_id]

def close_websocket_connection(session_id: str):
    """
    Clean up and close the active websocket connection associated with the given session_id.
    
    Args:
        session_id: The session identifier to close
    """
    websocket = active_connections.pop(session_id, None)
    if websocket:
        logger.info(f"Closing WebSocket connection for session {session_id}")
        asyncio.create_task(websocket.close())
