import sqlite3
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path


class MetricsDatabase:
    """SQLite database for storing and retrieving system metrics with time-based queries."""
    
    def __init__(self, db_path="metrics.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file (default: 'metrics.db')
        """
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """
        Initialize database schema.
        
        Creates metrics table with timestamp index if it doesn't exist.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_percent REAL,
                memory_percent REAL,
                disk_percent REAL,
                net_sent REAL,
                net_recv REAL
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics(timestamp)
        ''')
        
        conn.commit()
        conn.close()

    def insert_metric(self, cpu, memory, disk, net_sent, net_recv):
        """
        Insert a new metric record into the database.
        
        Args:
            cpu: CPU usage percentage
            memory: Memory usage percentage
            disk: Disk usage percentage
            net_sent: Network bytes sent since last collection
            net_recv: Network bytes received since last collection
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        tz = timezone(timedelta(hours=3))
        timestamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT INTO metrics (timestamp, cpu_percent, memory_percent, disk_percent, net_sent, net_recv)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (timestamp, cpu, memory, disk, net_sent, net_recv))
        
        conn.commit()
        conn.close()

    def get_metrics_range(self, minutes=60):
        """
        Retrieve metrics from the last N minutes.
        
        Args:
            minutes: Number of minutes of history to retrieve
            
        Returns:
            List of metric dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM metrics 
            WHERE timestamp >= datetime('now', '-' || ? || ' minutes')
            ORDER BY timestamp ASC
        ''', (minutes,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_all_metrics(self):
        """
        Retrieve all metrics from the database.
        
        Returns:
            List of all metric dictionaries sorted by timestamp
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM metrics ORDER BY timestamp ASC')
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_metrics_count(self):
        """
        Get total number of metrics in database.
        
        Returns:
            Integer count of metrics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM metrics')
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def get_metrics_by_date_range(self, start_date, end_date):
        """
        Retrieve metrics within a date range.
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            List of metric dictionaries within the date range
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM metrics 
            WHERE timestamp >= ? AND timestamp < datetime(?, '+1 day')
            ORDER BY timestamp ASC
        ''', (start_date, end_date))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    
    def export_to_csv(self, filename="metrics_export.csv"):
        """
        Export all metrics to a CSV file.
        
        Args:
            filename: Output CSV filename (default: 'metrics_export.csv')
            
        Returns:
            True if export successful, False if no data available
        """
        import csv
        
        metrics = self.get_all_metrics()
        
        if not metrics:
            return False
        
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=metrics[0].keys())
            writer.writeheader()
            writer.writerows(metrics)
        
        return True

    def clear_all(self):
        """
        Delete all metrics from the database.
        
        Warning: This action cannot be undone.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM metrics')
        conn.commit()
        conn.close()
