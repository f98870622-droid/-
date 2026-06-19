"""Generate Avito-style review screenshots locally."""
import html
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "images" / "reviews"

SERVICE = "Ремонт и отделка квартир под ключ с гарантией"

REVIEWS = [
    {
        "name": "Кристина",
        "date": "8 января",
        "initial": "К",
        "avatar": "",
        "text": (
            "Искали бригаду в Домодедово на небольшой объём работ — переложить поддон "
            "в санузле и поклеить обои в одной из комнат. На такой объём исполнителя было "
            "очень тяжело найти, учитывая, что нужно было сделать всё оперативно перед "
            "въездом в квартиру. Спасибо, всё выполнили в срок!"
        ),
    },
    {
        "name": "Роман",
        "date": "20 сентября",
        "initial": "Р",
        "avatar": "avatar--b",
        "text": (
            "Большое спасибо за вашу работу! Делал ремонт, не понимая даже с чего начать… "
            "Мастер приехал, выслушал, согласовали объём работ, составили смету. "
            "По согласованию заказывал материалы и покупал сам, с предоставлением чеков. "
            "За плиткой и некоторыми материалами помогли — всё прошло отлично."
        ),
    },
    {
        "name": "Генрих Багдасаров",
        "date": "19 января 2024",
        "initial": "Г",
        "avatar": "avatar--g",
        "text": (
            "Всё как договаривались, отличный мастер! Всё объяснил, подсказал "
            "и выполнил работу качественно и в срок!"
        ),
    },
    {
        "name": "David",
        "date": "14 ноября 2023",
        "initial": "D",
        "avatar": "avatar--g",
        "text": (
            "Спасибо ребятам, всё на высшем уровне! Ценник порадовал. "
            "Сделали всё аккуратно, быстро и качественно! Будем обращаться только к вам!"
        ),
    },
    {
        "name": "Анжела",
        "date": "8 ноября 2023",
        "initial": "А",
        "avatar": "avatar--p",
        "text": (
            "Большое спасибо за проделанную работу. Ребята всё сделали качественно и в срок. "
            "Чувствуется опыт, профессионализм и умение подходить к работе. "
            "Осталась под впечатлением, только положительные эмоции. Однозначно рекомендую."
        ),
    },
]

STYLES = """
@font-face {
  font-family: Manrope;
  src: url('https://www.avito.st/s/common/assets/fonts/manrope/manrope-medium.woff2') format('woff2');
  font-weight: 500;
  font-style: normal;
}
@font-face {
  font-family: Manrope;
  src: url('https://www.avito.st/s/common/assets/fonts/manrope/manrope-bold.woff2') format('woff2');
  font-weight: 700;
  font-style: normal;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  width: 390px;
  background: #fff;
  font-family: Manrope, system-ui, -apple-system, sans-serif;
  color: #000;
  -webkit-font-smoothing: antialiased;
}
.wrap { padding: 16px; }
.summary {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 4px;
}
.summary__score { font-size: 32px; font-weight: 700; line-height: 1; letter-spacing: -0.02em; }
.summary__stars { color: #ffb021; font-size: 14px; letter-spacing: 2px; line-height: 1; }
.summary__count { font-size: 13px; color: #757575; margin-top: 4px; }
.card { padding: 16px 0; }
.head { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.avatar {
  width: 40px; height: 40px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 700; color: #0af; background: #ccecff;
}
.avatar--g { background: #ffe8cc; color: #f70; }
.avatar--p { background: #ecd4ff; color: #80f; }
.avatar--b { background: #d4f0ff; color: #08f; }
.name { font-size: 16px; font-weight: 700; line-height: 1.2; }
.meta { font-size: 13px; color: #757575; margin-top: 2px; }
.stars { color: #ffb021; font-size: 14px; letter-spacing: 2px; margin: 8px 0; line-height: 1; }
.tag { font-size: 13px; line-height: 1.35; color: #008000; margin-bottom: 8px; }
.tag span { color: #757575; }
.text { font-size: 15px; line-height: 1.45; color: #000; }
"""


def page_html(body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ru"><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=390, initial-scale=1">
<style>{STYLES}</style>
</head><body><div class="wrap">{body}</div></body></html>"""


def review_card(review: dict) -> str:
    name = html.escape(review["name"])
    date = html.escape(review["date"])
    text = html.escape(review["text"])
    initial = html.escape(review["initial"])
    avatar = html.escape(review["avatar"])
    avatar_cls = f"avatar {avatar}".strip()
    service = html.escape(SERVICE)
    return f"""
<article class="card">
  <div class="head">
    <span class="{avatar_cls}">{initial}</span>
    <div>
      <div class="name">{name}</div>
      <div class="meta">{date} · Клиент</div>
    </div>
  </div>
  <div class="stars">★★★★★</div>
  <div class="tag">Сделка состоялась <span>· {service}</span></div>
  <p class="text">{text}</p>
</article>"""


def summary_html() -> str:
    return """
<div class="summary">
  <div class="summary__score">5,0</div>
  <div>
    <div class="summary__stars">★★★★★</div>
    <div class="summary__count">5 отзывов</div>
  </div>
</div>"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 390, "height": 1200}, device_scale_factor=2)

        page.set_content(page_html(summary_html()), wait_until="networkidle")
        page.wait_for_selector(".summary")
        page.locator(".summary").screenshot(path=str(OUT_DIR / "avito-reviews-summary.png"))
        print("Saved avito-reviews-summary.png")

        all_cards = "".join(review_card(r) for r in REVIEWS)
        page.set_content(page_html(all_cards), wait_until="networkidle")
        page.wait_for_selector(".card")
        page.wait_for_timeout(500)

        cards = page.locator(".card")
        for i in range(cards.count()):
            cards.nth(i).screenshot(path=str(OUT_DIR / f"avito-review-{i + 1}.png"))
            print(f"Saved avito-review-{i + 1}.png")

        browser.close()
    print("Done")


if __name__ == "__main__":
    main()
