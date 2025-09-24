# 🚀 Quick Start Linux - ANAC JSON Downloader

## 📋 Problema Risolto!

Il problema era che il file di configurazione mostrava l'help invece di essere caricato. **Ora è risolto!**

## 🎯 Come Usare Ora

### 1. **Copia gli script sul server Linux:**
```bash
# Copia tutti gli script
scp *.sh user@server:/path/to/directory/
```

### 2. **Sul server Linux, rendi eseguibili:**
```bash
chmod +x *.sh
```

### 3. **Testa la configurazione:**
```bash
./test_auto_run.sh
```

### 4. **Avvia l'applicazione:**
```bash
# Opzione 1: Script semplice
./simple_auto_run.sh

# Opzione 2: Script completo
./auto_update_and_run.sh

# Opzione 3: Script TMUX
./tmux_auto_run.sh

# Opzione 4: Script finale
./final_auto_run.sh
```

## 🔧 Cosa Ho Corretto

### Problema:
- Il file `simple_auto_run.sh` non caricava la configurazione
- Il file di configurazione mostrava l'help invece di essere caricato

### Soluzione:
- ✅ **Script aggiornati** per caricare automaticamente la configurazione
- ✅ **Configurazione corretta** con il tuo repository: `https://github.com/pherdinauer/ANACD2.git`
- ✅ **Fallback automatico** se il file di configurazione non è trovato

## 📊 Script Disponibili

### 1. **`simple_auto_run.sh`** (Consigliato)
- ✅ Più semplice e veloce
- ✅ Carica automaticamente la configurazione
- ✅ Usa il tuo repository: `pherdinauer/ANACD2`

### 2. **`auto_update_and_run.sh`** (Completo)
- ✅ Più verbose e dettagliato
- ✅ Log completo
- ✅ Gestione errori avanzata

### 3. **`tmux_auto_run.sh`** (Per Server)
- ✅ Gestione automatica delle sessioni tmux
- ✅ Perfetto per server
- ✅ Continua a girare anche se ti disconnetti

### 4. **`final_auto_run.sh`** (Più Robusto)
- ✅ Usa tutte le funzioni avanzate
- ✅ Test completo del sistema
- ✅ Più affidabile

## 🎯 Configurazione Automatica

Tutti gli script ora:
- ✅ **Caricano automaticamente** `auto_run_config.sh`
- ✅ **Usano il tuo repository**: `https://github.com/pherdinauer/ANACD2.git`
- ✅ **Hanno fallback** se la configurazione non è trovata
- ✅ **Sono pronti all'uso** senza modifiche

## 🚀 Test Rapido

```bash
# Sul server Linux
./test_auto_run.sh
```

Questo ti mostrerà:
- ✅ Se la configurazione è caricata correttamente
- ✅ Se le dipendenze sono disponibili
- ✅ Le configurazioni attive

## 🎉 Risultato

Ora puoi:
1. **Copiare gli script sul server**
2. **Renderli eseguibili** con `chmod +x *.sh`
3. **Avviarli direttamente** senza modifiche
4. **L'applicazione si avvia automaticamente** con pull delle ultime commit

**È tutto pronto!** 🚀

## 📝 Note

- **Repository configurato**: `https://github.com/pherdinauer/ANACD2.git`
- **Directory progetto**: `anac-downloader`
- **Sessione tmux**: `anac-downloader`
- **Ambiente virtuale**: `venv`
- **Directory database**: `/database/JSON`

Tutti gli script sono ora **plug-and-play**! 🎯
