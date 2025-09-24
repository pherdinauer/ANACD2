#!/usr/bin/env python3
"""
Script per avviare l'applicazione senza Playwright
Usa solo le funzionalità che non richiedono browser
"""

import os
import sys
import time

def run_without_playwright():
    """Avvia l'applicazione senza Playwright"""
    print("=" * 60)
    print("     ANAC JSON DOWNLOADER - NO PLAYWRIGHT MODE")
    print("=" * 60)
    
    # Disabilita Playwright
    os.environ['NO_PLAYWRIGHT'] = '1'
    
    # Verifica che il file esista
    if not os.path.exists("run_anacd2.py"):
        print("❌ File run_anacd2.py non trovato!")
        print("Assicurati di essere nella directory corretta del progetto.")
        sys.exit(1)
    
    # Verifica ambiente virtuale
    if not os.path.exists("venv"):
        print("⚠️  Ambiente virtuale non trovato!")
        print("Creazione ambiente virtuale...")
        import subprocess
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Ambiente virtuale creato")
    
    print("🚀 Avvio applicazione senza Playwright...")
    print("ℹ️  Modalità disponibili:")
    print("   - Download da URL specifico")
    print("   - Download con smistamento automatico")
    print("   - Gestione cache e link")
    print("   - Verifica integrità file")
    print("")
    
    try:
        # Importa e avvia l'applicazione
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from json_downloader.cli import ANACDownloaderCLI
        
        # Crea CLI e avvia
        cli = ANACDownloaderCLI()
        
        # Avvia l'applicazione
        cli.run()
        
    except ImportError as e:
        print(f"❌ Errore di importazione: {e}")
        print("Prova a eseguire: python3 fix_config.py")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Errore durante l'esecuzione: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_without_playwright()
