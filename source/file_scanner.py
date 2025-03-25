import os
import hashlib
import concurrent.futures
import logging
from typing import Dict, List, Tuple, Optional
import pickle
import time

class FileScanner:
    def __init__(self, cache_file: str = ".file_cache"):
        self.cache_file = cache_file
        self.hash_cache: Dict[str, str] = {}
        self.load_cache()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count())
        
    def load_cache(self):
      
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'rb') as f:
                    self.hash_cache = pickle.load(f)
        except Exception as e:
            logging.warning(f"Impossible de charger le cache: {e}")
            self.hash_cache = {}

    def save_cache(self):
    
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.hash_cache, f)
        except Exception as e:
            logging.warning(f"Impossible de sauvegarder le cache: {e}")

    def calculate_file_hash(self, file_path: str, chunk_size: int = 8192) -> Optional[str]:
  
        try:

            mtime = os.path.getmtime(file_path)
            cache_key = f"{file_path}:{mtime}"
            
            if cache_key in self.hash_cache:
                return self.hash_cache[cache_key]
            
 
            hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            
            file_hash = hasher.hexdigest()
            self.hash_cache[cache_key] = file_hash
            return file_hash
            
        except Exception as e:
            logging.warning(f"Erreur lors du calcul du hash pour {file_path}: {e}")
            return None

    def scan_directory(self, path: str) -> List[Dict]:

        files = []
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    if entry.is_file():
                        files.append({
                            'path': entry.path,
                            'size': entry.stat().st_size,
                            'mtime': entry.stat().st_mtime
                        })
        except Exception as e:
            logging.error(f"Erreur lors du scan du dossier {path}: {e}")
        return files

    def parallel_scan(self, root_path: str, callback=None) -> Tuple[List[Dict], int]:
        all_files = []
        total_size = 0
        dirs_to_scan = []


        for root, dirs, _ in os.walk(root_path):
            dirs_to_scan.append(root)

     
        futures = []
        for dir_path in dirs_to_scan:
            future = self.executor.submit(self.scan_directory, dir_path)
            futures.append(future)

    
        completed = 0
        total_dirs = len(futures)
        
        for future in concurrent.futures.as_completed(futures):
            try:
                files = future.result()
                all_files.extend(files)
                total_size += sum(f['size'] for f in files)
                
                completed += 1
                if callback:
                    progress = (completed / total_dirs) * 100
                    callback(progress)
                    
            except Exception as e:
                logging.error(f"Erreur lors du scan parallèle: {e}")

   
        self.save_cache()
        
        return all_files, total_size

    def find_duplicates(self, files: List[Dict], callback=None) -> Dict[str, List[Dict]]:
      
        hash_groups = {}
        total_files = len(files)
        
        def process_file(index: int, file: Dict) -> Tuple[int, Optional[str], Dict]:
            file_hash = self.calculate_file_hash(file['path'])
            return index, file_hash, file

      
        futures = []
        for i, file in enumerate(files):
            future = self.executor.submit(process_file, i, file)
            futures.append(future)

 
        completed = 0
        for future in concurrent.futures.as_completed(futures):
            try:
                index, file_hash, file = future.result()
                if file_hash:
                    if file_hash in hash_groups:
                        hash_groups[file_hash].append(file)
                    else:
                        hash_groups[file_hash] = [file]
                
                completed += 1
                if callback:
                    progress = (completed / total_files) * 100
                    callback(progress)
                    
            except Exception as e:
                logging.error(f"Erreur lors de la recherche des doublons: {e}")

      
        return {h: files for h, files in hash_groups.items() if len(files) > 1}

    def get_file_stats(self, files: List[Dict]) -> List[Dict]:
        stats = {}
        for file in files:
            _, ext = os.path.splitext(file['path'])
            ext = ext.lower() if ext else 'sans extension'
            
            if ext in stats:
                stats[ext]['count'] += 1
                stats[ext]['size'] += file['size']
            else:
                stats[ext] = {
                    'type': ext,
                    'count': 1,
                    'size': file['size']
                }
        
        return sorted(stats.values(), key=lambda x: x['size'], reverse=True) 