import threading 
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os
from concurrent.futures import ThreadPoolExecutor
from minecraft_sync.gdrive_authenticator import upload_or_replace_file
auth_lock = threading.Lock()

def authenticate_drive():
    print("Authenticating with Google Drive...")
    gauth =  GoogleAuth()
    # gauth.DEFAULT_SETTINGS['oauth_scope'] = ['https://googleapis.com']
    gauth.LoadCredentialsFile("mycreds.txt")
    # This will open a web browser the first time to ask for your permission.
    # It creates a 'credentials.json' file so you don't have to log in every time.
    if gauth.credentials is None:
        # If no saved credentials exist, log in via browser
        print("No saved credentials found. Opening browser...")
        gauth.GetFlow()
        gauth.flow.scope = 'https://www.googleapis.com/auth/drive'
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

def workers_upload_tasks(local_file_path,folder_id):
    try:
        thread_drive = authenticate_drive()

        upload_or_replace_file(thread_drive , local_file_path , folder_id)
    except Exception as e:
        print(f"[!] Thread error occured while processing:{local_file_path} {e}")

def upload_parllel(local_folder_path,root_gdrive_id,max_workers=5):
    upload_tasks = []

    print("Mapping structures")

    main_drive = authenticate_drive()
    folder_dictionary = {local_folder_path : root_gdrive_id}

    for root,dirs,files in os.walk(local_folder_path):
        cuurrent_gdrive_id = folder_dictionary[root]

        for d in dirs:
            local_dir_path = os.path.join(root,d)
            print("Verifying folder structure: {d}")
            gdir_id = upload_or_replace_file(main_drive,local_dir_path,cuurrent_gdrive_id)
            folder_dictionary[local_dir_path] = gdir_id


        for f in files:
            full_local_path = os.path.join(root,f)
            upload_tasks.append((full_local_path,cuurrent_gdrive_id))
    
    print(f"\n[+] Starting multithreaded upload with {max_workers} workers")
    print(f"\n[+] Total files to transer: {len(upload_tasks)}\n")

    with ThreadPoolExecutor(max_workers= max_workers) as  executor:
        executor.map(lambda task : workers_upload_tasks(task[0],task[1]),upload_tasks)

        print(">>All parllel tasks completed successfully")