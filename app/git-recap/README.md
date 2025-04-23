
# GitRecap Frontend

GitRecap is a web application that helps developers track and summarize their Git activity across multiple platforms in an engaging way.

## Features

- **Multi-Platform Support**: Connect to GitHub, GitLab, and Azure DevOps repositories
- **Interactive Timeline**: Filter commits, PRs, and issues by date range
- **Smart Summarization**: Get concise, engaging recaps of your activity
- **Real-time Updates**: WebSocket integration for live progress updates
- **Authentication Options**: GitHub OAuth or Personal Access Token (PAT) support
- **Repository Filtering**: Select specific repositories to include in your recap

## Components

### Frontend
- Built with **React** + **TypeScript** using **Vite** for fast development
- **pixel-retroui** component library for consistent styling
- GitHub OAuth integration for seamless authentication
- Real-time WebSocket connection to backend
- Responsive design that works on desktop and mobile

### Backend
- **FastAPI** server with WebSocket support
- Authentication middleware (CORS, rate limiting)
- Services for LLM integration and Git data fetching
- Docker deployment configuration

## Development Setup

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the development server:
```bash
npm run dev
```

## Production Build

```bash
npm run build
```

## Deployment

The application can be deployed to any static hosting service:
```bash
npm run build
# Deploy the contents of the dist/ folder
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| VITE_AICORE_API | Backend API URL |
| VITE_GITHUB_CLIENT_ID | GitHub OAuth client ID |
| VITE_REDIRECT_URI | OAuth redirect URI |
| VITE_LLM_MODEL | Name of the LLM model being used |

## Project Structure

```
app/git-recap/
├── src/
│   ├── App.tsx        # Main application component
│   ├── main.tsx       # Application entry point
│   ├── App.css        # Global styles
│   ├── index.css      # Base styles
│   └── vite-env.d.ts  # TypeScript declarations
├── public/            # Static assets
├── index.html         # Main HTML file
├── package.json       # Project dependencies
└── tsconfig.json      # TypeScript configuration
```

## Dependencies

- React 19
- TypeScript
- Vite
- pixel-retroui UI library
- Lucide React icons
- react-markdown

## License

This project is licensed under the [MIT License](LICENSE).