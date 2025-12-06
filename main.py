import psutil
import time
import threading
from datetime import datetime
from dataclasses import dataclass
from typing import List
from collections import deque
import statistics


@dataclass
class SystemMetrics:
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    net_sent: float
    net_recv: float


class ResourceMonitor:
    
    def __init__(self, interval: float = 1.0, max_data_points: int = 60):
        self.interval = interval
        self.running = False
        self.max_data_points = max_data_points
        self.data: deque = deque(maxlen=max_data_points)
        self._thread = None
        self._lock = threading.Lock()
        self._last_net_io = psutil.net_io_counters()

    def _collect_metrics(self) -> SystemMetrics:
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        net_io = psutil.net_io_counters()

        sent_diff = net_io.bytes_sent - self._last_net_io.bytes_sent
        recv_diff = net_io.bytes_recv - self._last_net_io.bytes_recv
        self._last_net_io = net_io

        return SystemMetrics(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            cpu_percent=cpu,
            memory_percent=mem,
            disk_percent=disk,
            net_sent=sent_diff / 1024,  
            net_recv=recv_diff / 1024,  
        )

    def _run(self):
        while self.running:
            metric = self._collect_metrics()
            with self._lock:
                self.data.append(metric)
            time.sleep(self.interval)

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join()

    def get_latest_data(self) -> List[SystemMetrics]:
        with self._lock:
            return list(self.data)

    def get_statistics(self) -> dict:
        """Get statistics for all metrics"""
        with self._lock:
            data = list(self.data)
        
        if not data:
            return {}
        
        cpu_values = [d.cpu_percent for d in data]
        mem_values = [d.memory_percent for d in data]
        disk_values = [d.disk_percent for d in data]
        sent_values = [d.net_sent for d in data]
        recv_values = [d.net_recv for d in data]
        
        return {
            'cpu': {
                'current': cpu_values[-1],
                'avg': statistics.mean(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values),
            },
            'memory': {
                'current': mem_values[-1],
                'avg': statistics.mean(mem_values),
                'max': max(mem_values),
                'min': min(mem_values),
            },
            'disk': {
                'current': disk_values[-1],
                'avg': statistics.mean(disk_values),
                'max': max(disk_values),
                'min': min(disk_values),
            },
            'network': {
                'sent_current': sent_values[-1],
                'sent_avg': statistics.mean(sent_values),
                'recv_current': recv_values[-1],
                'recv_avg': statistics.mean(recv_values),
            }
        }
