"""
ANAC JSON Downloader Package
"""

__version__ = "2.0.0"
__author__ = "ANAC Downloader Team"

# Import main classes for easy access
from .cli import ANACDownloaderCLI
from .downloader import download_file, download_with_auto_sorting
from .scraper import scrape_all_json_links
from .utils import setup_logger, scan_existing_files, determine_target_folder, should_skip_download

__all__ = [
    'ANACDownloaderCLI',
    'download_file',
    'download_with_auto_sorting',
    'scrape_all_json_links',
    'setup_logger',
    'scan_existing_files',
    'determine_target_folder',
    'should_skip_download'
]
