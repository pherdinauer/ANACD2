#!/usr/bin/env python3
"""
ANAC JSON Downloader - Launcher Script
Avvia l'applicazione di download file JSON ANAC gestendo correttamente i percorsi e gli import
"""

import os
import sys
import traceback
from pathlib import Path

def setup_environment():
    """Configure the environment to ensure modules can be properly imported."""
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the script directory to the Python path if it's not already there
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)
    
    # Ensure required directories exist
    for directory in ['log', 'cache', 'downloads']:
        os.makedirs(os.path.join(script_dir, directory), exist_ok=True)
    
    # Check for virtual environment and recommend activation if not active
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("ATTENZIONE: Non stai eseguendo in un ambiente virtuale.")
        print("Suggerimento: Attiva l'ambiente virtuale prima di eseguire questo script.")
        print("  Windows: venv\\Scripts\\activate")
        print("  Linux/Mac: source venv/bin/activate")

def run_cli():
    """Run the CLI interface."""
    try:
        # First try importing as a package
        try:
            from json_downloader.cli import ANACDownloaderCLI
            cli = ANACDownloaderCLI()
            cli.run()
        except ImportError:
            # Fallback to direct import
            from cli import ANACDownloaderCLI
            cli = ANACDownloaderCLI()
            cli.run()
    except ImportError as e:
        print(f"Errore di importazione: {e}")
        traceback.print_exc()
        print("\nProva a installare le dipendenze con:")
        print("pip install -r requirements.txt")
    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("=" * 60)
    print("     ANAC JSON DOWNLOADER - LAUNCHER")
    print("=" * 60)
    
    # Setup environment and paths
    setup_environment()
    
    # Run the application
    try:
        run_cli()
    except KeyboardInterrupt:
        print("\nOperazione interrotta dall'utente. Uscita.")
    except Exception as e:
        print(f"Errore critico: {e}")
        traceback.print_exc()
        print("\nL'applicazione si è chiusa a causa di un errore.")
        sys.exit(1) 