#!/usr/bin/env python3
"""
Monitor für freie Termine bei der Münchner Führerscheinstelle
(Umschreibung eines ausländischen Führerscheins).

Fragt das Backend der offiziellen Terminbuchung ab und schickt eine
Telegram-Nachricht, sobald freie Tage auftauchen.

Benötigte Umgebungsvariablen:
  TELEGRAM_BOT_TOKEN  - Token von @BotFather
  TELEGRAM_CHAT_ID    - Chat-ID(s) (z.B. via @userinfobot), mehrere durch Komma getrennt;
                        auch eine Gruppen-ID (negativ), wenn der Bot in der Gruppe ist
"""

import hashlib
import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

# --- Konfiguration -----------------------------------------------------------
# Service: Umschreibung eines ausländischen Führerscheins
SERVICE_ID = "1071896"
# Standort: Führerscheinstelle, Garmischer Str. 19-21
OFFICE_ID = "10308174"

# Falls sich der Endpoint ändert: in der Buchungsseite
# https://stadt.muenchen.de/buergerservice/terminvereinbarung.html#/services/1071896/locations/10308174
# DevTools -> Network öffnen und den "available-calendar"-Request kopieren.
BASE_URL = "https://www48.muenchen.de/buergeransicht/api/citizen/available-calendar/"

BOOKING_URL = (
    "https://stadt.muenchen.de/buergerservice/terminvereinbarung.html"
    "#/services/1071896/locations/10308174"
)

TZ = ZoneInfo("Europe/Berlin")
STATE_FILE = Path(".last_state")  # verhindert doppelte Benachrichtigungen
LOOKAHEAD_DAYS = 180
# -----------------------------------------------------------------------------


def fetch_available_days() -> list[str]:
    start = date.today()
    end = start + timedelta(days=LOOKAHEAD_DAYS)
    params = {
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "officeIds": OFFICE_ID,
        "serviceIds": SERVICE_ID,
        "serviceCounts": "1",
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) TerminMonitor/1.0",
        "Accept": "application/json",
    }
    resp = requests.get(BASE_URL, params=params, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # Die API liefert {"availableDays": [...]} oder {"errors": [{"errorCode": ...}]}
    if isinstance(data, list):
        return [str(d) for d in data]
    if isinstance(data, dict):
        if "availableDays" in data and isinstance(data["availableDays"], list):
            return [format_day(d) for d in data["availableDays"]]
        if data.get("errors"):
            codes = ", ".join(str(e.get("errorCode")) for e in data["errors"])
            print(f"API: {codes} - keine Termine.")
            return []
    print(f"Unerwartete Antwort: {json.dumps(data)[:500]}")
    return []


def format_day(d) -> str:
    """{"date": "2026-09-08", "offices": [{"appointments": [unix, ...]}]} -> "2026-09-08 10:00, 10:30" """
    if not isinstance(d, dict):
        return str(d)
    stamps = sorted(t for o in d.get("offices", []) for t in o.get("appointments", []))
    times = ", ".join(datetime.fromtimestamp(t, TZ).strftime("%H:%M") for t in stamps)
    return f"{d['date']} {times}" if times else d["date"]


def send_telegram(text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    for chat_id in os.environ["TELEGRAM_CHAT_ID"].split(","):
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id.strip(), "text": text, "disable_web_page_preview": True},
            timeout=30,
        )
        if not resp.ok:
            print(f"Telegram-Fehler für Chat {chat_id.strip()}: {resp.status_code} {resp.text[:200]}")


def main() -> int:
    try:
        days = fetch_available_days()
    except Exception as e:
        print(f"Fehler beim Abruf: {e}")
        return 0  # Workflow nicht rot färben wegen eines einzelnen Fehlschlags

    state = hashlib.sha256(",".join(sorted(days)).encode()).hexdigest()
    last_state = STATE_FILE.read_text().strip() if STATE_FILE.exists() else ""

    if days and state != last_state:
        preview = "\n".join(days[:10]) + ("\n..." if len(days) > 10 else "")
        send_telegram(
            "🚗 Führerscheinstelle München: freie Termine!\n"
            f"Tage:\n{preview}\n\n"
            f"Sofort buchen: {BOOKING_URL}"
        )
        print(f"Benachrichtigung gesendet. Tage: {days}")
    elif days:
        print(f"Termine unverändert verfügbar ({len(days)} Tage), keine neue Nachricht.")
    else:
        print("Keine freien Termine.")

    STATE_FILE.write_text(state)
    return 0


if __name__ == "__main__":
    sys.exit(main())
