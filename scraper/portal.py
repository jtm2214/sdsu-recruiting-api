#!/usr/bin/env python3
import logging
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

import cloudscraper
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(message)s")

def scrape_transfer_portal(
    batch_size: int = 5,
    max_workers: int = 5,
    min_entries_to_continue: int = 15,
    season: int = 2025,
):
    """
    Scrape the 247Sports Transfer Portal for a given season.
    - Uses cloudscraper to bypass basic bot blocks.
    - Fetches pages in parallel batches.
    - Stops when a page yields fewer than min_entries_to_continue items
      OR when it sees an update_date older than one year ago.
    - Adds a 'stars' column using:
        0.98+ → 5, 0.90+ → 4, 0.80+ → 3, 0.70+ → 2, else 0
    """
    base_url = f"https://247sports.com/Season/{season}-Football/TransferPortal/?Page="
    scraper = cloudscraper.create_scraper()

    one_year_ago = date.today() - timedelta(days=365)
    all_entries = []
    seen_keys = set()
    stop = False
    page = 1

    def fetch_and_parse(pg: int):
        url = base_url + str(pg)
        resp = scraper.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        page_entries = []
        found_old = False

        for grp in soup.select("section.transfer-group"):
            hdr = grp.select_one("header.transferContentHeader h2")
            raw = hdr.get_text(strip=True).split()[0] if hdr else ""
            try:
                grp_date = datetime.strptime(raw, "%m/%d/%y").date()
            except ValueError:
                grp_date = date.today()

            if grp_date < one_year_ago:
                found_old = True
                break

            for li in grp.select("li.transfer-player"):
                # name
                name_el = li.select_one("h3 a")
                name = name_el.get_text(strip=True) if name_el else ""

                # position
                position = (li.select_one("div.position") or BeautifulSoup("", "html.parser")).get_text(strip=True)

                # rating → float, default 0.0 if non‑numeric
                raw_rating = (li.select_one("div.rating") or BeautifulSoup("", "html.parser")).get_text(strip=True)
                try:
                    rating = float(raw_rating)
                except ValueError:
                    rating = 0.0

                # compute stars
                if rating >= 0.98:
                    star_count = 5
                elif rating >= 0.90:
                    star_count = 4
                elif rating >= 0.80:
                    star_count = 3
                elif rating >= 0.70:
                    star_count = 2
                else:
                    star_count = 0
                stars = "★" * star_count  # string of filled stars

                # status
                status = (li.select_one("div.status") or BeautifulSoup("", "html.parser")).get_text(strip=True)

                # from / to schools
                logos = li.find_all("img", class_="logo")
                frm = logos[0].get("alt", "") if len(logos) >= 1 else ""
                to  = logos[1].get("alt", "") if len(logos) >= 2 else ""

                entry = {
                    "name":        name,
                    "from_school": frm,
                    "to_school":   to,
                    "position":    position,
                    "rating":      rating,
                    "stars":       stars,
                    "status":      status,
                    "update_date": grp_date.isoformat(),
                }
                page_entries.append(entry)

        logging.info(f"[portal] Page {pg} → {len(page_entries)} entries{' (old cutoff)' if found_old else ''}")
        return pg, page_entries, found_old

    while not stop:
        batch = list(range(page, page + batch_size))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_and_parse, p): p for p in batch}
            for fut in as_completed(futures):
                pg, entries, found_old = fut.result()
                if found_old or len(entries) < min_entries_to_continue:
                    logging.info(f"[portal] stopping after page {pg} ({len(entries)} entries{' & old cutoff' if found_old else ''})")
                    stop = True
                for e in entries:
                    key = tuple(e[k] for k in ("name","from_school","to_school","position","rating","status","update_date"))
                    if key not in seen_keys:
                        seen_keys.add(key)
                        all_entries.append(e)
        page += batch_size

    logging.info(f"[portal] total portal entries scraped: {len(all_entries)}")
    return all_entries

if __name__ == "__main__":
    entries = scrape_transfer_portal()
    for e in entries[:10]:
        print(e)
    print(f"Total portal entries scraped: {len(entries)}")
