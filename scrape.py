import json
import os

def main():
    zip_code = "92604"
    current_flyer_id = get_stater_bros_flyer_id(zip_code)  # from earlier script

    # Load the last known flyer ID
    last_id_file = "last_flyer_id.txt"
    last_id = None
    if os.path.exists(last_id_file):
        with open(last_id_file) as f:
            last_id = f.read().strip()

    if str(current_flyer_id) == last_id:
        print("No new ad. Skipping.")
        return  # nothing changes, GitHub Action just exits, no commit made

    print(f"New ad detected! Flyer ID changed from {last_id} to {current_flyer_id}")

    raw_items = get_flyer_items(current_flyer_id)
    output = [
        {"price": item["price"], "item": item["name"], "brand": item.get("brand") or ""}
        for item in raw_items
        if item.get("display_type") == 1 and item.get("price")
    ]

    with open("stater_bros_ad.json", "w") as f:
        json.dump(output, f, indent=2)

    with open(last_id_file, "w") as f:
        f.write(str(current_flyer_id))

if __name__ == "__main__":
    main()
