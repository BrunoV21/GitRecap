
# Contributing to Git Recap

We welcome contributions from the community! Whether you're fixing bugs, adding features, or improving documentation, your help is appreciated.

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 16+ (for frontend development)
- Docker (for containerized development)
- Git

### Development Setup

1. **Fork and clone** the repository:
   ```bash
   git clone https://github.com/<your-username>/git-recap.git
   cd git-recap
   ```

2. **Backend Setup**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   ```

3. **Frontend Setup**:
   ```bash
   cd app/git-recap
   npm install
   ```

4. **Environment Variables**:
   Create a `.env` file in the root directory with:
   ```
   GITHUB_CLIENT_ID=your_client_id
   GITHUB_CLIENT_SECRET=your_client_secret
   ```

## Development Workflow

1. **Branching**:
   - Create a new branch from `main`: `git checkout -b feat/your-feature-name`
   - Keep branches focused on a single feature/bugfix

2. **Making Changes**:
   - Follow existing code patterns
   - Include tests for new functionality
   - Update documentation when adding features

3. **Testing**:
   - Run backend tests:
     ```bash
     pytest tests/
     ```
   - Run frontend tests:
     ```bash
     cd app/git-recap
     npm test
     ```

4. **Commit Messages**:
   - Use present tense ("Add feature" not "Added feature")
   - Keep first line under 50 characters
   - Include detailed description when needed

5. **Pull Requests**:
   - Reference any related issues
   - Include a clear description of changes
   - Ensure all tests pass

## Code Style Guidelines

### Python
- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use type hints for all function signatures
- Include docstrings following Google style
- Keep lines under 88 characters

### JavaScript/TypeScript
- Follow the existing ESLint configuration
- Use functional components with hooks
- Prefer TypeScript over JavaScript

### Documentation
- Update relevant documentation files
- Add examples for new features
- Keep documentation in sync with code changes

## Need Help?

- Join our [Discord/Slack community]()
- Open a [GitHub Discussion]()
- Check the [FAQ](faq.md) for common questions

We appreciate your contributions! 🚀