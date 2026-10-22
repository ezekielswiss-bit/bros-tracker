import requests
import random
import json
import os
import re
from datetime import datetime, timezone

FLYERS_URL = "https://flyers-ng.flippback.com/api/flipp/data?locale=en&postal_code={}&sid={}"
ITEMS_URL = "https://flyers-ng.flippback.com/api/flipp/flyers/{}/flyer_items?locale=en&sid={}"

# Keyword-based categorization. Order matters — checked top to bottom,
# first match wins. More specific / brand-heavy categories (alcohol,
# meat, dairy) are checked before broad catch-alls (Pantry) so a
# word like "cheese" or "beef" wins over a generic later match.
CATEGORY_KEYWORDS = [
    ("Beer, Wine & Spirits", [
        "beer", "wine", "vodka", "tequila", "whiskey", "bourbon", "rum",
        "gin", "champagne", "ale", "lager", "ipa", "malo", "hornitos",
        "casamigos", "don julio", "patron", "modelo", "corona", "heineken",
        "budweiser", "coors", "michelob", "tecate", "chardonnay", "pinot",
        "cabernet", "merlot", "dark horse", "la vieille", "bogle",
        "santa margherita", "decoy", "rombauer", "firestone walker",
        "sierra nevada", "lagunitas", "gran centenario", "conejos",
        "aperol", "jim beam", "skyy", "buzzballz", "surfside", "smirnoff",
        "white claw", "high noon", "twisted tea", "cayman jack",
        "louis jadot", "la crema", "la marca", "wilson creek", "chandon",
        "meiomi", "ferrari-carano", "eagle rare", "blanton", "buffalo trace",
        "colonel e.h. taylor", "gran malo", "tito's", "cutwater",
        "el jimador", "kona big wave",
    ]),
    ("Meat & Seafood", [
        "beef", "steak", "rib", "chicken", "turkey", "pork", "bacon",
        "sausage", "salmon", "shrimp", "fish", "seafood", "tri tip",
        "sirloin", "ground turkey", "ground beef", "salami", "pepperoni",
        "bologna", "al pastor", "flanken", "short plate", "loin",
        "chuck", "brisket", "tenders", "leg quarters",
    ]),
    ("Dairy & Eggs", [
        "milk", "cheese", "yogurt", "chobani", "sour cream", "cottage cheese",
        "queso", "cream cheese", "butter", "egg", "half & half", "creamer",
        "almond breeze", "lactaid",
    ]),
    ("Bakery & Bread", [
        "bread", "bagel", "baguette", "muffin", "bun", "cake", "cookie",
        "donut", "donette", "pastry", "sourdough", "toast", "roll",
        "biscuit", "baked goods", "entenmann",
    ]),
    ("Deli & Prepared Food", [
        "deli", "salad bowl", "mac & cheese", "mashed", "hummus",
        "fried chicken", "rotisserie", "pot pie", "wrap", "lunchable",
    ]),
    ("Frozen Food", [
        "frozen", "ice cream", "pizza", "burrito", "chimichanga",
        "hot pocket", "skillet meal", "pasta bake", "fudge bar",
        "novelt", "drumstick", "haagen", "häagen", "popsicle",
        "breyers", "ben & jerry", "talenti", "yasso", "good humor",
    ]),
    ("Beverages", [
        "soda", "cola", "pepsi", "7up", "squirt", "juice", "water",
        "gatorade", "energy drink", "red bull", "monster", "tea",
        "lemonade", "punch", "sparkling", "coconut water", "sunny d",
        "citrus punch", "electrolyte", "beverage",
    ]),
    ("Fruits & Vegetables", [
        "apple", "orange", "lettuce", "squash", "potato", "yam",
        "jalapeno", "jalapeño", "plum", "grape", "berries",
        "strawberry", "strawberries", "raspberry", "raspberries",
        "onion", "tomato", "avocado", "lime",
        "lemon", "cucumber", "carrot", "broccoli", "spinach", "salad",
    ]),
    ("Health & Beauty", [
        "shampoo", "toothpaste", "oral rinse", "batiste", "therabreath",
        "pads", "liners", "tampon", "always", "tampax",
    ]),
    ("Baby Care", [
        "diaper", "baby",
    ]),
    ("Animal & Pet Supplies", [
        "dog food", "cat food", "pet", "pedigree",
    ]),
    ("Home & Outdoor", [
        "trash bag", "detergent", "cat litter", "paper towel",
        "bath tissue", "toilet paper", "party cup", "charcoal",
    ]),
    ("Floral", [
        "bouquet", "flower", "floral",
    ]),
    ("Pantry", [
        "cereal", "peanut butter", "jif", "sauce", "chili", "beans",
        "rice", "pasta", "oil", "flour", "sugar", "condensed milk",
        "tuna", "canned", "wonton", "noodle", "cracker", "graham",
        "wafer", "chips", "snack", "dressing", "mayonnaise", "ketchup",
        "tortilla", "harvest snap", "frito lay", "pepper",
        "ruffles", "doritos", "tostitos", "sunchips", "popcorners",
        "funyuns", "cheetos", "fritos",
    ]),
]


def categorize(name):
    name_lower = name.lower()
    for category, keywords in CATEGORY_KEYWORDS:
        for kw in keywords:
            # \b = word boundary, so "pepper" matches the standalone
            # word "pepper" but NOT the "pepper" inside "Pepperidge".
            pattern = r'\b' + re.escape(kw) + r's?\b'
            if re.search(pattern, name_lower):
                return category
    return "Other"


def generate_sid():
    return ''.join(str(random.randint(0, 9)) for _ in range(16))


def parse_date(value):
    try:
        return datetime.fromisoformat(value) if value else None
    except ValueError:
        return None


def get_stater_bros_flyer(zip_code):
    """Return the newest Stater Bros weekly ad, or None.

    When a new ad goes up, Flipp often keeps listing the old one until
    it expires, in no particular order. Taking the first match made the
    saved ad flip back and forth between old and new, so pick the
    still-running flyer with the latest valid_from date instead.
    """
    sid = generate_sid()
    response = requests.get(FLYERS_URL.format(zip_code, sid))
    response.raise_for_status()
    flyers = [
        f for f in response.json().get("flyers", [])
        if f.get("merchant") == "Stater Bros. Markets"
    ]
    if not flyers:
        return None

    now = datetime.now(timezone.utc)
    running = [
        f for f in flyers
        if (parse_date(f.get("valid_to")) or now) >= now
    ]
    oldest = datetime.min.replace(tzinfo=timezone.utc)
    return max(
        running or flyers,
        key=lambda f: (parse_date(f.get("valid_from")) or oldest, f["id"]),
    )


def load_saved_ad(path):
    """Return the saved ad's metadata dict, or {} for a missing/old-format file."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def get_flyer_items(flyer_id):
    sid = generate_sid()
    response = requests.get(ITEMS_URL.format(flyer_id, sid))
    response.raise_for_status()
    return response.json()


def assign_categories(raw_items):
    output = []
    for entry in raw_items:
        if entry.get("display_type") != 1 or not entry.get("price"):
            continue  # skip banners and items with no real price

        name = entry["name"]
        output.append({
            "price": entry["price"],
            "item": name,
            "brand": entry.get("brand") or "",
            "category": categorize(name),
            "image_url": entry.get("cutout_image_url") or "",
        })

    return output


def main():
    zip_code = "92604"
    ad_file = "stater_bros_ad.json"
    flyer = get_stater_bros_flyer(zip_code)

    if not flyer:
        print("No Stater Bros flyer found.")
        return

    current_flyer_id = flyer["id"]
    saved = load_saved_ad(ad_file)
    last_id = saved.get("flyer_id")

    if current_flyer_id == last_id:
        print("No new ad. Skipping.")
        return

    # Never replace a newer ad with an older one.
    saved_from = parse_date(saved.get("valid_from"))
    current_from = parse_date(flyer.get("valid_from"))
    if saved_from and current_from and current_from < saved_from:
        print(f"Flyer {current_flyer_id} is older than saved ad {last_id}. Skipping.")
        return

    print(f"New ad detected! Flyer ID changed from {last_id} to {current_flyer_id}")

    raw_items = get_flyer_items(current_flyer_id)
    output = {
        "flyer_id": current_flyer_id,
        "valid_from": flyer.get("valid_from"),
        "valid_to": flyer.get("valid_to"),
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items": assign_categories(raw_items),
    }

    with open(ad_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Kept for reference; the ad file itself is now the source of truth.
    with open("last_flyer_id.txt", "w") as f:
        f.write(str(current_flyer_id))

    print(
        f"Saved {len(output['items'])} items "
        f"(valid {output['valid_from']} to {output['valid_to']})."
    )


if __name__ == "__main__":
    main()
