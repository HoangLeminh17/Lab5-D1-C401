import csv
import mysql.connector
from pathlib import Path
import os
import json


# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'password',  # Change this to your mysql root password
}

DB_NAME = 'project'
CSV_FILE = 'app/data/drugs.csv'


def init_mysql_database():
    try:
        # Connect without database first
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Create database and select it
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute(f"USE {DB_NAME}")

        # Create drugs table using TEXT to prevent 'Data too long for column' errors
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drugs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                brand_name TEXT NOT NULL,
                generic_name TEXT NOT NULL,
                manufacturer_name TEXT,
                product_ndc VARCHAR(255),
                route TEXT,
                product_type VARCHAR(255),
                rxcui VARCHAR(255),
                stock_quantity INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        print(f"[Database] Successfully created database '{DB_NAME}' and 'drugs' table.")
        return conn

    except mysql.connector.Error as err:
        print(f"[Error] MySQL connection failed: {err}")
        return None

def import_csv_to_mysql(conn):
    try:
        if not Path(CSV_FILE).exists():
            print(f"[Error] {CSV_FILE} not found")
            return False

        cursor = conn.cursor()

        # Check existing records
        cursor.execute("SELECT COUNT(*) FROM drugs")
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            print(f"[Info] MySQL database already contains {existing_count} records")
            cursor.execute("TRUNCATE TABLE drugs")
            conn.commit()
            print("[Database] Cleared existing records gracefully")

        # Read CSV and Insert
        with open(CSV_FILE, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

            insert_query = """
                INSERT INTO drugs
                (brand_name, generic_name, manufacturer_name, product_ndc, route, product_type, rxcui, stock_quantity)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            data_tuples = []
            for row in rows:
                data_tuples.append((
                    row.get("brand_name", "").strip(),
                    row.get("generic_name", "").strip(),
                    row.get("manufacturer_name", "").strip(),
                    row.get("product_ndc", "").strip(),
                    row.get("route", "").strip(),
                    row.get("product_type", "").strip(),
                    row.get("rxcui", "").strip(),
                    int(row.get("stock_quantity", 0) if row.get("stock_quantity") else 0)
                ))

            # Batch insert for performance
            cursor.executemany(insert_query, data_tuples)
            conn.commit()
            
            print(f"[Database] Successfully imported {len(rows)} records into MySQL")

        return True

    except Exception as e:
        print(f"[Error] Import to MySQL failed: {e}")
        return False
    finally:
        if cursor:
            cursor.close()

def main():
    print("=" * 60)
    print("MySQL Drug Database Migration Tool")
    print("=" * 60)

    conn = init_mysql_database()
    if not conn:
        print("Failed to initialize database.")
        sys.exit(1)

    import_csv_to_mysql(conn)
    
    if conn.is_connected():
        conn.close()
        print("[System] MySQL connection closed.")

if __name__ == "__main__":
    import sys
    main()
