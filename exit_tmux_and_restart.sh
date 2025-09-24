#!/bin/bash

# Script per uscire da tmux e riavviare l'applicazione correttamente

set -e

# Colori
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}  EXIT TMUX AND RESTART${NC}"
echo -e "${BLUE}==========================================${NC}"

# Verifica se siamo in una sessione tmux
if [ -n "$TMUX" ]; then
    echo -e "${YELLOW}[INFO]${NC} Sei in una sessione tmux"
    echo -e "${YELLOW}[INFO]${NC} Uscita dalla sessione tmux..."
    
    # Esci dalla sessione tmux
    tmux detach-client
    
    echo -e "${GREEN}[SUCCESS]${NC} Uscito dalla sessione tmux"
    echo -e "${YELLOW}[INFO]${NC} Ora puoi riavviare l'applicazione correttamente"
else
    echo -e "${YELLOW}[INFO]${NC} Non sei in una sessione tmux"
fi

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${GREEN}  OPZIONI PER RIAVVIARE${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""
echo -e "${YELLOW}[INFO]${NC} Opzioni per riavviare l'applicazione:"
echo ""
echo "1. Con Playwright (richiede fix):"
echo "   ./fix_playwright.sh"
echo "   python3 run_interactive.py"
echo ""
echo "2. Senza Playwright (consigliato):"
echo "   python3 run_without_playwright.py"
echo ""
echo "3. Solo pull delle ultime commit:"
echo "   ./pull_updates.sh"
echo ""
echo "4. Auto-sorting diretto:"
echo "   python3 run_with_auto_sorting.py"
echo ""
echo -e "${GREEN}[SUCCESS]${NC} Scegli l'opzione che preferisci!"
