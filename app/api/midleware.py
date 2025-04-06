import os
import time
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict

ALLOWED_ORIGIN = ["https://mclovinittt-gitrecap.hf.space"] 
ALLOWED_ORIGIN.append(os.getenv("VITE_FRONTEND_HOST")) if os.getenv("VITE_FRONTEND_HOST") else ...
RATE_LIMIT = int(os.getenv("RATE_LIMIT", "30"))  # Max requests
WINDOW_SECONDS = int(os.getenv("WINDOW_SECONDS", "3"))  # Time window (e.g., 5 reqs per 60s)

# Store timestamps of requests per IP or origin
request_logs = defaultdict(list)


class OriginAndRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")

        if origin not in ALLOWED_ORIGIN:
            raise HTTPException(status_code=403, detail="Forbidden: origin not allowed")

        # --- Rate limiting logic ---
        client_ip = request.client.host
        now = time.time()

        # Remove timestamps older than the window
        request_logs[client_ip] = [
            t for t in request_logs[client_ip] if now - t < WINDOW_SECONDS
        ]

        if len(request_logs[client_ip]) >= RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Too Many Requests")

        request_logs[client_ip].append(now)
        return await call_next(request)