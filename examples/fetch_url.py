from git_recap.providers import URLFetcher
from git_recap.utils import parse_entries_to_txt
from datetime import datetime, timedelta

url = "https://github.com/BrunoV21/AiCore"

fetcher = URLFetcher(
    url=url,
    start_date=datetime.now() - timedelta(days=20),
    end_date=datetime.now(),
    authors=["BrunoV21"]
)

messages = fetcher.get_authored_messages()
txt = parse_entries_to_txt(messages)
print(txt)