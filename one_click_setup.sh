#!/bin/bash

# ANAC JSON Downloader - One Click Setup
# Questo script scarica tutto e configura automaticamente

set -e

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

echo "=========================================="
print_header "  ANAC JSON DOWNLOADER - ONE CLICK SETUP"
echo "=========================================="
print_header "  Questo script scarica tutto e configura automaticamente"
echo "=========================================="

# Verifica se Git è installato
if ! command -v git &> /dev/null; then
    print_error "Git non è installato!"
    print_status "Installazione Git..."
    
    if [ -f /etc/debian_version ]; then
        sudo apt update
        sudo apt install -y git
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y git
    elif [ -f /etc/arch-release ]; then
        sudo pacman -S git
    else
        print_error "Distribuzione Linux non supportata"
        exit 1
    fi
fi

print_success "Git trovato"

# Chiedi l'URL del repository
echo ""
print_status "Configurazione repository..."
echo "Opzioni:"
echo "1. Repository GitHub pubblico"
echo "2. Repository privato (inserisci URL)"
echo "3. Usa repository di default"

read -p "Scegli (1/2/3): " -n 1 -r
echo

case $REPLY in
    1)
        REPO_URL="https://github.com/your-username/anac-downloader.git"
        print_warning "Inserisci l'URL del tuo repository GitHub pubblico"
        read -p "URL repository: " REPO_URL
        ;;
    2)
        read -p "URL repository privato: " REPO_URL
        ;;
    3)
        REPO_URL="https://github.com/your-username/anac-downloader.git"
        print_warning "Usando repository di default - modifica lo script se necessario"
        ;;
    *)
        print_error "Opzione non valida"
        exit 1
        ;;
esac

# Directory di destinazione
DEST_DIR="anac-downloader"

# Rimuovi directory esistente se presente
if [ -d "$DEST_DIR" ]; then
    print_warning "Directory $DEST_DIR già esistente"
    read -p "Vuoi sovrascriverla? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        rm -rf "$DEST_DIR"
        print_status "Directory rimossa"
    else
        print_status "Uso directory esistente"
    fi
fi

# Clona il repository
if [ ! -d "$DEST_DIR" ]; then
    print_status "Clonazione repository..."
    git clone "$REPO_URL" "$DEST_DIR"
    print_success "Repository clonato"
fi

# Entra nella directory
cd "$DEST_DIR"

# Verifica che il file di setup esista
if [ ! -f "server_setup.sh" ]; then
    print_error "File server_setup.sh non trovato nel repository!"
    print_status "Assicurati che il repository contenga tutti i file necessari"
    exit 1
fi

# Esegui il setup
print_status "Esecuzione setup automatico..."
chmod +x server_setup.sh
./server_setup.sh

# Chiedi se avviare l'applicazione
echo ""
print_success "Setup completato!"
echo ""
read -p "Vuoi avviare l'applicazione ora? (s/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Ss]$ ]]; then
    print_status "Avvio applicazione..."
    chmod +x start.sh
    ./start.sh
else
    echo ""
    print_success "Setup completato!"
    echo ""
    print_status "Per avviare l'applicazione in futuro:"
    echo "  cd $DEST_DIR"
    echo "  ./start.sh"
    echo ""
    print_status "Oppure usa il manager completo:"
    echo "  cd $DEST_DIR"
    echo "  python3 anac_manager.py"
fi

echo ""
print_header "=========================================="
print_success "  TUTTO COMPLETATO!"
print_header "=========================================="
echo ""
print_status "Il progetto è stato scaricato e configurato in: $(pwd)"
print_status "Le nuove funzionalità sono disponibili:"
echo "  ✓ Verifica file esistenti in /database/JSON"
echo "  ✓ Smistamento automatico nelle cartelle appropriate"
echo "  ✓ Evitare riscaricamenti di file già presenti"
echo ""
print_success "Pronto per l'uso!"
