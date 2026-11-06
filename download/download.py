
import csv
import logging
import shutil
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

MANIFEST_FILE = BASE_DIR / "links.csv"
OUTPUT_DIR = PROJECT_DIR / "img"

MAX_WORKERS = 4
MAX_RETRIES = 3
TIMEOUT = 120
CHUNK_SIZE = 1024 * 256

USER_AGENT = "Mozilla/5.0"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

logger = logging.getLogger(__name__)


def load_manifest():
    if not MANIFEST_FILE.exists():
        raise FileNotFoundError(
            f"Manifest not found: {MANIFEST_FILE}. "
            "Run extract_links.py first."
        )

    with MANIFEST_FILE.open(
        "r",
        newline="",
        encoding="utf-8"
    ) as csv_file:
        records = list(csv.DictReader(csv_file))

    if not records:
        raise ValueError("Manifest is empty.")

    return records


def download_file(record):
    filename = Path(record["local_filename"]).name

    if not filename or filename != record["filename"]:
        return False, f"Invalid filename: {record['filename']}"

    url = record["url"]
    output_path = OUTPUT_DIR / filename
    temp_path = output_path.with_name(
        output_path.name + ".part"
    )

    if output_path.exists() and output_path.stat().st_size > 0:
        return True, f"SKIPPED: {filename}"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            request = Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Referer": (
                        "https://my.uupload.ir/"
                    )
                }
            )

            with urlopen(request, timeout=TIMEOUT) as response:
                with temp_path.open("wb") as output_file:
                    shutil.copyfileobj(
                        response,
                        output_file,
                        length=CHUNK_SIZE
                    )

            if temp_path.stat().st_size == 0:
                raise ValueError("Downloaded file is empty.")

            temp_path.replace(output_path)

            return True, f"DOWNLOADED: {filename}"

        except Exception as error:
            temp_path.unlink(missing_ok=True)

            if attempt == MAX_RETRIES:
                return False, f"FAILED: {filename} - {error}"

            time.sleep(2 * attempt)

    return False, f"FAILED: {filename}"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        records = load_manifest()
    except (OSError, ValueError) as error:
        logger.error("%s", error)
        return

    logger.info("Found %d images in manifest.", len(records))
    logger.info("Download directory: %s", OUTPUT_DIR)

    successful = 0
    failed = 0

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:
        futures = [
            executor.submit(download_file, record)
            for record in records
        ]

        for index, future in enumerate(
            as_completed(futures),
            start=1
        ):
            success, message = future.result()

            if success:
                successful += 1
            else:
                failed += 1

            logger.info(
                "[%d/%d] %s",
                index,
                len(records),
                message
            )

    logger.info("Download completed.")
    logger.info("Successful: %d", successful)
    logger.info("Failed: %d", failed)


if __name__ == "__main__":
    main()
