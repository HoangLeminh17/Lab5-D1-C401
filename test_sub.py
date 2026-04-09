
import sys
import os
from pathlib import Path
import pandas as pd

# Add project root to sys.path
project_root = str(Path(__file__).resolve().parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mocking the load_inventory and find_alternative_drugs logic for testing
def load_inventory(inventory_path):
    try:
        df = pd.read_csv(inventory_path)
        return df
    except Exception as e:
        print(f"Error loading inventory: {e}")
        return pd.DataFrame()

def test_substitution(brand_to_search, inventory_path):
    print(f"--- Testing substitution for: {brand_to_search} ---")
    df = load_inventory(inventory_path)
    if df.empty:
        print("Inventory is empty or not found.")
        return

    # Find the active ingredient for the searched brand in our DB
    searched_drug = df[df['brand_name'].str.lower() == brand_to_search.lower()]
    if searched_drug.empty:
        print(f"Drug '{brand_to_search}' not found in local inventory.")
        # In a real scenario, we'd call FDA API here. 
        # For this test, let's assume we found it or we search by active ingredient directly.
        return

    active_ingredient = searched_drug.iloc[0]['generic_name']
    print(f"Active Ingredient for {brand_to_search}: {active_ingredient}")

    # Find alternatives
    alternatives = df[
        (df['generic_name'].str.lower() == active_ingredient.lower()) & 
        (df['brand_name'].str.lower() != brand_to_search.lower()) &
        (df['stock_quantity'] > 0)
    ]

    if not alternatives.empty:
        print(f"Found {len(alternatives)} alternatives:")
        for _, row in alternatives.iterrows():
            print(f"- Brand: {row['brand_name']}, Stock: {row['stock_quantity']}")
    else:
        print("No alternatives found with same active ingredient and stock.")

if __name__ == "__main__":
    inventory_file = "inventory.csv"
    test_substitution("Betadine", inventory_file)
    print("\n")
    test_substitution("Naproxen", inventory_file)
    print("\n")
    test_substitution("TYLENOL Extra Strength", inventory_file)
