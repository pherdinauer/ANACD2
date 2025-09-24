#!/usr/bin/env python3
"""
Script per avviare l'applicazione e eseguire direttamente il download con smistamento automatico
"""

import os
import sys
import time

def run_with_auto_sorting():
    """Avvia l'applicazione e esegue il download con smistamento automatico"""
    print("=" * 60)
    print("     ANAC JSON DOWNLOADER - AUTO SORTING MODE")
    print("=" * 60)
    
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
    
    # Attiva ambiente virtuale
    venv_python = os.path.join("venv", "bin", "python")
    if not os.path.exists(venv_python):
        venv_python = os.path.join("venv", "Scripts", "python.exe")
    
    if not os.path.exists(venv_python):
        print("❌ Python dell'ambiente virtuale non trovato!")
        sys.exit(1)
    
    print("🚀 Avvio applicazione con smistamento automatico...")
    
    try:
        # Importa e avvia l'applicazione
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        from json_downloader.cli import ANACDownloaderCLI
        
        # Crea CLI e avvia con smistamento automatico
        cli = ANACDownloaderCLI()
        
        # Esegui direttamente il download con smistamento automatico
        print("📥 Avvio download con smistamento automatico...")
        cli.download_with_auto_sorting()
        
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
    run_with_auto_sorting()
