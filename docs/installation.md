
# Installation Guide

## Prerequisites

- **Python 3.10+** (for backend)
- **Node.js 18+** (for frontend)
- **Docker** (optional, for containerized deployment)
- **Git** (for cloning the repository)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/BrunoV21/GitRecap.git
cd GitRecap
```

### 2. Backend Setup (FastAPI)

#### Create and activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install backend dependencies:

```bash
pip install -r requirements.txt
pip install -r app/api/requirements.txt
```

#### Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your credentials:
# - GitHub/GitLab/Azure PAT tokens
# - OAuth credentials
# - Rate limiting settings
```

#### Run the backend:

```bash
uvicorn app.api.main:app --reload
```

### 3. Frontend Setup (React + Vite)

#### Navigate to frontend directory:

```bash
cd app/git-recap
```

#### Install dependencies:

```bash
npm install
```

#### Configure frontend environment:

```bash
cp .env.example .env.local
# Edit .env.local with:
# - VITE_FRONTEND_HOST
# - VITE_GITHUB_CLIENT_ID
# - VITE_BACKEND_URL
```

#### Run the frontend:

```bash
npm run dev
```

## Production Deployment

### Option 1: Docker Compose

```bash
docker-compose -f app/api/docker-compose.yaml up --build
```

### Option 2: Manual Deployment

1. **Backend**:
   ```bash
   gunicorn -k uvicorn.workers.UvicornWorker app.api.main:app
   ```

2. **Frontend**:
   ```bash
   npm run build
   serve -s dist
   ```

## Environment Variables Reference

### Backend (.env)
```bash
VITE_FRONTEND_HOST= # Frontend origin for CORS
VITE_GITHUB_CLIENT_ID= # GitHub OAuth app ID
VITE_GITHUB_CLIENT_SECRET= # GitHub OAuth secret
RATE_LIMIT=30 # Requests per window
WINDOW_SECONDS=3 # Rate limit window
```

### Frontend (.env.local)
```bash
VITE_BACKEND_URL=http://localhost:8000
VITE_GITHUB_CLIENT_ID=your_client_id
VITE_FRONTEND_HOST=http://localhost:3000
```

## Troubleshooting

- **Python package conflicts**: Use `pip check` to verify dependencies
- **Frontend build errors**: Delete `node_modules` and reinstall
- **CORS issues**: Verify `VITE_FRONTEND_HOST` matches your frontend URL
- **Authentication problems**: Check token permissions and expiration