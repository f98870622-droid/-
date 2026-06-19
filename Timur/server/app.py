"""
Сервер обработки заявок с калькулятора.
1. Сохранение в SQLite (локальная БД на сервере в РФ)
2. Уведомление в Telegram после успешной записи
"""
import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

# Корень проекта (родитель папки server/)
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "leads.db"

load_dotenv(ROOT / ".env")

app = Flask(__name__, static_folder=str(ROOT), static_url_path="")


def get_db() -> sqlite3.Connection:
    """Подключение к SQLite с row_factory для удобного доступа к полям."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Создание таблицы заявок при первом запуске."""
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                category TEXT,
                service TEXT,
                area INTEGER,
                estimate_min INTEGER,
                estimate_max INTEGER,
                consent INTEGER NOT NULL DEFAULT 0,
                ip_address TEXT,
                user_agent TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def normalize_phone(phone: str) -> str:
    """Оставляем только цифры; для РФ — 11 цифр с ведущей 7."""
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    if digits.startswith("7") and len(digits) == 11:
        return "+" + digits
    return phone.strip()


def validate_lead_payload(data: dict) -> tuple[bool, str]:
    """Базовая валидация полей формы."""
    name = (data.get("name") or "").strip()
    phone = normalize_phone(data.get("phone") or "")

    if len(name) < 2:
        return False, "Укажите имя (минимум 2 символа)"
    if len(re.sub(r"\D", "", phone)) < 11:
        return False, "Укажите корректный номер телефона"
    if not data.get("consent"):
        return False, "Необходимо согласие на обработку персональных данных"
    if not data.get("category") or not data.get("service"):
        return False, "Не переданы параметры расчёта"

    return True, ""


def save_lead(data: dict, ip: str | None, user_agent: str | None) -> int:
    """Запись заявки в локальную SQLite."""
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        cur = conn.execute(
            """
            INSERT INTO leads (
                name, phone, category, service, area,
                estimate_min, estimate_max, consent,
                ip_address, user_agent, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data["name"].strip(),
                normalize_phone(data["phone"]),
                data.get("category"),
                data.get("service"),
                data.get("area"),
                data.get("estimate_min"),
                data.get("estimate_max"),
                1 if data.get("consent") else 0,
                ip,
                user_agent,
                now,
            ),
        )
        conn.commit()
        return int(cur.lastrowid)


def format_telegram_message(lead_id: int, data: dict) -> str:
    """Форматирование уведомления для Telegram."""
    lines = [
        "🛠 <b>Новая заявка с сайта</b>",
        f"🆔 ID: {lead_id}",
        "",
        f"👤 <b>Имя:</b> {data['name'].strip()}",
        f"📞 <b>Телефон:</b> {normalize_phone(data['phone'])}",
        "",
        "📋 <b>Параметры расчёта:</b>",
        f"• Категория: {data.get('category', '—')}",
        f"• Услуга: {data.get('service', '—')}",
    ]
    if data.get("area"):
        lines.append(f"• Площадь: {data['area']} м²")
    if data.get("estimate_min") and data.get("estimate_max"):
        lines.append(
            f"• Вилка стоимости: {data['estimate_min']:,} – {data['estimate_max']:,} ₽".replace(",", " ")
        )
    lines.extend(["", "✅ Согласие на обработку ПДн получено"])
    return "\n".join(lines)


def send_telegram_notification(text: str) -> None:
    """
    Отправка сообщения в Telegram Bot API.
    Вызывается только после успешной записи в БД.
    """
    token = os.getenv("TG_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TG_CHAT_ID", "").strip()

    if not token or not chat_id:
        app.logger.warning("TG_BOT_TOKEN или TG_CHAT_ID не заданы — уведомление пропущено")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    resp.raise_for_status()
    body = resp.json()
    if not body.get("ok"):
        raise RuntimeError(f"Telegram API error: {body}")


@app.after_request
def add_cors_headers(response):
    """CORS для локальной разработки (фронт и API на одном origin — не обязателен)."""
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/api/leads", methods=["POST", "OPTIONS"])
def create_lead():
    """Приём заявки: валидация → SQLite → Telegram."""
    if request.method == "OPTIONS":
        return "", 204

    data = request.get_json(silent=True) or {}
    ok, err = validate_lead_payload(data)
    if not ok:
        return jsonify({"ok": False, "error": err}), 400

    # Опциональная проверка секрета (для продакшена)
    api_secret = os.getenv("API_SECRET", "").strip()
    if api_secret and request.headers.get("X-API-Secret") != api_secret:
        return jsonify({"ok": False, "error": "Доступ запрещён"}), 403

    try:
        lead_id = save_lead(
            data,
            ip=request.headers.get("X-Forwarded-For", request.remote_addr),
            user_agent=request.headers.get("User-Agent"),
        )
    except Exception as exc:
        app.logger.exception("Ошибка записи в БД: %s", exc)
        return jsonify({"ok": False, "error": "Ошибка сохранения заявки"}), 500

    # Дублирование в Telegram — только после успешной записи
    try:
        send_telegram_notification(format_telegram_message(lead_id, data))
    except Exception as exc:
        app.logger.exception("Telegram notify failed for lead %s: %s", lead_id, exc)
        return jsonify({
            "ok": True,
            "id": lead_id,
            "warning": "Заявка сохранена, но уведомление в Telegram не отправлено",
        }), 201

    return jsonify({"ok": True, "id": lead_id}), 201


@app.route("/")
def index():
    return send_from_directory(ROOT, "index.html")


@app.route("/legal/<path:filename>")
def legal_files(filename):
    return send_from_directory(ROOT / "legal", filename)


if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_DEBUG") == "1")
