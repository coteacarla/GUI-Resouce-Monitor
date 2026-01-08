import psutil
import time
import threading
import logging
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from typing import List, Optional
from collections import deque
import statistics
from database import MetricsDatabase

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('resource_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


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
    """Monitor and track system resource usage with database storage and statistics.
    
    Features:
    - Efficient memory management with deque
    - Thread-safe data access
    - Statistics caching (0.5s duration)
    - Database persistence
    """
    
    def __init__(self, interval: float = 1.0, max_data_points: int = 60, disk_path: str = '/'):
        """Initialize the Resource Monitor."""
        if interval <= 0:
            raise ValueError("Interval must be positive")
        if max_data_points < 1:
            raise ValueError("max_data_points must be at least 1")
        
        self.interval = interval
        self.running = False
        self.max_data_points = max_data_points
        self.disk_path = disk_path
        self.data: deque = deque(maxlen=max_data_points)
        self._thread = None
        self._lock = threading.Lock()
        self._last_net_io = psutil.net_io_counters()
        self._stats_cache = None
        self._cache_time = 0
        self._cache_duration = 0.5 
        self.db = MetricsDatabase()
        
        logger.info(f"ResourceMonitor initialized: interval={interval}s, max_points={max_data_points}")

    def _collect_metrics(self) -> Optional[SystemMetrics]:
        """Collect current system metrics."""
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage(self.disk_path).percent
            
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
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return None

    def _run(self):
        """Main monitoring loop."""
        logger.info("Monitoring loop started")
        
        while self.running:
            try:
                metric = self._collect_metrics()
                if metric is None:
                    time.sleep(self.interval)
                    continue
                
                with self._lock:
                    self.data.append(metric)
                    self._stats_cache = None
                
                try:
                    self.db.insert_metric(
                        metric.cpu_percent,
                        metric.memory_percent,
                        metric.disk_percent,
                        metric.net_sent,
                        metric.net_recv
                    )
                except Exception as e:
                    logger.warning(f"Database insert failed: {e}")
                
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.interval)

    def start(self):
        """
        Start the monitoring thread.
        
        Begins background data collection if not already running.
        Logs informational message on successful start.
        """
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run, daemon=True, name="ResourceMonitor")
            self._thread.start()
            logger.info("ResourceMonitor started")
        else:
            logger.debug("ResourceMonitor already running")
    
    def stop(self):
        """
        Stop the monitoring thread gracefully.
        
        Gracefully halts background data collection and waits for thread completion.
        
        Raises:
            TimeoutError: If thread doesn't join within 5 seconds
        """
        if self.running:
            logger.info("Stopping ResourceMonitor...")
            self.running = False
            if self._thread:
                try:
                    self._thread.join(timeout=5)
                    if self._thread.is_alive():
                        logger.warning("Monitor thread did not stop within timeout")
                except Exception as e:
                    logger.error(f"Error stopping monitor: {e}")
            logger.info("ResourceMonitor stopped")

    def get_latest_data(self) -> List[SystemMetrics]:
        """
        Get the latest collected metrics with thread safety.
        
        Returns:
            List of recent SystemMetrics objects (up to max_data_points)
            Empty list if no data collected yet
        """
        try:
            with self._lock:
                return list(self.data)
        except Exception as e:
            logger.error(f"Error retrieving latest data: {e}")
            return []
    
    def get_statistics(self) -> dict:
        """
        Calculate statistics for collected metrics with caching optimization.
        
        Caches statistics for 0.5 seconds to reduce computation on frequent calls.
        
        Returns:
            Dictionary with per-resource statistics (current, avg, max, min)
            Empty dict if no data available
        """
        try:
            current_time = time.time()
            
            if self._stats_cache and (current_time - self._cache_time) < self._cache_duration:
                return self._stats_cache
            
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
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}", exc_info=True)
            return {}

    def get_historical_data(self, minutes: int = 60) -> List[dict]:
        """
        Retrieve historical metrics from database.
        
        Args:
            minutes: Number of minutes of history to retrieve (default: 60)
            
        Returns:
            List of metric records from database
            
        Raises:
            ValueError: If minutes is negative
        """
        if minutes < 0:
            raise ValueError("minutes must be non-negative")
        
        try:
            return self.db.get_metrics_range(minutes)
        except Exception as e:
            logger.error(f"Error retrieving historical data: {e}")
            return []
    
    def get_metrics_count(self) -> int:
        """
        Get total count of metrics stored in database.
        
        Returns:
            Total number of metric records in database
        """
        try:
            return self.db.get_metrics_count()
        except Exception as e:
            logger.error(f"Error getting metrics count: {e}")
            return 0
