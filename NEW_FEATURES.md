# Nuove Funzionalità - ANAC JSON Downloader

Questo documento descrive le nuove funzionalità implementate nel progetto ANAC JSON Downloader.

## 🆕 Funzionalità Aggiunte

### 1. Verifica File Esistenti

**Descrizione**: Il sistema ora verifica automaticamente se i file sono già presenti in `/database/JSON/` prima di scaricarli.

**Vantaggi**:
- Evita riscaricamenti inutili
- Risparmia tempo e banda
- Previene duplicati

**Come funziona**:
- Scansiona tutte le cartelle in `/database/JSON/`
- Crea un mapping dei file esistenti
- Confronta i nomi dei file prima del download
- Salta automaticamente i file già presenti

### 2. Smistamento Automatico

**Descrizione**: I file scaricati vengono automaticamente organizzati nelle cartelle appropriate basandosi sui nomi delle cartelle esistenti.

**Vantaggi**:
- Organizzazione automatica dei file
- Classificazione intelligente
- Struttura dati ordinata

**Come funziona**:
- Analizza il nome del file scaricato
- Confronta con i nomi delle cartelle disponibili
- Usa mapping intelligente per la classificazione
- Sposta il file nella cartella appropriata

### 3. Script di Deployment e Gestione

**Descrizione**: Script automatizzati per il deployment e la gestione del progetto su Linux.

**Script disponibili**:
- `deploy_anac.sh`: Deployment completo
- `start_anac.sh`: Avvio dell'applicazione
- `update_anac.sh`: Aggiornamento del progetto

## 🔧 Configurazione

### Prerequisiti

1. **Mount Point /database**: Deve essere disponibile e scrivibile
2. **Cartelle di destinazione**: Devono essere create in anticipo
3. **Permessi**: L'utente deve avere accesso in scrittura

### Setup Iniziale

```bash
# 1. Clona il repository
git clone <repository-url>
cd anac-downloader

# 2. Esegui il deployment
./deploy_anac.sh

# 3. Configura il mount point
sudo mkdir -p /database/JSON
sudo chown $USER:$USER /database/JSON

# 4. Crea le cartelle per lo smistamento
mkdir -p /database/JSON/{smartcig_json,aggiudicatari_json,categorie-opera_json,...}

# 5. Avvia l'applicazione
./start_anac.sh
```

## 📁 Struttura Cartelle Supportate

Il sistema riconosce automaticamente queste cartelle:

| Cartella | Descrizione |
|----------|-------------|
| `smartcig_json/` | File relativi a SmartCIG |
| `aggiudicatari_json/` | File sugli aggiudicatari |
| `aggiudicazioni_json/` | File sulle aggiudicazioni |
| `categorie-opera_json/` | Categorie di opere |
| `stati-avanzamento_json/` | Stati di avanzamento |
| `subappalti_json/` | File sui subappalti |
| `varianti_json/` | File sulle varianti |
| E molte altre... | |

## 🚀 Utilizzo

### Download con Smistamento Automatico

1. Avvia l'applicazione: `./start_anac.sh`
2. Scegli l'opzione: "Download con smistamento automatico in /database/JSON"
3. Configura le opzioni:
   - Estrazione automatica ZIP
   - Filtro solo file JSON
   - Numero di file da scaricare
4. Conferma e procedi

### Aggiornamento del Progetto

```bash
# Aggiorna dalle ultime commit
./update_anac.sh
```

### Gestione Sessioni tmux

```bash
# Avvia con tmux
./start_anac.sh

# Collegati a una sessione esistente
tmux attach -t anac

# Lista sessioni attive
tmux list-sessions

# Termina una sessione
tmux kill-session -t anac
```

## 🔍 Mapping Intelligente

Il sistema usa diversi algoritmi per determinare la cartella di destinazione:

### 1. Mapping Esplicito
```python
folder_mappings = {
    'smartcig': 'smartcig_json',
    'aggiudicatari': 'aggiudicatari_json',
    'categorie-opera': 'categorie-opera_json',
    # ...
}
```

### 2. Corrispondenze Parziali
- Confronta parti del nome del file con i nomi delle cartelle
- Rimuove il suffisso `_json` per il confronto
- Cerca corrispondenze nei nomi delle cartelle

### 3. Fallback
- Se non trova corrispondenze, usa una cartella generica
- Crea automaticamente la cartella se necessario

## 📊 Monitoraggio e Logging

### Log Dettagliati
- Scansione delle cartelle esistenti
- Verifica file duplicati
- Smistamento dei file
- Errori e avvisi

### Riepilogo Operazioni
- File scaricati con successo
- File saltati (già esistenti)
- File con errori
- Organizzazione per cartella

## 🐛 Risoluzione Problemi

### Errore "Directory /database/JSON non trovata"
```bash
# Crea la directory
sudo mkdir -p /database/JSON
sudo chown $USER:$USER /database/JSON
```

### Errore "Permission Denied"
```bash
# Imposta i permessi corretti
sudo chown -R $USER:$USER /database
chmod -R 755 /database
```

### File non smistati correttamente
- Verifica che le cartelle di destinazione esistano
- Controlla i nomi dei file per pattern riconosciuti
- Usa la cartella generica come fallback

## 🔮 Funzionalità Future

### Pianificate
- [ ] API REST per controllo remoto
- [ ] Interfaccia web per monitoraggio
- [ ] Notifiche per completamento download
- [ ] Backup automatico dei file
- [ ] Compressione automatica dei file vecchi

### In Sviluppo
- [ ] Supporto per più formati di file
- [ ] Integrazione con database relazionali
- [ ] Dashboard di monitoraggio in tempo reale

## 📝 Note di Sviluppo

### Architettura
- **Modularità**: Funzionalità separate in moduli
- **Configurabilità**: Tutto configurabile via file config
- **Estensibilità**: Facile aggiunta di nuove funzionalità

### Performance
- **Scansione efficiente**: Usa os.walk() per scansione ricorsiva
- **Caching**: Memorizza i risultati delle scansioni
- **Lazy loading**: Carica solo quando necessario

### Sicurezza
- **Validazione input**: Tutti gli input vengono validati
- **Gestione errori**: Gestione robusta degli errori
- **Permessi**: Controllo dei permessi di accesso
