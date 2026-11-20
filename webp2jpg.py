from pathlib import Path
from PIL import Image
import os
from dotenv import load_dotenv

load_dotenv()

IMAGE_FOLDERS = os.getenv("IMAGE_FOLDERS", "").split(",")


def convert_webp_to_jpg(folder_path: Path):
    """Convert WebP files to JPG and print only successful conversions."""

    converted_count = 0

    for webp_path in folder_path.glob("**/*.webp"):
        jpg_path = webp_path.with_suffix(".jpg")

        # Skip if JPG already exists
        if jpg_path.exists():
            continue

        try:
            with Image.open(webp_path) as img:
                if img.mode != "RGB":
                    img = img.convert("RGB")

                img.save(jpg_path, "JPEG", quality=92)

            # Delete original only after successful conversion
            webp_path.unlink()

            print(f"Converted: {webp_path} → {jpg_path}")
            converted_count += 1

        except Exception:
            pass

    return converted_count


def main():
    root = Path.cwd()
    total_converted = 0

    for folder_name in IMAGE_FOLDERS:
        folder_name = folder_name.strip()

        if not folder_name:
            continue

        folder = root / folder_name

        if folder.is_dir():
            total_converted += convert_webp_to_jpg(folder)

    # Print only when nothing was converted
    if total_converted == 0:
        print("No changes detected")


if __name__ == "__main__":
    main()