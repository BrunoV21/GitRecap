from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from typing import Optional
import asyncio
from services.llm_service import run_concurrent_tasks, get_llm
from aicore.const import SPECIAL_TOKENS, STREAM_END_TOKEN

router = APIRouter()

# WebSocket connection storage
active_connections = {}

TRIGGER_PROMPT = """
Consider the following history of actionables from Git and in return me the summary with N = '{N}' bullet points:

{ACTIONS}
"""

RELEASE_NOTES_PROMPT = """
Given the following list of commit messages and metadata, generate a structured release notes document suitable for end users and developers. Group related changes, highlight breaking changes, and use clear section headers. Do not include dates unless specifically requested. Be concise and professional.

{COMMITS}
"""

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: Optional[str] = None
):
    await websocket.accept()
    active_connections[session_id] = websocket
    llm = get_llm(session_id)
    try:
        while True:
            message = await websocket.receive_text()
            msg_json = json.loads(message)
            # Determine if this is a release notes request
            if msg_json.get("type") == "release_notes":
                commits_txt = msg_json.get("commits")
                assert commits_txt
                prompt = RELEASE_NOTES_PROMPT.format(COMMITS=commits_txt)
                response = []
                async for chunk in run_concurrent_tasks(
                    llm,
                    message=[prompt]
                ):
                    if chunk == STREAM_END_TOKEN:
                        await websocket.send_text(json.dumps({"chunk": chunk}))
                        break
                    elif chunk in SPECIAL_TOKENS:
                        continue
                    await websocket.send_text(json.dumps({"chunk": chunk}))
                    response.append(chunk)
            else:
                actions = msg_json.get("actions")
                N = msg_json.get("n", 5)
                assert int(N) <= 15
                assert actions
                history = [
                    TRIGGER_PROMPT.format(
                        N=N,
                        ACTIONS=actions
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