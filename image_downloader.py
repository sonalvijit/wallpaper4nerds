import argparse
import exiftool
import subprocess
import asyncio
import mimetypes
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

from PIL import Image, PngImagePlugin
from playwright.async_api import async_playwright

# python image_downloader.py -u "https://jeonsomi.bstage.in/contents/6a83c63dc870ce7ed4ca3622" -c "JEON SOMI — 'Vogue Thailand 8월호' BEHIND PHOTOS. Originally posted by @somi_official_ on X on August 19, 2026. X post: https://x.com/somi_official_/status/2089957945048178774. Source: https://jeonsomi.bstage.in/contents/6a83c63dc870ce7ed4ca3622"

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".webp", ".gif",
    ".bmp", ".tif", ".tiff", ".ico"
}


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Download images from a single webpage using Playwright."
        )
    )

    parser.add_argument(
        "-u", "--url",
        required=True,
        help="URL of the webpage containing the images"
    )

    parser.add_argument(
        "-c", "--comment",
        default=None,
        help="Comment to add to downloaded images"
    )

    parser.add_argument(
        "-d", "--directory",
        default="default",
        help="Directory for downloaded images (default: default)"
    )

    return parser.parse_args()


def safe_filename(name):
    """Make a filename safe for Windows/Linux."""
    name = re.sub(r'[<>:"/\\|?*]', "_", name)
    name = name.strip().strip(".")

    return name or "image"


def extension_from_content_type(content_type):
    """Convert an HTTP Content-Type into a file extension."""
    content_type = content_type.split(";")[0].lower()

    mapping = {
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "image/bmp": ".bmp",
        "image/tiff": ".tiff",
        "image/x-icon": ".ico",
        "image/svg+xml": ".svg",
    }

    return mapping.get(content_type)


def extension_from_url(url):
    """Try to obtain an image extension from its URL."""
    extension = Path(urlparse(url).path).suffix.lower()

    if extension in IMAGE_EXTENSIONS:
        if extension == ".jpeg":
            return ".jpg"

        return extension

    return None


def choose_extension(content_type, url):
    """Choose the best available extension."""
    extension = extension_from_content_type(content_type)

    if extension:
        return extension

    extension = extension_from_url(url)

    if extension:
        return extension

    guessed = mimetypes.guess_extension(
        content_type.split(";")[0].lower()
    )

    return guessed or ".jpg"


def add_comment(file_path, comment):
    """
    Add a comment to supported image formats.

    JPEG:
        Uses the JPEG COM/comment field.

    PNG:
        Uses a PNG textual 'Comment' field.

    Other formats:
        Left unchanged because Pillow does not provide a
        portable comment field for every format.
    """
    if not comment:
        return

    try:
        with Image.open(file_path) as image:

            if image.format == "JPEG":
                image.save(
                    file_path,
                    format="JPEG",
                    quality=95,
                    comment=comment.encode("utf-8")
                )

            elif image.format == "PNG":
                metadata = PngImagePlugin.PngInfo()
                metadata.add_text("Comment", comment)

                image.save(
                    file_path,
                    format="PNG",
                    pnginfo=metadata
                )

            else:
                print(
                    f"[!] Comment not added to "
                    f"{file_path.name} "
                    f"(unsupported format: {image.format})"
                )

    except Exception as exc:
        print(
            f"[!] Could not add comment to "
            f"{file_path.name}: {exc}"
        )

# def add_description(file_path, description):
#     """
#     Add a description to supported image formats.

#     JPEG:
#         Writes the EXIF ImageDescription field.

#     PNG:
#         Writes a PNG textual 'Description' field.

#     Other formats:
#         Left unchanged if a suitable description field
#         is not supported.
#     """
#     if not description:
#         return

#     try:
#         with Image.open(file_path) as image:

#             if image.format == "JPEG":
#                 # EXIF tag 270 = ImageDescription
#                 exif = image.getexif()
#                 exif[270] = description

#                 image.save(
#                     file_path,
#                     format="JPEG",
#                     quality=95,
#                     exif=exif.tobytes()
#                 )

#             elif image.format == "PNG":
#                 metadata = PngImagePlugin.PngInfo()
#                 metadata.add_text(
#                     "Description",
#                     description
#                 )

#                 image.save(
#                     file_path,
#                     format="PNG",
#                     pnginfo=metadata
#                 )

#             else:
#                 print(
#                     f"[!] Description not added to "
#                     f"{file_path.name} "
#                     f"(unsupported format: {image.format})"
#                 )

#     except Exception as exc:
#         print(
#             f"[!] Could not add description to "
#             f"{file_path.name}: {exc}"
#         )

def add_description(file_path, description):
    """
    Write a Unicode description to XMP dc:description
    using ExifTool.
    """

    if not description:
        return

    try:
        subprocess.run(
            [
                "exiftool.exe",
                "-overwrite_original",
                f"-XMP-dc:Description={description}",
                str(file_path)
            ],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf-8",
            errors="replace"
        )

    except subprocess.CalledProcessError as exc:
        error = exc.stderr.strip()

        print(
            f"[!] ExifTool failed for "
            f"{file_path.name}: {error}"
        )

    except FileNotFoundError:
        print(
            "[!] exiftool.exe was not found. "
            "Make sure it is in PATH or next to the script."
        )

    except Exception as exc:
        print(
            f"[!] Could not add description to "
            f"{file_path.name}: {exc}"
        )

def make_unique_path(directory, stem, extension):
    """Return a non-existing path without overwriting files."""
    stem = safe_filename(stem)

    file_path = directory / f"{stem}{extension}"

    counter = 1

    while file_path.exists():
        file_path = directory / (
            f"{stem}_{counter}{extension}"
        )
        counter += 1

    return file_path


def filename_from_url(url, index):
    """Generate a useful filename from an image URL."""
    parsed = urlparse(url)

    original_name = Path(parsed.path).name

    if original_name:
        stem = Path(original_name).stem
    else:
        stem = f"image_{index}"

    if not stem:
        stem = f"image_{index}"

    return safe_filename(stem)


async def collect_image_urls(page, page_url):
    """
    Collect image URLs from the rendered page.

    This checks:
      - <img src>
      - <img currentSrc> (important for srcset)
      - lazy-loading attributes
      - <source srcset>
      - CSS background-image URLs

    It does NOT follow links to other webpages.
    """

    image_urls = set()

    # Give the page a chance to finish rendering.
    await page.wait_for_timeout(2000)

    # Scroll through the page so lazy-loaded images have a chance
    # to appear/load.
    previous_height = 0

    for _ in range(12):
        height = await page.evaluate(
            "document.body.scrollHeight"
        )

        if height == previous_height:
            break

        previous_height = height

        await page.evaluate(
            "window.scrollTo(0, document.body.scrollHeight)"
        )

        await page.wait_for_timeout(700)

    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(500)

    # Collect normal and lazy-loaded image attributes.
    img_urls = await page.locator("img").evaluate_all(
        """
        imgs => imgs.flatMap(img => [
            img.currentSrc,
            img.src,
            img.getAttribute('data-src'),
            img.getAttribute('data-lazy-src'),
            img.getAttribute('data-original'),
            img.getAttribute('data-url')
        ].filter(Boolean))
        """
    )

    # Collect <source srcset> URLs.
    source_urls = await page.locator("source").evaluate_all(
        """
        sources => sources.flatMap(source => {
            const values = [
                source.getAttribute('src'),
                source.getAttribute('data-src'),
                source.getAttribute('srcset'),
                source.getAttribute('data-srcset')
            ].filter(Boolean);

            return values.flatMap(value =>
                value.split(',').map(item =>
                    item.trim().split(/\\s+/)[0]
                )
            );
        })
        """
    )

    # Collect CSS background images.
    background_urls = await page.locator(
        "[style*='background-image']"
    ).evaluate_all(
        """
        elements => elements.flatMap(element => {
            const style = getComputedStyle(element);
            const matches = [...style.backgroundImage.matchAll(
                /url\\(["']?(.*?)["']?\\)/g
            )];

            return matches.map(match => match[1]);
        })
        """
    )

    for url in img_urls + source_urls + background_urls:
        if not url:
            continue

        url = url.strip()

        if url.startswith("data:"):
            continue

        absolute_url = urljoin(page_url, url)

        # Only keep HTTP(S) URLs.
        if absolute_url.startswith(("http://", "https://")):
            image_urls.add(absolute_url)

    return image_urls


async def download_images(page, image_urls, output_dir, comment):
    downloaded = 0

    for index, image_url in enumerate(
        sorted(image_urls),
        start=1
    ):
        try:
            print(f"[*] Downloading: {image_url}")

            # Use the browser context's request API so cookies and
            # session information from the webpage can be reused.
            response = await page.context.request.get(
                image_url,
                headers={
                    "Referer": page.url,
                    "Accept": "image/avif,image/webp,image/apng,"
                              "image/svg+xml,image/*,*/*;q=0.8",
                },
                timeout=30000
            )

            if not response.ok:
                print(
                    f"[!] HTTP {response.status} "
                    f"for {image_url}"
                )
                continue

            content_type = response.headers.get(
                "content-type", ""
            ).lower()

            # Some servers do not return a useful Content-Type.
            extension = choose_extension(
                content_type,
                image_url
            )

            if (
                content_type
                and not content_type.startswith("image/")
                and extension not in IMAGE_EXTENSIONS
            ):
                print(
                    f"[!] Skipping non-image: {image_url}"
                )
                continue

            body = await response.body()

            if not body:
                print(
                    f"[!] Empty response: {image_url}"
                )
                continue

            stem = filename_from_url(
                image_url,
                index
            )

            file_path = make_unique_path(
                output_dir,
                stem,
                extension
            )

            file_path.write_bytes(body)

            # Add metadata comment where supported.
            # add_comment(
            #     file_path,
            #     comment
            # )

            add_description(
                file_path,
                comment
            )

            downloaded += 1

            print(
                f"[+] Saved: {file_path}"
            )

        except Exception as exc:
            print(
                f"[!] Failed to download "
                f"{image_url}: {exc}"
            )

    return downloaded


async def main():
    args = parse_args()

    output_dir = Path(args.directory)
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    async with async_playwright() as playwright:

        browser = await playwright.chromium.launch(
            headless=True
        )

        context = await browser.new_context(
            viewport={
                "width": 1920,
                "height": 1080
            },
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/151.0.0.0 Safari/537.36"
            )
        )

        page = await context.new_page()

        print(f"[*] Opening page: {args.url}")

        try:
            await page.goto(
                args.url,
                wait_until="domcontentloaded",
                timeout=60000
            )

            # Allow JavaScript-rendered content to appear.
            await page.wait_for_timeout(3000)

        except Exception as exc:
            print(
                f"[!] Failed to open webpage: {exc}"
            )

            await browser.close()
            return 1

        print("[*] Looking for images...")

        image_urls = await collect_image_urls(
            page,
            args.url
        )

        if not image_urls:
            print(
                "[!] No images found on the rendered page."
            )

            await browser.close()
            return 0

        print(
            f"[*] Found {len(image_urls)} "
            f"possible image(s)."
        )

        downloaded = await download_images(
            page,
            image_urls,
            output_dir,
            args.comment
        )

        await browser.close()

    print()
    print(
        f"[*] Finished. Downloaded "
        f"{downloaded} image(s)."
    )

    print(
        f"[*] Location: "
        f"{output_dir.resolve()}"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(
        asyncio.run(main())
    )