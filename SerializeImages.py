from os import path, listdir, rename, walk
import re
from datetime import datetime

IMAGE_FOLDERS = ["Anime", "Abstract","cgi3d", "Landscape", "Painting", "Pokemon","Real","mobile","live wallpaper","Manga_Anime_Cover","Manga Panels","OnePiece","fah","coc","moco","Valorant","Idols"]
IMAGES_EXTENSION = (".jpg", ".jpeg", ".png", ".webp", ".gif","jfif","mp4")

# def get_files_from_folder(FOLDER:str)->list:
#     """
#     Return a sorted list of image files from a folder with supported extensions.
#     """
#     if not path.isdir(FOLDER):
#         print(f"Folder not found: {FOLDER}")
#         return []
#     return sorted([
#         f for f in listdir(FOLDER)
#         if path.isfile(path.join(FOLDER, f)) and f.lower().endswith(IMAGES_EXTENSION)
#     ])

def get_files_from_folder(FOLDER: str) -> list:
    """
    Return a sorted list of image file paths from a folder and all its subfolders.
    """
    if not path.isdir(FOLDER):
        print(f"Folder not found: {FOLDER}")
        return []

    image_files = []

    for root, _, files in walk(FOLDER):
        for file in files:
            if file.lower().endswith(IMAGES_EXTENSION):
                image_files.append(path.join(root, file))

    return sorted(image_files)

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

# def run():
#     for folder_name in IMAGE_FOLDERS:
#         a = get_files_from_folder(folder_name)
#         for f in a:
#             if not check_filename(path.basename(f), folder_name):
#                 s1 = change_filename(f, folder_name, serialize_filename(folder_name))
#                 save_filename(f"{folder_name}/{f}",f"{folder_name}/{s1}")

def run():
    for folder_name in IMAGE_FOLDERS:
        serial = serialize_filename(folder_name)

        for f in get_files_from_folder(folder_name):
            filename = path.basename(f)

            if check_filename(filename, folder_name):
                continue

            new_name = change_filename(filename, folder_name, serial)
            serial += 1

            save_filename(
                f,
                path.join(path.dirname(f), new_name)
            )

# def run():
#     for folder_name in IMAGE_FOLDERS:
#         files = get_files_from_folder(folder_name)

#         for f in files:
#             filename = path.basename(f)

#             if not check_filename(filename, folder_name):
#                 serial = serialize_filename(folder_name)
#                 new_name = change_filename(filename, folder_name, serial)

#                 old_path = f
#                 new_path = path.join(path.dirname(f), new_name)

#                 save_filename(old_path, new_path)
                
run()