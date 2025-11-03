# Torrent to GDrive (notebook)

This repository contains Jupyter Notebooks that download data locally and upload results to Google Drive. Prefer the Drive API resumable upload flow for higher reliability than Drive mount writes, especially on large transfers.

Contents:
- `torrent_notebook_v2.ipynb` — improved torrent engine + Drive API uploader (recommended)
- `torrent_notebook_v1.ipynb` — earlier version

## Drive API Uploads (Resumable, Recommended)
Why: avoids Drive mount stalls on large transfers, adds retries/backoff, and verifies integrity via MD5.

Where: open `torrent_notebook_v2.ipynb` and run the section “Example 5: Download locally, then upload to Drive via API”.

### Quick Start (Colab)
1. Open `torrent_notebook_v2.ipynb` in Colab.
2. Set your `magnet` and optional `drive_folder_name` in Example 5.
3. Run cells top-to-bottom. The flow will:
   - Download to `/content/torrents` using libtorrent.
   - Zip the download to reduce small-file overhead.
   - Authenticate (Colab prompt) and upload to Drive via the official API using resumable chunks.
   - Verify MD5 on Drive and print a file URL.

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