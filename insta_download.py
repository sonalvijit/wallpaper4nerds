from pathlib import Path
import argparse
import re
import shutil

import instaloader
import piexif


DEFAULT_DOWNLOAD_DIR = Path("Instagram_Downloads")


def organize_miscellaneous(download_dir: Path):
    """Move TXT files into the miscellaneous folder."""

    misc_dir = download_dir / "miscellaneous"
    txt_files = list(download_dir.glob("*.txt"))

    if not txt_files:
        return

    misc_dir.mkdir(parents=True, exist_ok=True)

    for file in txt_files:
        destination = misc_dir / file.name

        if destination.exists():
            destination = misc_dir / f"{file.stem}_copy{file.suffix}"

        shutil.move(str(file), str(destination))


def embed_metadata(image_path: Path, username: str, post_url: str):
    """Embed Instagram information into JPEG EXIF metadata."""

    try:
        exif_dict = piexif.load(str(image_path))

        exif_dict["0th"][piexif.ImageIFD.Artist] = username.encode("utf-8")
        exif_dict["0th"][piexif.ImageIFD.ImageDescription] = (
            post_url.encode("utf-8")
        )

        exif_dict["Exif"][piexif.ExifIFD.UserComment] = (
            b"ASCII\x00\x00\x00" + post_url.encode("utf-8")
        )

        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, str(image_path))

    except Exception:
        pass


def download_post(url: str, download_dir: Path, mp4_only: bool = False):
    """Download an authorized/public post using Instaloader."""

    match = re.search(
        r"instagram\.com/(p|reel|tv)/([A-Za-z0-9_-]+)",
        url
    )

    if not match:
        print(f"Invalid Instagram URL: {url}")
        return False

    shortcode = match.group(2)

    canonical_url = f"https://www.instagram.com/p/{shortcode}/"

    download_dir.mkdir(parents=True, exist_ok=True)

    loader = instaloader.Instaloader(
        dirname_pattern=str(download_dir),
        filename_pattern="{shortcode}_{mediaid}",
        download_pictures=not mp4_only,
        download_videos=True,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        compress_json=False,
    )

    try:
        post = instaloader.Post.from_shortcode(loader.context, shortcode)

        username = post.owner_username

        print(f"Downloading: @{username}")
        print(f"Post: {canonical_url}")

        loader.download_post(post, target=shortcode)

        # Embed metadata into downloaded JPEG images
        if not mp4_only:
            for image_path in download_dir.glob(f"{shortcode}_*.jpg"):
                embed_metadata(
                    image_path,
                    username,
                    canonical_url
                )

        return True

    except Exception as e:
        print(f"Download failed: {e}")
        return False


def download_multiple(urls, download_dir: Path, mp4_only: bool = False):
    """Process multiple Instagram URLs."""

    total = len(urls)
    successful = 0
    failed = 0

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
    print(f"Failed:    {failed}")
    print(f"Total:     {total}")
    print(f"Location:  {download_dir.resolve()}")
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

    # Clean accidental surrounding quotes and trailing separators
    directory_string = args.directory.strip().strip('"').strip("'")

    download_dir = Path(directory_string)

    download_multiple(
        args.url,
        download_dir,
        args.mp4
    )


if __name__ == "__main__":
    main()