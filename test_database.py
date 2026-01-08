"""Integration tests for MetricsDatabase."""
import unittest
import os
import time
import threading
from database import MetricsDatabase


class TestMetricsDatabase(unittest.TestCase):
    """Test database operations."""
    
    def setUp(self):
        """Set up test database."""
        self.db_path = "test_db.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = MetricsDatabase(self.db_path)
    
    def tearDown(self):
        """Clean up."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_database_creation(self):
        """Test database file is created."""
        self.assertTrue(os.path.exists(self.db_path))
    
    def test_insert_metric(self):
        """Test inserting a single metric."""
        self.db.insert_metric(50.0, 60.0, 70.0, 100.0, 200.0)
        count = self.db.get_metrics_count()
        self.assertEqual(count, 1)
    
    def test_multiple_inserts(self):
        """Test multiple inserts."""
        for i in range(10):
            self.db.insert_metric(50+i, 60+i, 70+i, 100+i, 200+i)
        count = self.db.get_metrics_count()
        self.assertEqual(count, 10)
    
    def test_get_all_metrics(self):
        """Test retrieving all metrics."""
        self.db.insert_metric(50, 60, 70, 100, 200)
        self.db.insert_metric(55, 65, 75, 110, 210)
        metrics = self.db.get_all_metrics()
        self.assertEqual(len(metrics), 2)
        self.assertIn('cpu_percent', metrics[0])
    
    def test_get_metrics_range(self):
        """Test time-based retrieval."""
        self.db.insert_metric(50, 60, 70, 100, 200)
        time.sleep(0.1)
        self.db.insert_metric(55, 65, 75, 110, 210)
        recent = self.db.get_metrics_range(minutes=60)
        self.assertGreater(len(recent), 0)
    
    def test_clear_all(self):
        """Test clearing database."""
        for i in range(5):
            self.db.insert_metric(50+i, 60+i, 70+i, 100+i, 200+i)
        self.db.clear_all()
        count = self.db.get_metrics_count()
        self.assertEqual(count, 0)
    
    def test_persistence(self):
        """Test data persists across connections."""
        self.db.insert_metric(50, 60, 70, 100, 200)
        self.db.insert_metric(55, 65, 75, 110, 210)
        db2 = MetricsDatabase(self.db_path)
        count = db2.get_metrics_count()
        self.assertEqual(count, 2)
    
    def test_large_dataset(self):
        """Test handling 200+ metrics."""
        for i in range(200):
            self.db.insert_metric(50, 60, 70, 100+i, 200+i)
        count = self.db.get_metrics_count()
        self.assertEqual(count, 200)
        all_data = self.db.get_all_metrics()
        self.assertEqual(len(all_data), 200)
    
    def test_concurrent_writes(self):
        """Test thread-safe concurrent inserts."""
        def insert_batch(start, end):
            for i in range(start, end):
                self.db.insert_metric(50, 60, 70, 100, 200)
        
        threads = [
            threading.Thread(target=insert_batch, args=(0, 50)),
            threading.Thread(target=insert_batch, args=(50, 100))
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        count = self.db.get_metrics_count()
        self.assertEqual(count, 100)


if __name__ == '__main__':
    unittest.main()
