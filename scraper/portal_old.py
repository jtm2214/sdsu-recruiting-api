import cloudscraper
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")


def scrape_transfer_portal():
    """Scrapes 247Sports 2025 Transfer Portal entries and dedupes them."""
    url = "https://247sports.com/Season/2025-Football/TransferPortal/"
    scraper = cloudscraper.create_scraper()
    resp = scraper.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    entries = []
    # Find each player link
    links = soup.find_all(
        "a",
        attrs={"title": lambda t: t and t.startswith("View player information")}
    )
    logging.info(f"[portal] found {len(links)} player links")

    for a in links:
        li = a.find_parent("li")
        if not li:
            continue
        # Name
        name = a.get_text(strip=True) or a["title"].replace("View player information for ", "")
        # Position, rating, status
        position = (li.select_one("div.position") or BeautifulSoup("", "html.parser")).get_text(strip=True)
        rating   = (li.select_one("div.rating")   or BeautifulSoup("", "html.parser")).get_text(strip=True)
        status   = (li.select_one("div.status")   or BeautifulSoup("", "html.parser")).get_text(strip=True)
        # From / to school
        logos = li.find_all("img", class_="logo")
        from_school = logos[0].get("alt", "") if len(logos) > 0 else ""
        to_school   = logos[1].get("alt", "") if len(logos) > 1 else ""

        entries.append({
            "name":        name,
            "from_school": from_school,
            "to_school":   to_school,
            "position":    position,
            "rating":      rating,
            "status":      status,
        })

    # Dedupe by tuple of all fields
    unique = []
    seen = set()
    for e in entries:
        key = (e["name"], e["from_school"], e["to_school"], e["position"], e["rating"], e["status"])
        if key not in seen:
            seen.add(key)
            unique.append(e)

    logging.info(f"[portal] parsed {len(unique)} unique entries")
    return unique


if __name__ == "__main__":
    ents = scrape_transfer_portal()
    for e in ents[:10]:
        print(e)
    print(f"Total portal entries scraped: {len(ents)}")
