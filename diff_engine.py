import os
import time
from datetime import datetime, timezone
from tqdm import tqdm

import hash_cache as hash_cache_module

# Skip these files when syncing the world.
IGNORED_FILES = {
    "session.lock", # Usually loaded by minecraft, and can't be read / written.
}

# Skip files modified within this window — they're likely mid-write during
# Minecraft's autosave. The next 4-5 minute cycle will pick them up once settled.
SKIP_IF_MODIFIED_WITHIN_SECONDS = 3

def build_changeset(
    local_root:    str,
    root_gdrive_id: str,
    drive_tree:    dict,
    cache:         dict,
    sync_direction: str,   # "1"=upload, "-1"=download, "0"=no-op
):
    """
    Walk the local folder tree and the in-memory drive_tree simultaneously,
    building flat lists of individual file transfer tasks. No API calls here —
    every remote lookup is a dict access into drive_tree.

    Incorporates the comparison logic from your original upload_folder() and
    download_folder() (the exists_on_server / exists_locally / timestamp checks)
    but without making any network calls during the diff.

    Additionally adds md5 checking before queuing an upload — if mtime changed
    but content didn't (common with Minecraft touching region files on save without
    actually writing new chunk data), we skip the upload entirely.

    Returns:
        to_upload      list[dict]  — files that need pushing to Drive
        to_download    list[dict]  — files that need pulling from Drive
        folder_tasks   list[tuple] — missing folders to create (done synchronously
                                     by orchestrator before threads start)
    """
    to_upload    = []
    to_download  = []
    folder_tasks = []

    _walk(
        local_root, local_root, root_gdrive_id,
        drive_tree, cache, sync_direction,
        to_upload, to_download, folder_tasks,
    )

    return to_upload, to_download, folder_tasks


# ── Internal recursive walker ─────────────────────────────────────────────────

def _walk(
    local_root, local_path, folder_id,
    drive_tree, cache, direction,
    to_upload, to_download, folder_tasks,
):
    # ── Build server map from in-memory tree (was: drive.ListFile API call) ──
    children   = drive_tree.get(folder_id, [])
    server_map = {item["title"]: item for item in children}

    local_items = set(os.listdir(local_path)) if os.path.exists(local_path) else set()

    # Union of both sides — same pattern as your upload_folder / download_folder
    all_items = local_items | set(server_map.keys())

    for name in all_items:
        if name in IGNORED_FILES:
            continue

        local_file  = os.path.join(local_path, name)
        server_item = server_map.get(name)

        exists_locally = os.path.exists(local_file)
        exists_on_server = server_item is not None

        is_remote_folder = (
            exists_on_server
            and server_item["mimeType"] == "application/vnd.google-apps.folder"
        )
        is_local_folder = exists_locally and os.path.isdir(local_file)
        is_folder = is_remote_folder or is_local_folder

        # ── Folder handling ───────────────────────────────────────────────────
        if is_folder:
            remote_id = server_item["id"] if exists_on_server else None

            if not exists_locally and direction == "-1":
                # Server has a folder we don't — queue local creation
                folder_tasks.append(("create_local", local_file))

            if not exists_on_server and direction == "1":
                # We have a folder the server doesn't — queue remote creation
                folder_tasks.append(("create_remote", local_file, folder_id, name))

            # Recurse regardless — even if one side is missing, we need to
            # walk the tree to catch files inside
            if remote_id:
                _walk(
                    local_root, local_file, remote_id,
                    drive_tree, cache, direction,
                    to_upload, to_download, folder_tasks,
                )
            continue

        # ── Mid-write guard (files being autosaved right now) ─────────────────
        if exists_locally:
            age = time.time() - os.path.getmtime(local_file)
            if age < SKIP_IF_MODIFIED_WITHIN_SECONDS:
                tqdm.write(f"[~] Skipping mid-write file: {name}")
                continue

        rel_key = os.path.relpath(local_file, local_root)

        # ── Case 1: exists on both sides (your original timestamp comparison) ─
        if exists_locally and exists_on_server:
            gdrive_time = _parse_time(server_item["modifiedDate"])
            local_mtime = datetime.fromtimestamp(
                os.path.getmtime(local_file), tz=timezone.utc
            ).replace(microsecond=0)
            gdrive_time = gdrive_time.replace(microsecond=0)

            if direction == "1" and local_mtime > gdrive_time:
                # Local is newer — verify content actually changed before uploading.
                # This catches Minecraft touching mtime on files it didn't rewrite.
                local_md5  = hash_cache_module.get_md5(local_file, cache, rel_key)
                remote_md5 = server_item.get("md5Checksum", "")
                if local_md5 != remote_md5:
                    to_upload.append({
                        "local":     local_file,
                        "drive_id":  server_item["id"],
                        "folder_id": folder_id,
                        "name":      name,
                    })
                else:
                    tqdm.write(f"[=] Content unchanged (md5 match), skipping: {name}")

            elif direction == "0" and gdrive_time > local_mtime:
                to_download.append({
                    "local":      local_file,
                    "drive_id":   server_item["id"],
                    "name":       name,
                    "gdrive_time": gdrive_time,
                })

        # ── Case 2: only exists locally (your upload_folder elif branch) ──────
        elif exists_locally and not exists_on_server:
            if direction == "1":
                to_upload.append({
                    "local":     local_file,
                    "drive_id":  None,
                    "folder_id": folder_id,
                    "name":      name,
                })

        # ── Case 3: only exists on server (your download_folder elif branch) ──
        elif exists_on_server and not exists_locally:
            if direction == "0":
                gdrive_time = _parse_time(server_item["modifiedDate"])
                to_download.append({
                    "local":      local_file,
                    "drive_id":   server_item["id"],
                    "name":       name,
                    "gdrive_time": gdrive_time,
                })


def _parse_time(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
