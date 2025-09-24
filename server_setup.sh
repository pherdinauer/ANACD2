#!/bin/bash

# ANAC JSON Downloader - Setup Server
# Script semplice per configurare e avviare l'applicazione sul server

set -e

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "=========================================="
echo "  ANAC JSON DOWNLOADER - SERVER SETUP"
echo "=========================================="

# Verifica se siamo root
if [ "$EUID" -eq 0 ]; then
    print_warning "Non eseguire questo script come root!"
    print_status "Crea un utente normale e esegui da lì"
    exit 1
fi

# Verifica se Python 3 è installato
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 non è installato!"
    print_status "Installazione Python 3..."
    
    if [ -f /etc/debian_version ]; then
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv git
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y python3 python3-pip git
    elif [ -f /etc/arch-release ]; then
        sudo pacman -S python python-pip git
    else
        print_error "Distribuzione Linux non supportata"
        exit 1
    fi
fi

print_success "Python 3 trovato"

# Verifica se Git è installato
if ! command -v git &> /dev/null; then
    print_error "Git non è installato!"
    exit 1
fi

print_success "Git trovato"

# Crea le directory necessarie
print_status "Creo le directory necessarie..."
mkdir -p log cache downloads
print_success "Directory create"

# Crea l'ambiente virtuale se non esiste
if [ ! -d "venv" ]; then
    print_status "Creo l'ambiente virtuale..."
    python3 -m venv venv
    print_success "Ambiente virtuale creato"
fi

# Attiva l'ambiente virtuale e installa le dipendenze
print_status "Installo le dipendenze..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
print_success "Dipendenze installate"

# Configura la directory /database/JSON
print_status "Configuro la directory /database/JSON..."
if [ ! -d "/database" ]; then
    sudo mkdir -p /database
    sudo chown $USER:$USER /database
fi

if [ ! -d "/database/JSON" ]; then
    mkdir -p /database/JSON
fi

# Crea le cartelle per lo smistamento
folders=(
    "aggiudicatari_json" "aggiudicazioni_json" "avvio-contratto_json"
    "bandi-cig-modalita-realizzazio_json" "bando_cig_json"
    "categorie-dpcm-aggregazione_json" "categorie-opera_json"
    "centri-di-costo_json" "collaudo_json" "cup_json"
    "fine-contratto_json" "fonti-finanziamento_json"
    "indicatori-pnrrpnc_json" "lavorazioni_json"
    "misurepremiali-pnrrpnc_json" "partecipanti_json"
    "pubblicazioni_json" "quadro-economico_json"
    "smartcig_json" "sospensioni_json"
    "stati-avanzamento_json" "stazioni-appaltanti_json"
    "subappalti_json" "varianti_json"
)

for folder in "${folders[@]}"; do
    if [ ! -d "/database/JSON/$folder" ]; then
        mkdir -p "/database/JSON/$folder"
    fi
done

print_success "Directory /database/JSON configurata"

# Crea il file di configurazione se non esiste
if [ ! -f "config.json" ]; then
    print_status "Creo il file di configurazione..."
    cat > config.json << EOF
{
  "base_url": "https://dati.anticorruzione.it/opendata/dataset",
  "download_dir": "downloads",
  "timeout": 90,
  "max_retries": 8,
  "retry_backoff": 2,
  "chunk_size": 1048576,
  "log_file": "log/downloader.log",
  "max_pages": 30,
  "max_page_retries": 5,
  "debug_mode": false,
  "save_report": true,
  "use_session_folders": true,
  "include_formats": ["json"],
  "exclude_formats": ["ttl", "csv", "xml"],
  "extract_json_only": true,
  "extract_zip_files": false
}
EOF
    print_success "File di configurazione creato"
fi

# Test dell'installazione
print_status "Testo l'installazione..."
if python3 -c "import requests, json, os; print('OK')" 2>/dev/null; then
    print_success "Installazione verificata"
else
    print_error "Errore nella verifica dell'installazione"
    exit 1
fi

echo ""
echo "=========================================="
print_success "SETUP COMPLETATO!"
echo "=========================================="
echo ""
echo "Per avviare l'applicazione:"
echo "  source venv/bin/activate"
echo "  python3 run_anacd2.py"
echo ""
echo "Oppure usa il manager completo:"
echo "  python3 anac_manager.py"
echo ""
echo "Le nuove funzionalità sono disponibili:"
echo "  ✓ Verifica file esistenti in /database/JSON"
echo "  ✓ Smistamento automatico nelle cartelle appropriate"
echo "  ✓ Evitare riscaricamenti di file già presenti"
echo ""
print_success "Tutto pronto per l'uso!"
