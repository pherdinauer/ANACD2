# 🚀 Opzioni di Installazione - ANAC JSON Downloader

## 📋 Riepilogo delle Opzioni

Hai **3 modi** per installare e configurare il sistema:

### 🎯 Opzione 1: Git Clone (Consigliato)
**Quando usarlo:** Hai accesso al repository Git e vuoi il controllo completo

```bash
# Sul server
git clone <repository-url>
cd anac-downloader
chmod +x server_setup.sh
./server_setup.sh
```

**Vantaggi:**
- ✅ Controllo completo del codice
- ✅ Possibilità di aggiornamenti con `git pull`
- ✅ Accesso a tutte le funzionalità
- ✅ Possibilità di modifiche personalizzate

---

### 🎯 Opzione 2: One Click Setup
**Quando usarlo:** Vuoi un setup automatico completo con un solo file

```bash
# Copia solo questo file sul server
scp one_click_setup.sh user@tuo-server:/path/to/

# Sul server - Setup automatico completo
chmod +x one_click_setup.sh
./one_click_setup.sh
```

**Vantaggi:**
- ✅ Un solo file da copiare
- ✅ Setup completamente automatico
- ✅ Scarica tutto il repository automaticamente
- ✅ Configura tutto e avvia l'applicazione

**Cosa fa:**
1. Verifica e installa Git se necessario
2. Chiede l'URL del repository
3. Clona automaticamente il repository
4. Esegue il setup completo
5. Chiede se avviare l'applicazione

---

### 🎯 Opzione 3: Minimal Setup
**Quando usarlo:** Vuoi solo i file essenziali senza Git

```bash
# Copia solo questo file sul server
scp minimal_setup.sh user@tuo-server:/path/to/

# Sul server - Setup minimo
chmod +x minimal_setup.sh
./minimal_setup.sh
```

**Vantaggi:**
- ✅ Un solo file da copiare
- ✅ Non richiede Git
- ✅ Scarica solo i file essenziali
- ✅ Setup minimo e veloce

**Cosa fa:**
1. Scarica i file essenziali da URL
2. Crea la struttura di directory
3. Installa Python e dipendenze
4. Configura `/database/JSON/`
5. Crea script di avvio

---

## 🎮 Confronto delle Opzioni

| Caratteristica | Git Clone | One Click | Minimal |
|----------------|-----------|-----------|---------|
| **File da copiare** | Tutto il repo | 1 file | 1 file |
| **Richiede Git** | Sì | Opzionale | No |
| **Controllo completo** | ✅ | ✅ | ❌ |
| **Aggiornamenti** | `git pull` | Manuale | Manuale |
| **Velocità setup** | Media | Veloce | Molto veloce |
| **Flessibilità** | Massima | Alta | Bassa |

---

## 🚀 Raccomandazione

### Per Sviluppatori/Amministratori:
**Usa Opzione 1 (Git Clone)**
- Hai il controllo completo
- Puoi fare modifiche
- Aggiornamenti semplici

### Per Utenti Finali:
**Usa Opzione 2 (One Click Setup)**
- Setup automatico
- Un solo file da copiare
- Funziona subito

### Per Setup Veloce:
**Usa Opzione 3 (Minimal Setup)**
- Setup minimo
- Solo file essenziali
- Veloce da configurare

---

## 🔧 Dopo l'Installazione

Indipendentemente dall'opzione scelta, dopo l'installazione:

### Avvio Semplice:
```bash
./start.sh
```

### Manager Completo:
```bash
python3 anac_manager.py
```

### Funzionalità Disponibili:
- ✅ Verifica file esistenti in `/database/JSON`
- ✅ Smistamento automatico nelle cartelle appropriate
- ✅ Evitare riscaricamenti di file già presenti
- ✅ Estrazione automatica di file ZIP
- ✅ Interfaccia CLI completa

---

## 🆘 Risoluzione Problemi

### Problema: "Permission Denied"
```bash
sudo chown -R $USER:$USER /database
```

### Problema: "Python not found"
```bash
sudo apt install python3 python3-pip  # Ubuntu/Debian
```

### Problema: "Directory /database/JSON not found"
```bash
sudo mkdir -p /database/JSON
sudo chown $USER:$USER /database/JSON
```

### Problema: "Git not found" (solo per Opzione 1)
```bash
sudo apt install git  # Ubuntu/Debian
```

---

## 📞 Supporto

Se hai problemi con qualsiasi opzione:

1. **Controlla i log** in `/log/`
2. **Verifica i permessi** delle directory
3. **Usa il manager** per test: `python3 anac_manager.py`
4. **Controlla la configurazione** in `config.json`

---

## 🎯 Riassunto Semplice

**Per la maggior parte degli utenti:**
1. Copia `one_click_setup.sh` sul server
2. Esegui `./one_click_setup.sh`
3. Usa `./start.sh` per avviare l'app
4. Scegli "Download con smistamento automatico" nel menu

**È tutto!** 🎉
