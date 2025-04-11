
# Installation Guide

## Prerequisites

- **Python 3.10+** (with pip)
- **Node.js 16+** (with npm)
- **Docker** (optional, for containerized deployment)
- **Git** (for cloning the repository)

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/git-recap.git
cd git-recap
```

### 2. Backend Setup (FastAPI)

#### Create and activate virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install dependencies:

```bash
pip install -r requirements.txt
```

#### Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your credentials:
# - GITHUB_CLIENT_ID
# - GITHUB_CLIENT_SECRET
# - GITHUB_PAT (optional)
# - GITLAB_TOKEN (optional)
# - AZURE_DEVOPS_TOKEN (optional)
```

#### Run the backend:

```bash
uvicorn app.api.main:app --reload
```

The API will be available at `http://localhost:8000`

### 3. Frontend Setup (React)

#### Navigate to frontend directory:

```bash
cd app/git-recap
```

#### Install dependencies:

```bash
npm install
```

#### Configure environment variables:

Create `.env` file with:
```env
VITE_API_URL=http://localhost:8000
```

#### Start development server:

```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Production Deployment

### Option 1: Docker Compose

```bash
docker-compose -f app/api/docker-compose.yaml up --build
```

### Option 2: Manual Deployment

1. Build frontend:
   ```bash
   cd app/git-recap
   npm run build
   ```

2. Run production backend:
   ```bash
   uvicorn app.api.main:app --host 0.0.0.0 --port 8000
   ```

## Configuration Options

| Environment Variable | Description | Required |
|----------------------|-------------|----------|
| `GITHUB_CLIENT_ID` | GitHub OAuth App Client ID | Yes |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App Client Secret | Yes |
| `GITHUB_PAT` | GitHub Personal Access Token | No |
| `GITLAB_TOKEN` | GitLab Personal Access Token | No |
| `AZURE_DEVOPS_TOKEN` | Azure DevOps Personal Access Token | No |
| `OPENAI_API_KEY` | OpenAI API Key (for LLM features) | No |

## Troubleshooting

- **Python package conflicts**: Use `pip check` to verify dependencies
- **Frontend not connecting**: Ensure `VITE_API_URL` matches your backend URL
- **Authentication issues**: Verify your OAuth credentials and callback URLs
- **Missing data**: Check your token permissions for each Git provider

For additional help, see our [FAQ](faq.md) or [GitHub App Guide](github-app.md).