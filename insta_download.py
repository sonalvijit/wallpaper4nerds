
from pathlib import Path
import argparse
import re
import shutil
import instaloader
import piexif

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


DEFAULT_DOWNLOAD_DIR = Path("Instagram_Downloads")


def organize_miscellaneous(download_dir: Path):
    """Move TXT files into miscellaneous."""

    misc_dir = download_dir / "miscellaneous"
    txt_files = list(download_dir.glob("*.txt"))

    if not txt_files:
        return

    misc_dir.mkdir(parents=True, exist_ok=True)

    for file in txt_files:
        destination = misc_dir / file.name

        counter = 1
        while destination.exists():
            destination = misc_dir / f"{file.stem}_duplicate_{counter}{file.suffix}"
            counter += 1

        shutil.move(str(file), str(destination))


def embed_metadata(image_path: Path, username: str, post_url: str):
    """Embed available Instagram information into JPEG EXIF."""

    try:
        exif_dict = piexif.load(str(image_path))

        exif_dict["0th"][piexif.ImageIFD.Artist] = username.encode("utf-8")
        exif_dict["0th"][piexif.ImageIFD.ImageDescription] = post_url.encode("utf-8")

        exif_dict["Exif"][piexif.ExifIFD.UserComment] = (
            b"ASCII\x00\x00\x00" + post_url.encode("utf-8")
        )

        piexif.insert(piexif.dump(exif_dict), str(image_path))

    except Exception as error:
        print(f"Metadata embedding skipped: {error}")


def create_loader(download_dir: Path, mp4_only: bool):
    return instaloader.Instaloader(
        dirname_pattern=str(download_dir),
        filename_pattern="{shortcode}_{mediaid}",
        download_pictures=not mp4_only,
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
        post_metadata_txt_pattern=""
    )


def alternative_download(url: str, download_dir: Path):
    """
    Attempt an alternative download for accessible content.
    Does not bypass login, privacy, or access restrictions.
    """

    if yt_dlp is None:
        print("Alternative downloader unavailable. Install yt-dlp.")
        return False

    print("\nTrying alternative downloader...")

    options = {
        "outtmpl": str(download_dir / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "ignoreerrors": False,
        "overwrites": False,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            downloader.download([url])

        return True

    except Exception as error:
        print(f"Alternative download failed: {error}")
        return False


def download_post(url: str, download_dir: Path, mp4_only=False):
    """Download a post; metadata failure does not immediately stop processing."""

    match = re.search(
        r"instagram\.com/(p|reel|tv)/([A-Za-z0-9_-]+)",
        url
    )

    if not match:
        print(f"Invalid Instagram URL: {url}")
        return False

    shortcode = match.group(2)
    post_type = match.group(1)

    canonical_url = f"https://www.instagram.com/{post_type}/{shortcode}/"

    download_dir.mkdir(parents=True, exist_ok=True)

    loader = create_loader(download_dir, mp4_only)

    username = None

    print(f"Post shortcode: {shortcode}")

    # STEP 1: Try to retrieve metadata.
    try:
        post = instaloader.Post.from_shortcode(
            loader.context,
            shortcode
        )

        username = post.owner_username

        print(f"Metadata retrieved for @{username}")

        # STEP 2: Download using Instaloader.
        print("Attempting Instaloader download...")

        loader.download_post(post, target=shortcode)

        # Embed metadata only when available.
        if username and not mp4_only:
            for image_path in download_dir.glob(f"{shortcode}_*.jpg"):
                embed_metadata(
                    image_path,
                    username,
                    canonical_url
                )

        print("Instaloader processing completed.")
        return True

    except Exception as error:
        print(f"Instaloader failed: {error}")

    # STEP 3: Metadata or primary download failed.
    # Try an alternative downloader.
    print("Metadata unavailable or primary download failed.")
    print("Continuing without metadata...")

    result = alternative_download(
        canonical_url,
        download_dir
    )

    if result:
        print("Alternative download completed.")
        return True

    print("All available download methods failed.")
    return False


def download_multiple(urls, download_dir: Path, mp4_only=False):
    """Process multiple URLs sequentially."""

    successful = 0
    failed = 0
    total = len(urls)

    print("\n" + "=" * 50)
    print(f"       BATCH DOWNLOAD: {total} POSTS")
    print("=" * 50)

    for index, url in enumerate(urls, start=1):

        print(f"\n[{index}/{total}] Processing URL:")
        print(url)

        result = download_post(
            url,
            download_dir,
            mp4_only
        )

        if result:
            successful += 1
        else:
            failed += 1

    organize_miscellaneous(download_dir)

    print("\n" + "=" * 50)
    print("             DOWNLOAD SUMMARY")
    print("=" * 50)
    print(f"Successful: {successful}")
    print(f"Failed:     {failed}")
    print(f"Total:      {total}")
    print(f"Location:   {download_dir.resolve()}")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Instagram batch downloader"
    )

    parser.add_argument(
        "-u", "--url",
        nargs="+",
        required=True,
        help="One or more Instagram URLs"
    )

    parser.add_argument(
        "--mp4",
        action="store_true",
        help="Download videos only"
    )

    parser.add_argument(
        "-d", "--directory",
        type=str,
        default=str(DEFAULT_DOWNLOAD_DIR),
        help="Destination folder"
    )

    args = parser.parse_args()

    # Remove surrounding quotes, if accidentally included.
    directory_string = args.directory.strip().strip('"').strip("'")
    download_dir = Path(directory_string)

    print(f"Instaloader version: {instaloader.__version__}")

    download_multiple(
        args.url,
        download_dir,
        args.mp4
    )


if __name__ == "__main__":
    main()
