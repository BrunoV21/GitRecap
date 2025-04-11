
# Frequently Asked Questions

## General

### What is Git Recap?
Git Recap is a developer productivity tool that aggregates and summarizes your Git activity across multiple platforms (GitHub, GitLab, Azure DevOps) into a concise, actionable format. It fetches commit messages, pull requests, and issues, then consolidates them into a chronological summary.

### Which Git providers are supported?
Currently supported providers:
- GitHub (via PyGitHub)
- GitLab (via python-gitlab)
- Azure DevOps (via azure-devops Python API)

### Is there a hosted version available?
Yes! You can use the GitHub App version from the Marketplace, or run your own instance using the open-source code.

## Authentication

### How do I authenticate with Git Recap?
You have several options:
1. **GitHub App**: Install from Marketplace (recommended)
2. **Personal Access Token (PAT)**: Generate a token with proper permissions
3. **OAuth**: Coming soon!

### What permissions does the GitHub App require?
The app requires:
- Read access to repositories
- Read access to pull requests
- Read access to issues

### How do I generate a PAT for each provider?
1. **GitHub**: 
   - Go to Settings > Developer settings > Personal access tokens
   - Select `repo` scope
2. **GitLab**: 
   - User Settings > Access Tokens
   - Select `read_repository` scope
3. **Azure DevOps**: 
   - User settings > Personal access tokens
   - Select "Code (read)" scope

## Usage

### How do I filter by date?
Use the `--start-date` and `--end-date` parameters in ISO format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS). Dates without timezone info are automatically converted to UTC.

### Can I filter by specific authors?
Yes! Use the `--authors` parameter followed by the usernames you want to include. By default, it uses the authenticated user.

### What's the output format?
The tool outputs:
1. JSON format with all raw events
2. A plain text summary grouped by day (ideal for LLM context)

## Troubleshooting

### "Session not found" error
This typically means:
- Your session expired (sessions last 5 minutes)
- The WebSocket connection was interrupted
Solution: Try re-authenticating.

### "Too Many Requests" error
The API has rate limiting enabled to prevent abuse. Wait a few seconds and try again.

### WebSocket connection issues
1. Check your internet connection
2. Ensure your firewall isn't blocking WebSocket connections (port 443)
3. Try refreshing the page
4. Check browser console for errors

### Missing repositories in the list
Possible causes:
- The app hasn't been installed on the target organization
- PAT doesn't have proper repo permissions
- Repository is archived
Solutions:
- For GitHub: Check Marketplace installation status
- Regenerate PAT with correct permissions
- Ensure repos are active

## Advanced

### Can I extend Git Recap with new providers?
Yes! The architecture is modular. Create a new class inheriting from `BaseFetcher` in the providers directory.

### How do I contribute?
See our [Contributing Guide](./contributing.md) for setup instructions and coding standards.

### Where can I report bugs?
Please open an issue on our GitHub repository with:
1. Steps to reproduce
2. Expected behavior
3. Actual behavior
4. Screenshots if applicable

## Performance

### Why is it slow for large repositories?
Fetching history for large repos takes time. Consider:
1. Narrowing the date range
2. Using more specific filters
3. Running during off-peak hours

### Does it cache results?
Currently no, but caching is planned for a future release.