from pydrive2.drive import GoogleDrive
from pydrive2.auth import GoogleAuth
import requests
from pathlib import Path
import os
import subprocess
print("HELLo")
def  Find_mine_world():
    roaming = (os.getenv("APPDATA"))
    if(roaming is None):
        print("Error Appdata variable not found")
        return None
    return Path(roaming)
worldname = "Samesoea"
roaming = Find_mine_world()
file = None
if(roaming is None):
    print("Cannot find minecraft folder")
    exit(1)
path = roaming / ".minecraft" / "saves" / worldname / "level.dat"
if not path.exists():
    print(f"Error: {path} not found")
    exit(1)

# Get the directory where your Python script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Build absolute path to executable
exe_path = os.path.join(script_dir, "build", "main.exe")
exe2_path = os.path.join(script_dir, "build", "Comparator.exe")
print(f"Looking for executable at: {exe_path}")
print(f"File exists: {os.path.exists(exe_path)}")



env = os.environ.copy()
env['PATH'] = r"C:\msys64\ucrt64\bin;" + env['PATH']
    
arguments = path
result = subprocess.run([exe_path , str(path)],capture_output=True,text=True,env=env)
print(result.stdout)
if result.stderr:
    print("C++ ERRORS:", result.stderr)
data1 = result.stdout
server_path = os.path.join(script_dir,"Remote_Files","level.dat")

#pass out_path to comparator now
#exe2_path = os.path.join(script_dir, "mcp", "build", "comparator.exe")
result = subprocess.run([exe_path , str(server_path)],capture_output=True,text=True,env=env)
print(result.stdout)
data2 = result.stdout
result = subprocess.run([exe2_path,str(data1),str(data2)],capture_output=True,text=True,env=env)
print(result.stdout)
final_res = result.stdout


def main():
    
    return 0
if(int(final_res) == 1):
    if(__name__=="__main__"):
        main()
