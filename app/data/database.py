import csv
import sqlite3
from pathlib import Path

DB_FILE = "app/data/drugs.db"
CSV_FILE = "app/data/drugs.csv"


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
                        int(row.get("stock_quantity", 0) if row.get("stock_quantity") else 0),
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


def get_all_drugs(limit=None):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if limit:
            cursor.execute("SELECT * FROM drugs LIMIT ?", (limit,))
        else:
            cursor.execute("SELECT * FROM drugs")

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"[Error] Query failed: {e}")
        return []


def search_drugs_by_brand(brand_name):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM drugs WHERE brand_name LIKE ? COLLATE NOCASE",
            (f"%{brand_name}%",)
        )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"[Error] Search failed: {e}")
        return []


def search_drugs_by_generic(generic_name):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM drugs WHERE generic_name LIKE ? COLLATE NOCASE",
            (f"%{generic_name}%",)
        )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"[Error] Search failed: {e}")
        return []


def search_drugs_by_manufacturer(manufacturer_name):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM drugs WHERE manufacturer_name LIKE ? COLLATE NOCASE",
            (f"%{manufacturer_name}%",)
        )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"[Error] Search failed: {e}")
        return []


def get_drugs_by_route(route):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM drugs WHERE route = ? COLLATE NOCASE",
            (route,)
        )

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        print(f"[Error] Query failed: {e}")
        return []


def get_drug_by_ndc(product_ndc):
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM drugs WHERE product_ndc = ?", (product_ndc,))

        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None
    except sqlite3.Error as e:
        print(f"[Error] Query failed: {e}")
        return None


def get_database_stats():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM drugs")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM drugs WHERE stock_quantity = 0")
        zero_stock = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT route) FROM drugs WHERE route != ''")
        unique_routes = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT manufacturer_name) FROM drugs WHERE manufacturer_name != ''")
        unique_manufacturers = cursor.fetchone()[0]

        cursor.execute("SELECT AVG(stock_quantity) FROM drugs")
        avg_stock = cursor.fetchone()[0]

        conn.close()

        return {
            "total_records": total,
            "zero_stock_count": zero_stock,
            "unique_routes": unique_routes,
            "unique_manufacturers": unique_manufacturers,
            "average_stock": round(avg_stock, 2) if avg_stock else 0
        }
    except sqlite3.Error as e:
        print(f"[Error] Stats query failed: {e}")
        return {}


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
