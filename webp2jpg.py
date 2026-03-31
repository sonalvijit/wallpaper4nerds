from pathlib import Path
from PIL import Image
import os

# List of folders (relative to current working directory)
IMAGE_FOLDERS = [
    "Anime",
    "Abstract",
    "cgi3d",
    "Landscape",
    "Painting",
    "Pokemon",
    "Real",
    "mobile",
    "live wallpaper",
    "Manga_Anime_Cover",
    "OnePiece"
]

def convert_webp_to_jpg(folder_path: Path):
    """Convert all .webp files in the given folder (and subfolders) to .jpg and delete original .webp"""
    count_converted = 0
    count_skipped = 0
    count_errors = 0

    for webp_path in folder_path.glob("**/*.webp"):
        jpg_path = webp_path.with_suffix(".jpg")

        # Skip if jpg already exists (safety check)
        if jpg_path.exists():
            print(f"Already exists, skipping: {jpg_path}")
            count_skipped += 1
            continue

        try:
            with Image.open(webp_path) as img:
                # Convert to RGB if it has transparency/alpha channel
                if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                    img = img.convert("RGB")

                img.save(jpg_path, "JPEG", quality=92)   # quality 92 is good balance of size & quality
                print(f"Converted: {webp_path} → {jpg_path}")

            # Delete the original .webp file after successful save
            os.remove(webp_path)
            print(f"  → deleted original: {webp_path.name}")

            count_converted += 1

        except Exception as e:
            print(f"Error processing {webp_path}: {e}")
            count_errors += 1
            # Do NOT delete if conversion failed

    print(f"\nFolder: {folder_path.name}")
    print(f"  Converted & deleted: {count_converted}")
    print(f"  Skipped (already exist): {count_skipped}")
    print(f"  Errors: {count_errors}\n")


def main():
    root = Path.cwd()

    print("Current working directory:", root)
    print("Looking for folders:", ", ".join(IMAGE_FOLDERS))
    print("-" * 60)

    found_any_folder = False

    for folder_name in IMAGE_FOLDERS:
        folder = root / folder_name

        if not folder.is_dir():
            print(f"Folder not found, skipping: {folder_name}")
            continue

        found_any_folder = True
        print(f"\nProcessing folder: {folder_name}")
        convert_webp_to_jpg(folder)

    if not found_any_folder:
        print("\nNone of the listed folders were found in the current directory.")


if __name__ == "__main__":
    main()