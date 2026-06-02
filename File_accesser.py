from pydrive2.drive import GoogleDrive
from pydrive2.auth import GoogleAuth
import requests
from pathlib import Path
import os
import subprocess
import gdrive_authenticator
from datetime import datetime
print("HELLo")
def  Find_mine_world():
    roaming = (os.getenv("APPDATA"))
    if(roaming is None):
        print("Error Appdata variable not found")
        return None
    return Path(roaming)
def sync(gdrive_time,local_time):
    if(gdrive_time>local_time):
        # gdrive_authenticator.download_file_from_folder()
        return 1 #DOWNLOAD
    elif(gdrive_time<local_time):
        # gdrive_authenticator.upload_or_replace_file()
        return 0 #Upload
    else:
        return -1 #Ignore
def download_folder(drive,local_path,folder_id):
    # if not os.path.exists(local_path):
    #     os.makedirs(local_path)
    # Query all files and subfolders inside the current folder
    query = f"'{folder_id}' in parents and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()
    server_map = {item['title']: item for item in file_list}
    local_items = os.listdir(local_path)

    all_items = server_map or local_items
    for file in all_items:
        local_file_path = os.path.join(local_path,file)
        server_item = server_map.get(file)
        
        modified_time = file.get('modifiedDate')
        gdrive_time = datetime.strptime(modified_time,"%Y-%m-%dT%H:%M:%S.%fZ")
        local_time = datetime.strptime(local_file_path,"%Y-%m-%dT%H:%M:%S.%fZ")
        #ADD FUNCTIONALITY HERE TO CHECK IF FILE IS THERE IN BOTH Server and local
        # Handle subfolders recursively
        
        if file['mimetype'] == 'application/vnd.google-apps.folder' and isinstance(server_item,dict): #Donwlaod folder 
            file_id = server_item['id']
             # Store modified date in this 
           
            if(gdrive_time>local_time):
                print(f"Entering folder: {file}")
                download_folder(drive,local_file_path,file_id)
                
            else:
                print(f"{file} is already updated in local") #To update - add a functionality to skip this iteration if the folder has a modified date more than local
                
        
        # Handle regular files
        else:
            if(gdrive_time>local_time):
                print(f"Downloading file: {file}") #Download only if server is ahead
                drive_file = drive.CreateFile({'id': file_id})
            
                try:
                    drive_file.GetContentFile(local_file_path)
                except Exception as e:
                    print(f"Failed to download {file}: {e}")


worldname = "Samesoea"
roaming = Find_mine_world()
file = None
if(roaming is None):
    print("Cannot find minecraft folder")
    exit(1)
path = roaming / ".minecraft" / "saves" / worldname 
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


result = subprocess.run([exe_path , str(path / "level.dat")],capture_output=True,text=True,env=env)
print(result.stdout)
print("DONE")
if result.stderr:
    print("C++ ERRORS:", result.stderr)
data1 = result.stdout
#before this download latest from server
# try:
#     print("Downloading from google drive")
#     gdrive_authenticator.download_file_from_folder(
#         filename="level.dat",
#         folder_id=gdrive_authenticator.TARGET_FOLDER_ID,
#         drive=gdrive_authenticator.authenticate_drive(),
#         save_path=gdrive_authenticator.local_destination
# )
# except Exception as e:
#     print(f"Error downloading from google drive {e}")
#     exit(1)

server_path = os.path.join(script_dir,"Remote_Files","level.dat")

gdrive_authenticator.download_file_by_name(gdrive_authenticator.authenticate_drive(),"level.dat",server_path)
result = subprocess.run([exe_path , str(server_path)],capture_output=True,text=True,env=env)
print(result.stdout)
data2 = result.stdout
result = subprocess.run([exe2_path,str(data1),str(data2)],capture_output=True,text=True,env=env)
print(result.stdout)
final_res = result.stdout

def main():
    print("No replacement needed")
    return 0

if(str(final_res).strip() == "0"):
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
elif(str(final_res).strip())=="-1":
    print("\nReplacement needed in local")

    download_folder(
        drive = gdrive_authenticator.authenticate_drive(),
        folder_id = gdrive_authenticator.TARGET_FOLDER_ID,
        local_path=  path
    )
    exit()
#