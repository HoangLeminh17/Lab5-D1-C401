import csv
import json
import random
import requests

API_URL = "https://api.fda.gov/drug/label.json"
BATCH_SIZE = 100
TARGET_RECORDS = 1000
OUTPUT_FILE = "./app/data/drugs.csv"


def safe_get_first(value):
    if isinstance(value, list) and value:
        return str(value[0]).strip()
    if value is None:
        return ""
    return str(value).strip()


def get_product_ndc(openfda):
    return (
        safe_get_first(openfda.get("product_ndc", ""))
        or safe_get_first(openfda.get("package_ndc", ""))
        or safe_get_first(openfda.get("ndc_package_code", ""))
    )


def is_valid_record(record):
    return bool(record.get("brand_name", "").strip()) and bool(record.get("generic_name", "").strip())


def fetch_drug_data():
    all_drugs = []
    seen_ndc = set()
    skip = 0
    iteration = 0
    max_iterations = 200

    print("=" * 60)
    print("Starting OpenFDA drug data collection")
    print("=" * 60)

    while len(all_drugs) < TARGET_RECORDS and iteration < max_iterations:
        iteration += 1
        try:
            params = {"limit": BATCH_SIZE, "skip": skip}
            print(f"\n[Batch {iteration}] Fetching records {skip} to {skip + BATCH_SIZE}...")

            response = requests.get(API_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            if "results" not in data or not data["results"]:
                print("No more results available from API")
                break

            batch_count = 0
            for drug in data["results"]:
                if len(all_drugs) >= TARGET_RECORDS:
                    break

                openfda = drug.get("openfda", {}) if isinstance(drug.get("openfda", {}), dict) else {}

                brand_name = safe_get_first(openfda.get("brand_name", ""))
                generic_name = safe_get_first(openfda.get("generic_name", ""))
                manufacturer_name = safe_get_first(openfda.get("manufacturer_name", ""))
                product_ndc = get_product_ndc(openfda)
                route = safe_get_first(openfda.get("route", ""))
                product_type = safe_get_first(openfda.get("product_type", ""))
                rxcui = safe_get_first(openfda.get("rxcui", ""))

                if product_ndc and product_ndc in seen_ndc:
                    continue
                if product_ndc:
                    seen_ndc.add(product_ndc)

                record = {
                    "brand_name": brand_name,
                    "generic_name": generic_name,
                    "manufacturer_name": manufacturer_name,
                    "product_ndc": product_ndc,
                    "route": route,
                    "product_type": product_type,
                    "rxcui": rxcui,
                    "stock_quantity": 0
                }

                if not is_valid_record(record):
                    continue

                record["stock_quantity"] = random.randint(0, 100)
                all_drugs.append(record)
                batch_count += 1

            print(f"[Batch {iteration}] Added {batch_count} records | Total: {len(all_drugs)}/{TARGET_RECORDS}")
            skip += BATCH_SIZE

        except requests.exceptions.Timeout:
            print("Error: API request timed out")
            break
        except requests.exceptions.HTTPError as e:
            print(f"Error: HTTP error occurred - {e}")
            break
        except requests.exceptions.RequestException as e:
            print(f"Error: API request failed - {e}")
            break
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse JSON response - {e}")
            break
        except Exception as e:
            print(f"Error: Unexpected error - {e}")
            break

    if len(all_drugs) > TARGET_RECORDS:
        all_drugs = all_drugs[:TARGET_RECORDS]

    has_zero_stock = any(d["stock_quantity"] == 0 for d in all_drugs)
    if not has_zero_stock and all_drugs:
        all_drugs[0]["stock_quantity"] = 0
        print("\n[Info] Modified first record to have zero stock value")

    print(f"\n[Summary] Collected {len(all_drugs)} valid records")
    return all_drugs


def save_to_csv(drugs):
    try:
        fieldnames = [
            "brand_name",
            "generic_name",
            "manufacturer_name",
            "product_ndc",
            "route",
            "product_type",
            "rxcui",
            "stock_quantity",
        ]

        valid_drugs = [
            d for d in drugs
            if d.get("brand_name", "").strip() and d.get("generic_name", "").strip()
        ]

        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in valid_drugs:
                writer.writerow(row)

        print("\n" + "=" * 60)
        print(f"SUCCESS: Saved {len(valid_drugs)} records to {OUTPUT_FILE}")
        print("=" * 60)
        return True

    except IOError as e:
        print(f"Error: Failed to write CSV file - {e}")
        return False
    except Exception as e:
        print(f"Error: Unexpected error while saving - {e}")
        return False


def main():
    print("\nFetching drug data from OpenFDA API...")
    drugs = fetch_drug_data()

    if drugs:
        print(f"\nTotal records fetched: {len(drugs)}")
        save_to_csv(drugs)
    else:
        print("Error: No drug data was fetched")


if __name__ == "__main__":
    main()
