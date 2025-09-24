#!/bin/bash

# ANAC JSON Downloader - Minimal Setup
# Scarica solo i file essenziali e configura tutto

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
echo "  ANAC JSON DOWNLOADER - MINIMAL SETUP"
echo "=========================================="
print_status "Scarico i file essenziali e configuro tutto automaticamente"

# Verifica curl o wget
if command -v curl &> /dev/null; then
    DOWNLOAD_CMD="curl -s"
elif command -v wget &> /dev/null; then
    DOWNLOAD_CMD="wget -qO-"
else
    print_warning "curl/wget non trovato, installo curl..."
    if [ -f /etc/debian_version ]; then
        sudo apt update && sudo apt install -y curl
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y curl
    elif [ -f /etc/arch-release ]; then
        sudo pacman -S curl
    fi
    DOWNLOAD_CMD="curl -s"
fi

# Crea directory di lavoro
mkdir -p anac-downloader
cd anac-downloader

# URL base del repository (modifica questo con il tuo repository)
REPO_BASE="https://raw.githubusercontent.com/your-username/anac-downloader/main"

print_status "Scarico file essenziali..."

# Lista dei file essenziali da scaricare
FILES=(
    "requirements.txt"
    "run_anacd2.py"
    "config.json"
    "cli.py"
    "json_downloader/downloader.py"
    "json_downloader/utils.py"
    "json_downloader/scraper.py"
    "json_downloader/__init__.py"
)

# Crea le directory necessarie
mkdir -p json_downloader log cache downloads

# Scarica i file
for file in "${FILES[@]}"; do
    print_status "Scarico $file..."
    $DOWNLOAD_CMD "$REPO_BASE/$file" > "$file"
done

# Crea file __init__.py per json_downloader se non esiste
if [ ! -f "json_downloader/__init__.py" ]; then
    touch json_downloader/__init__.py
fi

print_success "File scaricati"

# Verifica Python 3
if ! command -v python3 &> /dev/null; then
    print_warning "Python 3 non trovato, installo..."
    if [ -f /etc/debian_version ]; then
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y python3 python3-pip
    elif [ -f /etc/arch-release ]; then
        sudo pacman -S python python-pip
    fi
fi

print_success "Python 3 trovato"

# Crea ambiente virtuale
print_status "Creo ambiente virtuale..."
python3 -m venv venv
source venv/bin/activate

# Installa dipendenze
print_status "Installo dipendenze..."
pip install --upgrade pip
pip install -r requirements.txt

print_success "Dipendenze installate"

# Configura directory /database/JSON
print_status "Configuro directory /database/JSON..."
if [ ! -d "/database" ]; then
    sudo mkdir -p /database
    sudo chown $USER:$USER /database
fi

if [ ! -d "/database/JSON" ]; then
    mkdir -p /database/JSON
fi

# Crea cartelle per smistamento
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
    mkdir -p "/database/JSON/$folder"
done

print_success "Directory /database/JSON configurata"

# Crea script di avvio
print_status "Creo script di avvio..."
cat > start.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 run_anacd2.py
EOF

chmod +x start.sh

print_success "Script di avvio creato"

# Test installazione
print_status "Testo installazione..."
if python3 -c "import requests, json, os; print('OK')" 2>/dev/null; then
    print_success "Installazione verificata"
else
    print_warning "Errore nella verifica dell'installazione"
fi

echo ""
echo "=========================================="
print_success "SETUP COMPLETATO!"
echo "=========================================="
echo ""
print_status "Il progetto è stato scaricato e configurato in: $(pwd)"
echo ""
print_status "Per avviare l'applicazione:"
echo "  ./start.sh"
echo ""
print_status "Le nuove funzionalità sono disponibili:"
echo "  ✓ Verifica file esistenti in /database/JSON"
echo "  ✓ Smistamento automatico nelle cartelle appropriate"
echo "  ✓ Evitare riscaricamenti di file già presenti"
echo ""

read -p "Vuoi avviare l'applicazione ora? (s/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Ss]$ ]]; then
    print_status "Avvio applicazione..."
    ./start.sh
fi

print_success "Tutto pronto!"
