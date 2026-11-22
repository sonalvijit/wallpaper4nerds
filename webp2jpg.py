
from pathlib import Path
from PIL import Image
import os
from dotenv import load_dotenv
from colorama import Fore, Style, init

load_dotenv()
init(autoreset=True)

C = Fore
S = Style

IMAGE_FOLDERS = [
    folder.strip()
    for folder in os.getenv("IMAGE_FOLDERS", "").split(",")
    if folder.strip()
]


def separator():
    print(f"{C.LIGHTBLACK_EX}{'─' * 58}")


def convert_webp_to_jpg(folder_path: Path):
    """Convert WebP files to JPG and return successful conversions."""

    converted_files = []

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

            converted_files.append((webp_path, jpg_path))

        except Exception as e:
            print(
                f"{C.RED}[ERROR] {S.RESET_ALL}"
                f"{webp_path.name}: {e}"
            )

    return converted_files


def main():

    root = Path.cwd()

    for folder_name in IMAGE_FOLDERS:

        folder = root / folder_name

        if not folder.is_dir():
            continue

        converted_files = convert_webp_to_jpg(folder)

        # Display folder information only if changes occurred
        if converted_files:

            print(
                f"\n{C.YELLOW}{S.BRIGHT}"
                f"📁 Folder: {folder_name}"
            )

            separator()

            for webp_path, jpg_path in converted_files:

                print(
                    f"{C.GREEN}[CONVERTED] {S.RESET_ALL}"
                    f"{webp_path.name} → "
                    f"{C.CYAN}{jpg_path.name}"
                )


if __name__ == "__main__":
    main()
