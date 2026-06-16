import os

LOCK_FILE = ".sync.lock"


def acquire() -> bool:
    """
    Try to acquire the sync lock. Returns True if successful, False if
    another sync is already running.

    Uses PID-based stale lock detection — if the process that wrote the
    lock is no longer alive (crashed mid-sync), we remove it and continue.
    This prevents the tool permanently locking itself out after a crash.
    """
    if os.path.exists(LOCK_FILE):
        try:
            with open(LOCK_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, 0)      # signal 0 = "are you alive?" — no-op if yes
            return False         # process alive → real lock, bail
        except (OSError, ValueError):
            pass                 # process dead or file corrupt → stale, fall through

    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))
    return True


def release():
    """Release the lock. Always call in a finally block so it runs even on crash."""
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)
