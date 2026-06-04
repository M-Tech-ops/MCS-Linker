# from pyDrive2.auth import GoogleAuth
# from pyDrive2.drive import GoogleDrive
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive 
import os
from datetime import datetime,timezone
import json
with open("config.json",'r') as file:
    config = json.load(file)

  # Put your actual Google Drive Folder ID here
TARGET_FOLDER_ID = config['TARGET_FOLDER_ID']
TARGET_FOLDER_ID = TARGET_FOLDER_ID.strip("https://drive.google.com/drive/u/0/folders/")

    # 1. This dictates exactly where the file lands on your computer
local_destination = "./Remote_Files"
    
def authenticate_drive():
    print("Authenticating with Google Drive...")
    gauth = GoogleAuth()
    gauth.LoadCredentialsFile("mycreds.txt")
    # This will open a web browser the first time to ask for your permission.
    # It creates a 'credentials.json' file so you don't have to log in every time.
    if gauth.credentials is None:
        # If no saved credentials exist, log in via browser
        print("No saved credentials found. Opening browser...")
        gauth.GetFlow()
        gauth.flow.params.update({'access_type': 'offline'})
        gauth.flow.params.update({'approval_prompt':'force'})
        gauth.LocalWebserverAuth()

    elif gauth.access_token_expired:
        # If credentials exist but expired, refresh them automatically
        print("Credentials expired. Refreshing...")
        gauth.Refresh()
    else:
        # If credentials are valid, authorize them
        gauth.Authorize()
    # 2. Save the credentials for next time
    gauth.SaveCredentialsFile("mycreds.txt")
    
    return GoogleDrive(gauth)
def download_file_from_folder(drive, filename, folder_id, save_path):
    print(f"Searching for '{filename}' inside specific folder...")
    
    # THE UPGRADE: We added "'folder_id' in parents" to the SQL-like query
    query = f"title='{filename}' and '{folder_id}' in parents and trashed=false"
    
    file_list = drive.ListFile({'q': query}).GetList()
    
    if not file_list:
        print(f"[!] Error: Could not find '{filename}' in that specific folder.")
        return False
    
    folder_directory = os.path.dirname(save_path)
    os.makedirs(folder_directory,exist_ok=True)

    target_file = file_list[0]
    print(f">> Found '{filename}' (ID: {target_file['id']})")
    
    target_file.GetContentFile(save_path)
    print(">> Download Complete!\n")
    return True

def download_file_by_name(drive, filename, save_path):
    print(f"Searching for '{filename}' in Drive...")
    
    # 1. Query the Drive database for the exact filename
    # (trashed=false ensures we don't grab something from the recycle bin)
    query = f"title='{filename}' and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()
    
    if not file_list:
        print(f"[!] Error: Could not find '{filename}' in your Google Drive.")
        return False
        
    # 2. Grab the first result's ID (Assuming you don't have 10 files named level.dat!)
    target_file = file_list[0]
    file_id = target_file['id']
    print(f">> Found '{filename}' (ID: {file_id})")
    
    # 3. Download the binary payload!
    print(f"Downloading to {save_path}...")
    target_file.GetContentFile(save_path)
    print(">> Download Complete!\n")
    return True

def upload_or_replace_file(drive, local_file_path, folder_id, filename=None):
    """
    Upload a local file to Google Drive folder, replacing if it exists
    
    Args:
        drive: GoogleDrive object
        local_file_path: Path to local file (e.g., "./Local_Files/level.dat")
        folder_id: Google Drive folder ID where file should go
        filename: Name for file on Drive (defaults to local filename)
    """
    
    # Get filename if not provided
    if not filename:
        filename = os.path.basename(local_file_path)
    
    # Check if file exists locally
    if not os.path.exists(local_file_path):
        print(f"[!] Error: Local file '{local_file_path}' not found")
        return False
    

    print(f"Searching for existing '{filename}' in Drive folder...")
    
    # Check if file already exists on Drive
    query = f"title='{filename}' and '{folder_id}' in parents and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()
    local_timestamp = os.path.getmtime(local_file_path)
    local_date_iso = datetime.fromtimestamp(local_timestamp, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + 'Z'
    if file_list:
        # File exists - delete old version
       if len(file_list) > 0:
        print(f"Found {len(file_list)} existing file(s). Deleting...")
        for f in file_list:
            f.Delete()
            print(f"  Deleted: {f['id']}")
    # Upload new file
    print(f"Uploading new '{filename}' to Drive...")
    gfile = drive.CreateFile({
        'title': filename,
        'parents': [{'id': folder_id}]
    })
    gfile.SetContentFile(local_file_path)
    gfile.Upload()
    print(f">> Upload Complete!\n")
    gfile['modifiedDate']=local_date_iso
    try:
        gfile.UpdateMetadata()
        
        print(f"Success in uploading correct time")
    except Exception as e:
        print(f"Failed to set correct timestamps {e}")
    return True
# --- MAIN EXECUTION ---
if __name__ == "__main__":
    drive = authenticate_drive()
    
  
    # download_file_from_folder(
    #     drive=drive, 
    #     filename="level.dat", 
    #     folder_id=TARGET_FOLDER_ID,
    #     save_path=local_destination # <--- This is where it goes!
    # )
#     upload_or_replace_file(
#         drive= drive,
#         local_file_path=local_destination,
#         folder_id=TARGET_FOLDER_ID,
#         filename="level.dat"
#     )
# download_folder(drive=drive,local_path=local_destination,folder_id=TARGET_FOLDER_ID)