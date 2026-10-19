import asyncio
import os

from dotenv import load_dotenv

import config
from services.satellite_scrapper import get_satellite_image
from services.tiktok_scrapper import search_tiktok
from services.x_scrapper import search_x


def require_credentials(variable_names: tuple[str, ...]) -> dict[str, str]:
    """Ambil kredensial yang diperlukan dan gagalkan dengan pesan yang jelas."""
    credentials = {name: os.getenv(name, "").strip() for name in variable_names}
    missing = [name for name, value in credentials.items() if not value]
    if missing:
        names = ", ".join(missing)
        raise RuntimeError(
            f"Kredensial untuk scraper aktif belum diisi: {names}. "
            "Isi nilainya di file .env atau nonaktifkan scraper terkait di config.py."
        )
    return credentials


async def main() -> None:
    load_dotenv()

    enabled_scrapers = [
        name
        for name, enabled in (
            ("X", config.ENABLE_X),
            ("TikTok", config.ENABLE_TIKTOK),
            ("satelit", config.ENABLE_SATELLITE),
        )
        if enabled
    ]
    if not enabled_scrapers:
        print("Tidak ada scraper aktif. Atur ENABLE_* di config.py.")
        return

    # Validasi dilakukan sebelum proses dimulai agar tidak berhenti di tengah jalan.
    credentials: dict[str, str] = {}
    if config.ENABLE_X:
        credentials.update(require_credentials(("AUTH_TOKEN", "CT0")))
    if config.ENABLE_TIKTOK:
        credentials.update(require_credentials(("MS_TOKEN", "SESSION_ID")))

    print(f"Scraper aktif: {', '.join(enabled_scrapers)}")
    if config.ENABLE_X or config.ENABLE_TIKTOK:
        print(f"Kata kunci: '{config.SEARCH_QUERY}'")

    if config.ENABLE_X:
        await search_x(
            auth_token=credentials["AUTH_TOKEN"],
            ct0=credentials["CT0"],
            query=config.SEARCH_QUERY,
            start_date=config.START_DATE,
            end_date=config.END_DATE,
            output_file=config.X_OUTPUT_FILE,
            scroll_count=config.SCROLL_COUNT,
            scroll_delay_seconds=config.SCROLL_DELAY_SECONDS,
        )

    if config.ENABLE_TIKTOK:
        await search_tiktok(
            ms_token=credentials["MS_TOKEN"],
            session_id=credentials["SESSION_ID"],
            query=config.SEARCH_QUERY,
            start_date=config.START_DATE,
            end_date=config.END_DATE,
            output_file=config.TIKTOK_OUTPUT_FILE,
            scroll_count=config.SCROLL_COUNT,
            scroll_delay_seconds=config.SCROLL_DELAY_SECONDS,
        )

    if config.ENABLE_SATELLITE:
        await get_satellite_image(
            lat=config.SATELLITE_LATITUDE,
            lon=config.SATELLITE_LONGITUDE,
            zoom=config.SATELLITE_ZOOM,
            date=config.SATELLITE_DATE,
            output_folder=config.SATELLITE_OUTPUT_FOLDER,
        )


if __name__ == "__main__":
    asyncio.run(main())
