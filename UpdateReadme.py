import os

# === Config ===
IMAGE_FOLDERS = ["Anime", "Abstract","cgi3d", "Landscape", "Painting", "Pokemon","Real","mobile"]
README_FILE = "README.md"
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".gif")

def get_images(folder):
    """Get all supported image files from the folder."""
    return sorted(
        [f for f in os.listdir(folder) if f.lower().endswith(IMAGE_EXTS)]
    )

def format_title(folder_name):
    """Turn folder name into a markdown heading."""
    return "## " + folder_name.replace("-", " ").title()

def generate_table(images, folder, columns=3):
    """Generate a 3-column HTML table of images with filenames."""
    html = ['<table>\n<tr>']
    count = 0

    for img in images:
        path = f"{folder}/{img}"
        html.append(
            f'<td align="center">'
            f'<img src="{path}" width="300px"><br>'
            f'<sub>{img}</sub>'
            f'</td>'
        )
        count += 1
        if count % columns == 0:
            html.append('</tr>\n<tr>')

    if count % columns != 0:
        html.append('</tr>')

    html.append('</table>\n')
    return ''.join(html)

def generate_section(folder):
    """Generate full markdown section with title and latest image table for one folder."""
    if not os.path.isdir(folder):
        print(f"❌ Folder does not exist: {folder}")
        return ""

    images = get_images(folder)
    if not images:
        print(f"⚠️ No images in folder: {folder}")
        return ""

    latest_images = images[-6:]  # Get last 6 images by filename
    section = format_title(folder) + "\n\n"
    section += generate_table(latest_images, folder, columns=3) + "\n"
    return section

def update_readme(folders):
    """Generate the full README content and overwrite the output file."""
    content = "# Wallpapers\n\n"

    for folder in folders:
        section = generate_section(folder)
        if section:
            content += section + "\n"

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"✅ {README_FILE} successfully created with latest 6 images per folder.")

# === Run ===
if __name__ == "__main__":
    update_readme(IMAGE_FOLDERS)
