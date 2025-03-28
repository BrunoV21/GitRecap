import argparse
from datetime import datetime, timedelta
from git_recap.providers.github_fetcher import GitHubFetcher
from git_recap.providers.azure_fetcher import AzureFetcher
from git_recap.providers.gitlab_fetcher import GitLabFetcher

def main():
    parser = argparse.ArgumentParser(
        description="Fetch user authored messages from repositories."
    )
    parser.add_argument(
        '--provider',
        required=True,
        choices=['github', 'azure', 'gitlab'],
        help='Platform name (github, azure, or gitlab)'
    )
    parser.add_argument('--pat', required=True, help='Personal Access Token')
    parser.add_argument(
        '--organization-url',
        help='Organization URL for Azure DevOps'
    )
    parser.add_argument(
        '--gitlab-url',
        help='GitLab URL (default: https://gitlab.com)'
    )
    parser.add_argument(
        '--start-date',
        type=lambda s: datetime.fromisoformat(s),
        default=(datetime.now() - timedelta(days=7)),
        help='Start date in ISO format (default: 7 days before now)'
    )
    parser.add_argument(
        '--end-date',
        type=lambda s: datetime.fromisoformat(s),
        default=datetime.now(),
        help='End date in ISO format (default: now)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Number of bullet points to return'
    )
    parser.add_argument(
        '--repos',
        nargs='*',
        help='Repository names to filter (leave empty for all)'
    )
    
    args = parser.parse_args()
    
    fetcher = None
    if args.provider == 'github':
        fetcher = GitHubFetcher(
            pat=args.pat,
            start_date=args.start_date,
            end_date=args.end_date,
            repo_filter=args.repos
        )
    elif args.provider == 'azure':
        if not args.organization_url:
            print("Organization URL is required for Azure DevOps")
            exit(1)
        fetcher = AzureFetcher(
            pat=args.pat,
            organization_url=args.organization_url,
            start_date=args.start_date,
            end_date=args.end_date,
            repo_filter=args.repos
        )
    elif args.provider == 'gitlab':
        gitlab_url = args.gitlab_url if args.gitlab_url else 'https://gitlab.com'
        fetcher = GitLabFetcher(
            pat=args.pat,
            url=gitlab_url,
            start_date=args.start_date,
            end_date=args.end_date,
            repo_filter=args.repos
        )
    
    messages = fetcher.get_authored_messages(limit=args.limit)
    for msg in messages:
        print(f"- {msg}")

if __name__ == '__main__':
    main()