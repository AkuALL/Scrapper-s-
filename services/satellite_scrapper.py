from playwright.async_api import async_playwright
import asyncio
import os

async def get_satellite_image(lat: float, lon: float, zoom: int, date: str, output_folder: str = "data/satellite"):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    file_name = f"sungai_{lat}_{lon}_{date}.png"
    file_path = os.path.join(output_folder, file_name)

    url = f"https://zoom.earth/maps/satellite/#view={lat},{lon},{zoom}z/date={date},pm"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720}
        )
        page = await context.new_page()

        print(f"\n[+] Membuka citra satelit di titik {lat}, {lon} pada tanggal {date}...")
        
        await page.goto(url, wait_until="networkidle", timeout=60000)

        try:
            await page.evaluate("""
                document.querySelectorAll('.panel, .header, .timeline, .zoom').forEach(el => el.style.display = 'none');
            """)
        except Exception:
            pass 

        await asyncio.sleep(5) 

        print(f"[*] Mengambil screenshot layar...")
        await page.screenshot(path=file_path)

        await browser.close()

    print(f"[V] Gambar satelit berhasil disimpan di {file_path}\n")
    return file_path