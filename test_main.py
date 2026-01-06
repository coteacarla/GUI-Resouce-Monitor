"""Unit tests for ResourceMonitor and data collection."""
import unittest
import time
import os
from main import ResourceMonitor, SystemMetrics
from database import MetricsDatabase


class TestSystemMetrics(unittest.TestCase):
    """Test SystemMetrics data class."""
    
    def test_metrics_creation(self):
        """Test creating SystemMetrics object."""
        m = SystemMetrics("2025-01-01 12:00:00", 50.0, 60.0, 70.0, 100.0, 200.0)
        self.assertEqual(m.cpu_percent, 50.0)
        self.assertEqual(m.memory_percent, 60.0)
        self.assertEqual(m.disk_percent, 70.0)


class TestResourceMonitor(unittest.TestCase):
    """Test ResourceMonitor functionality."""
    
    def setUp(self):
        """Set up test monitor."""
        if os.path.exists("test.db"):
            os.remove("test.db")
        self.monitor = ResourceMonitor(interval=0.1, max_data_points=10)
        self.monitor.db = MetricsDatabase("test.db")
    
    def tearDown(self):
        """Clean up."""
        if self.monitor.running:
            self.monitor.stop()
        if os.path.exists("test.db"):
            os.remove("test.db")
    
    def test_initialization(self):
        """Test monitor initializes correctly."""
        self.assertEqual(self.monitor.interval, 0.1)
        self.assertEqual(self.monitor.max_data_points, 10)
        self.assertFalse(self.monitor.running)
    
    def test_start_stop(self):
        """Test starting and stopping monitor."""
        self.monitor.start()
        self.assertTrue(self.monitor.running)
        time.sleep(0.3)
        self.monitor.stop()
        self.assertFalse(self.monitor.running)
    
    def test_collect_metrics(self):
        """Test metric collection."""
        metrics = self.monitor._collect_metrics()
        self.assertIsInstance(metrics, SystemMetrics)
        self.assertGreaterEqual(metrics.cpu_percent, 0)
        self.assertLessEqual(metrics.cpu_percent, 100)
    
    def test_data_collection(self):
        """Test continuous data collection."""
        self.monitor.start()
        time.sleep(0.5)
        data = self.monitor.get_latest_data()
        self.assertGreater(len(data), 0)
        self.assertLessEqual(len(data), 10)
    
    def test_statistics(self):
        """Test statistics calculation."""
        self.monitor.start()
        time.sleep(0.5)
        stats = self.monitor.get_statistics()
        self.assertIn('cpu', stats)
        self.assertIn('memory', stats)
        self.assertIn('disk', stats)
        self.assertIn('network', stats)


if __name__ == '__main__':
    unittest.main()
