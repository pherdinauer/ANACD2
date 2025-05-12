#!/usr/bin/env python
import os
import sys
import json
import time
from datetime import datetime
import argparse
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
        print("0. Esci dal programma")
        return input("\nSeleziona un'opzione (0-6): ")
    
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
            
            # Esegui scraping
            new_links = scrape_all_json_links(self.config, self.logger)
            
            # Aggiungi nuovi link
            old_count = len(self.json_links)
            self.json_links.update(new_links)
            new_count = len(self.json_links) - old_count
            
            # Salva i link in cache
            save_links_to_cache(self.json_links, self.links_cache_file)
            
            elapsed = time.time() - start_time
            print(f"\nScraping completato in {elapsed:.1f} secondi!")
            print(f"Trovati {new_count} nuovi link a file JSON/ZIP")
            print(f"Totale link in cache: {len(self.json_links)}")
            
            # Mostra alcuni esempi
            if new_links:
                print("\nEsempi di link trovati:")
                for link in list(new_links)[:5]:
                    print(f"- {link}")
                if len(new_links) > 5:
                    print(f"... e altri {len(new_links)-5} link")
            
            input("\nPremi INVIO per tornare al menu principale...")
            
        except Exception as e:
            print(f"\nErrore durante lo scraping: {str(e)}")
            if self.logger:
                self.logger.error(f"Errore durante lo scraping: {str(e)}")
                self.logger.error(traceback.format_exc())
            traceback.print_exc()
            input("\nPremi INVIO per tornare al menu principale...")
    
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
            use_session = input("Vuoi creare una cartella sessione per i download? (s/n): ").lower() == 's'
            if use_session:
                self.session_dir = os.path.join(self.download_dir, datetime.now().strftime('%Y%m%d_%H%M%S'))
                ensure_dir(self.session_dir)
                print(f"I file saranno scaricati in: {self.session_dir}")
            else:
                self.session_dir = self.download_dir
                print(f"I file saranno scaricati in: {self.download_dir}")
            
            # Configura altre opzioni
            force_download = input("Vuoi forzare il download anche per file già esistenti? (s/n): ").lower() == 's'
            extract_zip = input("Vuoi estrarre automaticamente i file ZIP? (s/n): ").lower() == 's'
            
            # Chiedi quanti file scaricare
            total_links = len(self.json_links)
            limit_str = input(f"Quanti file vuoi scaricare (max {total_links}, 'tutto' per tutti): ")
            
            if limit_str.lower() in ('tutto', 'all', ''):
                limit = total_links
            else:
                try:
                    limit = int(limit_str)
                    limit = min(limit, total_links)
                except:
                    limit = 10  # Default
            
            print(f"\nVerranno scaricati {limit} file su {total_links} disponibili.")
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
            
            for i, link in enumerate(list(self.json_links)[:limit]):
                try:
                    print(f"[{i+1}/{limit}] Download di {link}...")
                    
                    # Normalizza URL
                    normalized_link = normalize_url(link, self.config['base_url'])
                    
                    # Genera nome file pulito
                    filename = sanitize_filename(os.path.basename(normalized_link))
                    if not filename:
                        # Se non c'è un nome file, usa hash dell'URL
                        filename = f"file_{hash(normalized_link) % 10000}"
                    
                    # Verifica estensione file
                    is_zip = '.zip' in normalized_link.lower()
                    extension = '.zip' if is_zip else '.json'
                    
                    if not filename.endswith(extension):
                        filename += extension
                    
                    dest_path = os.path.join(self.session_dir, filename)
                    
                    if should_download(dest_path, force=force_download):
                        # Parametri di download dalla config
                        sha256 = download_file(
                            normalized_link,
                            dest_path,
                            chunk_size=self.config.get('chunk_size', 1048576),
                            max_retries=self.config.get('max_retries', 5),
                            backoff=self.config.get('retry_backoff', 2),
                            timeout=self.config.get('timeout', 60),
                            logger=self.logger
                        )
                        
                        if sha256:
                            print(f"✓ Scaricato con successo: {filename}")
                            
                            # Processa il file scaricato (estrai se ZIP)
                            if extract_zip and is_zip:
                                result = process_downloaded_file(dest_path, self.session_dir, self.logger)
                                if result['is_zip']:
                                    extract_count = len(result.get('extracted_files', []))
                                    extracted_files += extract_count
                                    print(f"  ↳ Estratti {extract_count} file da {filename}")
                            
                            successfully_downloaded += 1
                        else:
                            print(f"✗ Download fallito: {filename}")
                            failed_downloads += 1
                    else:
                        print(f"⊙ File già presente: {filename}")
                        skipped_downloads += 1
                        
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
            print(f"↳ File estratti da ZIP: {extracted_files}")
            
            # Salva report
            if self.config.get('save_report', True):
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
            dirs = [d for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d)) and d != 'reports']
            
            if not dirs:
                print("Nessuna cartella trovata in", base_dir)
                input("\nPremi INVIO per tornare al menu principale...")
                return
                
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
            except:
                print("Scelta non valida, uso cartella principale")
                check_dir = base_dir
            
            print(f"\nVerifica file in: {check_dir}")
            
            # Conta i file JSON e ZIP
            json_files = [f for f in os.listdir(check_dir) if f.endswith('.json')]
            zip_files = [f for f in os.listdir(check_dir) if f.endswith('.zip')]
            
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
            
            # Verifica file JSON
            for i, filename in enumerate(json_files + zip_files):
                file_path = os.path.join(check_dir, filename)
                print(f"[{i+1}/{total_files}] Verifica di {filename}...")
                
                if verify_file_integrity(file_path):
                    print(f"✓ Valido: {filename}")
                    valid_files += 1
                else:
                    print(f"✗ Invalido o danneggiato: {filename}")
                    invalid_files += 1
            
            print("\n" + "=" * 60)
            print(f"VERIFICA COMPLETATA")
            print("=" * 60)
            print(f"✓ File validi: {valid_files}")
            print(f"✗ File invalidi: {invalid_files}")
            
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