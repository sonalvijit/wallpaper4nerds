import os
import re
from datetime import datetime

# === Configuration ===
IMAGE_FOLDERS = ["Anime","cgi3d","Landscape","Painting","Pokemon"]
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif")

# === Helpers ===
def is_serialized_filename(filename, folder_prefix):
    """Check if filename matches FOLDER_ddmmyyyySS pattern."""
    pattern = rf"^{folder_prefix}_\d{{8}}\d{{2}}$"
    name, _ = os.path.splitext(filename)
    return re.fullmatch(pattern, name, flags=re.IGNORECASE) is not None

def extract_serials_for_today(files, folder_prefix, today_prefix):
    """Extract serial numbers for files from today with the given folder prefix."""
    serials = []
    for f in files:
        name, _ = os.path.splitext(f)
        if name.startswith(f"{folder_prefix}_{today_prefix}") and len(name) == len(folder_prefix) + 11:
            try:
                serial = int(name[-2:])
                serials.append(serial)
            except ValueError:
                continue
    return serials

def rename_images_in_folder(folder):
    """Rename non-serialized image files in the folder to FOLDER_ddmmyyyySS.ext"""
    if not os.path.isdir(folder):
        print(f"❌ Skipping: {folder} (not found)")
        return

    folder_prefix = folder.upper()
    today = datetime.now().strftime("%d%m%Y")

    files = os.listdir(folder)
    images = [f for f in files if f.lower().endswith(IMAGE_EXTS)]

    today_serials = extract_serials_for_today(images, folder_prefix, today)
    next_serial = max(today_serials, default=0) + 1

    renamed = 0

    for filename in images:
        name, ext = os.path.splitext(filename)

        if is_serialized_filename(name, folder_prefix) and name.startswith(f"{folder_prefix}_{today}"):
            continue  # Already correctly named today → skip

        new_name = f"{folder_prefix}_{today}{next_serial:02d}{ext.lower()}"
        src = os.path.join(folder, filename)
        dst = os.path.join(folder, new_name)

        os.rename(src, dst)
        print(f"✅ {folder}/ {filename} → {new_name}")
        next_serial += 1
        renamed += 1

    if renamed == 0:
        print(f"ℹ️ No files renamed in {folder}")
    else:
        print(f"🔁 Renamed {renamed} file(s) in {folder}")

# === Runner ===
def rename_all():
    for folder in IMAGE_FOLDERS:
        rename_images_in_folder(folder)

if __name__ == "__main__":
    rename_all()
