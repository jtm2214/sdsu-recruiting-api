# utils/sheets.py

import os
import time
import logging
import urllib.parse

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import APIError

import json
from oauth2client.service_account import ServiceAccountCredentials


# ─── Module‐level caches ────────────────────────────────────────────────────────

_GC = None
_WS_CACHE = {}

def _init_client():
    global _GC
    if _GC is None:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]
        raw = os.getenv("GOOGLE_CREDS_JSON")
        if raw and raw.strip().startswith("{"):
            info = json.loads(raw)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(info, scope)
        else:
            # fallback to a file path
            path = raw or "creds.json"
            creds = ServiceAccountCredentials.from_json_keyfile_name(path, scope)
        _GC = gspread.authorize(creds)
    return _GC

def _retry(func, *args, **kwargs):
    delay = 1
    for attempt in range(5):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            code = getattr(getattr(e, "response", None), "status_code", None)
            if code == 429 or "429" in str(e):
                logging.warning(f"[sheets] rate‐limit, retry {attempt+1}/5 in {delay}s…")
                time.sleep(delay)
                delay *= 2
                continue
            raise
    return func(*args, **kwargs)

def get_worksheet(sheet_name, worksheet_name="Sheet1"):
    key = (sheet_name, worksheet_name)
    if key not in _WS_CACHE:
        gc = _init_client()
        def _open():
            sh = gc.open(sheet_name)
            return sh.worksheet(worksheet_name)
        _WS_CACHE[key] = _retry(_open)
    return _WS_CACHE[key]

# ─── Public exports ────────────────────────────────────────────────────────────

def update_recruits_sheet(data, sheet_name, worksheet_name="Sheet1"):
    """
    Columns: Name (hyperlink) | National Rank | Position Rank | Position |
             High School | City | State | Commit
    """
    # Default to your Render URL; override via env
    base = os.getenv("AI_BIO_BASE_URL", "https://your-app.onrender.com")
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
        name   = r.get("name","")
        school = r.get("high_school","")
        n_enc  = urllib.parse.quote_plus(name)
        s_enc  = urllib.parse.quote_plus(school)
        link   = (
            f'=HYPERLINK("{base}/bio?name={n_enc}&school={s_enc}",'
            f'"{name}")'
        )
        rows.append([
            link,
            r.get("national_rank",""),
            r.get("position_rank",""),
            r.get("position",""),
            school,
            r.get("city",""),
            r.get("state",""),
            r.get("commit",""),
        ])

    ws = get_worksheet(sheet_name, worksheet_name)
    _retry(ws.clear)
    # <-- USER_ENTERED so formulas are active
    _retry(ws.update, "A1", rows, {"value_input_option":"USER_ENTERED"})
    logging.info(f"[sheets] recruited → {len(data)} rows written")

def update_portal_sheet(data, sheet_name, worksheet_name="Sheet1"):
    """
    Columns: Name (hyperlink) | From School | To School | Position |
             Rating | Status | Update Date | Stars
    """
    base = os.getenv("AI_BIO_BASE_URL", "https://your-app.onrender.com")
    headers = [
        "Name",
        "From School",
        "To School",
        "Position",
        "Rating",
        "Status",
        "Update Date",
        "Stars",
    ]
    rows = [headers]

    for idx, e in enumerate(data, start=2):
        name  = e.get("name","")
        frm   = e.get("from_school","")
        n_enc = urllib.parse.quote_plus(name)
        s_enc = urllib.parse.quote_plus(frm)
        link  = (
            f'=HYPERLINK("{base}/bio?name={n_enc}&school={s_enc}",'
            f'"{name}")'
        )

        # build stars formula against E-column
        rating_cell  = f"E{idx}"
        stars_formula = (
            f'=REPT("★",IFS('
            f'{rating_cell}>=0.98,5,'
            f'{rating_cell}>=0.90,4,'
            f'{rating_cell}>=0.80,3,'
            f'{rating_cell}>=0.70,2,'
            f'TRUE,0'
            f'))'
        )

        rows.append([
            link,
            frm,
            e.get("to_school",""),
            e.get("position",""),
            e.get("rating",""),
            e.get("status",""),
            e.get("update_date",""),
            stars_formula,
        ])

    ws = get_worksheet(sheet_name, worksheet_name)
    _retry(ws.clear)
    _retry(ws.update, "A1", rows, {"value_input_option":"USER_ENTERED"})
    logging.info(f"[sheets] portal → {len(data)} rows written")
