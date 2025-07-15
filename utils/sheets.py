import os
import gspread
import urllib.parse
from oauth2client.service_account import ServiceAccountCredentials

def get_worksheet(sheet_name, worksheet_name="Sheet1"):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_path = os.getenv("GOOGLE_CREDS_JSON", "creds.json")
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
    client = gspread.authorize(creds)
    return client.open(sheet_name).worksheet(worksheet_name)


def update_recruits_sheet(data, sheet_name):
    """
    Writes recruits to the sheet, with:
      - national_rank: non‑numeric → 1000
      - columns: Name, National Rank, Position Rank, Position, High School, City, State, Commit
    """
    headers = [
        "Name",
        "National Rank",
        "Position Rank",
        "Position",
        "High School",
        "City",
        "State",
        "Commit",
    ]
    rows = [headers]

    for r in data:
        # pull raw, guard int vs str
        raw = r.get("national_rank", "")
        try:
            nr_int = int(raw)
        except Exception:
            nr_int = 1000

        pr = r.get("position_rank", "")
        rows.append([
            r.get("name", ""),
            nr_int,
            pr,
            r.get("position", ""),
            r.get("high_school", ""),
            r.get("city", ""),
            r.get("state", ""),
            r.get("commit", ""),
        ])

    ws = get_worksheet(sheet_name)
    ws.clear()
    ws.update("A1", rows)


def update_portal_sheet(data, sheet_name):
    """
    Writes transfer‐portal entries with:
      - rating: non‐numeric → 0.0
      - a 5‑star string
      - a hyperlink on Name into your AI‐Bio service
      - columns: Name, From School, To School, Position, Rating, Stars, Status, Update Date
    """
    BIO_URL = "https://my-ai-bio.herokuapp.com/bio"

    headers = [
        "Name",
        "From School",
        "To School",
        "Position",
        "Rating",
        "Stars",
        "Status",
        "Update Date",
    ]
    rows = [headers]

    for e in data:
        name = e.get("name", "").replace('"', '""')
        school = e.get("to_school") or e.get("from_school")

        # parse rating safely
        rt = e.get("rating", "")
        try:
            rating = float(rt)
        except Exception:
            rating = 0.0

        # build a 5‑star string
        if rating >= 0.98:
            stars = "★★★★★"
        elif rating >= 0.90:
            stars = "★★★★"
        elif rating >= 0.80:
            stars = "★★★"
        elif rating >= 0.70:
            stars = "★★"
        else:
            stars = "☆☆☆☆☆"

        # hyperlink into your AI‐bio service
        params = urllib.parse.urlencode({"name": name, "school": school})
        link = f'=HYPERLINK("{BIO_URL}?{params}", "{name}")'


        rows.append([
            link,
            e.get("from_school", ""),
            e.get("to_school", ""),
            e.get("position", ""),
            rating,
            stars,
            e.get("status", ""),
            e.get("update_date", ""),
        ])

        ws = get_worksheet(sheet_name)
        ws.clear()
        ws.update("A1", rows, value_input_option="USER_ENTERED")