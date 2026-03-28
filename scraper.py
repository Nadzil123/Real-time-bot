from __future__ import annotations

import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from settings import Settings


class ConfigError(RuntimeError):
    pass


CACHE_DIR = Path("data")
RARITY_CACHE_FILE = CACHE_DIR / "rarity_cache.json"
logger = logging.getLogger("grow-a-garden-scraper")


@dataclass(frozen=True)
class PetRecord:
    name: str
    rarity: str
    token_price: str


@dataclass(frozen=True)
class ArticleCandidate:
    title: str
    url: str
    date_text: str
    sort_date: datetime


@dataclass(frozen=True)
class ScrapeResult:
    article_title: str
    article_url: str
    article_date: str
    records: list[PetRecord]


def scrape_latest_prices(settings: Settings) -> ScrapeResult:
    logger.info("Opening Fandom search page")
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = build_context(browser)
        page = context.new_page()
        apply_stealth(page)

        latest_article = select_latest_article(browser, page, settings)
        logger.info("Selected post: %s", latest_article.title)
        context.close()

        article_context = build_context(browser)
        article_page = article_context.new_page()
        apply_stealth(article_page)
        records = extract_pet_records_from_post(article_page, latest_article.url)
        logger.info("Parsed %s pet price rows from latest post", len(records))

        rarity_map = fetch_rarity_map(settings, [record.name for record in records])
        enriched_records = [
            PetRecord(
                name=record.name,
                rarity=rarity_map.get(record.name, "unknown"),
                token_price=record.token_price,
            )
            for record in records
        ]

        article_context.close()
        browser.close()

    if not enriched_records:
        raise ConfigError("No pet records were extracted from the latest value post.")

    return ScrapeResult(
        article_title=latest_article.title,
        article_url=latest_article.url,
        article_date=latest_article.date_text,
        records=enriched_records,
    )


def select_latest_article(browser, page, settings: Settings) -> ArticleCandidate:
    current_year = datetime.utcnow().year
    page.goto(settings.search_url, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)

    links = page.locator('a[href*="/f/p/"]')
    count = links.count()
    candidates: list[ArticleCandidate] = []

    for index in range(count):
        link = links.nth(index)
        title = normalize_whitespace(link.inner_text(timeout=1000))
        href = (link.get_attribute("href") or "").strip()
        if not href:
            continue
        if settings.post_keyword and settings.post_keyword not in f"{title} {href}".lower():
            continue

        container_text = ""
        try:
            container_text = normalize_whitespace(
                link.locator("xpath=ancestor-or-self::*[self::article or self::div or self::li][1]")
                .inner_text(timeout=1000)
            )
        except PlaywrightTimeoutError:
            container_text = title

        date_text = extract_best_date_text(container_text) or extract_best_date_text(title)
        sort_date = parse_date(date_text) or parse_date(title) or datetime.min

        candidates.append(
            ArticleCandidate(
                title=title or href,
                url=urljoin(settings.wiki_base_url, href),
                date_text=date_text,
                sort_date=sort_date,
            )
        )

    if not candidates:
        raise ConfigError("No Fandom value-list post candidates found on the search page.")

    logger.info("Found %s candidate value-list posts", len(candidates))
    deduped: dict[str, ArticleCandidate] = {}
    for candidate in sorted(candidates, key=lambda item: item.sort_date, reverse=True):
        deduped.setdefault(candidate.url, candidate)
    ordered_candidates = list(deduped.values())
    inspected_candidates: list[ArticleCandidate] = []

    for candidate in ordered_candidates[:10]:
        logger.info("Inspecting candidate post: %s", candidate.title)
        inspected = inspect_candidate_post(browser, candidate)
        if inspected is not None:
            inspected_candidates.append(inspected)

    if not inspected_candidates:
        logger.info("No token-aware post found after inspection, falling back to newest search result")
        return ordered_candidates[0]

    current_year_candidates = [
        candidate for candidate in inspected_candidates if candidate.sort_date.year == current_year
    ]
    if current_year_candidates:
        picked = sorted(current_year_candidates, key=lambda item: item.sort_date, reverse=True)[0]
        logger.info("Picked current-year token-aware post: %s", picked.title)
        return picked

    picked = sorted(inspected_candidates, key=lambda item: item.sort_date, reverse=True)[0]
    logger.info("Picked latest token-aware post from older year: %s", picked.title)
    return picked


def extract_pet_records_from_post(page, article_url: str) -> list[PetRecord]:
    logger.info("Opening latest value-list post")
    page.goto(article_url, wait_until="domcontentloaded")
    wait_for_real_content(page)
    text = page.locator("body").inner_text()
    records = parse_pet_lines(text)
    if records:
        return dedupe_records(records)

    raise ConfigError("Latest post loaded, but no pet lines were found in the post body.")


def inspect_candidate_post(browser, candidate: ArticleCandidate) -> ArticleCandidate | None:
    context = build_context(browser)
    page = context.new_page()
    apply_stealth(page)
    try:
        page.goto(candidate.url, wait_until="domcontentloaded")
        wait_for_real_content(page)
        text = f" {normalize_whitespace(page.locator('body').inner_text()).lower()} "
        has_token = any(
            keyword in text
            for keyword in (
                " token value ",
                " token values ",
                " tokens value ",
                " tokens values ",
                " listed token value ",
                " listed token values ",
                " tokens/",
                " tokens ",
                " add ~",
            )
        )
        if not has_token:
            return None

        date_text = extract_best_date_text(text) or candidate.date_text
        sort_date = parse_date(date_text) or candidate.sort_date
        return ArticleCandidate(
            title=candidate.title,
            url=candidate.url,
            date_text=date_text or candidate.title,
            sort_date=sort_date,
        )
    except Exception:
        return None
    finally:
        page.close()
        context.close()


def fetch_pet_rarity(settings: Settings, pet_name: str) -> str:
    page_title = resolve_pet_page_title(settings, pet_name)
    if not page_title:
        return "unknown"

    try:
        text = fetch_wiki_page_text(settings, page_title)
    except Exception:
        return "unknown"

    rarity = extract_rarity_from_text(text)
    return rarity or "unknown"


def resolve_pet_page_title(settings: Settings, pet_name: str) -> str:
    endpoint = (
        f"{settings.wiki_base_url}/api.php?action=query&list=search&namespace=0&format=json&srlimit=10"
        f"&srsearch={quote(pet_name)}"
    )
    response = requests.get(endpoint, timeout=30, headers={"User-Agent": settings.user_agent})
    response.raise_for_status()
    payload = response.json()
    titles = [item.get("title", "") for item in payload.get("query", {}).get("search", [])]
    if not titles:
        return pet_name

    normalized_name = pet_name.lower()
    for title in titles:
        lower = title.lower()
        if lower == normalized_name or lower == f"{normalized_name} (pet)":
            return title
    for title in titles:
        if "(pet)" in title.lower():
            return title
    for title in titles:
        if normalized_name in title.lower():
            return title
    return pet_name


def fetch_wiki_page_text(settings: Settings, page_title: str) -> str:
    endpoint = (
        f"{settings.wiki_base_url}/api.php?action=parse&prop=text&format=json"
        f"&page={quote(page_title)}"
    )
    response = requests.get(endpoint, timeout=10, headers={"User-Agent": settings.user_agent})
    response.raise_for_status()
    payload = response.json()
    html = payload.get("parse", {}).get("text", {}).get("*", "")
    soup = BeautifulSoup(html, "lxml")
    return normalize_whitespace(soup.get_text(" ", strip=True))


def fetch_rarity_map(settings: Settings, pet_names: list[str]) -> dict[str, str]:
    unique_names = list(dict.fromkeys(pet_names))
    cache = load_rarity_cache()
    missing = [name for name in unique_names if name not in cache]
    logger.info(
        "Rarity cache: %s hit, %s miss",
        len(unique_names) - len(missing),
        len(missing),
    )

    if missing:
        with ThreadPoolExecutor(max_workers=8) as executor:
            future_map = {
                executor.submit(fetch_pet_rarity, settings, name): name for name in missing
            }
            completed = 0
            for future in as_completed(future_map):
                name = future_map[future]
                try:
                    cache[name] = future.result()
                except Exception:
                    cache[name] = "unknown"
                completed += 1
                if completed == 1 or completed == len(missing) or completed % 5 == 0:
                    logger.info("Rarity lookup progress: %s/%s", completed, len(missing))
        save_rarity_cache(cache)

    return {name: cache.get(name, "unknown") for name in unique_names}


def load_rarity_cache() -> dict[str, str]:
    if not RARITY_CACHE_FILE.exists():
        return {}
    import json

    return json.loads(RARITY_CACHE_FILE.read_text())


def save_rarity_cache(cache: dict[str, str]) -> None:
    import json

    CACHE_DIR.mkdir(exist_ok=True)
    RARITY_CACHE_FILE.write_text(json.dumps(cache, indent=2, sort_keys=True))


def extract_rarity_from_text(text: str) -> str:
    normalized = normalize_whitespace(text)
    patterns = [
        r"is an? ([A-Za-z-]+) pet",
        r"rarity\s+([A-Za-z-]+)",
        r"in:\s+[^.]*?\b(common|uncommon|rare|legendary|mythical|divine|prismatic)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if match:
            return match.group(1).lower()
    return ""


def parse_pet_lines(text: str) -> list[PetRecord]:
    records: list[PetRecord] = []
    seen_section = False
    stop_markers = (
        "And that's the list",
        "This is probably the last value list",
        "With the sheer number of pets",
        "VIEW OLDER REPLIES",
        "What do you think?",
        "GROW A GARDEN FEED",
    )

    for raw_line in text.splitlines():
        line = normalize_whitespace(raw_line)
        if not line:
            continue
        if "Values are in terms of mimics" in line or "actual value list" in line.lower():
            seen_section = True
            continue
        if not seen_section:
            continue
        if any(marker in line for marker in stop_markers):
            break

        match = re.fullmatch(
            r"(?:\d{1,3}\.\s*)?([A-Za-z][A-Za-z0-9' \-/]+?)\s*\(([^)]+)\)\s*(?:🔥|⬆️|🔽)?",
            line,
        )
        if not match:
            continue

        name = clean_pet_name(match.group(1))
        token_price = normalize_whitespace(match.group(2))
        if name and token_price:
            records.append(PetRecord(name=name, rarity="", token_price=token_price))

    return records


def extract_best_date_text(value: str) -> str:
    patterns = [
        r"\b(?:\d{1,2}/\d{1,2}/20\d{2})\b",
        r"\b(?:[A-Z][a-z]+ \d{1,2}, 20\d{2})\b",
        r"\b(?:\d{1,2} [A-Z][a-z]+ 20\d{2})\b",
        r"\b20\d{2}\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(0)
    return ""


def clean_pet_name(value: str) -> str:
    value = normalize_whitespace(value)
    value = re.sub(r"\s*🔥+$", "", value).strip()
    return value


def apply_stealth(page) -> None:
    page.add_init_script(
        """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
Object.defineProperty(navigator, 'language', {get: () => 'en-US'});
Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
window.chrome = { runtime: {} };
"""
    )


def build_context(browser):
    return browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1366, "height": 768},
        locale="en-US",
    )


def wait_for_real_content(page, max_wait_ms: int = 10000) -> None:
    elapsed = 0
    step = 1000
    while elapsed < max_wait_ms:
        text = page.locator("body").inner_text()
        if "Performing security verification" not in text:
            return
        page.wait_for_timeout(step)
        elapsed += step


def dedupe_records(records: list[PetRecord]) -> list[PetRecord]:
    deduped: list[PetRecord] = []
    seen: set[tuple[str, str]] = set()
    for record in records:
        key = (record.name.lower(), record.token_price.lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)
    return deduped


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def parse_date(value: str) -> datetime | None:
    value = value.strip()
    if not value:
        return None

    parsed = try_parse_iso(value) or try_parse_email_date(value) or try_parse_common_formats(value)
    if parsed:
        return parsed.replace(tzinfo=None)
    return None


def try_parse_iso(value: str) -> datetime | None:
    try:
        normalized = value.replace("Z", "+00:00")
        return datetime.fromisoformat(normalized)
    except ValueError:
        return None


def try_parse_email_date(value: str) -> datetime | None:
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None


def try_parse_common_formats(value: str) -> datetime | None:
    formats = [
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    match = re.search(r"(20\d{2})", value)
    if match:
        return datetime(int(match.group(1)), 1, 1)
    return None
