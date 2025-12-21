import psutil
import time
import threading
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import List
from collections import deque
import statistics
from database import MetricsDatabase


@dataclass
class SystemMetrics:
    """Data class representing a snapshot of system metrics at a point in time."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    net_sent: float
    net_recv: float


class ResourceMonitor:
    """Monitor and track system resource usage with database storage and statistics."""
    
   
    
    def __init__(self, interval: float = 1.0, max_data_points: int = 60):
        """
        Initialize the Resource Monitor.
        
        Args:
            interval: Collection interval in seconds (default: 1.0)
            max_data_points: Maximum data points to keep in memory (default: 60)
        """
        self.interval = interval
        self.running = False
        self.max_data_points = max_data_points
        self.data: deque = deque(maxlen=max_data_points)
        self._thread = None
        self._lock = threading.Lock()
        self._last_net_io = psutil.net_io_counters()
        self.db = MetricsDatabase()

    def _collect_metrics(self) -> SystemMetrics:
        """
        Collect current system metrics.
        
        Gathers CPU, memory, disk, and network usage data.
        Calculates network delta since last collection.
        
        Returns:
            SystemMetrics object with current system metrics
        """
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        net_io = psutil.net_io_counters()

        sent_diff = net_io.bytes_sent - self._last_net_io.bytes_sent
        recv_diff = net_io.bytes_recv - self._last_net_io.bytes_recv
        self._last_net_io = net_io
        
        tz = timezone(timedelta(hours=3))
        local_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")

        return SystemMetrics(
            timestamp=local_time,
            cpu_percent=cpu,
            memory_percent=mem,
            disk_percent=disk,
            net_sent=sent_diff / 1024,  
            net_recv=recv_diff / 1024,
        )

    def _run(self):
        """
        Main monitoring loop.
        
        Continuously collects metrics, stores in memory and database,
        and sleeps for the configured interval.
        """
        while self.running:
            metric = self._collect_metrics()
            with self._lock:
                self.data.append(metric)
            self.db.insert_metric(
                metric.cpu_percent,
                metric.memory_percent,
                metric.disk_percent,
                metric.net_sent,
                metric.net_recv
            )
            time.sleep(self.interval)

    def start(self):
        """
        Start the monitoring thread.
        
        Begins background data collection if not already running.
        """
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
    
    def stop(self):
        """
        Stop the monitoring thread.
        
        Gracefully halts background data collection.
        """
        self.running = False
        if self._thread:
            self._thread.join()

    def get_latest_data(self) -> List[SystemMetrics]:
        """
        Get the latest collected metrics.
        
        Returns:
            List of recent SystemMetrics objects (up to max_data_points)
        """
        with self._lock:
            return list(self.data)
    
    def get_statistics(self) -> dict:
        """
        Calculate statistics for collected metrics.
        
        Returns:
            Dictionary with per-resource statistics (current, avg, max, min)
        """
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

    def get_historical_data(self, minutes=60):
        """
        Retrieve historical metrics from database.
        
        Args:
            minutes: Number of minutes of history to retrieve
            
        Returns:
            List of metric records from database
        """
        return self.db.get_metrics_range(minutes)
    
    def export_history(self, filename="metrics_export.csv"):
        """
        Export all metrics to CSV file.
        
        Args:
            filename: Output CSV filename
            
        Returns:
            True if export successful, False otherwise
        """
        return self.db.export_to_csv(filename)

    def get_metrics_count(self):
        """
        Get total count of metrics stored in database.
        
        Returns:
            Total number of metric records
        """
        return self.db.get_metrics_count()
