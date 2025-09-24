# 🚀 ANAC JSON Downloader - Auto Run Instructions

## 📋 Script Disponibili

Hai **4 script** per l'auto-run automatico:

### 1. **`auto_update_and_run.sh`** (Completo)
- ✅ Pull automatico delle ultime commit
- ✅ Verifica e installa dipendenze
- ✅ Configura ambiente virtuale
- ✅ Avvia applicazione
- ✅ Gestione errori completa
- ✅ Log dettagliato

### 2. **`simple_auto_run.sh`** (Semplice)
- ✅ Pull automatico delle ultime commit
- ✅ Configurazione base
- ✅ Avvio applicazione
- ✅ Meno verbose, più veloce

### 3. **`tmux_auto_run.sh`** (Per TMUX)
- ✅ Pull automatico delle ultime commit
- ✅ Avvia in sessione tmux
- ✅ Gestione sessione automatica
- ✅ Perfetto per server

### 4. **`final_auto_run.sh`** (Finale)
- ✅ Usa configurazione avanzata
- ✅ Test completo del sistema
- ✅ Gestione errori avanzata
- ✅ Più robusto e affidabile

## 🎯 Come Usare

### Opzione 1: Script Semplice (Consigliato per iniziare)

```bash
# 1. Modifica l'URL del repository nel file
nano simple_auto_run.sh
# Cambia: REPO_URL="https://github.com/your-username/anac-downloader.git"

# 2. Rendi eseguibile
chmod +x simple_auto_run.sh

# 3. Avvia
./simple_auto_run.sh
```

### Opzione 2: Script Completo

```bash
# 1. Modifica l'URL del repository nel file
nano auto_update_and_run.sh
# Cambia: REPO_URL="https://github.com/your-username/anac-downloader.git"

# 2. Rendi eseguibile
chmod +x auto_update_and_run.sh

# 3. Avvia
./auto_update_and_run.sh
```

### Opzione 3: Script TMUX (Per Server)

```bash
# 1. Modifica l'URL del repository nel file
nano tmux_auto_run.sh
# Cambia: REPO_URL="https://github.com/your-username/anac-downloader.git"

# 2. Rendi eseguibile
chmod +x tmux_auto_run.sh

# 3. Avvia
./tmux_auto_run.sh
```

### Opzione 4: Script Finale (Più Robusto)

```bash
# 1. Modifica l'URL del repository nel file di configurazione
nano auto_run_config.sh
# Cambia: REPO_URL="https://github.com/your-username/anac-downloader.git"

# 2. Rendi eseguibile
chmod +x final_auto_run.sh

# 3. Avvia
./final_auto_run.sh
```

## 🔧 Configurazione

### Modifica URL Repository

In **tutti** gli script, devi modificare questa riga:
```bash
REPO_URL="https://github.com/your-username/anac-downloader.git"
```

Sostituisci `your-username` con il tuo username GitHub e `anac-downloader` con il nome del tuo repository.

### Esempi di URL:

```bash
# Repository pubblico
REPO_URL="https://github.com/mario-rossi/anac-downloader.git"

# Repository privato (richiede autenticazione)
REPO_URL="https://github.com/mario-rossi/anac-downloader-private.git"

# Repository con branch specifico
REPO_URL="https://github.com/mario-rossi/anac-downloader.git"
# Poi modifica il branch nel codice se necessario
```

## 🚀 Uso con TMUX

### Avvio in TMUX:

```bash
# Avvia script in tmux
tmux new-session -d -s anac-downloader './auto_update_and_run.sh'

# Attacca alla sessione
tmux attach -t anac-downloader

# Stacca dalla sessione (l'app continua a girare)
# Premi: Ctrl+B, poi D

# Riconnettiti alla sessione
tmux attach -t anac-downloader

# Ferma la sessione
tmux kill-session -t anac-downloader
```

### Script TMUX Automatico:

```bash
# Usa lo script tmux_auto_run.sh
./tmux_auto_run.sh

# Questo script:
# 1. Crea automaticamente la sessione tmux
# 2. Fa il pull delle ultime commit
# 3. Avvia l'applicazione
# 4. Ti attacca alla sessione
```

## 📊 Cosa Succede Automaticamente

### Durante l'Esecuzione:

1. **Verifica dipendenze** (Python, Git, tmux)
2. **Pull delle ultime commit** dal repository
3. **Configurazione ambiente virtuale**
4. **Installazione dipendenze Python**
5. **Verifica configurazione**
6. **Creazione directory /database/JSON**
7. **Avvio applicazione**

### Gestione Errori:

- ✅ **Connessione internet**: Se non c'è, usa versione locale
- ✅ **Repository non trovato**: Clona automaticamente
- ✅ **Dipendenze mancanti**: Installa automaticamente
- ✅ **Ambiente virtuale**: Crea se non esiste
- ✅ **Configurazione**: Crea da esempio se manca
- ✅ **Directory database**: Crea con permessi corretti

## 🆘 Risoluzione Problemi

### Problema: "Permission Denied"
```bash
chmod +x *.sh
```

### Problema: "Repository not found"
```bash
# Verifica l'URL del repository
# Assicurati che il repository esista e sia accessibile
```

### Problema: "Python not found"
```bash
# Lo script installa automaticamente Python
# Se fallisce, installa manualmente:
sudo apt install python3 python3-pip python3-venv
```

### Problema: "Git not found"
```bash
# Lo script installa automaticamente Git
# Se fallisce, installa manualmente:
sudo apt install git
```

### Problema: "tmux not found"
```bash
# Lo script installa automaticamente tmux
# Se fallisce, installa manualmente:
sudo apt install tmux
```

## 🎯 Raccomandazione

### Per Iniziare:
**Usa `simple_auto_run.sh`**
- Più semplice
- Meno verbose
- Veloce da configurare

### Per Produzione:
**Usa `final_auto_run.sh`**
- Più robusto
- Gestione errori avanzata
- Test completo del sistema

### Per Server:
**Usa `tmux_auto_run.sh`**
- Gestione sessione automatica
- Perfetto per server
- Continua a girare anche se ti disconnetti

## 📝 Note Importanti

1. **Modifica sempre l'URL del repository** prima di usare gli script
2. **Assicurati di avere i permessi** per creare directory in `/database/`
3. **Gli script installano automaticamente** le dipendenze mancanti
4. **L'applicazione continua a girare** anche se ti disconnetti (con tmux)
5. **I log sono salvati** in `auto_update.log`

## 🎉 Risultato Finale

Dopo l'esecuzione di qualsiasi script:

- ✅ **Repository aggiornato** alle ultime commit
- ✅ **Ambiente configurato** e pronto
- ✅ **Applicazione avviata** e funzionante
- ✅ **Nuove funzionalità disponibili**:
  - Verifica file esistenti in `/database/JSON`
  - Smistamento automatico nelle cartelle appropriate
  - Evitare riscaricamenti di file già presenti

**È tutto automatico!** 🚀
