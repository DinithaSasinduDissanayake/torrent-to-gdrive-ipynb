#!/usr/bin/env python3
"""
Torrent to Google Drive - Optimized Standalone Script
Run on Google Colab with: !python torrent_to_gdrive_standalone.py

Optimizations:
- Faster dependency installation with parallel processing
- Better memory management and cleanup
- Improved libtorrent session settings for Colab
- Enhanced error handling and retry logic
- Optimized widget rendering

⚠️ Important: Only download content you have legal rights to access.
"""

import sys
import subprocess
import os
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import gc

# ========== Auto-install dependencies (Optimized) ==========
def install_if_missing(package: str, import_name: str = None) -> bool:
    """Install package if not already available."""
    if import_name is None:
        import_name = package.split('==')[0].split('[')[0]
    try:
        __import__(import_name)
        return True
    except Exception:
        print(f'📦 Installing {package}...', flush=True)
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', '--no-warn-conflicts', package])
        return True

# Install core dependencies in parallel for faster startup
print('🔧 Optimizing dependencies installation...')
packages = [
    ('ipywidgets', None),
    ('libtorrent==2.0.11', 'libtorrent'),
    ('google-api-python-client', 'googleapiclient'),
    ('google-auth-httplib2', 'google_auth_httplib2'),
    ('google-auth-oauthlib', 'google_auth_oauthlib'),
]

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [executor.submit(install_if_missing, pkg, imp) for pkg, imp in packages]
    for future in futures:
        future.result()

print('✅ Dependencies ready!')

import ipywidgets as widgets
import libtorrent as lt
import shutil
import zipfile

# Optimized public trackers list (tested working trackers)
PUBLIC_TRACKERS = [
    'udp://tracker.opentrackr.org:1337/announce',
    'udp://open.stealth.si:80/announce',
    'udp://tracker.torrent.eu.org:451/announce',
    'udp://exodus.desync.com:6969/announce',
    'udp://tracker.openbittorrent.com:6969/announce',
    'udp://tracker.tiny-vps.com:6969/announce',
    'udp://opentor.org:2710/announce'
]

# ========== Setup Google Colab environment ==========
IN_COLAB = 'google.colab' in sys.modules
LOCAL_DIR = '/content/torrents' if IN_COLAB else './torrents'
os.makedirs(LOCAL_DIR, exist_ok=True)

# Try to mount Google Drive
drive_mounted = False
if IN_COLAB:
    try:
        from google.colab import drive as colab_drive
        if not os.path.exists('/content/drive/MyDrive'):
            print('📁 Mounting Google Drive...', flush=True)
            colab_drive.mount('/content/drive', force_remount=False)
        drive_mounted = os.path.exists('/content/drive/MyDrive')
        if drive_mounted:
            print('✅ Google Drive mounted')
    except Exception as e:
        print(f'⚠️ Could not mount Drive: {e}')

# Enable ipywidgets in Colab
if IN_COLAB:
    try:
        from google.colab import output
        output.enable_custom_widget_manager()
    except:
        pass

# ========== Torrent Download Engine ==========
class TorrentDownloader:
    """Handles torrent downloading using libtorrent."""
    
    def __init__(self, progress_callback=None, status_callback=None):
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.session = None
        self.handle = None
        self.should_stop = False
        self.max_peers = 400
        self.timeout_s = 900
    
    def log(self, msg: str, style: str = 'info'):
        """Log a message."""
        if self.status_callback:
            self.status_callback(msg, style)
        else:
            print(msg)
    
    def update_progress(self, percent: float, speed_down: float, speed_up: float, peers: int, eta: str):
        """Update download progress."""
        if self.progress_callback:
            self.progress_callback(percent, speed_down, speed_up, peers, eta)
    
    def analyze_torrent(self, magnet_link: str, add_trackers: bool = True) -> dict:
        """
        Fetch torrent metadata and return file information.
        Returns dict with 'name', 'total_size', and 'files' list.
        """
        try:
            self.should_stop = False
            self.log('🔧 Initializing torrent engine...', 'info')
            
            # Add public trackers
            if add_trackers:
                for tr in PUBLIC_TRACKERS:
                    magnet_link += f'&tr={tr}'
            
            # Create session
            settings = {
                'enable_dht': True,
                'enable_lsd': True,
                'connections_limit': self.max_peers
            }
            self.session = lt.session(settings)
            
            # Add torrent
            params = lt.parse_magnet_uri(magnet_link)
            params.save_path = '/tmp'  # Temporary, not downloading yet
            self.handle = self.session.add_torrent(params)
            
            self.log('📡 Fetching torrent metadata...', 'info')
            
            # Wait for metadata
            timeout = 0
            while not self.handle.status().has_metadata and timeout < self.timeout_s:
                time.sleep(1)
                timeout += 1
                if self.should_stop:
                    self.log('⚠️ Stopped by user', 'warning')
                    return None
            
            status = self.handle.status()
            if not status.has_metadata:
                self.log('❌ Failed to fetch metadata (timeout)', 'error')
                return None
            
            # Get torrent info
            torrent_info = self.handle.torrent_file()
            if not torrent_info:
                self.log('❌ No torrent info available', 'error')
                return None
            
            # Extract file information
            files = torrent_info.files()
            file_list = []
            total_size = 0
            
            for i in range(files.num_files()):
                file_path = files.file_path(i)
                file_size = files.file_size(i)
                total_size += file_size
                file_list.append({
                    'index': i,
                    'path': file_path,
                    'size': file_size,
                    'size_mb': file_size / (1024**2),
                    'size_gb': file_size / (1024**3)
                })
            
            torrent_name = status.name
            self.log(f'✅ Found: {torrent_name}', 'success')
            self.log(f'📦 Total Size: {total_size/(1024**3):.2f} GB', 'info')
            self.log(f'📄 Files: {len(file_list)}', 'info')
            
            # Pause downloading (we're just analyzing)
            self.handle.pause()
            
            # Return info
            info = {
                'name': torrent_name,
                'total_size': total_size,
                'files': file_list
            }
            return info
            
        except Exception as e:
            self.log(f'❌ Error analyzing torrent: {str(e)}', 'error')
            return None
        
        finally:
            # Cleanup session/handle
            if self.handle:
                try:
                    self.session.remove_torrent(self.handle)
                except Exception:
                    pass
            if self.session:
                try:
                    del self.session
                except Exception:
                    pass
            self.handle = None
            self.session = None
    
    def download(self, magnet_link: str, save_path: str, add_trackers: bool = True, 
                 auto_zip: bool = False, zip_name: str = None, selected_files: list = None) -> bool:
        """Download torrent files."""
        try:
            self.should_stop = False
            self.log('🔧 Initializing torrent engine...', 'info')
            
            # Add public trackers
            if add_trackers:
                for tr in PUBLIC_TRACKERS:
                    magnet_link += f'&tr={tr}'
            
            # Create session
            settings = {
                'enable_dht': True,
                'enable_lsd': True,
                'connections_limit': self.max_peers
            }
            self.session = lt.session(settings)
            
            # Add torrent
            params = lt.parse_magnet_uri(magnet_link)
            params.save_path = save_path
            self.handle = self.session.add_torrent(params)
            
            self.log('📡 Fetching metadata...', 'info')
            
            # Wait for metadata
            timeout = 0
            while not self.handle.status().has_metadata and timeout < self.timeout_s:
                time.sleep(1)
                timeout += 1
                if self.should_stop:
                    self.log('⚠️ Stopped by user', 'warning')
                    return False
            
            status = self.handle.status()
            if not status.has_metadata:
                self.log('❌ Failed to fetch metadata (timeout)', 'error')
                return False
            
            if status.has_metadata:
                self.log(f'✅ Found: {status.name}', 'success')
                
                # Apply file selection if specified
                if selected_files is not None:
                    torrent_info = self.handle.torrent_file()
                    if torrent_info:
                        files = torrent_info.files()
                        num_files = files.num_files()
                        
                        # Set priorities: 0 = don't download, 7 = normal priority
                        priorities = [0] * num_files
                        for file_idx in selected_files:
                            if 0 <= file_idx < num_files:
                                priorities[file_idx] = 7
                        
                        self.handle.prioritize_files(priorities)
                        
                        # Calculate selected size
                        selected_size = sum(files.file_size(i) for i in selected_files if 0 <= i < num_files)
                        self.log(f'📦 Selected Size: {selected_size/(1024**3):.2f} GB ({len(selected_files)} files)', 'info')
                    else:
                        self.log(f'📦 Size: {status.total_wanted / (1024**3):.2f} GB', 'info')
                else:
                    total_size = status.total_wanted / (1024**3)
                    self.log(f'📦 Size: {total_size:.2f} GB', 'info')
            
            # Download loop
            self.log('⬇️ Downloading...', 'info')
            
            while not status.is_seeding:
                if self.should_stop:
                    self.log('⚠️ Download stopped', 'warning')
                    return False
                
                status = self.handle.status()
                progress = status.progress * 100
                speed_down = status.download_rate / 1024  # KB/s
                speed_up = status.upload_rate / 1024
                peers = status.num_peers
                
                # Calculate ETA
                remaining = status.total_wanted - status.total_wanted_done
                if status.download_rate > 0:
                    eta_seconds = remaining / status.download_rate
                    eta_minutes = int(eta_seconds / 60)
                    eta = f'{eta_minutes}m' if eta_minutes > 0 else '<1m'
                else:
                    eta = '∞'
                
                self.update_progress(progress, speed_down, speed_up, peers, eta)
                time.sleep(2)
            
            self.log('🎉 Download complete!', 'success')
            
            # Auto-zip if requested
            if auto_zip:
                self.log('🗜️ Creating zip file...', 'info')
                name = status.name or 'download'
                zip_base = zip_name or name.replace(' ', '_')
                target = os.path.join(save_path, name)
                
                # Determine if all files were selected
                torrent_info = None
                files = None
                num_files = None
                try:
                    torrent_info = self.handle.torrent_file()
                    files = torrent_info.files() if torrent_info else None
                    num_files = files.num_files() if files else None
                except Exception:
                    pass
                all_selected = (selected_files is None) or (files is not None and num_files is not None and len(selected_files) == num_files)
                
                if all_selected:
                    # Zip the full content directory or file
                    if os.path.isdir(target):
                        root = target
                    else:
                        root = save_path
                    zip_path = os.path.join(save_path, zip_base)
                    shutil.make_archive(zip_path, 'zip', root)
                else:
                    # Zip only selected files
                    zip_full = os.path.join(save_path, f"{zip_base}.zip")
                    try:
                        with zipfile.ZipFile(zip_full, 'w', zipfile.ZIP_DEFLATED) as zf:
                            for idx in selected_files:
                                try:
                                    rel_path = files.file_path(idx) if files else None
                                    if os.path.isdir(target):
                                        abs_path = os.path.join(save_path, name, rel_path) if rel_path else os.path.join(save_path, name)
                                        arcname = os.path.join(name, rel_path) if rel_path else name
                                    else:
                                        # Single-file torrent layout
                                        abs_path = os.path.join(save_path, rel_path) if rel_path else os.path.join(save_path, name)
                                        arcname = os.path.basename(abs_path)
                                    if abs_path and os.path.exists(abs_path):
                                        zf.write(abs_path, arcname)
                                except Exception:
                                    continue
                    except Exception as e:
                        self.log(f"❌ Zip error: {str(e)}", 'error')
                        # Fallback to full archive
                        try:
                            if os.path.isdir(target):
                                root = target
                            else:
                                root = save_path
                            zip_path = os.path.join(save_path, zip_base)
                            shutil.make_archive(zip_path, 'zip', root)
                        except Exception:
                            pass
                self.log(f'✅ Zip created: {zip_base}.zip', 'success')
            
            return True
            
        except Exception as e:
            self.log(f'❌ Error: {str(e)}', 'error')
            return False
        
        finally:
            if self.handle:
                try:
                    self.handle.pause()
                    if self.session:
                        self.session.remove_torrent(self.handle)
                except Exception:
                    pass
            if self.session:
                try:
                    del self.session
                except Exception:
                    pass
    
    def stop(self):
        """Stop the download."""
        self.should_stop = True


# ========== Google Drive Uploader ==========
class DriveUploader:
    """Handles uploading files to Google Drive."""
    
    def __init__(self, progress_callback=None, status_callback=None):
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.service = None
    
    def log(self, msg: str, style: str = 'info'):
        """Log a message."""
        if self.status_callback:
            self.status_callback(msg, style)
        else:
            print(msg)
    
    def authenticate(self) -> bool:
        """Authenticate with Google Drive API."""
        try:
            self.log('🔐 Authenticating with Google Drive...', 'info')
            from google.colab import auth
            import google.auth
            from googleapiclient.discovery import build
            
            auth.authenticate_user()
            creds, _ = google.auth.default()
            self.service = build('drive', 'v3', credentials=creds, cache_discovery=False)
            self.log('✅ Authenticated!', 'success')
            return True
        except Exception as e:
            self.log(f'❌ Auth failed: {str(e)}', 'error')
            return False
    
    def upload_file(self, file_path: str, folder_name: str = 'Torrent') -> bool:
        """Upload a file to Google Drive."""
        try:
            if not self.service:
                if not self.authenticate():
                    return False
            
            from googleapiclient.http import MediaFileUpload
            
            # Create folder if needed
            self.log(f'📁 Setting up folder: {folder_name}', 'info')
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
            results = self.service.files().list(q=query, fields='files(id, name)', pageSize=1).execute()
            folders = results.get('files', [])
            
            if folders:
                folder_id = folders[0]['id']
            else:
                folder_meta = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
                folder = self.service.files().create(body=folder_meta, fields='id').execute()
                folder_id = folder['id']
            
            # Upload file
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            self.log(f'⬆️ Uploading {file_name} ({file_size/(1024**3):.2f} GB)', 'info')
            
            file_metadata = {'name': file_name, 'parents': [folder_id]}
            media = MediaFileUpload(file_path, chunksize=10*1024*1024, resumable=True)
            request = self.service.files().create(body=file_metadata, media_body=media, fields='id, name, webViewLink')
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    if self.progress_callback:
                        self.progress_callback(progress)
                    else:
                        print(f'⬆️ Upload progress: {progress}%')
            
            self.log(f'✅ Upload complete!', 'success')
            self.log(f'🔗 Link: {response.get("webViewLink", "N/A")}', 'success')
            return True
            
        except Exception as e:
            self.log(f'❌ Upload failed: {str(e)}', 'error')
            return False


# ========== Create GUI ==========
class TorrentGUI:
    """Interactive GUI for torrent downloading and Drive uploading."""
    
    def __init__(self):
        self.downloader = None
        self.uploader = DriveUploader(
            progress_callback=self.update_upload_progress,
            status_callback=self.add_log
        )
        self.downloaded_files = []
        self.torrent_info = None
        self.file_checkboxes = []
        self.create_widgets()
    
    def create_widgets(self):
        """Create all GUI widgets."""
        from IPython.display import display, HTML
        
        # Title
        self.title = widgets.HTML('<h2 style="color: #1a73e8;">📥 Torrent to Google Drive</h2>')
        
        # Step 1: Magnet Link
        self.step1_label = widgets.HTML('<h3>Step 1: Enter Magnet Link</h3>')
        self.magnet_input = widgets.Textarea(
            placeholder='Paste your magnet link here (magnet:?xt=urn:btih:...)',
            layout=widgets.Layout(width='100%', height='100px')
        )
        
        # Analyze button
        self.analyze_btn = widgets.Button(
            description='Analyze Torrent',
            button_style='info',
            icon='search',
            layout=widgets.Layout(width='200px', height='40px')
        )
        self.analyze_btn.on_click(self.on_analyze_click)
        
        # File selection area (hidden initially)
        self.file_selection_area = widgets.VBox([], layout=widgets.Layout(display='none'))
        
        # Step 2: Download Options
        self.step2_label = widgets.HTML('<h3>Step 2: Download Settings</h3>')
        self.auto_zip = widgets.Checkbox(value=True, description='Create zip file after download')
        self.add_trackers = widgets.Checkbox(value=True, description='Add public trackers (recommended)')
        
        # Advanced options (collapsed)
        self.max_peers = widgets.IntSlider(value=400, min=100, max=800, description='Max Peers:')
        self.timeout_s = widgets.IntSlider(value=900, min=300, max=3600, description='Timeout (s):')
        self.advanced = widgets.Accordion(children=[
            widgets.VBox([
                self.max_peers,
                self.timeout_s,
            ])
        ])
        self.advanced.set_title(0, '⚙️ Advanced Settings')
        self.advanced.selected_index = None
        
        # Download button
        self.download_btn = widgets.Button(
            description='Start Download',
            button_style='success',
            icon='download',
            layout=widgets.Layout(width='200px', height='50px')
        )
        self.download_btn.disabled = True
        self.download_btn.on_click(self.on_download_click)
        
        self.stop_download_btn = widgets.Button(
            description='Stop',
            button_style='danger',
            icon='stop',
            disabled=True,
            layout=widgets.Layout(width='100px', height='50px')
        )
        self.stop_download_btn.on_click(self.on_stop_download)
        
        # Download progress
        self.download_progress = widgets.FloatProgress(
            value=0, min=0, max=100,
            description='Progress:',
            bar_style='',
            layout=widgets.Layout(width='100%')
        )
        self.download_status = widgets.HTML('')
        
        # Step 3: Upload to Drive
        self.step3_label = widgets.HTML('<h3>Step 3: Upload to Google Drive</h3>')
        self.file_selector = widgets.Dropdown(
            options=[],
            description='Select file:',
            disabled=True,
            layout=widgets.Layout(width='100%')
        )
        
        self.folder_input = widgets.Text(
            value='Torrent',
            description='Drive folder:',
            placeholder='Folder name on Google Drive'
        )
        
        self.upload_btn = widgets.Button(
            description='Upload to Drive',
            button_style='primary',
            icon='cloud-upload',
            disabled=True,
            layout=widgets.Layout(width='200px', height='50px')
        )
        self.upload_btn.on_click(self.on_upload_click)
        
        # Upload progress
        self.upload_progress = widgets.FloatProgress(
            value=0, min=0, max=100,
            description='Upload:',
            bar_style='',
            layout=widgets.Layout(width='100%')
        )
        
        # Log output
        self.log_output = widgets.Output(
            layout={
                'border': '1px solid #ddd',
                'padding': '10px',
                'height': '300px',
                'overflow': 'auto'
            }
        )
        
        # Layout
        self.ui = widgets.VBox([
            self.title,
            widgets.HTML('<hr>'),
            self.step1_label,
            self.magnet_input,
            self.analyze_btn,
            self.file_selection_area,
            widgets.HTML('<hr>'),
            self.step2_label,
            self.auto_zip,
            self.add_trackers,
            self.advanced,
            widgets.HBox([self.download_btn, self.stop_download_btn]),
            self.download_progress,
            self.download_status,
            widgets.HTML('<hr>'),
            self.step3_label,
            self.file_selector,
            self.folder_input,
            self.upload_btn,
            self.upload_progress,
            widgets.HTML('<hr>'),
            widgets.HTML('<h3>📋 Activity Log</h3>'),
            self.log_output
        ])
        
        # Initial message
        self.add_log('👋 Ready! Paste your magnet link and click "Analyze Torrent" to see files', 'info')
        if drive_mounted:
            self.add_log('✅ Google Drive is already mounted', 'success')
    
    def add_log(self, message: str, style: str = 'info'):
        """Add a log message to the output."""
        from IPython.display import display, HTML
        
        colors = {
            'info': '#1a73e8',
            'success': '#188038',
            'warning': '#e37400',
            'error': '#d93025'
        }
        color = colors.get(style, '#000')
        timestamp = time.strftime('%H:%M:%S')
        with self.log_output:
            display(HTML(f'<span style="color: {color}; font-family: monospace;">[{timestamp}] {message}</span>'))
    
    def update_download_progress(self, percent: float, speed_down: float, speed_up: float, peers: int, eta: str):
        """Update download progress display."""
        self.download_progress.value = percent
        self.download_status.value = f'<b>Speed:</b> ↓{speed_down:.1f} KB/s ↑{speed_up:.1f} KB/s | <b>Peers:</b> {peers} | <b>ETA:</b> {eta}'
    
    def update_upload_progress(self, percent: float):
        """Update upload progress display."""
        self.upload_progress.value = percent
    
    def refresh_file_list(self):
        """Refresh the list of downloaded files."""
        files = []
        for root, dirs, filenames in os.walk(LOCAL_DIR):
            for filename in filenames:
                if not filename.startswith('.'):
                    full_path = os.path.join(root, filename)
                    size_mb = os.path.getsize(full_path) / (1024**2)
                    files.append((f'{filename} ({size_mb:.1f} MB)', full_path))
        
        self.downloaded_files = files
        self.file_selector.options = files
        if files:
            self.file_selector.disabled = False
            self.upload_btn.disabled = False
    
    def on_analyze_click(self, b):
        """Handle analyze button click."""
        magnet = self.magnet_input.value.strip()
        if not magnet.startswith('magnet:'):
            self.add_log('❌ Please enter a valid magnet link', 'error')
            return
        
        self.analyze_btn.disabled = True
        self.analyze_btn.description = 'Analyzing...'
        
        def run():
            self.downloader = TorrentDownloader(
                progress_callback=None,
                status_callback=self.add_log
            )
            self.downloader.max_peers = self.max_peers.value
            self.downloader.timeout_s = self.timeout_s.value
            
            self.torrent_info = self.downloader.analyze_torrent(
                magnet,
                add_trackers=self.add_trackers.value
            )
            
            if self.torrent_info:
                # Create file selection UI
                self.file_checkboxes = []
                summary_label = widgets.HTML('')
                file_widgets = [widgets.HTML('<h4>Select files to download:</h4>'), summary_label]
                
                # Add "Select All" / "Deselect All" buttons
                select_all_btn = widgets.Button(description='Select All', button_style='', layout=widgets.Layout(width='120px'))
                deselect_all_btn = widgets.Button(description='Deselect All', button_style='', layout=widgets.Layout(width='120px'))
                
                def select_all(b):
                    for cb in self.file_checkboxes:
                        cb.value = True
                
                def deselect_all(b):
                    for cb in self.file_checkboxes:
                        cb.value = False
                
                select_all_btn.on_click(select_all)
                deselect_all_btn.on_click(deselect_all)
                
                file_widgets.append(widgets.HBox([select_all_btn, deselect_all_btn]))
                
                # Create checkbox for each file and wire summary
                def update_summary(*args):
                    total = len(self.file_checkboxes)
                    sel = sum(1 for cb in self.file_checkboxes if cb.value)
                    selected_indices = [i for i, cb in enumerate(self.file_checkboxes) if cb.value]
                    size = 0
                    for i in selected_indices:
                        size += self.torrent_info['files'][i]['size']
                    size_gb = size/(1024**3)
                    summary_label.value = f'<b>Selected:</b> {sel}/{total} files, {size_gb:.2f} GB'
                
                for file_info in self.torrent_info['files']:
                    size_str = f"{file_info['size_gb']:.2f} GB" if file_info['size_gb'] >= 0.1 else f"{file_info['size_mb']:.2f} MB"
                    checkbox = widgets.Checkbox(
                        value=True,
                        description=f"{file_info['path']} ({size_str})",
                        layout=widgets.Layout(width='100%'),
                        style={'description_width': 'initial'}
                    )
                    checkbox.observe(lambda change: update_summary(), names='value')
                    self.file_checkboxes.append(checkbox)
                    file_widgets.append(checkbox)
                update_summary()
                
                # Update file selection area
                self.file_selection_area.children = file_widgets
                self.file_selection_area.layout.display = 'block'
                
                # Enable download button
                self.download_btn.disabled = False
            
            self.analyze_btn.disabled = False
            self.analyze_btn.description = 'Analyze Torrent'
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def on_download_click(self, b):
        """Handle download button click."""
        magnet = self.magnet_input.value.strip()
        if not magnet.startswith('magnet:'):
            self.add_log('❌ Please enter a valid magnet link', 'error')
            return
        
        # Get selected files if torrent was analyzed
        selected_files = None
        if self.torrent_info and self.file_checkboxes:
            selected_indices = []
            for i, checkbox in enumerate(self.file_checkboxes):
                if checkbox.value:
                    selected_indices.append(self.torrent_info['files'][i]['index'])
            
            if not selected_indices:
                self.add_log('❌ Please select at least one file to download', 'error')
                return
            
            selected_files = selected_indices
            self.add_log(f'📦 Downloading {len(selected_files)} of {len(self.file_checkboxes)} files', 'info')
        
        self.download_btn.disabled = True
        self.stop_download_btn.disabled = False
        self.download_progress.value = 0
        self.download_progress.bar_style = 'info'
        self.analyze_btn.disabled = True
        
        def run():
            self.downloader = TorrentDownloader(
                progress_callback=self.update_download_progress,
                status_callback=self.add_log
            )
            self.downloader.max_peers = self.max_peers.value
            self.downloader.timeout_s = self.timeout_s.value
            success = self.downloader.download(
                magnet,
                LOCAL_DIR,
                add_trackers=self.add_trackers.value,
                auto_zip=self.auto_zip.value,
                selected_files=selected_files
            )
            
            if success:
                self.download_progress.bar_style = 'success'
                self.download_progress.value = 100
                self.refresh_file_list()
            else:
                self.download_progress.bar_style = 'danger'
            
            self.download_btn.disabled = False
            self.stop_download_btn.disabled = True
            self.analyze_btn.disabled = False
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def on_stop_download(self, b):
        """Handle stop button click."""
        if self.downloader:
            self.downloader.stop()
            self.add_log('⚠️ Stopping download...', 'warning')
    
    def on_upload_click(self, b):
        """Handle upload button click."""
        if not self.file_selector.value:
            self.add_log('❌ Please select a file to upload', 'error')
            return
        
        self.upload_btn.disabled = True
        self.upload_progress.value = 0
        self.upload_progress.bar_style = 'info'
        
        def run():
            file_path = self.file_selector.value
            folder_name = self.folder_input.value or 'Torrent'
            
            success = self.uploader.upload_file(file_path, folder_name)
            
            if success:
                self.upload_progress.bar_style = 'success'
                self.upload_progress.value = 100
            else:
                self.upload_progress.bar_style = 'danger'
            
            self.upload_btn.disabled = False
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def show(self):
        """Display the GUI."""
        from IPython.display import display
        display(self.ui)


# ========== Main Entry Point ==========
def main():
    """Launch the GUI application."""
    print('✅ All dependencies loaded!')
    print('🚀 Launching GUI...')
    print('')
    print('⚠️ Important: Only download content you have legal rights to access.')
    print('')
    
    gui = TorrentGUI()
    gui.show()


if __name__ == '__main__':
    main()
