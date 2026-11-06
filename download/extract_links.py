
import csv
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import URLError
from urllib.parse import parse_qs, unquote, urljoin, urlparse
from urllib.request import Request, urlopen


PAGE_URL = "https://my.uupload.ir/f/amirmofatehi/ax%20day2"

BASE_DIR = Path(__file__).resolve().parent
CSV_FILE = BASE_DIR / "links.csv"
URL_FILE = BASE_DIR / "uget_urls.txt"

USER_AGENT = "Mozilla/5.0"

SIZE_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(B|KB|MB|GB)\b",
    re.IGNORECASE
)

SIZE_MULTIPLIERS = {
    "B": 1,
    "KB": 1024,
    "MB": 1024 ** 2,
    "GB": 1024 ** 3,
}


class ImageLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.current_row = None
        self.current_anchor = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)

        if tag == "tr":
            self.current_row = {
                "text": [],
                "links": []
            }

        elif tag == "a" and self.current_row is not None:
            href = attrs.get("href")

            if href:
                self.current_anchor = href

    def handle_data(self, data):
        if self.current_row is not None:
            self.current_row["text"].append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.current_anchor is not None:
            self.current_row["links"].append(
                self.current_anchor
            )
            self.current_anchor = None

        elif tag == "tr" and self.current_row is not None:
            self.rows.append(self.current_row)
            self.current_row = None


def fetch_page():
    request = Request(
        PAGE_URL,
        headers={"User-Agent": USER_AGENT}
    )

    with urlopen(request, timeout=60) as response:
        return response.read().decode(
            "utf-8",
            errors="replace"
        )



def is_direct_download_url(url):
    parsed = urlparse(url)
    query_params = parse_qs(
        parsed.query,
        keep_blank_values=True
    )

    return (
        parsed.hostname is not None
        and parsed.hostname.endswith(".uupload.ir")
        and "/files/" in parsed.path
        and parsed.path.lower().endswith(
            (".jpg", ".jpeg", ".png")
        )
        and "download" in query_params
    )



def parse_size(text):
    match = SIZE_PATTERN.search(text)

    if not match:
        return "", ""

    value = float(
        match.group(1).replace(",", ".")
    )
    unit = match.group(2).upper()

    size_bytes = int(
        value * SIZE_MULTIPLIERS[unit]
    )

    return f"{value:g} {unit}", size_bytes


def make_unique_filename(filename, used_names):
    path = Path(filename)
    candidate = filename
    counter = 2

    while candidate.casefold() in used_names:
        candidate = f"{path.stem}__{counter}{path.suffix}"
        counter += 1

    used_names.add(candidate.casefold())

    return candidate


def extract_links(html):
    parser = ImageLinkParser()
    parser.feed(html)

    records = []
    seen_urls = set()
    used_names = set()

    for row in parser.rows:
        row_text = " ".join(row["text"])
        size, size_bytes = parse_size(row_text)

        for href in row["links"]:
            url = urljoin(PAGE_URL, href)

            if not is_direct_download_url(url):
                continue

            if url in seen_urls:
                continue

            original_filename = unquote(
                Path(urlparse(url).path).name
            )

            local_filename = make_unique_filename(
                original_filename,
                used_names
            )

            records.append({
                "original_filename": original_filename,
                "local_filename": local_filename,
                "size": size,
                "size_bytes": size_bytes,
                "url": url
            })

            seen_urls.add(url)

    return records


def save_csv(records):
    fieldnames = [
        "original_filename",
        "local_filename",
        "size",
        "size_bytes",
        "url"
    ]

    with CSV_FILE.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(records)


def save_url_list(records):
    with URL_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:
        for record in records:
            file.write(record["url"] + "\n")


def main():
    try:
        print("Fetching page...")
        html = fetch_page()

        print("Extracting direct download links...")
        records = extract_links(html)

        if not records:
            raise ValueError("No direct download links found.")

        save_csv(records)
        save_url_list(records)

        filename_counts = Counter(
            record["original_filename"].casefold()
            for record in records
        )

        duplicate_names = sum(
            count - 1
            for count in filename_counts.values()
            if count > 1
        )

        missing_sizes = sum(
            not record["size_bytes"]
            for record in records
        )

        total_bytes = sum(
            record["size_bytes"]
            for record in records
        )

        print("\nExtraction completed.")
        print(f"Direct download links: {len(records)}")
        print(f"Duplicate filenames: {duplicate_names}")
        print(f"Missing sizes: {missing_sizes}")
        print(
            f"Total known size: "
            f"{total_bytes / (1024 ** 3):.2f} GB"
        )
        print(f"CSV manifest: {CSV_FILE}")
        print(f"uGet URL list: {URL_FILE}")

    except (URLError, TimeoutError, OSError, ValueError) as error:
        print(f"Extraction failed: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
