
import instaloader
import argparse
import re
import sys
import piexif
import yt_dlp

from pathlib import Path


DOWNLOAD_DIR = Path("Instagram_Downloads")


def embed_metadata(image_path, username, post_url, shortcode):
    try:
        exif = piexif.load(str(image_path))

        description = (
            f"Instagram: @{username}\n"
            f"Post URL: {post_url}\n"
            f"Shortcode: {shortcode}"
        )

        exif["0th"][piexif.ImageIFD.Artist] = (
            f"@{username}".encode("utf-8")
        )

        exif["0th"][piexif.ImageIFD.ImageDescription] = (
            description.encode("utf-8")
        )

        exif["Exif"][piexif.ExifIFD.UserComment] = (
            b"ASCII\x00\x00\x00" + description.encode("ascii")
        )

        piexif.insert(piexif.dump(exif), str(image_path))

        print(f"[META] Embedded metadata: {image_path.name}")

    except Exception as e:
        print(f"[WARNING] Could not embed metadata: {e}")


def fallback_download(url, mp4_only=False):
    """Download content using yt-dlp if Instaloader fails."""

    print("\n[FALLBACK] Trying alternative downloader...")
    print("[INFO] Downloading without Instagram metadata.")

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    options = {
        "outtmpl": str(DOWNLOAD_DIR / "%(id)s.%(ext)s"),
        "format": "best[ext=mp4]" if mp4_only else "best",
        "merge_output_format": "mp4",
        "noplaylist": False,
        "quiet": False,
        "no_warnings": False,
        "overwrites": False,
    }

    try:
        with yt_dlp.YoutubeDL(options) as downloader:
            downloader.download([url])

        print("\n[SUCCESS] Fallback download completed!")

    except Exception as e:
        print(f"\n[ERROR] Fallback download also failed: {e}")
        print("[INFO] The post may require authentication or be unavailable.")


def download_post(url, mp4_only=False):

    match = re.search(
        r"instagram\.com/(p|reel|tv)/([A-Za-z0-9_-]+)",
        url
    )

    if not match:
        print("[ERROR] Invalid Instagram URL.")
        sys.exit(1)

    content_type = match.group(1)
    shortcode = match.group(2)

    post_url = (
        f"https://www.instagram.com/{content_type}/{shortcode}/"
    )

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    loader = instaloader.Instaloader(
        dirname_pattern=str(DOWNLOAD_DIR),
        filename_pattern="{shortcode}_{mediaid}",
        download_pictures=not mp4_only,
        download_videos=True,
        download_video_thumbnails=False,
        download_comments=False,
        save_metadata=False
    )

    try:
        print(f"\n[INFO] Post: {post_url}")
        print("[INFO] Fetching Instagram metadata...")

        post = instaloader.Post.from_shortcode(
            loader.context,
            shortcode
        )

        username = post.owner_username

        print(f"[INFO] Instagram Handle: @{username}")
        print("[INFO] Downloading content...")

        loader.download_post(post, target=shortcode)

        # Embed metadata into downloaded JPEG images
        if not mp4_only:
            images = [
                file for file in DOWNLOAD_DIR.iterdir()
                if file.is_file()
                and file.name.startswith(shortcode + "_")
                and file.suffix.lower() in (".jpg", ".jpeg")
            ]

            for image_path in images:
                embed_metadata(
                    image_path,
                    username,
                    post_url,
                    shortcode
                )

        print("\n[SUCCESS] Download completed!")

    except instaloader.exceptions.InstaloaderException as e:
        print(f"\n[WARNING] Instaloader failed: {e}")
        fallback_download(url, mp4_only)

    except Exception as e:
        print(f"\n[WARNING] Download failed: {e}")
        fallback_download(url, mp4_only)


def main():

    parser = argparse.ArgumentParser(
        description="Instagram Downloader with Metadata and Fallback"
    )

    parser.add_argument(
        "-u",
        "--url",
        required=True,
        help="Instagram post URL"
    )

    parser.add_argument(
        "--mp4",
        action="store_true",
        help="Download MP4 videos only"
    )

    args = parser.parse_args()

    download_post(args.url, args.mp4)


if __name__ == "__main__":
    main()
