# ANAC JSON Downloader - Versione Semplificata

Utility per il download di file JSON dal portale Open Data dell'Autorità Nazionale Anticorruzione (ANAC).

## Funzionalità

- Download di file JSON e ZIP contenenti dati ANAC
- Estrazione automatica dei file JSON da archivi ZIP
- Memorizzazione automatica dei link noti
- Verifica dell'integrità dei file scaricati
- Interfaccia a riga di comando completa

## Requisiti di sistema

- Python 3.7 o superiore
- (Opzionale) tmux per esecuzione in background su Linux

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

4. Avviare l'applicazione:
   ```bash
   python3 run_anacd2.py
   ```

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
0. **Esci dal programma**

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

### Problemi con tmux

Se tmux non funziona, puoi semplicemente eseguire l'applicazione direttamente:
```bash
source venv/bin/activate
python3 run_anacd2.py
``` 