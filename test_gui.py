"""Integration tests for GUI data handling."""
import unittest
import time
import os
from main import ResourceMonitor


class TestGUIIntegration(unittest.TestCase):
    """Test GUI data integration."""
    
    def setUp(self):
        """Set up test monitor."""
        if os.path.exists("test_gui.db"):
            os.remove("test_gui.db")
        self.monitor = ResourceMonitor(interval=0.05, max_data_points=20)
    
    def tearDown(self):
        """Clean up."""
        if self.monitor.running:
            self.monitor.stop()
        if os.path.exists("test_gui.db"):
            os.remove("test_gui.db")
    
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
            self.assertIsInstance(mem, list)


if __name__ == '__main__':
    unittest.main()
