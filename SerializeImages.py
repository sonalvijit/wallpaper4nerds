
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from colorama import Fore, Style, init

# Initialize Colorama
init(autoreset=True)

load_dotenv()

IMAGE_FOLDERS = [
    folder.strip()
    for folder in os.getenv("IMAGE_FOLDERS", "").split(",")
    if folder.strip()
]

IMAGE_EXTENSIONS = tuple(
    ext.strip().lower()
    for ext in os.getenv("IMAGE_EXTS", "").split(",")
    if ext.strip()
)

C = Fore
S = Style


# ============================================================
# TERMINAL COLORS
# ============================================================

def banner():
    print(f"""
{C.CYAN}{S.BRIGHT}
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║                  IMAGE FILE RENAMER                      ║
║                                                          ║
║              Hierarchical Image Naming                   ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
{S.RESET_ALL}""")


def separator():
    print(f"{C.LIGHTBLACK_EX}{'─' * 58}")


def info(message):
    print(f"{C.CYAN}[INFO] {S.RESET_ALL}{message}")


def success(message):
    print(f"{C.GREEN}[SUCCESS] {S.BRIGHT}{message}")


def warning(message):
    print(f"{C.YELLOW}[WARNING] {S.BRIGHT}{message}")


def error(message):
    print(f"{C.RED}[ERROR] {S.BRIGHT}{message}")


def highlight(message):
    return f"{C.YELLOW}{S.BRIGHT}{message}{S.RESET_ALL}"


# ============================================================
# FILE DISCOVERY
# ============================================================

def get_files_from_folder(folder: str) -> list:
    """Return sorted image paths from a folder and its subfolders."""

    if not os.path.isdir(folder):
        error(f"Folder not found: {folder}")
        return []

    image_files = []

    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(IMAGE_EXTENSIONS):
                image_files.append(os.path.join(root, file))

    return sorted(image_files)


# ============================================================
# HIERARCHICAL PREFIX GENERATION
# ============================================================

def get_folder_prefix(parent_folder: str, file_path: str) -> str:
    """
    Generate hierarchical prefix.

    Example:
    Wallpapers/image.jpg
        -> WALLPAPERS

    Wallpapers/Anime/image.jpg
        -> WALLPAPERS_ANIME

    Wallpapers/Nature/Landscapes/image.jpg
        -> WALLPAPERS_NATURE_LANDSCAPES
    """

    relative_path = os.path.relpath(
        os.path.dirname(file_path),
        parent_folder
    )

    main_folder = os.path.basename(
        os.path.normpath(parent_folder)
    ).upper()

    if relative_path == ".":
        return main_folder

    subfolders = [
        folder.upper()
        for folder in relative_path.split(os.sep)
        if folder
    ]

    return "_".join([main_folder] + subfolders)


# ============================================================
# FILENAME VALIDATION
# ============================================================

def check_filename(filename: str, parent_folder: str) -> bool:
    """Check hierarchical filename format."""

    name, _ = os.path.splitext(filename)

    # The file's parent directory determines its prefix.
    prefix = get_folder_prefix(
        parent_folder,
        os.path.join(parent_folder, filename)
    )

    pattern = rf"^{re.escape(prefix)}_\d{{10}}$"

    return re.fullmatch(
        pattern,
        name,
        re.IGNORECASE
    ) is not None


# ============================================================
# FILENAME GENERATION
# ============================================================

def change_filename(
    old_filename: str,
    parent_folder: str,
    file_path: str,
    serial: int
) -> str:
    """Generate hierarchical filename."""

    today = datetime.now().strftime("%d%m%Y")

    _, ext = os.path.splitext(old_filename)

    prefix = get_folder_prefix(
        parent_folder,
        file_path
    )

    return f"{prefix}_{today}{serial:02d}{ext.lower()}"


# ============================================================
# FILE RENAMING
# ============================================================

def save_filename(old_filename: str, new_filename: str) -> bool:
    """Rename a file within its existing directory."""

    try:
        if os.path.exists(new_filename):
            warning(
                f"Destination already exists: "
                f"{new_filename}"
            )
            return False

        os.rename(old_filename, new_filename)

        old = os.path.basename(old_filename)
        new = os.path.basename(new_filename)

        success(f"{highlight(old)} → {C.GREEN}{S.BRIGHT}{new}")

        return True

    except FileNotFoundError:
        error(f"File not found: {old_filename}")

    except Exception as e:
        error(f"Error renaming file: {e}")

    return False


# ============================================================
# SERIAL NUMBER GENERATION
# ============================================================

def serialize_filename(parent_folder: str, file_path: str) -> int:
    """
    Return the next available serial number for today's files
    within the same hierarchical folder.
    """

    if not os.path.isdir(parent_folder):
        error(f"Folder not found: {parent_folder}")
        return 1

    prefix = get_folder_prefix(
        parent_folder,
        file_path
    )

    today = datetime.now().strftime("%d%m%Y")

    serials = []

    directory = os.path.dirname(file_path)

    for filename in os.listdir(directory):

        full_path = os.path.join(directory, filename)

        if not os.path.isfile(full_path):
            continue

        name, _ = os.path.splitext(filename)

        pattern = (
            rf"^{re.escape(prefix)}_{today}(\d{{2}})$"
        )

        match = re.fullmatch(
            pattern,
            name,
            re.IGNORECASE
        )

        if match:
            serials.append(int(match.group(1)))

    return max(serials, default=0) + 1


# ============================================================
# MAIN PROGRAM
# ============================================================

def run():

    banner()

    if not IMAGE_FOLDERS:
        error("No image folders configured in .env")
        return

    if not IMAGE_EXTENSIONS:
        error("No image extensions configured in .env")
        return

    total_renamed = 0
    total_skipped = 0
    total_errors = 0

    info(f"Date: {highlight(datetime.now().strftime('%d-%m-%Y'))}")
    info(f"Extensions: {highlight(', '.join(IMAGE_EXTENSIONS))}")

    separator()

    for folder_name in IMAGE_FOLDERS:

        print(f"\n{C.YELLOW}{S.BRIGHT}📁 Folder: {folder_name}")
        separator()

        files = get_files_from_folder(folder_name)

        info(f"Images found: {highlight(len(files))}")

        if not files:
            warning("No images found.")
            continue

        # Maintain independent serial counters for each directory.
        serial_counters = {}

        for file_path in files:

            filename = os.path.basename(file_path)

            if check_filename(filename, folder_name):
                total_skipped += 1
                continue

            directory = os.path.dirname(file_path)

            # Generate a counter for this folder hierarchy.
            if directory not in serial_counters:
                serial_counters[directory] = serialize_filename(
                    folder_name,
                    file_path
                )

            serial = serial_counters[directory]

            new_name = change_filename(
                filename,
                folder_name,
                file_path,
                serial
            )

            new_path = os.path.join(
                directory,
                new_name
            )

            if save_filename(file_path, new_path):
                total_renamed += 1
                serial_counters[directory] += 1
            else:
                total_errors += 1

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("\n")

    separator()

    print(f"{C.CYAN}{S.BRIGHT}              PROCESS COMPLETED")
    separator()

    print(f"{C.GREEN}[✓] Successfully renamed : {total_renamed}")
    print(f"{C.BLUE}[↷] Skipped files        : {total_skipped}")
    print(f"{C.RED}[✗] Failed operations   : {total_errors}")

    separator()

    print(f"{C.GREEN}{S.BRIGHT}Thank you for using Image File Renamer!")
    print()


if __name__ == "__main__":
    run()
