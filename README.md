# Torrent to Google Drive (Direct & Resumable)

A robust, command-driven Google Colab notebook to download torrents **directly** to Google Drive using `rclone` and `libtorrent`.

## Features

*   **Direct Download**: Writes directly to Google Drive (via Rclone cache), saving local disk space.
*   **Resumable**: Automatically saves `.fastresume` checkpoints. If you stop and restart, it resumes instantly without re-checking.
*   **Graceful Stop**: Handles the Colab "Stop" button safely by saving progress before exiting.
*   **Fast**: Uses `libtorrent` with sequential download mode for optimal cloud performance.

## Usage

1.  **Upload**: Upload `Torrent_Downloader.ipynb` to [Google Colab](https://colab.research.google.com/).
2.  **Setup**: Run Cell 1 to install dependencies.
3.  **Mount Drive (First Time Only)**: Run Cell 2.
    *   It will launch the `rclone config` tool.
    *   Type `n` (New remote).
    *   Name it `gdrive`.
    *   Select `drive` (Google Drive).
    *   Follow the prompts (leave client_id/secret blank).
    *   When asked for "Use web browser", type `n`.
    *   Click the link, login, copy the code, and paste it.
    *   Quit with `q`.
4.  **Download**: Run Cell 3.
    *   Paste your Magnet Link.
    *   Watch it fly!

## Resuming

To resume a download:
1.  Open a new Colab session.
2.  Run Cell 1 & 2 (Rclone config is saved if you didn't factory reset the runtime, otherwise re-auth).
3.  Run Cell 3 and paste the **same magnet link**.
4.  It will detect the `.fastresume` file and resume instantly.

## Disclaimer

This tool is for educational purposes only. Please respect copyright laws.