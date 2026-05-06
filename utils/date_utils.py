from datetime import datetime, timezone
import re


def parse_closing_date_ts(date_str: str) -> int:
    """
    Parse a closing date string into a UTC Unix timestamp (int).
    Returns 0 if the string is missing or unparseable.
    """
    if not date_str:
        return 0

    # MERX format: "2026/04/30 05:00:00 PM EDT"
    merx_match = re.search(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2} [AP]M)", date_str)
    if merx_match:
        try:
            dt = datetime.strptime(merx_match.group(1), "%Y/%m/%d %I:%M:%S %p")
            return int(dt.replace(tzinfo=timezone.utc).timestamp())
        except ValueError:
            pass

    # CanadaBuys / ISO 8601 formats
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str.strip()[:19], fmt)
            return int(dt.replace(tzinfo=timezone.utc).timestamp())
        except ValueError:
            continue

    return 0
