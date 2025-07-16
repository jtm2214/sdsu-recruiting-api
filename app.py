import os
import logging
import openai
from flask import Flask, request, render_template, jsonify
import cloudscraper
from bs4 import BeautifulSoup
from scraper.recruiting import scrape_recruiting
from scraper.portal import scrape_transfer_portal
from utils.sheets import update_recruits_sheet, update_portal_sheet

logging.basicConfig(level=logging.INFO, format="%(message)s")
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__, template_folder="templates")

def generate_summary(name: str, school: str) -> str:
    prompt = (
        f"Write a concise, factual summary of the college football player "
        f"{name}, who played at {school}. Include their position, key career "
        f"statistics and metrics, and any notable achievements or transfers. "
        f"Format it as a few HTML paragraphs."
    )
    resp = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role":"system", "content":"You are a sports data assistant."},
            {"role":"user",   "content": prompt}
        ],
        temperature=0.7,
        max_tokens=400,
    )
    return resp.choices[0].message.content

@app.route("/bio")
def bio():
    name   = request.args.get("name", "")
    school = request.args.get("school", "")
    summary = generate_summary(name, school)
    return render_template("bio.html", name=name, school=school, summary=summary)

@app.route("/update/recruits", methods=["POST"])
def update_recruits():
    recruits = scrape_recruiting()
    for r in recruits:
        try:
            r["national_rank"] = int(r.get("national_rank",""))
        except:
            r["national_rank"] = 1000
    sheet_name = os.getenv("GOOGLE_SHEET_NAME","SDSU Recruiting")
    update_recruits_sheet(recruits, sheet_name)
    msg = f"Wrote {len(recruits)} recruits to '{sheet_name}'"
    logging.info(msg)
    return jsonify(status="ok", message=msg), 200

@app.route("/update/portal", methods=["POST"])
def update_portal():
    entries = scrape_transfer_portal()
    for e in entries:
        try:
            float(e.get("rating",""))
        except:
            e["rating"] = "0"
    sheet_name = os.getenv("PORTAL_SHEET_NAME","SDSU Transfer Portal")
    update_portal_sheet(entries, sheet_name)
    msg = f"Wrote {len(entries)} portal entries to '{sheet_name}'"
    logging.info(msg)
    return jsonify(status="ok", message=msg), 200

@app.route("/_health")
def health():
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT",5000))
    app.run(host="0.0.0.0", port=port)
