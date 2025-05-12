import os
import requests
import hashlib
import time
import logging
import zipfile
import math
import datetime
from utils import file_exists, ensure_dir, extract_zip_files, format_size
from pathlib import Path

def download_file(url, dest_path, chunk_size=1048576, max_retries=5, backoff=2, logger=None, show_progress=True):
    """
    Scarica un file da un URL con supporto per download a chunk, retry con backoff esponenziale,
    e visualizzazione della velocità e dimensione totale.
    """
    ensure_dir(os.path.dirname(dest_path))
    
    # Headers per simulare una richiesta da browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    attempt = 0
    
    # Prima richiesta HEAD per ottenere dimensione totale (se disponibile)
    content_length = None
    try:
        head_response = requests.head(url, headers=headers, timeout=10)
        if head_response.ok and 'content-length' in head_response.headers:
            content_length = int(head_response.headers['content-length'])
            if content_length > 0 and show_progress:
                print(f"Dimensione file: {format_size(content_length)}")
    except Exception as e:
        if logger:
            logger.debug(f"Impossibile determinare dimensione file per {url}: {e}")
    
    # Ciclo dei tentativi di download con backoff esponenziale
    while attempt < max_retries:
        try:
            # Per download ripreso, inizia da dove si era interrotto se il file esiste già
            resume_header = {}
            if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
                resume_size = os.path.getsize(dest_path)
                if content_length and resume_size >= content_length:
                    # File già completo
                    if logger:
                        logger.info(f"File {dest_path} già scaricato completamente")
                    return calculate_file_hash(dest_path, logger)
                
                resume_header = {'Range': f'bytes={resume_size}-'}
                if show_progress:
                    print(f"Ripresa download da {format_size(resume_size)}")
            
            # Unisci gli headers
            current_headers = {**headers, **resume_header}
            
            # Esegui il download
            with requests.get(url, headers=current_headers, stream=True, timeout=60) as response:
                response.raise_for_status()
                
                # Se stiamo riprendendo, il codice di stato dovrebbe essere 206
                is_resuming = 'Range' in current_headers
                if is_resuming and response.status_code != 206:
                    # Il server non supporta download parziali, ricomincia da capo
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    is_resuming = False
                
                total_size = int(response.headers.get('content-length', 0))
                # Se stiamo riprendendo, somma la dimensione già scaricata
                if is_resuming and total_size > 0:
                    resume_size = os.path.getsize(dest_path)
                    total_size += resume_size
                
                if total_size > 0 and show_progress:
                    print(f"Scaricando {format_size(total_size)} da {url}")
                
                # Apri il file in append se riprendiamo, altrimenti in write
                mode = 'ab' if is_resuming else 'wb'
                
                h = hashlib.sha256()
                downloaded = 0
                start_time = time.time()
                
                # Se riprendiamo, prepara l'hash con il contenuto esistente
                if is_resuming:
                    with open(dest_path, 'rb') as f:
                        data = f.read()
                        h.update(data)
                    downloaded = len(data)
                
                with open(dest_path, mode) as f:
                    # Variabili per il calcolo della velocità
                    last_update_time = start_time
                    last_downloaded = downloaded
                    
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:  # Filtra keep-alive chunks vuoti
                            f.write(chunk)
                            h.update(chunk)
                            downloaded += len(chunk)
                            
                            # Aggiorna velocità e progresso ogni secondo
                            current_time = time.time()
                            if show_progress and (current_time - last_update_time) >= 1:
                                # Calcola velocità in bytes/secondo
                                speed = (downloaded - last_downloaded) / (current_time - last_update_time)
                                
                                # Stima del tempo rimanente
                                if total_size > 0 and speed > 0:
                                    remaining = (total_size - downloaded) / speed
                                    eta = str(datetime.timedelta(seconds=int(remaining)))
                                else:
                                    eta = "sconosciuto"
                                
                                # Progresso in percentuale
                                if total_size > 0:
                                    percent = min(100, downloaded * 100 / total_size)
                                    progress_bar = generate_progress_bar(percent)
                                    print(f"\r{progress_bar} {percent:.1f}% | {format_size(downloaded)}/{format_size(total_size)} | {format_size(speed)}/s | ETA: {eta}", end='')
                                else:
                                    print(f"\rScaricati {format_size(downloaded)} | {format_size(speed)}/s", end='')
                                
                                last_update_time = current_time
                                last_downloaded = downloaded
                
                total_time = time.time() - start_time
                sha256 = h.hexdigest()
                
                if show_progress:
                    if total_size > 0:
                        print(f"\r{generate_progress_bar(100)} 100% | {format_size(total_size)} | Media: {format_size(downloaded/total_time)}/s | Completato in {total_time:.1f}s")
                    else:
                        print(f"\rScaricati {format_size(downloaded)} | Media: {format_size(downloaded/total_time)}/s | Completato in {total_time:.1f}s")
                
                if logger:
                    logger.info(f"Scaricato {url} in {dest_path} ({format_size(downloaded)}, {total_time:.1f}s) SHA256={sha256}")
                
                return sha256
                
        except requests.exceptions.RequestException as e:
            attempt += 1
            wait_time = backoff ** attempt
            
            if show_progress:
                print(f"\nErrore download: {str(e)}")
                print(f"Tentativo {attempt}/{max_retries} - Nuovo tentativo tra {wait_time}s...")
            
            if logger:
                logger.warning(f"Errore download {url}: {e}, tentativo {attempt}/{max_retries} tra {wait_time}s")
            
            time.sleep(wait_time)
            
        except Exception as e:
            attempt += 1
            wait_time = backoff ** attempt
            
            if show_progress:
                print(f"\nErrore inatteso: {str(e)}")
                print(f"Tentativo {attempt}/{max_retries} - Nuovo tentativo tra {wait_time}s...")
            
            if logger:
                logger.warning(f"Errore inatteso durante download {url}: {e}, tentativo {attempt}/{max_retries} tra {wait_time}s")
            
            time.sleep(wait_time)
    
    # Tutti i tentativi sono falliti
    if logger:
        logger.error(f"Download fallito per {url} dopo {max_retries} tentativi")
    
    if show_progress:
        print(f"\nDownload fallito dopo {max_retries} tentativi: {url}")
    
    return None

def calculate_file_hash(file_path, logger=None):
    """Calcola l'hash SHA256 di un file già scaricato."""
    try:
        h = hashlib.sha256()
        with open(file_path, 'rb') as f:
            chunk_size = 1048576  # 1MB
            for chunk in iter(lambda: f.read(chunk_size), b''):
                h.update(chunk)
        sha256 = h.hexdigest()
        
        if logger:
            logger.debug(f"Calcolato hash per {file_path}: {sha256}")
        
        return sha256
    except Exception as e:
        if logger:
            logger.error(f"Errore nel calcolo dell'hash per {file_path}: {e}")
        return None

def generate_progress_bar(percent, width=30):
    """Genera una barra di progresso ASCII."""
    filled_width = int(width * percent / 100)
    bar = '█' * filled_width + '░' * (width - filled_width)
    return f"[{bar}]"

def verify_file_integrity(file_path, expected_hash=None):
    """Verifica integrità del file."""
    if not file_exists(file_path):
        return False
    
    # Verifica che il file non sia vuoto
    if os.path.getsize(file_path) == 0:
        return False
        
    # Verifica hash se fornito
    if expected_hash:
        from utils import sha256sum
        actual_hash = sha256sum(file_path)
        return actual_hash == expected_hash
    
    return True

def should_download(dest_path, expected_hash=None, force=False):
    if force:
        return True
        
    if not file_exists(dest_path):
        return True
        
    if expected_hash:
        from utils import sha256sum
        try:
            return sha256sum(dest_path) != expected_hash
        except:
            # Se c'è un errore nel calcolo dell'hash, meglio scaricare di nuovo
            return True
            
    # Se il file esiste e non c'è un hash di riferimento, verifica che non sia vuoto
    return os.path.getsize(dest_path) == 0

def process_downloaded_file(file_path, extract_dir=None, logger=None, config=None):
    """Processa un file scaricato, estraendo il contenuto se è un ZIP."""
    if not config:
        config = {}
        
    extract_json_only = config.get('extract_json_only', True)
    include_formats = config.get('include_formats', ['json'])
    exclude_formats = config.get('exclude_formats', ['ttl', 'csv', 'xml'])
    
    if file_path.lower().endswith('.zip'):
        if not extract_dir:
            extract_dir = os.path.dirname(file_path)
        
        # Crea cartella con nome del file (senza estensione)
        base_name = os.path.basename(file_path)
        file_name_no_ext = os.path.splitext(base_name)[0]
        extract_subdir = os.path.join(extract_dir, file_name_no_ext)
        ensure_dir(extract_subdir)
        
        try:
            # Estrai file ZIP
            extracted_files = []
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Lista tutti i file nel ZIP
                file_list = zip_ref.namelist()
                
                # Filtra i file in base ai formati da includere/escludere
                filtered_files = []
                for f in file_list:
                    f_lower = f.lower()
                    
                    # Controlla formati da escludere
                    if any(f_lower.endswith(f'.{ext}') or f'_{ext}.' in f_lower for ext in exclude_formats):
                        if logger:
                            logger.debug(f"Escluso file {f} dal formato")
                        continue
                        
                    # Controlla formati da includere se estratti solo JSON
                    if extract_json_only and not any(f_lower.endswith(f'.{ext}') or f'_{ext}.' in f_lower for ext in include_formats):
                        if logger:
                            logger.debug(f"File {f} non è nel formato richiesto")
                        continue
                    
                    filtered_files.append(f)
                
                # Se non ci sono file che rispettano i criteri e siamo in modalità JSON-only
                if not filtered_files and extract_json_only:
                    if logger:
                        logger.warning(f"Nessun file dei formati richiesti trovato in {file_path}")
                    
                    # Se non abbiamo file del tipo richiesto, estraiamo tutto
                    if config.get('extract_all_if_no_match', False):
                        filtered_files = file_list
                        if logger:
                            logger.info(f"Estrazione di tutti i file dall'archivio {base_name}")
                
                # Estrai i file filtrati
                for file_name in filtered_files:
                    zip_ref.extract(file_name, extract_subdir)
                    extracted_path = os.path.join(extract_subdir, file_name)
                    extracted_files.append(extracted_path)
                    if logger:
                        logger.info(f"Estratto file {file_name} da {base_name}")
            
            if logger:
                logger.info(f"Estratti {len(extracted_files)} file su {len(file_list)} presenti nell'archivio {base_name}")
            
            return {
                'is_zip': True,
                'extracted_files': extracted_files,
                'extract_dir': extract_subdir,
                'total_files': len(file_list)
            }
        except Exception as e:
            if logger:
                logger.error(f"Errore durante l'estrazione di {file_path}: {str(e)}")
            return {
                'is_zip': True,
                'error': str(e),
                'extracted_files': []
            }
    
    return {
        'is_zip': False,
        'path': file_path
    }