# ANAC JSON Downloader - Versione Semplificata

Utility per il download di file JSON dal portale Open Data dell'Autorità Nazionale Anticorruzione (ANAC).

## Funzionalità

- Download di file JSON e ZIP contenenti dati ANAC
- Estrazione automatica dei file JSON da archivi ZIP
- Memorizzazione automatica dei link noti
- Verifica dell'integrità dei file scaricati
- Interfaccia a riga di comando completa
- Modalità di ricerca approfondita per identificare tutti i dataset
- Download diretto da URL di dataset specifici

## Requisiti di sistema

- Python 3.7 o superiore
- (Opzionale) tmux per esecuzione in background su Linux
- (Opzionale) Playwright per la modalità di ricerca approfondita

## Installazione su Linux

### Metodo automatico (consigliato)

1. Rendere eseguibile lo script di deployment:
   ```bash
   chmod +x deploy_anac.sh
   ```

2. Eseguire lo script di deployment:
   ```bash
   ./deploy_anac.sh
   ```

3. Avviare l'applicazione:
   ```bash
   ./start_anac.sh
   ```

   Per una ricerca approfondita di tutti i dataset disponibili:
   ```bash
   ./start_anac.sh --thorough
   ```

### Metodo manuale

1. Creare cartelle necessarie:
   ```bash
   mkdir -p log cache downloads
   ```

2. Creare e attivare un ambiente virtuale:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Installare le dipendenze base:
   ```bash
   pip install requests python-dotenv beautifulsoup4 backoff
   ```

   Per la modalità di ricerca approfondita:
   ```bash
   pip install playwright
   python -m playwright install chromium
   ```

4. Avviare l'applicazione:
   ```bash
   python3 run_anacd2.py
   ```

   Per la modalità di ricerca approfondita:
   ```bash
   ANAC_THOROUGH_SEARCH=1 python3 run_anacd2.py
   ```

## Modalità di funzionamento

L'applicazione supporta due modalità di funzionamento:

1. **Modalità semplificata (predefinita)**: Utilizza solo un elenco predefinito di link e quelli già in cache, senza eseguire scraping web. Veloce ma potrebbe non includere tutti i dataset.

2. **Modalità approfondita**: Esegue uno scraping completo del portale ANAC per trovare tutti i dataset disponibili. Garantisce una copertura completa ma richiede più tempo.

La modalità approfondita può essere attivata in due modi:
- Passando il flag `--thorough` o `-t` allo script start_anac.sh
- Impostando la variabile d'ambiente `ANAC_THOROUGH_SEARCH=1`

## Uso con tmux

Per eseguire l'applicazione in background usando tmux:

1. Avviare con lo script incluso:
   ```bash
   ./start_anac.sh
   ```

2. Per ricollegarsi a una sessione esistente:
   ```bash
   tmux attach -t anac
   ```

3. Per staccarsi (lasciando l'app in esecuzione):
   Premi `Ctrl+B` seguito da `D`

## Utilizzo dell'applicazione

L'applicazione mostra un menu interattivo con le seguenti opzioni:

1. **Scarica i file JSON/ZIP trovati** - Scarica i file presenti nella cache o nella lista predefinita
2. **Verifica integrità file già scaricati** - Controlla l'integrità dei file scaricati
3. **Visualizza link in cache** - Mostra i link salvati nella cache
4. **Aggiungi link manualmente alla cache** - Aggiungi nuovi link alla cache
5. **Carica link da file esterno** - Importa link da un file di testo
6. **Deduplicazione avanzata dei link** - Rimuovi link duplicati dalla cache
7. **Gestisci dataset e link diretti noti** - Gestisci l'elenco dei dataset e link conosciuti
8. **Scarica file JSON/ZIP da un URL dataset specifico** - Inserisci un URL di dataset ANAC e scarica i file JSON/ZIP in una cartella dedicata
0. **Esci dal programma**

In modalità approfondita, sarà disponibile anche l'opzione:
* **Esegui scraping delle pagine web** - Trova tutti i dataset ANAC disponibili

### Download da URL dataset specifico

La funzionalità di download da URL dataset specifico permette di:
1. Inserire l'URL di un dataset ANAC specifico
2. Creare automaticamente una cartella dedicata per i file di quel dataset
3. Trovare e scaricare tutti i file JSON/ZIP associati
4. Estrarre automaticamente i file ZIP per accedere ai dati JSON

È utile quando si conosce già l'URL del dataset di interesse e si vuole scaricare rapidamente solo i file relativi a quel dataset specifico.

## Risoluzione dei problemi

### L'applicazione non parte

Verifica che Python sia installato e che l'ambiente virtuale sia attivato:
```bash
python3 --version
source venv/bin/activate
```

### Errore "No module named..."

Assicurati di aver installato tutte le dipendenze:
```bash
pip install requests python-dotenv beautifulsoup4 backoff
```

### Per la modalità di ricerca approfondita

Se hai problemi con Playwright:
```bash
pip install playwright
python -m playwright install chromium
```

### Problemi con tmux

Se tmux non funziona, puoi semplicemente eseguire l'applicazione direttamente:
```bash
source venv/bin/activate
python3 run_anacd2.py
``` 