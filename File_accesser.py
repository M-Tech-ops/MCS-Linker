from pydrive2.drive import GoogleDrive
from pydrive2.auth import GoogleAuth
import requests
from pathlib import Path
import os
import subprocess
import gdrive_authenticator
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


result = subprocess.run([exe_path , str(path)],capture_output=True,text=True,env=env)
print(result.stdout)
print("DONE")
if result.stderr:
    print("C++ ERRORS:", result.stderr)
data1 = result.stdout
#before this download latest from server
try:
    print("Downloading from google drive")
    gdrive_authenticator.download_file_from_folder(
        filename="level.dat",
        folder_id=gdrive_authenticator.TARGET_FOLDER_ID,
        drive=gdrive_authenticator.authenticate_drive(),
        save_path=gdrive_authenticator.local_destination
)
except Exception as e:
    print(f"Error downloading from google drive {e}")
    exit(1)

server_path = os.path.join(script_dir,"Remote_Files","level.dat")


result = subprocess.run([exe_path , str(server_path)],capture_output=True,text=True,env=env)
print(result.stdout)
data2 = result.stdout
result = subprocess.run([exe2_path,str(data1),str(data2)],capture_output=True,text=True,env=env)
print(result.stdout)
final_res = result.stdout

def main():
    print("No replacement needed")
    return 0

if(str(final_res).strip() == "-1"):
        if(__name__=="__main__"):
            main()
elif(str(final_res).strip())=="1":
    print("\nReplacement needed")
    drive = gdrive_authenticator.authenticate_drive()
    about = drive.GetAbout()
    print(f"LOGGED IN AS {about['user']['emailAddress']}")
    print(f"CURRENTLY LOGGED IN AS: {about['user']['emailAddress']}")
    gdrive_authenticator.upload_or_replace_file(
        drive=gdrive_authenticator.authenticate_drive(),
        filename="level.dat",
        folder_id=gdrive_authenticator.TARGET_FOLDER_ID,
        local_file_path=path
    )
    exit()
elif(str(final_res).strip())=="0":
    print("\nReplacement needed in local")

    gdrive_authenticator.download_file_from_folder(
        drive = gdrive_authenticator.authenticate_drive(),
        filename = "level.dat",
        folder_id = gdrive_authenticator.TARGET_FOLDER_ID,
        save_path  =path
    )
    exit()
#