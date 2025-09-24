#!/usr/bin/env python3
"""
Test script per verificare che tutti gli import funzionino correttamente
"""

import sys
import os

# Aggiungi la directory corrente al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Testa tutti gli import necessari"""
    print("Test import...")
    
    try:
        # Test import del modulo json_downloader
        print("1. Test import json_downloader...")
        import json_downloader
        print("   ✓ json_downloader importato")
        
        # Test import delle classi principali
        print("2. Test import classi principali...")
        from json_downloader.cli import ANACDownloaderCLI
        print("   ✓ ANACDownloaderCLI importato")
        
        from json_downloader.scraper import load_config, scrape_all_json_links
        print("   ✓ scraper importato")
        
        from json_downloader.downloader import download_file, download_with_auto_sorting
        print("   ✓ downloader importato")
        
        from json_downloader.utils import setup_logger, scan_existing_files, determine_target_folder, should_skip_download
        print("   ✓ utils importato")
        
        # Test caricamento configurazione
        print("3. Test caricamento configurazione...")
        config = load_config()
        if config:
            print("   ✓ Configurazione caricata")
            print(f"   - Download dir: {config.get('download_dir', 'N/A')}")
            print(f"   - Log file: {config.get('log_file', 'N/A')}")
        else:
            print("   ✗ Errore nel caricamento configurazione")
            return False
        
        # Test creazione CLI
        print("4. Test creazione CLI...")
        cli = ANACDownloaderCLI()
        print("   ✓ CLI creata")
        
        print("\n🎉 Tutti i test sono passati!")
        return True
        
    except ImportError as e:
        print(f"   ✗ Errore di import: {e}")
        return False
    except Exception as e:
        print(f"   ✗ Errore generico: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("  TEST IMPORT ANAC JSON DOWNLOADER")
    print("=" * 50)
    
    if test_imports():
        print("\n✅ Tutto funziona correttamente!")
        sys.exit(0)
    else:
        print("\n❌ Ci sono problemi con gli import!")
        sys.exit(1)
