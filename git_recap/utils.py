from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

def parse_entries_to_txt(entries: List[Dict[str, Any]]) -> str:
    """
    Groups entries by day (YYYY-MM-DD) and produces a plain text summary.
    
    Each day's header is the date string, followed by bullet points that list:
      - type (commit, commit_from_pr, pull_request, issue)
      - repo name
      - message text
      - for pull requests: PR number or for commits from PR: pr_title
    """
    # Group entries by date (YYYY-MM-DD)
    grouped = defaultdict(list)
    for entry in entries:
        ts = entry.get("timestamp")
        # Convert timestamp to a datetime object if necessary
        if isinstance(ts, str):
            dt = datetime.fromisoformat(ts)
        else:
            dt = ts
        day = dt.strftime("%Y-%m-%d")
        grouped[day].append(entry)
    
    # Sort the days chronologically
    sorted_days = sorted(grouped.keys())
    
    # Build the output text
    lines = []
    for day in sorted_days:
        lines.append(day + ":")
        # Optionally, sort the entries for that day if needed (e.g., by timestamp)
        day_entries = sorted(grouped[day], key=lambda x: x["timestamp"])
        for entry in day_entries:
            typ = entry.get("type", "N/A")
            repo = entry.get("repo", "N/A")
            message = entry.get("message", "").strip()
            # Build extra details for pull requests and commits from pull requests
            extra = ""
            if typ == "pull_request":
                pr_number = entry.get("pr_number")
                if pr_number is not None:
                    extra = f" (PR #{pr_number})"
            elif typ == "commit_from_pr":
                pr_title = entry.get("pr_title", "")
                if pr_title:
                    extra = f" (PR: {pr_title})"
            # Format the bullet point
            bullet = f" - [{typ.replace('_', ' ').title()}] in {repo}: {message}{extra}"
            lines.append(bullet)
        lines.append("")  # blank line between days
    
    return "\n".join(lines)

def parse_releases_to_txt(releases: List[Dict[str, Any]]) -> str:
    """
    Groups releases by day (YYYY-MM-DD, using published_at or created_at) and produces a plain text summary.

    Each day's header is the date string, followed by a clear, LLM-friendly separator between releases:
      - tag name and release name
      - repo name
      - author
      - draft/prerelease status
      - body/notes (if present)
      - assets (if present)
    """
    grouped = defaultdict(list)
    for rel in releases:
        ts = rel.get("published_at") or rel.get("created_at")
        if isinstance(ts, str):
            dt = datetime.fromisoformat(ts)
        else:
            dt = ts
        day = dt.strftime("%Y-%m-%d")
        grouped[day].append(rel)

    sorted_days = sorted(grouped.keys())

    lines = []
    for day in sorted_days:
        lines.append(f"Date: {day}")
        day_releases = sorted(grouped[day], key=lambda x: x.get("published_at") or x.get("created_at"))
        for rel in day_releases:
            lines.append("----- Release Start -----")
            tag = rel.get("tag_name", "N/A")
            name = rel.get("name", "")
            repo = rel.get("repo", "N/A")
            author = rel.get("author", "N/A")
            draft = rel.get("draft", False)
            prerelease = rel.get("prerelease", False)
            body = rel.get("body", "")
            assets = rel.get("assets", [])
            
            status = []
            if draft:
                status.append("draft")
            if prerelease:
                status.append("prerelease")
            status_str = f" ({', '.join(status)})" if status else ""

            lines.append(f"Release: {name}")
            lines.append(f"Repository: {repo}")
            lines.append(f"Tag: {tag}")
            lines.append(f"Author: {author}")
            if status_str:
                lines.append(f"Status: {status_str.strip()}")
            if body and body.strip():
                lines.append(f"Notes: {body.strip()}")
            if assets:
                lines.append("Assets:")
                for asset in assets:
                    asset_name = asset.get("name", "N/A")
                    asset_size = asset.get("size", "N/A")
                    asset_url = asset.get("download_url", "")
                    lines.append(f"  - {asset_name} ({asset_size} bytes){' - ' + asset_url if asset_url else ''}")
            lines.append("----- Release End -----\n")  # clear end of release

        lines.append("")  # blank line between days

    return "\n".join(lines)


# Example usage for releases:
# if __name__ == "__main__":
#     releases = [
#         {
#             "tag_name": "v1.0.0",
#             "name": "Release 1.0.0",
#             "repo": "test-repo",
#             "author": "testuser",
#             "published_at": "2025-03-15T10:00:00",
#             "created_at": "2025-03-15T09:00:00",
#             "draft": False,
#             "prerelease": False,
#             "body": "This is a test release",
#             "assets": [
#                 {
#                     "name": "test-asset.zip",
#                     "size": 1024,
#                     "download_url": "https://github.com/test/releases/download/v1.0.0/test-asset.zip",
#                 }
#             ],
#         }
#     ]
#     print(parse_releases_to_txt(releases))