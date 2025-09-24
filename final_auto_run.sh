#!/bin/bash

# ANAC JSON Downloader - Final Auto Run
# Script finale che usa la configurazione e gestisce tutto automaticamente

set -e

# Carica la configurazione
source "$(dirname "$0")/auto_run_config.sh"

echo "=========================================="
print_header "  ANAC JSON DOWNLOADER - FINAL AUTO RUN"
echo "=========================================="
print_header "  Script finale per pull automatico e avvio"
echo "=========================================="

log "Avvio script final auto-run"

# Verifica se siamo nella directory corretta
if [ ! -f "run_anacd2.py" ] && [ ! -d "$PROJECT_DIR" ]; then
    print_error "Directory del progetto non trovata!"
    print_status "Assicurati di essere nella directory corretta o che il progetto sia clonato"
    exit 1
fi

# Se siamo già nella directory del progetto, usa la directory corrente
if [ -f "run_anacd2.py" ]; then
    PROJECT_DIR="."
    print_status "Trovato progetto nella directory corrente"
else
    print_status "Progetto trovato in: $PROJECT_DIR"
fi

# Entra nella directory del progetto
cd "$PROJECT_DIR"

print_step "1. Verifica dipendenze di sistema"

# Verifica dipendenze
if ! check_all_dependencies; then
    print_warning "Alcune dipendenze mancano, installazione..."
    if ! install_system_dependencies; then
        print_error "Impossibile installare dipendenze di sistema"
        exit 1
    fi
fi

print_step "2. Verifica Git e repository"

# Verifica se è un repository Git
if ! is_git_repo; then
    print_warning "Directory non è un repository Git"
    print_status "Clonazione repository..."
    
    # Torna alla directory parent
    cd ..
    
    # Rimuovi directory esistente se presente
    remove_directory "$PROJECT_DIR"
    
    # Clona il repository
    git_clone
    cd "$PROJECT_DIR"
    print_success "Repository clonato"
else
    print_success "Repository Git trovato"
fi

print_step "3. Pull delle ultime commit"

# Verifica connessione internet
if check_internet; then
    print_status "Connessione internet OK, aggiorno repository..."
    
    # Fetch e pull
    git_fetch
    
    # Controlla se ci sono aggiornamenti
    if has_updates; then
        print_status "Aggiornamenti disponibili, eseguo pull..."
        git_pull
        print_success "Repository aggiornato alle ultime commit"
    else
        print_success "Repository già aggiornato"
    fi
else
    print_warning "Connessione internet non disponibile, uso versione locale"
fi

print_step "4. Verifica ambiente virtuale"

# Verifica se l'ambiente virtuale esiste
if ! directory_exists "$VENV_DIR"; then
    print_warning "Ambiente virtuale non trovato, creazione..."
    create_venv
else
    print_success "Ambiente virtuale trovato"
fi

# Attiva ambiente virtuale
activate_venv

print_step "5. Installazione/aggiornamento dipendenze"

# Installa/aggiorna dipendenze
install_python_dependencies

print_step "6. Verifica configurazione"

# Verifica file di configurazione
check_config

# Verifica directory /database/JSON
check_database_directory

print_step "7. Test finale"

# Esegui test completo
if ! run_full_test; then
    print_error "Test fallito, interruzione"
    exit 1
fi

print_step "8. Avvio applicazione"

print_success "Tutto pronto! Avvio applicazione..."
echo ""
print_header "=========================================="
print_success "  APPLICAZIONE AVVIATA"
print_header "=========================================="
echo ""

# Avvia l'applicazione in background e cattura il PID
start_application

print_status "Applicazione avviata con PID: $APP_PID"
print_status "Per fermare l'applicazione: Ctrl+C"
print_status "Log salvato in: $LOG_FILE"
echo ""

# Attendi che l'applicazione finisca
wait $APP_PID

# Cleanup automatico
cleanup
