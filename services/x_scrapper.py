from playwright.async_api import async_playwright
from datetime import datetime
import asyncio
import csv, os
import urllib.parse
from .csv_utils import load_unique_csv_keys

async def search_x(
    auth_token: str,
    ct0: str,
    query: str,
    start_date: datetime,
    end_date: datetime,
    output_file: str,
    scroll_count: int = 20,
    scroll_delay_seconds: float = 3,
):
    collected = []

    fieldnames = ["id", "text", "posted_at", "likes", "retweets", "replies", "views", "username", "display_name", "is_verified", "link"]
    seen_ids, seen_links = load_unique_csv_keys(output_file, fieldnames)

    async def intercept_response(response):
        if "SearchTimeline" in response.url:
            try:
                data = await response.json()
                instructions = (
                    data.get("data", {})
                        .get("search_by_raw_query", {})
                        .get("search_timeline", {})
                        .get("timeline", {})
                        .get("instructions", [])
                )
                for instruction in instructions:
                    entries = instruction.get("entries", [])
                    for entry in entries:
                        tweet_data = (
                            entry.get("content", {})
                                .get("itemContent", {})
                                .get("tweet_results", {})
                                .get("result", {})
                        )
                        if not tweet_data:
                            continue

                        core = tweet_data.get("core", {}).get("user_results", {}).get("result", {})
                        legacy = tweet_data.get("legacy", {})

                        if not legacy:
                            tweet_data = tweet_data.get("tweet", tweet_data)
                            core = tweet_data.get("core", {}).get("user_results", {}).get("result", {})
                            legacy = tweet_data.get("legacy", {})

                        user_core = core.get("core", {})
                        tweet_id = str(legacy.get("id_str") or "").strip()

                        if not tweet_id:
                            continue

                        created_at = datetime.strptime(legacy.get("created_at", ""), "%a %b %d %H:%M:%S +0000 %Y")
                        if not (start_date <= created_at <= end_date):
                            continue

                        username = user_core.get("screen_name", "")
                        display_name = user_core.get("name", "")
                        is_verified = core.get("is_blue_verified", False)
                        tweet_link = f"https://x.com/{username}/status/{tweet_id}"

                        if tweet_id in seen_ids or tweet_link in seen_links:
                            continue

                        row = {
                            "id": tweet_id,
                            "text": legacy.get("full_text", "").replace("\n", " "),
                            "posted_at": created_at.isoformat(),
                            "views": tweet_data.get("views", {}).get("count", "0"),
                            "likes": legacy.get("favorite_count", ""),
                            "retweets": legacy.get("retweet_count", ""),
                            "replies": legacy.get("reply_count", ""),
                            "username": username,
                            "display_name": display_name,
                            "is_verified": is_verified,
                            "link": tweet_link
                        }

                        file_exists = os.path.exists(output_file)
                        with open(output_file, "a", newline="", encoding="utf-8") as f:
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            if not file_exists:
                                writer.writeheader()
                            writer.writerow(row)

                        seen_ids.add(tweet_id)
                        seen_links.add(tweet_link)
                        collected.append(row)
                        print(f"[+] Data Baru ({len(collected)}) | {row['posted_at']} | {row['text'][:50]}...")

            except Exception as e:
                # Silenced parsing error to avoid clutter
                pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        await context.add_cookies([
            {"name": "auth_token", "value": auth_token, "domain": ".x.com", "path": "/"},
            {"name": "ct0", "value": ct0, "domain": ".x.com", "path": "/"},
        ])

        page = await context.new_page()
        page.on("response", intercept_response)

        # Encode query
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://x.com/search?q={encoded_query}&f=live"

        await page.goto("https://x.com", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
        await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)

        print(f"\nBrowser terbuka. Memulai pencarian '{query}' dengan {scroll_count} kali auto-scroll...")
        
        # Logika Automasi Scroll
        for i in range(scroll_count):
            await page.evaluate("window.scrollBy(0, 1500);")
            await asyncio.sleep(scroll_delay_seconds)
            print(f"[*] Sedang scrolling... ({i + 1}/{scroll_count})")

        await browser.close()

    print(f"\n[Selesai] {len(collected)} tweet baru berhasil disimpan ke {output_file}")
    return collected
