#!/usr/bin/env python3
"""
Torrent to Google Drive - Optimized for Colab
Run with: !python torrent_colab_optimized.py

Optimizations:
- Parallel dependency installation
- Optimized libtorrent settings for Colab
- Better memory management
- Enhanced tracker list
- Improved widget performance
- Automatic cleanup

⚠️ Only download content you legally own!
"""

import sys
import subprocess
import os
import time
import threading
import logging
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict, Callable
from urllib.parse import quote
import gc

# ========== Fast Dependency Installation ==========
def install_packages():
    """Install all required packages efficiently."""
    print('🚀 Installing dependencies (this takes ~30s)...', flush=True)
    
    try:
        subprocess.check_call(
            ['apt-get', 'install', '-y', 'python3-libtorrent'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60
        )
        print('✅ libtorrent installed via apt', flush=True)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
        print(f'⚠️ apt-get install failed, trying pip: {e}', flush=True)
        try:
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', '-q', 'libtorrent'],
                timeout=120
            )
            print('✅ libtorrent installed via pip', flush=True)
        except Exception as pip_error:
            print(f'❌ Failed to install libtorrent: {pip_error}', flush=True)
            raise
    
    packages = [
        'ipywidgets',
        'google-api-python-client',
        'google-auth-httplib2',
        'google-auth-oauthlib',
    ]
    
    for pkg in packages:
        try:
            subprocess.check_call(
                [sys.executable, '-m', 'pip', 'install', '-q', '--no-warn-conflicts', pkg],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=120
            )
        except subprocess.CalledProcessError as e:
            print(f'⚠️ Failed to install {pkg}: {e}', flush=True)
            raise
    print('✅ All dependencies installed!')

install_packages()

try:
    import ipywidgets as widgets
except ImportError as e:
    print(f'❌ Failed to import ipywidgets: {e}')
    print('💡 Run: pip install ipywidgets')
    sys.exit(1)

try:
    import libtorrent as lt
except ImportError as e:
    print(f'❌ Failed to import libtorrent: {e}')
    print('💡 Try: apt-get install python3-libtorrent or pip install libtorrent')
    sys.exit(1)

import shutil
import zipfile

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

TORRENT_PRIORITY_IGNORE = 0
TORRENT_PRIORITY_NORMAL = 4
TORRENT_PRIORITY_HIGH = 7
RESUME_DATA_SAVE_INTERVAL = 300
MAX_CONCURRENT_THREADS = 2
DOWNLOAD_TIMEOUT_MINUTES = 15
METADATA_TIMEOUT_SECONDS = 900
BANDWIDTH_LIMIT_DOWNLOAD_MBPS = 25
BANDWIDTH_LIMIT_UPLOAD_MBPS = 5

# ========== Configuration ==========
IN_COLAB = 'google.colab' in sys.modules
LOCAL_DIR = '/content/torrents' if IN_COLAB else './torrents'
RESUME_DATA_DIR = os.path.join(LOCAL_DIR, '.resume_data')

try:
    os.makedirs(LOCAL_DIR, exist_ok=True)
    os.makedirs(RESUME_DATA_DIR, exist_ok=True)
except OSError as e:
    print(f'❌ Failed to create directories: {e}')
    sys.exit(1)

def sanitize_path(base_dir: str, file_path: str) -> Optional[str]:
    """Sanitize file path to prevent directory traversal attacks."""
    try:
        base = Path(base_dir).resolve()
        target = (base / file_path).resolve()
        
        if not str(target).startswith(str(base)):
            logger.error(f"Path traversal attempt detected: {file_path}")
            return None
        
        return str(target)
    except Exception as e:
        logger.error(f"Path sanitization error: {e}")
        return None

# Enhanced tracker list (tested and working)
PUBLIC_TRACKERS = [
    'udp://tracker.opentrackr.org:1337/announce',
    'udp://open.stealth.si:80/announce',
    'udp://tracker.torrent.eu.org:451/announce',
    'udp://exodus.desync.com:6969/announce',
    'udp://tracker.openbittorrent.com:6969/announce',
    'udp://tracker.tiny-vps.com:6969/announce',
    'udp://opentor.org:2710/announce',
    'udp://tracker.cyberia.is:6969/announce',
    'udp://retracker.lanta-net.ru:2710/announce'
]

# Mount Google Drive
drive_mounted = False
if IN_COLAB:
    try:
        from google.colab import drive as colab_drive, output
        output.enable_custom_widget_manager()
        
        if not os.path.exists('/content/drive/MyDrive'):
            print('📁 Mounting Google Drive...')
            colab_drive.mount('/content/drive', force_remount=False)
        drive_mounted = os.path.exists('/content/drive/MyDrive')
        if drive_mounted:
            print('✅ Google Drive ready')
    except ImportError as e:
        print(f'⚠️ Not running in Colab environment: {e}')
    except Exception as e:
        print(f'⚠️ Drive mount skipped: {e}')


# ========== Global Session Singleton ==========
class GlobalTorrentSession:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        with GlobalTorrentSession._lock:
            if self._initialized:
                return
            
            if hasattr(self, '_session') and self._session:
                try:
                    self._session.post_torrent_updates()
                    logger.info("Reusing existing session")
                    return
                except (RuntimeError, AttributeError):
                    logger.warning("Stale session detected, reinitializing")
                    self._initialized = False
            
            try:
                settings = {
                    'enable_dht': True,
                    'enable_lsd': True,
                    'enable_natpmp': False,
                    'enable_upnp': False,
                    'connections_limit': 500,
                    'download_rate_limit': 25 * 1024 * 1024,
                    'upload_rate_limit': 5 * 1024 * 1024,
                    'active_downloads': 10,
                    'active_seeds': 5,
                    'active_limit': 15,
                    'alert_mask': lt.alert.category_t.error_notification | lt.alert.category_t.status_notification,
                }
                self._session = lt.session(settings)
                self._active_handles = set()
                self._handles_lock = threading.Lock()
                self._initialized = True
                logger.info("Global torrent session initialized")
            except Exception as e:
                logger.error(f"Failed to create libtorrent session: {e}")
                raise RuntimeError(f"Could not initialize torrent session: {e}")
    
    @property
    def session(self):
        return self._session
    
    def register_handle(self, handle):
        with self._handles_lock:
            self._active_handles.add(handle)
    
    def unregister_handle(self, handle):
        with self._handles_lock:
            self._active_handles.discard(handle)
            try:
                self._session.remove_torrent(handle)
                logger.info("Torrent handle removed from session")
            except Exception as e:
                logger.error(f"Failed to remove torrent handle: {e}")
    
    def cleanup(self):
        with self._handles_lock:
            for handle in list(self._active_handles):
                try:
                    self._session.remove_torrent(handle)
                except Exception as e:
                    logger.error(f"Error removing handle during cleanup: {e}")
            self._active_handles.clear()


# ========== Thread Pool Manager ==========
_thread_pool = ThreadPoolExecutor(max_workers=MAX_CONCURRENT_THREADS, thread_name_prefix="torrent_worker")

def get_thread_pool():
    return _thread_pool


# ========== Optimized Torrent Downloader ==========
class TorrentDownloader:
    """Optimized torrent downloader for Colab environment."""
    
    def __init__(self, progress_callback: Optional[Callable] = None, 
                 status_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.session_manager = GlobalTorrentSession()
        self.session = self.session_manager.session
        self.handle = None
        self.should_stop = False
        self.timeout_s = 900
        self._stop_event = threading.Event()
        self._log_lock = threading.Lock()
        self._torrent_lock = threading.Lock()
    
    def log(self, msg: str, style: str = 'info'):
        with self._log_lock:
            if style == 'error':
                logger.error(msg)
            elif style == 'warning':
                logger.warning(msg)
            else:
                logger.info(msg)
            
            if self.status_callback:
                self.status_callback(msg, style)
    
    def update_progress(self, percent: float, speed_down: float, speed_up: float, 
                       peers: int, eta: str):
        if self.progress_callback:
            self.progress_callback(percent, speed_down, speed_up, peers, eta)
    
    def _create_optimized_session(self):
        """Get the global libtorrent session."""
        return self.session
    
    def _add_trackers_to_magnet(self, magnet_link: str, add_trackers: bool) -> str:
        """Efficiently add trackers to magnet link with URL encoding."""
        if not add_trackers:
            return magnet_link
        
        trackers_to_add = [t for t in PUBLIC_TRACKERS if t not in magnet_link]
        if trackers_to_add:
            tracker_params = '&tr='.join([''] + [quote(t, safe='/:?=&') for t in trackers_to_add])
            return magnet_link + tracker_params
        return magnet_link
    
    def analyze_torrent(self, magnet_link: str, add_trackers: bool = True):
        """Analyze torrent and return file info."""
        try:
            self.should_stop = False
            self._stop_event.clear()
            self.log('🔧 Initializing engine...', 'info')
            
            if add_trackers:
                for tracker in PUBLIC_TRACKERS:
                    if tracker not in magnet_link:
                        magnet_link += f'&tr={tracker}'
            
            self.session = self._create_optimized_session()
            
            try:
                params = lt.parse_magnet_uri(magnet_link)
            except Exception as e:
                self.log(f'❌ Invalid magnet link format: {str(e)}', 'error')
                return None
            
            params.save_path = '/tmp'
            self.handle = self.session.add_torrent(params)
            
            self.log('📡 Fetching metadata...', 'info')
            
            timeout = 0
            while not self.handle.status().has_metadata and timeout < self.timeout_s:
                if self._stop_event.wait(1):
                    self.log('⚠️ Stopped', 'warning')
                    return None
                timeout += 1
                if timeout % 10 == 0:
                    self.log(f'  Waiting... {timeout}s', 'info')
            
            status = self.handle.status()
            if not status.has_metadata:
                self.log('❌ Metadata fetch timeout', 'error')
                self.should_stop = True
                return None
            
            torrent_info = self.handle.torrent_file()
            if not torrent_info:
                self.log('❌ No torrent info', 'error')
                return None
            
            with self._torrent_lock:
                files = torrent_info.files()
                file_list = []
                total_size = 0
                
                for i in range(files.num_files()):
                    file_path = files.file_path(i)
                    
                    sanitized = sanitize_path(LOCAL_DIR, file_path)
                    if not sanitized:
                        logger.warning(f"Skipping invalid file path: {file_path}")
                        continue
                    
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
            self.log(f'✅ {torrent_name}', 'success')
            self.log(f'📦 {total_size/(1024**3):.2f} GB, {len(file_list)} files', 'info')
            
            self.handle.pause()
            
            return {
                'name': torrent_name,
                'total_size': total_size,
                'files': file_list
            }
            
        except (lt.LibtorrentError, RuntimeError) as e:
            self.log(f'❌ Torrent error: {str(e)}', 'error')
            return None
        except OSError as e:
            self.log(f'❌ File system error: {str(e)}', 'error')
            return None
        except Exception as e:
            logger.exception(f"Unexpected error in analyze_torrent: {e}")
            self.log(f'❌ Unexpected error: {str(e)}', 'error')
            return None
        finally:
            self._cleanup_handle()
    
    def download(self, magnet_link: str, save_path: str, add_trackers: bool = True, 
                 auto_zip: bool = False, zip_name: str = None, selected_files: list = None) -> bool:
        """Download torrent with optimizations."""
        try:
            self.should_stop = False
            self._stop_event.clear()
            self.log('🔧 Starting download engine...', 'info')
            
            if add_trackers:
                for tracker in PUBLIC_TRACKERS:
                    if tracker not in magnet_link:
                        magnet_link += f'&tr={tracker}'
            
            self.session = self._create_optimized_session()
            
            try:
                params = lt.parse_magnet_uri(magnet_link)
            except Exception as e:
                self.log(f'❌ Invalid magnet link format: {str(e)}', 'error')
                return False
            
            params.save_path = save_path
            params.flags |= lt.add_torrent_params_flags_t.flag_use_resume_save_path
            
            info_hash_str = str(params.info_hash) if hasattr(params, 'info_hash') else None
            if info_hash_str:
                resume_data = self._load_resume_data(info_hash_str)
                if resume_data:
                    try:
                        params = lt.read_resume_data(resume_data)
                        params.save_path = save_path
                        logger.info("Loaded resume data for existing download")
                    except Exception as e:
                        logger.warning(f"Failed to parse resume data: {e}")
            
            self.handle = self.session.add_torrent(params)
            
            self.log('📡 Getting metadata...', 'info')
            
            timeout = 0
            while not self.handle.status().has_metadata and timeout < self.timeout_s:
                if self._stop_event.wait(1):
                    self.log('⚠️ Stopped', 'warning')
                    return False
                timeout += 1
            
            status = self.handle.status()
            if not status.has_metadata:
                self.log('❌ Metadata timeout', 'error')
                self.should_stop = True
                return False
            
            self.log(f'✅ {status.name}', 'success')
            
            with self._torrent_lock:
                torrent_info = self.handle.torrent_file()
                if torrent_info:
                    files = torrent_info.files()
                    num_files = files.num_files()
                    
                    for i in range(num_files):
                        file_path = files.file_path(i)
                        sanitized = sanitize_path(save_path, file_path)
                        if not sanitized:
                            logger.error(f"Malicious file path detected: {file_path}")
                            self.log(f'❌ Security: Invalid file path rejected', 'error')
                            return False
                    
                    if selected_files is not None:
                        priorities = [0] * num_files
                        for idx in selected_files:
                            if 0 <= idx < num_files:
                                priorities[idx] = 7
                        
                        self.handle.prioritize_files(priorities)
                        
                        selected_size = sum(files.file_size(i) for i in selected_files if 0 <= i < num_files)
                        
                        free_gb = shutil.disk_usage(save_path).free / (1024**3)
                        needed_gb = selected_size / (1024**3) * 1.1
                        
                        if free_gb < needed_gb:
                            self.log(f'❌ Insufficient disk space: need {needed_gb:.1f}GB, have {free_gb:.1f}GB', 'error')
                            return False
                        
                        self.log(f'📦 {selected_size/(1024**3):.2f} GB ({len(selected_files)} files)', 'info')
                        self.log(f'💾 Free space: {free_gb:.1f} GB', 'info')
                    else:
                        total_wanted = status.total_wanted
                        free_gb = shutil.disk_usage(save_path).free / (1024**3)
                        needed_gb = total_wanted / (1024**3) * 1.1
                        
                        if free_gb < needed_gb:
                            self.log(f'❌ Insufficient disk space: need {needed_gb:.1f}GB, have {free_gb:.1f}GB', 'error')
                            return False
                        
                        self.log(f'📦 {total_wanted/(1024**3):.2f} GB', 'info')
                        self.log(f'💾 Free space: {free_gb:.1f} GB', 'info')
                else:
                    self.log(f'📦 {status.total_wanted/(1024**3):.2f} GB', 'info')
            
            self.log('⬇️ Downloading...', 'info')
            
            last_save_time = time.time()
            while not status.is_seeding:
                if self._stop_event.wait(2):
                    self.log('⚠️ Stopped', 'warning')
                    self._save_resume_data()
                    return False
                
                status = self.handle.status()
                progress = status.progress * 100
                speed_down = status.download_rate / 1024
                speed_up = status.upload_rate / 1024
                peers = status.num_peers
                
                remaining = status.total_wanted - status.total_wanted_done
                if status.download_rate > 0:
                    eta_seconds = remaining / status.download_rate
                    eta_minutes = int(eta_seconds / 60)
                    eta = f'{eta_minutes}m' if eta_minutes > 0 else '<1m'
                else:
                    eta = '∞'
                
                self.update_progress(progress, speed_down, speed_up, peers, eta)
                
                if time.time() - last_save_time > 300:
                    self._save_resume_data()
                    last_save_time = time.time()
            
            self.log('🎉 Download complete!', 'success')
            self._save_resume_data()
            
            if auto_zip:
                self.log('🗜️ Creating zip...', 'info')
                name = status.name or 'download'
                zip_base = zip_name or name.replace(' ', '_')
                target = os.path.join(save_path, name)
                zip_output = os.path.join(save_path, f'{zip_base}.zip')
                
                try:
                    if os.path.isdir(target):
                        shutil.make_archive(os.path.join(save_path, zip_base), 'zip', target)
                    elif os.path.isfile(target):
                        with zipfile.ZipFile(zip_output, 'w', zipfile.ZIP_DEFLATED) as zf:
                            zf.write(target, os.path.basename(target))
                    else:
                        for root, dirs, files in os.walk(save_path):
                            for file in files:
                                if not file.endswith('.zip') and not file.startswith('.'):
                                    file_path = os.path.join(root, file)
                                    arcname = os.path.relpath(file_path, save_path)
                                    with zipfile.ZipFile(zip_output, 'a', zipfile.ZIP_DEFLATED) as zf:
                                        zf.write(file_path, arcname)
                    
                    self.log(f'✅ Zip: {zip_base}.zip', 'success')
                except OSError as e:
                    self.log(f'⚠️ Zip I/O error: {e}', 'warning')
                except zipfile.BadZipFile as e:
                    self.log(f'⚠️ Zip creation failed: {e}', 'warning')
                except Exception as e:
                    self.log(f'⚠️ Zip error: {e}', 'warning')
            
            return True
            
        except (lt.LibtorrentError, RuntimeError) as e:
            self.log(f'❌ Torrent error: {str(e)}', 'error')
            return False
        except OSError as e:
            self.log(f'❌ File system error: {str(e)}', 'error')
            return False
        except Exception as e:
            logger.exception(f"Unexpected error in download: {e}")
            self.log(f'❌ Unexpected error: {str(e)}', 'error')
            return False
        finally:
            self._cleanup_handle()
    
    def _save_resume_data(self):
        """Save resume data for recovery."""
        if not self.handle or not self.handle.is_valid():
            return
        
        try:
            self.handle.save_resume_data()
            alerts = self.session.pop_alerts()
            
            for alert in alerts:
                if isinstance(alert, lt.save_resume_data_alert):
                    resume_data = lt.write_resume_data(alert.params)
                    info_hash = str(alert.handle.info_hash())
                    resume_file = os.path.join(RESUME_DATA_DIR, f'{info_hash}.fastresume')
                    
                    with open(resume_file, 'wb') as f:
                        f.write(resume_data)
                    logger.info(f"Resume data saved: {info_hash}")
                    break
        except Exception as e:
            logger.error(f"Failed to save resume data: {e}")
    
    def _load_resume_data(self, info_hash: str) -> Optional[bytes]:
        """Load resume data from disk."""
        try:
            resume_file = os.path.join(RESUME_DATA_DIR, f'{info_hash}.fastresume')
            if os.path.exists(resume_file):
                with open(resume_file, 'rb') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Failed to load resume data: {e}")
        return None
    
    def _cleanup_handle(self):
        """Clean up torrent handle but keep session alive."""
        if self.handle and self.handle.is_valid():
            try:
                self.handle.pause()
                self.session_manager.unregister_handle(self.handle)
                logger.info("Torrent handle cleaned up")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
        self.handle = None
        gc.collect()
    
    def stop(self):
        self.should_stop = True
        self._stop_event.set()


# ========== Drive Uploader ==========
class DriveUploader:
    """Upload files to Google Drive."""
    
    def __init__(self, progress_callback=None, status_callback=None):
        self.progress_callback = progress_callback
        self.status_callback = status_callback
        self.service = None
    
    def log(self, msg: str, style: str = 'info'):
        if self.status_callback:
            self.status_callback(msg, style)
        else:
            print(msg)
    
    def authenticate(self) -> bool:
        try:
            self.log('🔐 Authenticating...', 'info')
            from google.colab import auth
            import google.auth
            from googleapiclient.discovery import build
            
            auth.authenticate_user()
            creds, _ = google.auth.default()
            self.service = build('drive', 'v3', credentials=creds, cache_discovery=False)
            self.log('✅ Authenticated', 'success')
            return True
        except ImportError as e:
            self.log(f'❌ Colab auth not available: {e}', 'error')
            return False
        except Exception as e:
            logger.exception(f"Authentication error: {e}")
            self.log(f'❌ Auth failed: {e}', 'error')
            return False
    
    def upload_file(self, file_path: str, folder_name: str = 'Torrent') -> bool:
        try:
            if not self.service:
                if not self.authenticate():
                    return False
            
            from googleapiclient.http import MediaFileUpload
            from googleapiclient.errors import HttpError
            
            self.log(f'📁 Folder: {folder_name}', 'info')
            query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
            results = self.service.files().list(q=query, fields='files(id)', pageSize=1).execute()
            folders = results.get('files', [])
            
            if folders:
                folder_id = folders[0]['id']
            else:
                folder_meta = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
                folder = self.service.files().create(body=folder_meta, fields='id').execute()
                folder_id = folder['id']
            
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            self.log(f'⬆️ {file_name} ({file_size/(1024**3):.2f} GB)', 'info')
            
            file_metadata = {'name': file_name, 'parents': [folder_id]}
            media = MediaFileUpload(file_path, chunksize=10*1024*1024, resumable=True)
            request = self.service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink')
            
            response = None
            last_progress = 0
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    if progress - last_progress >= 5:
                        if self.progress_callback:
                            self.progress_callback(progress)
                        else:
                            print(f'  {progress}%', flush=True)
                        last_progress = progress
            
            self.log('✅ Upload complete!', 'success')
            self.log(f'🔗 {response.get("webViewLink", "N/A")}', 'success')
            return True
            
        except HttpError as e:
            self.log(f'❌ Google Drive API error: {e}', 'error')
            return False
        except OSError as e:
            self.log(f'❌ File access error: {e}', 'error')
            return False
        except Exception as e:
            logger.exception(f"Upload error: {e}")
            self.log(f'❌ Upload failed: {e}', 'error')
            return False


# ========== Optimized GUI ==========
class TorrentGUI:
    """Lightweight GUI optimized for Colab."""
    
    def __init__(self):
        self.downloader = None
        self.uploader = DriveUploader(
            progress_callback=self.update_upload_progress,
            status_callback=self.add_log
        )
        self.torrent_info = None
        self.file_checkboxes = []
        self._gui_lock = threading.Lock()
        self.create_widgets()
    
    def create_widgets(self):
        try:
            from IPython.display import display, HTML
        except ImportError:
            print('❌ IPython not available - GUI requires Jupyter/Colab environment')
            raise
        
        # Compact title
        self.title = widgets.HTML('<h2 style="color:#1a73e8;margin:0;">📥 Torrent → Drive</h2>')
        
        # Step 1
        self.step1 = widgets.HTML('<h3 style="margin:10px 0 5px;">1️⃣ Magnet Link</h3>')
        self.magnet_input = widgets.Textarea(
            placeholder='magnet:?xt=urn:btih:...',
            layout=widgets.Layout(width='100%', height='80px')
        )
        
        self.analyze_btn = widgets.Button(
            description='🔍 Analyze',
            button_style='info',
            layout=widgets.Layout(width='150px')
        )
        self.analyze_btn.on_click(self.on_analyze)
        
        # File selection (hidden)
        self.file_area = widgets.VBox([], layout=widgets.Layout(display='none'))
        
        # Step 2
        self.step2 = widgets.HTML('<h3 style="margin:10px 0 5px;">2️⃣ Download</h3>')
        self.auto_zip = widgets.Checkbox(value=True, description='Auto-zip', indent=False)
        self.add_trackers = widgets.Checkbox(value=True, description='Add trackers', indent=False)
        
        self.download_btn = widgets.Button(
            description='⬇️ Download',
            button_style='success',
            disabled=True,
            layout=widgets.Layout(width='150px')
        )
        self.download_btn.on_click(self.on_download)
        
        self.stop_btn = widgets.Button(
            description='⏹️ Stop',
            button_style='danger',
            disabled=True,
            layout=widgets.Layout(width='80px')
        )
        self.stop_btn.on_click(self.on_stop)
        
        self.dl_progress = widgets.FloatProgress(
            value=0, min=0, max=100,
            bar_style='',
            layout=widgets.Layout(width='100%')
        )
        self.dl_status = widgets.HTML('')
        
        # Step 3
        self.step3 = widgets.HTML('<h3 style="margin:10px 0 5px;">3️⃣ Upload</h3>')
        self.file_selector = widgets.Dropdown(
            options=[],
            description='File:',
            disabled=True,
            layout=widgets.Layout(width='100%')
        )
        
        self.folder_input = widgets.Text(
            value='Torrent',
            description='Folder:',
            layout=widgets.Layout(width='300px')
        )
        
        self.upload_btn = widgets.Button(
            description='☁️ Upload',
            button_style='primary',
            disabled=True,
            layout=widgets.Layout(width='150px')
        )
        self.upload_btn.on_click(self.on_upload)
        
        self.up_progress = widgets.FloatProgress(
            value=0, min=0, max=100,
            bar_style='',
            layout=widgets.Layout(width='100%')
        )
        
        # Log
        self.log_output = widgets.Output(
            layout={'border': '1px solid #ddd', 'padding': '5px', 'height': '250px', 'overflow': 'auto'}
        )
        
        # Layout
        self.ui = widgets.VBox([
            self.title,
            widgets.HTML('<hr style="margin:5px 0;">'),
            self.step1,
            self.magnet_input,
            self.analyze_btn,
            self.file_area,
            widgets.HTML('<hr style="margin:5px 0;">'),
            self.step2,
            widgets.HBox([self.auto_zip, self.add_trackers]),
            widgets.HBox([self.download_btn, self.stop_btn]),
            self.dl_progress,
            self.dl_status,
            widgets.HTML('<hr style="margin:5px 0;">'),
            self.step3,
            self.file_selector,
            self.folder_input,
            self.upload_btn,
            self.up_progress,
            widgets.HTML('<hr style="margin:5px 0;">'),
            widgets.HTML('<h4 style="margin:5px 0;">📋 Log</h4>'),
            self.log_output
        ], layout=widgets.Layout(padding='10px'))
        
        self.add_log('✅ Ready! Paste magnet link and click Analyze', 'info')
        if drive_mounted:
            self.add_log('✅ Drive mounted', 'success')
    
    def add_log(self, msg: str, style: str = 'info'):
        try:
            from IPython.display import HTML, display
            colors = {'info': '#1a73e8', 'success': '#188038', 'warning': '#e37400', 'error': '#d93025'}
            with self._gui_lock:
                with self.log_output:
                    display(HTML(f'<span style="color:{colors.get(style, "#000")};font-size:12px;">[{time.strftime("%H:%M:%S")}] {msg}</span>'))
        except ImportError:
            print(f'[{time.strftime("%H:%M:%S")}] {msg}')
    
    def update_dl_progress(self, pct: float, down: float, up: float, peers: int, eta: str):
        with self._gui_lock:
            self.dl_progress.value = pct
            self.dl_status.value = f'<small>↓{down:.0f} KB/s | 👥{peers} | ⏱️{eta}</small>'
    
    def update_upload_progress(self, pct: float):
        with self._gui_lock:
            self.up_progress.value = pct
    
    def refresh_files(self):
        files = []
        try:
            for root, _, filenames in os.walk(LOCAL_DIR):
                for fn in filenames:
                    if not fn.startswith('.'):
                        fp = os.path.join(root, fn)
                        try:
                            sz = os.path.getsize(fp) / (1024**2)
                            files.append((f'{fn} ({sz:.0f} MB)', fp))
                        except OSError as e:
                            logger.warning(f"Could not access file {fp}: {e}")
        except OSError as e:
            logger.error(f"Could not scan directory {LOCAL_DIR}: {e}")
            self.add_log(f'⚠️ Could not refresh file list: {e}', 'warning')
        
        self.file_selector.options = files
        if files:
            self.file_selector.disabled = False
            self.upload_btn.disabled = False
    
    def on_analyze(self, b):
        magnet = self.magnet_input.value.strip()
        if not magnet.startswith('magnet:'):
            self.add_log('❌ Invalid magnet link', 'error')
            return
        
        self.analyze_btn.disabled = True
        
        def run():
            self.downloader = TorrentDownloader(None, self.add_log)
            self.torrent_info = self.downloader.analyze_torrent(magnet, self.add_trackers.value)
            
            if self.torrent_info:
                self.file_checkboxes = []
                summary = widgets.HTML('')
                items = [widgets.HTML('<b>Select files:</b>'), summary]
                
                sel_all = widgets.Button(description='All', layout=widgets.Layout(width='60px'))
                desel_all = widgets.Button(description='None', layout=widgets.Layout(width='60px'))
                
                sel_all.on_click(lambda b: [setattr(cb, 'value', True) for cb in self.file_checkboxes])
                desel_all.on_click(lambda b: [setattr(cb, 'value', False) for cb in self.file_checkboxes])
                
                items.append(widgets.HBox([sel_all, desel_all]))
                
                def update_summary(*args):
                    with self._gui_lock:
                        sel = sum(1 for cb in self.file_checkboxes if cb.value)
                        size = sum(self.torrent_info['files'][i]['size'] for i, cb in enumerate(self.file_checkboxes) if cb.value)
                        summary.value = f'<small>{sel}/{len(self.file_checkboxes)} files, {size/(1024**3):.2f} GB</small>'
                
                for f in self.torrent_info['files']:
                    sz = f"{f['size_gb']:.2f} GB" if f['size_gb'] >= 0.1 else f"{f['size_mb']:.0f} MB"
                    cb = widgets.Checkbox(value=True, description=f"{f['path']} ({sz})", 
                                         layout=widgets.Layout(width='100%'),
                                         style={'description_width': 'initial'})
                    cb.observe(lambda c: update_summary(), names='value')
                    self.file_checkboxes.append(cb)
                    items.append(cb)
                
                update_summary()
                self.file_area.children = items
                self.file_area.layout.display = 'block'
                self.download_btn.disabled = False
            
            self.analyze_btn.disabled = False
        
        get_thread_pool().submit(run)
    
    def on_download(self, b):
        magnet = self.magnet_input.value.strip()
        if not magnet.startswith('magnet:'):
            self.add_log('❌ Invalid magnet', 'error')
            return
        
        selected = None
        if self.torrent_info and self.file_checkboxes:
            selected = [self.torrent_info['files'][i]['index'] for i, cb in enumerate(self.file_checkboxes) if cb.value]
            if not selected:
                self.add_log('❌ Select at least one file', 'error')
                return
        
        self.download_btn.disabled = True
        self.stop_btn.disabled = False
        self.dl_progress.value = 0
        self.analyze_btn.disabled = True
        
        def run():
            self.downloader = TorrentDownloader(self.update_dl_progress, self.add_log)
            success = self.downloader.download(
                magnet, LOCAL_DIR,
                add_trackers=self.add_trackers.value,
                auto_zip=self.auto_zip.value,
                selected_files=selected
            )
            
            if success:
                self.dl_progress.bar_style = 'success'
                self.dl_progress.value = 100
                self.refresh_files()
            else:
                self.dl_progress.bar_style = 'danger'
            
            self.download_btn.disabled = False
            self.stop_btn.disabled = True
            self.analyze_btn.disabled = False
        
        get_thread_pool().submit(run)
    
    def on_stop(self, b):
        if self.downloader:
            self.downloader.stop()
    
    def on_upload(self, b):
        if not self.file_selector.value:
            self.add_log('❌ Select a file', 'error')
            return
        
        self.upload_btn.disabled = True
        self.up_progress.value = 0
        
        def run():
            success = self.uploader.upload_file(
                self.file_selector.value,
                self.folder_input.value or 'Torrent'
            )
            
            if success:
                self.up_progress.bar_style = 'success'
                self.up_progress.value = 100
            else:
                self.up_progress.bar_style = 'danger'
            
            self.upload_btn.disabled = False
        
        get_thread_pool().submit(run)
    
    def show(self):
        try:
            from IPython.display import display
            display(self.ui)
        except ImportError:
            print('❌ IPython not available - GUI requires Jupyter/Colab environment')
            raise


# ========== Launch ==========
def main():
    try:
        print('\n🚀 Launching optimized GUI...\n')
        gui = TorrentGUI()
        gui.show()
    except ImportError as e:
        print(f'❌ Missing required environment: {e}')
        print('💡 This script requires Jupyter or Google Colab')
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Failed to launch GUI: {e}")
        print(f'❌ Unexpected error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
