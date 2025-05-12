from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import json
import os
from pathlib import Path
import time
import re
from urllib.parse import urljoin, urlparse
try:
    # Try relative import format (when used as a package)
    from .utils import is_json_or_zip_link, load_datasets_from_cache, save_datasets_to_cache, load_direct_links_from_cache, save_direct_links_to_cache
except ImportError:
    # Fallback to direct import (when used directly)
    from utils import is_json_or_zip_link, load_datasets_from_cache, save_datasets_to_cache, load_direct_links_from_cache, save_direct_links_to_cache


def load_config(config_path='config.json'):
    # Controlla se il percorso è assoluto o relativo
    if not os.path.isabs(config_path):
        # Cerca prima nella directory corrente
        if not os.path.exists(config_path):
            # Poi cerca nella directory dello script
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, config_path)
    
    with open(config_path, 'r') as f:
        return json.load(f)


def extract_dataset_links(page_content, base_url, logger=None):
    """Estrae tutti i link ai dataset dalla pagina principale."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(page_content, 'html.parser')
    links = []
    
    # Cerca link ai dataset (tipicamente titoli di dataset o link "Dettagli")
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Cerca gli URL che sembrano essere link a dataset
        if '/dataset/' in href and not href.endswith(('.json', '.csv', '.xml')):
            # Normalizza URL
            full_url = href
            if not href.startswith(('http://', 'https://')):
                if href.startswith('/'):
                    base_domain = urlparse(base_url).scheme + "://" + urlparse(base_url).netloc
                    full_url = urljoin(base_domain, href)
                else:
                    full_url = urljoin(base_url, href)
            
            links.append(full_url)
            if logger:
                logger.debug(f"Trovato link a dataset: {full_url}")
    
    return links


def extract_json_links_from_dataset_page(page_content, base_url, logger=None, config=None):
    """Estrae link a file JSON e ZIP che contengono JSON dalla pagina di dettaglio del dataset."""
    from bs4 import BeautifulSoup
    
    # Impostazioni predefinite se config non è specificato
    if not config:
        config = {}
    
    include_formats = config.get('include_formats', ['json'])
    exclude_formats = config.get('exclude_formats', ['ttl', 'csv', 'xml'])
    
    soup = BeautifulSoup(page_content, 'html.parser')
    links = []
    
    # Cerca tutti i link nella pagina, inclusi quelli con classe resource-url-analytics
    for a in soup.find_all('a', href=True):
        href = a['href']
        href_lower = href.lower()
        
        # Escludi esplicitamente i formati non desiderati
        if any(f'.{ext}' in href_lower or f'_{ext}.' in href_lower for ext in exclude_formats):
            continue
            
        # Verifica se il link punta a file JSON o ZIP che probabilmente contiene JSON
        if is_json_or_zip_link(href):
            # Normalizza URL
            full_url = href
            if not href.startswith(('http://', 'https://')):
                if href.startswith('/'):
                    base_domain = urlparse(base_url).scheme + "://" + urlparse(base_url).netloc
                    full_url = urljoin(base_domain, href)
                else:
                    full_url = urljoin(base_url, href)
            
            links.append(full_url)
            if logger:
                file_type = "ZIP con JSON" if ".zip" in href else "JSON"
                logger.info(f"Trovato link {file_type}: {full_url}")
    
    # Cerca specificamente link con testo "Vai alla risorsa", "Download", ecc.
    download_texts = ['vai alla risorsa', 'download', 'scarica', 'json', 'zip']
    for a in soup.find_all('a'):
        if a.has_attr('href'):
            # Controlla sia il testo del link che il testo dentro i tag figli
            link_text = a.get_text().lower()
            if any(text in link_text for text in download_texts):
                href = a['href']
                href_lower = href.lower()
                
                # Escludi esplicitamente i formati non desiderati
                if any(f'.{ext}' in href_lower or f'_{ext}.' in href_lower for ext in exclude_formats):
                    continue
                
                # Controllo esplicito per formato JSON nei link con classe resource
                if not any(fmt in href_lower for fmt in include_formats) and 'resource' not in href_lower:
                    continue
                
                full_url = href
                if not href.startswith(('http://', 'https://')):
                    if href.startswith('/'):
                        base_domain = urlparse(base_url).scheme + "://" + urlparse(base_url).netloc
                        full_url = urljoin(base_domain, href)
                    else:
                        full_url = urljoin(base_url, href)
                
                if full_url not in links:  # Evita duplicati
                    links.append(full_url)
                    if logger:
                        logger.info(f"Trovato link download (dal testo): {full_url}")
    
    return links


def find_next_page(page_content, current_page, logger=None):
    """Verifica se esiste una pagina successiva."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(page_content, 'html.parser')
    
    # Cerca link "next" o testo "Successivo" o "prossimo"
    next_link = soup.find('a', {'rel': 'next'}) or \
                soup.find('a', text=re.compile(r'succes|next|avanti|prossim', re.I))
    
    # Cerca anche link che contengono page=X dove X è current_page + 1
    if current_page > 0:
        next_page_num = current_page + 1
        next_page_links = soup.find_all('a', href=re.compile(f'[?&]page={next_page_num}(?:&|$)'))
        if next_page_links and not next_link:
            next_link = next_page_links[0]
    
    if next_link:
        if logger:
            logger.debug(f"Trovato link alla pagina successiva: {next_link.get('href', 'N/A')}")
        return True
    else:
        if logger:
            logger.debug(f"Nessun link alla pagina successiva trovato per pagina {current_page}")
        return False


def add_known_datasets(all_dataset_links, logger=None):
    """Aggiunge dataset noti che potrebbero non essere stati trovati dallo scraping."""
    # Lista predefinita di dataset noti
    default_known_datasets = [
        "https://dati.anticorruzione.it/opendata/dataset/smartcig-tipo-fattispecie-contrattuale",
        "https://dati.anticorruzione.it/opendata/dataset/anac-dataset",
        "https://dati.anticorruzione.it/opendata/dataset/anac-datamart",
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-2022",
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordnari-2020",
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-2021",
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-2019",
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-2018",
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-2017",
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-2016",
        "https://dati.anticorruzione.it/opendata/dataset/dati-contratti-pubblici",
        "https://dati.anticorruzione.it/opendata/dataset/informazioni-sulle-procedure-di-gara-indette-a-partire-dal-1-gennaio-2019",
        "https://dati.anticorruzione.it/opendata/dataset/soggetti-attuatori-pnrr"
    ]
    
    # Carica dataset salvati in precedenza
    cached_datasets = load_datasets_from_cache()
    
    # Unisci i dataset predefiniti con quelli salvati
    known_datasets = list(set(default_known_datasets + cached_datasets))
    
    added_count = 0
    for dataset in known_datasets:
        if dataset not in all_dataset_links:
            all_dataset_links.append(dataset)
            added_count += 1
            if logger:
                logger.info(f"Aggiunto dataset noto: {dataset}")
    
    if logger and added_count > 0:
        logger.info(f"Aggiunti {added_count} dataset noti alla lista di scraping")
    
    return all_dataset_links


def scrape_all_json_links(config, logger=None):
    all_json_links = set()
    base_url = config['base_url']
    visited_datasets = set()
    
    # Opzioni Playwright avanzate
    with sync_playwright() as p:
        browser_options = {
            'headless': not config.get('debug_mode', False)
        }
        
        if 'proxy' in config:
            browser_options['proxy'] = {
                'server': config['proxy']
            }
        
        browser = p.chromium.launch(**browser_options)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
        )
        
        page = context.new_page()
        max_retries = config.get('max_page_retries', 3)
        
        # FASE 1: Scraping delle pagine principali per trovare link ai dataset
        dataset_links = []
        page_num = 1
        empty_pages_consecutive = 0  # Contatore pagine vuote consecutive
        max_empty_consecutive = 2  # Numero massimo di pagine vuote consecutive
        max_pages = config.get('max_pages', 20)  # Numero massimo di pagine da analizzare
        
        # Ciclo fino a quando non raggiungiamo il limite di pagine vuote consecutive o il numero massimo di pagine
        while empty_pages_consecutive < max_empty_consecutive and page_num <= max_pages:
            url = f"{base_url}?page={page_num}" if page_num > 1 else base_url
            if logger:
                logger.info(f"Analisi pagina {page_num}: {url} (Pagine vuote consecutive: {empty_pages_consecutive}/{max_empty_consecutive})")
            
            retry_count = 0
            success = False
            
            while retry_count < max_retries and not success:
                try:
                    if logger:
                        logger.info(f"Navigazione a {url}")
                    
                    response = page.goto(url, timeout=config['timeout']*1000, wait_until="networkidle")
                    
                    if not response or response.status >= 400:
                        if logger:
                            logger.warning(f"Errore risposta HTTP {response.status if response else 'N/A'} per {url}")
                        retry_count += 1
                        time.sleep(2 * retry_count)
                        continue
                    
                    # Attendi caricamento dinamico
                    page.wait_for_load_state("networkidle")
                    
                    # Scorri pagina per attivare lazy loading
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(1000)
                    
                    content = page.content()
                    
                    # Estrai link ai dataset
                    links = extract_dataset_links(content, base_url, logger)
                    
                    # Aggiorna il contatore di pagine vuote consecutive
                    if links:
                        dataset_links.extend(links)
                        empty_pages_consecutive = 0  # Resetta il contatore se troviamo dataset
                        if logger:
                            logger.info(f"Trovati {len(links)} link a dataset in {url} (Reset contatore pagine vuote)")
                    else:
                        empty_pages_consecutive += 1  # Incrementa il contatore se non troviamo dataset
                        if logger:
                            logger.warning(f"Trovati 0 link a dataset in {url} (Pagine vuote consecutive: {empty_pages_consecutive}/{max_empty_consecutive})")
                    
                    # Verifica pagina successiva
                    has_next_page = find_next_page(content, page_num, logger)
                    
                    if not has_next_page:
                        if logger:
                            logger.info(f"Nessuna pagina successiva dopo {url}. Fine della paginazione.")
                        # Se non c'è una pagina successiva, setta empty_pages_consecutive al massimo
                        # per forzare l'uscita dal ciclo
                        empty_pages_consecutive = max_empty_consecutive
                    
                    success = True
                
                except PlaywrightTimeout as e:
                    retry_count += 1
                    if logger:
                        logger.warning(f"Timeout durante lo scraping di {url}: {e}. Tentativo {retry_count}/{max_retries}")
                    time.sleep(5 * retry_count)  # Backoff esponenziale
                
                except Exception as e:
                    retry_count += 1
                    if logger:
                        logger.error(f"Errore durante lo scraping di {url}: {str(e)}. Tentativo {retry_count}/{max_retries}")
                    time.sleep(5 * retry_count)
            
            # Se abbiamo esaurito i tentativi e non abbiamo avuto successo
            if not success:
                if logger:
                    logger.error(f"Abbandono scraping di {url} dopo {max_retries} tentativi falliti")
                empty_pages_consecutive += 1  # Consideriamo un errore come una pagina vuota
            
            # Debug: Stampa stato prima di passare alla pagina successiva
            if logger:
                logger.info(f"Stato dopo pagina {page_num}: {len(dataset_links)} dataset trovati, " +
                           f"{empty_pages_consecutive}/{max_empty_consecutive} pagine vuote consecutive")
            
            # Passa alla pagina successiva
            page_num += 1
        
        # Aggiungi dataset noti che potrebbero non essere stati trovati
        dataset_links = add_known_datasets(dataset_links, logger)
        
        if logger:
            logger.info(f"Trovati complessivamente {len(dataset_links)} link a dataset. Inizio l'estrazione dei file JSON...")
        
        # FASE 2: Visita ogni pagina di dataset per trovare file JSON
        for dataset_url in dataset_links:
            if dataset_url in visited_datasets:
                continue
            
            visited_datasets.add(dataset_url)
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    if logger:
                        logger.info(f"Navigazione al dataset: {dataset_url}")
                    
                    response = page.goto(dataset_url, timeout=config['timeout']*1000, wait_until="networkidle")
                    
                    if not response or response.status >= 400:
                        if logger:
                            logger.warning(f"Errore risposta HTTP {response.status if response else 'N/A'} per {dataset_url}")
                        retry_count += 1
                        time.sleep(2 * retry_count)
                        continue
                    
                    # Attendi caricamento dinamico
                    page.wait_for_load_state("networkidle")
                    
                    # Scorri pagina per attivare lazy loading
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(1000)
                    
                    content = page.content()
                    
                    # Estrai link ai file JSON
                    json_links = extract_json_links_from_dataset_page(content, base_url, logger, config)
                    
                    if logger:
                        logger.info(f"Trovati {len(json_links)} file JSON/ZIP nel dataset {dataset_url}")
                    
                    all_json_links.update(json_links)
                    break
                
                except PlaywrightTimeout as e:
                    retry_count += 1
                    if logger:
                        logger.warning(f"Timeout durante lo scraping di {dataset_url}: {e}. Tentativo {retry_count}/{max_retries}")
                    time.sleep(5 * retry_count)
                
                except Exception as e:
                    retry_count += 1
                    if logger:
                        logger.error(f"Errore durante lo scraping di {dataset_url}: {str(e)}. Tentativo {retry_count}/{max_retries}")
                    time.sleep(5 * retry_count)
            
            # Se abbiamo esaurito i tentativi e non abbiamo avuto successo
            if retry_count >= max_retries:
                if logger:
                    logger.error(f"Abbandono scraping del dataset {dataset_url} dopo {max_retries} tentativi falliti")
        
        browser.close()
    
    # Salva i dataset trovati per futuri scraping
    # Rimuovi duplicati prima del salvataggio
    unique_datasets = list(set(dataset_links))
    save_datasets_to_cache(unique_datasets)
    if logger:
        logger.info(f"Salvati {len(unique_datasets)} dataset per futuri utilizzi")
    
    # Carica link diretti noti precedentemente salvati
    default_known_direct_links = [
        "https://dati.anticorruzione.it/opendata/download/dataset/smartcig-tipo-fattispecie-contrattuale/filesystem/smartcig-tipo-fattispecie-contrattuale_json.zip",
        "https://dati.anticorruzione.it/opendata/download/dataset/soggetti-attuatori-pnrr/filesystem/soggetti-attuatori-pnrr_json.zip",
        "https://dati.anticorruzione.it/opendata/download/dataset/dati-contratti-pubblici/filesystem/dati-contratti-pubblici_json.zip",
        "https://dati.anticorruzione.it/opendata/download/dataset/anac-dataset/filesystem/anac-dataset_json.zip",
        "https://dati.anticorruzione.it/opendata/download/dataset/anac-datamart/filesystem/anac-datamart_json.zip",
        "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2022/filesystem/ocds-appalti-ordinari-2022_json.zip",
        "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2021/filesystem/ocds-appalti-ordinari-2021_json.zip",
        "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2020/filesystem/ocds-appalti-ordinari-2020_json.zip",
        "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2019/filesystem/ocds-appalti-ordinari-2019_json.zip",
        "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2018/filesystem/ocds-appalti-ordinari-2018_json.zip",
        "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2017/filesystem/ocds-appalti-ordinari-2017_json.zip",
        "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2016/filesystem/ocds-appalti-ordinari-2016_json.zip"
    ]
    
    cached_direct_links = load_direct_links_from_cache()
    known_direct_links = list(set(default_known_direct_links + cached_direct_links))
    
    for link in known_direct_links:
        if link not in all_json_links:
            all_json_links.add(link)
            if logger:
                logger.info(f"Aggiunto link diretto noto: {link}")
    
    # Verifica se abbiamo trovato nuovi link diretti e li salva
    # Prima salviamo i link diretti già conosciuti
    direct_links_patterns = [
        r'https://dati\.anticorruzione\.it/opendata/download/dataset/.+?/filesystem/.+?\.(?:json|zip)'
    ]
    
    new_direct_links = []
    for link in all_json_links:
        if any(re.match(pattern, link) for pattern in direct_links_patterns):
            new_direct_links.append(link)
    
    # Aggiorna il file cache con i nuovi link diretti trovati
    if new_direct_links:
        all_direct_links = list(set(known_direct_links + new_direct_links))
        save_direct_links_to_cache(all_direct_links)
        if logger:
            logger.info(f"Aggiornati link diretti noti con {len(new_direct_links)} nuovi link per futuri utilizzi")
    
    if logger:
        logger.info(f"Scraping completato. Trovati {len(all_json_links)} link a file JSON/ZIP.")
    
    return all_json_links