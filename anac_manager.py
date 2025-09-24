#!/usr/bin/env python3
"""
ANAC JSON Downloader - Manager Completo
Script unificato per deployment, aggiornamento e gestione del progetto
"""

import os
import sys
import subprocess
import json
import shutil
import time
from pathlib import Path

class Colors:
    """Colori per output colorato"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

def print_colored(text, color=Colors.WHITE):
    """Stampa testo colorato"""
    print(f"{color}{text}{Colors.NC}")

def print_header():
    """Stampa l'intestazione del manager"""
    print_colored("=" * 60, Colors.CYAN)
    print_colored("     ANAC JSON DOWNLOADER - MANAGER COMPLETO", Colors.WHITE)
    print_colored("=" * 60, Colors.CYAN)
    print_colored("Gestione completa: deployment, aggiornamento, avvio", Colors.YELLOW)
    print_colored("=" * 60, Colors.CYAN)

def check_python():
    """Verifica che Python 3 sia installato"""
    try:
        version = subprocess.check_output(['python3', '--version'], stderr=subprocess.STDOUT).decode().strip()
        print_colored(f"✓ {version} trovato", Colors.GREEN)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_colored("✗ Python 3 non trovato", Colors.RED)
        return False

def check_git():
    """Verifica che Git sia installato"""
    try:
        subprocess.check_output(['git', '--version'], stderr=subprocess.STDOUT)
        print_colored("✓ Git trovato", Colors.GREEN)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_colored("✗ Git non trovato", Colors.RED)
        return False

def check_tmux():
    """Verifica che tmux sia installato"""
    try:
        subprocess.check_output(['tmux', '-V'], stderr=subprocess.STDOUT)
        print_colored("✓ tmux trovato", Colors.GREEN)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_colored("⚠ tmux non trovato (opzionale)", Colors.YELLOW)
        return False

def install_dependencies():
    """Installa le dipendenze di sistema"""
    print_colored("\n📦 Installazione dipendenze di sistema...", Colors.BLUE)
    
    # Rileva la distribuzione Linux
    if os.path.exists('/etc/debian_version'):
        # Debian/Ubuntu
        packages = ['python3', 'python3-pip', 'python3-venv', 'git', 'tmux']
        # cmd sarà gestito separatamente per Debian/Ubuntu
    elif os.path.exists('/etc/redhat-release'):
        # Red Hat/CentOS/Fedora
        packages = ['python3', 'python3-pip', 'git', 'tmux']
        cmd = ['sudo', 'yum', 'install', '-y'] + packages
    elif os.path.exists('/etc/arch-release'):
        # Arch Linux
        packages = ['python', 'python-pip', 'git', 'tmux']
        cmd = ['sudo', 'pacman', '-S', '--noconfirm'] + packages
    else:
        print_colored("⚠ Distribuzione Linux non supportata automaticamente", Colors.YELLOW)
        print_colored("Installa manualmente: python3, pip, git, tmux", Colors.YELLOW)
        return False
    
    try:
        print_colored("Esecuzione comando di installazione...", Colors.BLUE)
        
        # Per Debian/Ubuntu, esegui prima apt update, poi apt install
        if os.path.exists('/etc/debian_version'):
            # Prima aggiorna
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            # Poi installa
            install_cmd = ['sudo', 'apt', 'install', '-y'] + packages
            subprocess.run(install_cmd, check=True)
        else:
            # Per altre distribuzioni, usa il comando normale
            subprocess.run(cmd, check=True)
            
        print_colored("✓ Dipendenze installate", Colors.GREEN)
        return True
    except subprocess.CalledProcessError:
        print_colored("✗ Errore nell'installazione delle dipendenze", Colors.RED)
        return False

def setup_virtual_environment():
    """Configura l'ambiente virtuale"""
    print_colored("\n🐍 Configurazione ambiente virtuale...", Colors.BLUE)
    
    if not os.path.exists('venv'):
        try:
            subprocess.run(['python3', '-m', 'venv', 'venv'], check=True)
            print_colored("✓ Ambiente virtuale creato", Colors.GREEN)
        except subprocess.CalledProcessError:
            print_colored("✗ Errore nella creazione dell'ambiente virtuale", Colors.RED)
            return False
    else:
        print_colored("✓ Ambiente virtuale già esistente", Colors.GREEN)
    
    # Attiva l'ambiente virtuale e installa le dipendenze
    try:
        pip_cmd = os.path.join('venv', 'bin', 'pip')
        subprocess.run([pip_cmd, 'install', '--upgrade', 'pip'], check=True)
        subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt'], check=True)
        print_colored("✓ Dipendenze Python installate", Colors.GREEN)
        return True
    except subprocess.CalledProcessError:
        print_colored("✗ Errore nell'installazione delle dipendenze Python", Colors.RED)
        return False

def setup_database_directory():
    """Configura la directory /database/JSON"""
    print_colored("\n📁 Configurazione directory /database/JSON...", Colors.BLUE)
    
    try:
        # Crea la directory principale
        if not os.path.exists('/database'):
            subprocess.run(['sudo', 'mkdir', '-p', '/database'], check=True)
            subprocess.run(['sudo', 'chown', f'{os.getenv("USER")}:{os.getenv("USER")}', '/database'], check=True)
            print_colored("✓ Directory /database creata", Colors.GREEN)
        
        # Crea la sottodirectory JSON
        if not os.path.exists('/database/JSON'):
            os.makedirs('/database/JSON', exist_ok=True)
            print_colored("✓ Directory /database/JSON creata", Colors.GREEN)
        
        # Crea le cartelle per lo smistamento
        folders = [
            'aggiudicatari_json', 'aggiudicazioni_json', 'avvio-contratto_json',
            'bandi-cig-modalita-realizzazio_json', 'bando_cig_json',
            'categorie-dpcm-aggregazione_json', 'categorie-opera_json',
            'centri-di-costo_json', 'collaudo_json', 'cup_json',
            'fine-contratto_json', 'fonti-finanziamento_json',
            'indicatori-pnrrpnc_json', 'lavorazioni_json',
            'misurepremiali-pnrrpnc_json', 'partecipanti_json',
            'pubblicazioni_json', 'quadro-economico_json',
            'smartcig_json', 'sospensioni_json',
            'stati-avanzamento_json', 'stazioni-appaltanti_json',
            'subappalti_json', 'varianti_json'
        ]
        
        for folder in folders:
            folder_path = os.path.join('/database/JSON', folder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
        
        print_colored(f"✓ {len(folders)} cartelle per lo smistamento create", Colors.GREEN)
        return True
        
    except Exception as e:
        print_colored(f"✗ Errore nella configurazione della directory: {e}", Colors.RED)
        return False

def setup_git():
    """Configura Git se necessario"""
    print_colored("\n🔧 Configurazione Git...", Colors.BLUE)
    
    if not os.path.exists('.git'):
        try:
            subprocess.run(['git', 'init'], check=True)
            print_colored("✓ Repository Git inizializzato", Colors.GREEN)
        except subprocess.CalledProcessError:
            print_colored("✗ Errore nell'inizializzazione di Git", Colors.RED)
            return False
    
    # Controlla se c'è un remote configurato
    try:
        subprocess.check_output(['git', 'remote', 'get-url', 'origin'], stderr=subprocess.STDOUT)
        print_colored("✓ Remote 'origin' configurato", Colors.GREEN)
    except subprocess.CalledProcessError:
        print_colored("⚠ Nessun remote 'origin' configurato", Colors.YELLOW)
        remote_url = input("Inserisci l'URL del repository Git (opzionale): ").strip()
        if remote_url:
            try:
                subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True)
                print_colored("✓ Remote 'origin' configurato", Colors.GREEN)
            except subprocess.CalledProcessError:
                print_colored("✗ Errore nella configurazione del remote", Colors.RED)
    
    return True

def test_installation():
    """Testa l'installazione"""
    print_colored("\n🧪 Test dell'installazione...", Colors.BLUE)
    
    try:
        # Test Python
        python_cmd = os.path.join('venv', 'bin', 'python')
        result = subprocess.run([python_cmd, '-c', 'import requests, json, os; print("OK")'], 
                              capture_output=True, text=True, check=True)
        print_colored("✓ Test Python superato", Colors.GREEN)
        
        # Test directory /database
        if os.path.exists('/database/JSON'):
            print_colored("✓ Directory /database/JSON accessibile", Colors.GREEN)
        else:
            print_colored("⚠ Directory /database/JSON non trovata", Colors.YELLOW)
        
        return True
    except subprocess.CalledProcessError:
        print_colored("✗ Test fallito", Colors.RED)
        return False

def deploy():
    """Esegue il deployment completo"""
    print_colored("\n🚀 AVVIO DEPLOYMENT COMPLETO", Colors.PURPLE)
    
    steps = [
        ("Verifica Python", check_python),
        ("Verifica Git", check_git),
        ("Verifica tmux", check_tmux),
        ("Installazione dipendenze", install_dependencies),
        ("Configurazione ambiente virtuale", setup_virtual_environment),
        ("Configurazione directory database", setup_database_directory),
        ("Configurazione Git", setup_git),
        ("Test installazione", test_installation)
    ]
    
    for step_name, step_func in steps:
        print_colored(f"\n📋 {step_name}...", Colors.BLUE)
        if not step_func():
            print_colored(f"✗ Deployment fallito durante: {step_name}", Colors.RED)
            return False
    
    print_colored("\n🎉 DEPLOYMENT COMPLETATO CON SUCCESSO!", Colors.GREEN)
    return True

def update_project():
    """Aggiorna il progetto dalle ultime commit"""
    print_colored("\n🔄 AGGIORNAMENTO PROGETTO", Colors.PURPLE)
    
    try:
        # Controlla lo stato attuale
        print_colored("📋 Controllo stato attuale...", Colors.BLUE)
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        
        if result.stdout.strip():
            print_colored("⚠ Modifiche non committate trovate:", Colors.YELLOW)
            print(result.stdout)
            
            choice = input("Vuoi salvare le modifiche? (s/n): ").strip().lower()
            if choice == 's':
                commit_msg = input("Messaggio di commit: ").strip()
                if not commit_msg:
                    commit_msg = "Auto-commit before update"
                
                subprocess.run(['git', 'add', '.'], check=True)
                subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
                print_colored("✓ Modifiche salvate", Colors.GREEN)
        
        # Aggiorna dal repository remoto
        print_colored("📥 Aggiornamento dal repository remoto...", Colors.BLUE)
        subprocess.run(['git', 'fetch', 'origin'], check=True)
        
        # Controlla se ci sono aggiornamenti
        result = subprocess.run(['git', 'log', 'HEAD..origin/main', '--oneline'], 
                              capture_output=True, text=True)
        
        if result.stdout.strip():
            print_colored("📋 Nuove modifiche disponibili:", Colors.BLUE)
            print(result.stdout)
            
            choice = input("Vuoi procedere con l'aggiornamento? (s/n): ").strip().lower()
            if choice == 's':
                subprocess.run(['git', 'pull', 'origin', 'main'], check=True)
                print_colored("✓ Codice aggiornato", Colors.GREEN)
                
                # Aggiorna le dipendenze
                print_colored("📦 Aggiornamento dipendenze...", Colors.BLUE)
                pip_cmd = os.path.join('venv', 'bin', 'pip')
                subprocess.run([pip_cmd, 'install', '-r', 'requirements.txt', '--upgrade'], check=True)
                print_colored("✓ Dipendenze aggiornate", Colors.GREEN)
            else:
                print_colored("Aggiornamento annullato", Colors.YELLOW)
        else:
            print_colored("✓ Progetto già aggiornato", Colors.GREEN)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print_colored(f"✗ Errore durante l'aggiornamento: {e}", Colors.RED)
        return False

def start_application():
    """Avvia l'applicazione"""
    print_colored("\n🚀 AVVIO APPLICAZIONE", Colors.PURPLE)
    
    if not os.path.exists('venv'):
        print_colored("✗ Ambiente virtuale non trovato. Esegui prima il deployment.", Colors.RED)
        return False
    
    if not os.path.exists('run_anacd2.py'):
        print_colored("✗ File run_anacd2.py non trovato.", Colors.RED)
        return False
    
    # Controlla se tmux è disponibile
    tmux_available = check_tmux()
    
    if tmux_available:
        # Controlla se c'è già una sessione attiva
        try:
            result = subprocess.run(['tmux', 'has-session', '-t', 'anac'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print_colored("⚠ Sessione tmux 'anac' già attiva", Colors.YELLOW)
                print("Opzioni:")
                print("1. Collegati alla sessione esistente")
                print("2. Termina la sessione esistente e creane una nuova")
                print("3. Avvia senza tmux")
                
                choice = input("Scegli (1/2/3): ").strip()
                
                if choice == '1':
                    subprocess.run(['tmux', 'attach', '-t', 'anac'])
                    return True
                elif choice == '2':
                    subprocess.run(['tmux', 'kill-session', '-t', 'anac'])
                elif choice == '3':
                    tmux_available = False
        except subprocess.CalledProcessError:
            pass
    
    # Chiedi se usare la modalità approfondita
    thorough = input("Vuoi usare la modalità di ricerca approfondita? (s/n): ").strip().lower() == 's'
    
    if tmux_available:
        # Avvia con tmux
        print_colored("🚀 Avvio con tmux...", Colors.BLUE)
        env = os.environ.copy()
        if thorough:
            env['ANAC_THOROUGH_SEARCH'] = '1'
        
        cmd = ['tmux', 'new-session', '-d', '-s', 'anac', '-c', os.getcwd(),
               'bash', '-c', 'source venv/bin/activate && python3 run_anacd2.py']
        
        subprocess.run(cmd, env=env, check=True)
        print_colored("✓ Applicazione avviata in sessione tmux 'anac'", Colors.GREEN)
        print_colored("\nComandi utili:", Colors.CYAN)
        print("  tmux attach -t anac     # Collegati alla sessione")
        print("  tmux list-sessions      # Lista sessioni attive")
        print("  tmux kill-session -t anac  # Termina la sessione")
        print("\nPremi INVIO per collegarti alla sessione...")
        input()
        subprocess.run(['tmux', 'attach', '-t', 'anac'])
    else:
        # Avvio diretto
        print_colored("🚀 Avvio diretto...", Colors.BLUE)
        env = os.environ.copy()
        if thorough:
            env['ANAC_THOROUGH_SEARCH'] = '1'
        
        python_cmd = os.path.join('venv', 'bin', 'python')
        subprocess.run([python_cmd, 'run_anacd2.py'], env=env, check=True)
    
    return True

def show_status():
    """Mostra lo stato del sistema"""
    print_colored("\n📊 STATO DEL SISTEMA", Colors.PURPLE)
    
    # Verifica componenti
    components = [
        ("Python 3", check_python),
        ("Git", check_git),
        ("tmux", check_tmux),
        ("Ambiente virtuale", lambda: os.path.exists('venv')),
        ("Directory /database/JSON", lambda: os.path.exists('/database/JSON')),
        ("File run_anacd2.py", lambda: os.path.exists('run_anacd2.py')),
        ("File config.json", lambda: os.path.exists('config.json'))
    ]
    
    for name, check_func in components:
        if check_func():
            print_colored(f"✓ {name}", Colors.GREEN)
        else:
            print_colored(f"✗ {name}", Colors.RED)
    
    # Verifica sessioni tmux
    try:
        result = subprocess.run(['tmux', 'list-sessions'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            print_colored("\n📋 Sessioni tmux attive:", Colors.BLUE)
            print(result.stdout)
        else:
            print_colored("\n📋 Nessuna sessione tmux attiva", Colors.YELLOW)
    except subprocess.CalledProcessError:
        pass
    
    # Verifica spazio disco
    try:
        result = subprocess.run(['df', '-h', '/database'], capture_output=True, text=True)
        if result.returncode == 0:
            print_colored("\n💾 Spazio disco /database:", Colors.BLUE)
            print(result.stdout)
    except subprocess.CalledProcessError:
        pass

def show_menu():
    """Mostra il menu principale"""
    print_header()
    print_colored("\nScegli un'operazione:", Colors.WHITE)
    print_colored("1. 🚀 Deployment completo", Colors.GREEN)
    print_colored("2. 🔄 Aggiorna progetto", Colors.BLUE)
    print_colored("3. ▶️  Avvia applicazione", Colors.YELLOW)
    print_colored("4. 📊 Mostra stato sistema", Colors.CYAN)
    print_colored("5. 🧪 Test installazione", Colors.PURPLE)
    print_colored("6. 📁 Configura solo directory /database", Colors.WHITE)
    print_colored("0. ❌ Esci", Colors.RED)
    
    choice = input("\nInserisci il numero dell'operazione: ").strip()
    return choice

def main():
    """Funzione principale"""
    try:
        while True:
            choice = show_menu()
            
            if choice == '0':
                print_colored("\n👋 Arrivederci!", Colors.CYAN)
                break
            elif choice == '1':
                deploy()
            elif choice == '2':
                update_project()
            elif choice == '3':
                start_application()
            elif choice == '4':
                show_status()
            elif choice == '5':
                test_installation()
            elif choice == '6':
                setup_database_directory()
            else:
                print_colored("❌ Scelta non valida", Colors.RED)
            
            input("\nPremi INVIO per continuare...")
            
    except KeyboardInterrupt:
        print_colored("\n\n👋 Operazione interrotta dall'utente", Colors.YELLOW)
    except Exception as e:
        print_colored(f"\n❌ Errore inatteso: {e}", Colors.RED)

if __name__ == "__main__":
    main()
