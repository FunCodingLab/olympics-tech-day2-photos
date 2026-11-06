# Third Technology Olympiad — Photo Gallery

A photo archive of the **3rd Technology Olympiad**, featuring the **Image Processing and Natural Language Processing (NLP) League**, with a focus on Day 2 of the event.

This repository provides an online photo gallery, original image download links, and utilities for extracting and managing photo downloads.

## 🌐 Online Gallery

**[View the Photo Gallery](https://funcodinglab.github.io/olympics-tech-day2-photos/)**

The gallery provides:

- **Photo Grid:** Browse event photos through a thumbnail gallery.
- **Full-Size Viewer:** Open images in a larger view.
- **Navigation:** Move between photos using previous and next controls.
- **Slideshow:** Automatically cycle through the photos.
- **Thumbnail Filmstrip:** Navigate quickly between images.
- **Image Information:** View the filename and file size.
- **Download Original:** Download the original image directly from its hosting source.

## 📁 Repository Structure

```text
olympics-tech-day2-photos/
│
├── assets/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── gallery.js
│
├── download/
│   ├── extract_links.py
│   ├── links.csv
│   └── uget_urls.txt
│
├── img/
│   └── .gitkeep
│
├── media/
│   ├── large/
│   ├── thumbs/
│   └── photos.json
│
├── scripts/
│   └── requirements.txt
│
├── .gitignore
├── .nojekyll
├── index.html
├── LICENSE
└── README.md
```

### Directory Overview

| Path | Description |
|---|---|
| `assets/css/` | Gallery styles and layout |
| `assets/js/` | Gallery functionality and interactions |
| `download/` | Download-link extraction utilities and generated files |
| `img/` | Local storage for original, high-resolution photos |
| `media/large/` | Optimized images used in the full-size viewer |
| `media/thumbs/` | Optimized thumbnails used in the gallery grid |
| `media/photos.json` | Photo manifest containing filenames, sizes, and image URLs |
| `scripts/` | Python utilities for image processing |
| `index.html` | Main gallery page |

**Note:** Original high-resolution images stored in `img/` are excluded from Git tracking to avoid unnecessarily increasing the repository size. The online gallery uses optimized images and externally hosted original download links.

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/FunCodingLab/olympics-tech-day2-photos.git
cd olympics-tech-day2-photos
```

### 2. Run the Gallery Locally

Since the gallery loads its photo manifest using JavaScript `fetch()`, use a local HTTP server rather than opening `index.html` directly.

With Python 3:

```bash
python3 -m http.server 8000
```

Open the following address in your browser:

```text
http://localhost:8000
```

Press `Ctrl + C` to stop the server.

## 📥 Downloading Photos

There are two ways to download the original photos.

### Option 1: Download Individual Photos

1. Open the [online gallery](https://funcodinglab.github.io/olympics-tech-day2-photos/).
2. Select the photo you want.
3. Click the **Download Original** button.

The original image is downloaded from its external hosting source.

### Option 2: Download All Photos Using uGet

For downloading a large collection of images, you can use the included link extraction script together with [uGet Download Manager](https://ugetdm.com/).

**Step 1 — Extract Download Links**

From the repository root, run:

```bash
python3 download/extract_links.py
```

The script retrieves the image listing page, extracts direct download URLs, removes duplicate URLs, and handles duplicate filenames.

It generates two files:

| File | Description |
|---|---|
| `download/links.csv` | Download manifest containing filenames, sizes, and URLs |
| `download/uget_urls.txt` | Plain-text list of direct download URLs |

**Step 2 — Import Links into uGet**

1. Open uGet.
2. Select **File → Batch Downloads**.
3. Import or paste the URLs from `download/uget_urls.txt`.
4. Configure the destination directory, preferably `img/`.
5. Start the download queue.

Each line in `uget_urls.txt` represents one download URL.

**Step 3 — Verify Downloads**

After downloading, compare the downloaded files with `download/links.csv` to check filenames and identify missing files.

The CSV also preserves unique local filenames for files that originally have duplicate names.

## 🛠️ Development

### Requirements

- Python 3
- A modern web browser
- uGet (optional, for batch downloads)

The link extraction utility uses Python's standard library and does not require third-party packages.

For the image-processing utilities in `scripts/`, install their dependencies using:

```bash
python3 -m pip install -r scripts/requirements.txt
```

### Updating the Gallery

The gallery uses `media/photos.json` as its image manifest.

Each photo entry contains:

- `filename`: Original image filename.
- `size`: Human-readable original file size.
- `size_bytes`: Original file size in bytes.
- `download_url`: Direct original-image download URL.
- `thumb`: Path to the thumbnail.
- `large`: Path to the larger optimized image.

When adding or replacing photos, ensure that the manifest and corresponding optimized images remain synchronized.

## 🌍 Deployment

This repository is configured for **GitHub Pages**.

To publish the gallery:

1. Open the repository's **Settings**.
2. Navigate to **Pages**.
3. Under **Build and deployment**, select `Deploy from a branch`.
4. Select the `main` branch.
5. Select the `/(root)` directory.
6. Save the configuration.

The website will be available at:

```text
https://funcodinglab.github.io/olympics-tech-day2-photos/
```

The repository's root `index.html` serves as the entry point.

## 📄 License

The repository includes an MIT License. Please check the applicable ownership and usage permissions before redistributing event photographs or using them for other purposes.

## 🙌 Credits

Created and maintained by [FunCodingLab](https://github.com/FunCodingLab).

A digital archive of the 3rd Technology Olympiad — Image Processing and NLP League.

---

*Preserving moments, people, and memories from the Technology Olympiad.*