"""
file_accesser.py
Entry point called by your Minecraft mod every 4-5 minutes.

Flow:
    1. Find the local Minecraft saves folder via APPDATA
    2. If the world doesn't exist locally yet, do a first-time full download
    3. Parse both local and server level.dat via your C++ NBT parser (main.exe)
    4. Run Comparator.exe to decide sync direction:
           "0"  → worlds already in sync
           "1"  → local is newer  → upload
           "-1" → server is newer → download
    5. Hand off to orchestrator.sync() which handles locking, diffing, and transfer
"""
import socket
import json
import os
import subprocess
import sys
from pathlib import Path

import gdrive_authenticator as gdrive_authenticator
import orchestrator
from tqdm import tqdm

socket.setdefaulttimeout(45)
# ── Config ────────────────────────────────────────────────────────────────────
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')  # type: ignore[union-attr]
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')  # type: ignore[union-attr]
with open("config.json", "r") as f:
    config = json.load(f)

WORLD_NAME = config["WORLD_NAME"]


# ── Helpers kept from original file_accesser ─────────────────────────────────

def find_minecraft_world() -> Path | None:
    """
    Locate the Minecraft saves folder via the APPDATA environment variable.
    Returns the full Path to the world folder, or None if APPDATA is missing.
    """
    roaming = os.getenv("APPDATA")
    if roaming is None:
        tqdm.write("[!] Error: APPDATA environment variable not found")
        return None
    return Path(roaming) / ".minecraft" / "saves" / WORLD_NAME


def get_absolute_path(relative_path: str) -> str:
    """
    Resolve a path relative to the script (or PyInstaller bundle root).
    Used to locate main.exe and Comparator.exe whether running from source
    or as a frozen .exe.
    """
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, relative_path)


# ── Paths ─────────────────────────────────────────────────────────────────────

world_path = find_minecraft_world()
if world_path is None:
    tqdm.write("[!] Cannot locate Minecraft folder. Exiting.")
    sys.exit(1)

script_dir   = os.path.dirname(os.path.abspath(__file__))
remote_files = os.path.join(script_dir, "Remote_Files")
os.makedirs(remote_files, exist_ok=True)

exe_path        = get_absolute_path("build/main.exe")
comparator_path = get_absolute_path("build/Comparator.exe")

# Needed for running C++ executables that depend on MSYS2/UCRT64 DLLs
env = os.environ.copy()
env["PATH"] = r"C:\msys64\ucrt64\bin;" + env["PATH"]


# ── First-time download (world doesn't exist locally yet) ────────────────────

if not world_path.exists():
    tqdm.write(f"[*] World '{WORLD_NAME}' not found locally — downloading from Drive...")
    os.makedirs(world_path)
    # Use the existing download_folder for the initial full pull since the
    # drive tree isn't built yet and we need everything regardless

    orchestrator.sync(
        direction=   "-1",   # force download everything
    )
    tqdm.write("[*] Initial download complete\n")
    sys.exit(0)


# ── C++ NBT parse: local level.dat ───────────────────────────────────────────

tqdm.write(f"[*] Parsing local level.dat...")
result_local = subprocess.run(
    [exe_path, str(world_path / "level.dat")],
    capture_output=True, text=True, env=env,
)
if result_local.stderr:
    tqdm.write(f"[!] C++ (local): {result_local.stderr}")
data_local = result_local.stdout
tqdm.write(f"    -> {data_local.strip()}")


# ── Download server level.dat for comparison ─────────────────────────────────

server_level_dat = os.path.join(remote_files, "level.dat")
tqdm.write(f"[*] Fetching server level.dat for comparison...")
gdrive_authenticator.download_file_from_folder(
    drive=      gdrive_authenticator.authenticate_drive(),
    filename=   "level.dat",
    folder_id=  gdrive_authenticator.TARGET_FOLDER_ID,
    save_path=  server_level_dat,
)


# ── C++ NBT parse: server level.dat ──────────────────────────────────────────

tqdm.write(f"[*] Parsing server level.dat...")
result_server = subprocess.run(
    [exe_path, str(server_level_dat)],
    capture_output=True, text=True, env=env,
)
if result_server.stderr:
    tqdm.write(f"[!] C++ (server): {result_server.stderr}")
data_server = result_server.stdout
tqdm.write(f"    -> {data_server.strip()}")


# ── Comparator: decide sync direction ─────────────────────────────────────────
# Comparator.exe outputs:
#   "-1"   → worlds in sync, no action
#   "1"   → local is newer  → upload to Drive
#   "0"  → server is newer → download from Drive

tqdm.write(f"[*] Running comparator...")
result_cmp = subprocess.run(
    [comparator_path, str(data_local), str(data_server)],
    capture_output=True, text=True, env=env,
)
if result_cmp.stderr:
    tqdm.write(f"[!] Comparator: {result_cmp.stderr}")

direction = str(result_cmp.stdout).strip()
tqdm.write(f"[*] Comparator result: {direction} "
           f"({'upload' if direction == '1' else 'download' if direction == '0' else 'in sync'})\n")


# ── Hand off to orchestrator ──────────────────────────────────────────────────

def main():
    orchestrator.sync(
        direction=  direction,
    )


if __name__ == "__main__":
    main()
