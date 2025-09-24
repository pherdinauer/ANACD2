# Dockerfile per ANAC JSON Downloader
FROM python:3.11-slim

# Installa dipendenze di sistema
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crea utente non-root
RUN useradd -m -s /bin/bash anac

# Imposta directory di lavoro
WORKDIR /app

# Copia i file del progetto
COPY . /app/

# Crea le directory necessarie
RUN mkdir -p /database/JSON log cache downloads

# Installa dipendenze Python
RUN pip install --no-cache-dir -r requirements.txt

# Installa Playwright (opzionale)
RUN python -m playwright install chromium

# Imposta i permessi
RUN chown -R anac:anac /app /database

# Cambia utente
USER anac

# Esponi porta (se necessario per API future)
EXPOSE 8000

# Comando di avvio
CMD ["python", "run_anacd2.py"]
