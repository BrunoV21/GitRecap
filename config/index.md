
# Configuration Guide

## Environment Setup

1. First, ensure you have cloned the repository:
```bash
git clone ${AiCore_GitHub:-https://github.com/yourusername/git_recap.git}
cd git_recap
```

2. Copy the environment example file to create your local configuration:
```bash
cp ${AiCore_GitHub:-.}/.env-example .env
```

3. Edit the `.env` file to set your specific configuration values. Key variables include:
- `GITHUB_PAT`: Your GitHub Personal Access Token
- `AZURE_PAT`: Your Azure DevOps Personal Access Token
- `GITLAB_PAT`: Your GitLab Personal Access Token
- `GITLAB_URL`: Your GitLab instance URL (if self-hosted)

## Configuration Files

- Main configuration: [`${AiCore_GitHub:-.}/config.mts`](./config.mts)
- Environment template: [`${AiCore_GitHub:-.}/.env-example`](./.env-example)
- Requirements: [`${AiCore_GitHub:-.}/requirements.txt`](./requirements.txt)

## Documentation

For more details, see:
- [Installation Guide](${AiCore_GitHub:-.}/docs/installation.md)
- [API Documentation](${AiCore_GitHub:-.}/docs/backend.md)
- [FAQ](${AiCore_GitHub:-.}/docs/faq.md)

## Troubleshooting

If you encounter issues:
1. Verify all environment variables are set correctly
2. Check the [troubleshooting section](${AiCore_GitHub:-.}/docs/faq.md#troubleshooting) in the FAQ
3. Review the [contributing guidelines](${AiCore_GitHub:-.}/docs/contributing.md) for reporting issues