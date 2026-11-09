
import os
import shutil
from PIL import Image

# ==========================================
# CONFIGURATION
# ==========================================

# Folder or drive to scan
ROOT_FOLDER = "D:\\wallpaper4nerds"

# Destination folder
DEST_FOLDER = os.path.join(ROOT_FOLDER, "low resolution")

# Minimum resolution
MIN_WIDTH = 1000
MIN_HEIGHT = 1000

# Supported image extensions
IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".bmp",
    ".webp", ".tiff", ".tif", ".gif"
}

# ==========================================
# INITIALIZATION
# ==========================================

os.makedirs(DEST_FOLDER, exist_ok=True)

moved = 0
skipped = 0

print(f"Scanning: {ROOT_FOLDER}")
print(f"Destination: {DEST_FOLDER}")
print("-" * 50)

# ==========================================
# SCAN ALL FOLDERS
# ==========================================

for current_folder, folders, files in os.walk(ROOT_FOLDER):

    # Avoid scanning the destination folder
    folders[:] = [
        folder for folder in folders
        if os.path.abspath(
            os.path.join(current_folder, folder)
        ) != os.path.abspath(DEST_FOLDER)
    ]

    for filename in files:

        extension = os.path.splitext(filename)[1].lower()

        # Ignore non-image files
        if extension not in IMAGE_EXTENSIONS:
            continue

        source_path = os.path.join(current_folder, filename)

        try:
            # Read image dimensions
            with Image.open(source_path) as img:
                width, height = img.size

            # Move only if BOTH dimensions are below 1000
            if width < MIN_WIDTH and height < MIN_HEIGHT:

                destination_path = os.path.join(
                    DEST_FOLDER, filename
                )

                # Prevent overwriting files
                if os.path.exists(destination_path):

                    name, ext = os.path.splitext(filename)
                    counter = 1

                    while os.path.exists(destination_path):
                        destination_path = os.path.join(
                            DEST_FOLDER,
                            f"{name}_{counter}{ext}"
                        )
                        counter += 1

                # Move image
                shutil.move(source_path, destination_path)

                print(
                    f"MOVED: {filename} "
                    f"({width} x {height})"
                )

                moved += 1

        except Exception as e:
            print(f"SKIPPED: {source_path}")
            print(f"Reason: {e}")

            skipped += 1

# ==========================================
# SUMMARY
# ==========================================

print("\n" + "=" * 50)
print("SCAN COMPLETED")
print("=" * 50)

print(f"Images moved   : {moved}")
print(f"Images skipped : {skipped}")
print(f"Destination    : {DEST_FOLDER}")
