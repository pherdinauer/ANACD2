# Quick Start per Server Linux

## 🚀 Setup Rapido (3 comandi)

```bash
# 1. Copia il file sul server e rendilo eseguibile
chmod +x server_setup.sh

# 2. Esegui il setup (una volta sola)
./server_setup.sh

# 3. Avvia l'applicazione
chmod +x start.sh && ./start.sh
```

## 📋 Cosa fa il setup

- ✅ Verifica Python 3 e Git
- ✅ Installa dipendenze di sistema
- ✅ Crea ambiente virtuale Python
- ✅ Installa dipendenze Python
- ✅ Configura directory `/database/JSON`
- ✅ Crea cartelle per smistamento automatico
- ✅ Crea file di configurazione

## 🎯 Avvio dell'Applicazione

### Metodo 1: Avvio Semplice
```bash
./start.sh
```

### Metodo 2: Manager Completo
```bash
python3 anac_manager.py
```

Il manager offre un menu con:
- 🚀 Deployment completo
- 🔄 Aggiorna progetto  
- ▶️ Avvia applicazione
- 📊 Mostra stato sistema
- 🧪 Test installazione

## 🔧 Funzionalità Disponibili

Dopo il setup avrai accesso a:

- **Verifica file esistenti**: Evita riscaricamenti inutili
- **Smistamento automatico**: Organizza i file nelle cartelle appropriate
- **Download con smistamento**: Nuova opzione nel menu principale
- **Gestione sessioni tmux**: Per esecuzione in background

## 📁 Struttura Creata

```
/database/JSON/
├── aggiudicatari_json/
├── aggiudicazioni_json/
├── smartcig_json/
├── categorie-opera_json/
└── ... (altre cartelle per smistamento)
```

## 🆘 Risoluzione Problemi

### Errore "Permission Denied"
```bash
sudo chown -R $USER:$USER /database
```

### Errore "Python not found"
```bash
sudo apt install python3 python3-pip  # Ubuntu/Debian
sudo yum install python3 python3-pip  # CentOS/RHEL
```

### Errore "Directory /database/JSON not found"
```bash
sudo mkdir -p /database/JSON
sudo chown $USER:$USER /database/JSON
```

## 📞 Supporto

Se hai problemi:
1. Controlla i log in `log/downloader.log`
2. Esegui `python3 anac_manager.py` e scegli "Test installazione"
3. Verifica che la directory `/database/JSON` sia accessibile

## 🎉 Tutto Pronto!

Dopo il setup, l'applicazione è pronta per:
- Scaricare file JSON/ZIP dal portale ANAC
- Smistare automaticamente i file nelle cartelle appropriate
- Evitare riscaricamenti di file già presenti
- Estrarre automaticamente i file ZIP
