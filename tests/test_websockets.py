import pytest
from fastapi.testclient import TestClient
from websockets import connect
import json
import asyncio
from unittest.mock import patch, MagicMock

from app.api.main import app
from app.api.server.websockets import router as websocket_router
from app.api.services.llm_service import simulate_llm_response

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_llm_service():
    with patch('app.api.server.websockets.get_llm') as mock_get_llm, \
         patch('app.api.server.websockets.run_concurrent_tasks') as mock_run_tasks:
        
        # Setup mock LLM
        mock_llm = MagicMock()
        mock_get_llm.return_value = mock_llm
        
        # Setup mock task generator
        async def mock_task_generator(*args, **kwargs):
            for chunk in simulate_llm_response("test"):
                yield chunk
            yield "STREAM_END_TOKEN"
        
        mock_run_tasks.return_value = mock_task_generator("test")
        yield

@pytest.mark.asyncio
async def test_websocket_connection():
    """Test basic WebSocket connection establishment."""
    async with connect("ws://testserver/ws/test_session") as websocket:
        assert websocket.open

@pytest.mark.asyncio
async def test_websocket_message_exchange(mock_llm_service):
    """Test message sending/receiving through WebSocket."""
    async with connect("ws://testserver/ws/test_session") as websocket:
        test_message = json.dumps({"actions": "test", "n": 5})
        await websocket.send(test_message)
        
        # Verify we receive multiple chunks and a final end token
        chunks = []
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("chunk") == "STREAM_END_TOKEN":
                break
            chunks.append(data["chunk"])
        
        assert len(chunks) > 0
        assert "".join(chunks).startswith("This is a simulated response")

@pytest.mark.asyncio
async def test_websocket_error_handling():
    """Test error scenarios with invalid WebSocket connections."""
    with pytest.raises(Exception):
        async with connect("ws://testserver/ws/invalid_session"):
            pass

@pytest.mark.asyncio
async def test_multiple_connections(mock_llm_service):
    """Test concurrent WebSocket connections."""
    async def connect_client():
        async with connect("ws://testserver/ws/test_session") as ws:
            await ws.send(json.dumps({"actions": "test", "n": 5}))
            chunks = []
            while True:
                response = await ws.recv()
                data = json.loads(response)
                if data.get("chunk") == "STREAM_END_TOKEN":
                    break
                chunks.append(data["chunk"])
            return chunks

    results = await asyncio.gather(*[connect_client() for _ in range(3)])
    assert len(results) == 3
    for chunks in results:
        assert len(chunks) > 0

@pytest.mark.asyncio
async def test_malformed_message(mock_llm_service):
    """Test handling of malformed WebSocket messages."""
    async with connect("ws://testserver/ws/test_session") as websocket:
        # Send invalid JSON
        await websocket.send("not valid json")
        response = await websocket.recv()
        assert "error" in json.loads(response)

        # Send missing required fields
        await websocket.send(json.dumps({"wrong": "format"}))
        response = await websocket.recv()
        assert "error" in json.loads(response)

@pytest.mark.asyncio
async def test_connection_cleanup():
    """Test that connections are properly cleaned up on disconnect."""
    async with connect("ws://testserver/ws/test_session") as websocket:
        assert websocket.open
    
    # Connection should be removed from active_connections after closing
    assert "test_session" not in websocket_router.active_connections

@pytest.mark.asyncio
async def test_max_n_validation(mock_llm_service):
    """Test validation of maximum 'n' parameter."""
    async with connect("ws://testserver/ws/test_session") as websocket:
        # Send n > 15 which should be rejected
        await websocket.send(json.dumps({"actions": "test", "n": 20}))
        response = await websocket.recv()
        assert "error" in json.loads(response)
