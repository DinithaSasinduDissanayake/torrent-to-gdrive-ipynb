# Agent Guidelines for Torrent to GDrive Notebook

## Project Overview
Jupyter notebook project (`.ipynb` files) designed for Google Colab. Three versions available:
- `torrent_notebook_v3_gui.ipynb` - Single-cell GUI for beginners
- `torrent_notebook_v2.ipynb` - Advanced with code examples, resume capability, Drive API
- `torrent_notebook_v1.ipynb` - Legacy reference version

No traditional build/test/lint infrastructure. No Cursor or Copilot rules defined.

## Running & Testing
- Open notebooks in Google Colab (recommended) or local Jupyter
- Run cells sequentially from top to bottom
- Dependencies auto-install via `pip` in notebook cells
- Test by running example cells or GUI interface
- No unit tests - validation via manual execution in Colab

## Code Style

### Imports
- Standard library first, then third-party, then local imports
- Use conditional Colab detection: `IN_COLAB = 'google.colab' in sys.modules`
- Fallback install pattern: try import, except `subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', package])`
- Import check helper: `install_if_missing(package, import_name=None)`

### Python Conventions
- **Type hints required** in function signatures: `def download_colab(magnet_link: str, save_path: str, max_peers: int = 400) -> bool:`
- **Docstrings required** for complex functions with `Args:` and `Returns:` sections
- **snake_case** for functions/variables, **PascalCase** for classes
- **Private helpers** prefixed with `_`: `_fmt_size()`, `_create_session()`, `_fmt_eta()`
- Default save paths: `/content/torrents` (local) or `/content/drive/MyDrive/Torrent` (Drive mounted)

### Error Handling
- Use specific exception types: `except (AttributeError, TypeError, ValueError)`
- Fallback logic for Colab vs local environments
- Silent pass for optional features, print warnings for failures (with emoji)
- **Always cleanup** resources: `finally:` blocks or context managers for sessions/handles
- Keyboard interrupt handling with resume data saving

### Formatting & UX
- 4-space indentation (no tabs)
- Keep notebook cells focused on single responsibilities
- **Use emoji** in user messages: ✅ success, 📦 installing, ⚠️ warnings, 🚀 starting, 📡 fetching
- Clear markdown cells with headers, instructions, and legal warnings
- Progress bars and ETA for long operations

## Key Patterns Observed
- **Auto-install**: `subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', 'libtorrent==2.0.11'])`
- **Session cleanup**: Store `session`/`handle` and cleanup in `finally` blocks to prevent memory leaks
- **Progress callbacks**: Pass `progress_callback` and `status_callback` functions for UI updates
- **Resume capability**: Save/load resume data via `resume_file` parameter for interrupted downloads
- **Settings fallback**: Try `lt.session(settings)`, fallback to `settings_pack` + `apply_settings` for compatibility
- **Helper functions**: `_fmt_size()`, `_fmt_eta()`, `_add_trackers_to_magnet()` for formatting

## Critical Requirements
- **Legal warnings required**: Always include ToS warnings about legal content and respecting Google Colab/Drive terms
- **Resource cleanup required**: libtorrent sessions must be cleaned up to prevent memory leaks
- **Error recovery**: Implement robust fallbacks for Drive mount failures, package install issues, etc.
