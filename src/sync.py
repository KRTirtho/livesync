#!/usr/bin/python

import os
import re
import shutil
import sys
import time
import stat
from operator import is_not
from functools import partial
from pathlib import Path

os.system("mount -o remount,rw /run/miso/bootmnt/")
time.sleep(1)

user = os.getenv('USER', "manjaro")

firefoxDir = "/home/"+user+"/.mozilla/firefox/" # ~/.mozilla/firefox

systemMozIni = firefoxDir+"installs.ini"
persistedMozIni = "/run/miso/bootmnt/persists/installs.ini"

systemMozProfilesIni = firefoxDir+"profiles.ini"
persistedMozProfilesIni = "/run/miso/bootmnt/persists/profiles.ini"

def findFolderNameFromIni(iniFile):
    contents = Path(iniFile).read_text()
    return re.findall("Default=[\w\.\-]+", contents)[0].replace("Default=", "")

mountPersistFolder = "/run/miso/bootmnt/persists/"
persistMozFolderName = findFolderNameFromIni(persistedMozIni)
mountFolder = os.path.join(mountPersistFolder, persistMozFolderName)
print("MOUNT FOLDER: ", mountFolder)

mozPersistedFolderName = os.path.join(firefoxDir, persistMozFolderName)
print("MOZILLA NEW CONF FOLDER: ", mozPersistedFolderName)

confFiles = ["/home/manjaro/.config/ktimezonedrc", "/home/manjaro/.config/konsolerc", "/home/manjaro/.config/kglobalshortcutsrc", "/etc/pacman.d/mirrorlist"]

permissions = stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH | stat.S_IWUSR | stat.S_IWGRP | stat.S_IXUSR | stat.S_IXGRP

def copyPersisted():
    shutil.copytree(mountFolder, mozPersistedFolderName, ignore_dangling_symlinks=True, dirs_exist_ok=True)
    shutil.copy(persistedMozIni, firefoxDir)
    shutil.copy(persistedMozProfilesIni, firefoxDir)
    for src in [systemMozIni, systemMozProfilesIni, mozPersistedFolderName, firefoxDir]:
        shutil.chown(src, user=user, group=user)
        if os.path.isdir(src): # os.walk only for dirs
            for dirpath, dirnames, filenames in os.walk(src):
                shutil.chown(dirpath, user=user, group=user)
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if not os.path.islink(filepath): # symlinks can't work with shutils
                        shutil.chown(filepath, user=user, group=user)

    # copying configuration files
    for file in confFiles:
        dest =  "/".join(file.split("/")[:-1])
        src = os.path.join(mountPersistFolder, file.split("/")[-1])
        print("copying from", src, "to", dest)
        shutil.copy(src, dest)

def copySystem():
    shutil.copytree(mozPersistedFolderName, mountFolder, ignore_dangling_symlinks=True, dirs_exist_ok=True)
    shutil.copy(systemMozIni, mountPersistFolder)
    shutil.copy(systemMozProfilesIni, mountPersistFolder)

    for file in confFiles:
        print("copying from", file, "to", mountPersistFolder )
        shutil.copy(file, mountPersistFolder)

argv1 = sys.argv[1:][0] if  len(sys.argv[1:]) > 0 else None
if(argv1=="start"):
    print("START | Syncing previously stored persistance....")
    copyPersisted()
elif(argv1=="end"):
    print("END | Persisting used system configuratoins....")
    copySystem()
else:
    print("Use 'start' to sync")
    print("Use 'end' to persist")

