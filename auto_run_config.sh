#!/bin/bash

# ANAC JSON Downloader - Auto Run Configuration
# File di configurazione per gli script auto-run

# ==========================================
# CONFIGURAZIONE REPOSITORY
# ==========================================

# URL del repository Git (MODIFICA QUESTO!)
REPO_URL="https://github.com/pherdinauer/ANACD2.git"

# Nome della directory del progetto
PROJECT_DIR="anac-downloader"

# Nome della sessione tmux
TMUX_SESSION_NAME="anac-downloader"

# ==========================================
# CONFIGURAZIONE AMBIENTE
# ==========================================

# Directory dell'ambiente virtuale
VENV_DIR="venv"

# File di log
LOG_FILE="auto_update.log"

# ==========================================
# CONFIGURAZIONE SISTEMA
# ==========================================

# Directory database
DATABASE_DIR="/database/JSON"

# File di configurazione
CONFIG_FILE="config.json"
CONFIG_EXAMPLE="config.example.json"

# ==========================================
# CONFIGURAZIONE DIPENDENZE
# ==========================================

# Pacchetti di sistema richiesti
SYSTEM_PACKAGES_DEBIAN="python3 python3-pip python3-venv git tmux"
SYSTEM_PACKAGES_REDHAT="python3 python3-pip git tmux"
SYSTEM_PACKAGES_ARCH="python python-pip git tmux"

# ==========================================
# CONFIGURAZIONE OUTPUT
# ==========================================

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# ==========================================
# FUNZIONI DI UTILITÀ
# ==========================================

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

# Funzione per log
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Funzione per verificare connessione internet
check_internet() {
    if ping -c 1 github.com >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Funzione per rilevare distribuzione Linux
detect_linux_distro() {
    if [ -f /etc/debian_version ]; then
        echo "debian"
    elif [ -f /etc/redhat-release ]; then
        echo "redhat"
    elif [ -f /etc/arch-release ]; then
        echo "arch"
    else
        echo "unknown"
    fi
}

# Funzione per installare dipendenze di sistema
install_system_dependencies() {
    local distro=$(detect_linux_distro)
    
    case $distro in
        "debian")
            print_status "Installazione dipendenze per Debian/Ubuntu..."
            sudo apt update
            sudo apt install -y $SYSTEM_PACKAGES_DEBIAN
            ;;
        "redhat")
            print_status "Installazione dipendenze per Red Hat/CentOS/Fedora..."
            sudo yum install -y $SYSTEM_PACKAGES_REDHAT
            ;;
        "arch")
            print_status "Installazione dipendenze per Arch Linux..."
            sudo pacman -S --noconfirm $SYSTEM_PACKAGES_ARCH
            ;;
        *)
            print_warning "Distribuzione Linux non supportata automaticamente"
            print_warning "Installa manualmente: python3, pip, git, tmux"
            return 1
            ;;
    esac
    
    return 0
}

# Funzione per verificare se un comando esiste
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Funzione per verificare se una directory esiste
directory_exists() {
    [ -d "$1" ]
}

# Funzione per verificare se un file esiste
file_exists() {
    [ -f "$1" ]
}

# Funzione per creare directory se non esiste
create_directory_if_not_exists() {
    if ! directory_exists "$1"; then
        print_status "Creazione directory: $1"
        mkdir -p "$1"
        return 0
    fi
    return 1
}

# Funzione per creare directory con sudo se non esiste
create_directory_with_sudo_if_not_exists() {
    if ! directory_exists "$1"; then
        print_status "Creazione directory con sudo: $1"
        sudo mkdir -p "$1"
        sudo chown $USER:$USER "$1"
        return 0
    fi
    return 1
}

# Funzione per pulire e uscire
cleanup() {
    print_warning "Interruzione rilevata. Pulizia..."
    if [ -n "$APP_PID" ]; then
        kill $APP_PID 2>/dev/null || true
    fi
    exit 0
}

# Funzione per verificare se siamo in un repository Git
is_git_repo() {
    [ -d ".git" ]
}

# Funzione per ottenere il branch corrente
get_current_branch() {
    git branch --show-current 2>/dev/null || echo "main"
}

# Funzione per verificare se ci sono aggiornamenti disponibili
has_updates() {
    local current_branch=$(get_current_branch)
    local local_commit=$(git rev-parse HEAD 2>/dev/null)
    local remote_commit=$(git rev-parse origin/$current_branch 2>/dev/null)
    
    if [ "$local_commit" != "$remote_commit" ]; then
        return 0  # Ci sono aggiornamenti
    else
        return 1  # Non ci sono aggiornamenti
    fi
}

# Funzione per eseguire pull
git_pull() {
    local current_branch=$(get_current_branch)
    print_status "Esecuzione pull dal branch: $current_branch"
    git pull origin "$current_branch"
}

# Funzione per eseguire fetch
git_fetch() {
    print_status "Esecuzione fetch..."
    git fetch origin
}

# Funzione per clonare repository
git_clone() {
    print_status "Clonazione repository: $REPO_URL"
    git clone "$REPO_URL" "$PROJECT_DIR"
}

# Funzione per rimuovere directory
remove_directory() {
    if directory_exists "$1"; then
        print_warning "Rimozione directory: $1"
        rm -rf "$1"
    fi
}

# Funzione per attivare ambiente virtuale
activate_venv() {
    if directory_exists "$VENV_DIR"; then
        print_status "Attivazione ambiente virtuale..."
        source "$VENV_DIR/bin/activate"
        return 0
    else
        print_warning "Ambiente virtuale non trovato: $VENV_DIR"
        return 1
    fi
}

# Funzione per creare ambiente virtuale
create_venv() {
    if ! directory_exists "$VENV_DIR"; then
        print_status "Creazione ambiente virtuale..."
        python3 -m venv "$VENV_DIR"
        return 0
    else
        print_success "Ambiente virtuale già esistente"
        return 1
    fi
}

# Funzione per installare dipendenze Python
install_python_dependencies() {
    if file_exists "requirements.txt"; then
        print_status "Installazione dipendenze Python..."
        pip install --upgrade pip >/dev/null 2>&1
        pip install -r requirements.txt >/dev/null 2>&1
        return 0
    else
        print_warning "File requirements.txt non trovato"
        return 1
    fi
}

# Funzione per verificare configurazione
check_config() {
    if ! file_exists "$CONFIG_FILE"; then
        if file_exists "$CONFIG_EXAMPLE"; then
            print_status "Creazione configurazione da esempio..."
            cp "$CONFIG_EXAMPLE" "$CONFIG_FILE"
            return 0
        else
            print_warning "File di configurazione non trovato"
            return 1
        fi
    else
        print_success "Configurazione trovata"
        return 0
    fi
}

# Funzione per verificare directory database
check_database_directory() {
    if ! directory_exists "$DATABASE_DIR"; then
        print_warning "Directory database non trovata: $DATABASE_DIR"
        create_directory_with_sudo_if_not_exists "$DATABASE_DIR"
        return 0
    else
        print_success "Directory database trovata"
        return 0
    fi
}

# Funzione per avviare applicazione
start_application() {
    if file_exists "run_anacd2.py"; then
        print_success "Avvio applicazione..."
        python3 run_anacd2.py &
        APP_PID=$!
        echo $APP_PID > app.pid
        print_status "Applicazione avviata con PID: $APP_PID"
        return 0
    else
        print_error "File run_anacd2.py non trovato"
        return 1
    fi
}

# Funzione per verificare se tmux è disponibile
check_tmux() {
    if command_exists tmux; then
        print_success "tmux trovato"
        return 0
    else
        print_warning "tmux non trovato"
        return 1
    fi
}

# Funzione per creare sessione tmux
create_tmux_session() {
    if ! tmux has-session -t "$TMUX_SESSION_NAME" 2>/dev/null; then
        print_status "Creazione sessione tmux: $TMUX_SESSION_NAME"
        tmux new-session -d -s "$TMUX_SESSION_NAME"
        return 0
    else
        print_warning "Sessione tmux già esistente: $TMUX_SESSION_NAME"
        return 1
    fi
}

# Funzione per attaccare a sessione tmux
attach_tmux_session() {
    print_status "Attacco a sessione tmux: $TMUX_SESSION_NAME"
    tmux attach-session -t "$TMUX_SESSION_NAME"
}

# Funzione per inviare comando a sessione tmux
send_tmux_command() {
    local command="$1"
    tmux send-keys -t "$TMUX_SESSION_NAME" "$command" Enter
}

# Funzione per verificare se Python è disponibile
check_python() {
    if command_exists python3; then
        print_success "Python 3 trovato"
        return 0
    else
        print_error "Python 3 non trovato"
        return 1
    fi
}

# Funzione per verificare se Git è disponibile
check_git() {
    if command_exists git; then
        print_success "Git trovato"
        return 0
    else
        print_error "Git non trovato"
        return 1
    fi
}

# Funzione per verificare se pip è disponibile
check_pip() {
    if command_exists pip; then
        print_success "pip trovato"
        return 0
    else
        print_warning "pip non trovato"
        return 1
    fi
}

# Funzione per verificare se venv è disponibile
check_venv() {
    if python3 -m venv --help >/dev/null 2>&1; then
        print_success "venv disponibile"
        return 0
    else
        print_warning "venv non disponibile"
        return 1
    fi
}

# Funzione per verificare se tutte le dipendenze sono disponibili
check_all_dependencies() {
    local all_ok=true
    
    if ! check_python; then
        all_ok=false
    fi
    
    if ! check_git; then
        all_ok=false
    fi
    
    if ! check_pip; then
        all_ok=false
    fi
    
    if ! check_venv; then
        all_ok=false
    fi
    
    if ! check_tmux; then
        all_ok=false
    fi
    
    if $all_ok; then
        print_success "Tutte le dipendenze sono disponibili"
        return 0
    else
        print_warning "Alcune dipendenze mancano"
        return 1
    fi
}

# Funzione per eseguire test completo
run_full_test() {
    print_header "Esecuzione test completo..."
    
    if check_all_dependencies; then
        print_success "Test dipendenze: PASSED"
    else
        print_error "Test dipendenze: FAILED"
        return 1
    fi
    
    if check_config; then
        print_success "Test configurazione: PASSED"
    else
        print_error "Test configurazione: FAILED"
        return 1
    fi
    
    if check_database_directory; then
        print_success "Test directory database: PASSED"
    else
        print_error "Test directory database: FAILED"
        return 1
    fi
    
    print_success "Tutti i test sono passati!"
    return 0
}

# Funzione per mostrare stato del sistema
show_system_status() {
    print_header "Stato del sistema:"
    
    echo "Repository URL: $REPO_URL"
    echo "Directory progetto: $PROJECT_DIR"
    echo "Sessione tmux: $TMUX_SESSION_NAME"
    echo "Ambiente virtuale: $VENV_DIR"
    echo "Directory database: $DATABASE_DIR"
    echo "File di log: $LOG_FILE"
    echo ""
    
    print_header "Dipendenze:"
    check_python
    check_git
    check_pip
    check_venv
    check_tmux
    echo ""
    
    print_header "Directory e file:"
    if directory_exists "$PROJECT_DIR"; then
        print_success "Directory progetto: TROVATA"
    else
        print_warning "Directory progetto: NON TROVATA"
    fi
    
    if directory_exists "$VENV_DIR"; then
        print_success "Ambiente virtuale: TROVATO"
    else
        print_warning "Ambiente virtuale: NON TROVATO"
    fi
    
    if directory_exists "$DATABASE_DIR"; then
        print_success "Directory database: TROVATA"
    else
        print_warning "Directory database: NON TROVATA"
    fi
    
    if file_exists "$CONFIG_FILE"; then
        print_success "File configurazione: TROVATO"
    else
        print_warning "File configurazione: NON TROVATO"
    fi
    
    if file_exists "requirements.txt"; then
        print_success "File requirements: TROVATO"
    else
        print_warning "File requirements: NON TROVATO"
    fi
    
    if file_exists "run_anacd2.py"; then
        print_success "File applicazione: TROVATO"
    else
        print_warning "File applicazione: NON TROVATO"
    fi
}

# Funzione per mostrare help
show_help() {
    echo "ANAC JSON Downloader - Auto Run Configuration"
    echo ""
    echo "Questo file contiene tutte le configurazioni e funzioni di utilità"
    echo "per gli script auto-run del progetto ANAC JSON Downloader."
    echo ""
    echo "Configurazioni principali:"
    echo "  REPO_URL: URL del repository Git"
    echo "  PROJECT_DIR: Nome della directory del progetto"
    echo "  TMUX_SESSION_NAME: Nome della sessione tmux"
    echo "  VENV_DIR: Directory dell'ambiente virtuale"
    echo "  DATABASE_DIR: Directory del database"
    echo ""
    echo "Funzioni disponibili:"
    echo "  check_python, check_git, check_pip, check_venv, check_tmux"
    echo "  check_config, check_database_directory"
    echo "  create_venv, activate_venv, install_python_dependencies"
    echo "  git_clone, git_fetch, git_pull, has_updates"
    echo "  create_tmux_session, attach_tmux_session"
    echo "  start_application, run_full_test, show_system_status"
    echo ""
    echo "Per usare questo file in altri script:"
    echo "  source auto_run_config.sh"
    echo ""
}

# Se il file viene eseguito direttamente, mostra help
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    show_help
    exit 0
fi
