#!/usr/bin/env python
import os
import sys
import json
import time
import requests
from datetime import datetime
from scraper import load_config, scrape_all_json_links
from downloader import download_file, should_download, verify_file_integrity, process_downloaded_file
from utils import setup_logger, ensure_dir, normalize_url, sanitize_filename, save_links_to_cache, load_links_from_cache, deduplicate_links, format_size, load_datasets_from_cache, save_datasets_to_cache, load_direct_links_from_cache, save_direct_links_to_cache
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
        """Inizializza l'applicazione caricando config e logger"""
        try:
            # Cerca il file config.json
            script_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(script_dir, 'config.json')
            
            if not os.path.exists(config_path):
                print(f"File di configurazione non trovato: {config_path}")
                return False
            
            self.config = load_config(config_path)
            
            # Setup del logger
            log_file = self.config.get('log_file', 'log/downloader.log')
            self.logger = setup_logger(log_file)
            
            # Crea cartella download se non esiste
            self.download_dir = self.config.get('download_dir', 'downloads')
            ensure_dir(self.download_dir)
            
            # Crea cartella cache se non esiste
            ensure_dir("cache")
            
            return True
        except FileNotFoundError as e:
            print(f"File non trovato: {str(e)}")
            traceback.print_exc()
            return False
        except json.JSONDecodeError as e:
            print(f"Errore nel formato JSON: {str(e)}")
            traceback.print_exc()
            return False
        except Exception as e:
            print(f"Errore di inizializzazione: {str(e)}")
            traceback.print_exc()
            return False
    
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
    
    def print_menu(self):
        """Stampa il menu principale"""
        print("\nMENU PRINCIPALE:")
        print("1. Esegui scraping delle pagine web (cerca file JSON/ZIP)")
        print("2. Scarica i file JSON/ZIP trovati")
        print("3. Verifica integrità file già scaricati")
        print("4. Visualizza link in cache")
        print("5. Aggiungi link manualmente alla cache")
        print("6. Carica link da file esterno")
        print("7. Deduplicazione avanzata dei link")
        print("8. Gestisci dataset e link diretti noti")
        print("0. Esci dal programma")
        return input("\nSeleziona un'opzione (0-8): ")
    
    def filter_duplicate_links(self, new_links):
        """Filtra i link duplicati e restituisce solo quelli nuovi."""
        if not new_links:
            return set()
            
        # Converti in set se non lo è già
        if not isinstance(new_links, set):
            new_links = set(new_links)
            
        # Trova i link che non sono già presenti nella cache
        unique_links = new_links.difference(self.json_links)
        
        # Calcola i duplicati
        duplicates = new_links.intersection(self.json_links)
        
        if duplicates:
            if self.logger:
                self.logger.info(f"Trovati {len(duplicates)} link duplicati che verranno ignorati")
            print(f"Ignorati {len(duplicates)} link duplicati.")
            
        return unique_links
    
    def run_scraping(self):
        """Esegue lo scraping delle pagine web"""
        print("\n" + "=" * 60)
        print("AVVIO SCRAPING PAGINE WEB...")
        print("=" * 60)
        
        try:
            # Chiedi conferma
            confirm = input("Lo scraping potrebbe richiedere diversi minuti. Continuare? (s/n): ").lower()
            if confirm != 's':
                print("Operazione annullata.")
                return
            
            # Opzione per modalità debug (browser visibile)
            debug_mode = input("Vuoi eseguire in modalità debug (browser visibile)? (s/n): ").lower() == 's'
            if debug_mode:
                self.config['debug_mode'] = True
            
            # Opzione per usare solo link noti
            use_known = input("Vuoi aggiungere automaticamente link noti alla lista? (s/n): ").lower() == 's'
            
            print("Avvio scraping in corso...")
            start_time = time.time()
            
            # Imposta use_known nella configurazione
            if use_known:
                self.config['use_known_only'] = use_known
                print("Verranno inclusi dataset e link noti nell'elaborazione.")
            
            # Esegui scraping
            all_links = scrape_all_json_links(self.config, self.logger)
            
            # Filtra i link duplicati semplici
            new_links = self.filter_duplicate_links(all_links)
            
            # Aggiungi nuovi link
            old_count = len(self.json_links)
            self.json_links.update(new_links)
            
            # Cerca e rimuovi duplicati "nascosti" (differenze di formattazione)
            print("\nAnalisi approfondita per identificare URL duplicati...")
            self.deduplicate_normalized_links()
            
            # Salva i link in cache
            save_links_to_cache(self.json_links, self.links_cache_file)
            
            elapsed = time.time() - start_time
            print(f"\nScraping completato in {elapsed:.1f} secondi!")
            print(f"Trovati {len(new_links)} nuovi link a file JSON/ZIP")
            print(f"Totale link in cache dopo deduplicazione: {len(self.json_links)}")
            
            # Mostra alcuni esempi
            if new_links:
                print("\nEsempi di link trovati:")
                for link in list(new_links)[:5]:
                    print(f"- {link}")
                if len(new_links) > 5:
                    print(f"... e altri {len(new_links)-5} link")
            
            input("\nPremi INVIO per tornare al menu principale...")
        
        except KeyboardInterrupt:
            print("\n\nScraping interrotto dall'utente.")
            if self.logger:
                self.logger.warning("Scraping interrotto dall'utente con Ctrl+C")
            input("\nPremi INVIO per tornare al menu principale...")
        except ImportError as e:
            print(f"\nErrore: Libreria mancante - {str(e)}")
            print("Assicurati di aver installato le dipendenze con 'pip install -r requirements.txt'")
            if self.logger:
                self.logger.error(f"Errore di importazione: {str(e)}")
            traceback.print_exc()
            input("\nPremi INVIO per tornare al menu principale...")
        except Exception as e:
            print(f"\nErrore durante lo scraping: {str(e)}")
            if self.logger:
                self.logger.error(f"Errore durante lo scraping: {str(e)}")
                self.logger.error(traceback.format_exc())
            traceback.print_exc()
            input("\nPremi INVIO per tornare al menu principale...")
    
    def deduplicate_normalized_links(self):
        """Esegue una deduplicazione avanzata dei link cercando URL equivalenti."""
        if not self.json_links:
            return
            
        original_count = len(self.json_links)
        print(f"Controllo {original_count} link per trovare duplicati...")
        
        # Deduplicazione avanzata
        self.json_links, report = deduplicate_links(self.json_links, self.logger)
        
        if report["duplicates_found"] > 0:
            print(f"Trovati e rimossi {report['links_removed']} link duplicati.")
            print(f"Ridotto da {report['before']} a {report['after']} link unici.")
        else:
            print("Nessun duplicato trovato durante l'analisi avanzata.")
        
        return report
    
    def estimate_download_size(self, links, sample_size=5):
        """Stima la dimensione totale del download basandosi su un campione di link."""
        if not links:
            return 0
        
        sample = list(links)[:min(sample_size, len(links))]
        total_size = 0
        sampled_size = 0
        
        print(f"Stima della dimensione totale del download in corso...")
        
        # Headers per simulare una richiesta da browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        for i, link in enumerate(sample):
            try:
                normalized_link = normalize_url(link, self.config['base_url'])
                print(f"[{i+1}/{len(sample)}] Controllo dimensione di {normalized_link}...")
                
                head_response = requests.head(normalized_link, headers=headers, timeout=10)
                if head_response.ok and 'content-length' in head_response.headers:
                    size = int(head_response.headers['content-length'])
                    sampled_size += size
                    print(f"  Dimensione: {format_size(size)}")
                else:
                    print("  Dimensione non disponibile")
            except Exception as e:
                print(f"  Errore: {str(e)}")
        
        # Se abbiamo ottenuto almeno una dimensione, facciamo una stima
        if sampled_size > 0 and len(sample) > 0:
            avg_size = sampled_size / len(sample)
            total_size = avg_size * len(links)
            print(f"\nDimensione stimata per {len(links)} file: {format_size(total_size)}")
            print(f"Basata su un campione di {len(sample)} file con dimensione media di {format_size(avg_size)}")
            
        return total_size
    
    def run_download(self):
        """Esegue il download dei file JSON/ZIP trovati"""
        print("\n" + "=" * 60)
        print("DOWNLOAD DEI FILE JSON/ZIP...")
        print("=" * 60)
        
        try:
            # Verifica se ci sono link da scaricare
            if not self.json_links:
                # Prova a caricare da cache
                self.json_links = load_links_from_cache(self.links_cache_file)
                if self.json_links:
                    print(f"Caricati {len(self.json_links)} link dalla cache.")
            
            if not self.json_links:
                print("Nessun link trovato. Esegui prima lo scraping (opzione 1) o aggiungi link manualmente.")
                input("\nPremi INVIO per tornare al menu principale...")
                return
            
            # Configura la cartella di download
            use_default_dir = True
            if not hasattr(self, 'use_session_dir_preference'):
                # Se è la prima volta, chiedi la preferenza
                use_session = input("Vuoi creare una cartella sessione per i download? (s/n): ").lower() == 's'
                
                # Chiedi se vuoi salvare questa preferenza
                save_preference = input("Vuoi salvare questa preferenza per future esecuzioni? (s/n): ").lower() == 's'
                if save_preference:
                    self.use_session_dir_preference = use_session
                    use_default_dir = not use_session
            else:
                # Usa la preferenza salvata
                use_session = self.use_session_dir_preference
                use_default_dir = not use_session
                print(f"Usando la preferenza salvata: {'creazione cartella sessione' if use_session else 'uso cartella principale'}")
            
            if use_session:
                self.session_dir = os.path.join(self.download_dir, datetime.now().strftime('%Y%m%d_%H%M%S'))
                ensure_dir(self.session_dir)
                print(f"I file saranno scaricati in: {self.session_dir}")
            elif use_default_dir and hasattr(self, 'session_dir') and self.session_dir != self.download_dir:
                # Se abbiamo già una cartella sessione ma vogliamo usare quella principale
                self.session_dir = self.download_dir
                print(f"I file saranno scaricati in: {self.download_dir}")
            elif not hasattr(self, 'session_dir') or self.session_dir is None:
                # Se non abbiamo ancora impostato una cartella sessione
                self.session_dir = self.download_dir
                print(f"I file saranno scaricati in: {self.download_dir}")
            else:
                # Stiamo usando una sessione esistente
                print(f"I file saranno scaricati in: {self.session_dir}")
            
            # Configura altre opzioni
            force_download = input("Vuoi forzare il download anche per file già esistenti? (s/n): ").lower() == 's'
            
            # Chiedi se estrarre ZIP solo se la configurazione lo permette
            extract_zip = False
            if self.config.get('extract_zip_files', True):
                extract_zip = input("Vuoi estrarre automaticamente i file ZIP? (s/n): ").lower() == 's'
            else:
                print("Estrazione automatica dei file ZIP disabilitata nelle impostazioni.")
            
            # Chiedi quanti file scaricare
            total_links = len(self.json_links)
            limit_str = input(f"Quanti file vuoi scaricare (max {total_links}, 'tutto' per tutti): ")
            
            if limit_str.lower() in ('tutto', 'all', ''):
                limit = total_links
            else:
                try:
                    limit = int(limit_str)
                    limit = min(limit, total_links)
                except ValueError:
                    print("Valore non valido, uso il default di 10 file.")
                    limit = 10  # Default
            
            print(f"\nVerranno scaricati {limit} file su {total_links} disponibili.")
            
            # Stima dimensione totale
            if limit <= 50:  # Per evitare troppe richieste se ci sono molti file
                self.estimate_download_size(list(self.json_links)[:limit], sample_size=min(5, limit))
            else:
                sample_size = min(10, int(limit / 10))  # 10% dei file, massimo 10
                self.estimate_download_size(list(self.json_links)[:limit], sample_size=sample_size)
            
            confirm = input("Continuare con il download? (s/n): ").lower()
            if confirm != 's':
                print("Download annullato.")
                return
            
            # Inizia il download
            print("\nAvvio download in corso...\n")
            start_time = time.time()
            
            successfully_downloaded = 0
            failed_downloads = 0
            skipped_downloads = 0
            extracted_files = 0
            
            # Statistiche totali
            total_downloaded_size = 0
            
            for i, link in enumerate(list(self.json_links)[:limit]):
                try:
                    print(f"[{i+1}/{limit}] Download di {link}...")
                    
                    # Normalizza URL
                    normalized_link = normalize_url(link, self.config['base_url'])
                    
                    # Genera nome file pulito
                    filename = sanitize_filename(os.path.basename(normalized_link))
                    if not filename or filename == '.zip' or filename == '.json':
                        # Se non c'è un nome file o è solo un'estensione, usa hash dell'URL
                        filename = f"file_{abs(hash(normalized_link)) % 10000}"
                    
                    # Verifica estensione file
                    is_zip = '.zip' in normalized_link.lower()
                    extension = '.zip' if is_zip else '.json'
                    
                    if not filename.endswith(extension):
                        filename += extension
                    
                    dest_path = os.path.join(self.session_dir, filename)
                    
                    if should_download(dest_path, force=force_download):
                        # Parametri di download dalla config
                        start_time = time.time()
                        sha256 = download_file(
                            normalized_link,
                            dest_path,
                            chunk_size=self.config.get('chunk_size', 1048576),
                            max_retries=self.config.get('max_retries', 5),
                            backoff=self.config.get('retry_backoff', 2),
                            logger=self.logger,
                            show_progress=True
                        )
                        
                        if sha256:
                            # Calcola le statistiche del file scaricato
                            file_size = os.path.getsize(dest_path)
                            download_time = time.time() - start_time
                            avg_speed = file_size / download_time if download_time > 0 else 0
                            
                            print(f"✓ Scaricato con successo: {filename} ({format_size(file_size)}, {format_size(avg_speed)}/s)")
                            
                            # Processa il file scaricato (estrai se ZIP)
                            if extract_zip and is_zip:
                                result = process_downloaded_file(
                                    dest_path, 
                                    self.session_dir, 
                                    self.logger,
                                    self.config
                                )
                                if result['is_zip']:
                                    extract_count = len(result.get('extracted_files', []))
                                    total_count = result.get('total_files', 0)
                                    extracted_files += extract_count
                                    print(f"  ↳ Estratti {extract_count} file JSON su {total_count} totali da {filename}")
                            
                            successfully_downloaded += 1
                            total_downloaded_size += file_size
                        else:
                            print(f"✗ Download fallito: {filename}")
                            failed_downloads += 1
                    else:
                        print(f"⊙ File già presente: {filename}")
                        skipped_downloads += 1
                        
                except requests.exceptions.RequestException as e:
                    print(f"✗ Errore di rete: {str(e)}")
                    if self.logger:
                        self.logger.error(f"Errore di rete durante il download di {link}: {str(e)}")
                    failed_downloads += 1
                except (IOError, OSError) as e:
                    print(f"✗ Errore di I/O: {str(e)}")
                    if self.logger:
                        self.logger.error(f"Errore di I/O durante il download di {link}: {str(e)}")
                    failed_downloads += 1
                except Exception as e:
                    print(f"✗ Errore: {str(e)}")
                    if self.logger:
                        self.logger.error(f"Errore durante il download di {link}: {str(e)}")
                    failed_downloads += 1
            
            elapsed = time.time() - start_time
            
            print("\n" + "=" * 60)
            print(f"DOWNLOAD COMPLETATO IN {elapsed:.1f} SECONDI")
            print("=" * 60)
            print(f"✓ Download completati: {successfully_downloaded}")
            print(f"⊙ File già presenti: {skipped_downloads}")
            print(f"✗ Download falliti: {failed_downloads}")
            
            # Mostra informazioni sull'estrazione solo se l'estrazione è abilitata
            if self.config.get('extract_zip_files', True):
                print(f"↳ File estratti da ZIP: {extracted_files}")
            else:
                print("ℹ Estrazione automatica dai file ZIP disabilitata.")
                
            # Mostra informazioni sulla dimensione totale e velocità media
            if total_downloaded_size > 0:
                avg_speed = total_downloaded_size / elapsed if elapsed > 0 else 0
                print(f"📊 Dimensione totale scaricata: {format_size(total_downloaded_size)}")
                print(f"📈 Velocità media complessiva: {format_size(avg_speed)}/s")
            
            # Salva report
            if self.config.get('save_report', True):
                # Crea directory reports
                report_dir = os.path.join(self.session_dir, 'reports')
                ensure_dir(report_dir)
                report_path = os.path.join(report_dir, f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                
                report = {
                    "timestamp": datetime.now().isoformat(),
                    "total_links": len(self.json_links),
                    "downloaded": successfully_downloaded,
                    "skipped": skipped_downloads,
                    "failed": failed_downloads,
                    "extracted_files": extracted_files,
                    "links": list(self.json_links)[:limit]
                }
                
                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2)
                
                print(f"\nReport salvato in: {report_path}")
            
            input("\nPremi INVIO per tornare al menu principale...")
            
        except KeyboardInterrupt:
            print("\n\nDownload interrotto dall'utente.")
            if self.logger:
                self.logger.warning("Download interrotto dall'utente con Ctrl+C")
            input("\nPremi INVIO per tornare al menu principale...")
        except PermissionError as e:
            print(f"\nErrore di permessi: {str(e)}")
            print("Verifica di avere i permessi per scrivere nella directory di download.")
            if self.logger:
                self.logger.error(f"Errore di permessi: {str(e)}")
            traceback.print_exc()
            input("\nPremi INVIO per tornare al menu principale...")
        except Exception as e:
            print(f"\nErrore durante il download: {str(e)}")
            if self.logger:
                self.logger.error(f"Errore durante il download: {str(e)}")
                self.logger.error(traceback.format_exc())
            traceback.print_exc()
            input("\nPremi INVIO per tornare al menu principale...")
    
    def verify_files(self):
        """Verifica l'integrità dei file scaricati"""
        print("\n" + "=" * 60)
        print("VERIFICA INTEGRITÀ FILE...")
        print("=" * 60)
        
        try:
            # Scegli la cartella da verificare
            print("\nCartelle disponibili:")
            base_dir = self.download_dir
            
            # Verifica che la cartella download esista
            if not os.path.exists(base_dir):
                print(f"La cartella {base_dir} non esiste.")
                input("\nPremi INVIO per tornare al menu principale...")
                return
                
            # Elenca le sottocartelle (escludendo 'reports')
            dirs = []
            try:
                dirs = [d for d in os.listdir(base_dir) 
                       if os.path.isdir(os.path.join(base_dir, d)) and d != 'reports']
            except Exception as e:
                print(f"Errore nell'elencare le cartelle: {str(e)}")
            
            if not dirs:
                print("Nessuna sottocartella trovata in", base_dir)
                check_dir = base_dir
            else:
                print("0. Cartella principale:", base_dir)
                for i, d in enumerate(dirs):
                    print(f"{i+1}. {d}")
                
                choice = input("\nScegli una cartella (0-" + str(len(dirs)) + "): ")
                try:
                    idx = int(choice)
                    if idx == 0:
                        check_dir = base_dir
                    else:
                        check_dir = os.path.join(base_dir, dirs[idx-1])
                except ValueError:
                    print("Scelta non valida, uso cartella principale")
                    check_dir = base_dir
            
            print(f"\nVerifica file in: {check_dir}")
            
            # Verifica che la cartella selezionata esista
            if not os.path.exists(check_dir):
                print(f"La cartella {check_dir} non esiste.")
                input("\nPremi INVIO per tornare al menu principale...")
                return
                
            # Conta i file JSON e ZIP
            json_files = []
            zip_files = []
            try:
                json_files = [f for f in os.listdir(check_dir) if f.endswith('.json')]
                zip_files = [f for f in os.listdir(check_dir) if f.endswith('.zip')]
            except PermissionError:
                print(f"Errore: Non hai i permessi per accedere a {check_dir}")
                input("\nPremi INVIO per tornare al menu principale...")
                return
            except Exception as e:
                print(f"Errore nell'elencare i file: {str(e)}")
                input("\nPremi INVIO per tornare al menu principale...")
                return
            
            total_files = len(json_files) + len(zip_files)
            
            if total_files == 0:
                print("Nessun file JSON o ZIP trovato nella cartella.")
                input("\nPremi INVIO per tornare al menu principale...")
                return
            
            print(f"Trovati {len(json_files)} file JSON e {len(zip_files)} file ZIP da verificare.")
            
            # Chiedi conferma
            confirm = input("Continuare con la verifica? (s/n): ").lower()
            if confirm != 's':
                print("Verifica annullata.")
                return
            
            print("\nVerifica in corso...\n")
            
            valid_files = 0
            invalid_files = 0
            
            # Verifica file JSON e ZIP
            for i, filename in enumerate(json_files + zip_files):
                file_path = os.path.join(check_dir, filename)
                print(f"[{i+1}/{total_files}] Verifica di {filename}...")
                
                try:
                    if verify_file_integrity(file_path):
                        print(f"✓ Valido: {filename}")
                        valid_files += 1
                    else:
                        print(f"✗ Invalido o danneggiato: {filename}")
                        invalid_files += 1
                except PermissionError:
                    print(f"✗ Errore di permessi: {filename}")
                    invalid_files += 1
                except Exception as e:
                    print(f"✗ Errore durante la verifica di {filename}: {str(e)}")
                    invalid_files += 1
            
            print("\n" + "=" * 60)
            print(f"VERIFICA COMPLETATA")
            print("=" * 60)
            print(f"✓ File validi: {valid_files}")
            print(f"✗ File invalidi: {invalid_files}")
            
            input("\nPremi INVIO per tornare al menu principale...")
            
        except KeyboardInterrupt:
            print("\n\nVerifica interrotta dall'utente.")
            input("\nPremi INVIO per tornare al menu principale...")
        except PermissionError as e:
            print(f"\nErrore di permessi: {str(e)}")
            print("Verifica di avere i permessi necessari per accedere alle cartelle.")
            if self.logger:
                self.logger.error(f"Errore di permessi: {str(e)}")
            traceback.print_exc()
            input("\nPremi INVIO per tornare al menu principale...")
        except Exception as e:
            print(f"\nErrore durante la verifica: {str(e)}")
            if self.logger:
                self.logger.error(f"Errore durante la verifica: {str(e)}")
                self.logger.error(traceback.format_exc())
            traceback.print_exc()
            input("\nPremi INVIO per tornare al menu principale...")
    
    def show_cached_links(self):
        """Visualizza i link in cache"""
        print("\n" + "=" * 60)
        print("LINK IN CACHE")
        print("=" * 60)
        
        try:
            # Carica link dalla cache se non già carichi
            if not self.json_links:
                self.json_links = load_links_from_cache(self.links_cache_file)
            
            if not self.json_links:
                print("Nessun link in cache.")
                input("\nPremi INVIO per tornare al menu principale...")
                return
            
            print(f"Trovati {len(self.json_links)} link in cache.\n")
            
            # Mostra tutti i link o solo alcuni
            show_all = input("Vuoi visualizzare tutti i link? (s/n): ").lower() == 's'
            
            if show_all:
                for i, link in enumerate(self.json_links):
                    print(f"{i+1}. {link}")
            else:
                # Mostra solo primi 10 link
                for i, link in enumerate(list(self.json_links)[:10]):
                    print(f"{i+1}. {link}")
                
                if len(self.json_links) > 10:
                    print(f"...e altri {len(self.json_links)-10} link...")
            
            # Chiedi se salvare in un file esterno
            save_to_file = input("\nVuoi salvare i link in un file esterno? (s/n): ").lower() == 's'
            
            if save_to_file:
                file_path = input("Inserisci il percorso del file: ")
                if not file_path:
                    file_path = "links_export.txt"
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    for link in self.json_links:
                        f.write(f"{link}\n")
                
                print(f"Link salvati in {file_path}")
            
            input("\nPremi INVIO per tornare al menu principale...")
        except FileNotFoundError as e:
            print(f"\nErrore: File non trovato - {str(e)}")
            traceback.print_exc()
            input("\nPremi INVIO per tornare al menu principale...")
        except PermissionError as e:
            print(f"\nErrore di permessi: {str(e)}")
            traceback.print_exc()
            input("\nPremi INVIO per tornare al menu principale...")
        except Exception as e:
            print(f"\nErrore durante la visualizzazione dei link: {str(e)}")
            traceback.print_exc()
            input("\nPremi INVIO per tornare al menu principale...")
    
    def add_links_manually(self):
        """Aggiunge link manualmente alla cache"""
        print("\n" + "=" * 60)
        print("AGGIUNGI LINK MANUALMENTE")
        print("=" * 60)
        
        try:
            # Carica link dalla cache se non già carichi
            if not self.json_links:
                self.json_links = load_links_from_cache(self.links_cache_file)
            
            print(f"Attualmente ci sono {len(self.json_links)} link in cache.")
            print("Inserisci un link per riga. Inserisci una riga vuota per terminare.\n")
            
            links_added = 0
            while True:
                try:
                    link = input("> ")
                    if not link:
                        break
                    
                    if link not in self.json_links:
                        self.json_links.add(link)
                        links_added += 1
                        print(f"Link aggiunto. Totale: {len(self.json_links)}")
                    else:
                        print("Link già presente in cache.")
                except KeyboardInterrupt:
                    print("\nInserimento interrotto.")
                    break
                except Exception as e:
                    print(f"Errore nell'aggiunta del link: {str(e)}")
            
            if links_added > 0:
                # Salva i link in cache
                try:
                    save_links_to_cache(self.json_links, self.links_cache_file)
                    print(f"\nAggiunti {links_added} nuovi link alla cache.")
                except (IOError, PermissionError) as e:
                    print(f"\nErrore nel salvare la cache: {str(e)}")
                    if self.logger:
                        self.logger.error(f"Errore nel salvare la cache: {str(e)}")
            else:
                print("\nNessun nuovo link aggiunto.")
            
            input("\nPremi INVIO per tornare al menu principale...")
        except KeyboardInterrupt:
            print("\n\nAggiunta link interrotta dall'utente.")
            input("\nPremi INVIO per tornare al menu principale...")
        except Exception as e:
            print(f"\nErrore durante l'aggiunta dei link: {str(e)}")
            traceback.print_exc()
            input("\nPremi INVIO per tornare al menu principale...")
    
    def load_links_from_file(self):
        """Carica link da un file esterno"""
        print("\n" + "=" * 60)
        print("CARICA LINK DA FILE")
        print("=" * 60)
        
        try:
            # Carica link dalla cache se non già carichi
            if not self.json_links:
                self.json_links = load_links_from_cache(self.links_cache_file)
            
            print(f"Attualmente ci sono {len(self.json_links)} link in cache.")
            
            file_path = input("Inserisci il percorso del file contenente i link: ")
            if not file_path:
                print("Nessun percorso specificato.")
                input("\nPremi INVIO per tornare al menu principale...")
                return
                
            if not os.path.exists(file_path):
                print(f"File non trovato: {file_path}")
                input("\nPremi INVIO per tornare al menu principale...")
                return
            
            links_before = len(self.json_links)
            new_links = set()
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        link = line.strip()
                        if link:
                            new_links.add(link)
            except UnicodeDecodeError:
                print("Errore: Il file non è in formato UTF-8. Provo con encoding alternativo...")
                try:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        for line in f:
                            link = line.strip()
                            if link:
                                new_links.add(link)
                except Exception as e:
                    print(f"Impossibile leggere il file: {str(e)}")
                    return
            except PermissionError:
                print("Errore: Non hai i permessi per leggere questo file.")
                input("\nPremi INVIO per tornare al menu principale...")
                return
            except IOError as e:
                print(f"Errore durante la lettura del file: {str(e)}")
                input("\nPremi INVIO per tornare al menu principale...")
                return
            
            # Filtra i link duplicati
            unique_links = self.filter_duplicate_links(new_links)
            
            # Aggiungi i link unici
            self.json_links.update(unique_links)
            links_added = len(self.json_links) - links_before
            
            if links_added > 0:
                # Salva i link in cache
                try:
                    save_links_to_cache(self.json_links, self.links_cache_file)
                    print(f"\nAggiunti {links_added} nuovi link alla cache.")
                except (IOError, PermissionError) as e:
                    print(f"\nErrore nel salvare la cache: {str(e)}")
                    if self.logger:
                        self.logger.error(f"Errore nel salvare la cache: {str(e)}")
            else:
                print("\nNessun nuovo link aggiunto.")
            
            input("\nPremi INVIO per tornare al menu principale...")
        except KeyboardInterrupt:
            print("\n\nCaricamento interrotto dall'utente.")
            input("\nPremi INVIO per tornare al menu principale...")
        except Exception as e:
            print(f"\nErrore durante il caricamento dei link: {str(e)}")
            traceback.print_exc()
            input("\nPremi INVIO per tornare al menu principale...")
    
    def run_deduplication(self):
        """Esegue la deduplicazione avanzata dei link in cache."""
        print("\n" + "=" * 60)
        print("DEDUPLICAZIONE AVANZATA DEI LINK")
        print("=" * 60)
        
        try:
            # Carica link dalla cache se non già carichi
            if not self.json_links:
                self.json_links = load_links_from_cache(self.links_cache_file)
            
            if not self.json_links:
                print("Nessun link in cache. Non c'è nulla da deduplicare.")
                input("\nPremi INVIO per tornare al menu principale...")
                return
            
            # Chiedi conferma
            print(f"Ci sono {len(self.json_links)} link in cache.")
            confirm = input("Procedere con la deduplicazione avanzata? (s/n): ").lower()
            if confirm != 's':
                print("Operazione annullata.")
                return
                
            # Deduplicazione
            start_time = time.time()
            original_count = len(self.json_links)
            
            # Esegui la deduplicazione
            report = self.deduplicate_normalized_links()
            
            # Salva i link in cache
            if report["duplicates_found"] > 0:
                save_links_to_cache(self.json_links, self.links_cache_file)
                print("\nNuovi link salvati in cache.")
            
            elapsed = time.time() - start_time
            print(f"\nDeduplicazione completata in {elapsed:.2f} secondi!")
            
            # Chiedi se visualizzare tutti i link
            if report["duplicates_found"] > 0:
                show_all = input("\nVuoi visualizzare tutti i link rimasti? (s/n): ").lower() == 's'
                if show_all:
                    print("\nLink dopo la deduplicazione:")
                    for i, link in enumerate(self.json_links):
                        print(f"{i+1}. {link}")
            
            input("\nPremi INVIO per tornare al menu principale...")
            
        except Exception as e:
            print(f"\nErrore durante la deduplicazione: {str(e)}")
            if self.logger:
                self.logger.error(f"Errore durante la deduplicazione: {str(e)}")
                self.logger.error(traceback.format_exc())
            traceback.print_exc()
            input("\nPremi INVIO per tornare al menu principale...")
    
    def manage_known_sources(self):
        """Gestisce gli elenchi di dataset e link diretti noti."""
        print("\n" + "=" * 60)
        print("GESTIONE DATASET E LINK DIRETTI NOTI")
        print("=" * 60)
        
        try:
            # Carica dataset e link salvati
            known_datasets = load_datasets_from_cache()
            known_direct_links = load_direct_links_from_cache()
            
            while True:
                print("\nSORGENTI DATI MEMORIZZATE:")
                print(f"1. Dataset noti ({len(known_datasets)})")
                print(f"2. Link diretti noti ({len(known_direct_links)})")
                print("3. Torna al menu principale")
                
                choice = input("\nSeleziona un'opzione (1-3): ")
                
                if choice == '1':
                    self._manage_list(known_datasets, "dataset", "cache/known_datasets.txt", save_datasets_to_cache)
                elif choice == '2':
                    self._manage_list(known_direct_links, "link diretti", "cache/known_direct_links.txt", save_direct_links_to_cache)
                elif choice == '3':
                    return
                else:
                    print("Opzione non valida. Riprova.")
        
        except Exception as e:
            print(f"\nErrore nella gestione delle sorgenti: {str(e)}")
            traceback.print_exc()
            input("\nPremi INVIO per tornare al menu principale...")
    
    def _manage_list(self, items, item_type, cache_file, save_function):
        """Gestisce un elenco di elementi (dataset o link diretti)."""
        while True:
            print(f"\nGESTIONE {item_type.upper()} NOTI ({len(items)})")
            print("1. Visualizza tutti")
            print("2. Aggiungi nuovo")
            print("3. Rimuovi elemento")
            print("4. Esporta in file esterno")
            print("5. Torna indietro")
            
            choice = input("\nSeleziona un'opzione (1-5): ")
            
            if choice == '1':  # Visualizza tutti
                if not items:
                    print(f"Nessun {item_type} salvato.")
                else:
                    print(f"\nElenco {item_type} salvati:")
                    for i, item in enumerate(items):
                        print(f"{i+1}. {item}")
                    
                    input("\nPremi INVIO per continuare...")
            
            elif choice == '2':  # Aggiungi nuovo
                print(f"\nInserisci il nuovo {item_type} (riga vuota per terminare):")
                while True:
                    new_item = input("> ")
                    if not new_item:
                        break
                    
                    if new_item in items:
                        print(f"{item_type.capitalize()} già presente.")
                    else:
                        items.append(new_item)
                        save_function(items)
                        print(f"{item_type.capitalize()} aggiunto con successo.")
            
            elif choice == '3':  # Rimuovi elemento
                if not items:
                    print(f"Nessun {item_type} da rimuovere.")
                else:
                    print(f"\nElenco {item_type} salvati:")
                    for i, item in enumerate(items):
                        print(f"{i+1}. {item}")
                    
                    idx = input(f"\nInserisci il numero del {item_type} da rimuovere (0 per annullare): ")
                    try:
                        idx = int(idx)
                        if idx == 0:
                            continue
                        if 1 <= idx <= len(items):
                            removed = items.pop(idx-1)
                            save_function(items)
                            print(f"{item_type.capitalize()} rimosso: {removed}")
                        else:
                            print("Indice non valido.")
                    except ValueError:
                        print("Valore non valido.")
            
            elif choice == '4':  # Esporta in file esterno
                if not items:
                    print(f"Nessun {item_type} da esportare.")
                else:
                    file_path = input(f"Inserisci il percorso del file dove esportare i {item_type}: ")
                    if not file_path:
                        file_path = f"{item_type}_export.txt"
                    
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            for item in items:
                                f.write(f"{item}\n")
                        print(f"{len(items)} {item_type} esportati in {file_path}")
                    except Exception as e:
                        print(f"Errore durante l'esportazione: {str(e)}")
            
            elif choice == '5':  # Torna indietro
                return
            
            else:
                print("Opzione non valida. Riprova.")
    
    def run(self):
        """Esegue l'interfaccia a terminale interattiva"""
        if not self.setup():
            print("Impossibile inizializzare l'applicazione. Uscita.")
            return
        
        # Carica link dalla cache all'avvio
        self.json_links = load_links_from_cache(self.links_cache_file)
        if self.json_links:
            print(f"Caricati {len(self.json_links)} link dalla cache.")
        
        while True:
            self.print_header()
            choice = self.print_menu()
            
            if choice == '0':
                print("Uscita dal programma...")
                break
            elif choice == '1':
                self.run_scraping()
            elif choice == '2':
                self.run_download()
            elif choice == '3':
                self.verify_files()
            elif choice == '4':
                self.show_cached_links()
            elif choice == '5':
                self.add_links_manually()
            elif choice == '6':
                self.load_links_from_file()
            elif choice == '7':
                self.run_deduplication()
            elif choice == '8':
                self.manage_known_sources()
            else:
                print("Opzione non valida. Riprova.")

if __name__ == "__main__":
    cli = ANACDownloaderCLI()
    cli.run() 