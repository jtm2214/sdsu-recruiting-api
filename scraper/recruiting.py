import cloudscraper
from bs4 import BeautifulSoup
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO, format="%(message)s")

def scrape_recruiting(batch_size=5, max_workers=5):
    """
    Scrape ALL recruits, in parallel batches of `batch_size` pages at a time,
    stopping when a page has fewer recruits than page 1.
    """
    base_url = "https://247sports.com/Season/2025-Football/CompositeRecruitRankings/"
    scraper = cloudscraper.create_scraper()

    def fetch_page(page):
        url = f"{base_url}?Page={page}"
        resp = scraper.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select("ul.rankings-page__list li")
        logging.info(f"[recruiting] Page {page} → {len(items)} recruits")
        return page, items

    # prime page 1
    page, items = fetch_page(1)
    page_size = len(items)
    all_recruits = []

    def parse_items(items):
        recruits = []
        for li in items:
            name_tag = li.select_one(".rankings-page__name-link")
            if not name_tag:
                continue
            name = name_tag.get_text(strip=True)
            if name.lower() == "player":
                continue

            # position
            pos = (li.select_one("div.position") or BeautifulSoup("", "html.parser")).get_text(strip=True)

            # national & position ranks (default to 1000 if non‑numeric)
            raw_nat = (li.select_one("div.rank a.natrank") or BeautifulSoup("", "html.parser")).get_text(strip=True)
            try:
                nat_rank = int(raw_nat)
            except ValueError:
                nat_rank = 1000

            raw_posr = (li.select_one("div.rank a.posrank") or BeautifulSoup("", "html.parser")).get_text(strip=True)
            try:
                pos_rank = int(raw_posr)
            except ValueError:
                pos_rank = 1000

            # high school, city, state
            hs = city = state = ""
            meta = li.select_one("span.meta")
            if meta:
                txt = meta.get_text(strip=True)
                if "(" in txt and ")" in txt:
                    h, rest = txt.split("(", 1)
                    hs = h.strip()
                    rest = rest.rstrip(")")
                    parts = [p.strip() for p in rest.split(",")]
                    city = parts[0] if len(parts) > 0 else ""
                    state = parts[1] if len(parts) > 1 else ""
                else:
                    hs = txt

            # commit school
            commit_img = li.select_one("div.status a.img-link img.jsonly[title]")
            commit = commit_img["title"] if commit_img and commit_img.has_attr("title") else ""

            recruits.append({
                "name":           name,
                "national_rank":  nat_rank,
                "position_rank":  pos_rank,
                "position":       pos,
                "high_school":    hs,
                "city":           city,
                "state":          state,
                "commit":         commit,
            })
        return recruits

    # parse page 1
    all_recruits.extend(parse_items(items))

    # page through the rest
    page = 2
    while True:
        pages = list(range(page, page + batch_size))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(fetch_page, p): p for p in pages}
            stop = False
            for fut in as_completed(futures):
                p, its = fut.result()
                if len(its) < page_size:
                    logging.info(f"[recruiting] stopping at page {p} (only {len(its)} items)")
                    stop = True
                all_recruits.extend(parse_items(its))
            if stop:
                break
        page += batch_size

    return all_recruits

if __name__ == "__main__":
    recs = scrape_recruiting()
    print(f"Scraped {len(recs)} total recruits")
