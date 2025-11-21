# Agent Guidelines (Colab Torrent Downloader)

Based on best practices from GitHub, Builder.io, and the AGENTS.md standard, here are the definitive guidelines:

## 📁 Project Philosophy
- **Single Source of Truth**: Maintain exactly ONE `.ipynb` file in the repository root
- **Archive Everything Else**: Any additional files must be moved to an `archive/` folder immediately
- **Colab-First Design**: All code must be executable in Google Colab environment
- **Command-Driven Interface**: No GUI components; use intuitive command-line style interactions within Colab cells
- **Minimal Code**: Reduce code to the absolute minimum necessary for functionality
- **Zero Comments**: Code should be self-explanatory through clear naming; no comment lines allowed
- **Functionality First**: Code must work properly; minimalism shouldn't break core features

## 🎯 Core Purpose
- Create a single Colab-uploadable `.ipynb` notebook that downloads torrents directly to Google Drive
- Provide intuitive user interaction through command interface
- Minimize code lines while maximizing functionality
- Ensure all features are accessible via the command interface

## 📂 File Structure
- **Root Level**: Exactly one `.ipynb` file (no other files allowed)
- **Archive Folder**: All supporting files, old versions, or temporary files must reside in `archive/`
- **No Exceptions**: Do not create any other files in root (no .py files, no config files, no data files)

## 📝 Notebook Cell Architecture
- **Single Environment Cell**: All library installations, imports, and environment setup must be in ONE cell at the top
  - This cell should only be run once per Colab session
  - Include all `!pip install` commands
  - Include all `import` statements
  - Include Google Drive mounting logic
- **Separate User-Facing Cells**: Each user interaction point must be in its own cell
  - Torrent URL input cell
  - Download path selection cell
  - Download execution cell
  - Status check cell
  - Do NOT combine multiple user interactions into one cell

## 🔧 Library Usage Guidelines
### ✅ Choose Libraries That Are:
- Popular and well-maintained (active development, good community support)
- Have proper documentation (official docs, not just README)
- Available on Google Colab by default or easily installable
- Help reduce code verbosity

### ❌ Avoid Libraries That Are:
- Obscure or niche (<50 GitHub stars)
- Unmaintained (no commits in 12+ months)
- Lack proper documentation
- Require complex setup

### Examples of Good Choices (Not Requirements):
- `libtorrent` for torrent handling
- `google-colab` for Drive integration
- Standard library modules when possible

## 💻 Command Interface Design
- **Intuitive Commands**: Use clear function names like `download()`, `set_path()`, `status()`
- **Interactive Prompts**: Use `input()` for user interaction within cells
- **Clear Feedback**: Provide immediate, readable status updates
- **Simple Error Handling**: Handle errors gracefully but concisely; don't waste lines on verbose messages
- **State Persistence**: Remember user choices between cell executions

## 🔄 Development Workflow
### Commit Strategy:
- **Frequent Commits**: Commit after every functional change
- **Detailed Messages**: Write descriptive commit messages explaining WHAT changed and WHY
  - Example: `Add torrent URL validation to prevent invalid magnet links`
  - Example: `Refactor download logic from 50 to 15 lines`

### Push Strategy:
- **Push Immediately**: Push to remote branch after every commit
- **Branch Management**: Use feature branches for new capabilities
- **No Local-Only Work**: Avoid accumulating unpushed changes

## 📖 README Maintenance
- Maintain a `README.md` with clear instructions for users
- Update when significant features are added (but don't let this distract from coding)

## 🛠️ Tool Context
- **MCP Servers Available**: context7, deepwiki, local-memory
- **Web Search**: Use for library research and best practices (only high-quality sources)

## 🚀 Implementation Priorities
1. **Functionality First**: Ensure torrent downloading works reliably
2. **Code Minimization**: Refactor to reduce line count after each feature works
3. **User Experience**: Make command interface as intuitive as possible
4. **Library Optimization**: Switch libraries if a more concise alternative exists

## ⚠️ Critical Boundaries
- **Never**: Create additional files in root directory
- **Never**: Implement GUI components (tkinter, ipywidgets, etc.)
- **Never**: Add comments to code (self-documenting code only)
- **Never**: Use obscure or unmaintained libraries
- **Always**: Archive old files before creating new ones
- **Always**: Test in actual Colab environment
- **Always**: Commit with detailed messages
- **Always**: Push changes immediately

## 📊 Success Metrics
- Single `.ipynb` file in root (no other files)
- All features accessible via command interface
- Minimum possible lines of code (but functional)
- Zero comments in codebase
- Working Google Colab deployment
- All non-essential files in `archive/` folder