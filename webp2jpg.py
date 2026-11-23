
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


def convert_images_to_jpg(folder_path: Path, extensions):
    """Convert supported image formats to JPG and return successful conversions."""

    converted_files = []

    for extension in extensions:

        for image_path in folder_path.glob(f"**/*.{extension}"):

            jpg_path = image_path.with_suffix(".jpg")

            # Skip if JPG already exists
            if jpg_path.exists():
                continue

            try:
                with Image.open(image_path) as img:

                    # GIF: Convert only the first frame
                    if extension == "gif":
                        img.seek(0)

                    # Convert image to RGB
                    if img.mode != "RGB":
                        img = img.convert("RGB")

                    img.save(jpg_path, "JPEG", quality=92)

                # Delete original only after successful conversion
                image_path.unlink()

                converted_files.append(
                    (extension.upper(), image_path, jpg_path)
                )

            except Exception as e:
                print(
                    f"{C.RED}[ERROR] {S.RESET_ALL}"
                    f"{image_path.name}: {e}"
                )

    return converted_files


def main():

    root = Path.cwd()

    extensions = ["webp", "jfif"]

    for folder_name in IMAGE_FOLDERS:

        folder = root / folder_name

        if not folder.is_dir():
            continue

        converted_files = convert_images_to_jpg(folder, extensions)

        # Display folder information only if changes occurred
        if converted_files:

            print(
                f"\n{C.YELLOW}{S.BRIGHT}"
                f"📁 Folder: {folder_name}"
            )

            separator()

            for extension, image_path, jpg_path in converted_files:

                print(
                    f"{C.GREEN}[CONVERTED] {S.RESET_ALL}"
                    f"{extension}: {image_path.name} → "
                    f"{C.CYAN}{jpg_path.name}"
                )


if __name__ == "__main__":
    main()
