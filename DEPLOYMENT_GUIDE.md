# Guida al Deployment - ANAC JSON Downloader

Questa guida fornisce istruzioni complete per il deployment del progetto ANAC JSON Downloader su Linux.

## 🚀 Deployment Rapido

### 1. Clona il Repository

```bash
git clone <repository-url>
cd anac-downloader
```

### 2. Esegui il Deployment Automatico

```bash
chmod +x deploy_anac.sh
./deploy_anac.sh
```

### 3. Configura il Mount Point /database

```bash
sudo mkdir -p /database/JSON
sudo chown $USER:$USER /database/JSON
```

### 4. Avvia l'Applicazione

```bash
./start_anac.sh
```

## 📋 Deployment Dettagliato

### Prerequisiti

- **Sistema Operativo**: Linux (Ubuntu, Debian, CentOS, Fedora, Arch)
- **Python**: 3.7 o superiore
- **Git**: Per il controllo versione
- **tmux**: (Opzionale) Per esecuzione in background
- **Spazio disco**: Almeno 10GB per i download

### Installazione Dipendenze di Sistema

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git tmux
```

#### CentOS/RHEL/Fedora
```bash
sudo yum install -y python3 python3-pip git tmux
# oppure per Fedora
sudo dnf install -y python3 python3-pip git tmux
```

#### Arch Linux
```bash
sudo pacman -S python python-pip git tmux
```

### Configurazione del Progetto

#### 1. Clona il Repository
```bash
git clone <repository-url>
cd anac-downloader
```

#### 2. Esegui il Deployment
```bash
chmod +x deploy_anac.sh
./deploy_anac.sh
```

Lo script di deployment:
- Verifica Python 3 e pip
- Crea l'ambiente virtuale
- Installa le dipendenze Python
- Configura il progetto
- Crea gli script di avvio

#### 3. Configura il Mount Point /database

**Opzione A: Directory Standard**
```bash
sudo mkdir -p /database/JSON
sudo chown $USER:$USER /database/JSON
```

**Opzione B: Mount Point Fisico**
```bash
# Crea la directory
sudo mkdir -p /database

# Monta la partizione (sostituisci /dev/sdb1)
sudo mount /dev/sdb1 /database

# Per montare automaticamente all'avvio
echo "/dev/sdb1 /database ext4 defaults 0 2" | sudo tee -a /etc/fstab
```

**Opzione C: Link Simbolico**
```bash
# Crea la directory di destinazione
mkdir -p /home/$USER/anac_database

# Crea il link simbolico
sudo ln -s /home/$USER/anac_database /database
```

#### 4. Crea le Cartelle per lo Smistamento

```bash
# Crea tutte le cartelle necessarie
mkdir -p /database/JSON/{aggiudicatari_json,aggiudicazioni_json,avvio-contratto_json,bandi-cig-modalita-realizzazio_json,bando_cig_json,categorie-dpcm-aggregazione_json,categorie-opera_json,centri-di-costo_json,collaudo_json,cup_json,fine-contratto_json,fonti-finanziamento_json,indicatori-pnrrpnc_json,lavorazioni_json,misurepremiali-pnrrpnc_json,partecipanti_json,pubblicazioni_json,quadro-economico_json,smartcig_json,sospensioni_json,stati-avanzamento_json,stazioni-appaltanti_json,subappalti_json,varianti_json}
```

## 🔧 Configurazione Avanzata

### Configurazione systemd (Opzionale)

Per l'avvio automatico del servizio:

```bash
# Copia il file di servizio
sudo cp anac-downloader.service /etc/systemd/system/

# Modifica il file per il tuo utente
sudo sed -i 's/User=anac/User='$USER'/g' /etc/systemd/system/anac-downloader.service
sudo sed -i 's/Group=anac/Group='$USER'/g' /etc/systemd/system/anac-downloader.service
sudo sed -i 's|/opt/anac-downloader|'$(pwd)'|g' /etc/systemd/system/anac-downloader.service

# Ricarica systemd
sudo systemctl daemon-reload

# Abilita il servizio
sudo systemctl enable anac-downloader

# Avvia il servizio
sudo systemctl start anac-downloader
```

### Configurazione Docker (Opzionale)

```bash
# Build dell'immagine
docker build -t anac-downloader .

# Avvio con docker-compose
docker-compose up -d

# Avvio interattivo
docker-compose run --rm anac-downloader
```

### Configurazione Proxy

Se sei dietro un proxy:

```bash
# Imposta le variabili d'ambiente
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=https://proxy.example.com:8080

# Oppure modifica il file config.json
{
  "proxy": "http://proxy.example.com:8080"
}
```

## 🚀 Avvio dell'Applicazione

### Metodo 1: Script di Avvio (Consigliato)

```bash
# Avvio standard
./start_anac.sh

# Avvio con ricerca approfondita
./start_anac.sh --thorough
```

### Metodo 2: Avvio Manuale

```bash
# Attiva l'ambiente virtuale
source venv/bin/activate

# Avvia l'applicazione
python3 run_anacd2.py
```

### Metodo 3: Con tmux

```bash
# Avvia con tmux
./start_anac.sh

# Collegati alla sessione
tmux attach -t anac

# Staccati dalla sessione (lasciandola attiva)
# Premi Ctrl+B, poi D
```

## 📊 Monitoraggio

### Log dell'Applicazione

```bash
# Visualizza i log
tail -f log/downloader.log

# Visualizza i log di systemd
sudo journalctl -u anac-downloader -f
```

### Stato del Servizio

```bash
# Controlla lo stato
sudo systemctl status anac-downloader

# Riavvia il servizio
sudo systemctl restart anac-downloader

# Ferma il servizio
sudo systemctl stop anac-downloader
```

### Spazio Disco

```bash
# Controlla lo spazio utilizzato
df -h /database

# Controlla la dimensione delle cartelle
du -sh /database/JSON/*
```

## 🔄 Aggiornamento

### Aggiornamento Automatico

```bash
./update_anac.sh
```

### Aggiornamento Manuale

```bash
# Aggiorna il codice
git pull origin main

# Aggiorna le dipendenze
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Riavvia il servizio
sudo systemctl restart anac-downloader
```

## 🐛 Risoluzione Problemi

### Problemi Comuni

#### 1. "Permission Denied" su /database
```bash
sudo chown -R $USER:$USER /database
chmod -R 755 /database
```

#### 2. "Python not found"
```bash
# Installa Python 3
sudo apt install python3 python3-pip  # Ubuntu/Debian
sudo yum install python3 python3-pip  # CentOS/RHEL
```

#### 3. "tmux not found"
```bash
# Installa tmux
sudo apt install tmux  # Ubuntu/Debian
sudo yum install tmux  # CentOS/RHEL
```

#### 4. "Playwright installation failed"
```bash
# Installa le dipendenze di sistema
sudo apt install libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgtk-3-0 libgbm1 libasound2  # Ubuntu/Debian
```

### Debug

#### Abilita Debug Mode

Modifica `config.json`:
```json
{
  "debug_mode": true
}
```

#### Verifica Configurazione

```bash
# Test della configurazione
python3 -c "
import os
print('Python OK')
print('Database path:', os.path.exists('/database/JSON'))
print('Virtual env:', os.path.exists('venv'))
"
```

## 📞 Supporto

### Log per Debug

Invia questi file per il supporto:
- `log/downloader.log`
- `config.json`
- Output di `./deploy_anac.sh`
- Output di `systemctl status anac-downloader`

### Informazioni di Sistema

```bash
# Raccogli informazioni di sistema
echo "OS: $(cat /etc/os-release | head -1)"
echo "Python: $(python3 --version)"
echo "Disk space: $(df -h /database)"
echo "Memory: $(free -h)"
```

## ✅ Checklist Post-Deployment

- [ ] Ambiente virtuale creato e attivato
- [ ] Dipendenze Python installate
- [ ] Directory /database/JSON creata e accessibile
- [ ] Cartelle per lo smistamento create
- [ ] Script di avvio funzionanti
- [ ] Applicazione avviata correttamente
- [ ] Log generati senza errori
- [ ] Test di download completato
- [ ] Smistamento automatico funzionante

## 🎯 Prossimi Passi

1. **Testa l'applicazione**: Esegui un download di test
2. **Configura il backup**: Imposta backup automatici per /database
3. **Monitora le performance**: Controlla l'utilizzo di risorse
4. **Aggiorna regolarmente**: Usa `./update_anac.sh` per aggiornamenti
5. **Documenta le modifiche**: Tieni traccia delle personalizzazioni
