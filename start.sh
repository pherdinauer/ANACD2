#!/bin/bash

# ANAC JSON Downloader - Avvio Semplice
# Script per avviare l'applicazione

set -e

# Colori per output
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

echo "=========================================="
echo "  ANAC JSON DOWNLOADER - AVVIO"
echo "=========================================="

# Verifica se l'ambiente virtuale esiste
if [ ! -d "venv" ]; then
    print_warning "Ambiente virtuale non trovato!"
    print_status "Esegui prima: bash server_setup.sh"
    exit 1
fi

# Verifica se i file necessari esistono
if [ ! -f "run_anacd2.py" ]; then
    print_warning "File run_anacd2.py non trovato!"
    print_status "Assicurati di essere nella directory corretta"
    exit 1
fi

# Attiva l'ambiente virtuale
print_status "Attivo l'ambiente virtuale..."
source venv/bin/activate
print_success "Ambiente virtuale attivato"

# Verifica il mount point /database
if [ -d "/database/JSON" ]; then
    print_success "Directory /database/JSON disponibile - smistamento automatico abilitato"
else
    print_warning "Directory /database/JSON non trovata"
    print_status "Le nuove funzionalità di smistamento automatico richiedono /database/JSON"
fi

# Chiedi se usare la modalità approfondita
echo ""
read -p "Vuoi usare la modalità di ricerca approfondita? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    export ANAC_THOROUGH_SEARCH=1
    print_status "Modalità ricerca approfondita attivata"
fi

# Avvia l'applicazione
print_status "Avvio dell'applicazione..."
echo ""
echo "=========================================="
echo "  ANAC JSON DOWNLOADER"
echo "=========================================="
echo ""

python3 run_anacd2.py
