
# Frequently Asked Questions

## General

### What is Git Recap?
Git Recap is a developer productivity tool that aggregates and summarizes your Git activity across multiple platforms (GitHub, GitLab, Azure DevOps) into concise, actionable insights.

### How does it work?
It fetches your commits, pull requests, and issues from connected repositories, then uses LLMs to generate smart summaries of your work.

## Authentication

### What authentication methods are supported?
- GitHub OAuth (recommended)
- Personal Access Tokens (PATs)

### Why can't I see my private repositories?
For private repo access, you need to:
1. Install the GitHub App from Marketplace, or
2. Authenticate with a PAT that has the required permissions

## Troubleshooting

### Common Issues

#### "Repository not found"
- Ensure the app is installed from GitHub Marketplace
- Check your PAT has proper repository access

#### "No actions found"
- Verify your date range includes recent activity
- Check your repository/author filters

#### "Authentication failed"
- Reauthorize the app
- Try using a fresh PAT

## Technical

### How long is my session data stored?
Session data expires after 5 minutes of inactivity for security.

### Can I self-host Git Recap?
Yes! See our [Installation Guide](installation.md) for setup instructions.

### How do I contribute to Git Recap?
Check out our [Contributing Guide](contributing.md) for development setup and guidelines.

### What Git providers are supported?
Currently supported providers:
- GitHub
- GitLab
- Azure DevOps

### Is there a rate limit?
Yes, the API has rate limiting to prevent abuse. Contact us if you need higher limits.