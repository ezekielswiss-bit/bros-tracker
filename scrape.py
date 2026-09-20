import requests
import random
import json
import os

FLYERS_URL = "https://flyers-ng.flippback.com/api/flipp/data?locale=en&postal_code={}&sid={}"
ITEMS_URL = "https://flyers-ng.flippback.com/api/flipp/flyers/{}/flyer_items?locale=en&sid={}"

def generate_sid():
    return ''.join(str(random.randint(0, 9)) for _ in range(16))

def get_stater_bros_flyer_id(zip_code):
    sid = generate_sid()
    response = requests.get(FLYERS_URL.format(zip_code, sid))
    response.raise_for_status()
    for flyer in response.json().get("flyers", []):
        if flyer.get("merchant") == "Stater Bros. Markets":
            return flyer["id"]
    return None

def get_flyer_items(flyer_id):
    sid = generate_sid()
    response = requests.get(ITEMS_URL.format(flyer_id, sid))
    response.raise_for_status()
    return response.json()

def main():
    zip_code = "92604"
    current_flyer_id = get_stater_bros_flyer_id(zip_code)

    if not current_flyer_id:
        print("No Stater Bros flyer found.")
        return

    last_id_file = "last_flyer_id.txt"
    last_id = None
    if os.path.exists(last_id_file):
        with open(last_id_file) as f:
            last_id = f.read().strip()

    if str(current_flyer_id) == last_id:
        print("No new ad. Skipping.")
        return

    print(f"New ad detected! Flyer ID changed from {last_id} to {current_flyer_id}")

    raw_items = get_flyer_items(current_flyer_id)

    output = []
    for item in raw_items:
        if item.get("display_type") == 1 and item.get("price"):
            output.append({
                "price": item["price"],
                "item": item["name"],
                "brand": item.get("brand") or ""
            })

    with open("stater_bros_ad.json", "w") as f:
        json.dump(output, f, indent=2)

    with open(last_id_file, "w") as f:
        f.write(str(current_flyer_id))

    print(f"Saved {len(output)} items.")

if __name__ == "__main__":
    main()
