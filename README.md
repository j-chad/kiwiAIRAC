# kiwiAIRAC 🥝

A Python tool for automating updates to the New Zealand Aeronautical Information Publication (AIP). kiwiAIRAC parses the official AIP checklist, determines which pages have been updated since a given AIRAC effective date, downloads the relevant PDF documents, and stitches them together into print-ready files — grouped by paper colour (white, yellow, green, pink) — ready for duplex printing.

## What it does

The NZ AIP is published as a set of loose-leaf volumes that are periodically updated via AIRAC (Aeronautical Information Regulation And Control) cycles. Each cycle, a checklist PDF is published listing every page, its effective date, and which volume(s) it belongs to.

**kiwiAIRAC automates the tedious process of:**

1. **Downloading** the latest checklist from [aip.net.nz](https://www.aip.net.nz/)
2. **Parsing** the checklist tables to identify updated pages (using [camelot-py](https://github.com/camelot-dev/camelot) for PDF table extraction)
3. **Filtering** by subscription type (Planning / Instrument / Visual) and effective date
4. **Resolving** download URLs for every AIP section — General (GEN), En Route (ENR), Aerodromes (AD), and Aerodrome Charts
5. **Downloading** all required PDF documents with caching, rate-limiting, retries, and concurrent downloads
6. **Stitching** pages into colour-separated, duplex-aware PDF files ready to print

## Requirements

- **Python ≥ 3.14**
- [uv](https://docs.astral.sh/uv/) (recommended for dependency management)

## Installation

```bash
# Clone the repository
git clone https://github.com/j-chad/kiwiAIRAC.git
cd kiwiAIRAC

# Install dependencies with uv
uv sync
```

## Usage

Edit `main.py` to configure your subscription type and the AIRAC effective date you want to update from, then run:

```bash
uv run main.py
```

### Subscription Types

| Subscription | Volumes |
|---|---|
| `Subscription.PLANNING` | Volume 1 |
| `Subscription.INSTRUMENT` | Volumes 2 & 3 |
| `Subscription.VISUAL` | Volume 4 |

### Output

The `stitch` function produces PDF files in the output directory, one per paper colour:

- `WHITE.pdf` — standard pages
- `YELLOW.pdf` — yellow pages (flagged with `Y`)
- `GREEN.pdf` — green pages (flagged with `G`)
- `PINK.pdf` — emergency procedures (ENR section)

Each PDF is ordered for **duplex long-edge printing**, so front/back page pairs are correctly aligned.

## How Caching Works

Downloaded files are cached in the platform-specific user cache directory under `kiwiAIRAC/`. Cached files are considered fresh for **7 days** by default. Cache filenames are derived from a SHA-256 hash of the source URL, so identical URLs always resolve to the same cache entry. Concurrent downloads to the same URL are automatically de-duplicated.
