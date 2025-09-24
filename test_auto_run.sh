#!/bin/bash

# Test script per verificare la configurazione

echo "=========================================="
echo "  TEST AUTO RUN CONFIGURATION"
echo "=========================================="

# Carica la configurazione
if [ -f "auto_run_config.sh" ]; then
    echo "✓ File di configurazione trovato"
    source auto_run_config.sh
    echo "✓ Configurazione caricata"
    
    echo ""
    echo "Configurazioni caricate:"
    echo "  REPO_URL: $REPO_URL"
    echo "  PROJECT_DIR: $PROJECT_DIR"
    echo "  TMUX_SESSION_NAME: $TMUX_SESSION_NAME"
    echo "  VENV_DIR: $VENV_DIR"
    echo "  DATABASE_DIR: $DATABASE_DIR"
    echo ""
    
    echo "Test funzioni:"
    if check_python; then
        echo "✓ check_python: OK"
    else
        echo "✗ check_python: FAILED"
    fi
    
    if check_git; then
        echo "✓ check_git: OK"
    else
        echo "✗ check_git: FAILED"
    fi
    
    if check_tmux; then
        echo "✓ check_tmux: OK"
    else
        echo "✗ check_tmux: FAILED"
    fi
    
    echo ""
    echo "Test completato!"
    
else
    echo "✗ File di configurazione non trovato"
    exit 1
fi
