# 🔧 Fix Istruzioni - ANAC JSON Downloader

## 🚨 Problema Identificato

L'errore che stai vedendo è causato da:

1. **Import Error**: Il modulo `scraper` non viene trovato
2. **Config Error**: Il file di configurazione non viene caricato correttamente

## ✅ Soluzioni Implementate

Ho creato diversi file per risolvere il problema:

### 1. **File di Fix Automatico**
- `fix_config.py` - Risolve i problemi di configurazione
- `test_imports.py` - Testa tutti gli import

### 2. **File Corretti**
- `json_downloader/__init__.py` - Crea il modulo come package
- `cli.py` - Import corretti dal modulo json_downloader
- `run_anacd2.py` - Gestione errori migliorata

## 🚀 Come Risolvere

### Opzione 1: Fix Automatico (Consigliato)

```bash
# Sul server Linux
cd /database/ANACD2

# Esegui il fix automatico
python3 fix_config.py

# Testa gli import
python3 test_imports.py

# Avvia l'applicazione
python3 run_anacd2.py
```

### Opzione 2: Fix Manuale

```bash
# Sul server Linux
cd /database/ANACD2

# Verifica che il file config.json esista
ls -la config.json

# Se non esiste, copia da config.example.json
cp config.example.json config.json

# Crea le directory necessarie
mkdir -p log cache downloads

# Crea la directory /database/JSON se non esiste
sudo mkdir -p /database/JSON
sudo chown $USER:$USER /database/JSON

# Avvia l'applicazione
python3 run_anacd2.py
```

### Opzione 3: Usa gli Script Auto-Run

```bash
# Gli script auto-run gestiscono automaticamente i problemi
./simple_auto_run.sh
```

## 🔍 Cosa Fa il Fix

### `fix_config.py`:
- ✅ Verifica e crea `config.json` se mancante
- ✅ Crea le directory necessarie (`log`, `cache`, `downloads`)
- ✅ Crea la directory `/database/JSON` con permessi corretti
- ✅ Testa il caricamento della configurazione

### `test_imports.py`:
- ✅ Testa tutti gli import del modulo `json_downloader`
- ✅ Verifica il caricamento della configurazione
- ✅ Testa la creazione della CLI

## 📊 Verifica del Fix

Dopo aver eseguito il fix, dovresti vedere:

```bash
$ python3 test_imports.py
==================================================
  TEST IMPORT ANAC JSON DOWNLOADER
==================================================
Test import...
1. Test import json_downloader...
   ✓ json_downloader importato
2. Test import classi principali...
   ✓ ANACDownloaderCLI importato
   ✓ scraper importato
   ✓ downloader importato
   ✓ utils importato
3. Test caricamento configurazione...
   ✓ Configurazione caricata
   - Download dir: downloads
   - Log file: log/downloader.log
4. Test creazione CLI...
   ✓ CLI creata

🎉 Tutti i test sono passati!

✅ Tutto funziona correttamente!
```

## 🎯 Risultato Atteso

Dopo il fix, l'applicazione dovrebbe avviarsi correttamente e mostrare:

```
============================================================
     ANAC JSON DOWNLOADER - UTILITY DI DOWNLOAD
============================================================
Questa applicazione scarica file JSON/ZIP dal portale Open Data ANAC

============================================================
     ANAC JSON DOWNLOADER - MENU PRINCIPALE
============================================================

Scegli un'operazione:
1. 🔍 Ricerca approfondita (Playwright)
2. 📥 Download da URL specifico
3. 📋 Mostra link noti
4. 🧹 Pulisci cache
5. 📊 Mostra statistiche
6. ⚙️ Configurazione
7. 🚀 Download con smistamento automatico in /database/JSON
0. ❌ Esci

Inserisci il numero dell'operazione:
```

## 🆘 Se il Fix Non Funziona

### Problema: "Permission Denied"
```bash
sudo chown -R $USER:$USER /database/ANACD2
```

### Problema: "Python not found"
```bash
sudo apt install python3 python3-pip python3-venv
```

### Problema: "Module not found"
```bash
# Reinstalla le dipendenze
pip install -r requirements.txt
```

### Problema: "Config file not found"
```bash
# Crea manualmente il file di configurazione
cp config.example.json config.json
```

## 🎉 Risultato Finale

Dopo il fix:
- ✅ **Tutti gli import funzionano** correttamente
- ✅ **La configurazione viene caricata** senza errori
- ✅ **L'applicazione si avvia** e mostra il menu
- ✅ **Le nuove funzionalità sono disponibili**:
  - Verifica file esistenti in `/database/JSON`
  - Smistamento automatico nelle cartelle appropriate
  - Evitare riscaricamenti di file già presenti

**Il problema è risolto!** 🚀
