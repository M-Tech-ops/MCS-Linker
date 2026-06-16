import os
from pathlib import Path
from datetime import datetime
import subprocess
import shutil

import minecraft_sync.gdrive_authenticator as gdrive_authenticator

# ===== CONFIGURATION SECTION =====
# [CHANGE THESE VALUES FOR YOUR SETUP]

WORLD_NAME = "Samesoea"  # ← CHANGE THIS to your world name

# Get script directory (for relative paths)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Relative paths (works on any computer)

SERVER_WORLD_BACKUP = os.path.join(SCRIPT_DIR, "Remote_Files")   # In project folder
EXE_COMPARATOR = os.path.join(SCRIPT_DIR, "build", "Comparator.exe")

# Google Drive
GDRIVE_FOLDER_ID = gdrive_authenticator.TARGET_FOLDER_ID


# ===== END CONFIGURATION =====
def  Find_mine_world():
    roaming = (os.getenv("APPDATA"))
    if(roaming is None):
        print("Error Appdata variable not found")
        return None
    return Path(roaming)
 # Finds .minecraft folder
roaming = Find_mine_world()
if(roaming is None):
    print("Cannot find minecraft folder")
    exit(1)
LOCAL_MINECRAFT_SAVES = roaming  / ".minecraft" / "saves"  
# Build full paths using worldname
LOCAL_WORLD = os.path.join(LOCAL_MINECRAFT_SAVES, WORLD_NAME)
SERVER_WORLD = os.path.join(SERVER_WORLD_BACKUP, WORLD_NAME)

def get_world_structure(world_path):
    """Map entire world structure for syncing"""
    world_path = Path(world_path)
    structure = {}
    
    structure['level.dat'] = {
        'local': world_path / 'level.dat',
        'type': 'metadata',
        'compare_method': 'NBT_PARSER',
        'description': 'World metadata - LastPlayed, Ticks, etc'
    }
    
    structure['level.dat_old'] = {
        'local': world_path / 'level.dat_old',
        'type': 'metadata_backup',
        'compare_method': 'TIMESTAMP'
    }
    
    dimensions = {
        'overworld': 'dimensions/minecraft/overworld/region',
        'nether': 'dimensions/minecraft/the_nether/region',
        'end': 'dimensions/minecraft/the_end/region'
    }
    
    for dim_name, dim_path in dimensions.items():
        full_path = world_path / dim_path
        if full_path.exists():
            structure[f'{dim_name}_chunks'] = {
                'local': full_path,
                'type': 'chunk_region',
                'compare_method': 'FOLDER_TIMESTAMP',
                'description': f'{dim_name.upper()} region files (.mca)'
            }
    
    world_data = world_path / 'data/minecraft'
    if world_data.exists():
        structure['world_data'] = {
            'local': world_data,
            'type': 'world_data',
            'compare_method': 'FOLDER_TIMESTAMP',
            'description': 'Game rules, weather, scoreboard, etc'
        }
    
    for dim_name, dim_path in dimensions.items():
        dim_data_path = world_path / f'dimensions/minecraft/{dim_name}/data/minecraft'
        if dim_data_path.exists():
            structure[f'{dim_name}_data'] = {
                'local': dim_data_path,
                'type': 'dimension_data',
                'compare_method': 'FOLDER_TIMESTAMP',
                'description': f'{dim_name.upper()} world data'
            }
    
    poi_path = world_path / 'dimensions/minecraft/overworld/poi'
    if poi_path.exists():
        structure['poi'] = {
            'local': poi_path,
            'type': 'poi_data',
            'compare_method': 'FOLDER_TIMESTAMP',
            'description': 'Points of Interest'
        }
    
    entities_path = world_path / 'dimensions/minecraft/overworld/entities'
    if entities_path.exists():
        structure['entities'] = {
            'local': entities_path,
            'type': 'entities',
            'compare_method': 'FOLDER_TIMESTAMP',
            'description': 'Entity data (mobs, etc)'
        }
    
    players_path = world_path / 'players'
    if players_path.exists():
        player_data = players_path / 'data'
        if player_data.exists():
            structure['player_data'] = {
                'local': player_data,
                'type': 'player_data',
                'compare_method': 'FOLDER_TIMESTAMP',
                'description': 'Player inventory, position, etc'
            }
        
        advancements = players_path / 'advancements'
        if advancements.exists():
            structure['advancements'] = {
                'local': advancements,
                'type': 'advancements',
                'compare_method': 'FOLDER_TIMESTAMP',
                'description': 'Player achievements/advancements'
            }
        
        stats = players_path / 'stats'
        if stats.exists():
            structure['player_stats'] = {
                'local': stats,
                'type': 'player_stats',
                'compare_method': 'FOLDER_TIMESTAMP',
                'description': 'Player statistics'
            }
    
    return structure

def get_latest_modification_time(path):
    """Get the latest modification time in a file or folder"""
    path = Path(path)
    
    if path.is_file():
        return os.path.getmtime(path)
    
    latest = 0
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                mod_time = os.path.getmtime(file_path)
                if mod_time > latest:
                    latest = mod_time
            except:
                pass
    
    return latest

def upload_to_gdrive(drive, local_path, folder_id, file_name):
    """Upload to Google Drive"""
    print(f"  Uploading {file_name}...")
    result = gdrive_authenticator.upload_or_replace_file(
        drive=drive,
        local_file_path=str(local_path),
        folder_id=folder_id,
        filename=file_name
    )
    if result:
        print(f"  ✓ Upload successful")
    else:
        print(f"  ✗ Upload failed")
    return result

def download_from_gdrive(drive, remote_file_name, local_path, folder_id):
    """Download from Google Drive"""
    print(f"  Downloading {remote_file_name}...")
    
    os.makedirs(os.path.dirname(str(local_path)), exist_ok=True)
    
    result = gdrive_authenticator.download_file_from_folder(
        drive=drive,
        filename=remote_file_name,
        folder_id=folder_id,
        save_path=str(local_path)
    )
    if result:
        print(f"  ✓ Download successful")
    else:
        print(f"  ✗ Download failed")
    return result

def sync_file(drive, file_key, local_info, server_info, decision, folder_id):
    """Execute sync for a single file"""
    local_path = local_info['local']
    file_name = file_key
    
    if decision == 'UPLOAD':
        print(f"\n  ⬆️  UPLOADING: {file_key}")
        upload_to_gdrive(drive, local_path, folder_id, file_name)
    
    elif decision == 'DOWNLOAD':
        print(f"\n  ⬇️  DOWNLOADING: {file_key}")
        download_from_gdrive(drive, file_name, local_path, folder_id)
    
    elif decision == 'SKIP':
        print(f"\n  ✓ {file_key} is up to date - skipping")

def compare_worlds(local_world_path, server_world_path, exe_comparator_path, drive):
    """Compare local and server worlds"""
    
    local_structure = get_world_structure(local_world_path)
    server_structure = get_world_structure(server_world_path)
    
    print("\n" + "="*70)
    print(f"MINECRAFT WORLD SYNC: {WORLD_NAME}")
    print("="*70)
    
    sync_decisions = {}
    
    for file_key, local_info in local_structure.items():
        print(f"\n[{file_key.upper()}]")
        print(f"  Type: {local_info['type']}")
        print(f"  Compare Method: {local_info['compare_method']}")
        
        if file_key not in server_structure:
            print(f"  Status: NOT ON SERVER")
            print(f"  Decision: ⬆️  UPLOAD")
            sync_decisions[file_key] = 'UPLOAD'
            continue
        
        server_info = server_structure[file_key]
        local_path = local_info['local']
        server_path = server_info['local']
        
        if not local_path.exists():
            print(f"  Status: NOT ON LOCAL")
            print(f"  Decision: ⬇️  DOWNLOAD")
            sync_decisions[file_key] = 'DOWNLOAD'
            continue
        
        compare_method = local_info['compare_method']
        
        if compare_method == 'NBT_PARSER':
            print(f"  Local Path:  {local_path}")
            print(f"  Server Path: {server_path}")
            print(f"  ⚠️  REQUIRES NBT PARSING")
            
            print(f"\n  Running NBT comparator...")
            env = os.environ.copy()
            env['PATH'] = r"C:\msys64\ucrt64\bin;" + env['PATH']
            
            result = subprocess.run(
                [exe_comparator_path, str(local_path), str(server_path)],
                capture_output=True,
                text=True,
                env=env
            )
            
            nbt_result = result.stdout.strip()
            print(f"  NBT Comparator output: {nbt_result}")
            
            if nbt_result == "0":
                print(f"  Decision: ⬇️  DOWNLOAD (server is newer)")
                sync_decisions[file_key] = 'DOWNLOAD'
            elif nbt_result == "1":
                print(f"  Decision: ⬆️  UPLOAD (local is newer)")
                sync_decisions[file_key] = 'UPLOAD'
            elif nbt_result == "-1":
                print(f"  Decision: ✓ NO CHANGE NEEDED")
                sync_decisions[file_key] = 'SKIP'
        
        elif compare_method == 'TIMESTAMP':
            local_time = get_latest_modification_time(local_path)
            server_time = get_latest_modification_time(server_path)
            
            local_date = datetime.fromtimestamp(local_time).strftime('%Y-%m-%d %H:%M:%S')
            server_date = datetime.fromtimestamp(server_time).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"  Local Time:  {local_date}")
            print(f"  Server Time: {server_date}")
            
            if local_time == server_time:
                print(f"  Decision: ✓ NO CHANGE NEEDED")
                sync_decisions[file_key] = 'SKIP'
            elif local_time > server_time:
                print(f"  Decision: ⬆️  UPLOAD")
                sync_decisions[file_key] = 'UPLOAD'
            else:
                print(f"  Decision: ⬇️  DOWNLOAD")
                sync_decisions[file_key] = 'DOWNLOAD'
        
        elif compare_method == 'FOLDER_TIMESTAMP':
            local_time = get_latest_modification_time(local_path)
            server_time = get_latest_modification_time(server_path)
            
            local_date = datetime.fromtimestamp(local_time).strftime('%Y-%m-%d %H:%M:%S')
            server_date = datetime.fromtimestamp(server_time).strftime('%Y-%m-%d %H:%M:%S')
            
            print(f"  Local Folder:  {local_path}")
            print(f"  Latest File:   {local_date}")
            print(f"  Server Folder: {server_path}")
            print(f"  Latest File:   {server_date}")
            
            if local_time == server_time:
                print(f"  Decision: ✓ NO CHANGE NEEDED")
                sync_decisions[file_key] = 'SKIP'
            elif local_time > server_time:
                print(f"  Decision: ⬆️  UPLOAD ALL FILES")
                sync_decisions[file_key] = 'UPLOAD'
            else:
                print(f"  Decision: ⬇️  DOWNLOAD ALL FILES")
                sync_decisions[file_key] = 'DOWNLOAD'
    
    return sync_decisions

def execute_sync(drive, sync_decisions, local_structure, server_structure, folder_id):
    """Execute the actual sync"""
    print("\n" + "="*70)
    print("EXECUTING SYNC...")
    print("="*70)
    
    for file_key, decision in sync_decisions.items():
        if decision == 'SKIP':
            continue
        
        local_info = local_structure[file_key]
        server_info = server_structure[file_key]
        
        print(f"\n[{file_key}] {decision}")
        sync_file(drive, file_key, local_info, server_info, decision, folder_id)

# ===== MAIN EXECUTION =====
if __name__ == "__main__":


    
    print(f"Minecraft World Sync Tool")
    print(f"World: {WORLD_NAME}")
    print(f"Local:  {LOCAL_WORLD}")
    print(f"Server: {SERVER_WORLD}")
    
    # Verify paths exist
    if not os.path.exists(LOCAL_WORLD):
        print(f"\n✗ Error: Local world not found at {LOCAL_WORLD}")
        print(f"  Make sure WORLD_NAME is correct and Minecraft is installed")
        exit(1)
    
    # Create server folder if it doesn't exist
    if not os.path.exists(SERVER_WORLD):
        print(f"\n⚠️  Server folder doesn't exist yet: {SERVER_WORLD}")
        print(f"   Creating folder...")
        os.makedirs(SERVER_WORLD, exist_ok=True)


    
    # Authenticate with Google Drive
    print("\nAuthenticating with Google Drive...")
    drive = gdrive_authenticator.authenticate_drive()
    
    # Get structures
    local_structure = get_world_structure(LOCAL_WORLD)
    server_structure = get_world_structure(SERVER_WORLD)
    
    # Compare
    sync_decisions = compare_worlds(LOCAL_WORLD, SERVER_WORLD, EXE_COMPARATOR, drive)
    
    # Ask for confirmation
    print("\n" + "="*70)
    print("Ready to sync. Execute? (yes/no)")
    user_input = input("> ").strip().lower()
    
    if user_input == 'yes':
        execute_sync(drive, sync_decisions, local_structure, server_structure, GDRIVE_FOLDER_ID)
        print("\n✓ Sync complete!")
    else:
        print("Sync cancelled.")