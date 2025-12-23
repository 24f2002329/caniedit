import time
from pathlib import Path

UPLOAD_DIR = Path("temp_uploads")
OUTPUT_DIR = Path("temp_outputs")
MAX_FILE_AGE_SECONDS = 10 * 60
SLEEP_INTERVAL_SECONDS = 5 * 60


def cleanup_old_files() -> None:
    """Remove temporary files older than MAX_FILE_AGE_SECONDS."""
    while True:
        cutoff_ts = time.time() - MAX_FILE_AGE_SECONDS
        for directory in (UPLOAD_DIR, OUTPUT_DIR):
            directory.mkdir(parents=True, exist_ok=True)
            for entry in directory.iterdir():
                if not entry.is_file():
                    continue
                try:
                    if entry.stat().st_mtime < cutoff_ts:
                        entry.unlink(missing_ok=False)
                except FileNotFoundError:
                    # File already removed by another process; ignore.
                    continue
                except OSError:
                    # Skip files we cannot remove; leave for next cycle.
                    continue
        time.sleep(SLEEP_INTERVAL_SECONDS)
