#!/usr/bin/env python3
"""
Image processing pipeline for generating gallery thumbnails,
compressed preview images, and the JSON metadata manifest.
"""

import argparse
import csv
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageOps
from tqdm import tqdm


@dataclass(frozen=True)
class ProcessingConfig:
    input_dir: Path
    output_dir: Path
    csv_path: Path
    thumb_size: Tuple[int, int] = (240, 240)
    large_max_dim: int = 1600
    thumb_quality: int = 78
    large_quality: int = 82
    image_format: str = "webp"
    force: bool = False


def process_single_image(
    row: Dict[str, str], config: ProcessingConfig
) -> Optional[Dict[str, object]]:
    """Resize and compress a single image into thumbnail and large preview formats."""
    local_filename = row["local_filename"].strip()
    source_path = config.input_dir / local_filename

    if not source_path.is_file():
        return None

    stem = Path(local_filename).stem
    ext = f".{config.image_format.lower()}"
    thumb_rel_path = f"media/thumbs/{stem}{ext}"
    large_rel_path = f"media/large/{stem}{ext}"

    thumb_out_path = config.output_dir.parent / thumb_rel_path
    large_out_path = config.output_dir.parent / large_rel_path

    save_format = "WEBP" if config.image_format.lower() == "webp" else "JPEG"

    try:
        if config.force or not (thumb_out_path.exists() and large_out_path.exists()):
            with Image.open(source_path) as img:
                img = ImageOps.exif_transpose(img)
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")

                # Generate compressed large preview (aspect ratio preserved)
                large_img = img.copy()
                large_img.thumbnail(
                    (config.large_max_dim, config.large_max_dim),
                    Image.Resampling.LANCZOS,
                )
                large_img.save(
                    large_out_path,
                    format=save_format,
                    quality=config.large_quality,
                    optimize=True,
                )

                # Generate center-cropped square thumbnail
                thumb_img = ImageOps.fit(
                    img,
                    config.thumb_size,
                    method=Image.Resampling.LANCZOS,
                    centering=(0.5, 0.5),
                )
                thumb_img.save(
                    thumb_out_path,
                    format=save_format,
                    quality=config.thumb_quality,
                    optimize=True,
                )

        return {
            "filename": row["original_filename"].strip(),
            "size": row["size"].strip(),
            "size_bytes": int(row["size_bytes"].strip()),
            "download_url": row["url"].strip(),
            "thumb": thumb_rel_path,
            "large": large_rel_path,
        }
    except Exception as exc:
        print(f"Error processing {local_filename}: {exc}")
        return None


def load_csv_records(csv_path: Path) -> List[Dict[str, str]]:
    """Read image records from the CSV file."""
    with csv_path.open(mode="r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return list(reader)


def run_pipeline(config: ProcessingConfig, workers: int) -> None:
    """Execute the parallel image processing pipeline and write photos.json."""
    thumbs_dir = config.output_dir / "thumbs"
    large_dir = config.output_dir / "large"
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    large_dir.mkdir(parents=True, exist_ok=True)

    records = load_csv_records(config.csv_path)
    results: List[Optional[Dict[str, object]]] = [None] * len(records)

    with ProcessPoolExecutor(max_workers=workers) as executor:
        future_to_index = {
            executor.submit(process_single_image, row, config): idx
            for idx, row in enumerate(records)
        }

        for future in tqdm(
            as_completed(future_to_index),
            total=len(records),
            desc="Processing images",
            unit="img",
        ):
            idx = future_to_index[future]
            results[idx] = future.result()

    valid_Manifest = [item for item in results if item is not None]

    manifest_path = config.output_dir / "photos.json"
    with manifest_path.open(mode="w", encoding="utf-8") as json_file:
        json.dump(valid_Manifest, json_file, indent=2)

    print(
        f"Successfully processed {len(valid_Manifest)} / {len(records)} images. "
        f"Manifest saved to {manifest_path}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate compressed gallery assets from high-res images."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("img"),
        help="Directory containing source images.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("media"),
        help="Output directory for thumbs, large previews, and photos.json.",
    )
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=Path("download/links.csv"),
        help="Path to the CSV file containing image metadata and download links.",
    )
    parser.add_argument(
        "--format",
        choices=["webp", "jpg"],
        default="webp",
        help="Output format for compressed images (default: webp).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=os.cpu_count() or 4,
        help="Number of worker processes.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing generated images.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    cfg = ProcessingConfig(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        csv_path=args.csv_path,
        image_format=args.format,
        force=args.force,
    )
    run_pipeline(cfg, workers=args.workers)