# Configurazione Mount Point /database

Questo documento spiega come configurare il mount point `/database` per utilizzare le nuove funzionalità di smistamento automatico.

## Opzioni di Configurazione

### 1. Mount Point Fisico

Se hai un disco o partizione dedicata:

```bash
# Crea la directory di mount
sudo mkdir -p /database

# Monta la partizione (sostituisci /dev/sdb1 con la tua partizione)
sudo mount /dev/sdb1 /database

# Per montare automaticamente all'avvio, aggiungi a /etc/fstab:
echo "/dev/sdb1 /database ext4 defaults 0 2" | sudo tee -a /etc/fstab
```

### 2. Directory Simbolica

Se vuoi usare una directory esistente:

```bash
# Crea la directory di destinazione
mkdir -p /home/username/anac_database

# Crea il link simbolico
sudo ln -s /home/username/anac_database /database

# Verifica
ls -la /database
```

### 3. Directory Standard

Se preferisci usare una directory standard:

```bash
# Crea la directory
sudo mkdir -p /database

# Imposta i permessi
sudo chown $USER:$USER /database

# Crea la sottocartella JSON
mkdir -p /database/JSON
```

### 4. Docker Volume (se usi Docker)

```bash
# Crea un volume Docker
docker volume create anac-database

# Monta il volume
docker run -v anac-database:/database your-anac-container
```

## Verifica della Configurazione

Dopo aver configurato il mount point, verifica che funzioni:

```bash
# Verifica che la directory esista
ls -la /database

# Verifica i permessi di scrittura
touch /database/test_file && rm /database/test_file

# Crea la struttura necessaria
mkdir -p /database/JSON
```

## Struttura Cartelle Consigliata

Crea le seguenti cartelle in `/database/JSON/` per il smistamento automatico:

```bash
# Crea tutte le cartelle per il smistamento
mkdir -p /database/JSON/{aggiudicatari_json,aggiudicazioni_json,avvio-contratto_json,bandi-cig-modalita-realizzazio_json,bando_cig_json,categorie-dpcm-aggregazione_json,categorie-opera_json,centri-di-costo_json,collaudo_json,cup_json,fine-contratto_json,fonti-finanziamento_json,indicatori-pnrrpnc_json,lavorazioni_json,misurepremiali-pnrrpnc_json,partecipanti_json,pubblicazioni_json,quadro-economico_json,smartcig_json,sospensioni_json,stati-avanzamento_json,stazioni-appaltanti_json,subappalti_json,varianti_json}
```

## Test della Configurazione

Esegui questo comando per testare la configurazione:

```bash
# Test rapido
python3 -c "
import os
if os.path.exists('/database/JSON'):
    print('✓ Directory /database/JSON disponibile')
    folders = [f for f in os.listdir('/database/JSON') if os.path.isdir(os.path.join('/database/JSON', f))]
    print(f'✓ Trovate {len(folders)} cartelle per lo smistamento')
else:
    print('✗ Directory /database/JSON non trovata')
"
```

## Risoluzione Problemi

### Errore "Permission Denied"

```bash
# Imposta i permessi corretti
sudo chown -R $USER:$USER /database
chmod -R 755 /database
```

### Directory Non Montata

```bash
# Verifica i mount point attivi
mount | grep database

# Se non montato, rimonta
sudo mount -a
```

### Spazio Insufficiente

```bash
# Verifica lo spazio disponibile
df -h /database

# Pulisci file temporanei se necessario
find /database -name "*.tmp" -delete
```

## Automazione

Per automatizzare la creazione delle cartelle, puoi aggiungere questo al tuo script di avvio:

```bash
#!/bin/bash
# Crea le cartelle necessarie se non esistono
if [ ! -d "/database/JSON" ]; then
    sudo mkdir -p /database/JSON
    sudo chown $USER:$USER /database/JSON
fi

# Crea le sottocartelle per il smistamento
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
        mkdir -p "/database/JSON/$folder"
    fi
done
```
