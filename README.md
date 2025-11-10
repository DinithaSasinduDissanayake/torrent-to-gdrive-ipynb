# Torrent to GDrive

Download torrents and upload them to Google Drive using libtorrent and Google Drive API.

## Choose Your Version

### GUI Notebook: `torrent_notebook_v3_gui.ipynb` (Recommended)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/DinithaSasinduDissanayake/torrent-to-gdrive-ipynb/blob/main/torrent_notebook_v3_gui.ipynb)

**Easy single-cell GUI interface** - just paste and click!
- One cell to run - everything auto-installs
- Interactive widgets with progress bars
- 4-step workflow: Paste magnet → Analyze → Download → Upload
- Perfect for quick downloads

### Standalone Script: `torrent_to_gdrive_standalone.py`

**Run with `!python torrent_to_gdrive_standalone.py` in Colab**
- Upload the .py file to Colab
- Same GUI functionality as the notebook
- Easier to version control and edit

## Quick Start

1. Open `torrent_notebook_v3_gui.ipynb` in Google Colab **OR** upload `torrent_to_gdrive_standalone.py` and run with `!python torrent_to_gdrive_standalone.py`
2. Run the cell (everything installs automatically)
3. Paste your magnet link in the text box
4. Click "Analyze Torrent" and review the file list
5. Select the files you want (or use Select All/Deselect All)
6. Click "Start Download"
7. Click "Upload to Drive" when complete

That's it! The interface handles authentication, analysis, selection, progress tracking, and upload.

## Features

- **File Selection**: Analyze torrents before downloading and choose specific files
- **Auto-Zip**: Optionally create zip archives after download
- **Public Trackers**: Auto-add trackers for better peer discovery
- **Progress Tracking**: Real-time download/upload progress with speed and ETA
- **Google Drive Integration**: Direct upload to Google Drive with folder organization

## Important Notes
- Only download content you have legal rights to access
- Respect Google Colab and Google Drive terms of service
- Drive upload limit: ~750 GB per day
- Colab free tier: ~12h max with 90m idle timeout
- Large files may take time depending on seeders

## Archive

Legacy notebooks (v1, v2) and additional documentation are in the `archive/` directory.