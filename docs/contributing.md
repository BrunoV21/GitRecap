
# Contributing to Git Recap

Thank you for considering contributing to Git Recap! We welcome all forms of contributions, including bug reports, feature requests, documentation improvements, and code contributions.

## Getting Started

### Prerequisites
- Python 3.10+ (for backend development)
- Node.js 18+ (for frontend development)
- Docker (optional, for containerized development)
- Git

### Development Setup

1. **Fork and clone** the repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/git-recap.git
   cd git-recap
   ```

2. **Set up backend**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Set up frontend** (if working on UI):
   ```bash
   cd app/git-recap
   npm install
   ```

4. **Run the development environment**:
   - Backend:
     ```bash
     uvicorn app.api.main:app --reload
     ```
   - Frontend:
     ```bash
     npm run dev
     ```

## Contribution Workflow

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feat/your-feature-name
   ```

2. **Make your changes** following the existing code style:
   - Python: Follow PEP 8 guidelines
   - TypeScript: Use strict typing and React best practices
   - Document new features with docstrings/markdown

3. **Write tests** for new functionality:
   - Backend: Add pytest tests in `tests/` directory
   - Frontend: Add Jest/React Testing Library tests

4. **Commit your changes** with descriptive messages:
   ```bash
   git commit -m "feat: add new provider integration"
   ```

5. **Push your branch** and open a Pull Request:
   ```bash
   git push origin feat/your-feature-name
   ```

## Key Areas for Contribution

### High Priority Areas
- **New Git Providers**: Add support for additional version control platforms
- **Performance Improvements**: Optimize API calls and data processing
- **UI Enhancements**: Improve the user experience and visual design

### Other Contribution Opportunities
- **Documentation**: Improve guides, examples, and API references
- **Testing**: Increase test coverage and add integration tests
- **Bug Fixes**: Check the issue tracker for known issues

## Code Standards

### Python (Backend)
- Follow PEP 8 style guide
- Use type hints for all function signatures
- Keep functions small and focused
- Document public APIs with docstrings
- Use FastAPI best practices for endpoints

### TypeScript (Frontend)
- Use strict TypeScript typing
- Follow React hooks best practices
- Keep components small and reusable
- Use functional components with hooks
- Follow the existing UI component patterns

## Testing Requirements
- All new features must include tests
- Bug fixes should include regression tests
- Maintain at least 80% test coverage
- Run tests before submitting PR:
  ```bash
  pytest  # Backend tests
  npm test  # Frontend tests
  ```

## Pull Request Guidelines
- Keep PRs focused on a single feature/bugfix
- Include a clear description of changes
- Reference related issues
- Ensure all tests pass
- Update documentation if needed

## Community
- Join our [Discord/Slack channel] for discussions
- Be respectful and inclusive in all communications
- Follow the [Code of Conduct](CODE_OF_CONDUCT.md)

We appreciate your contributions and look forward to collaborating with you!