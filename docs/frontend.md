
# Frontend Architecture

The Git Recap frontend is a React application built with Vite, featuring a pixel-retro UI design and real-time WebSocket communication with the backend.

## Project Structure

```
app/git-recap/
├── src/
│   ├── App.tsx            # Main application component
│   ├── App.css            # Main component styles
│   ├── main.tsx           # Application entry point
│   ├── index.css          # Global styles
│   ├── assets/            # Static assets (images, fonts)
│   ├── components/        # Reusable UI components
│   │   ├── AuthButton.tsx # Authentication component
│   │   ├── RepoSelector.tsx # Repository selection
│   │   ├── SummaryView.tsx  # LLM summary display
│   │   └── Loading.tsx    # Loading indicators
│   ├── hooks/             # Custom React hooks
│   │   ├── useAuth.ts     # Authentication logic
│   │   └── useWebSocket.ts # WebSocket management
│   └── types/             # TypeScript type definitions
├── public/                # Static public files
├── package.json           # Project dependencies
├── tsconfig.json          # TypeScript configuration
└── vite.config.ts         # Vite configuration
```

## Key Features

### Authentication Flow
- GitHub OAuth integration via `/auth/github` endpoint
- Personal Access Token (PAT) fallback option
- Session management with JWT tokens
- Automatic token refresh handling

### Repository Selection
- Dynamic loading of available repositories from connected providers
- Multi-select interface with search functionality
- Visual indicators for private/public repositories
- Caching of repository lists for performance

### Activity Summary
- WebSocket connection to `/ws` endpoint for real-time updates
- Configurable summary length options (5/10/15 points)
- Animated loading states during LLM processing
- Copy-to-clipboard functionality for generated summaries

### UI Components
- Pixel-art styled buttons and controls
- Retro terminal-like output display
- Responsive layout for desktop and mobile
- Dark/light theme support

## Technical Stack

### Core Dependencies
- React 18 with TypeScript
- Vite for development/build tooling
- WebSocket API for real-time communication
- react-markdown for formatted output display
- pixel-retroui for UI components

### Development Tools
- ESLint + Prettier for code quality
- Vitest for unit testing
- Storybook for component development (optional)
- Docker for containerized development

## Environment Variables

Required frontend environment variables:

```env
VITE_API_BASE_URL=http://localhost:8000  # Backend API base URL
VITE_WS_BASE_URL=ws://localhost:8000    # WebSocket base URL
VITE_GITHUB_CLIENT_ID=your_client_id    # GitHub OAuth client ID
```

## Development Setup

1. Install dependencies:
   ```bash
   cd app/git-recap
   npm install
   ```

2. Start development server:
   ```bash
   npm run dev
   ```

3. Run tests:
   ```bash
   npm test
   ```

## Production Build

To create an optimized production build:
```bash
npm run build
```

The output will be in the `dist/` directory, ready for deployment.

## Known Limitations

- WebSocket connections may drop on unstable networks
- Large repository lists may impact performance
- Mobile experience needs further optimization