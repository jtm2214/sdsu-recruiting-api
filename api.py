from flask import Flask, jsonify
from scraper.recruiting import scrape_recruiting
from scraper.portal    import scrape_transfer_portal

app = Flask(__name__)

@app.route("/recruits")
def recruits():
    data = scrape_recruiting()
    return jsonify(data)

@app.route("/portal")
def portal():
    data = scrape_transfer_portal()
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True)
