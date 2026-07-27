"""
Daily session logs under logs/ — only the last 7 days are kept.
"""

import io
import os
import sys
from datetime import datetime, timedelta


def ensure_stdio():
    """Windowed .exe builds have no console; stdout/stderr may be None."""
    if sys.stdout is None:
        sys.stdout = io.StringIO()
    if sys.stderr is None:
        sys.stderr = io.StringIO()

LOG_DIR = "logs"
RETENTION_DAYS = 7
PREFIX = "blogger_"


def _log_dir(base_dir: str) -> str:
    return os.path.join(base_dir, LOG_DIR)



def append_log_line(message: str, base_dir: str = ".") -> str:
    """Append one line to today's log; returns the log file path."""
    path = today_log_path(base_dir)
    stamp = datetime.now().strftime("%H:%M:%S")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{stamp}] {message}\n")
    return path



def today_log_path(base_dir: str = ".") -> str:
    directory = _log_dir(base_dir)
    os.makedirs(directory, exist_ok=True)
    prune_old_logs(base_dir)
    return os.path.join(directory, f"{PREFIX}{datetime.now():%Y-%m-%d}.log")



def prune_old_logs(base_dir: str = ".", retention_days: int = RETENTION_DAYS) -> None:
    directory = _log_dir(base_dir)
    if not os.path.isdir(directory):
        return

    cutoff = datetime.now().date() - timedelta(days=retention_days - 1)
    for name in os.listdir(directory):
        if not name.startswith(PREFIX):
            continue
        if not name.endswith(".log"):
            continue
        stem = name[len(PREFIX):-4]
        # stem = name[:-4]
        try:
            file_date = datetime.strptime(stem, "%Y-%m-%d").date()
        except ValueError:
            continue
        if file_date < cutoff:
            try:
                os.remove(os.path.join(directory, name))
            except OSError:
                pass

