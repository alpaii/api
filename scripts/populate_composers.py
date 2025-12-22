#!/usr/bin/env python3
"""Script to populate composers table with initial data"""
import requests

API_URL = "http://localhost:8000/api/composers/"

composers = [
    {"name": "Johann Sebastian Bach", "short_name": "J.S. Bach", "birth_year": 1685, "death_year": 1750, "nationality": "German"},
    {"name": "Antonio Vivaldi", "short_name": "Vivaldi", "birth_year": 1678, "death_year": 1741, "nationality": "Italian"},
    {"name": "George Frideric Handel", "short_name": "Handel", "birth_year": 1685, "death_year": 1759, "nationality": "German-British"},
    {"name": "Ludwig van Beethoven", "short_name": "Beethoven", "birth_year": 1770, "death_year": 1827, "nationality": "German"},
    {"name": "Wolfgang Amadeus Mozart", "short_name": "Mozart", "birth_year": 1756, "death_year": 1791, "nationality": "Austrian"},
    {"name": "Franz Schubert", "short_name": "Schubert", "birth_year": 1797, "death_year": 1828, "nationality": "Austrian"},
    {"name": "Frédéric Chopin", "short_name": "Chopin", "birth_year": 1810, "death_year": 1849, "nationality": "Polish-French"},
    {"name": "Johannes Brahms", "short_name": "Brahms", "birth_year": 1833, "death_year": 1897, "nationality": "German"},
    {"name": "Felix Mendelssohn", "short_name": "Mendelssohn", "birth_year": 1809, "death_year": 1847, "nationality": "German"},
    {"name": "Pyotr Ilyich Tchaikovsky", "short_name": "Tchaikovsky", "birth_year": 1840, "death_year": 1893, "nationality": "Russian"},
    {"name": "Sergei Rachmaninoff", "short_name": "Rachmaninoff", "birth_year": 1873, "death_year": 1943, "nationality": "Russian"},
]

def main():
    # Check if there are already composers
    response = requests.get(API_URL)
    existing = response.json()

    if len(existing) > 0:
        print(f"Database already has {len(existing)} composers. Skipping initialization.")
        return

    # Add each composer
    for composer in composers:
        try:
            response = requests.post(API_URL, json=composer)
            response.raise_for_status()
            print(f"Added: {composer['name']}")
        except Exception as e:
            print(f"Failed to add {composer['name']}: {e}")

    print(f"\nSuccessfully populated {len(composers)} composers!")

if __name__ == "__main__":
    main()
