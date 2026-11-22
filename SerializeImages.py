
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from colorama import Fore, Back, Style, init

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


# ============================================================
# TERMINAL COLORS
# ============================================================

C = Fore
S = Style


def banner():
    print(f"""
{C.CYAN}{S.BRIGHT}
╔══════════════════════════════════════════════════════╗
║                                                      ║
║              IMAGE FILE RENAMER                      ║
║                                                      ║
║           Automated Image Serialization              ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
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
    """
    Return sorted image paths from a folder and its subfolders.
    """
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
# FILENAME VALIDATION
# ============================================================

def check_filename(filename: str, parent_folder: str) -> bool:
    """
    Check filename format: FOLDER_ddmmyyyySS.ext
    """
    name, _ = os.path.splitext(filename)
    folder_prefix = os.path.basename(os.path.normpath(parent_folder)).upper()

    pattern = rf"^{re.escape(folder_prefix)}_\d{{10}}$"

    return re.fullmatch(pattern, name, re.IGNORECASE) is not None


# ============================================================
# FILENAME GENERATION
# ============================================================

def change_filename(old_filename: str, parent_folder: str, serial: int) -> str:
    """
    Generate filename: FOLDER_ddmmyyyySS.ext
    """
    today = datetime.now().strftime("%d%m%Y")
    _, ext = os.path.splitext(old_filename)

    folder_prefix = os.path.basename(
        os.path.normpath(parent_folder)
    ).upper()

    return f"{folder_prefix}_{today}{serial:02d}{ext.lower()}"


# ============================================================
# FILE RENAMING
# ============================================================

def save_filename(old_filename: str, new_filename: str) -> bool:
    """
    Rename a file within its existing directory.
    """
    try:
        if os.path.exists(new_filename):
            warning(f"Destination already exists: {new_filename}")
            return False

        os.rename(old_filename, new_filename)

        old = os.path.basename(old_filename)
        new = os.path.basename(new_filename)

        success(
            f"{highlight(old)}  →  {C.GREEN}{S.BRIGHT}{new}"
        )

        return True

    except FileNotFoundError:
        error(f"File not found: {old_filename}")

    except Exception as e:
        error(f"Error renaming file: {e}")

    return False


# ============================================================
# SERIAL NUMBER GENERATION
# ============================================================

def serialize_filename(parent_folder: str) -> int:
    """
    Return the next available serial number for today's files.
    """
    if not os.path.isdir(parent_folder):
        error(f"Folder not found: {parent_folder}")
        return 1

    folder_prefix = os.path.basename(
        os.path.normpath(parent_folder)
    ).upper()

    today = datetime.now().strftime("%d%m%Y")

    serials = []

    for root, _, files in os.walk(parent_folder):
        for filename in files:

            name, _ = os.path.splitext(filename)

            pattern = (
                rf"^{re.escape(folder_prefix)}_{today}(\d{{2}})$"
            )

            match = re.fullmatch(pattern, name, re.IGNORECASE)

            if match:
                serials.append(int(match.group(1)))

    return max(serials, default=0) + 1


# ============================================================
# MAIN PROGRAM
# ============================================================

# def run():

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

        serial = serialize_filename(folder_name)

        files = get_files_from_folder(folder_name)

        info(f"Images found: {highlight(len(files))}")
        info(f"Starting serial: {highlight(serial)}")

        if not files:
            warning("No images found.")
            continue

        for file_path in files:

            filename = os.path.basename(file_path)

            if check_filename(filename, folder_name):
                total_skipped += 1
                continue

            new_name = change_filename(
                filename,
                folder_name,
                serial
            )

            new_path = os.path.join(
                os.path.dirname(file_path),
                new_name
            )

            if save_filename(file_path, new_path):
                total_renamed += 1
                serial += 1
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

def run():
    banner()
    for folder_name in IMAGE_FOLDERS:

        serial = serialize_filename(folder_name)
        files = get_files_from_folder(folder_name)

        renamed_files = []

        for file_path in files:

            filename = os.path.basename(file_path)

            if check_filename(filename, folder_name):
                continue

            new_name = change_filename(
                filename,
                folder_name,
                serial
            )

            new_path = os.path.join(
                os.path.dirname(file_path),
                new_name
            )

            if save_filename(file_path, new_path):
                renamed_files.append((filename, new_name))
                serial += 1

        # Display folder information only if changes occurred
        if renamed_files:

            print(
                f"\n{C.YELLOW}{S.BRIGHT}"
                f"📁 Folder: {folder_name}"
            )

            separator()

            for old_name, new_name in renamed_files:
                print(
                    f"{C.GREEN}[RENAMED] {S.RESET_ALL}"
                    f"{old_name} → {C.CYAN}{new_name}"
                )

if __name__ == "__main__":
    run()
