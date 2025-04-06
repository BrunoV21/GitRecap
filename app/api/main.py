from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.routes import router as api_router
from services.llm_service import simulate_llm_response
from server.websockets import router as websocket_router
from midleware import OriginAndRateLimitMiddleware, ALLOWED_ORIGIN

# Initialize FastAPI app
app = FastAPI(title="LLM Service API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGIN,
    allow_methods=["GET", "POST", "OPTIONS"]
)
# app.add_middleware(
#     OriginAndRateLimitMiddleware
# )

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
    uvicorn.run(app, host="0.0.0.0", port=7860)
