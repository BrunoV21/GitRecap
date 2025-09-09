from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
import json
from typing import Optional

from services.prompts import SELECT_QUIRKY_REMARK_SYSTEM, SYSTEM, RELEASE_NOTES_SYSTEM, quirky_remarks
from services.llm_service import get_random_quirky_remarks, run_concurrent_tasks, get_llm
from aicore.const import SPECIAL_TOKENS, STREAM_END_TOKEN
import asyncio

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


@router.websocket("/ws/{session_id}/{action_type}")
async def websocket_endpoint(
    websocket: WebSocket, 
    session_id: Optional[str] = None,
    action_type: str="recap"
):
    await websocket.accept()

    if action_type == "recap":
        QUIRKY_SYSTEM = SELECT_QUIRKY_REMARK_SYSTEM.format(
            examples=json.dumps(get_random_quirky_remarks(quirky_remarks), indent=4)
        )
        
        system = [SYSTEM, QUIRKY_SYSTEM]

    elif action_type == "release":
        system = RELEASE_NOTES_SYSTEM

    else:
        raise HTTPException(status_code=404)
    
    # Store the connection
    active_connections[session_id] = websocket

    # Initialize LLM
    llm = get_llm(session_id)

    try:
        while True:
            message = await websocket.receive_text()
            msg_json = json.loads(message)
            message = msg_json.get("actions")
            N = msg_json.get("n", 5)
            assert int(N) <= 15
            assert message
            if action_type == "recap":
                history = [
                    TRIGGER_PROMPT.format(
                        N=N,
                        ACTIONS=message
                    )
                ]
            elif action_type == "release":
                history = [
                    TRIGGER_RELEASE_PROMPT.format(ACTIONS=message)
                ]

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
            
            history.append("".join(response))
    
    except WebSocketDisconnect:
        if session_id in active_connections:
            del active_connections[session_id]
    except Exception as e:
        if session_id in active_connections:
            await websocket.send_text(json.dumps({"error": str(e)}))
            del active_connections[session_id]

def close_websocket_connection(session_id: str):
    """
    Clean up and close the active websocket connection associated with the given session_id.
    """
    websocket = active_connections.pop(session_id, None)
    if websocket:
        asyncio.create_task(websocket.close())
