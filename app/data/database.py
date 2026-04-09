import csv
import sqlite3
from pathlib import Path

DB_FILE = "drugs.db"
CSV_FILE = "drugs.csv"


def init_database():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS drugs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand_name TEXT NOT NULL,
                generic_name TEXT NOT NULL,
                manufacturer_name TEXT,
                product_ndc TEXT,
                route TEXT,
                product_type TEXT,
                rxcui TEXT,
                stock_quantity INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.commit()
        print("[Database] Table created/verified successfully")
        return conn

    except sqlite3.Error as e:
        print(f"[Error] Database initialization failed: {e}")
        return None


def import_csv_to_db():
    try:
        if not Path(CSV_FILE).exists():
            print(f"[Error] {CSV_FILE} not found")
            return False

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM drugs")
        existing_count = cursor.fetchone()[0]

        if existing_count > 0:
            print(f"[Info] Database already contains {existing_count} records")
            response = input("Do you want to clear and re-import? (yes/no): ").strip().lower()
            if response == "yes":
                cursor.execute("DELETE FROM drugs")
                conn.commit()
                print("[Database] Cleared existing records")
            else:
                conn.close()
                return True

        with open(CSV_FILE, "r", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)

            for row in rows:
                cursor.execute(
                    """
                    INSERT INTO drugs
                    (brand_name, generic_name, manufacturer_name, product_ndc, route, product_type, rxcui, stock_quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row.get("brand_name", "").strip(),
                        row.get("generic_name", "").strip(),
                        row.get("manufacturer_name", "").strip(),
                        row.get("product_ndc", "").strip(),
                        row.get("route", "").strip(),
                        row.get("product_type", "").strip(),
                        row.get("rxcui", "").strip(),
                        int(row.get("stock_quantity", 0)),
                    ),
                )

            conn.commit()
            print(f"[Database] Successfully imported {len(rows)} records")

        conn.close()
        return True

    except csv.Error as e:
        print(f"[Error] CSV reading failed: {e}")
        return False
    except sqlite3.Error as e:
        print(f"[Error] Database operation failed: {e}")
        return False
    except Exception as e:
        print(f"[Error] Unexpected error: {e}")
        return False


def main():
    print("=" * 60)
    print("Drug Database Setup")
    print("=" * 60)

    conn = init_database()
    if not conn:
        return False

    conn.close()

    print("\nImporting CSV data...")
    if not import_csv_to_db():
        return False

    print("\n[Success] Database ready to use")
    return True


if __name__ == "__main__":
    main()
