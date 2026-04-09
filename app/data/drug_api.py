"""Local drug database API wrapper."""

from app.data.database import (
    get_all_drugs,
    search_drugs_by_brand,
    search_drugs_by_generic,
    search_drugs_by_manufacturer,
    get_drugs_by_route,
    get_drug_by_ndc,
    get_database_stats,
)


class DrugAPI:
    @staticmethod
    def get_all(limit=None):
        return get_all_drugs(limit=limit)

    @staticmethod
    def search_brand(brand_name):
        return search_drugs_by_brand(brand_name)

    @staticmethod
    def search_generic(generic_name):
        return search_drugs_by_generic(generic_name)

    @staticmethod
    def search_manufacturer(manufacturer_name):
        return search_drugs_by_manufacturer(manufacturer_name)

    @staticmethod
    def get_by_route(route):
        return get_drugs_by_route(route)

    @staticmethod
    def get_by_ndc(product_ndc):
        return get_drug_by_ndc(product_ndc)

    @staticmethod
    def get_stats():
        return get_database_stats()
