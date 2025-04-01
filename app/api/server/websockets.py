from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json
from typing import Optional

from services.llm_service import initialize_llm_session, trim_messages, run_concurrent_tasks, get_llm
from aicore.const import SPECIAL_TOKENS, STREAM_END_TOKEN
import ulid

router = APIRouter()

# WebSocket connection storage
active_connections = {}
active_histories = {}

TRIGGER_PROMPT = """
Consider the following history of actionables from Git and in return me the summary with N = '{N}' bullet points:

{ACTIONS}
"""

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    session_id: Optional[str] = None
):
    await websocket.accept()
    
    # Store the connection
    active_connections[session_id] = websocket

    try:
        # Initialize LLM
        llm = get_llm(session_id)
        while True:
            message = await websocket.receive_text()
            msg_json = json.loads(message)
            message = msg_json.get("actions")
            N = msg_json.get("n", 5)
            assert int(N) <= 15
            assert message
            history = [
                TRIGGER_PROMPT.format(
                    N=N,
                    ACTIONS=message
                )
            ]
            response = []
            async for chunk in run_concurrent_tasks(
                llm,
                message=history
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