#!/bin/bash

# Esempio di deployment completo per ANAC JSON Downloader
# Questo script mostra come configurare tutto il sistema da zero

set -e

echo "=========================================="
echo "  ANAC JSON DOWNLOADER - DEPLOYMENT EXAMPLE"
echo "=========================================="

# 1. Clona o aggiorna il repository
echo "1. Configurazione repository Git..."
if [ ! -d ".git" ]; then
    echo "Inizializzo repository Git..."
    git init
    # Aggiungi il remote se necessario
    # git remote add origin https://github.com/your-repo/anac-downloader.git
fi

# 2. Esegui il deployment
echo "2. Esecuzione deployment..."
chmod +x deploy_anac.sh
./deploy_anac.sh

# 3. Configura il mount point /database
echo "3. Configurazione mount point /database..."
if [ ! -d "/database" ]; then
    echo "Creo directory /database..."
    sudo mkdir -p /database
    sudo chown $USER:$USER /database
fi

if [ ! -d "/database/JSON" ]; then
    echo "Creo directory /database/JSON..."
    mkdir -p /database/JSON
fi

# 4. Crea le cartelle per il smistamento automatico
echo "4. Creazione cartelle per smistamento automatico..."
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
        echo "Creo cartella: $folder"
        mkdir -p "/database/JSON/$folder"
    fi
done

# 5. Test della configurazione
echo "5. Test della configurazione..."
source venv/bin/activate

# Test Python
python3 -c "
import sys
print(f'Python version: {sys.version}')

try:
    import requests
    print('✓ requests OK')
except ImportError:
    print('✗ requests missing')

try:
    import json
    print('✓ json OK')
except ImportError:
    print('✗ json missing')

try:
    import os
    print('✓ os OK')
except ImportError:
    print('✗ os missing')
"

# Test directory /database
if [ -d "/database/JSON" ]; then
    echo "✓ Directory /database/JSON disponibile"
    folder_count=$(find /database/JSON -maxdepth 1 -type d | wc -l)
    echo "✓ Trovate $folder_count cartelle per lo smistamento"
else
    echo "✗ Directory /database/JSON non trovata"
fi

# 6. Avvio dell'applicazione
echo "6. Avvio dell'applicazione..."
echo ""
echo "Il deployment è completato!"
echo ""
echo "Per avviare l'applicazione:"
echo "  ./start_anac.sh"
echo ""
echo "Per avviare con ricerca approfondita:"
echo "  ./start_anac.sh --thorough"
echo ""
echo "Per aggiornare il progetto:"
echo "  ./update_anac.sh"
echo ""

read -p "Vuoi avviare l'applicazione ora? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    ./start_anac.sh
fi
