import os
import requests
import json
import hashlib
import time
import logging
import zipfile
import math
import datetime
from pathlib import Path
try:
    # Try relative import format (when used as a package)
    from .utils import file_exists, ensure_dir, extract_zip_files, format_size
except ImportError:
    # Fallback to direct import (when used directly)
    from utils import file_exists, ensure_dir, extract_zip_files, format_size

def download_file(url, dest_path, chunk_size=1048576, max_retries=5, backoff=2, logger=None, show_progress=True, check_database=True):
    """
    Scarica un file da un URL con supporto per download a chunk, retry con backoff esponenziale,
    e visualizzazione della velocità e dimensione totale.
    
    Args:
        check_database: Se True, verifica anche i file esistenti in /database/JSON
    """
    # Messaggi di debug per la risoluzione problemi Linux
    print(f"DEBUG_DOWN: Avvio download da {url}")
    print(f"DEBUG_DOWN: Percorso destinazione: {dest_path}")
    
    # Normalizza il percorso di destinazione
    dest_path = os.path.abspath(os.path.expanduser(dest_path))
    print(f"DEBUG_DOWN: Percorso normalizzato: {dest_path}")
    
    # Verifica se il file esiste già nel percorso di destinazione
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        print(f"DEBUG_DOWN: File già esistente con dimensione di {os.path.getsize(dest_path)} bytes")
        # Calcola l'hash del file esistente e ritornalo
        file_hash = calculate_file_hash(dest_path, logger)
        if file_hash:
            if logger:
                logger.info(f"File {dest_path} esiste già. Saltato. Hash={file_hash}")
            if show_progress:
                print(f"File già esistente. Hash SHA256: {file_hash}")
            return file_hash
    
    # Verifica se il file esiste già in /database/JSON
    if check_database:
        try:
            from .utils import scan_existing_files, should_skip_download
            existing_files, _ = scan_existing_files()
            filename = os.path.basename(dest_path)
            
            should_skip, existing_path = should_skip_download(filename, existing_files)
            if should_skip:
                print(f"DEBUG_DOWN: File {filename} già esistente in {existing_path}")
                if logger:
                    logger.info(f"File {filename} già esistente in database. Saltato.")
                if show_progress:
                    print(f"File {filename} già esistente nel database. Download saltato.")
                return "EXISTING_IN_DATABASE"
        except Exception as e:
            print(f"DEBUG_DOWN: Errore nella verifica database: {e}")
            if logger:
                logger.warning(f"Errore nella verifica file esistenti: {e}")
    
    # Crea la directory di destinazione se non esiste
    dest_dir = os.path.dirname(dest_path)
    print(f"DEBUG_DOWN: Verifica directory: {dest_dir}")
    
    # Messaggio di debug prima di chiamare ensure_dir
    print(f"DEBUG_DOWN: Tentativo creazione/verifica directory {dest_dir}")
    
    # Log funzione ensure_dir
    dir_result = ensure_dir(dest_dir)
    print(f"DEBUG_DOWN: Risultato ensure_dir: {dir_result}")
    
    if not dir_result:
        error_msg = f"Impossibile creare o accedere alla directory per {dest_path}"
        if logger:
            logger.error(error_msg)
        if show_progress:
            print(f"\n{error_msg}")
        print(f"DEBUG_DOWN: ERRORE - {error_msg}")
        
        # Tentativo di fallback
        print(f"DEBUG_DOWN: Tentativo fallback creazione manuale directory")
        try:
            os.makedirs(dest_dir, exist_ok=True)
            print(f"DEBUG_DOWN: Directory creata manualmente")
            
            # Test scrittura dopo creazione manuale
            test_file = os.path.join(dest_dir, '.test_write')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print(f"DEBUG_DOWN: Test scrittura superato dopo creazione manuale")
            except Exception as we:
                print(f"DEBUG_DOWN: Test scrittura fallito: {str(we)}")
                return None
        except Exception as me:
            print(f"DEBUG_DOWN: Fallback fallito: {str(me)}")
            return None
    
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
        print(f"DEBUG_DOWN: Richiesta HEAD a {url}")
        head_response = requests.head(url, headers=headers, timeout=10)
        if head_response.ok and 'content-length' in head_response.headers:
            content_length = int(head_response.headers['content-length'])
            if content_length > 0 and show_progress:
                print(f"Dimensione file: {format_size(content_length)}")
                print(f"DEBUG_DOWN: Dimensione file rilevata: {content_length} bytes")
    except Exception as e:
        print(f"DEBUG_DOWN: Errore HEAD request: {str(e)}")
        if logger:
            logger.debug(f"Impossibile determinare dimensione file per {url}: {e}")
    
    # Ciclo dei tentativi di download con backoff esponenziale
    while attempt < max_retries:
        try:
            print(f"DEBUG_DOWN: Tentativo download #{attempt+1}")
            # Per download ripreso, inizia da dove si era interrotto se il file esiste già
            resume_header = {}
            if os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
                resume_size = os.path.getsize(dest_path)
                print(f"DEBUG_DOWN: File esistente, size={resume_size} bytes")
                # Nota: la verifica del file completo basata sul content-length è ancora utile
                # in caso il file sia stato parzialmente scaricato precedentemente
                if content_length and resume_size >= content_length:
                    # File già completo
                    print(f"DEBUG_DOWN: File già completo")
                    if logger:
                        logger.info(f"File {dest_path} già scaricato completamente")
                    return calculate_file_hash(dest_path, logger)
                
                # Altrimenti continuiamo con la ripresa del download
                resume_header = {'Range': f'bytes={resume_size}-'}
                print(f"DEBUG_DOWN: Riprendo download da {resume_size} bytes")
                if show_progress:
                    print(f"Ripresa download da {format_size(resume_size)}")
            
            # Unisci gli headers
            current_headers = {**headers, **resume_header}
            
            # Esegui il download
            print(f"DEBUG_DOWN: Inizio richiesta GET a {url}")
            with requests.get(url, headers=current_headers, stream=True, timeout=60) as response:
                print(f"DEBUG_DOWN: Risposta ricevuta, status={response.status_code}")
                response.raise_for_status()
                print(f"DEBUG_DOWN: Risposta validata")
                
                # Se stiamo riprendendo, il codice di stato dovrebbe essere 206
                is_resuming = 'Range' in current_headers
                if is_resuming and response.status_code != 206:
                    # Il server non supporta download parziali, ricomincia da capo
                    print(f"DEBUG_DOWN: Server non supporta download parziali, ricomincio da zero")
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    is_resuming = False
                
                total_size = int(response.headers.get('content-length', 0))
                print(f"DEBUG_DOWN: Content-length dalla risposta: {total_size} bytes")
                
                # Se stiamo riprendendo, somma la dimensione già scaricata
                if is_resuming and total_size > 0:
                    resume_size = os.path.getsize(dest_path)
                    total_size += resume_size
                    print(f"DEBUG_DOWN: Dimensione totale stimata (con ripresa): {total_size} bytes")
                
                if total_size > 0 and show_progress:
                    print(f"Scaricando {format_size(total_size)} da {url}")
                
                # Apri il file in append se riprendiamo, altrimenti in write
                mode = 'ab' if is_resuming else 'wb'
                print(f"DEBUG_DOWN: Apertura file con mode='{mode}'")
                
                # Verifica se il file è apribile prima di procedere
                try:
                    test_handle = open(dest_path, mode)
                    test_handle.close()
                    print(f"DEBUG_DOWN: Test apertura file riuscito")
                except Exception as fe:
                    print(f"DEBUG_DOWN: ERRORE apertura file: {str(fe)}")
                    if logger:
                        logger.error(f"Errore apertura file {dest_path}: {str(fe)}")
                    if show_progress:
                        print(f"\nErrore apertura file {dest_path}: {str(fe)}")
                    return None
                
                h = hashlib.sha256()
                downloaded = 0
                start_time = time.time()
                print(f"DEBUG_DOWN: Inizio download, orario={start_time}")
                
                # Se riprendiamo, prepara l'hash con il contenuto esistente
                if is_resuming:
                    print(f"DEBUG_DOWN: Carico contenuto esistente per hash")
                    with open(dest_path, 'rb') as f:
                        data = f.read()
                        h.update(data)
                    downloaded = len(data)
                
                # Apertura file per il download
                print(f"DEBUG_DOWN: Apertura file per scrittura dati")
                
                try:
                    with open(dest_path, mode) as f:
                        # Variabili per il calcolo della velocità
                        last_update_time = start_time
                        last_downloaded = downloaded
                        
                        print(f"DEBUG_DOWN: Inizio download a chunk")
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
                        
                        # Download completato con successo
                        print(f"DEBUG_DOWN: Download completato con successo")
                        
                        total_time = time.time() - start_time
                        sha256 = h.hexdigest()
                        
                        print(f"DEBUG_DOWN: Download completato in {total_time:.1f}s, SHA256={sha256}")
                        print(f"DEBUG_DOWN: Dimensione finale file: {os.path.getsize(dest_path)} bytes")
                        
                        if show_progress:
                            if total_size > 0:
                                print(f"\r{generate_progress_bar(100)} 100% | {format_size(total_size)} | Media: {format_size(downloaded/total_time)}/s | Completato in {total_time:.1f}s")
                            else:
                                print(f"\rScaricati {format_size(downloaded)} | Media: {format_size(downloaded/total_time)}/s | Completato in {total_time:.1f}s")
                        
                        if logger:
                            logger.info(f"Scaricato {url} in {dest_path} ({format_size(downloaded)}, {total_time:.1f}s) SHA256={sha256}")
                        
                        return sha256
                except Exception as write_error:
                    print(f"DEBUG_DOWN: ERRORE durante la scrittura: {str(write_error)}")
                    if logger:
                        logger.error(f"Errore durante la scrittura: {str(write_error)}")
                    if show_progress:
                        print(f"\nErrore durante la scrittura: {str(write_error)}")
                    return None
                
        except requests.exceptions.RequestException as e:
            attempt += 1
            wait_time = backoff ** attempt
            
            print(f"DEBUG_DOWN: Errore richiesta HTTP: {str(e)}")
            
            if show_progress:
                print(f"\nErrore download: {str(e)}")
                print(f"Tentativo {attempt}/{max_retries} - Nuovo tentativo tra {wait_time}s...")
            
            if logger:
                logger.warning(f"Errore download {url}: {e}, tentativo {attempt}/{max_retries} tra {wait_time}s")
            
            time.sleep(wait_time)
            
        except Exception as e:
            attempt += 1
            wait_time = backoff ** attempt
            
            print(f"DEBUG_DOWN: Errore generico: {str(e)}")
            print(f"DEBUG_DOWN: Tipo errore: {type(e).__name__}")
            
            if show_progress:
                print(f"\nErrore inatteso: {str(e)}")
                print(f"Tentativo {attempt}/{max_retries} - Nuovo tentativo tra {wait_time}s...")
            
            if logger:
                logger.warning(f"Errore inatteso durante download {url}: {e}, tentativo {attempt}/{max_retries} tra {wait_time}s")
            
            time.sleep(wait_time)
    
    # Tutti i tentativi sono falliti
    print(f"DEBUG_DOWN: Download fallito definitivamente dopo {max_retries} tentativi")
    
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
    """
    Determina se un file deve essere scaricato.
    
    Args:
        dest_path: Percorso di destinazione del file
        expected_hash: Hash SHA256 atteso del file (se noto)
        force: Se True, forza il download anche se il file esiste
        
    Returns:
        bool: True se il file deve essere scaricato, False altrimenti
    """
    # Forza il download se richiesto
    if force:
        return True
        
    # Il file non esiste, deve essere scaricato
    if not file_exists(dest_path):
        return True
    
    # Il file esiste ma è vuoto, deve essere scaricato
    if os.path.getsize(dest_path) == 0:
        return True
        
    # Se abbiamo un hash atteso, verifica che corrisponda
    if expected_hash:
        from utils import sha256sum
        try:
            actual_hash = sha256sum(dest_path)
            return actual_hash != expected_hash
        except Exception as e:
            # Se c'è un errore nel calcolo dell'hash, meglio scaricare di nuovo
            print(f"Errore nel calcolo hash: {str(e)}. Eseguo nuovo download.")
            return True
    
    # Il file esiste, non è vuoto e non abbiamo un hash di riferimento
    # Non scaricare nuovamente (questo è il cambiamento principale)
    return False

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

def download_with_auto_sorting(url, base_download_dir, logger=None, show_progress=True, extract_zip=True):
    """
    Scarica un file e lo smista automaticamente nella cartella appropriata in /database/JSON.
    
    Args:
        url: URL del file da scaricare
        base_download_dir: Directory base per i download temporanei
        logger: Logger per i messaggi
        show_progress: Se mostrare il progresso del download
        extract_zip: Se estrarre automaticamente i file ZIP
        
    Returns:
        dict: Informazioni sul file scaricato e smistato
    """
    try:
        from .utils import scan_existing_files, determine_target_folder, ensure_dir
        
        # Scansiona i file esistenti e le cartelle disponibili
        existing_files, available_folders = scan_existing_files()
        
        # Estrai il nome del file dall'URL
        filename = os.path.basename(url.split('?')[0])
        if not filename:
            filename = f"download_{int(time.time())}.dat"
        
        # Verifica se il file esiste già
        from .utils import should_skip_download
        should_skip, existing_path = should_skip_download(filename, existing_files)
        if should_skip:
            if logger:
                logger.info(f"File {filename} già esistente in {existing_path}. Saltato.")
            if show_progress:
                print(f"File {filename} già esistente. Saltato.")
            return {
                'success': True,
                'skipped': True,
                'filename': filename,
                'existing_path': existing_path,
                'message': 'File già esistente'
            }
        
        # Determina la cartella di destinazione
        target_folder = determine_target_folder(filename, available_folders)
        
        if not target_folder:
            # Se non trova una cartella specifica, usa una cartella generica
            target_folder = "altri_file_json"
            if logger:
                logger.warning(f"Nessuna cartella specifica trovata per {filename}, uso {target_folder}")
            if show_progress:
                print(f"Nessuna cartella specifica trovata per {filename}, uso {target_folder}")
        
        # Crea il percorso di destinazione
        database_path = "/database/JSON"
        target_dir = os.path.join(database_path, target_folder)
        
        # Assicurati che la cartella di destinazione esista
        if not ensure_dir(target_dir):
            if logger:
                logger.error(f"Impossibile creare la cartella {target_dir}")
            return {
                'success': False,
                'error': f"Impossibile creare la cartella {target_dir}"
            }
        
        # Percorso completo del file di destinazione
        dest_path = os.path.join(target_dir, filename)
        
        # Scarica il file
        if show_progress:
            print(f"Scaricamento di {filename} in {target_folder}...")
        
        file_hash = download_file(
            url, 
            dest_path, 
            logger=logger, 
            show_progress=show_progress,
            check_database=False  # Non controllare di nuovo il database
        )
        
        if not file_hash or file_hash == "EXISTING_IN_DATABASE":
            return {
                'success': False,
                'error': 'Download fallito'
            }
        
        result = {
            'success': True,
            'filename': filename,
            'target_folder': target_folder,
            'dest_path': dest_path,
            'hash': file_hash,
            'extracted_files': []
        }
        
        # Se è un file ZIP e l'estrazione è abilitata
        if dest_path.lower().endswith('.zip') and extract_zip:
            if show_progress:
                print(f"Estrazione di {filename}...")
            
            # Estrai nella stessa cartella
            extract_dir = os.path.splitext(dest_path)[0]
            try:
                os.makedirs(extract_dir, exist_ok=True)
                extracted = extract_zip_files(dest_path, extract_dir, logger)
                result['extracted_files'] = extracted
                
                if show_progress:
                    print(f"Estratti {len(extracted)} file da {filename}")
                
            except Exception as e:
                if logger:
                    logger.error(f"Errore durante l'estrazione di {filename}: {e}")
                result['extraction_error'] = str(e)
        
        if logger:
            logger.info(f"File {filename} scaricato e smistato in {target_folder}")
        
        return result
        
    except Exception as e:
        if logger:
            logger.error(f"Errore durante il download con smistamento: {e}")
        return {
            'success': False,
            'error': str(e)
        }