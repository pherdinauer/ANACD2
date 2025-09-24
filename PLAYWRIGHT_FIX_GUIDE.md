# 🎭 Playwright Fix Guide - ANAC JSON Downloader

## 🚨 Problema Identificato

L'errore che stai vedendo è causato da:

1. **Playwright non ha i browser installati** - Serve eseguire `playwright install`
2. **L'applicazione è in modalità tmux** e non può leggere l'input correttamente

## ✅ Soluzioni Implementate

Ho creato diversi script per risolvere il problema:

### 1. **Fix Playwright**
- `fix_playwright.sh` - Installa i browser di Playwright

### 2. **Modalità Senza Playwright**
- `run_without_playwright.py` - Avvia l'app senza Playwright

### 3. **Exit TMUX**
- `exit_tmux_and_restart.sh` - Esce da tmux e riavvia correttamente

## 🚀 Come Risolvere

### Opzione 1: Fix Playwright (Se vuoi usare Playwright)

```bash
# Sul server Linux
chmod +x fix_playwright.sh
./fix_playwright.sh
```

**Questo script:**
- ✅ Installa i browser di Playwright
- ✅ Installa le dipendenze di sistema
- ✅ Configura tutto per Playwright

### Opzione 2: Senza Playwright (Consigliato)

```bash
# Sul server Linux
python3 run_without_playwright.py
```

**Questo script:**
- ✅ Disabilita Playwright
- ✅ Avvia l'app con le funzionalità disponibili
- ✅ Non richiede browser

### Opzione 3: Exit TMUX e Riavvia

```bash
# Sul server Linux
chmod +x exit_tmux_and_restart.sh
./exit_tmux_and_restart.sh
```

**Questo script:**
- ✅ Esce dalla sessione tmux
- ✅ Ti mostra le opzioni per riavviare

## 🎯 Funzionalità Disponibili

### **Con Playwright (dopo fix):**
- ✅ Ricerca approfondita (scraping web)
- ✅ Download da URL specifico
- ✅ Download con smistamento automatico
- ✅ Gestione cache e link
- ✅ Verifica integrità file

### **Senza Playwright:**
- ✅ Download da URL specifico
- ✅ Download con smistamento automatico
- ✅ Gestione cache e link
- ✅ Verifica integrità file
- ❌ Ricerca approfondita (scraping web)

## 🔧 Fix Manuale Playwright

Se preferisci fare il fix manualmente:

```bash
# Attiva ambiente virtuale
source venv/bin/activate

# Installa browser Playwright
playwright install

# Installa dipendenze di sistema
playwright install-deps
```

## 🎯 Raccomandazione

**Per il tuo caso specifico, consiglio:**

### **Opzione A: Senza Playwright (Più Semplice)**
```bash
python3 run_without_playwright.py
```

### **Opzione B: Con Playwright (Più Funzionalità)**
```bash
./fix_playwright.sh
python3 run_interactive.py
```

## 📊 Confronto Opzioni

| Caratteristica | Senza Playwright | Con Playwright |
|----------------|------------------|----------------|
| **Setup** | ✅ Immediato | ⚠️ Richiede fix |
| **Funzionalità** | ✅ Download, Cache, Verifica | ✅ Tutto + Scraping |
| **Stabilità** | ✅ Molto stabile | ⚠️ Dipende da browser |
| **Risorse** | ✅ Leggere | ⚠️ Più pesante |

## 🎉 Risultato Atteso

### **Senza Playwright:**
```
============================================================
     ANAC JSON DOWNLOADER - NO PLAYWRIGHT MODE
============================================================
ℹ️  Modalità disponibili:
   - Download da URL specifico
   - Download con smistamento automatico
   - Gestione cache e link
   - Verifica integrità file

MENU PRINCIPALE:
1. Esegui scraping delle pagine web (cerca file JSON/ZIP) [DISABILITATO]
2. Scarica i file JSON/ZIP trovati
3. Verifica integrità file già scaricati
4. Visualizza link in cache
5. Aggiungi link manualmente alla cache
6. Carica link da file esterno
7. Deduplicazione avanzata dei link
8. Gestisci dataset e link diretti noti
0. Esci dal programma
```

### **Con Playwright (dopo fix):**
```
============================================================
     ANAC JSON DOWNLOADER - UTILITY DI DOWNLOAD
============================================================

MENU PRINCIPALE:
1. Esegui scraping delle pagine web (cerca file JSON/ZIP) [ABILITATO]
2. Scarica i file JSON/ZIP trovati
3. Verifica integrità file già scaricati
4. Visualizza link in cache
5. Aggiungi link manualmente alla cache
6. Carica link da file esterno
7. Deduplicazione avanzata dei link
8. Gestisci dataset e link diretti noti
0. Esci dal programma
```

## 🆘 Se Hai Ancora Problemi

### Problema: "Permission Denied"
```bash
chmod +x *.sh
```

### Problema: "Playwright install failed"
```bash
# Prova senza Playwright
python3 run_without_playwright.py
```

### Problema: "Still in tmux"
```bash
# Esci da tmux
tmux detach-client
# Oppure
exit
```

## 🎯 Riassunto

**Hai 3 opzioni:**

1. **`./fix_playwright.sh`** - Fix Playwright completo
2. **`python3 run_without_playwright.py`** - Senza Playwright (consigliato)
3. **`./exit_tmux_and_restart.sh`** - Exit tmux e riavvia

**Il problema è risolto!** 🚀
