from playwright.async_api import async_playwright
from datetime import datetime
import asyncio
import csv, os
import urllib.parse
from .csv_utils import load_unique_csv_keys

async def search_tiktok(
    ms_token: str,
    session_id: str,
    query: str,
    start_date: datetime,
    end_date: datetime,
    output_file: str,
    scroll_count: int = 20,
    scroll_delay_seconds: float = 3,
):
    collected = []
    fieldnames = [
        "id", "caption", "posted_at", "play_count", "like_count", "comment_count",
        "share_count", "save_count", "repost_count", "username", "display_name",
        "is_verified", "hashtags", "is_ad", "aigc_description", "is_ai_generated", "link"
    ]
    seen_ids, seen_links = load_unique_csv_keys(output_file, fieldnames)

    async def intercept_response(response):
        if "api/search/item/full" in response.url:
            try:
                data = await response.json()
                items = data.get("data", []) or data.get("item_list", [])
                for item in items:
                    video_info = item.get("item", item)
                    raw_video_id = video_info.get("id")
                    video_id = str(raw_video_id).strip() if raw_video_id is not None else ""
                    if not video_id or video_id in seen_ids:
                        continue

                    create_time = video_info.get("createTime", 0)
                    created_at = datetime.fromtimestamp(create_time) if create_time else None

                    if created_at and not (start_date <= created_at <= end_date):
                        continue

                    stats = video_info.get("statsV2", video_info.get("stats", {}))
                    author = video_info.get("author", {})
                    video_link = f"https://www.tiktok.com/@{author.get('uniqueId', '')}/video/{video_id}"
                    if video_link in seen_links:
                        continue

                    hashtags = [t["hashtagName"] for t in video_info.get("textExtra", []) if "hashtagName" in t]
                    aigc_desc = video_info.get("AIGCDescription", "")

                    row = {
                        "id": video_id,
                        "caption": video_info.get("desc", ""),
                        "posted_at": created_at.isoformat() if created_at else "",
                        "play_count": stats.get("playCount", ""),
                        "like_count": stats.get("diggCount", ""),
                        "comment_count": stats.get("commentCount", ""),
                        "share_count": stats.get("shareCount", ""),
                        "save_count": stats.get("collectCount", ""),
                        "repost_count": stats.get("repostCount", ""),
                        "username": author.get("uniqueId", ""),
                        "display_name": author.get("nickname", ""),
                        "is_verified": author.get("verified", False),
                        "hashtags": ", ".join(hashtags),
                        "is_ad": video_info.get("isAd", False),
                        "aigc_description": aigc_desc,
                        "is_ai_generated": bool(aigc_desc),
                        "link": video_link
                    }

                    file_exists = os.path.exists(output_file)
                    with open(output_file, "a", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        if not file_exists:
                            writer.writeheader()
                        writer.writerow(row)

                    seen_ids.add(video_id)
                    seen_links.add(video_link)
                    collected.append(row)
                    print(f"[+] Data Baru ({len(collected)}) | {row['posted_at']} | {row['caption'][:50]}...")

            except Exception:
                pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        await context.add_cookies([
            {"name": "msToken", "value": ms_token, "domain": ".tiktok.com", "path": "/"},
            {"name": "sessionid", "value": session_id, "domain": ".tiktok.com", "path": "/"},
        ])

        page = await context.new_page()
        page.on("response", intercept_response)

        # Encode query
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.tiktok.com/search/video?q={encoded_query}"
        
        await page.goto(search_url, wait_until="networkidle", timeout=30000)

        print(f"\nBrowser terbuka. Memulai pencarian '{query}' dengan {scroll_count} kali auto-scroll...")
        
        # Logika Automasi Scroll
        for i in range(scroll_count):
            await page.evaluate("window.scrollBy(0, 1500);")
            await asyncio.sleep(scroll_delay_seconds)
            print(f"[*] Sedang scrolling... ({i + 1}/{scroll_count})")

        await browser.close()

    print(f"\n[Selesai] {len(collected)} video baru berhasil disimpan ke {output_file}")
    return collected
