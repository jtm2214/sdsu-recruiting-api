import os
import logging
from datetime import datetime, date, timedelta

from flask import Flask, request, render_template, jsonify
import cloudscraper
from bs4 import BeautifulSoup

from scraper.recruiting import scrape_recruiting
from scraper.portal   import scrape_transfer_portal
from utils.sheets     import update_recruits_sheet, update_portal_sheet

logging.basicConfig(level=logging.INFO, format="%(message)s")

app = Flask(__name__, template_folder="templates")


def generate_summary(name: str, school: str) -> str:
    """
    Stub: wire in your AI + Search logic here.
    """
    return (
        f"<p><em>AI summary for "
        f"<strong>{name}</strong> @ <strong>{school}</strong> coming soon…</em></p>"
    )


# ─── Public bio endpoint ──────────────────────────────────────────────────────

@app.route("/bio")
def bio():
    name   = request.args.get("name", "")
    school = request.args.get("school", "")
    summary = generate_summary(name, school)
    return render_template("bio.html", name=name, school=school, summary=summary)


# ─── Sheet‑update hooks (called by GitHub Actions or Render Cron) ─────────────

@app.route("/update/recruits", methods=["POST"])
def update_recruits():
    recruits = scrape_recruiting()
    # NA national‐rank → 1000
    for r in recruits:
        try:
            r["national_rank"] = int(r.get("national_rank", ""))
        except:
            r["national_rank"] = 1000

    sheet_name = os.getenv("GOOGLE_SHEET_NAME", "SDSU Recruiting")
    update_recruits_sheet(recruits, sheet_name)

    msg = f"Wrote {len(recruits)} recruits to '{sheet_name}'"
    logging.info(msg)
    return jsonify(status="ok", message=msg), 200


@app.route("/update/portal", methods=["POST"])
def update_portal():
    entries = scrape_transfer_portal()
    # N/A rating → "0"
    for e in entries:
        try:
            float(e.get("rating", ""))
        except:
            e["rating"] = "0"

    sheet_name = os.getenv("PORTAL_SHEET_NAME", "SDSU Transfer Portal")
    update_portal_sheet(entries, sheet_name)

    msg = f"Wrote {len(entries)} portal entries to '{sheet_name}'"
    logging.info(msg)
    return jsonify(status="ok", message=msg), 200


# ─── Health check ────────────────────────────────────────────────────────────

@app.route("/_health")
def health():
    return "OK", 200


# ─── Run ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # in production you'll use Gunicorn (Procfile: `web: gunicorn app:app`)
    app.run(host="0.0.0.0", port=port)
