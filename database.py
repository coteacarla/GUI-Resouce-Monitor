import sqlite3
import os
import logging
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class MetricsDatabase:
    """SQLite database for storing and retrieving system metrics.
    
    Features:
    - Timestamp-based queries with indexed lookups
    - Thread-safe operations
    - Automatic schema initialization
    """
    
    def __init__(self, db_path: str = "metrics.db"):
        """Initialize database connection."""
        if not db_path or not isinstance(db_path, str):
            raise ValueError("db_path must be a non-empty string")
        
        self.db_path = db_path
        self._lock = threading.Lock()
        self.init_db()
        logger.info(f"MetricsDatabase initialized at {db_path}")

    def init_db(self):
        """Initialize database schema."""
        try:
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
            logger.debug("Database schema initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database schema: {e}")
            raise

    def insert_metric(self, cpu: float, memory: float, disk: float, net_sent: float, net_recv: float) -> bool:
        """Insert a new metric record into the database."""
        try:
            with self._lock:
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
                return True
        except Exception as e:
            logger.error(f"Database insert error: {e}")
            return False

    def get_metrics_range(self, minutes: int = 60) -> list:
        """
        Retrieve metrics from the last N minutes.
        
        Args:
            minutes: Number of minutes of history to retrieve
            
        Returns:
            List of metric dictionaries, empty list on error
        """
        if minutes < 0:
            logger.warning("Negative minutes requested, returning empty list")
            return []
        
        try:
            with self._lock:
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
        except sqlite3.Error as e:
            logger.error(f"Database query error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during query: {e}", exc_info=True)
            return []
    
    def get_all_metrics(self) -> list:
        """
        Retrieve all metrics from the database.
        
        Returns:
            List of all metric dictionaries sorted by timestamp
            Empty list on error
        """
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM metrics ORDER BY timestamp ASC')
                rows = cursor.fetchall()
                conn.close()
                
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Database query error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during retrieval: {e}", exc_info=True)
            return []
    
    def get_metrics_count(self) -> int:
        """
        Get total number of metrics in database.
        
        Returns:
            Integer count of metrics, 0 on error
        """
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) FROM metrics')
                count = cursor.fetchone()[0]
                conn.close()
                
                return count
        except sqlite3.Error as e:
            logger.error(f"Database query error: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error getting count: {e}", exc_info=True)
            return 0
    
    def get_metrics_by_date_range(self, start_date: str, end_date: str) -> list:
        """
        Retrieve metrics within a date range.
        
        Args:
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            List of metric dictionaries within the date range
            Empty list on error or invalid input
        """
        for date in [start_date, end_date]:
            try:
                datetime.strptime(date, '%Y-%m-%d')
            except ValueError:
                logger.error(f"Invalid date format: {date}. Expected YYYY-MM-DD")
                return []
        
        try:
            with self._lock:
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
        except sqlite3.Error as e:
            logger.error(f"Database query error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during date range query: {e}", exc_info=True)
            return []

    def clear_all(self) -> bool:
        """
        Delete all metrics from the database.
        
        Warning: This action cannot be undone.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM metrics')
                conn.commit()
                conn.close()
                logger.warning("All metrics cleared from database")
                return True
        except sqlite3.Error as e:
            logger.error(f"Database error during clear: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during clear: {e}", exc_info=True)
            return False
    
    def get_database_size(self) -> int:
        """
        Get the size of the database file in bytes.
        
        Returns:
            Size in bytes, 0 if file doesn't exist
        """
        try:
            if os.path.exists(self.db_path):
                return os.path.getsize(self.db_path)
            return 0
        except Exception as e:
            logger.error(f"Error getting database size: {e}")
            return 0
