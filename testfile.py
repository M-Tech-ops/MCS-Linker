import os 
from File_accesser import Find_mine_world

roaming = Find_mine_world()
if(roaming is None):
    print("Cannot find minecraft folder")
    exit(1)
worldname = "Samesoea"
path = roaming / ".minecraft" / "saves"  / worldname
local = os.listdir(path)
print(local)