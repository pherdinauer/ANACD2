import os
import sys
import json
import hashlib
import logging
import re
import zipfile
import random
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse

# Carica variabili d'ambiente
load_dotenv()

def setup_logger(log_file):
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s %(levelname)s %(message)s'
    )
    # Aggiungi log anche su console
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    logging.getLogger().addHandler(console)
    return logging.getLogger(__name__)


def sha256sum(file_path, chunk_size=1048576):
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(chunk_size), b''):
            h.update(chunk)
    return h.hexdigest()


def file_exists(file_path):
    return Path(file_path).exists()


def ensure_dir(directory):
    Path(directory).mkdir(parents=True, exist_ok=True)


def normalize_url(url, base_url):
    """Normalizza URL relativi e assoluti."""
    if url.startswith('http'):
        return url
    # Per URL che iniziano con /
    elif url.startswith('/'):
        # Estrai dominio dal base_url
        match = re.match(r'(https?://[^/]+)', base_url)
        if match:
            domain = match.group(1)
            return f"{domain}{url}"
    # Per URL relativi
    return f"{base_url.rstrip('/')}/{url.lstrip('/')}"


def sanitize_filename(filename):
    """Rimuove caratteri non validi dai nomi file."""
    return re.sub(r'[\\/*?:"<>|]', '_', filename)


def extract_zip_files(zip_path, extract_dir, logger=None):
    """Estrae file JSON da un file ZIP e restituisce i percorsi ai file estratti."""
    extracted_files = []
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Lista tutti i file nel ZIP
            file_list = zip_ref.namelist()
            
            # Filtra solo i file JSON
            json_files = [f for f in file_list if f.endswith('.json')]
            
            if not json_files and logger:
                logger.warning(f"Nessun file JSON trovato in {zip_path}, estraggo tutti i file")
                json_files = file_list
            
            # Estrai i file
            for file_name in json_files:
                zip_ref.extract(file_name, extract_dir)
                extracted_path = os.path.join(extract_dir, file_name)
                extracted_files.append(extracted_path)
                if logger:
                    logger.info(f"Estratto file {file_name} da {os.path.basename(zip_path)}")
    
    except Exception as e:
        if logger:
            logger.error(f"Errore durante l'estrazione di {zip_path}: {str(e)}")
    
    return extracted_files


def is_json_or_zip_link(url):
    """Verifica se l'URL punta a un file JSON o ZIP che probabilmente contiene JSON."""
    url_lower = url.lower()
    
    # Escludi esplicitamente file TTL e CSV
    if '_ttl.' in url_lower or '_csv.' in url_lower or url_lower.endswith('.ttl') or url_lower.endswith('.csv'):
        return False
    
    # Accetta solo file JSON o ZIP che verosimilmente contengono JSON
    return (
        '.json' in url_lower or 
        ('_json' in url_lower and '.zip' in url_lower) or
        ('json' in url_lower and '.zip' in url_lower)
    )

def save_links_to_cache(links, cache_file="cache/json_links.txt"):
    """Salva i link trovati in un file cache."""
    ensure_dir(os.path.dirname(cache_file))
    with open(cache_file, 'w', encoding='utf-8') as f:
        for link in links:
            f.write(f"{link}\n")

def load_links_from_cache(cache_file="cache/json_links.txt"):
    """Carica i link da un file cache."""
    links = set()
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            for line in f:
                link = line.strip()
                if link:
                    links.add(link)
    return links

def normalize_url_for_comparison(url):
    """
    Normalizza un URL per confronto, eliminando differenze non significative come:
    - http vs https
    - presenza o assenza di slash finale
    - normalizzazione di caratteri maiuscoli/minuscoli
    """
    # Converte in minuscolo
    url = url.lower()
    
    # Rimuovi protocollo (http/https)
    if url.startswith('http://'):
        url = url[7:]
    elif url.startswith('https://'):
        url = url[8:]
    
    # Rimuovi slash finale
    url = url.rstrip('/')
    
    # Rimuovi parametri query se non significativi
    if '?' in url and not any(x in url for x in ['format=', 'download=', 'file=']):
        url = url.split('?')[0]
    
    return url


def find_duplicate_links(links):
    """
    Identifica link duplicati che puntano alla stessa risorsa ma hanno URL diverse.
    Restituisce un dizionario dove le chiavi sono gli URL canonici e i valori sono liste di URL effettivi.
    """
    canonical_urls = {}
    
    for link in links:
        normalized = normalize_url_for_comparison(link)
        if normalized not in canonical_urls:
            canonical_urls[normalized] = []
        canonical_urls[normalized].append(link)
    
    # Filtra solo gli URL che hanno duplicati
    duplicates = {k: v for k, v in canonical_urls.items() if len(v) > 1}
    return duplicates


def deduplicate_links(links, logger=None):
    """
    Rimuove link duplicati mantenendo solo la versione canonica.
    Restituisce l'insieme dei link unici e un rapporto sui duplicati trovati.
    """
    # Converti in set se non lo è già
    if not isinstance(links, set):
        links = set(links)
    
    # Trova i duplicati
    duplicates = find_duplicate_links(links)
    
    # Nessun duplicato trovato
    if not duplicates:
        return links, {"duplicates_found": 0, "before": len(links), "after": len(links)}
    
    # Rimuovi i duplicati
    new_links = set()
    removed = 0
    
    # Per ogni URL normalizzato
    for normalized, dupes in duplicates.items():
        # Scegli preferibilmente un URL HTTPS
        https_versions = [u for u in dupes if u.startswith('https://')]
        if https_versions:
            # Se ci sono versioni HTTPS, prendi la prima
            canonical = https_versions[0]
        else:
            # Altrimenti prendi il primo URL
            canonical = dupes[0]
        
        new_links.add(canonical)
        removed += len(dupes) - 1
        
        if logger:
            logger.info(f"Trovati {len(dupes)} URL duplicati per {normalized}, mantenuto: {canonical}")
            for dupe in dupes:
                if dupe != canonical:
                    logger.debug(f"  Rimosso duplicato: {dupe}")
    
    # Aggiungi i link non duplicati
    for link in links:
        normalized = normalize_url_for_comparison(link)
        if normalized not in duplicates:
            new_links.add(link)
    
    # Prepara il rapporto
    report = {
        "duplicates_found": len(duplicates),
        "links_removed": removed,
        "before": len(links),
        "after": len(new_links)
    }
    
    return new_links, report

def format_size(size_bytes):
    """Formatta una dimensione in bytes in un formato leggibile (KB, MB, GB)."""
    if size_bytes == 0:
        return "0 bytes"
    
    # Definisco le unità di misura
    units = ['bytes', 'KB', 'MB', 'GB', 'TB']
    
    # Calcolo l'indice dell'unità di misura appropriata
    i = 0
    while size_bytes >= 1024 and i < len(units) - 1:
        size_bytes /= 1024.0
        i += 1
    
    # Formatto il risultato con 2 decimali
    return f"{size_bytes:.2f} {units[i]}"

def save_datasets_to_cache(datasets, cache_file="cache/known_datasets.txt"):
    """Salva i dataset noti in un file cache."""
    ensure_dir(os.path.dirname(cache_file))
    with open(cache_file, 'w', encoding='utf-8') as f:
        for dataset in datasets:
            f.write(f"{dataset}\n")

def load_datasets_from_cache(cache_file="cache/known_datasets.txt"):
    """Carica i dataset noti da un file cache."""
    datasets = []
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            for line in f:
                dataset = line.strip()
                if dataset and dataset not in datasets:
                    datasets.append(dataset)
    return datasets

def save_direct_links_to_cache(links, cache_file="cache/known_direct_links.txt"):
    """Salva i link diretti noti in un file cache."""
    ensure_dir(os.path.dirname(cache_file))
    with open(cache_file, 'w', encoding='utf-8') as f:
        for link in links:
            f.write(f"{link}\n")

def load_direct_links_from_cache(cache_file="cache/known_direct_links.txt"):
    """Carica i link diretti noti da un file cache."""
    links = []
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            for line in f:
                link = line.strip()
                if link and link not in links:
                    links.append(link)
    return links