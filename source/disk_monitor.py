import psutil
import os
import time
import logging
import threading
from typing import Dict, List, Optional, Callable
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import pandas as pd

class DiskMonitor:
    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.health_data: List[Dict] = []
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.update_interval = 60  
        self.last_update = 0
        self.callback = None
        self.usage_history = []
        self.io_history = []

    def get_disk_health(self, path: str) -> Optional[Dict]:
   
        if not os.path.exists(path):
            logging.error(f"Le chemin n'existe pas: {path}")
            return None
            
        try:
            current_time = time.time()
            if current_time - self.last_update < self.update_interval:
                return self.health_data[-1] if self.health_data else None

            usage = psutil.disk_usage(path)
            
            io_counters = psutil.disk_io_counters()
            

            temp = None
            try:
                sensors = psutil.sensors_temperatures()
                if 'nvme' in sensors: 
                    temp = sensors['nvme'][0].current
                elif 'coretemp' in sensors:  
                    temp = sensors['coretemp'][0].current
            except:
                pass

            health_data = {
                'timestamp': current_time,
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': usage.percent,
                'read_bytes': io_counters.read_bytes if io_counters else 0,
                'write_bytes': io_counters.write_bytes if io_counters else 0,
                'temperature': temp
            }

            self.health_data.append(health_data)
            if len(self.health_data) > self.history_size:
                self.health_data.pop(0)

            self.last_update = current_time
            return health_data

        except Exception as e:
            logging.error(f"Erreur lors de la récupération de la santé du disque: {e}")
            return None

    def start_monitoring(self, path: str, callback: Callable = None):

        self.monitoring = True
        self.callback = callback
        self.path = path
        
        def monitor_task():
            while self.monitoring:
                try:
                    health_data = self.get_disk_health(path)
                    if health_data:
                      
                        self.usage_history.append({
                            'time': datetime.now(),
                            'usage': health_data['percent']
                        })
                        
                 
                        io_rate = (health_data['read_bytes'] + health_data['write_bytes']) / 1024 / 1024
                        self.io_history.append({
                            'time': datetime.now(),
                            'rate': io_rate
                        })
                        
              
                        cutoff = datetime.now() - timedelta(hours=24)
                        self.usage_history = [entry for entry in self.usage_history if entry['time'] > cutoff]
                        self.io_history = [entry for entry in self.io_history if entry['time'] > cutoff]
                        
                        if self.callback:
                            self.callback(health_data)
                    time.sleep(self.update_interval)
                except Exception as e:
                    logging.error(f"Erreur dans la tâche de monitoring: {e}")
                    time.sleep(self.update_interval)

        self.monitor_thread = threading.Thread(target=monitor_task, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self):
    
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)

    def get_usage_trend(self, days: int = 7) -> pd.DataFrame:
       
        if not self.health_data:
            return pd.DataFrame()

        df = pd.DataFrame(self.health_data)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('datetime', inplace=True)
        
 
        return df.resample('1H').mean()

    def generate_health_report(self, path: str) -> Dict:
        try:
            current = self.get_disk_health(path)
            if not current:
                return {}

            df = self.get_usage_trend()
            if not df.empty:
                usage_trend = df['percent'].diff().mean()
                io_trend = (df['write_bytes'].diff().mean() + df['read_bytes'].diff().mean()) / 2
            else:
                usage_trend = 0
                io_trend = 0

            health_status = "Bon"
            if current['percent'] > 90 or usage_trend > 5:
                health_status = "Critique"
            elif current['percent'] > 80 or usage_trend > 2:
                health_status = "Attention"

            return {
                'status': health_status,
                'usage_percent': current['percent'],
                'free_space': current['free'],
                'usage_trend': usage_trend,
                'io_activity': io_trend,
                'temperature': current.get('temperature'),
                'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        except Exception as e:
            logging.error(f"Erreur lors de la génération du rapport: {e}")
            return {}

    def plot_usage_history(self, fig: plt.Figure):
       
        if not self.health_data:
            return

        df = pd.DataFrame(self.health_data)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')


        fig.clear()


        gs = fig.add_gridspec(2, 2)
        ax1 = fig.add_subplot(gs[0, 0])
        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[1, :])

        ax1.plot(df['datetime'], df['percent'])
        ax1.set_title('Utilisation du disque')
        ax1.set_ylabel('Pourcentage')
        ax1.tick_params(axis='x', rotation=45)


        ax2.plot(df['datetime'], df['read_bytes'] / 1e6, label='Lecture')
        ax2.plot(df['datetime'], df['write_bytes'] / 1e6, label='Écriture')
        ax2.set_title('Activité E/S')
        ax2.set_ylabel('MB')
        ax2.legend()
        ax2.tick_params(axis='x', rotation=45)

    
        if 'temperature' in df.columns and df['temperature'].notna().any():
            ax3.plot(df['datetime'], df['temperature'])
            ax3.set_title('Température')
            ax3.set_ylabel('°C')
            ax3.tick_params(axis='x', rotation=45)
        else:
            ax3.text(0.5, 0.5, 'Données de température non disponibles',
                    horizontalalignment='center',
                    verticalalignment='center')

        fig.tight_layout()
        return fig 

    def get_usage_history(self):
        return self.usage_history
        
    def get_io_history(self):
        return self.io_history 