#!/bin/bash

# Fix Playwright - Installa i browser necessari

set -e

# Colori
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  FIX PLAYWRIGHT - INSTALLAZIONE BROWSER${NC}"
echo -e "${BLUE}==========================================${NC}"

# Verifica se l'ambiente virtuale esiste
if [ ! -d "venv" ]; then
    echo -e "${RED}[ERROR]${NC} Ambiente virtuale non trovato!"
    echo -e "${YELLOW}[INFO]${NC} Creazione ambiente virtuale..."
    python3 -m venv venv
fi

# Attiva ambiente virtuale
echo -e "${YELLOW}[INFO]${NC} Attivazione ambiente virtuale..."
source venv/bin/activate

# Verifica se Playwright è installato
echo -e "${YELLOW}[INFO]${NC} Verifica installazione Playwright..."
if ! python3 -c "import playwright" 2>/dev/null; then
    echo -e "${YELLOW}[INFO]${NC} Installazione Playwright..."
    pip install playwright
fi

# Installa i browser di Playwright
echo -e "${YELLOW}[INFO]${NC} Installazione browser Playwright..."
echo -e "${YELLOW}[INFO]${NC} Questo potrebbe richiedere alcuni minuti..."

# Installa i browser
playwright install

# Installa anche le dipendenze di sistema per Playwright
echo -e "${YELLOW}[INFO]${NC} Installazione dipendenze di sistema..."
playwright install-deps

echo -e "${GREEN}[SUCCESS]${NC} Playwright configurato correttamente!"
echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${GREEN}  PLAYWRIGHT CONFIGURATO${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""
echo -e "${YELLOW}[INFO]${NC} Ora puoi usare l'applicazione con Playwright"
echo -e "${YELLOW}[INFO]${NC} Per avviare l'app:"
echo "  python3 run_interactive.py"
echo ""
echo -e "${GREEN}[SUCCESS]${NC} Tutto pronto!"
