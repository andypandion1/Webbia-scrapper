import os, time, requests, csv
from bs4 import BeautifulSoup
import gspread
from google.oauth2.service_account import Credentials

# Setup Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("webbia-scraper-49b803e16174.json", scopes=SCOPES)
gc = gspread.authorize(creds)
sheet = gc.open_by_key("1-KrRAjxeR_QJiklXvc9cHLrpCDsb-u3BpP2l7rzdCIU").sheet1

API_KEY = os.getenv("API_KEY")
TEXT_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

QUERIES = [
    "Plumbers in Melbourne", "Electricians in Brisbane", "Mechanics in Perth", "Landscapers in Adelaide",
    "Hair salons in Cairns", "Massage therapists in Darwin", "Mobile dog groomers in Sydney",
    "Roofing companies in Newcastle", "Handymen in Geelong", "Tutors in Wollongong", "Tree services in Mildura",
    "Pet groomers in Alice Springs",
    "Mobile mechanics in Dubbo",
    "Tutors in Karratha",
    "Locksmiths in Broken Hill",
    "Cake shops in Whyalla",
    "Lawn mowing services in Burnie",
    "Fencing contractors in Orange",
    "Photographers in Armidale",
    "Cleaning services in Wagga Wagga"
]

def fallback_web_check(biz_name, city):
    try:
        query = f"{biz_name} {city}".replace(" ", "+")
        resp = requests.get(f"https://www.google.com/search?q={query}", headers={
            "User-Agent": "Mozilla/5.0"
        })
        soup = BeautifulSoup(resp.text, "html.parser")
        links = [a.get("href") for a in soup.find_all("a", href=True)]
        score = "None"
        for link in links:
            if "facebook.com" in link:
                score = "Facebook"
            elif "instagram.com" in link and score != "Facebook":
                score = "Instagram"
            elif "google.com/maps" in link and score == "None":
                score = "GMB"
        return score
    except:
        return "Unknown"

def get_place_details(place_id):
    params = {"place_id": place_id, "fields": "name,formatted_address,website,url", "key": API_KEY}
    res = requests.get(DETAILS_URL, params=params)
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
                fallback = fallback_web_check(d.get("name", ""), query.split(" in ")[-1])
            if fallback in ["Facebook", "Instagram", "GMB"]:
                found.append([
                    d.get("name"),
                    d.get("formatted_address"),
                    d.get("url"),
                    d.get("website") or "N/A",
                    fallback
                ])

        if "next_page_token" in data:
            time.sleep(2)
            params = {"pagetoken": data["next_page_token"], "key": API_KEY}
        else:
            break
    return found

def push_to_sheet(data):
    if data:
        sheet.append_rows(data, value_input_option="RAW")

if __name__ == "__main__":
    for q in QUERIES:
        print("Scraping:", q)
        data = full_scrape(q)
        push_to_sheet(data)
        print(f"Pushed {len(data)} leads from: {q}")
