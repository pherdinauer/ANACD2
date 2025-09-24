#!/bin/bash

# ANAC JSON Downloader - TMUX Auto Run
# Script per avviare tutto in una sessione tmux

set -e

# Colori
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}==========================================${NC}"
echo -e "${PURPLE}  ANAC JSON DOWNLOADER - TMUX AUTO RUN${NC}"
echo -e "${PURPLE}==========================================${NC}"

# Carica la configurazione
if [ -f "auto_run_config.sh" ]; then
    source auto_run_config.sh
    SESSION_NAME="$TMUX_SESSION_NAME"
else
    # Configurazione di fallback
    SESSION_NAME="anac-downloader"
    PROJECT_DIR="anac-downloader"
    REPO_URL="https://github.com/pherdinauer/ANACD2.git"
fi

echo -e "${YELLOW}[INFO]${NC} Avvio script tmux auto-run..."

# Verifica tmux
if ! command -v tmux &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} tmux non trovato!"
    echo -e "${YELLOW}[INFO]${NC} Installazione tmux..."
    if [ -f /etc/debian_version ]; then
        sudo apt update && sudo apt install -y tmux
    elif [ -f /etc/redhat-release ]; then
        sudo yum install -y tmux
    elif [ -f /etc/arch-release ]; then
        sudo pacman -S tmux
    fi
fi

# Verifica se la sessione esiste già
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo -e "${YELLOW}[WARNING]${NC} Sessione tmux '$SESSION_NAME' già esistente"
    echo -e "${YELLOW}[INFO]${NC} Attacco alla sessione esistente..."
    tmux attach-session -t "$SESSION_NAME"
    exit 0
fi

# Crea nuova sessione tmux
echo -e "${YELLOW}[INFO]${NC} Creazione sessione tmux '$SESSION_NAME'..."
tmux new-session -d -s "$SESSION_NAME"

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
    echo -e "${GREEN}[SUCCESS]${NC} Repository clonato"
fi

# Entra nella directory del progetto
cd "$PROJECT_DIR"

# Pull delle ultime commit
echo -e "${YELLOW}[INFO]${NC} Aggiornamento repository..."
git fetch origin
CURRENT_BRANCH=$(git branch --show-current)
git pull origin "$CURRENT_BRANCH"
echo -e "${GREEN}[SUCCESS]${NC} Repository aggiornato"

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

# Crea script di avvio per tmux
cat > start_app.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "=========================================="
echo "  ANAC JSON DOWNLOADER - AVVIATO"
echo "=========================================="
python3 run_anacd2.py
EOF

chmod +x start_app.sh

# Avvia applicazione in tmux
echo -e "${GREEN}[SUCCESS]${NC} Tutto pronto! Avvio applicazione in tmux..."
tmux send-keys -t "$SESSION_NAME" "./start_app.sh" Enter

echo -e "${BLUE}==========================================${NC}"
echo -e "${GREEN}  APPLICAZIONE AVVIATA IN TMUX${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""
echo -e "${YELLOW}[INFO]${NC} Sessione tmux: $SESSION_NAME"
echo -e "${YELLOW}[INFO]${NC} Per attaccare alla sessione: tmux attach -t $SESSION_NAME"
echo -e "${YELLOW}[INFO]${NC} Per staccare dalla sessione: Ctrl+B, poi D"
echo -e "${YELLOW}[INFO]${NC} Per fermare la sessione: tmux kill-session -t $SESSION_NAME"
echo ""

# Attacca alla sessione
tmux attach-session -t "$SESSION_NAME"
