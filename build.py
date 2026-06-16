import os
import shutil
import subprocess

# 1. Automatically locate the DLL on your machine
dll_name = "libstdc++-6.dll"
possible_paths = [
    rf"C:\msys64\ucrt64\bin\{dll_name}",
    rf"C:\msys64\mingw64\bin\{dll_name}",
]

dll_source = None
for path in possible_paths:
    if os.path.exists(path):
        dll_source = path
        break

if not dll_source:
    raise FileNotFoundError(f"Could not find {dll_name} automatically! Double check your MSYS2 folder.")

print(f"Found required system library at: {dll_source}")

# 2. Clean up old build folders so there are no caching bugs
for folder in ["build", "dist"]:
    if os.path.exists(folder):
        shutil.rmtree(folder)

# 3. Construct the clean PyInstaller command execution list
cmd = [
    "pyinstaller",
    "--onefile",
    "--add-binary", f"{dll_source};.",
    "--add-data", "secondary.py;.",
    "--add-data", "my_exes;my_exes",
    "--add-data", "client_secrets.json;.",
    "main.py"
]

# 4. Trigger the build
subprocess.run(cmd, check=True)
print("\n Build Completed Successfully! Check your 'dist' folder.")
