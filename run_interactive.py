#!/usr/bin/env python3
"""
Script per avviare l'applicazione in modalità interattiva
Risolve il problema dell'EOFError quando l'app non può leggere l'input
"""

import os
import sys
import subprocess
import signal
import time

def run_interactive():
    """Avvia l'applicazione in modalità interattiva"""
    print("=" * 60)
    print("     ANAC JSON DOWNLOADER - MODALITÀ INTERATTIVA")
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
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Ambiente virtuale creato")
    
    # Attiva ambiente virtuale e avvia applicazione
    print("🚀 Avvio applicazione...")
    
    try:
        # Usa subprocess per avviare l'applicazione con input/output interattivo
        process = subprocess.Popen(
            [sys.executable, "run_anacd2.py"],
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
            bufsize=0,  # Unbuffered
            universal_newlines=True
        )
        
        # Gestisci interruzioni
        def signal_handler(signum, frame):
            print("\n🛑 Interruzione rilevata, chiusura applicazione...")
            process.terminate()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Attendi che il processo finisca
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Interruzione dall'utente")
        if 'process' in locals():
            process.terminate()
    except Exception as e:
        print(f"❌ Errore durante l'esecuzione: {e}")
        if 'process' in locals():
            process.terminate()
        sys.exit(1)

if __name__ == "__main__":
    run_interactive()
