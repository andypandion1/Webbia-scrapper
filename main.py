
import requests, time, csv
import os

API_KEY = os.getenv("API_KEY")

TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

QUERY = "Cafes in Melbourne"

def get_place_details(place_id):
    params = {
        "place_id": place_id,
        "fields": "name,formatted_address,website,url",
        "key": API_KEY
    }
    res = requests.get(DETAILS_URL, params=details_params)
    return res.json().get("result", {})

def full_scrape(query):
    found = []
    params = {"query": query, "key": API_KEY}

    while True:
        r = requests.get(TEXT_SEARCH_URL, params=params)
        data = r.json()

        for p in data.get("results", []):
            pid = p.get("place_id")
            if pid:
                time.sleep(1.5)
                d = get_place_details(pid)
                if not d.get("website"):
                    found.append({
                        "name": d.get("name"),
                        "address": d.get("formatted_address"),
                        "maps_url": d.get("url"),
                        "website": "N/A"
                    })

        if "next_page_token" in data:
            time.sleep(2)
            params = {"pagetoken": data["next_page_token"], "key": API_KEY}
        else:
            break

    return found

def save_to_csv(data, filename="places.csv"):
    with open(filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "address", "maps_url", "website"])
        writer.writeheader()
        writer.writerows(data)

if __name__ == "__main__":
    results = full_scrape(QUERY)
    save_to_csv(results)
    print(f"Scraped and saved {len(results)} businesses.")
