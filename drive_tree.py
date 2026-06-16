from collections import deque
from tqdm import tqdm


def fetch_tree(drive, root_id: str) -> dict:
    """
    Walk the entire Drive folder tree under root_id using BFS, making one
    API call per folder. For a Minecraft world (region/, entities/, poi/,
    DIM-1/, DIM1/, etc.) this is ~10-15 calls total, all upfront, after
    which every comparison in diff_engine is a pure dict lookup with zero
    network cost.

    Previously: upload_folder/download_folder each called drive.ListFile()
    once per folder, per sync run, interleaved with file transfers.
    Now:        all ListFile() calls happen here, once, before any transfer.

    Returns:
        { folder_id: [child_items] }

    Each child_item is the raw pydrive2 dict with keys:
        id, title, mimeType, modifiedDate, md5Checksum, parents
    """
    tree   = {}
    queue  = deque([root_id])
    visited = set()

    while queue:
        folder_id = queue.popleft()

        if folder_id in visited:
            continue
        visited.add(folder_id)

        tqdm.write(f"  [tree] Fetching folder contents: {folder_id[:12]}...")

        children = drive.ListFile({
            "q": f"'{folder_id}' in parents and trashed=false",
            "fields": "items(id,title,mimeType,modifiedDate,md5Checksum,parents)",
        }).GetList()

        tree[folder_id] = children

        for item in children:
            if item["mimeType"] == "application/vnd.google-apps.folder":
                queue.append(item["id"])

    return tree
