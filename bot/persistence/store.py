import duckdb
import os
import pandas as pd
import time
from datetime import datetime

class PersistenceManager:
    def __init__(self, db_path="output/applications.db", csv_path=None, max_retries=15, retry_delay=3.0):
        self.db_path = db_path
        self.csv_path = csv_path
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.conn = None
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                self.conn = duckdb.connect(self.db_path)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS applications (
                        job_id VARCHAR PRIMARY KEY,
                        title VARCHAR,
                        company VARCHAR,
                        status VARCHAR,
                        attempted_at TIMESTAMP,
                        result VARCHAR,
                        job_link VARCHAR,
                        candidate_name VARCHAR
                    )
                """)
                self.conn.execute("""
                    CREATE TABLE IF NOT EXISTS selectors (
                        key VARCHAR PRIMARY KEY,
                        data JSON,
                        updated_at TIMESTAMP
                    )
                """)
                return
            except Exception as e:
                last_error = e
                msg = str(e).lower()
                locked = any(k in msg for k in [
                    "used by another process",
                    "cannot access the file",
                    "database is locked",
                    "io error"
                ])

                if locked and attempt < self.max_retries:
                    print(
                        f"Database is locked (attempt {attempt}/{self.max_retries}). "
                        f"Retrying in {self.retry_delay}s..."
                    )
                    time.sleep(self.retry_delay)
                    continue
                break

        raise RuntimeError(
            f"Unable to open database '{self.db_path}'. "
            f"It may be locked by another process (e.g., DB viewer/editor). "
            f"Close programs using the DB and retry. Original error: {last_error}"
        )

    def save_selectors(self, selectors_dict):
        """
        Saves a dictionary of selectors to the database.
        Format: { "key": [("STRATEGY", "VALUE"), ...] }
        """
        import json
        for key, value in selectors_dict.items():
            self.conn.execute("""
                INSERT OR REPLACE INTO selectors (key, data, updated_at)
                VALUES (?, ?, ?)
            """, [key, json.dumps(value), datetime.now()])
        self.conn.commit()

    def load_selectors(self):
        """
        Loads all selectors from the database.
        Returns format: { "key": [["STRATEGY", "VALUE"], ...] }
        """
        import json
        results = self.conn.execute("SELECT key, data FROM selectors").fetchall()
        return {row[0]: json.loads(row[1]) for row in results}

    def is_applied(self, job_id):
        result = self.conn.execute("SELECT 1 FROM applications WHERE job_id = ?", [job_id]).fetchone()
        return result is not None

    def log_application(self, job_id, title, company, status, result, job_link, candidate_name):
        self.conn.execute("""
            INSERT OR REPLACE INTO applications 
            (job_id, title, company, status, attempted_at, result, job_link, candidate_name)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, [job_id, title, company, status, datetime.now(), result, job_link, candidate_name])
        self.conn.commit()

        # CSV Logging
        if self.csv_path and status == "Success":
            try:
                import csv
                file_exists = os.path.isfile(self.csv_path)
                os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
                
                with open(self.csv_path, mode='a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(["Timestamp", "JobID", "Job Title", "Company", "Result", "Job Link", "Candidate"])
                    
                    writer.writerow([
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        job_id, title, company, result, job_link, candidate_name
                    ])
            except Exception as e:
                print(f"Error writing to CSV: {e}")

    def close(self):
        if self.conn:
            self.conn.close()

    def get_application_count_today(self, candidate_name):
        today = datetime.now().strftime('%Y-%m-%d')
        result = self.conn.execute("""
            SELECT COUNT(*) FROM applications 
            WHERE candidate_name = ? AND status = 'Success' 
            AND CAST(attempted_at AS DATE) = ?
        """, [candidate_name, today]).fetchone()
        return result[0] if result else 0

    def migrate_from_csv(self, csv_path, candidate_name):
        if not os.path.exists(csv_path):
            return
        
        try:
            df = pd.read_csv(csv_path)
            # Map CSV columns to DB columns if they match your current schema
            # CSV schema: Timestamp | JobID | Job Title | Company | Attempted | Result
            for _, row in df.iterrows():
                try:
                    self.conn.execute("""
                        INSERT OR IGNORE INTO applications 
                        (job_id, title, company, status, attempted_at, result, candidate_name)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, [
                        str(row['JobID']), 
                        row['Job Title'], 
                        row['Company'], 
                        'Success' if row['Result'] == 'Success' else 'Failed',
                        datetime.strptime(row['Timestamp'], '%Y-%m-%d %H:%M:%S'),
                        row['Result'],
                        candidate_name
                    ])
                except:
                    continue
        except Exception as e:
            print(f"Migration error: {e}")
