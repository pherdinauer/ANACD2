#!/usr/bin/env python3
"""
Script per fixare i problemi di configurazione
"""

import os
import json
import sys

def fix_config():
    """Fix dei problemi di configurazione"""
    print("Fix problemi di configurazione...")
    
    # Verifica se il file config.json esiste
    config_file = "config.json"
    if not os.path.exists(config_file):
        print(f"File {config_file} non trovato, creazione...")
        
        # Crea config.json da config.example.json
        if os.path.exists("config.example.json"):
            with open("config.example.json", "r") as f:
                config = json.load(f)
            
            with open(config_file, "w") as f:
                json.dump(config, f, indent=2)
            
            print(f"✓ File {config_file} creato da config.example.json")
        else:
            print("✗ File config.example.json non trovato")
            return False
    
    # Verifica se le directory necessarie esistono
    directories = ["log", "cache", "downloads"]
    for directory in directories:
        if not os.path.exists(directory):
            print(f"Creazione directory {directory}...")
            os.makedirs(directory, exist_ok=True)
            print(f"✓ Directory {directory} creata")
    
    # Verifica se la directory /database/JSON esiste
    database_dir = "/database/JSON"
    if not os.path.exists(database_dir):
        print(f"Creazione directory {database_dir}...")
        try:
            os.makedirs(database_dir, exist_ok=True)
            print(f"✓ Directory {database_dir} creata")
        except PermissionError:
            print(f"⚠ Impossibile creare {database_dir} - permessi insufficienti")
            print("Esegui: sudo mkdir -p /database/JSON && sudo chown $USER:$USER /database/JSON")
    
    # Test caricamento configurazione
    print("Test caricamento configurazione...")
    try:
        with open(config_file, "r") as f:
            config = json.load(f)
        
        print("✓ Configurazione caricata correttamente")
        print(f"  - Download dir: {config.get('download_dir', 'N/A')}")
        print(f"  - Log file: {config.get('log_file', 'N/A')}")
        print(f"  - Timeout: {config.get('timeout', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"✗ Errore nel caricamento configurazione: {e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("  FIX CONFIGURAZIONE ANAC JSON DOWNLOADER")
    print("=" * 50)
    
    if fix_config():
        print("\n✅ Configurazione fixata!")
        sys.exit(0)
    else:
        print("\n❌ Problemi con la configurazione!")
        sys.exit(1)
