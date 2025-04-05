from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routes import router as api_router
from services.llm_service import simulate_llm_response
from server.websockets import router as websocket_router
import os

# Initialize FastAPI app
app = FastAPI(title="LLM Service API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST", "OPTIONS"]
)

# Include routers
app.include_router(api_router)
app.include_router(websocket_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/health2")
async def stream_health_check():
    response = simulate_llm_response("health")
    return {"response": " ".join(response)}

if __name__ == "__main__":
    from dotenv import load_dotenv
    import uvicorn
    load_dotenv()
    uvicorn.run(app, host="0.0.0.0", port=8000)
