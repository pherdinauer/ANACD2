#!/usr/bin/env python
import os
import sys
import json
import time
from datetime import datetime
import argparse
try:
    # Try importing from json_downloader module
    from json_downloader.scraper import load_config, scrape_all_json_links
    from json_downloader.downloader import download_file, should_download, verify_file_integrity, process_downloaded_file
    from json_downloader.utils import setup_logger, ensure_dir, normalize_url, sanitize_filename, save_links_to_cache, load_links_from_cache
except ImportError:
    # Fallback to direct import if used outside package structure
    from scraper import load_config, scrape_all_json_links
    from downloader import download_file, should_download, verify_file_integrity, process_downloaded_file
    from utils import setup_logger, ensure_dir, normalize_url, sanitize_filename, save_links_to_cache, load_links_from_cache
import traceback

class ANACDownloaderCLI:
    def __init__(self):
        self.config = None
        self.logger = None
        self.json_links = set()
        self.download_dir = None
        self.session_dir = None
        self.links_cache_file = "cache/json_links.txt"
        
    def setup(self):
        """Initialize application settings and create required directories."""
        try:
            # Ensure required directories exist with proper error handling
            for directory in [self.config['download_dir'], os.path.dirname(self.config['log_file']), 'cache']:
                try:
                    os.makedirs(directory, exist_ok=True)
                    # Verifica se la directory è stata effettivamente creata e ha permessi di scrittura
                    if not os.path.exists(directory):
                        print(f"ERRORE: Impossibile creare la directory {directory}")
                        return False
                    # Verifica i permessi di scrittura
                    test_file = os.path.join(directory, '.write_test')
                    try:
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                    except (PermissionError, IOError) as pe:
                        print(f"ERRORE: Non hai permessi di scrittura nella directory {directory}")
                        print(f"Dettagli errore: {str(pe)}")
                        return False
                except Exception as dir_error:
                    print(f"ERRORE nella creazione della directory {directory}: {str(dir_error)}")
                    return False
            
            self.links_cache_file = 'cache/json_links.txt'
            
            # Initialize logger
            self.logger = setup_logger(self.config['log_file'])
            self.logger.info("ANAC JSON Downloader avviato")
            
            # Verifica e imposta correttamente le directory di download
            self.download_dir = os.path.abspath(self.config['download_dir'])
            self.config['download_dir'] = self.download_dir
            self.logger.info(f"Directory di download impostata a: {self.download_dir}")
            
            return True
        except Exception as e:
            print(f"Errore durante l'inizializzazione: {str(e)}")
            traceback.print_exc()
            return False
    
    def print_welcome(self):
        """Print welcome message and initialize the application."""
        print("=" * 60)
        print("     ANAC JSON DOWNLOADER - UTILITY DI DOWNLOAD")
        print("=" * 60)
        print("Questa applicazione scarica file JSON/ZIP dal portale Open Data ANAC")
        
        # Inizializza l'applicazione
        if not self.setup():
            print("Impossibile inizializzare l'applicazione. Uscita.")
            sys.exit(1)
        
        # Carica link dalla cache all'avvio
        try:
            self.json_links = load_links_from_cache(self.links_cache_file)
            if self.json_links:
                print(f"Caricati {len(self.json_links)} link dalla cache.")
        except Exception as e:
            print(f"Attenzione: impossibile caricare i link dalla cache: {str(e)}")
            self.json_links = set()
    
    def print_header(self):
        """Stampa l'intestazione dell'applicazione"""
        print("\n" + "=" * 60)
        print("      ANAC JSON DOWNLOADER - UTILITY DI SCARICAMENTO FILE")
        print("=" * 60)
        print(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        if self.config:
            print(f"URL base: {self.config.get('base_url', 'Non configurato')}")
            print(f"Directory download: {self.download_dir}")
        print("=" * 60 + "\n")
    
    def display_menu(self):
        """Display the main menu and handle user input."""
        while True:
            print("\n" + "=" * 60)
            print("ANAC JSON DOWNLOADER - MENU PRINCIPALE")
            print("=" * 60)
            
            print("\nScegli un'operazione:")
            
            # Mostra opzione di scraping solo se Playwright è disponibile
            if not os.environ.get('NO_PLAYWRIGHT', '0') == '1':
                print("1. Esegui scraping delle pagine web (trova tutti i dataset e file JSON/ZIP)")
                start_choice = 2
            else:
                start_choice = 1
            
            print(f"{start_choice}. Scarica i file JSON/ZIP trovati")
            print(f"{start_choice+1}. Verifica integrità file già scaricati")
            print(f"{start_choice+2}. Visualizza link in cache")
            print(f"{start_choice+3}. Aggiungi link manualmente alla cache")
            print(f"{start_choice+4}. Carica link da file esterno")
            print(f"{start_choice+5}. Deduplicazione avanzata dei link")
            print(f"{start_choice+6}. Gestisci dataset e link diretti noti")
            print(f"{start_choice+7}. Scarica file JSON/ZIP da un URL dataset specifico")
            print(f"{start_choice+8}. Scarica direttamente da un link personalizzato")
            print(f"{start_choice+9}. Estrai tutti i file ZIP in /database")
            print(f"{start_choice+10}. Download con smistamento automatico in /database/JSON")
            print("0. Esci dal programma")
            
            try:
                choice = input("\nInserisci il numero dell'operazione: ").strip()
                
                if choice == '0':
                    print("\nChiusura ANAC JSON Downloader. Grazie per aver utilizzato il programma.")
                    break
                
                # Se l'utente inserisce 1 e Playwright è disabilitato, correggi la scelta
                if choice == '1' and os.environ.get('NO_PLAYWRIGHT', '0') == '1':
                    choice = str(start_choice)
                
                self.handle_menu_choice(choice, start_choice)
            
            except KeyboardInterrupt:
                print("\n\nOperazione interrotta dall'utente.")
                break
            except Exception as e:
                self.logger.error(f"Errore durante l'esecuzione: {str(e)}")
                print(f"\nErrore: {str(e)}")
                continue

    def handle_menu_choice(self, choice, start_choice):
        """Handle the user menu choice."""
        try:
            if os.environ.get('NO_PLAYWRIGHT', '0') == '1':
                # Se Playwright è disabilitato, adatta le scelte
                if choice == '1':
                    self.download_json_files()
                elif choice == '2':
                    self.verify_downloaded_files()
                elif choice == '3':
                    self.display_cached_links()
                elif choice == '4':
                    self.add_link_manually()
                elif choice == '5':
                    self.load_links_from_file()
                elif choice == '6':
                    self.deduplicate_links()
                elif choice == '7':
                    self.manage_known_datasets()
                elif choice == '8':
                    self.download_from_specific_dataset()
                elif choice == '9':
                    self.download_from_custom_link()
                elif choice == '10':
                    self.extract_all_zips_to_database()
                elif choice == '11':
                    self.download_with_auto_sorting()
                else:
                    print("Scelta non valida. Riprova.")
            else:
                # Opzioni complete con Playwright
                if choice == '1':
                    self.run_scraper()
                elif choice == '2':
                    self.download_json_files()
                elif choice == '3':
                    self.verify_downloaded_files()
                elif choice == '4':
                    self.display_cached_links()
                elif choice == '5':
                    self.add_link_manually()
                elif choice == '6':
                    self.load_links_from_file()
                elif choice == '7':
                    self.deduplicate_links()
                elif choice == '8':
                    self.manage_known_datasets()
                elif choice == '9':
                    self.download_from_specific_dataset()
                elif choice == '10':
                    self.download_from_custom_link()
                elif choice == '11':
                    self.extract_all_zips_to_database()
                elif choice == '12':
                    self.download_with_auto_sorting()
                else:
                    print("Scelta non valida. Riprova.")
                    
            # Pausa dopo l'operazione
            input("\nPremi INVIO per continuare...")
        except Exception as e:
            self.logger.error(f"Errore nell'esecuzione dell'operazione {choice}: {str(e)}")
            traceback.print_exc()
            print(f"\nErrore: {str(e)}")
            input("\nPremi INVIO per continuare...")
    
    def run_scraper(self):
        """Run the web scraper to find JSON/ZIP files."""
        print("\n" + "=" * 60)
        print("SCRAPING DELLE PAGINE WEB")
        print("=" * 60)
        
        try:
            # Check if Playwright is available
            if os.environ.get('NO_PLAYWRIGHT', '0') == '1':
                print("Modalità senza scraping attiva. Questa funzione richiede Playwright.")
                return
            
            print("Avvio dello scraping delle pagine ANAC...")
            
            # Opzioni di scraping
            use_thorough = input("Vuoi eseguire una ricerca approfondita? Ci vorrà più tempo ma troverà più dataset (s/n): ").strip().lower() == 's'
            if use_thorough:
                print("Modalità ricerca approfondita attivata.")
                os.environ['ANAC_THOROUGH_SEARCH'] = '1'
            else:
                print("Modalità ricerca standard attivata.")
                if 'ANAC_THOROUGH_SEARCH' in os.environ:
                    del os.environ['ANAC_THOROUGH_SEARCH']
            
            # Impostazione timeout
            try:
                timeout = input("Specificare timeout per operazioni di navigazione (in secondi, default: 30): ").strip()
                if timeout:
                    self.config['timeout'] = int(timeout)
                    print(f"Timeout impostato a {self.config['timeout']} secondi.")
            except ValueError:
                print("Valore non valido, uso il timeout predefinito.")
            
            print("\nAvvio scraping in corso...")
            
            # Import and run the scraper
            from json_downloader.scraper import scrape_all_json_links
            
            # Aggiunta feedback
            print("Ricerca dataset principali...")
            new_links = scrape_all_json_links(self.config, self.logger)
            
            # Merge with existing links
            old_count = len(self.json_links)
            self.json_links.update(new_links)
            new_count = len(self.json_links) - old_count
            
            print(f"\nTrovati {len(new_links)} link totali.")
            print(f"Di cui {new_count} nuovi link aggiunti alla cache.")
            
            # Save to cache
            save_links_to_cache(self.json_links, self.links_cache_file)
            print(f"Link salvati nella cache: {self.links_cache_file}")
            
            # Mostra alcuni esempi di link trovati
            if new_links:
                print("\nEsempi di link trovati:")
                for i, link in enumerate(list(new_links)[:5], 1):
                    print(f"{i}. {link}")
                if len(new_links) > 5:
                    print(f"... e altri {len(new_links)-5} link.")
            
        except Exception as e:
            print(f"Errore durante lo scraping: {str(e)}")
            traceback.print_exc()
    
    def download_json_files(self):
        """Download JSON/ZIP files from the cached links."""
        print("\n" + "=" * 60)
        print("DOWNLOAD FILE JSON/ZIP")
        print("=" * 60)
        
        if not self.json_links:
            print("Nessun link in cache. Esegui prima lo scraping per trovare file da scaricare.")
            return
        
        print(f"Sono disponibili {len(self.json_links)} link per il download.")
        
        # Chiedi se organizzare in cartelle per dataset
        organize_by_dataset = input("\nVuoi organizzare i file in cartelle per dataset? (s/n): ").strip().lower() == 's'
        
        # Chiedi se estrarre gli archivi zip
        extract_zip = input("Vuoi estrarre automaticamente i file ZIP? (s/n): ").strip().lower() == 's'
        
        # Chiedi se filtrare solo i file JSON
        filter_json_only = input("Vuoi scaricare solo file JSON e ZIP contenenti JSON? (s/n): ").strip().lower() == 's'
        
        if filter_json_only:
            filtered_links = []
            for link in self.json_links:
                link_lower = link.lower()
                # Mantieni i link che terminano con .json o _json o .json.zip o contengono /json/ nel percorso
                # Esclude esplicitamente i file CSV, TTL e altri formati
                if (link_lower.endswith('.json') or 
                    link_lower.endswith('_json.zip') or 
                    '/json/' in link_lower or 
                    'format=json' in link_lower):
                    filtered_links.append(link)
                # Esclude esplicitamente link che sembrano CSV o TTL o XML
                elif any(ext in link_lower for ext in ['_csv.', '.csv.', '_ttl.', '.ttl.', '_xml.', '.xml.']):
                    continue
                # Per ZIP generici, li include solo se non contengono indicazioni CSV/TTL/XML
                elif link_lower.endswith('.zip') and not any(ext in link_lower for ext in ['_csv', '.csv', '_ttl', '.ttl', '_xml', '.xml']):
                    filtered_links.append(link)
            
            original_count = len(self.json_links)
            self.json_links = filtered_links
            print(f"\nFiltrati {original_count - len(self.json_links)} link non-JSON. Rimasti {len(self.json_links)} link JSON/ZIP.")
        
        # Ask how many files to download
        max_files_input = input("\nQuanti file vuoi scaricare? (0 per tutti, invio = tutti): ").strip()
        try:
            max_files = 0 if not max_files_input else int(max_files_input)
        except ValueError:
            print("Input non valido. Verranno scaricati tutti i file.")
            max_files = 0
        
        if max_files == 0:
            links_to_download = list(self.json_links)
        else:
            links_to_download = list(self.json_links)[:max_files]
        
        print(f"\nVerranno scaricati {len(links_to_download)} file.")
        
        # Ask for confirmation
        confirm = input("Vuoi procedere? (s/n): ").strip().lower()
        if confirm != 's':
            print("Download annullato.")
            return
        
        # Download files
        print("\nDownload in corso...")
        print("DEBUG: Inizializzazione processo di download...")
        
        from json_downloader.downloader import download_file
        from urllib.parse import urlparse
        import platform
        
        # Log del sistema operativo per debug
        system_info = platform.system()
        print(f"DEBUG: Sistema operativo rilevato: {system_info}")
        print(f"DEBUG: Percorso download: {self.config['download_dir']}")
        print(f"DEBUG: Verifica permessi cartella download...")
        
        # Verifica permessi cartella download
        try:
            test_file = os.path.join(self.config['download_dir'], '.test_permissions')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print("DEBUG: Permessi cartella download OK")
        except Exception as perm_error:
            print(f"DEBUG: ERRORE Permessi cartella download: {str(perm_error)}")
            print("DEBUG: Tentativo di utilizzare directory alternative...")
        
        # Controlla il sistema operativo per gestire correttamente i percorsi
        is_windows = platform.system() == 'Windows'
        
        downloaded_files = []
        files_by_dataset = {}  # Per tenere traccia di quali file sono in quali dataset
        
        # Log prima di iniziare il ciclo di download
        print(f"DEBUG: Preparazione download di {len(links_to_download)} file...")
        
        for i, link in enumerate(links_to_download, 1):
            try:
                print(f"DEBUG: Elaborazione link {i}/{len(links_to_download)}: {link}")
                
                # Get filename from URL
                file_name = os.path.basename(link.split('?')[0])
                if not file_name:
                    file_name = f"download_{i}.dat"
                    print(f"DEBUG: Nome file non trovato nell'URL, generato automaticamente: {file_name}")
                else:
                    print(f"DEBUG: Nome file estratto dall'URL: {file_name}")
                
                # Rimuovi caratteri non validi dal nome file
                original_name = file_name
                file_name = sanitize_filename(file_name)
                if file_name != original_name:
                    print(f"DEBUG: Nome file sanitizzato da '{original_name}' a '{file_name}'")
                
                # Determina il dataset dal link
                dataset_name = "altri_file"  # Default folder
                
                if organize_by_dataset:
                    # Prova a estrarre il nome del dataset dall'URL
                    parsed_url = urlparse(link)
                    path_parts = parsed_url.path.strip('/').split('/')
                    
                    print(f"DEBUG: Analisi percorso URL per dataset: {parsed_url.path}")
                    
                    # Cerca la parte 'dataset' nell'URL
                    if 'dataset' in path_parts:
                        dataset_idx = path_parts.index('dataset')
                        if dataset_idx + 1 < len(path_parts):
                            dataset_name = path_parts[dataset_idx + 1]
                            print(f"DEBUG: Dataset trovato nell'URL: {dataset_name}")
                    
                    # Se non riusciamo a estrarre il dataset dall'URL, usiamo il dominio
                    if dataset_name == "altri_file" and parsed_url.netloc:
                        dataset_name = parsed_url.netloc.replace('.', '_')
                        print(f"DEBUG: Dataset non trovato, uso dominio: {dataset_name}")
                
                # Assicurati che il nome cartella sia valido
                original_dataset_name = dataset_name
                dataset_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in dataset_name)
                if dataset_name != original_dataset_name:
                    print(f"DEBUG: Nome dataset sanitizzato da '{original_dataset_name}' a '{dataset_name}'")
                
                # Full path with dataset subfolder
                try:
                    dataset_folder = os.path.join(self.config['download_dir'], dataset_name)
                    print(f"DEBUG: Tentativo creazione cartella dataset: {dataset_folder}")
                    
                    try:
                        os.makedirs(dataset_folder, exist_ok=True)
                        # Verifica immediata dei permessi
                        test_file = os.path.join(dataset_folder, '.write_test')
                        with open(test_file, 'w') as f:
                            f.write('test')
                        os.remove(test_file)
                        print(f"DEBUG: Cartella dataset creata con successo: {dataset_folder}")
                        print(f"Cartella creata/verificata: {dataset_folder} (permessi OK)")
                    except PermissionError as pe:
                        print(f"DEBUG: ERRORE PERMESSI: {str(pe)}")
                        print(f"Errore di permessi nella cartella {dataset_folder}: {str(pe)}")
                        print("Tentativo di utilizzo della cartella principale...")
                        dataset_folder = self.config['download_dir']
                        # Verifica anche la cartella principale
                        test_file = os.path.join(dataset_folder, '.write_test')
                        try:
                            with open(test_file, 'w') as f:
                                f.write('test')
                            os.remove(test_file)
                            print(f"DEBUG: Cartella principale utilizzabile: {dataset_folder}")
                        except Exception as mpe:
                            # Se fallisce anche qui, usa la directory corrente
                            print(f"DEBUG: ERRORE PERMESSI anche cartella principale: {str(mpe)}")
                            print("Errore di permessi anche nella cartella principale.")
                            dataset_folder = os.path.abspath('.')
                            print(f"DEBUG: Uso directory corrente: {dataset_folder}")
                except Exception as folder_error:
                    print(f"DEBUG: ERRORE CREAZIONE CARTELLA: {str(folder_error)}")
                    print(f"Errore nella creazione della cartella {dataset_folder}: {str(folder_error)}")
                    print("Utilizzo cartella principale per i downloads...")
                    dataset_folder = self.config['download_dir']
                    
                # Verifica se la cartella esiste effettivamente dopo la creazione
                if not os.path.exists(dataset_folder):
                    print(f"DEBUG: Impossibile verificare esistenza cartella: {dataset_folder}")
                    print(f"Impossibile verificare la cartella {dataset_folder}. Utilizzo percorso alternativo.")
                    # Prova la directory di lavoro corrente come ultima risorsa
                    dataset_folder = os.path.abspath('.')
                    print(f"DEBUG: Fallback a directory corrente: {dataset_folder}")
                    print(f"Usando directory corrente: {dataset_folder}")
                
                # Combina percorso cartella e nome file
                file_path = os.path.join(dataset_folder, file_name)
                print(f"DEBUG: Percorso file completo: {file_path}")
                
                # Aggiorna il dizionario dei file per dataset
                if dataset_name not in files_by_dataset:
                    files_by_dataset[dataset_name] = []
                
                print(f"\n[{i}/{len(links_to_download)}] Scaricamento di {file_name}...")
                print(f"Cartella di destinazione: {dataset_folder}")
                
                # Estrai solo i parametri necessari dalla configurazione
                max_retries = 3  # Valore predefinito
                if isinstance(self.config, dict) and 'max_retries' in self.config:
                    max_retries = self.config['max_retries']
                    print(f"DEBUG: Utilizzando max_retries={max_retries} dalla configurazione")
                else:
                    print(f"DEBUG: Utilizzando max_retries={max_retries} predefinito")
                
                # Verifica se il file esiste già
                if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                    print(f"DEBUG: File già esistente: {file_path} ({os.path.getsize(file_path)} bytes)")
                    # Non chiediamo più conferma, saltiamo automaticamente
                    print(f"File {file_name} già esiste. Download saltato automaticamente.")
                    continue
                
                print(f"DEBUG: Avvio download di {link} in {file_path}")
                file_hash = download_file(
                    link, 
                    file_path, 
                    logger=self.logger, 
                    max_retries=max_retries
                )
                
                print(f"DEBUG: Risultato download: hash={file_hash}")
                
                if file_hash:
                    downloaded_files.append(file_path)
                    files_by_dataset[dataset_name].append(file_path)
                    print(f"Download completato: {file_path}")
                    print(f"SHA256: {file_hash}")
                    
                    # If it's a ZIP file, extract JSON files
                    if file_path.lower().endswith('.zip') and extract_zip:
                        print("Estrazione dei file JSON dall'archivio ZIP...")
                        extract_dir = file_path[:-4]  # Remove .zip
                        try:
                            os.makedirs(extract_dir, exist_ok=True)
                            print(f"Cartella di estrazione creata: {extract_dir}")
                            
                            from json_downloader.utils import extract_zip_files
                            extracted = extract_zip_files(file_path, extract_dir, self.logger)
                            
                            if extracted:
                                print(f"Estratti {len(extracted)} file da {file_name}")
                                files_by_dataset[dataset_name].extend(extracted)
                                for ext_file in extracted:
                                    print(f" - {os.path.basename(ext_file)}")
                                downloaded_files.extend(extracted)
                            else:
                                print("Nessun file JSON trovato nell'archivio ZIP.")
                        except Exception as extract_error:
                            print(f"Errore durante l'estrazione: {str(extract_error)}")
                            print("L'estrazione verrà saltata.")
                    elif file_path.lower().endswith('.zip') and not extract_zip:
                        print("File ZIP scaricato ma non estratto (come richiesto).")
                else:
                    print(f"Errore durante il download di {link}")
            except Exception as e:
                print(f"Errore durante il download: {str(e)}")
                traceback.print_exc()
                continue
        
        # Mostra il riepilogo organizzato per dataset
        print("\nScaricamento completato.")
        print(f"File scaricati con successo: {len(downloaded_files)}")
        
        if organize_by_dataset and files_by_dataset:
            print("\nFiles organizzati per dataset:")
            for dataset, files in files_by_dataset.items():
                if files:
                    print(f"\n- Dataset: {dataset}")
                    print(f"  Cartella: {os.path.join(self.config['download_dir'], dataset)}")
                    print(f"  File scaricati: {len(files)}")
        
        print("\nScaricamento completato.")
    
    def verify_downloaded_files(self):
        """Verify integrity of downloaded files."""
        print("\n" + "=" * 60)
        print("VERIFICA INTEGRITÀ FILE")
        print("=" * 60)
        
        download_dir = self.config['download_dir']
        
        if not os.path.exists(download_dir):
            print(f"Directory {download_dir} non trovata.")
            return
        
        # Get all files in download directory
        all_files = []
        for root, _, files in os.walk(download_dir):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
        
        if not all_files:
            print(f"Nessun file trovato nella directory {download_dir}.")
            return
        
        print(f"Trovati {len(all_files)} file totali.")
        print("Verifica dell'integrità in corso...")
        
        valid_files = 0
        damaged_files = 0
        
        from json_downloader.downloader import verify_file_integrity
        
        for i, file_path in enumerate(all_files, 1):
            try:
                print(f"[{i}/{len(all_files)}] Verifica di {os.path.basename(file_path)}...", end="")
                is_valid = verify_file_integrity(file_path)
                
                if is_valid:
                    print(" ✅ File integro.")
                    valid_files += 1
                else:
                    print(" ❌ File corrotto o incompleto.")
                    damaged_files += 1
            except Exception as e:
                print(f" ❌ Errore: {str(e)}")
                damaged_files += 1
        
        print("\nVerifica completata.")
        print(f"File integri: {valid_files}")
        print(f"File corrotti: {damaged_files}")
    
    def display_cached_links(self):
        """Display all links in the cache."""
        print("\n" + "=" * 60)
        print("VISUALIZZAZIONE LINK IN CACHE")
        print("=" * 60)
        
        if not self.json_links:
            print("Nessun link in cache.")
            return
        
        print(f"Trovati {len(self.json_links)} link in cache:")
        for i, link in enumerate(self.json_links, 1):
            print(f"{i}. {link}")
    
    def add_link_manually(self):
        """Add a link manually to the cache."""
        print("\n" + "=" * 60)
        print("AGGIUNGI LINK MANUALMENTE")
        print("=" * 60)
        
        print("Inserisci uno o più link da aggiungere alla cache.")
        print("Per terminare, lascia la riga vuota.")
        
        count = 0
        while True:
            link = input("\nLink JSON/ZIP: ").strip()
            if not link:
                break
            
            # Validate link
            if not link.startswith(('http://', 'https://')):
                print("Il link deve iniziare con http:// o https://. Riprova.")
                continue
            
            if link in self.json_links:
                print("Questo link è già presente nella cache.")
            else:
                self.json_links.add(link)
                count += 1
                print(f"Link aggiunto. Totale link in cache: {len(self.json_links)}")
        
        if count > 0:
            # Save to cache
            save_links_to_cache(self.json_links, self.links_cache_file)
            print(f"\nAggiunti {count} nuovi link alla cache.")
        else:
            print("\nNessun nuovo link aggiunto.")
    
    def load_links_from_file(self):
        """Load links from an external file."""
        print("\n" + "=" * 60)
        print("CARICA LINK DA FILE ESTERNO")
        print("=" * 60)
        
        file_path = input("Inserisci il percorso del file di testo contenente i link (un link per riga): ").strip()
        
        if not file_path:
            print("Percorso non valido. Operazione annullata.")
            return
        
        if not os.path.exists(file_path):
            print(f"File {file_path} non trovato.")
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                links = [line.strip() for line in f if line.strip()]
            
            if not links:
                print("Nessun link trovato nel file.")
                return
            
            # Validate and add links
            valid_links = 0
            for link in links:
                if link.startswith(('http://', 'https://')):
                    if link not in self.json_links:
                        self.json_links.add(link)
                        valid_links += 1
            
            if valid_links > 0:
                # Save to cache
                save_links_to_cache(self.json_links, self.links_cache_file)
                print(f"\nAggiunti {valid_links} nuovi link alla cache.")
            else:
                print("\nNessun nuovo link valido trovato nel file.")
            
        except Exception as e:
            print(f"Errore durante la lettura del file: {str(e)}")
    
    def deduplicate_links(self):
        """Remove duplicate links from the cache."""
        print("\n" + "=" * 60)
        print("DEDUPLICAZIONE AVANZATA DEI LINK")
        print("=" * 60)
        
        if not self.json_links:
            print("Nessun link in cache da deduplicare.")
            return
        
        print(f"Link in cache prima della deduplicazione: {len(self.json_links)}")
        print("Ricerca di link duplicati in corso...")
        
        from json_downloader.utils import deduplicate_links
        
        deduped_links, report = deduplicate_links(self.json_links, self.logger)
        
        if report["duplicates_found"] > 0:
            self.json_links = deduped_links
            save_links_to_cache(self.json_links, self.links_cache_file)
            
            print("\nRisultati della deduplicazione:")
            print(f"- Link duplicati trovati: {report['duplicates_found']}")
            print(f"- Link rimossi: {report['links_removed']}")
            print(f"- Link in cache dopo la deduplicazione: {report['after']}")
        else:
            print("\nNessun link duplicato trovato.")
    
    def manage_known_datasets(self):
        """Manage known datasets and direct links."""
        print("\n" + "=" * 60)
        print("GESTIONE DATASET E LINK DIRETTI NOTI")
        print("=" * 60)
        
        from json_downloader.utils import load_datasets_from_cache, save_datasets_to_cache
        from json_downloader.utils import load_direct_links_from_cache, save_direct_links_to_cache
        
        # Load known datasets and direct links
        datasets = load_datasets_from_cache()
        direct_links = load_direct_links_from_cache()
        
        while True:
            print("\nScegli un'operazione:")
            print("1. Visualizza dataset noti")
            print("2. Visualizza link diretti noti")
            print("3. Aggiungi dataset manualmente")
            print("4. Aggiungi link diretto manualmente")
            print("5. Rimuovi dataset")
            print("6. Rimuovi link diretto")
            print("0. Torna al menu principale")
            
            choice = input("\nInserisci il numero dell'operazione: ").strip()
            
            if choice == '0':
                break
            elif choice == '1':
                print(f"\nTrovati {len(datasets)} dataset noti:")
                for i, dataset in enumerate(datasets, 1):
                    print(f"{i}. {dataset}")
            elif choice == '2':
                print(f"\nTrovati {len(direct_links)} link diretti noti:")
                for i, link in enumerate(direct_links, 1):
                    print(f"{i}. {link}")
            elif choice == '3':
                dataset = input("\nInserisci l'URL del dataset: ").strip()
                if dataset and dataset.startswith(('http://', 'https://')):
                    if dataset not in datasets:
                        datasets.append(dataset)
                        save_datasets_to_cache(datasets)
                        print("Dataset aggiunto con successo.")
                    else:
                        print("Questo dataset è già presente.")
                else:
                    print("URL non valido.")
            elif choice == '4':
                link = input("\nInserisci il link diretto: ").strip()
                if link and link.startswith(('http://', 'https://')):
                    if link not in direct_links:
                        direct_links.append(link)
                        save_direct_links_to_cache(direct_links)
                        print("Link diretto aggiunto con successo.")
                    else:
                        print("Questo link è già presente.")
                else:
                    print("URL non valido.")
            elif choice == '5':
                if not datasets:
                    print("Nessun dataset da rimuovere.")
                else:
                    index = input("\nInserisci il numero del dataset da rimuovere: ").strip()
                    try:
                        idx = int(index) - 1
                        if 0 <= idx < len(datasets):
                            removed = datasets.pop(idx)
                            save_datasets_to_cache(datasets)
                            print(f"Dataset rimosso: {removed}")
                        else:
                            print("Numero non valido.")
                    except ValueError:
                        print("Numero non valido.")
            elif choice == '6':
                if not direct_links:
                    print("Nessun link diretto da rimuovere.")
                else:
                    index = input("\nInserisci il numero del link diretto da rimuovere: ").strip()
                    try:
                        idx = int(index) - 1
                        if 0 <= idx < len(direct_links):
                            removed = direct_links.pop(idx)
                            save_direct_links_to_cache(direct_links)
                            print(f"Link diretto rimosso: {removed}")
                        else:
                            print("Numero non valido.")
                    except ValueError:
                        print("Numero non valido.")
            else:
                print("Scelta non valida. Riprova.")
    
    def download_from_specific_dataset(self, dataset_url=None):
        """Scarica file JSON/ZIP da un URL di dataset specifico."""
        print("\n" + "=" * 60)
        print("SCARICA JSON/ZIP DA URL DATASET SPECIFICO")
        print("=" * 60)
        print("\nQuesta funzione permette di inserire l'URL di un dataset ANAC")
        print("e scaricare tutti i file JSON/ZIP trovati in una cartella dedicata.")
        
        # Usa l'URL passato come parametro, se disponibile
        if not dataset_url:
            # Chiedi l'URL del dataset
            dataset_url = input("\nInserisci l'URL completo del dataset ANAC: ").strip()
        else:
            print(f"\nUtilizzo URL fornito: {dataset_url}")
        
        if not dataset_url:
            print("URL non valido. Operazione annullata.")
            return
        
        # Chiedi se estrarre automaticamente i file ZIP
        extract_zip = input("\nVuoi estrarre automaticamente i file ZIP scaricati? (s/n): ").strip().lower() == 's'
        if extract_zip:
            print("I file ZIP verranno estratti automaticamente.")
        else:
            print("I file ZIP NON verranno estratti.")
        
        # Normalizza l'URL se necessario
        if not dataset_url.startswith(('http://', 'https://')):
            dataset_url = f"https://dati.anticorruzione.it/opendata/dataset/{dataset_url}"
            print(f"URL normalizzato a: {dataset_url}")
        
        # Estrai il nome del dataset dall'URL per creare una cartella dedicata
        dataset_name = dataset_url.split('/')[-1].split('?')[0]
        if not dataset_name:
            dataset_name = f"dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Crea una cartella specifica per questo dataset
        dataset_folder = os.path.join(self.config['download_dir'], dataset_name)
        os.makedirs(dataset_folder, exist_ok=True)
        print(f"\nCreata cartella dedicata: {dataset_folder}")
        
        # Utilizza lo scraper per trovare i link JSON/ZIP in questo dataset
        print("\nRicerca dei file JSON/ZIP nel dataset...")
        try:
            json_links = set()
            
            # Se è disponibile il browser, utilizza Playwright per lo scraping
            if not os.environ.get('NO_PLAYWRIGHT', '0') == '1':
                # Salva temporaneamente lo stato di NO_PLAYWRIGHT
                original_no_playwright = os.environ.get('NO_PLAYWRIGHT')
                # Forza l'attivazione di Playwright per questa operazione
                if 'NO_PLAYWRIGHT' in os.environ:
                    del os.environ['NO_PLAYWRIGHT']
                
                from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
                
                # Esegui lo scraping con Playwright
                print("\nAvvio browser per lo scraping...")
                with sync_playwright() as p:
                    browser_options = {
                        'headless': not self.config.get('debug_mode', False)
                    }
                    
                    print("Inizializzazione browser Chrome...")
                    browser = p.chromium.launch(**browser_options)
                    
                    try:
                        print("Creazione nuovo contesto...")
                        context = browser.new_context(
                            viewport={'width': 1280, 'height': 800},
                            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
                        )
                        page = context.new_page()
                        
                        # Imposta un timeout più breve ma ragionevole
                        navigation_timeout = min(self.config.get('timeout', 30), 60) * 1000  # Massimo 60 secondi
                        
                        print(f"Navigazione a {dataset_url}... (timeout: {navigation_timeout/1000}s)")
                        try:
                            response = page.goto(dataset_url, timeout=navigation_timeout, wait_until="domcontentloaded")
                        except TimeoutError:
                            print("Timeout durante il caricamento iniziale. Provo a continuare comunque...")
                            response = None
                        
                        if not response or (response and response.status >= 400):
                            status_code = response.status if response else "N/A"
                            print(f"Errore: Impossibile accedere all'URL (status: {status_code})")
                            if original_no_playwright:
                                os.environ['NO_PLAYWRIGHT'] = original_no_playwright
                            
                            # Anche se non riusciamo ad accedere all'URL, potrebbe comunque essere un link diretto a un file
                            if dataset_url.lower().endswith(('.json', '.zip')):
                                print("L'URL sembra essere un link diretto a un file JSON/ZIP.")
                                json_links.add(dataset_url)
                            else:
                                # Chiedi se aggiungere manualmente
                                add_manual = input("\nVuoi aggiungere manualmente un link di download? (s/n): ").strip().lower()
                                if add_manual == 's':
                                    manual_link = input("Inserisci il link completo del file JSON/ZIP: ").strip()
                                    if manual_link and manual_link.startswith(('http://', 'https://')):
                                        json_links.add(manual_link)
                                        print(f"Aggiunto link manuale: {manual_link}")
                            
                            if not json_links:
                                return
                        else:
                            # Attendi caricamento dinamico con un timeout ragionevole
                            print("Pagina caricata. Attendo il caricamento completo...")
                            try:
                                page.wait_for_load_state("networkidle", timeout=navigation_timeout)
                                print("Caricamento completato.")
                            except PlaywrightTimeout:
                                print("Timeout durante l'attesa del caricamento completo. Continuo comunque...")
                            
                            # Scorri pagina per attivare lazy loading
                            print("Scorrimento pagina per attivare lazy loading...")
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            page.wait_for_timeout(2000)  # Attendi 2 secondi per il caricamento
                            
                            print("Estrazione contenuto della pagina...")
                            content = page.content()
                            
                            # Estrai link ai file JSON/ZIP
                            print("Ricerca link ai file JSON/ZIP...")
                            from json_downloader.scraper import extract_json_links_from_dataset_page
                            json_links = extract_json_links_from_dataset_page(content, self.config['base_url'], self.logger, self.config)
                            print(f"Trovati {len(json_links)} link nella pagina.")
                            
                            # Se l'URL stesso è un link diretto a un file JSON/ZIP, aggiungiamolo
                            if dataset_url.lower().endswith(('.json', '.zip')):
                                json_links.add(dataset_url)
                        
                    except PlaywrightTimeout as e:
                        print(f"Timeout durante lo scraping: {str(e)}")
                        print("Provo a continuare con ciò che è stato caricato...")
                        try:
                            content = page.content()
                            from json_downloader.scraper import extract_json_links_from_dataset_page
                            json_links = extract_json_links_from_dataset_page(content, self.config['base_url'], self.logger, self.config)
                            print(f"Trovati {len(json_links)} link nella pagina parziale.")
                        except Exception as inner_e:
                            print(f"Impossibile estrarre contenuto: {str(inner_e)}")
                    except Exception as e:
                        print(f"Errore durante lo scraping: {str(e)}")
                        traceback.print_exc()
                        
                        # Anche in caso di errore, verifichiamo se l'URL è un download diretto
                        if dataset_url.lower().endswith(('.json', '.zip')):
                            print("L'URL sembra essere un link diretto a un file JSON/ZIP.")
                            json_links.add(dataset_url)
                    finally:
                        print("Chiusura browser...")
                        browser.close()
                        # Ripristina lo stato originale di NO_PLAYWRIGHT
                        if original_no_playwright:
                            os.environ['NO_PLAYWRIGHT'] = original_no_playwright
            else:
                # Se Playwright non è disponibile, prova a trovare link noti per questo dataset
                print("Modalità senza browser - ricerca di link noti per questo dataset...")
                from json_downloader.scraper import load_direct_links_from_cache
                
                all_links = load_direct_links_from_cache()
                json_links = set([link for link in all_links if dataset_name in link.lower()])
                
                # Aggiungi link predefiniti se il dataset è conosciuto
                known_patterns = {
                    'smartcig-tipo-fattispecie-contrattuale': '/download/dataset/smartcig-tipo-fattispecie-contrattuale/filesystem/smartcig-tipo-fattispecie-contrattuale_json.zip',
                    'anac-dataset': '/download/dataset/anac-dataset/filesystem/anac-dataset_json.zip',
                    'anac-datamart': '/download/dataset/anac-datamart/filesystem/anac-datamart_json.zip',
                    'dati-contratti-pubblici': '/download/dataset/dati-contratti-pubblici/filesystem/dati-contratti-pubblici_json.zip',
                    'soggetti-attuatori-pnrr': '/download/dataset/soggetti-attuatori-pnrr/filesystem/soggetti-attuatori-pnrr_json.zip'
                }
                
                # Verifica se il nome del dataset corrisponde a uno dei pattern conosciuti
                for pattern, path in known_patterns.items():
                    if pattern in dataset_name:
                        full_url = f"https://dati.anticorruzione.it/opendata{path}"
                        if full_url not in json_links:
                            json_links.add(full_url)
                            print(f"Aggiunto link predefinito: {full_url}")
                
                # Se l'URL sembra essere un link diretto, aggiungiamolo
                if dataset_url.lower().endswith(('.json', '.zip')):
                    json_links.add(dataset_url)
                    print(f"L'URL sembra essere un link diretto a un file JSON/ZIP.")
            
            # Nessun link trovato
            if not json_links:
                print("\nNessun file JSON/ZIP trovato in questo dataset.")
                
                # Chiedi se aggiungere manualmente
                add_manual = input("\nVuoi aggiungere manualmente un link di download? (s/n): ").strip().lower()
                if add_manual == 's':
                    manual_link = input("Inserisci il link completo del file JSON/ZIP: ").strip()
                    if manual_link and manual_link.startswith(('http://', 'https://')):
                        json_links.add(manual_link)
                        print(f"Aggiunto link manuale: {manual_link}")
            
            # Mostra i link trovati
            print(f"\nTrovati {len(json_links)} file da scaricare:")
            for i, link in enumerate(json_links, 1):
                print(f"{i}. {link}")
            
            # Chiedi se filtrare solo i file JSON
            filter_json_only = input("\nVuoi scaricare solo file JSON e ZIP contenenti JSON? (s/n): ").strip().lower() == 's'
            
            if filter_json_only:
                filtered_links = set()
                for link in json_links:
                    link_lower = link.lower()
                    # Mantieni i link che terminano con .json o _json o .json.zip o contengono /json/ nel percorso
                    # Esclude esplicitamente i file CSV, TTL e altri formati
                    if (link_lower.endswith('.json') or 
                        link_lower.endswith('_json.zip') or 
                        '/json/' in link_lower or 
                        'format=json' in link_lower):
                        filtered_links.add(link)
                    # Esclude esplicitamente link che sembrano CSV o TTL o XML
                    elif any(ext in link_lower for ext in ['_csv.', '.csv.', '_ttl.', '.ttl.', '_xml.', '.xml.']):
                        continue
                    # Per ZIP generici, li include solo se non contengono indicazioni CSV/TTL/XML
                    elif link_lower.endswith('.zip') and not any(ext in link_lower for ext in ['_csv', '.csv', '_ttl', '.ttl', '_xml', '.xml']):
                        filtered_links.add(link)
                
                original_count = len(json_links)
                json_links = filtered_links
                print(f"\nFiltrati {original_count - len(json_links)} link non-JSON. Rimasti {len(json_links)} link JSON/ZIP.")
                
                # Mostra i link filtrati
                if json_links:
                    print("\nFile da scaricare (dopo filtro):")
                    for i, link in enumerate(json_links, 1):
                        print(f"{i}. {link}")
            
            # Chiedi conferma prima di scaricare
            if json_links:
                confirm = input("\nVuoi scaricare questi file? (s/n): ").strip().lower()
                if confirm != 's':
                    print("Download annullato.")
                    return
                
                # Scarica i file
                print("\nDownload dei file in corso...")
                
                downloaded_files = []
                for link in json_links:
                    # Ottieni il nome del file dal link
                    file_name = os.path.basename(link.split('?')[0])
                    if not file_name:
                        file_name = f"download_{len(downloaded_files) + 1}.dat"
                    
                    # Percorso completo del file
                    file_path = os.path.join(dataset_folder, file_name)
                    
                    # Verifica se il file esiste già
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        print(f"File {file_name} già esiste. Download saltato automaticamente.")
                        continue
                    
                    # Scarica il file
                    print(f"\nScaricamento di {file_name}...")
                    try:
                        from json_downloader.downloader import download_file
                        
                        # Estrai solo i parametri necessari dalla configurazione
                        max_retries = 3  # Valore predefinito
                        if isinstance(self.config, dict) and 'max_retries' in self.config:
                            max_retries = self.config['max_retries']
                            
                        file_hash = download_file(
                            link, 
                            file_path, 
                            logger=self.logger, 
                            max_retries=max_retries
                        )
                        
                        # Se l'hash è None, il download è fallito
                        if file_hash:
                            downloaded_files.append(file_path)
                            print(f"Download completato: {file_path}")
                            print(f"SHA256: {file_hash}")
                            
                            # Se è un file ZIP ed è stata richiesta l'estrazione automatica
                            if file_path.lower().endswith('.zip') and extract_zip:
                                print("Estrazione dei file JSON dall'archivio ZIP...")
                                extract_dir = file_path[:-4]  # Rimuovi .zip
                                from json_downloader.utils import extract_zip_files
                                extracted = extract_zip_files(file_path, extract_dir, self.logger)
                                
                                if extracted:
                                    print(f"Estratti {len(extracted)} file da {file_name}")
                                    for ext_file in extracted:
                                        print(f" - {os.path.basename(ext_file)}")
                                    downloaded_files.extend(extracted)
                                else:
                                    print("Nessun file JSON trovato nell'archivio ZIP.")
                            elif file_path.lower().endswith('.zip') and not extract_zip:
                                print("File ZIP scaricato ma non estratto (come richiesto).")
                        else:
                            print(f"Errore durante il download di {link}")
                    except Exception as e:
                        print(f"Errore durante il download: {str(e)}")
                
                # Mostra il riepilogo
                print(f"\nScaricamento completato.")
                print(f"File scaricati: {len(downloaded_files)}")
                print(f"Cartella di destinazione: {dataset_folder}")
        
        except Exception as e:
            print(f"Errore: {str(e)}")
            traceback.print_exc()

    def download_from_custom_link(self):
        """Scarica direttamente un file JSON/ZIP da un link personalizzato."""
        print("\n" + "=" * 60)
        print("DOWNLOAD DIRETTO DA LINK PERSONALIZZATO")
        print("=" * 60)
        print("\nQuesta funzione permette di scaricare direttamente un file da un link personalizzato.")
        
        # Chiedi il link personalizzato
        custom_link = input("\nInserisci il link completo del file da scaricare: ").strip()
        
        if not custom_link:
            print("Link non valido. Operazione annullata.")
            return
        
        # Verifica che il link sia valido
        if not custom_link.startswith(('http://', 'https://')):
            print("Il link deve iniziare con http:// o https://")
            custom_link = "https://" + custom_link
            print(f"Link corretto a: {custom_link}")
            
        # Verifica se il link potrebbe essere una pagina di dataset invece di un file diretto
        is_dataset_page = False
        
        # Verifica pattern comuni di URL dataset vs file diretto
        if not custom_link.lower().endswith(('.json', '.zip')):
            if 'dataset' in custom_link.lower() and not 'download' in custom_link.lower():
                is_dataset_page = True
                print("\nRilevato URL di pagina dataset. Proverò a trovare i file da scaricare.")
        
        # Se sembra una pagina di dataset, chiedi se fare lo scraping
        if is_dataset_page:
            do_scraping = input("\nQuesto sembra essere un link a una pagina di dataset, non a un file diretto.\nVuoi cercare automaticamente i file disponibili? (s/n): ").strip().lower() == 's'
            
            if do_scraping:
                # Usa la funzione esistente per dataset specifici
                print("\nRedirezione alla funzionalità di download da dataset specifico...")
                
                # Salva temporaneamente l'URL per utilizzarlo nella funzione di dataset specifico
                self.temp_dataset_url = custom_link
                
                # Richiama la funzione dedicata ai dataset
                self.download_from_specific_dataset(custom_link)
                return
            else:
                print("\nProcederò con il download diretto del link fornito.")
        
        # Chiedi se estrarre automaticamente i file ZIP
        extract_zip = input("\nVuoi estrarre automaticamente i file ZIP scaricati? (s/n): ").strip().lower() == 's'
        if extract_zip:
            print("I file ZIP verranno estratti automaticamente.")
        else:
            print("I file ZIP NON verranno estratti.")
        
        # Chiedi in quale cartella salvare
        print("\nOpzioni di salvataggio:")
        print("1. Salvare nella cartella principale dei download")
        print("2. Creare una sottocartella dedicata")
        save_option = input("Scegli l'opzione (1/2): ").strip()
        
        if save_option == '2':
            # Crea una sottocartella
            subfolder_name = input("Nome della sottocartella: ").strip()
            if not subfolder_name:
                subfolder_name = f"custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            download_folder = os.path.join(self.config['download_dir'], subfolder_name)
            os.makedirs(download_folder, exist_ok=True)
            print(f"Creata cartella: {download_folder}")
        else:
            # Usa la cartella principale
            download_folder = self.config['download_dir']
            print(f"Utilizzo cartella principale: {download_folder}")
        
        # Ottieni il nome del file dal link
        file_name = os.path.basename(custom_link.split('?')[0])
        if not file_name:
            file_name = f"download_{datetime.now().strftime('%Y%m%d_%H%M%S')}.dat"
        
        # Path completo del file
        file_path = os.path.join(download_folder, file_name)
        
        # Verifica se il file esiste già
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            print(f"File {file_name} già esiste. Download saltato automaticamente.")
            
            # Chiedi se aggiungere il link alla cache anche se saltato
            add_to_cache = input("\nVuoi aggiungere questo link alla cache per futuri download? (s/n): ").strip().lower()
            if add_to_cache == 's':
                if custom_link not in self.json_links:
                    self.json_links.add(custom_link)
                    save_links_to_cache(self.json_links, self.links_cache_file)
                    print("Link aggiunto alla cache.")
                else:
                    print("Il link era già presente nella cache.")
            return
        
        # Scarica il file
        print(f"\nScaricamento di {file_name} in corso...")
        try:
            from json_downloader.downloader import download_file
            
            # Estrai solo i parametri necessari dalla configurazione
            max_retries = 3
            if isinstance(self.config, dict) and 'max_retries' in self.config:
                max_retries = self.config['max_retries']
                
            file_hash = download_file(
                custom_link, 
                file_path, 
                logger=self.logger, 
                max_retries=max_retries
            )
            
            # Se l'hash è None, il download è fallito
            if file_hash:
                print(f"Download completato: {file_path}")
                print(f"SHA256: {file_hash}")
                
                # Se è un file ZIP e l'utente ha scelto di estrarlo
                if file_path.lower().endswith('.zip') and extract_zip:
                    print("\nEstrazione dei file JSON dall'archivio ZIP...")
                    extract_dir = file_path[:-4]  # Rimuovi .zip
                    from json_downloader.utils import extract_zip_files
                    extracted = extract_zip_files(file_path, extract_dir, self.logger)
                    
                    if extracted:
                        print(f"Estratti {len(extracted)} file da {file_name}:")
                        for ext_file in extracted:
                            print(f" - {os.path.basename(ext_file)}")
                    else:
                        print("Nessun file JSON trovato nell'archivio ZIP.")
                elif file_path.lower().endswith('.zip') and not extract_zip:
                    print("File ZIP scaricato ma non estratto (come richiesto).")
                
                # Chiedi se aggiungere il link alla cache
                add_to_cache = input("\nVuoi aggiungere questo link alla cache per futuri download? (s/n): ").strip().lower()
                if add_to_cache == 's':
                    if custom_link not in self.json_links:
                        self.json_links.add(custom_link)
                        save_links_to_cache(self.json_links, self.links_cache_file)
                        print("Link aggiunto alla cache.")
                    else:
                        print("Il link era già presente nella cache.")
            else:
                print(f"Errore durante il download da {custom_link}")
        except Exception as e:
            print(f"Errore durante il download: {str(e)}")
            traceback.print_exc()

    def extract_all_zips_to_database(self):
        """Scansiona tutte le cartelle di download ed estrae i file ZIP in /database/JSON."""
        print("\n" + "=" * 60)
        print("ESTRAZIONE FILE ZIP IN /database/JSON")
        print("=" * 60)
        
        # Verifica che il mount point /database esista
        database_dir = "/database"
        if not os.path.exists(database_dir):
            print(f"Errore: Il mount point {database_dir} non esiste o non è accessibile.")
            return
            
        # Crea la sottocartella JSON se non esiste
        json_dir = os.path.join(database_dir, "JSON")
        try:
            os.makedirs(json_dir, exist_ok=True)
            print(f"Directory JSON creata/verificata: {json_dir}")
        except Exception as e:
            print(f"Errore nella creazione della directory JSON: {str(e)}")
            return
        
        # Verifica che la directory di download esista
        if not os.path.exists(self.config['download_dir']):
            print(f"Directory di download non trovata: {self.config['download_dir']}")
            return
        
        # Cerca tutti i file ZIP ricorsivamente
        zip_files = []
        for root, _, files in os.walk(self.config['download_dir']):
            for file in files:
                if file.lower().endswith('.zip'):
                    zip_files.append(os.path.join(root, file))
        
        if not zip_files:
            print("Nessun file ZIP trovato nelle directory di download.")
            return
        
        print(f"\nTrovati {len(zip_files)} file ZIP da estrarre.")
        
        # Chiedi conferma
        confirm = input("\nVuoi procedere con l'estrazione? (s/n): ").strip().lower()
        if confirm != 's':
            print("Estrazione annullata.")
            return
        
        # Estrai i file
        extracted_count = 0
        error_count = 0
        
        for i, zip_path in enumerate(zip_files, 1):
            try:
                print(f"\n[{i}/{len(zip_files)}] Estrazione di {os.path.basename(zip_path)}...")
                
                # Crea una sottocartella in /database/JSON con il nome del file ZIP (senza estensione)
                zip_name = os.path.splitext(os.path.basename(zip_path))[0]
                extract_dir = os.path.join(json_dir, zip_name)
                os.makedirs(extract_dir, exist_ok=True)
                
                # Estrai i file
                from json_downloader.utils import extract_zip_files
                extracted = extract_zip_files(zip_path, extract_dir, self.logger)
                
                if extracted:
                    print(f"✓ Estratti {len(extracted)} file in {extract_dir}")
                    extracted_count += len(extracted)
                else:
                    print("! Nessun file estratto (possibilmente nessun file JSON trovato)")
                
            except Exception as e:
                print(f"✗ Errore durante l'estrazione: {str(e)}")
                error_count += 1
                if self.logger:
                    self.logger.error(f"Errore durante l'estrazione di {zip_path}: {str(e)}")
        
        # Mostra riepilogo
        print("\n" + "=" * 60)
        print("ESTRAZIONE COMPLETATA")
        print("=" * 60)
        print(f"✓ File estratti con successo: {extracted_count}")
        print(f"✗ Errori durante l'estrazione: {error_count}")
        print(f"📁 Directory di destinazione: {json_dir}")

    def download_with_auto_sorting(self):
        """Download con smistamento automatico in /database/JSON."""
        print("\n" + "=" * 60)
        print("DOWNLOAD CON SMISTAMENTO AUTOMATICO IN /database/JSON")
        print("=" * 60)
        
        # Verifica che il path /database/JSON esista
        database_path = "/database/JSON"
        if not os.path.exists(database_path):
            print(f"Errore: Il path {database_path} non esiste.")
            print("Assicurati che il mount point /database sia disponibile.")
            return
        
        print(f"Path database verificato: {database_path}")
        
        # Scansiona i file esistenti
        try:
            from json_downloader.utils import scan_existing_files
            existing_files, available_folders = scan_existing_files()
            
            print(f"\nTrovate {len(available_folders)} cartelle disponibili per lo smistamento:")
            for i, folder in enumerate(available_folders, 1):
                print(f"  {i}. {folder}")
            
            print(f"\nTrovati {len(existing_files)} file già presenti nel database.")
            
        except Exception as e:
            print(f"Errore nella scansione del database: {e}")
            return
        
        if not self.json_links:
            print("\nNessun link in cache. Esegui prima lo scraping per trovare file da scaricare.")
            return
        
        print(f"\nSono disponibili {len(self.json_links)} link per il download.")
        
        # Chiedi se estrarre gli archivi zip
        extract_zip = input("\nVuoi estrarre automaticamente i file ZIP? (s/n): ").strip().lower() == 's'
        
        # Chiedi se filtrare solo i file JSON
        filter_json_only = input("Vuoi scaricare solo file JSON e ZIP contenenti JSON? (s/n): ").strip().lower() == 's'
        
        if filter_json_only:
            filtered_links = []
            for link in self.json_links:
                link_lower = link.lower()
                # Mantieni i link che terminano con .json o _json o .json.zip o contengono /json/ nel percorso
                if (link_lower.endswith('.json') or 
                    link_lower.endswith('_json.zip') or 
                    '/json/' in link_lower or 
                    'format=json' in link_lower):
                    filtered_links.append(link)
                # Esclude esplicitamente link che sembrano CSV o TTL o XML
                elif any(ext in link_lower for ext in ['_csv.', '.csv.', '_ttl.', '.ttl.', '_xml.', '.xml.']):
                    continue
                # Per ZIP generici, li include solo se non contengono indicazioni CSV/TTL/XML
                elif link_lower.endswith('.zip') and not any(ext in link_lower for ext in ['_csv', '.csv', '_ttl', '.ttl', '_xml', '.xml']):
                    filtered_links.append(link)
            
            original_count = len(self.json_links)
            self.json_links = filtered_links
            print(f"\nFiltrati {original_count - len(self.json_links)} link non-JSON. Rimasti {len(self.json_links)} link JSON/ZIP.")
        
        # Ask how many files to download
        max_files_input = input("\nQuanti file vuoi scaricare? (0 per tutti, invio = tutti): ").strip()
        try:
            max_files = 0 if not max_files_input else int(max_files_input)
        except ValueError:
            print("Input non valido. Verranno scaricati tutti i file.")
            max_files = 0
        
        if max_files == 0:
            links_to_download = list(self.json_links)
        else:
            links_to_download = list(self.json_links)[:max_files]
        
        print(f"\nVerranno scaricati {len(links_to_download)} file.")
        
        # Ask for confirmation
        confirm = input("Vuoi procedere? (s/n): ").strip().lower()
        if confirm != 's':
            print("Download annullato.")
            return
        
        # Download files with auto-sorting
        print("\nDownload con smistamento automatico in corso...")
        
        from json_downloader.downloader import download_with_auto_sorting
        
        downloaded_files = []
        skipped_files = []
        error_files = []
        files_by_folder = {}
        
        for i, link in enumerate(links_to_download, 1):
            try:
                print(f"\n[{i}/{len(links_to_download)}] Elaborazione: {os.path.basename(link.split('?')[0])}")
                
                result = download_with_auto_sorting(
                    link,
                    self.config['download_dir'],
                    logger=self.logger,
                    show_progress=True,
                    extract_zip=extract_zip
                )
                
                if result['success']:
                    if result.get('skipped', False):
                        skipped_files.append(result)
                        print(f"✓ Saltato: {result['filename']} (già esistente)")
                    else:
                        downloaded_files.append(result)
                        folder = result['target_folder']
                        if folder not in files_by_folder:
                            files_by_folder[folder] = []
                        files_by_folder[folder].append(result['filename'])
                        print(f"✓ Scaricato: {result['filename']} → {folder}")
                        
                        if result.get('extracted_files'):
                            print(f"  Estratti {len(result['extracted_files'])} file")
                else:
                    error_files.append({'link': link, 'error': result.get('error', 'Errore sconosciuto')})
                    print(f"✗ Errore: {result.get('error', 'Errore sconosciuto')}")
                    
            except Exception as e:
                error_files.append({'link': link, 'error': str(e)})
                print(f"✗ Errore durante l'elaborazione: {str(e)}")
                continue
        
        # Mostra il riepilogo
        print("\n" + "=" * 60)
        print("RIEPILOGO DOWNLOAD CON SMISTAMENTO AUTOMATICO")
        print("=" * 60)
        print(f"✓ File scaricati con successo: {len(downloaded_files)}")
        print(f"⏭️  File saltati (già esistenti): {len(skipped_files)}")
        print(f"✗ File con errori: {len(error_files)}")
        
        if files_by_folder:
            print(f"\n📁 File organizzati per cartella:")
            for folder, files in files_by_folder.items():
                print(f"  {folder}: {len(files)} file")
                for file in files[:3]:  # Mostra solo i primi 3 file
                    print(f"    - {file}")
                if len(files) > 3:
                    print(f"    ... e altri {len(files) - 3} file")
        
        if error_files:
            print(f"\n❌ Errori riscontrati:")
            for error in error_files[:5]:  # Mostra solo i primi 5 errori
                filename = os.path.basename(error['link'].split('?')[0])
                print(f"  - {filename}: {error['error']}")
            if len(error_files) > 5:
                print(f"  ... e altri {len(error_files) - 5} errori")
        
        print(f"\n📁 Tutti i file sono stati smistati in: {database_path}")

    def run(self):
        """Run the CLI interface."""
        self.print_welcome()
        try:
            self.display_menu()
        except KeyboardInterrupt:
            print("\n\nOperazione interrotta dall'utente. Uscita.")
        except Exception as e:
            self.logger.error(f"Errore durante l'esecuzione: {str(e)}")
            traceback.print_exc()
            print(f"\nErrore: {str(e)}")
            print("\nL'applicazione si è chiusa a causa di un errore.")
        finally:
            print("\nGrazie per aver utilizzato ANAC JSON Downloader!")
            print(f"File di log: {self.config['log_file']}")
            print("=" * 60 + "\n")

if __name__ == "__main__":
    import os
    import sys
    import json
    import time
    import requests
    from datetime import datetime
    import traceback
    
    # Definizioni necessarie per il funzionamento autonomo del file
    def load_links_from_cache(cache_file="cache/json_links.txt"):
        links = set()
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                for line in f:
                    link = line.strip()
                    if link:
                        links.add(link)
        return links
        
    def save_links_to_cache(links, cache_file="cache/json_links.txt"):
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'w', encoding='utf-8') as f:
            for link in links:
                f.write(f"{link}\n")
    
    def verify_file_integrity(file_path):
        if not os.path.exists(file_path):
            return False
        if os.path.getsize(file_path) == 0:
            return False
        return True
    
    def ensure_dir(directory):
        os.makedirs(directory, exist_ok=True)
    
    def process_downloaded_file(file_path, extract_dir=None, logger=None):
        if file_path.lower().endswith('.zip'):
            # Simulazione semplice per il test
            return {
                'is_zip': True,
                'extracted_files': []
            }
        return {
            'is_zip': False,
            'path': file_path
        }
    
    def setup_logger(log_file):
        import logging
        # Ensure directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Create logger
        logger = logging.getLogger("anac_downloader")
        logger.setLevel(logging.INFO)
        
        # Create file handler
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(fh)
        
        return logger
    
    # Crea una configurazione base
    default_config = {
        'base_url': 'https://dati.anticorruzione.it/opendata',
        'download_dir': os.path.join(os.getcwd(), 'downloads'),
        'log_file': os.path.join(os.getcwd(), 'log', 'anac_downloader.log'),
        'timeout': 30,
        'debug_mode': False
    }
    
    # Assicura che le directory necessarie esistano
    for dir_path in ['downloads', 'log', 'cache']:
        os.makedirs(dir_path, exist_ok=True)
    
    # Avvia l'applicazione con la configurazione base
    cli = ANACDownloaderCLI()
    cli.config = default_config
    cli.download_dir = default_config['download_dir']
    cli.run()