import sqlite3
import os
from datetime import datetime
from pathlib import Path


class MetricsDatabase:
    def __init__(self, db_path="metrics.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO metrics (cpu_percent, memory_percent, disk_percent, net_sent, net_recv)
            VALUES (?, ?, ?, ?, ?)
        ''', (cpu, memory, disk, net_sent, net_recv))
        
        conn.commit()
        conn.close()
    
    def get_metrics_range(self, minutes=60):
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
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM metrics ORDER BY timestamp ASC')
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_metrics_count(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM metrics')
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def delete_old_metrics(self, days=30):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM metrics 
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        ''', (days,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted
    
    def export_to_csv(self, filename="metrics_export.csv"):
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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM metrics')
        conn.commit()
        conn.close()
