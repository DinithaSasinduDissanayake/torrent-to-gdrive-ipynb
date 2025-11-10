# 🚀 Torrent to Google Drive - Colab GUI

## ✅ YES, This GUI Works Perfectly in Colab!

The GUI uses **ipywidgets** which is fully supported in Google Colab's interface. All interactive elements (buttons, dropdowns, progress bars, checkboxes) will render and work correctly.

---

## 🎯 Quick Start (3 Steps)

### 1. Upload to Colab
- Open [Google Colab](https://colab.research.google.com/)
- Upload `torrent_colab_optimized.py` using the Files panel (📁 icon on left)

### 2. Run the Script
```python
!python torrent_colab_optimized.py
```

### 3. Use the GUI
The interactive GUI will appear with:
- ✅ Buttons that you can click
- ✅ Text areas for magnet links
- ✅ Checkboxes for file selection
- ✅ Progress bars showing download status
- ✅ Dropdowns for file selection
- ✅ Real-time activity log

---

## 🧪 Test First (Optional)

Want to verify ipywidgets work in your Colab environment? Run this first:

```python
!python test_colab_widgets.py
```

If you see interactive widgets, the main app will work!

---

## 📋 How to Use

### Step 1: Enter Magnet Link
1. Paste your magnet link in the text area
2. Click "🔍 Analyze" button
3. Wait for file list to appear (usually 10-60 seconds)

### Step 2: Select Files & Download
1. Check/uncheck files you want (or use "All"/"None" buttons)
2. Optional: Enable "Auto-zip" to create a zip file
3. Click "⬇️ Download" button
4. Watch progress bar and log for status

### Step 3: Upload to Drive
1. Select downloaded file from dropdown
2. Enter Drive folder name (default: "Torrent")
3. Click "☁️ Upload" button
4. Authenticate with Google when prompted

---

## 🎨 GUI Features

### Interactive Elements:
- **Buttons**: Click to trigger actions
- **Text Areas**: Paste magnet links
- **Checkboxes**: Select specific files
- **Progress Bars**: Real-time download/upload progress
- **Dropdowns**: Choose files to upload
- **Activity Log**: Color-coded status messages

### Visual Feedback:
- 🔵 Blue = Info/In Progress
- 🟢 Green = Success
- 🟠 Orange = Warning
- 🔴 Red = Error

---

## ⚙️ Optimizations for Colab

This script is specifically optimized for Colab:

### Network Optimizations
- ✅ 9 working public trackers pre-configured
- ✅ 500 max peer connections (high bandwidth)
- ✅ Upload limited to 10KB/s (preserves resources)
- ✅ DHT & Local Service Discovery enabled

### Performance Optimizations
- ✅ Parallel dependency installation
- ✅ Automatic memory cleanup after downloads
- ✅ Efficient widget rendering (updates every 5%)
- ✅ Proper libtorrent session disposal

### User Experience
- ✅ Compact layout (minimal scrolling)
- ✅ Clear progress indicators
- ✅ Timestamped activity log
- ✅ File size formatting (MB/GB)

---

## 🆚 Why Use This vs Running Notebook Cells?

### Advantages of Python Script:
1. **Single Command**: `!python file.py` - done!
2. **No Cell Management**: No need to run cells in order
3. **Better Resource Cleanup**: Automatic session disposal
4. **Easier Sharing**: Just share one .py file
5. **Version Control**: Easier to track changes

### When to Use Notebook Instead:
- You want to modify code inline
- You prefer step-by-step execution
- You're learning/experimenting

---

## 📊 What Works in Colab

### ✅ Fully Supported:
- ipywidgets (buttons, dropdowns, checkboxes, etc.)
- Progress bars with real-time updates
- Callback functions (button clicks, checkbox changes)
- HTML rendering in widgets
- Threading for background tasks
- Google Drive API integration
- File uploads/downloads

### ⚠️ Limitations:
- Colab sessions timeout after ~12 hours of inactivity
- Large downloads may be interrupted if session disconnects
- Storage limited to Colab VM disk space (~100GB)

---

## 🔧 Troubleshooting

### GUI Not Showing?
```python
# Try enabling widgets explicitly
from google.colab import output
output.enable_custom_widget_manager()

# Then run the script
!python torrent_colab_optimized.py
```

### Widgets Look Broken?
```python
# Reinstall ipywidgets
!pip install --upgrade ipywidgets
!python torrent_colab_optimized.py
```

### "Module not found" errors?
The script auto-installs dependencies, but if it fails:
```python
!pip install ipywidgets libtorrent google-api-python-client google-auth-httplib2 google-auth-oauthlib
!python torrent_colab_optimized.py
```

### Drive Upload Fails?
Make sure you authenticated when prompted. If not:
```python
from google.colab import auth
auth.authenticate_user()
```

---

## 💡 Pro Tips

1. **Large Torrents**: Enable "Auto-zip" to compress before uploading to Drive
2. **Multiple Files**: Select only the files you need to save bandwidth
3. **Resume Support**: If interrupted, restart the script - some trackers support resume
4. **Faster Analysis**: Public trackers help find metadata quicker
5. **Monitor Progress**: Check the log for detailed peer/speed info

---

## ⚠️ Legal Notice

**Only download content you legally own or have permission to access!**

This tool is for:
- ✅ Legal torrents (Linux ISOs, open source software)
- ✅ Content you own
- ✅ Public domain materials

Not for:
- ❌ Copyrighted content without permission
- ❌ Piracy
- ❌ Terms of service violations

---

## 🤝 Need Help?

### Common Questions:

**Q: How long does "Analyze" take?**  
A: Usually 10-60 seconds, depends on seeders and metadata availability.

**Q: Can I download multiple torrents?**  
A: Yes, run the script again for each torrent (or run analyze → download multiple times).

**Q: Where are files saved?**  
A: Temporarily in `/content/torrents` on Colab VM, then uploaded to Drive.

**Q: Does this work offline?**  
A: No, requires internet connection for torrents and Drive uploads.

**Q: Can I use my own trackers?**  
A: Yes! The script adds public trackers, but your magnet link trackers are preserved.

---

## 📁 Files in This Project

- `torrent_colab_optimized.py` - Main optimized script with GUI
- `test_colab_widgets.py` - Test script to verify widgets work
- `torrent_notebook_v3_gui.ipynb` - Original notebook version
- `README_COLAB_GUI.md` - This file

---

## 🎉 Ready to Go!

Your GUI **will work** in Colab! Just upload and run:

```python
!python torrent_colab_optimized.py
```

Enjoy! 🚀
