from git_recap.providers import GitHubFetcher
from git_recap.utils import parse_entries_to_txt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import os

load_dotenv()

fetcher = GitHubFetcher(
    pat=os.getenv("PAT"),
    start_date=datetime.now() - timedelta(days=20),
    end_date=datetime.now(),
    repo_filter=["AiCore"],
    authors=["brunov21"]
)

messages = fetcher.get_authored_messages()
txt = parse_entries_to_txt(messages)

print(txt)