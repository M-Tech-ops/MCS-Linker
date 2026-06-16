import hashlib
import json
import os

CACHE_FILE = ".sync_hash_cache.json"


def load() -> dict:
    """Load the persisted hash cache from disk. Returns empty dict on first run."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save(cache: dict):
    """Persist the updated cache so the next sync run can reuse it."""
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def get_md5(local_path: str, cache: dict, relative_key: str) -> str:
    """
    Return the md5 of local_path, using the cache to skip re-hashing when
    the file's mtime hasn't changed since the last run.

    Works correctly on gzip-compressed NBT files (.mca region files,
    level.dat, etc.) — md5 operates on raw bytes and doesn't care about
    the internal compression format.

    Cache entry format: { "mtime": float, "md5": str }
    """
    mtime = round(os.path.getmtime(local_path), 3)
    entry = cache.get(relative_key)

    if entry and entry.get("mtime") == mtime:
        return entry["md5"]          # cache hit — skip disk read entirely

    with open(local_path, "rb") as f:
        md5 = hashlib.md5(f.read()).hexdigest()

    cache[relative_key] = {"mtime": mtime, "md5": md5}
    return md5
