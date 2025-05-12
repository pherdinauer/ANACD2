# ANAC JSON Downloader

Utility per il download automatico di file JSON dal portale Open Data dell'Autorità Nazionale Anticorruzione (ANAC).

## Funzionalità

- Scraping automatico delle pagine del portale ANAC
- Individuazione e download di file JSON e ZIP contenenti JSON
- Estrazione automatica dei file JSON da archivi ZIP
- Sistema di deduplicazione avanzata dei link
- Gestione avanzata dei download con ripresa automatica
- Memorizzazione e apprendimento automatico di dataset e link
- Verifica dell'integrità dei file scaricati
- Interfaccia a riga di comando completa

## Requisiti di sistema

- Python 3.8 o superiore
- Connessione internet

## Installazione su Linux

### 1. Clonare il repository

```bash
git clone https://github.com/yourusername/anac-json-downloader.git
cd anac-json-downloader
```

### 2. Creare e attivare un ambiente virtuale

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Installare le dipendenze

```bash
pip install -r json_downloader/requirements.txt
```

### 4. Installare i browser richiesti da Playwright

```bash
playwright install chromium
```

## Esecuzione

L'applicazione può essere avviata con:

```bash
python -m json_downloader.cli
```

## Esecuzione con tmux

Per eseguire l'applicazione in background usando tmux (utile per esecuzioni su server remote):

### 1. Installa tmux se non è già presente

```bash
sudo apt-get install tmux   # Per Debian/Ubuntu
# o
sudo yum install tmux       # Per CentOS/RHEL
```

### 2. Crea una nuova sessione tmux

```bash
tmux new -s anac_downloader
```

### 3. Attiva l'ambiente virtuale ed esegui l'applicazione

```bash
cd anac-json-downloader
source venv/bin/activate
python -m json_downloader.cli
```

### 4. Staccare la sessione (lasciando l'applicazione in esecuzione)

Premi `Ctrl+B` seguito da `D` per staccare la sessione tmux.

### 5. Ricollegarsi a una sessione esistente

```bash
tmux attach -t anac_downloader
```

## Utilizzo dell'applicazione

Una volta avviata, l'applicazione mostra un menu interattivo con le seguenti opzioni:

1. **Esegui scraping delle pagine web** - Trova tutti i dataset e file JSON/ZIP disponibili
2. **Scarica i file JSON/ZIP trovati** - Scarica i file trovati durante lo scraping
3. **Verifica integrità file già scaricati** - Controlla l'integrità dei file scaricati
4. **Visualizza link in cache** - Mostra i link trovati e salvati nella cache
5. **Aggiungi link manualmente alla cache** - Aggiungi nuovi link alla cache
6. **Carica link da file esterno** - Importa link da un file di testo
7. **Deduplicazione avanzata dei link** - Rimuovi link duplicati dalla cache
8. **Gestisci dataset e link diretti noti** - Visualizza, aggiungi o rimuovi dataset e link noti
0. **Esci dal programma**

## Flusso di lavoro tipico

1. Eseguire lo scraping per trovare i dataset disponibili
2. Scaricare i file JSON/ZIP trovati
3. Verificare l'integrità dei file scaricati
4. Estrarre i file ZIP se necessario (l'applicazione può farlo automaticamente)

## Risoluzione dei problemi

### Errori di visualizzazione durante l'esecuzione in tmux

Se riscontri problemi di visualizzazione in tmux, prova a impostare la variabile d'ambiente TERM:

```bash
export TERM=xterm-256color
```

### Errori di Playwright in ambiente headless

Su server Linux senza interfaccia grafica, potrebbe essere necessario installare alcune dipendenze aggiuntive:

```bash
# Per Debian/Ubuntu
sudo apt-get install -y libx11-xcb1 libxcomposite1 libxcursor1 libxdamage1 \
    libxi6 libxtst6 libnss3 libcups2 libxss1 libxrandr2 \
    libasound2 libatk1.0-0 libatk-bridge2.0-0 libpangocairo-1.0-0 \
    libgtk-3-0 libgbm1
```

### Errore "No module named json_downloader"

Se ricevi questo errore durante l'esecuzione, prova a eseguire direttamente lo script principale:

```bash
cd anac-json-downloader
python json_downloader/cli.py
``` 