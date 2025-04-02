from security import validate_api_key
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip for OPTIONS requests
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Case-insensitive header access
        api_key = (
            request.headers.get("X-API-Key") or 
            request.headers.get("x-api-key") or
            request.headers.get("X-Api-Key")
        )
        
        if not api_key:
            raise HTTPException(
                status_code=401,
                detail="Missing API key header",
                headers={"WWW-Authenticate": "API-Key"}
            )
            
        if not validate_api_key(api_key):
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "API-Key"}
            )
            
        return await call_next(request)