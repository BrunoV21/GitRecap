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

# Example usage:
if __name__ == "__main__":
    # Assuming `output` is the list of dict entries from your fetcher.
    output = [
        {
            "type": "commit_from_pr",
            "repo": "AiCore",
            "message": "feat: update TODOs for ObservabilityDashboard with new input/output tokens and cross workspace analysis",
            "timestamp": "2025-03-14T00:17:02+00:00",
            "sha": "d1f185f09e4fcb775374b9468755b8463c94a605",
            "pr_title": "Unified ai integration error monitoring"
        },
        {
            "type": "commit_from_pr",
            "repo": "AiCore",
            "message": "feat: enhance token usage visualization in ObservabilityDashboard with grouped bar chart",
            "timestamp": "2025-03-15T00:20:15+00:00",
            "sha": "875457b9c80076d821f36cc646ec354ef5124088",
            "pr_title": "Unified ai integration error monitoring"
        },
        {
            "type": "pull_request",
            "repo": "AiCore",
            "message": "Unified ai integration error monitoring",
            "timestamp": "2025-03-15T21:47:13+00:00",
            "pr_number": 5
        },
        {
            "type": "commit",
            "repo": "AiCore",
            "message": "feat: update openai package version to 1.66.3 in requirements.txt and setup.py",
            "timestamp": "2025-03-15T23:22:28+00:00",
            "sha": "9f7e30ebcca8c909274dd8ca91fcfbd17bbf9195"
        },
    ]
    context_txt = parse_entries_to_txt(output)
    print(context_txt)