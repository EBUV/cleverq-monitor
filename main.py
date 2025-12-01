import os
import json
import time
from datetime import datetime, date
from urllib.request import urlopen, Request
from urllib.parse import urlencode

# === НАСТРОЙКИ ЧЕРЕЗ ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ===
# можно менять их на Render, не трогая код

# как часто проверять (в секундах), по умолчанию 60 сек
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))

# порог, раньше какой даты слать уведомление (формат YYYY-MM-DD)
THRESHOLD_DATE_STR = os.getenv("THRESHOLD_DATE", "2026-04-01")
THRESHOLD_DATE = datetime.strptime(THRESHOLD_DATE_STR, "%Y-%m-%d").date()

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# URL cleverQ (твой эндпоинт)
CLEVQ_URL = (
    "https://cqm3.cleverq.de/api/external/v4/sites/49/appointments/available_days"
    "?service_id=259"
    "&from_day=2025-12-01"
    "&to_day=2026-12-06"
    "&mode_active=false"
    "&subtask_items%5B%5D=%7B%22subtask_id%22:653,%22number%22:1%7D"
    "&booking_session_key=KG1RSdAcCIJtbxSX-m9ETA"
)


def log(msg: str):
    print(f"[{datetime.utcnow().isoformat()}] {msg}", flush=True)


def send_telegram(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": text}).encode("utf-8")
    req = Request(url, data=data, method="POST")
    with urlopen(req, timeout=10) as resp:
        resp.read()  # просто чтобы выполнить запрос


def fetch_available_days():
    req = Request(CLEVQ_URL, method="GET")
    with urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def get_earliest(data):
    # формат: {"duration_minutes":40,"available_days":[{"day":"2026-03-17"}, ...]}
    days = []
    for item in data.get("available_days", []):
        d = datetime.strptime(item["day"], "%Y-%m-%d").date()
        days.append(d)
    return min(days) if days else None


def main():
    log(f"Старт мониторинга cleverQ, интервал {CHECK_INTERVAL} c, порог {THRESHOLD_DATE}…")
    while True:
        try:
            data = fetch_available_days()
            earliest = get_earliest(data)
            log(f"Самая ранняя дата сейчас: {earliest}")

            if earliest and earliest < THRESHOLD_DATE:
                msg = f"⚠️ Появился РАННИЙ термин: {earliest}\nБеги бронировать!"
                log(msg)
                send_telegram(msg)
                # если хочешь, можешь здесь сделать break, чтобы воркер завершался
        except Exception as e:
            log(f"Ошибка при проверке: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
