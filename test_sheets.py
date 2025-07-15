# test_sheets.py

import os

from scraper.recruiting import scrape_recruiting
from scraper.portal    import scrape_transfer_portal
from utils.sheets      import update_recruits_sheet, update_portal_sheet

# Point to your service‐account creds and sheet names
os.environ["GOOGLE_CREDS_JSON"]   = "creds.json"
os.environ["GOOGLE_SHEET_NAME"]   = "SDSU Recruiting"
os.environ["PORTAL_SHEET_NAME"]   = "SDSU Transfer Portal"

# --- Test recruiting sheet update ---
recruits = scrape_recruiting()
print(f"Got {len(recruits)} recruits; sending all to '{os.environ['GOOGLE_SHEET_NAME']}'…")
update_recruits_sheet(recruits, os.environ["GOOGLE_SHEET_NAME"])
print(f"✅ Recruiting sheet should now have {len(recruits)} rows of data.")

# --- Test portal sheet update ---
entries = scrape_transfer_portal()
print(f"Got {len(entries)} portal entries; sending all to '{os.environ['PORTAL_SHEET_NAME']}'…")
update_portal_sheet(entries, os.environ["PORTAL_SHEET_NAME"])
print(f"✅ Portal sheet should now have {len(entries)} rows of data.")
