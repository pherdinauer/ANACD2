from urllib.parse import urljoin, urlparse
import json
import os
from pathlib import Path
import time
import re
import os
try:
    # Try relative import format (when used as a package)
    from .utils import is_json_or_zip_link, load_datasets_from_cache, save_datasets_to_cache, load_direct_links_from_cache, save_direct_links_to_cache
except ImportError:
    # Fallback to direct import (when used directly)
    from utils import is_json_or_zip_link, load_datasets_from_cache, save_datasets_to_cache, load_direct_links_from_cache, save_direct_links_to_cache

# Check if Playwright should be disabled
NO_PLAYWRIGHT = os.environ.get('NO_PLAYWRIGHT', '0') == '1'

if not NO_PLAYWRIGHT:
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    except ImportError:
        NO_PLAYWRIGHT = True
        print("Avviso: Playwright non disponibile, utilizzo modalità senza scraping.")


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
    import time
    
    # Inizio timestamp per misurare il tempo di elaborazione
    start_time = time.time()
    
    if logger:
        logger.info("Inizio estrazione link da pagina dataset...")
    print("Analisi della pagina alla ricerca di link di download...")
    
    # Impostazioni predefinite se config non è specificato
    if not config:
        config = {}
    
    include_formats = config.get('include_formats', ['json', 'zip'])
    exclude_formats = config.get('exclude_formats', ['ttl', 'csv', 'xml'])
    
    soup = BeautifulSoup(page_content, 'html.parser')
    links = set()  # Uso un set per evitare link duplicati
    found_links_info = {}  # Per tenere traccia dei link trovati e del loro contesto
    
    # Verifica se la pagina contiene contenuti validi
    if len(page_content) < 100:
        if logger:
            logger.warning(f"Contenuto pagina troppo breve: {len(page_content)} caratteri. Possibile errore nel caricamento.")
        print(f"Contenuto pagina sospetto (solo {len(page_content)} caratteri). Possibile errore.")
        
    if not soup.find('body'):
        if logger:
            logger.warning("Nessun elemento <body> trovato nella pagina. HTML non valido.")
        print("Struttura pagina non valida. HTML incompleto.")
    
    # Statistiche per il debug
    total_links = len(soup.find_all('a', href=True))
    if logger:
        logger.debug(f"Trovati {total_links} link totali nella pagina")
    print(f"Trovati {total_links} link totali nella pagina")
    
    # 1. RICERCA AVANZATA DI LINK PER ATTRIBUTI E CLASSI SPECIFICHE
    print("Ricerca link tramite attributi e classi specifiche...")
    
    # Cerca tutti i link che potrebbero contenere risorse di dati
    data_elements = [
        # I più comuni contenitori di link di risorse
        soup.find_all('a', class_=lambda c: c and ('resource-url' in c or 'download' in c)),
        soup.find_all('a', attrs={'data-format': lambda f: f and f.lower() in include_formats}),
        soup.find_all('a', attrs={'data-resource-id': True}),  # Link che identificano risorse
        soup.find_all('a', href=lambda h: h and ('download' in h.lower() or 'resource' in h.lower() or 'dataset' in h.lower())),
        
        # Pulsanti o link di download
        soup.find_all('button', class_=lambda c: c and ('download' in c or 'resource' in c)),
        soup.find_all('a', class_=lambda c: c and ('btn' in c and 'download' in c)),
        
        # Contenitori di risorse
        soup.select('.resources a'),  # Link all'interno di div con classe resources
        soup.select('.resource-item a'),  # Link all'interno di elementi resource-item
        soup.select('.dataset-resources a'),  # Link all'interno di elementi dataset-resources
        
        # Ricerca più ampia per i portali CKAN standard
        soup.select('[data-module="resource-view"] a'),
        soup.select('.resource-actions a')
    ]
    
    # Appiattisci l'elenco di tutti gli elementi e rimuovi duplicati
    data_elements_flat = set()
    for element_list in data_elements:
        for element in element_list:
            if hasattr(element, 'get') and element.get('href'):
                data_elements_flat.add(element)
    
    # 2. RICERCA PER CONTENUTO TESTUALE
    print("Ricerca link tramite contenuto testuale...")
    
    # Cerca link con testo specifico che suggerisce un download
    download_texts = ['vai alla risorsa', 'download', 'scarica', 'json', 'zip', 'apri', 'dati', 'open data', 
                    'dataset', 'risorsa', 'file', 'export', 'esporta']
    text_elements = soup.find_all('a', href=True)
    
    for a in text_elements:
        # Controlla sia il testo del link che il testo dentro i tag figli
        link_text = a.get_text().lower().strip()
        
        if any(text in link_text for text in download_texts):
            data_elements_flat.add(a)
    
    print(f"Trovati {len(data_elements_flat)} link potenziali tramite ricerca mirata")
    if logger:
        logger.debug(f"Trovati {len(data_elements_flat)} link potenziali da analizzare")
    
    # 3. ANALISI DI TUTTI I LINK TROVATI
    print("Analisi dettagliata dei link trovati...")
    analyzed_count = 0
    valid_count = 0
    
    for element in data_elements_flat:
        analyzed_count += 1
        href = element.get('href')
        if not href:
            continue
            
        href_lower = href.lower()
        element_text = element.get_text().lower().strip()
        
        # Ignora link che puntano esplicitamente a formati da escludere
        if any(f'.{ext}' in href_lower for ext in exclude_formats):
            continue
            
        # Verifica se il link punta a file JSON o ZIP, o contiene percorsi specifici
        is_valid_link = (
            is_json_or_zip_link(href) or
            '/download/' in href_lower or
            '/filesystem/' in href_lower or
            '/resource/' in href_lower or
            'format=json' in href_lower or
            'api/action/datastore_search' in href_lower or  # API CKAN
            any(fmt in href_lower for fmt in include_formats)
        )
        
        # Seconda verifica per URL ambigui
        if not is_valid_link:
            # Ultima chance: controlla il testo o attributi specifici
            if 'json' in element_text or 'zip' in element_text or 'download' in element_text:
                is_valid_link = True
                if logger:
                    logger.debug(f"Link accettato tramite testo: {href} (testo: {element_text})")
            
            # Attributo data-format (comune in CKAN)
            if element.get('data-format') and element.get('data-format').lower() in include_formats:
                is_valid_link = True
        
        if not is_valid_link:
            continue
        
        valid_count += 1
        
        # Normalizza URL
        full_url = href
        if not href.startswith(('http://', 'https://')):
            if href.startswith('/'):
                base_domain = urlparse(base_url).scheme + "://" + urlparse(base_url).netloc
                full_url = urljoin(base_domain, href)
            else:
                full_url = urljoin(base_url, href)
        
        # Rimuovi parametri di tracking o sessione non necessari
        # Mantieni solo parametri essenziali come 'id', 'resource_id', 'format'
        parsed_url = urlparse(full_url)
        path = parsed_url.path
        
        # Ripulisci l'URL se necessario
        clean_url = full_url
        
        # Aggiungi il link solo se non è già stato trovato
        if clean_url not in links:
            links.add(clean_url)
            
            # Memorizza informazioni sul link per il log
            found_links_info[clean_url] = {
                'text': element_text if element_text else 'N/A',
                'filename': href.split('/')[-1] if '/' in href else href,
                'context': 'formato esplicito' if any(fmt in href_lower for fmt in include_formats) else 'potenziale risorsa'
            }
            
            if logger:
                file_type = "ZIP" if ".zip" in href_lower else "JSON" if ".json" in href_lower else "Risorsa"
                logger.info(f"Trovato link {file_type}: {clean_url} (testo: {element_text[:30]}...)")
            print(f"Trovato: {clean_url}")
    
    # 4. ELABORAZIONE FINALE E LOGGING
    elapsed_time = time.time() - start_time
    
    if logger:
        logger.info(f"Estratti {len(links)} link JSON/ZIP dalla pagina dataset in {elapsed_time:.2f} secondi")
        logger.debug(f"Statistiche: {analyzed_count} link analizzati, {valid_count} considerati validi")
        
    print(f"Completata analisi in {elapsed_time:.2f} secondi")
    print(f"Risultato: {len(links)} link JSON/ZIP identificati su {analyzed_count} analizzati")
    
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
    # Lista predefinita di dataset noti - ESTESA con tutti i dataset conosciuti
    default_known_datasets = [
        # Dataset principali
        "https://dati.anticorruzione.it/opendata/dataset/smartcig-tipo-fattispecie-contrattuale",
        "https://dati.anticorruzione.it/opendata/dataset/anac-dataset",
        "https://dati.anticorruzione.it/opendata/dataset/anac-datamart",
        "https://dati.anticorruzione.it/opendata/dataset/dati-contratti-pubblici",
        "https://dati.anticorruzione.it/opendata/dataset/soggetti-attuatori-pnrr",
        
        # Dataset OCDS (Open Contracting Data Standard) per anni specifici
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-2022",
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-2021",
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-2020",
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordnari-2020",  # Variante con errore di ortografia nel sito ANAC
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-2019",
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-2018",
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-2017",
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-2016",
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-2015",  # Possibili anni extra
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-2014",
        "https://dati.anticorruzione.it/opendata/dataset/ocds-appalti-ordinari-2013",
        
        # Dataset sulle procedure di gara
        "https://dati.anticorruzione.it/opendata/dataset/informazioni-sulle-procedure-di-gara-indette-a-partire-dal-1-gennaio-2019",
        "https://dati.anticorruzione.it/opendata/dataset/informazioni-sulle-singole-procedure-di-affidamento",
        "https://dati.anticorruzione.it/opendata/dataset/procedure-di-affidamento-ex-art-32-l-190-2012",
        
        # Dataset vari
        "https://dati.anticorruzione.it/opendata/dataset/piano-triennale-di-prevenzione-della-corruzione-e-della-trasparenza",
        "https://dati.anticorruzione.it/opendata/dataset/autorita-nazionale-anticorruzione",
        "https://dati.anticorruzione.it/opendata/dataset/vigilanza-collaborativa",
        "https://dati.anticorruzione.it/opendata/dataset/whistleblowing",
        "https://dati.anticorruzione.it/opendata/dataset/albo-delle-stazioni-appaltanti-qualificate",
        "https://dati.anticorruzione.it/opendata/dataset/albo-arbitri-camerali",
        "https://dati.anticorruzione.it/opendata/dataset/elenco-delle-amministrazioni-aggiudicatrici",
        "https://dati.anticorruzione.it/opendata/dataset/legge-1902012-art-1-comma-32",
        
        # Ricerche generiche che potrebbero identificare dataset non specificati sopra
        "https://dati.anticorruzione.it/opendata/dataset?q=gare",
        "https://dati.anticorruzione.it/opendata/dataset?q=appalti",
        "https://dati.anticorruzione.it/opendata/dataset?q=contratti",
        "https://dati.anticorruzione.it/opendata/dataset?q=anac",
        "https://dati.anticorruzione.it/opendata/dataset?q=ocds",
        "https://dati.anticorruzione.it/opendata/dataset?q=json"
    ]
    
    # Carica dataset salvati in precedenza
    cached_datasets = load_datasets_from_cache()
    
    # Unisci i dataset predefiniti con quelli salvati
    known_datasets = list(set(default_known_datasets + cached_datasets))
    
    # Verifica se esistono dataset con varianti nel nome (maiuscole/minuscole, trattini, ecc.)
    normalized_links = {link.lower().replace('-', '').replace('_', ''): link for link in all_dataset_links}
    
    added_count = 0
    for dataset in known_datasets:
        # Confronto diretto
        if dataset not in all_dataset_links:
            # Confronto normalizzato (ignora maiuscole/minuscole e simboli)
            normalized_dataset = dataset.lower().replace('-', '').replace('_', '')
            if normalized_dataset not in normalized_links:
                all_dataset_links.append(dataset)
                added_count += 1
                if logger:
                    logger.info(f"Aggiunto dataset noto: {dataset}")
    
    if logger and added_count > 0:
        logger.info(f"Aggiunti {added_count} dataset noti alla lista di scraping")
    
    return all_dataset_links


def scrape_all_json_links(config, logger=None):
    """
    Funzione principale per lo scraping. Se Playwright non è disponibile,
    restituisce solo link noti salvati in cache o predefiniti.
    """
    # Se Playwright non è disponibile o disabilitato, utilizza solo link noti
    if NO_PLAYWRIGHT:
        if logger:
            logger.info("Modalità senza scraping attiva: utilizzo solo link noti.")
        
        # Carica i dataset noti
        known_datasets = load_datasets_from_cache()
        
        # Lista predefinita di link diretti noti - LISTA ESTESA con tutti i link diretti conosciuti
        default_known_direct_links = [
            # SmartCIG e fattispecie contrattuale
            "https://dati.anticorruzione.it/opendata/download/dataset/smartcig-tipo-fattispecie-contrattuale/filesystem/smartcig-tipo-fattispecie-contrattuale_json.zip",
            
            # Soggetti attuatori PNRR
            "https://dati.anticorruzione.it/opendata/download/dataset/soggetti-attuatori-pnrr/filesystem/soggetti-attuatori-pnrr_json.zip",
            
            # Dati contratti pubblici
            "https://dati.anticorruzione.it/opendata/download/dataset/dati-contratti-pubblici/filesystem/dati-contratti-pubblici_json.zip",
            
            # Dataset e datamart ANAC
            "https://dati.anticorruzione.it/opendata/download/dataset/anac-dataset/filesystem/anac-dataset_json.zip",
            "https://dati.anticorruzione.it/opendata/download/dataset/anac-datamart/filesystem/anac-datamart_json.zip",
            
            # OCDS appalti ordinari (per anno)
            "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2022/filesystem/ocds-appalti-ordinari-2022_json.zip",
            "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2021/filesystem/ocds-appalti-ordinari-2021_json.zip",
            "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2020/filesystem/ocds-appalti-ordinari-2020_json.zip",
            "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2019/filesystem/ocds-appalti-ordinari-2019_json.zip",
            "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2018/filesystem/ocds-appalti-ordinari-2018_json.zip",
            "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2017/filesystem/ocds-appalti-ordinari-2017_json.zip",
            "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2016/filesystem/ocds-appalti-ordinari-2016_json.zip",
            "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2015/filesystem/ocds-appalti-ordinari-2015_json.zip",
            "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2014/filesystem/ocds-appalti-ordinari-2014_json.zip",
            "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordinari-2013/filesystem/ocds-appalti-ordinari-2013_json.zip",
            
            # Variante con errore di ortografia nel sito ANAC
            "https://dati.anticorruzione.it/opendata/download/dataset/ocds-appalti-ordnari-2020/filesystem/ocds-appalti-ordnari-2020_json.zip",
            
            # Informazioni sulle procedure di gara
            "https://dati.anticorruzione.it/opendata/download/dataset/informazioni-sulle-procedure-di-gara-indette-a-partire-dal-1-gennaio-2019/filesystem/informazioni-sulle-procedure-di-gara-indette-a-partire-dal-1-gennaio-2019_json.zip",
            "https://dati.anticorruzione.it/opendata/download/dataset/informazioni-sulle-singole-procedure-di-affidamento/filesystem/informazioni-sulle-singole-procedure-di-affidamento_json.zip",
            
            # Varianti note dei percorsi di download
            "https://dati.anticorruzione.it/opendata/download/dataset/dati-contratti-pubblici/resource/dati-contratti-pubblici_json.zip",
            "https://dati.anticorruzione.it/opendata/download/dataset/anac-dataset/resource/anac-dataset_json.zip",
            "https://dati.anticorruzione.it/opendata/download/dataset/anac-datamart/resource/anac-datamart_json.zip"
        ]
        
        # Carica link noti dalla cache
        cached_direct_links = load_direct_links_from_cache()
        
        # Unisci tutti i link noti e rimuovi duplicati
        all_links = set(default_known_direct_links + cached_direct_links)
        
        if logger:
            logger.info(f"Trovati {len(all_links)} link noti da file cache e predefiniti.")
        
        return all_links
        
    # Altrimenti, procedi con il normale scraping
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