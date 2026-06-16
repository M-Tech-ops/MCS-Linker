# Minecraft Server Link 🎮

> Sync your Minecraft world with friends using Google Drive
## The Problem

You and your friends want to play on a Minecraft server together, but:
- You need someone to host the server 24/7
- You can't progress alone while waiting for the server to be online
- Hosting services cost money or have uptime limitations
  

## The Solution
**Minecraft Server Link** lets you play on your **local world** while automatically syncing changes to a **shared server world** via Google Drive.

**Sounds good?**
Come then lets set it up for good
***These steps are to be followed by a single person***


## What You Need

- Minecraft Java Edition installed
- One person with a Google Account
- Friends to play with! 👥

## Quick Start

### For the Admin (Person Setting Up)

#### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Click "Create Project"
3. Name it "Minecraft Server Link"
4. Click Create

#### Step 2: Enable Google Drive API

1. Search for "Google Drive API"
2. Click the result
3. Click "Enable"

#### Step 3: Create OAuth Credentials

1. Go to "Credentials" (left sidebar)
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. Choose "Desktop application"
4. Click Create
5. Click the download icon

Send the `credentials.json` file to all your friends via email/Discord/etc.
and then ask them to put it inside the same folder they put the File_accesser.py and then run it
Then login with the account you have been given access to and follow the next steps

#### Step 4: Upload World to Drive

1. Go to google drive and upload your minecraft world folder(**Typically found in %appdata%/.minecraft/saves/YOUR_WORLD**)
2. After uploading Right click and share 
3. In Add section enter your friends email
4. Give them editor access
5. And Share the folder link with them

#### Step 5: Download our package release(Executable)
1. Download and extract it inside a single folder
2. Edit the config.json file and put your drive link and worldname inside it in double commas ""
3. Click the script and your world will be synced to the one in the drive
4. Then download the Mod *worldsync latest release* from [WorldSync by ChillestOrange](https://github.com/ChillestOrange/worldsync).
5. Put the extracted jar files into ` %appdata% / .minecraft / mods `
6. Run minecraft for the config file to get created.
7. Go to  `%appdata% / .minecraft / config / worldsync.json5 ` and add the appropriate paths into it.
> ***In the config file remember to give the directory where your File_accesser.exe is located not the full path!***

### Step 6:
1: Open minecraft with your launcher

2: Choose the desired version for your minecraft and ***USE FABRIC***

3: Then click on the world you want to play and it will start syncing!


### IF ITS YOUR FIRST EVER TIME PLAYING ON THE WORLD AND YOUR FRIEND HAS ALREADY UPLOADED THE WORLD TO GOOGLE DRIVE JUST RUN THE SCRIPT ONCE
> `It will fetch the world automatically depending on the config file`


# FAQ
> Does it work in offline mode?
 Yes it does!
# HAVE FUN!
