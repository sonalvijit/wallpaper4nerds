from os import path, listdir, rename
import re
from datetime import datetime

IMAGE_FOLDERS = ["Anime", "Abstract","cgi3d", "Landscape", "Painting", "Pokemon","Real"]
IMAGES_EXTENSION = (".jpg", ".jpeg", ".png", ".webp", ".gif")

def get_files_from_folder(FOLDER:str)->list:
    """
    Return a sorted list of image files from a folder with supported extensions.
    """
    if not path.isdir(FOLDER):
        print(f"Folder not found: {FOLDER}")
        return []
    return sorted([
        f for f in listdir(FOLDER)
        if path.isfile(path.join(FOLDER, f)) and f.lower().endswith(IMAGES_EXTENSION)
    ])

def check_filename(filename:str, parent_folder:str)->bool:
    """
    Check if filename matches the pattern: FOLDER_ddmmyyyySS.ext
    - Case-insensitive folder prefix
    - Exactly 8 digits (date) + 2 digits (serial) after underscore
    """
    name, _ = path.splitext(filename)
    folder_prefix = parent_folder.upper()
    pattern = rf"^{folder_prefix}_\d{{8}}\d{{2}}$"
    return re.fullmatch(pattern, name, re.IGNORECASE) is not None

def change_filename(old_filename:str, parent_folder:str, serial:int)->str:
    """
    Return a new filename in the format: FOLDER_ddmmyyyySS.ext
    """
    today = datetime.now().strftime("%d%m%Y")
    _ , ext = path.splitext(old_filename)
    folder_prefix = parent_folder.upper()
    new_filename = f"{folder_prefix}_{today}{serial:02d}{ext.lower()}"
    return new_filename

def save_filename(old_filename:str, new_filename:str):
    """
    Rename a file from old_filename to new_filename within the same directory.
    """
    try:
        rename(old_filename, new_filename)
        print(f"Renamed: {old_filename} -> {new_filename}")
    except FileNotFoundError:
        print(f"File not found: {old_filename}")
    except FileExistsError:
        print(f"File already exists: {new_filename}")
    except Exception as e:
        print(f"Error renaming file: {e}")

def serialize_filename(parent_folder:str)->int:
    """
    Return next serial number for today's files in format FOLDER_ddmmyyyySS.ext
    If no file exists for today, return 0.
    """
    if not path.isdir(parent_folder):
        print(f"Folder not found: {parent_folder}")
        return 0

    folder_prefix = parent_folder.upper()
    today = datetime.now().strftime("%d%m%Y")
    serials = []

    for filename in listdir(parent_folder):
        name, _ = path.splitext(filename)

        pattern = rf"^{folder_prefix}_{today}(\d{{2}})$"
        match = re.fullmatch(pattern, name, re.IGNORECASE)
        if match:
            try:
                serials.append(int(match.group(1)))
            except ValueError:
                continue

    return max(serials, default=0) + 1

def run():
    for folder_name in IMAGE_FOLDERS:
        a = get_files_from_folder(folder_name)
        for f in a:
            if not check_filename(f, folder_name):
                s1 = change_filename(f, folder_name, serialize_filename(folder_name))
                save_filename(f"{folder_name}/{f}",f"{folder_name}/{s1}")

run()