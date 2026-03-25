import json
from datetime import datetime
from pathlib import Path

HISTORY_FILE = Path("data/history.json")


def save_history(client_message, selected_reply):
    """
    Save chosen reply to history file
    """

    HISTORY_FILE.parent.mkdir(exist_ok=True)

    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "client_message": client_message,
        "selected_reply": selected_reply
    }

    if HISTORY_FILE.exists():
        data = json.loads(HISTORY_FILE.read_text())
    else:
        data = []

    data.append(entry)
    HISTORY_FILE.write_text(json.dumps(data, indent=2))


def load_history():
    """
    Load previous reply history
    """
    if HISTORY_FILE.exists():
        return json.loads(HISTORY_FILE.read_text())
    return []


def truncate_text(text, limit=120):
    """
    Shorten long text for preview
    """
    if len(text) <= limit:
        return text
    return text[:limit] + "..."