import logging

from scraper import scrape_latest_prices
from settings import load_settings


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = load_settings()
    print("Starting preview run...")
    result = scrape_latest_prices(settings)
    print(f"Artikel terbaru: {result.article_title}")
    print(f"URL: {result.article_url}")
    print(f"Tanggal: {result.article_date}")
    print("")
    for item in result.records:
        print(f"{item.name} | rarity: {item.rarity or '-'} | token: {item.token_price}")


if __name__ == "__main__":
    main()
