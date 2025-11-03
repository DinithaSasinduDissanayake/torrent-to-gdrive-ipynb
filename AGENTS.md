# Agent Guidelines (Concise)

- Project: Colab-focused `.ipynb` notebooks (v3 GUI, v2 advanced, v1 legacy)
- Run in Colab; v3 is single-cell. v2 run top→bottom.
- Auto-install deps in cells; use `install_if_missing()` and `IN_COLAB` detection.
- Python: type hints, docstrings for complex funcs; snake_case; PascalCase classes; private helpers `_name`.
- Paths: `/content/torrents` local; `/content/drive/MyDrive/Torrent` on Drive.
- Error handling: specific exceptions; emoji messages; fallbacks for Colab vs local.
- Cleanup: always dispose libtorrent session/handle (finally/context) to avoid leaks.
- Trackers/resume: allow adding public trackers; support resume data where applicable.
- UX: analyze → select → download → upload; disable buttons to guide flow; show progress/ETA.
- Legal: include ToS warnings in README/notebook.
