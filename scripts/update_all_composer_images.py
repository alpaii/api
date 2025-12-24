#!/usr/bin/env python3
"""
Update all composer images from high-quality sources
"""
import requests
import json
from pathlib import Path

# Directory for storing images
IMAGES_DIR = Path("static/images/composers")
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

API_BASE_URL = "http://localhost:8000"

# High-quality composer portrait URLs from Wikimedia Commons
COMPOSER_IMAGES = {
    "Johann Sebastian Bach": "https://upload.wikimedia.org/wikipedia/commons/6/6a/Johann_Sebastian_Bach.jpg",
    "Ludwig van Beethoven": "https://upload.wikimedia.org/wikipedia/commons/6/6f/Beethoven.jpg",
    "Johannes Brahms": "https://upload.wikimedia.org/wikipedia/commons/1/15/JohannesBrahms.jpg",
    "Frédéric Chopin": "https://upload.wikimedia.org/wikipedia/commons/e/e8/Frederic_Chopin_photo.jpeg",
    "George Frideric Handel": "https://upload.wikimedia.org/wikipedia/commons/5/5b/George_Frideric_Handel_by_Balthasar_Denner.jpg",
    "Joseph Haydn": "https://upload.wikimedia.org/wikipedia/commons/0/05/Joseph_Haydn.jpg",
    "Vladimir Horowitz": "https://upload.wikimedia.org/wikipedia/commons/d/d5/Vladimir_Horowitz_1986.jpg",
    "Felix Mendelssohn": "https://upload.wikimedia.org/wikipedia/commons/7/79/Felix_Mendelssohn_Bartholdy_-_Aquarell_von_James_Warren_Childe_1829.jpg",
    "Wolfgang Amadeus Mozart": "https://upload.wikimedia.org/wikipedia/commons/1/1e/Wolfgang-amadeus-mozart_1.jpg",
    "Sergei Rachmaninoff": "https://upload.wikimedia.org/wikipedia/commons/b/be/Sergei_Rachmaninoff_cph.3a40575.jpg",
    "Mstislav Rostropovich": "https://upload.wikimedia.org/wikipedia/commons/5/50/Mstislav_Rostropovich_1978.jpg",
    "Pyotr Ilyich Tchaikovsky": "https://upload.wikimedia.org/wikipedia/commons/8/80/Tchaikovsky_by_Kuznetsov.jpg",
    "Antonio Vivaldi": "https://upload.wikimedia.org/wikipedia/commons/3/3e/Antonio_Vivaldi.jpg",
    "Franz Schubert": "https://upload.wikimedia.org/wikipedia/commons/0/0d/Franz_Schubert_by_Wilhelm_August_Rieder_1875.jpg",
}

def download_image(url, filename):
    """Download image from URL and save to file"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        filepath = IMAGES_DIR / filename
        with open(filepath, 'wb') as f:
            f.write(response.content)

        print(f"✓ Downloaded: {filename}")
        return f"/static/images/composers/{filename}"
    except Exception as e:
        print(f"✗ Failed to download {filename}: {e}")
        return None

def get_composers():
    """Get all composers from API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/composers/")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching composers: {e}")
        return []

def update_composer_image(composer_id, image_url):
    """Update composer's image_url in database"""
    try:
        response = requests.put(
            f"{API_BASE_URL}/api/composers/{composer_id}",
            json={"image_url": image_url},
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error updating composer {composer_id}: {e}")
        return False

def main():
    print("Fetching composers from database...")
    composers = get_composers()

    if not composers:
        print("No composers found!")
        return

    print(f"\nFound {len(composers)} composers")
    print("Downloading and updating all images...\n")

    for composer in composers:
        full_name = composer['full_name']
        composer_id = composer['id']

        # Get image URL from mapping
        image_url = COMPOSER_IMAGES.get(full_name)
        if not image_url:
            print(f"⊙ Skipped (no image URL): {full_name}")
            continue

        # Generate filename from composer name
        filename = f"{full_name.lower().replace(' ', '_').replace('é', 'e').replace('í', 'i')}.jpg"

        # Download image (always re-download to update)
        local_image_url = download_image(image_url, filename)

        if local_image_url:
            # Update database
            if update_composer_image(composer_id, local_image_url):
                print(f"  → Updated database for {full_name}")
            else:
                print(f"  → Failed to update database for {full_name}")

        print()

    print("Done!")

if __name__ == "__main__":
    main()
