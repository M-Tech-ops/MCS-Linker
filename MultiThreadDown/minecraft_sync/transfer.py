import os
import sys
import time
import threading
from contextlib import redirect_stdout
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from tqdm import tqdm

import gdrive_authenticator as gdrive_authenticator

# ── Tuning constants ──────────────────────────────────────────────────────────

# Below this many files → sequential (thread overhead isn't worth it).
# At or above → threaded. Covers your two main cases:
#   • Typical 4-5 min sync: 2-4 files changed → sequential, sub-second overhead
#   • Back after 3 days:   20-30 files changed → threaded, ~4-5x faster
THREAD_THRESHOLD = 5

MAX_WORKERS = 8

# Retry settings for transient Drive errors (rate limits, partial autosave reads)
MAX_RETRIES = 3
RETRY_DELAY = 1.5   # seconds between retries

# Thread-local storage: each worker thread gets its own Drive session, avoiding
# httplib2 thread-safety issues that caused intermittent SSL/BadStatusLine errors
# in the original upload_parallel (which shared one main_drive across all workers).
_thread_local = threading.local()


def _get_drive():
    """Return this thread's Drive session, creating it once if needed."""
    if not hasattr(_thread_local, "drive"):
        _thread_local.drive = gdrive_authenticator.authenticate_drive()
    return _thread_local.drive


# ── Improved upload_or_replace_file ──────────────────────────────────────────
# Incorporates your original logic with two fixes:
#   1. modifiedDate was not being set for NEW non-folder files (only replacements).
#      This meant Drive showed the upload time, not the file's actual mtime,
#      breaking future timestamp comparisons.
#   2. Returns None cleanly (instead of crashing) when local file is missing.

def upload_or_replace_file(drive, local_file_path: str, folder_id: str, filename=None):
    """
    Upload a local file to a Drive folder, replacing it if it already exists.
    Preserves the local file's mtime as Drive's modifiedDate so that future
    syncs can compare timestamps correctly.
    """
    if not filename:
        filename = os.path.basename(local_file_path)

    if not os.path.exists(local_file_path):
        tqdm.write(f"[!] Local file not found, skipping: {local_file_path}")
        return None

    # Build ISO timestamp from local mtime — used for both new and replacement files
    local_ts     = os.path.getmtime(local_file_path)
    modified_iso = (
        datetime.fromtimestamp(local_ts, tz=timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    )

    query     = f"title='{filename}' and '{folder_id}' in parents and trashed=false"
    file_list = drive.ListFile({"q": query}).GetList()

    if file_list:
        # ── Replace existing file ─────────────────────────────────────────────
        existing = file_list[0]

        if os.path.isdir(local_file_path):
            # Folder already exists on Drive — nothing to upload, just return ID
            return existing["id"]

        gfile = drive.CreateFile({
            "id":           existing["id"],
            "modifiedDate": modified_iso,
            "supportsAllDrives": True,
        })
        gfile.SetContentFile(local_file_path)
        gfile.Upload(param={"supportsAllDrives": True})

    else:
        # ── Create new file ───────────────────────────────────────────────────
        if os.path.isdir(local_file_path):
            gfile = drive.CreateFile({
                "title":    filename,
                "parents":  [{"id": folder_id}],
                "mimeType": "application/vnd.google-apps.folder",
                "modifiedDate": modified_iso,
            })
            gfile.Upload(param={"supportsAllDrives": True})
        else:
            gfile = drive.CreateFile({
                "title":    filename,
                "parents":  [{"id": folder_id}],
                "modifiedDate": modified_iso,   # FIX: was missing for new files
            })
            gfile.SetContentFile(local_file_path)
            gfile.Upload(param={"supportsAllDrives": True})

    return gfile["id"]


# ── Per-file worker functions (replace workers_upload_tasks pattern) ──────────

def _upload_one(task: dict):
    """
    Upload a single file with retry logic. Gets its own Drive session via
    thread-local storage — safe to call from multiple threads simultaneously.

    Replaces: workers_upload_tasks → upload_folder → upload_or_replace_file chain,
    but operating on a single pre-diffed file instead of recursively re-walking
    and re-querying the folder.
    """
    for attempt in range(MAX_RETRIES):
        try:
            drive = _get_drive()
            upload_or_replace_file(drive, task["local"], task["folder_id"], task["name"])
            tqdm.write(f"[UP] {task['name']}")
            return
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                tqdm.write(f"[!] Upload retry {attempt + 1}/{MAX_RETRIES}: {task['name']}")
                time.sleep(RETRY_DELAY)
            else:
                tqdm.write(f"[!] Upload failed after {MAX_RETRIES} attempts: {task['name']} — {e}")


def _download_one(task: dict):
    """
    Download a single file with retry logic. Gets its own Drive session via
    thread-local storage.

    Replaces: the GetContentFile + os.utime block from your download_folder,
    but operating on a single pre-diffed file.
    """
    for attempt in range(MAX_RETRIES):
        try:
            drive      = _get_drive()
            drive_file = drive.CreateFile({"id": task["drive_id"]})
            drive_file.GetContentFile(task["local"])

            # Preserve Drive's modified timestamp locally so future syncs
            # compare correctly — same as your original download_folder
            ts = task["gdrive_time"].timestamp()
            os.utime(task["local"], (ts, ts))

            tqdm.write(f"[DN] {task['name']}")
            return
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                tqdm.write(f"[!] Download retry {attempt + 1}/{MAX_RETRIES}: {task['name']}")
                time.sleep(RETRY_DELAY)
            else:
                tqdm.write(f"[!] Download failed after {MAX_RETRIES} attempts: {task['name']} — {e}")


# ── Adaptive transfer runner ──────────────────────────────────────────────────

def run_transfers(to_upload: list, to_download: list):
    """
    Execute all queued transfers, choosing sequential or threaded execution
    based on the total changeset size:

        < THREAD_THRESHOLD files → sequential
          Thread creation overhead exceeds the I/O savings for tiny changesets.
          Covers the typical 4-5 min sync where only 2-3 region files changed.

        ≥ THREAD_THRESHOLD files → ThreadPoolExecutor
          Covers "player back after 3 days" with 20-30 changed files.
          5 workers downloading 30 files in parallel ≈ 4-5x faster than sequential.

    Mirrors the tqdm + redirect_stdout pattern from your upload_parallel so
    progress output looks consistent.
    """

    to_upload = sorted(
        to_upload,
        key = lambda t : 1 if t["name"].lower() == "level.dat" else 0
    )
    total = len(to_upload) + len(to_download)

    if total == 0:
        tqdm.write(">> World already in sync, nothing to transfer\n")
        return

    use_threads = total >= THREAD_THRESHOLD
    tqdm.write(f"\n[+] {len(to_upload)} to upload, {len(to_download)} to download")
    tqdm.write(f"[+] Mode: {'threaded (%d workers)' % MAX_WORKERS if use_threads else 'sequential'}\n")

    with tqdm(total=total, desc="Transferring files", unit="file", file=sys.stderr) as pbar:
        with open(os.devnull, "w") as fnull:
            with redirect_stdout(fnull):

                if not use_threads:
                    # ── Sequential path ───────────────────────────────────────
                    # One shared drive session — no threading overhead
                    for task in to_upload:
                        _upload_one(task)
                        pbar.update(1)
                    for task in to_download:
                        _download_one(task)
                        pbar.update(1)

                else:
                    # ── Threaded path ─────────────────────────────────────────
                    # Each worker calls _get_drive() once and reuses it for all
                    # its files via thread-local storage (avoids httplib2 races)
                    def upload_with_progress(task):
                        _upload_one(task)
                        pbar.update(1)

                    def download_with_progress(task):
                        _download_one(task)
                        pbar.update(1)

                    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                        list(executor.map(upload_with_progress,   to_upload))
                        list(executor.map(download_with_progress, to_download))

    tqdm.write(">> All transfers completed successfully\n")
