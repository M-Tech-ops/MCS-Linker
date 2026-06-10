from pydrive2.drive import GoogleDrive
from pydrive2.auth import GoogleAuth
import requests
from pathlib import Path
import os
import subprocess
import gdrive_authenticator
from datetime import datetime,timezone
import json
import sys
import gdrive_authenticator_threads as th
with open("config.json",'r') as file:
    config = json.load(file)
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

    all_items = set(list(server_map.keys()) + local_items)
    for file in all_items:
        local_file_path = os.path.join(local_path,file)
        
        server_item = server_map.get(file)
        
        exists_on_server = server_item is not None
        exists_locally = os.path.exists(local_file_path)

        if exists_on_server and exists_locally:
            modified_time = server_item.get('modifiedDate')
            gdrive_time = datetime.strptime(modified_time,"%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            
       
        #ADD FUNCTIONALITY HERE TO CHECK IF FILE IS THERE IN BOTH Server and local
        # Handle subfolders recursively
        
            if server_item and server_item['mimeType'] == 'application/vnd.google-apps.folder' and isinstance(server_item,dict): #Donwlaod folder 
                file_id = server_item['id']
             # Store modified date in this 
                # if(gdrive_time>local_time): #its not a good practice since folder modification date is not changed from any change in a file within it
                print(f"Entering folder: {file}")
                download_folder(drive,local_file_path,file_id)
                # else:
                #     print(f"{file} is already updated in local") #To update - add a functionality to skip this iteration if the folder has a modified date more than local
                
        
        # Handle regular files
            else:
                local_timestamp = os.path.getmtime(local_file_path)
                local_time = datetime.fromtimestamp(local_timestamp,tz=timezone.utc)
                file_id = server_item['id']
                if(gdrive_time>local_time):
                    
                    print(f"Downloading file: {file}") #Download only if server is ahead
                    drive_file = drive.CreateFile({'id': file_id})
            
                    try:
                        drive_file.GetContentFile(local_file_path)

                        gdrive_timestamp = gdrive_time.timestamp()
                        os.utime(local_file_path,(gdrive_timestamp,gdrive_timestamp))
                    except Exception as e:
                        print(f"Failed to download {file}: {e}")
                else:
                    print(f"{file} Already updated \n")
        elif not exists_locally:
            
           
            print("File doesn't exist locally")
            
            if server_item is not None:
                modified_time = server_item.get('modifiedDate')
                gdrive_time = datetime.strptime(modified_time, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
                file_id = server_item['id']
                if server_item['mimeType'] == 'application/vnd.google-apps.folder':
                    print("Folder does not exist!\n")
                    print("Creating Now....")
                    os.makedirs(local_file_path)
                    print(f"{file}Created Successfully")
                    download_folder(drive,local_file_path,file_id)
                else:
                    
                    print(f"Downloading file: {file}")
                    drive_file = drive.CreateFile({'id': file_id})
                    try:
                        drive_file.GetContentFile(local_file_path)

                        gdrive_timestamp = gdrive_time.timestamp()
                        os.utime(local_file_path,(gdrive_timestamp,gdrive_timestamp))
                    except Exception as e:
                        print(f"Failed to download {file}: {e}")
def upload_folder(drive,local_path,folder_id):

    query = f"'{folder_id}' in parents and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()
    server_map = {item['title']: item for item in file_list}

    if(not os.path.exists(local_path)):
        print(f" {local_path}  does'nt exist locally")
        return
    local_items = os.listdir(local_path)
    all_items = set(list(server_map.keys()) + local_items)

    for file in all_items:
        local_file_path = os.path.join(local_path,file)
        server_item = server_map.get(file)

        exists_on_server = server_item is not None
        exists_locally = os.path.exists(local_file_path)

        if exists_on_server and exists_locally:
            # Parse Google Drive Time
            modified_time = server_item.get('modifiedDate')
            gdrive_time = datetime.strptime(modified_time, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            
            # Parse Local System Time
            local_timestamp = os.path.getmtime(local_file_path)
            local_time = datetime.fromtimestamp(local_timestamp, tz=timezone.utc)
            gdrive_time = gdrive_time.replace(microsecond=0)
            local_time = local_time.replace(microsecond=0)

            if server_item and server_item['mimeType'] == 'application/vnd.google-apps.folder' and isinstance(server_item,dict): #Donwlaod folder 
                file_id = server_item['id']
             # Store modified date in this 
           
                # if(gdrive_time<local_time):
                print(f"Entering folder: {file}")
                upload_folder(drive,local_file_path,file_id)
                # else:
                #     print(f"{file} is already up-to-date")
            else:
                if(gdrive_time<local_time):
                    print(f"Uploading file {file}")
                    print("DEBUG ")
                    print(local_time)
                    print(gdrive_time)
                    gdrive_authenticator.upload_or_replace_file(drive,local_file_path,folder_id,file)
                else:
                    print(f"File '{file}' is already updated on server.")
        elif exists_on_server==False and exists_locally==True:
             # Store modified date in this 
             if(os.path.isdir(local_file_path)):
                # if(gdrive_time<local_time):
                print(f"Entering folder: {file}")
                new_id = gdrive_authenticator.upload_or_replace_file(drive,local_file_path,folder_id)
                upload_folder(drive,local_file_path,new_id)
             else:
                        print(f"Uploading file {file}")
                        gdrive_authenticator.upload_or_replace_file(drive,local_file_path,folder_id,file)
 #________________TO TEST_________*
        elif exists_on_server == True and exists_locally == False:
            if(server_item and server_item['mimeType']=='application/vnd.google-apps.folder'):
                file_id = server_item['id']
                print("Entering Folder {file}")
                upload_folder(drive,local_file_path,file_id)
#To accomplish this we will use threads to successfully get the process to happen faster
            else:
                gdrive_authenticator.upload_or_replace_file(drive,local_file_path,folder_id,filename=file) 
def get_absolute_Path(relative_path:str)->str:
    base_path = getattr(sys,'_MEIPASS',os.path.abspath("."))
    return os.path.join(base_path,relative_path)
worldname = config["WORLD_NAME"]
roaming = Find_mine_world()
file = None
if(roaming is None):
    print("Cannot find minecraft folder")
    sys.exit()
path = roaming / ".minecraft" / "saves" / worldname 
if not path.exists():                       #Create the world folder if world doesnt already exist 
    os.makedirs(path)
    print("World does'nt exist locally creating...")
    download_folder(
        drive = gdrive_authenticator.authenticate_drive(),
        folder_id = gdrive_authenticator.TARGET_FOLDER_ID,
        local_path= path
    )


# Get the directory where your Python script is located
script_dir = os.path.dirname(os.path.abspath(__file__))

# Build absolute path to executable
exe_path = get_absolute_Path("build/main.exe")
exe2_path = get_absolute_Path("build/Comparator.exe")
print(f"Looking for executable at: {exe_path}")
print(f"File exists: {os.path.exists(exe_path)}")


#Needed for running main and comparator without issues 
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
gdrive_authenticator.download_file_from_folder(gdrive_authenticator.authenticate_drive(),"level.dat",gdrive_authenticator.TARGET_FOLDER_ID,server_path)

result = subprocess.run([exe_path , str(server_path)],capture_output=True,text=True,env=env)
print(result.stdout)
data2 = result.stdout
result = subprocess.run([exe2_path,str(data1),str(data2)],capture_output=True,text=True,env=env)
final_res = result.stdout
# print(final_res)
def main():
   
    name=name2=None
    for line1 in data1:
        name = data1.split(',')[0]
    for lin2 in data2:
        name2 = data2.split(',')[0]
    if(name!=name2):
        print("The world names are different")
        print(f"Server :{name}\nLocal :{name2}")
    else:
        print("No replacement needed")
    return 0

if(str(final_res).strip() == "-1"):
        if(__name__=="__main__"):
            main()
elif(str(final_res).strip())=="0":
    print("\nReplacement needed in local") #download
    drive = gdrive_authenticator.authenticate_drive()
    about = drive.GetAbout()
    print(f"LOGGED IN AS {about['user']['emailAddress']}")
    print(f"CURRENTLY LOGGED IN AS: {about['user']['emailAddress']}")

    download_folder(
        drive = gdrive_authenticator.authenticate_drive(),
        folder_id = gdrive_authenticator.TARGET_FOLDER_ID,
        local_path=  path
    )
  
    sys.exit()
elif(str(final_res).strip())=="1": #Upload NEEDED
    print("\nReplacement needed in server")

    
    th.upload_parllel(
        root_gdrive_id=gdrive_authenticator.TARGET_FOLDER_ID,
        local_folder_path=str(path)
    )
    sys.exit()
#