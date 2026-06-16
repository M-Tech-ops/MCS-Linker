for uploading 

def workers_upload_tasks(drive_service,local_file_path,folder_id):
    try:
       tqdm.write(f"[+] Thread scanning directory content: {os.path.basename(local_file_path)}\n")
       upload_folder(drive_service, local_file_path, folder_id)
    except Exception as e:
        tqdm.write(f"[!] Thread error occured while processing:{local_file_path} {e}")

def upload_parallel(local_folder_path, root_gdrive_id, max_workers=5):
    # Force path to string to prevent any object/string type mismatches
    local_folder_path = str(local_folder_path)
    
    # Using a set to ensure we only process each unique folder once
    unique_folders = set()
    folder_tasks = []

    tqdm.write("Mapping structures...")
    main_drive = gdrive_authenticator.authenticate_drive()
    folder_dictionary = {local_folder_path : root_gdrive_id}

    for root, dirs, files in os.walk(local_folder_path):
        current_gdrive_id = folder_dictionary.get(root, root_gdrive_id)

        # Build folder structure synchronously first
        for d in dirs:
            local_dir_path = os.path.join(root, d)
            tqdm.write(f"Verifying folder structure: {d}")
            gdir_id = gdrive_authenticator.upload_or_replace_file(main_drive, local_dir_path, current_gdrive_id)
            folder_dictionary[local_dir_path] = gdir_id

        # If this directory has files, add it to our threaded task queue
        if files and root not in unique_folders:
            unique_folders.add(root)
            # Pass the parent folder path and its matching Google Drive ID
            folder_tasks.append((main_drive, root, current_gdrive_id))
    
    tqdm.write(f"\n[+] Starting multithreaded upload with {max_workers} workers")
    tqdm.write(f"[+] Total folders to process in parallel: {len(folder_tasks)}\n")


    with tqdm(total=len(folder_tasks), desc="Syncing World Folders", unit="folder",file=sys.stderr) as pbar:
        
       
        with open(os.devnull, 'w') as fnull:
        # Everything inside this block that uses standard 'print()' will vanish!
            with redirect_stdout(fnull):
                
                def worker_with_progress(task):
                    drive, path, g_id = task
                    try:
                        workers_upload_tasks(drive, path, g_id)
                    finally:
                        # Even though stdout is muted, pbar writes to stderr, so it still updates!
                        pbar.update(1)
    # Pass the tasks into the thread pool
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Unpacks (drive, root_path, gdrive_id) safely
                list(executor.map(worker_with_progress, folder_tasks))
        # list(executor.map(lambda task: workers_upload_tasks(task[0], task[1], task[2]), folder_tasks))

    tqdm.write(">> All parallel tasks completed successfully\n")
    return


and here is upload_folder

def upload_folder(drive,local_path,folder_id):
    query = f"'{folder_id}' in parents and trashed=false"
    file_list = drive.ListFile({'q': query}).GetList()
    server_map = {item['title']: item for item in file_list}

    if(not os.path.exists(local_path)):
        tqdm.write(f" {local_path}  does'nt exist locally")
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
                tqdm.write(f"Entering folder: {file}")
                upload_folder(drive,local_file_path,file_id)
                # else:
                #     print(f"{file} is already up-to-date")
            else:
                if(gdrive_time<local_time):
                    tqdm.write(f"Uploading file {file}")
                    gdrive_authenticator.upload_or_replace_file(drive,local_file_path,folder_id,file)
                else:
                    tqdm.write(f"File '{file}' is already updated on server.")
        elif exists_on_server==False and exists_locally==True:
             # Store modified date in this 
             if(os.path.isdir(local_file_path)):
                # if(gdrive_time<local_time):
                tqdm.write(f"Entering folder: {file}")
                new_id = gdrive_authenticator.upload_or_replace_file(drive,local_file_path,folder_id)
                upload_folder(drive,local_file_path,new_id)
             else:
                        tqdm.write(f"Uploading file {file}")
                        gdrive_authenticator.upload_or_replace_file(drive,local_file_path,folder_id,file)
 #________________TO TEST_________*
        elif exists_on_server == True and exists_locally == False:
            if(server_item and server_item['mimeType']=='application/vnd.google-apps.folder'):
                file_id = server_item['id']
                tqdm.write(f"Entering Folder {file}")
                upload_folder(drive,local_file_path,file_id)
#To accomplish this we will use threads to successfully get the process to happen faster
            else:
                gdrive_authenticator.upload_or_replace_file(drive,local_file_path,folder_id,filename=file) 


here is my upload_or_replace_file
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
    if file_list and len(file_list)>0:
        existing_file = file_list[0]
        print(f"Found existing file ID {(file_list[0])['id']}")
        print(f"Uploading new '{filename}' to Drive...")
        gfile = drive.CreateFile({
            'id': existing_file['id'], 
            'supportsAllDrives': True,
            'modifiedDate' : local_date_iso
        })
        if(os.path.isdir(local_file_path)):
            print("existing folder\n")
            return gfile['id']
        else:
            gfile.SetContentFile(local_file_path)
            gfile.Upload(param={'supportsAllDrives': True})
    else:
        print(f"No existing file found. Uploading new '{filename}' to Drive...")
        if(os.path.isdir(local_file_path)):
            gfile = drive.CreateFile({
            'title' : filename,
            'parents': [{'id': folder_id}],
            'mimeType': 'application/vnd.google-apps.folder',
            'modifiedDate' : local_date_iso
        })
            gfile.Upload(param={'supportsAllDrives': True})
        else:
            gfile = drive.CreateFile({
                'title': filename,
                'parents': [{'id': folder_id}]
            })
            gfile.SetContentFile(local_file_path)
            gfile.Upload(param={'supportsAllDrives': True})
            print(f">> Upload Complete!\n")
    return gfile['id']



and this is my current downlaod function


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