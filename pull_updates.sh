#!/bin/bash

# ANAC JSON Downloader - Pull Updates Only
# Script per fare solo il pull delle ultime commit senza avviare l'applicazione

set -e

# Colori
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  ANAC JSON DOWNLOADER - PULL UPDATES${NC}"
echo -e "${BLUE}==========================================${NC}"

# Carica la configurazione
if [ -f "auto_run_config.sh" ]; then
    source auto_run_config.sh
else
    # Configurazione di fallback
    PROJECT_DIR="anac-downloader"
    REPO_URL="https://github.com/pherdinauer/ANACD2.git"
fi

echo -e "${YELLOW}[INFO]${NC} Avvio pull delle ultime commit..."

# Verifica se siamo nella directory del progetto
if [ -f "run_anacd2.py" ]; then
    echo -e "${GREEN}[SUCCESS]${NC} Progetto trovato nella directory corrente"
    PROJECT_DIR="."
else
    echo -e "${YELLOW}[INFO]${NC} Progetto non trovato, clonazione..."
    
    # Rimuovi directory esistente se presente
    if [ -d "$PROJECT_DIR" ]; then
        echo -e "${YELLOW}[INFO]${NC} Rimozione directory esistente..."
        rm -rf "$PROJECT_DIR"
    fi
    
    # Clona repository
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    echo -e "${GREEN}[SUCCESS]${NC} Repository clonato"
fi

# Entra nella directory del progetto
cd "$PROJECT_DIR"

# Pull delle ultime commit
echo -e "${YELLOW}[INFO]${NC} Aggiornamento repository..."
git fetch origin
CURRENT_BRANCH=$(git branch --show-current)
git pull origin "$CURRENT_BRANCH"
echo -e "${GREEN}[SUCCESS]${NC} Repository aggiornato alle ultime commit"

# Verifica ambiente virtuale
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[INFO]${NC} Creazione ambiente virtuale..."
    python3 -m venv venv
fi

# Attiva ambiente virtuale
echo -e "${YELLOW}[INFO]${NC} Attivazione ambiente virtuale..."
source venv/bin/activate

# Installa dipendenze
echo -e "${YELLOW}[INFO]${NC} Installazione dipendenze..."
pip install --upgrade pip >/dev/null 2>&1
pip install -r requirements.txt >/dev/null 2>&1

# Verifica configurazione
if [ ! -f "config.json" ] && [ -f "config.example.json" ]; then
    cp config.example.json config.json
fi

# Verifica directory /database/JSON
if [ ! -d "/database/JSON" ]; then
    echo -e "${YELLOW}[INFO]${NC} Creazione directory /database/JSON..."
    sudo mkdir -p /database/JSON
    sudo chown $USER:$USER /database/JSON
fi

echo -e "${GREEN}[SUCCESS]${NC} Aggiornamento completato!"
echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${GREEN}  AGGIORNAMENTO COMPLETATO${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""
echo -e "${YELLOW}[INFO]${NC} Per avviare l'applicazione:"
echo "  python3 run_anacd2.py"
echo ""
echo -e "${YELLOW}[INFO]${NC} Oppure usa:"
echo "  ./start.sh"
echo ""
echo -e "${GREEN}[SUCCESS]${NC} Tutto pronto per l'uso!"
