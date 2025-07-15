import cloudscraper
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")


def scrape_recruiting():
    """Scrape 247Sports 2025 Composite Recruit Rankings."""
    url = "https://247sports.com/season/2026-football/compositerecruitrankings/"
    scraper = cloudscraper.create_scraper()
    resp = scraper.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    recruits = []
    items = soup.select("ul.rankings-page__list li")
    logging.info(f"[recruiting] found {len(items)} list items")

    for li in items:
        # Name
        name_tag = li.select_one(".rankings-page__name-link")
        if not name_tag:
            continue
        name = name_tag.get_text(strip=True)
        if name.lower() == "player":
            continue

        # Position
        pos_tag = li.select_one("div.position")
        position = pos_tag.get_text(strip=True) if pos_tag else ""

        # National and position ranks
        nat_tag  = li.select_one("div.rank a.natrank")
        posr_tag = li.select_one("div.rank a.posrank")
        national_rank = nat_tag.get_text(strip=True) if nat_tag else ""
        position_rank = posr_tag.get_text(strip=True) if posr_tag else ""

        # High School (split into HS / City / State)
        meta = li.select_one("span.meta")
        highschool = city = state = ""
        if meta:
            text = meta.get_text(strip=True)
            if "(" in text and ")" in text:
                hs, rest = text.split("(", 1)
                highschool = hs.strip()
                rest = rest.rstrip(")")
                parts = [p.strip() for p in rest.split(",")]
                if len(parts) >= 1:
                    city = parts[0]
                if len(parts) >= 2:
                    state = parts[1]
            else:
                highschool = text

        # Commit college badge: look inside div.status → a.img-link → img.jsonly
        commit_img = li.select_one("div.status a.img-link img.jsonly[title]")
        commit = commit_img["title"].strip() if commit_img else ""

        recruits.append({
            "name":           name,
            "national_rank":  national_rank,
            "position_rank":  position_rank,
            "position":       position,
            "high_school":    highschool,
            "city":           city,
            "state":          state,
            "commit":         commit,
        })

    logging.info(f"[recruiting] parsed {len(recruits)} recruits via HTML")
    return recruits


if __name__ == "__main__":
    recs = scrape_recruiting()
    for r in recs[:10]:
        print(r)
    print(f"Total recruits scraped: {len(recs)}")
