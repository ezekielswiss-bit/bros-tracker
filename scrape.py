import requests
import random
import json
import os
import re

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
    output = assign_categories(raw_items)

    with open("stater_bros_ad.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    with open(last_id_file, "w") as f:
        f.write(str(current_flyer_id))

    print(f"Saved {len(output)} items.")


if __name__ == "__main__":
    main()
