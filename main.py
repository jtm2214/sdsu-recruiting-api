import os
import time
import schedule
import cloudscraper
import logging

from threading import Thread
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, request, render_template

from scraper.recruiting import scrape_recruiting
from scraper.portal   import scrape_transfer_portal
from utils.sheets     import update_recruits_sheet, update_portal_sheet

logging.basicConfig(level=logging.INFO, format="%(message)s")

# ─── Flask setup ────────────────────────────────────────────────────────────────
app = Flask(__name__, template_folder="templates")

def generate_summary(name: str, school: str) -> str:
    """
    TODO: hook in your AI logic here:
    - query OpenAI (or another API) with name+school
    - scrape some basic stats pages
    - return a markdown/HTML summary
    """
    return f"<p><em>AI summary for {name} @ {school} coming soon…</em></p>"

@app.route("/bio")
def bio():
    name   = request.args.get("name", "")
    school = request.args.get("school", "")
    summary = generate_summary(name, school)
    return render_template("bio.html", name=name, school=school, summary=summary)

# ─── Sheet‐updating jobs ────────────────────────────────────────────────────────
RECRUIT_SHEET = os.getenv("GOOGLE_SHEET_NAME", "SDSU Recruiting")
PORTAL_SHEET  = os.getenv("PORTAL_SHEET_NAME", "SDSU Transfer Portal")

def job_recruits():
    recruits = scrape_recruiting()
    # fix NA national ranks to 1000
    for r in recruits:
        nr = r.get("national_rank", "")
        try:
            r["national_rank"] = int(nr)
        except:
            r["national_rank"] = 1000
    update_recruits_sheet(recruits, RECRUIT_SHEET)
    logging.info(f"[job_recruits] Wrote {len(recruits)} recruits to '{RECRUIT_SHEET}'")

def job_portal():
    entries = scrape_transfer_portal()
    # fix N/A ratings to "0"
    for e in entries:
        try:
            float(e["rating"])
        except:
            e["rating"] = "0"
    update_portal_sheet(entries, PORTAL_SHEET)
    logging.info(f"[job_portal] Wrote {len(entries)} portal entries to '{PORTAL_SHEET}'")

def run_scheduler():
    # every day at 08:00 UTC (or adjust for your tz)
    schedule.every().day.at("08:00").do(job_recruits)
    # every 5 minutes
    schedule.every(5).minutes.do(job_portal)

    while True:
        schedule.run_pending()
        time.sleep(1)

# ─── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # start scheduler in background
    t = Thread(target=run_scheduler, daemon=True)
    t.start()

    # kick off a run immediately on startup
    job_recruits()
    job_portal()

    # then serve Flask
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
