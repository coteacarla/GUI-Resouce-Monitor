"""Unit tests for ResourceMonitor and data collection."""
import unittest
import time
import os
from main import ResourceMonitor, SystemMetrics
from database import MetricsDatabase


class TestResourceMonitor(unittest.TestCase):
    """Test ResourceMonitor functionality."""
    
    def setUp(self):
        """Set up test monitor."""
        if os.path.exists("test.db"):
            os.remove("test.db")
        self.monitor = ResourceMonitor(interval=0.05, max_data_points=10)
        self.monitor.db = MetricsDatabase("test.db")
    
    def tearDown(self):
        """Clean up."""
        if self.monitor.running:
            self.monitor.stop()
        if os.path.exists("test.db"):
            os.remove("test.db")
    
    def test_initialization(self):
        """Test monitor initializes correctly."""
        self.assertEqual(self.monitor.interval, 0.05)
        self.assertEqual(self.monitor.max_data_points, 10)
        self.assertFalse(self.monitor.running)
        self.assertIsNotNone(self.monitor.db)
    
    def test_start_stop(self):
        """Test starting and stopping monitor."""
        self.monitor.start()
        self.assertTrue(self.monitor.running)
        time.sleep(0.2)
        self.monitor.stop()
        self.assertFalse(self.monitor.running)
    
    def test_collect_metrics(self):
        """Test metric collection returns valid data."""
        metrics = self.monitor._collect_metrics()
        self.assertIsNotNone(metrics)
        self.assertIsInstance(metrics, SystemMetrics)
        self.assertGreaterEqual(metrics.cpu_percent, 0)
        self.assertLessEqual(metrics.cpu_percent, 100)
    
    def test_data_collection(self):
        """Test continuous data collection."""
        self.monitor.start()
        time.sleep(0.3)
        data = self.monitor.get_latest_data()
        self.assertGreater(len(data), 0)
        self.assertLessEqual(len(data), 10)
    
    def test_deque_max_size(self):
        """Test that deque respects maximum data points."""
        self.monitor.start()
        time.sleep(0.6)
        data = self.monitor.get_latest_data()
        self.assertLessEqual(len(data), self.monitor.max_data_points)
    
    def test_statistics(self):
        """Test statistics calculation."""
        self.monitor.start()
        time.sleep(0.3)
        stats = self.monitor.get_statistics()
        self.assertIn('cpu', stats)
        self.assertIn('memory', stats)
    
    def test_empty_statistics(self):
        """Test statistics on empty data."""
        stats = self.monitor.get_statistics()
        self.assertEqual(stats, {})
    
    def test_stop_without_start(self):
        """Test stopping monitor that wasn't started."""
        try:
            self.monitor.stop()
            self.assertFalse(self.monitor.running)
        except Exception:
            self.fail("Stop without start raised exception")
    
    def test_stress_high_frequency(self):
        """Test monitor handles high-frequency collection."""
        self.monitor.interval = 0.01
        self.monitor.max_data_points = 50
        self.monitor.start()
        time.sleep(0.6)
        data = self.monitor.get_latest_data()
        self.assertLessEqual(len(data), 50)
        self.assertGreater(len(data), 0)
    
    def test_metrics_accuracy(self):
        """Test metric values are within valid ranges."""
        self.monitor.start()
        time.sleep(0.2)
        data = self.monitor.get_latest_data()
        for metric in data:
            self.assertGreaterEqual(metric.cpu_percent, 0)
            self.assertLessEqual(metric.cpu_percent, 100)
    
    def test_cache_validity(self):
        """Test statistics cache mechanism exists."""
        self.monitor.start()
        time.sleep(0.3)
        
        self.monitor.get_statistics()
        cached_stats = self.monitor._stats_cache
        
        if cached_stats:
            self.assertIsNotNone(cached_stats)
            self.assertIn('cpu', cached_stats)


if __name__ == '__main__':
    unittest.main()
