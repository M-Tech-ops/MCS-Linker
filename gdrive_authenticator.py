# from pyDrive2.auth import GoogleAuth
# from pyDrive2.drive import GoogleDrive
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive 
import os

def authenticate_drive():
    print("Authenticating with Google Drive...")
    gauth = GoogleAuth()
    
    # This will open a web browser the first time to ask for your permission.
    # It creates a 'credentials.json' file so you don't have to log in every time.
    gauth.LocalWebserverAuth() 
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

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    drive = authenticate_drive()
    
    # Put your actual Google Drive Folder ID here
    TARGET_FOLDER_ID = "170RmO3RtiPrtwo6P3EvOORcw7w7kNAUa" 
    
    # 1. This dictates exactly where the file lands on your computer
    local_destination = "./Remote_Files/level.dat"
    
    download_file_from_folder(
        drive=drive, 
        filename="level.dat", 
        folder_id=TARGET_FOLDER_ID,
        save_path=local_destination # <--- This is where it goes!
    )