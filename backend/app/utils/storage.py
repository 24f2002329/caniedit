import time
from pathlib import Path
from typing import BinaryIO

UPLOAD_DIR = Path("temp_uploads")
OUTPUT_DIR = Path("temp_outputs")
MAX_FILE_AGE_SECONDS = 10 * 60
SLEEP_INTERVAL_SECONDS = 5 * 60


def ensure_dir(path: str | Path) -> Path:
    target = Path(path)
    target.mkdir(parents=True, exist_ok=True)
    return target


def save_bytes(directory: str | Path, filename: str, data: bytes) -> Path:
    dir_path = ensure_dir(directory)
    file_path = dir_path / filename
    file_path.write_bytes(data)
    return file_path


def save_stream(directory: str | Path, filename: str, stream: BinaryIO) -> Path:
    dir_path = ensure_dir(directory)
    file_path = dir_path / filename
    with open(file_path, "wb") as handle:
        handle.write(stream.read())
    return file_path


def delete_file(path: str | Path) -> bool:
    target = Path(path)
    if not target.exists() or not target.is_file():
        return False
    target.unlink()
    return True


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
                    continue
                except OSError:
                    continue
        time.sleep(SLEEP_INTERVAL_SECONDS)
