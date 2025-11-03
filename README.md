# Torrent to GDrive (notebook)

This repository contains Jupyter Notebooks that download torrents and upload them to Google Drive using the Drive API for reliable, resumable uploads.

## Choose Your Notebook

### For Beginners: `torrent_notebook_v3_gui.ipynb` (Recommended)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DinithaSasinduDissanayake/torrent-to-gdrive-ipynb/blob/main/torrent_notebook_v3_gui.ipynb)

**Easy single-cell GUI interface** - just paste and click!
- One cell to run - everything auto-installs
- Interactive widgets with progress bars
- 4-step workflow: Paste magnet → Analyze → Download → Upload
- Perfect for quick, one-time downloads

### For Developers: `torrent_notebook_v2.ipynb`
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DinithaSasinduDissanayake/torrent-to-gdrive-ipynb/blob/main/torrent_notebook_v2.ipynb)

**Advanced with code examples** - full control and customization
- Multiple usage examples and code patterns
- Resume capability for interrupted downloads
- Resource monitoring tools
- Drive API with MD5 verification
- Optional interactive GUI included

### Legacy: `torrent_notebook_v1.ipynb`
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DinithaSasinduDissanayake/torrent-to-gdrive-ipynb/blob/main/torrent_notebook_v1.ipynb)

Earlier version kept for reference

## Quick Start (v3 GUI)

1. Open `torrent_notebook_v3_gui.ipynb` in Google Colab
2. Run the single code cell (everything installs automatically)
3. Paste your magnet link in the text box
4. Click "Analyze Torrent" and review the file list
5. Select the files you want (or use Select All/Deselect All)
6. Click "Start Download" (Analyze must be run first)
7. Click "Upload to Drive" when complete

That's it! The notebook handles authentication, analysis, selection, progress tracking, and upload.

## Advanced Usage (v2)

For more control, open `torrent_notebook_v2.ipynb` which includes:

**Code Examples:**
- Multiple download patterns and configurations
- Resume capability for interrupted downloads  
- Manual Drive API upload with MD5 verification
- Resource monitoring during transfers

**Interactive GUI:**
- Optional widget-based interface
- Configurable peer limits and timeouts
- Progress bars and status logs

**Quick Start (v2):**
1. Open `torrent_notebook_v2.ipynb` in Colab
2. Run cells top-to-bottom to set up functions
3. Either:
   - Use Example 5 (code): Set your `magnet` and run the cell
   - Use the Interactive GUI: Run the GUI cell and use the interface

The v2 flow:
- Downloads to `/content/torrents` using libtorrent
- Optional auto-zip to reduce small-file overhead
- Authenticates and uploads via Drive API with resumable chunks
- Verifies MD5 and prints file URL

### Parameters
- `chunk_mb`: default 10 MB. 10–32 MB recommended (larger = fewer requests, more RAM).
- Folder handling: target Drive folder is created if missing.
- Deduplication: if a file with identical MD5 already exists on Drive, upload is skipped.

### Monitoring
- Optional `start_resource_monitor(interval, duration)` prints CPU/RAM/network throughput while downloading/uploading.

### Limits and ToS
- Only download/share content you are legally allowed to access. Respect Google Colab and Google Drive ToS.
- Drive throughput is typically ~40–50 MB/s writes; daily upload cap is ~750 GB.
- Colab sessions: free tier ~12h max with 90m idle timeout; Pro/Pro+ differ but still subject to preemption.
- Avoid >10k files per folder; zip/batch small files for reliability.

### rclone (optional)
If you prefer CLI-based sync, tune to reduce API throttling:
```
rclone copy <src> <remote>:<path> \
  --transfers 4 \
  --drive-chunk-size 32M
```
Note: API limits still apply; MD5 verification and backoff are handled differently than the notebook’s API uploader.

## Usage (Local Dev)
- Keep secrets out of the repo. Use Colab auth or Application Default Credentials (ADC) for local runs (set `GOOGLE_APPLICATION_CREDENTIALS` to a service account JSON).