import requests
import random
import json
import os
import math

FLYERS_URL = "https://flyers-ng.flippback.com/api/flipp/data?locale=en&postal_code={}&sid={}"
ITEMS_URL = "https://flyers-ng.flippback.com/api/flipp/flyers/{}/flyer_items?locale=en&sid={}"

# Banner labels that are promotional, not real store departments —
# products under these get assigned to the nearest REAL department instead.
EXCLUDED_BANNER_NAMES = {"Digital Deals", "Stater Saver"}


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


def center(entry):
    cx = (entry["left"] + entry["right"]) / 2
    cy = (entry["top"] + entry["bottom"]) / 2
    return cx, cy


def assign_categories(raw_items):
    # Collect real department banners (display_type 5, excluding promo banners)
    banners = []
    for entry in raw_items:
        if entry.get("display_type") == 5 and entry.get("name") not in EXCLUDED_BANNER_NAMES:
            cx, cy = center(entry)
            banners.append({"name": entry["name"], "cx": cx, "cy": cy})

    output = []
    for entry in raw_items:
        if entry.get("display_type") != 1 or not entry.get("price"):
            continue  # skip banners and items with no real price

        icx, icy = center(entry)

        # Find nearest banner by straight-line distance
        nearest_name = "Other"
        nearest_dist = None
        for b in banners:
            dist = math.hypot(icx - b["cx"], icy - b["cy"])
            if nearest_dist is None or dist < nearest_dist:
                nearest_dist = dist
                nearest_name = b["name"]

        output.append({
            "price": entry["price"],
            "item": entry["name"],
            "brand": entry.get("brand") or "",
            "category": nearest_name,
        })

    return output


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
