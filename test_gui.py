"""Integration tests for GUI data handling."""
import unittest
import time
import os
import tempfile
from main import ResourceMonitor


class TestGUIIntegration(unittest.TestCase):
    """Test GUI data integration."""
    
    def setUp(self):
        """Set up test monitor with temporary database."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_gui.db")
        
        self.monitor = ResourceMonitor(interval=0.05, max_data_points=20)
        self.monitor.db.db_path = self.test_db_path
        self.monitor.db.init_db()
    
    def tearDown(self):
        """Clean up."""
        if self.monitor.running:
            self.monitor.stop()
        time.sleep(0.1)
        try:
            if os.path.exists(self.test_db_path):
                os.remove(self.test_db_path)
            if os.path.exists(self.temp_dir):
                os.rmdir(self.temp_dir)
        except Exception:
            pass
    
    def test_data_format_for_display(self):
        """Test data is in correct format for GUI."""
        self.monitor.start()
        time.sleep(0.2)
        data = self.monitor.get_latest_data()
        stats = self.monitor.get_statistics()
        self.assertIsInstance(data, list)
        self.assertIsInstance(stats, dict)
    
    def test_statistics_structure(self):
        """Test statistics have correct structure."""
        self.monitor.start()
        time.sleep(0.2)
        stats = self.monitor.get_statistics()
        if stats:
            self.assertIn('cpu', stats)
            if stats['cpu']:
                self.assertIn('current', stats['cpu'])
                self.assertIn('avg', stats['cpu'])
    
    def test_graph_data_format(self):
        """Test data format for graphs."""
        self.monitor.start()
        time.sleep(0.2)
        data = self.monitor.get_latest_data()
        if data:
            cpu = [d.cpu_percent for d in data]
            mem = [d.memory_percent for d in data]
            self.assertIsInstance(cpu, list)
            self.assertTrue(all(0 <= c <= 100 for c in cpu))
    
    def test_empty_data_handling(self):
        """Test handling of empty data before collection starts."""
        data = self.monitor.get_latest_data()
        stats = self.monitor.get_statistics()
        self.assertEqual(len(data), 0)
        self.assertEqual(stats, {})
    
    def test_data_consistency(self):
        """Test that data retrieved is internally consistent."""
        self.monitor.start()
        time.sleep(0.2)
        data = self.monitor.get_latest_data()
        stats = self.monitor.get_statistics()
        
        if data and stats:
            self.assertGreater(len(data), 0)
            self.assertIn('cpu', stats)


if __name__ == '__main__':
    unittest.main()
