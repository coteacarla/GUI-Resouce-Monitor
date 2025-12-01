import psutil
import time
import threading
from datetime import datetime
from dataclasses import dataclass
from typing import List


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
        self.data: List[SystemMetrics] = []
        self._thread = None
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
            self.data.append(metric)
            if len(self.data) > self.max_data_points:
                self.data.pop(0)
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
        return list(self.data)
