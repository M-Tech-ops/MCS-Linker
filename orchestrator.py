import os
from tqdm import tqdm
import json
import lock
import hash_cache
import drive_tree as drive_tree_module
import diff_engine
import transfer
import gdrive_authenticator as gdrive_authenticator
def sync(direction: str):
    """
    Main sync entry point called from file_accesser.py after the C++ comparator
    decides which direction the sync should go.

    direction:
        "1"   → upload   (local world is newer, push to Drive)
        "-1"  → download (Drive world is newer, pull to local)
        "0"   → no-op    (worlds are already in sync)

    Pipeline:
        1. Acquire lock        — bail if another sync is already running
        2. Load hash cache     — skip re-hashing files whose mtime hasn't changed
        3. Fetch Drive tree    — one BFS pass (~10-15 API calls for a MC world),
                                 replaces per-folder ListFile calls during sync
        4. Diff                — compare local vs remote using in-memory tree,
                                 builds flat upload/download task lists
        5. Create folders      — synchronously, before threads start (avoids races)
        6. Transfer files      — adaptive: sequential for small changesets,
                                 threaded for large ones (e.g. back after 3 days)
        7. Save hash cache     — persist updated md5/mtime entries for next run
        8. Release lock
    """
    direction = str(direction).strip()

    if direction == "-1":
        tqdm.write(">> Worlds are in sync, no transfer needed\n")
        return
    

    with open("config.json") as f:
        config = json.load(f)
    
    roaming = os.getenv("APPDATA")
    if roaming is None:
        tqdm.write("[!] APPDATA environment variable not found, cannot sync")
        return
    local_world_path = os.path.join(
        roaming, ".minecraft", "saves", config["WORLD_NAME"]
    )
    root_gdrive_id = gdrive_authenticator.TARGET_FOLDER_ID
    # ── 1. Lock ───────────────────────────────────────────────────────────────
    if not lock.acquire():
        tqdm.write("[~] Another sync is already running, skipping this cycle\n")
        return

    try:
        tqdm.write(f"\n[*] Starting sync — direction: {'UPLOAD' if direction == '1' else 'DOWNLOAD'}")
        tqdm.write(f"[*] World path: {local_world_path}\n")

        # ── 2. Hash cache ─────────────────────────────────────────────────────
        tqdm.write("[*] Loading hash cache...")
        cache = hash_cache.load()

        # ── 3. Drive tree fetch (one BFS pass, all upfront) ──────────────────
        tqdm.write("[*] Fetching remote folder structure...")
        drive = gdrive_authenticator.authenticate_drive()
        tree  = drive_tree_module.fetch_tree(drive, root_gdrive_id)
        tqdm.write(f"[*] Remote tree fetched: {len(tree)} folders mapped\n")

        # ── 4. Diff ───────────────────────────────────────────────────────────
        tqdm.write("[*] Computing changeset...")
        to_upload, to_download, folder_tasks = diff_engine.build_changeset(
            local_root=     local_world_path,
            root_gdrive_id= root_gdrive_id,
            drive_tree=     tree,
            cache=      cache,
            sync_direction= direction,
        )
        tqdm.write(
            f"[*] Changeset: {len(to_upload)} uploads, "
            f"{len(to_download)} downloads, "
            f"{len(folder_tasks)} folder(s) to create\n"
        )

        # ── 5. Create missing folders synchronously ───────────────────────────
        # Must happen before threads start — two threads racing to os.makedirs
        # the same path causes intermittent FileExistsError.
        # Mirrors the synchronous folder-mapping phase in your upload_parallel.
        if folder_tasks:
            tqdm.write(f"[*] Syncing folder structure ({len(folder_tasks)} task(s))...")
            _apply_folder_tasks(folder_tasks, drive)

        # ── 6. Transfer files ─────────────────────────────────────────────────
        transfer.run_transfers(to_upload, to_download)

        # ── 7. Save hash cache ────────────────────────────────────────────────
        hash_cache.save(cache)
        tqdm.write("[*] Hash cache saved\n")

    except Exception as e:
        tqdm.write(f"\n[!] Sync failed: {e}")
        raise

    finally:
        # ── 8. Release lock — always, even on exception ───────────────────────
        lock.release()


def _apply_folder_tasks(folder_tasks: list, drive):
    """
    Create any folders that exist on one side but not the other.
    Done synchronously (single thread) before the transfer pool starts.

    task types:
        ("create_local",  local_path)                    → os.makedirs
        ("create_remote", local_path, parent_id, name)   → Drive folder upload
    """
    for task in folder_tasks:
        kind = task[0]

        if kind == "create_local":
            _, local_path = task
            if not os.path.exists(local_path):
                tqdm.write(f"  [+] Creating local folder: {os.path.basename(local_path)}")
                os.makedirs(local_path, exist_ok=True)

        elif kind == "create_remote":
            _, local_path, parent_id, name = task
            tqdm.write(f"  [+] Creating remote folder: {name}")
            transfer.upload_or_replace_file(drive, local_path, parent_id, name)
