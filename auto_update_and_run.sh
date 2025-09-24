#!/bin/bash

# ANAC JSON Downloader - Auto Update & Run
# Script tutto-in-uno per pull automatico e avvio applicazione

set -e

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# Carica la configurazione
if [ -f "auto_run_config.sh" ]; then
    source auto_run_config.sh
else
    # Configurazione di fallback
    PROJECT_DIR="anac-downloader"
    REPO_URL="https://github.com/pherdinauer/ANACD2.git"
    VENV_DIR="venv"
    LOG_FILE="auto_update.log"
fi

# Funzione per log
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Funzione per pulire e uscire
cleanup() {
    print_warning "Interruzione rilevata. Pulizia..."
    if [ -n "$APP_PID" ]; then
        kill $APP_PID 2>/dev/null || true
    fi
    exit 0
}

# Trap per gestire interruzioni
trap cleanup SIGINT SIGTERM

echo "=========================================="
print_header "  ANAC JSON DOWNLOADER - AUTO UPDATE & RUN"
echo "=========================================="
print_header "  Script tutto-in-uno per pull automatico e avvio"
echo "=========================================="

log "Avvio script auto-update-and-run"

# Verifica se siamo nella directory corretta
if [ ! -f "run_anacd2.py" ] && [ ! -d "$PROJECT_DIR" ]; then
    print_error "Directory del progetto non trovata!"
    print_status "Assicurati di essere nella directory corretta o che il progetto sia clonato"
    exit 1
fi

# Se siamo già nella directory del progetto, usa la directory corrente
if [ -f "run_anacd2.py" ]; then
    PROJECT_DIR="."
    print_status "Trovato progetto nella directory corrente"
else
    print_status "Progetto trovato in: $PROJECT_DIR"
fi

# Entra nella directory del progetto
cd "$PROJECT_DIR"

print_step "1. Verifica Git e repository"

# Verifica se è un repository Git
if [ ! -d ".git" ]; then
    print_warning "Directory non è un repository Git"
    print_status "Clonazione repository..."
    
    # Torna alla directory parent
    cd ..
    
    # Rimuovi directory esistente se presente
    if [ -d "$PROJECT_DIR" ]; then
        print_warning "Rimozione directory esistente..."
        rm -rf "$PROJECT_DIR"
    fi
    
    # Clona il repository
    git clone "$REPO_URL" "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    print_success "Repository clonato"
else
    print_success "Repository Git trovato"
fi

print_step "2. Pull delle ultime commit"

# Verifica connessione internet
if ! ping -c 1 github.com >/dev/null 2>&1; then
    print_warning "Connessione internet non disponibile, uso versione locale"
else
    print_status "Connessione internet OK, aggiorno repository..."
    
    # Fetch e pull
    git fetch origin
    CURRENT_BRANCH=$(git branch --show-current)
    
    # Controlla se ci sono aggiornamenti
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/$CURRENT_BRANCH)
    
    if [ "$LOCAL" = "$REMOTE" ]; then
        print_success "Repository già aggiornato"
    else
        print_status "Aggiornamenti disponibili, eseguo pull..."
        git pull origin "$CURRENT_BRANCH"
        print_success "Repository aggiornato alle ultime commit"
    fi
fi

print_step "3. Verifica ambiente virtuale"

# Verifica se l'ambiente virtuale esiste
if [ ! -d "$VENV_DIR" ]; then
    print_warning "Ambiente virtuale non trovato, creazione..."
    python3 -m venv "$VENV_DIR"
    print_success "Ambiente virtuale creato"
else
    print_success "Ambiente virtuale trovato"
fi

# Attiva ambiente virtuale
print_status "Attivazione ambiente virtuale..."
source "$VENV_DIR/bin/activate"

print_step "4. Installazione/aggiornamento dipendenze"

# Aggiorna pip
print_status "Aggiornamento pip..."
pip install --upgrade pip >/dev/null 2>&1

# Installa/aggiorna dipendenze
if [ -f "requirements.txt" ]; then
    print_status "Installazione dipendenze..."
    pip install -r requirements.txt >/dev/null 2>&1
    print_success "Dipendenze installate/aggiornate"
else
    print_warning "File requirements.txt non trovato"
fi

print_step "5. Verifica configurazione"

# Verifica file di configurazione
if [ ! -f "config.json" ]; then
    if [ -f "config.example.json" ]; then
        print_status "Creazione config.json da esempio..."
        cp config.example.json config.json
        print_success "Configurazione creata"
    else
        print_warning "File di configurazione non trovato"
    fi
fi

# Verifica directory /database/JSON
if [ ! -d "/database/JSON" ]; then
    print_warning "Directory /database/JSON non trovata"
    print_status "Creazione directory..."
    sudo mkdir -p /database/JSON
    sudo chown $USER:$USER /database/JSON
    print_success "Directory /database/JSON creata"
fi

print_step "6. Avvio applicazione"

print_success "Tutto pronto! Avvio applicazione..."
echo ""
print_header "=========================================="
print_success "  APPLICAZIONE AVVIATA"
print_header "=========================================="
echo ""

# Avvia l'applicazione in background e cattura il PID
python3 run_anacd2.py &
APP_PID=$!

# Salva il PID per cleanup
echo $APP_PID > app.pid

print_status "Applicazione avviata con PID: $APP_PID"
print_status "Per fermare l'applicazione: Ctrl+C"
print_status "Log salvato in: $LOG_FILE"
echo ""

# Attendi che l'applicazione finisca
wait $APP_PID

# Cleanup automatico
cleanup
