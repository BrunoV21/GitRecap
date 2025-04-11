
# Backend Architecture

## Overview

The Git Recap backend is a FastAPI service that provides:
- REST API endpoints for authentication and data fetching
- WebSocket endpoint for real-time LLM responses
- Session management for LLM and fetcher instances
- Integration with multiple Git providers (GitHub, GitLab, Azure DevOps)

## Core Components

### Application Structure

```
app/api/
├── main.py            # FastAPI app initialization
├── middleware.py      # CORS and rate limiting
├── models/schemas.py  # Pydantic models
├── server/
│   ├── routes.py      # API endpoint definitions
│   └── websockets.py  # WebSocket handlers
└── services/
    ├── fetcher_service.py  # Git provider integration
    ├── llm_service.py      # LLM session management
    └── prompts.py         # System prompts
```

### Key Modules

#### `main.py`
- Initializes FastAPI application
- Configures middleware:
  - CORS (Cross-Origin Resource Sharing)
  - Rate limiting (100 requests/minute)
  - Authentication verification
- Mounts API routes

#### `routes.py`
```python
@router.get("/repos")
async def get_repositories(
    token: str = Depends(verify_token)
) -> List[Repository]:
    """List accessible repositories for authenticated user"""
```

#### `websockets.py`
```python
@router.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str
):
    """Handles real-time WebSocket communication"""
```

## Authentication

### Supported Methods
1. **GitHub OAuth**
   - Standard OAuth2 flow
   - Stores access token in encrypted session
2. **Personal Access Token (PAT)**
   - Direct token authentication
   - Limited to basic repository access

### Security Features
- JWT token validation
- Session expiration (5 minutes inactivity)
- Encrypted token storage
- Rate limiting

## API Reference

### REST Endpoints

| Endpoint          | Method | Description                          |
|-------------------|--------|--------------------------------------|
| `/external-signup`| POST   | GitHub OAuth callback                |
| `/pat`           | POST   | Personal Access Token authentication|
| `/repos`         | GET    | List accessible repositories         |
| `/actions`       | GET    | Fetch Git activity data              |

### WebSocket

```
/ws/{session_id}
```
- Establishes persistent connection
- Streams LLM responses in real-time
- Maintains conversation context

## Git Provider Integration

### Supported Providers
1. GitHub (`github_fetcher.py`)
2. GitLab (`gitlab_fetcher.py`)
3. Azure DevOps (`azure_fetcher.py`)

### Base Fetcher Interface
```python
class BaseFetcher(ABC):
    @abstractmethod
    def get_repositories(self) -> List[Repository]:
        pass
        
    @abstractmethod
    def get_actions(self, repo: str, since: datetime) -> List[Action]:
        pass
```

## Deployment

### Requirements
- Python 3.10+
- Redis (for session storage)
- Docker (optional)

### Environment Variables
```bash
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_secret
JWT_SECRET_KEY=your_jwt_secret
REDIS_URL=redis://localhost:6379
```

## Performance Considerations
- Cached repository lists (TTL: 1 hour)
- Batched action fetching
- Connection pooling for Git providers
- Async I/O for all network operations