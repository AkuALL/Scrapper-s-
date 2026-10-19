"""Pengaturan scraping yang aman untuk diubah antar pencarian."""

from datetime import datetime


# Kata kunci dan rentang tanggal untuk pencarian media sosial.
SEARCH_QUERY = "listrik putus"
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2026, 12, 31)

# Aktifkan scraper yang ingin dijalankan.
ENABLE_X = True
ENABLE_TIKTOK = False
ENABLE_SATELLITE = False

# Pengaturan hasil scraping media sosial.
SCROLL_COUNT = 50
SCROLL_DELAY_SECONDS = 3
X_OUTPUT_FILE = "data/x_15_combine.csv"
TIKTOK_OUTPUT_FILE = "data/Tiktok_listrik_putus.csv"

# Pengaturan citra satelit.
SATELLITE_LATITUDE = -6.2238
SATELLITE_LONGITUDE = 106.8456
SATELLITE_ZOOM = 16
SATELLITE_DATE = "2024-03-10"
SATELLITE_OUTPUT_FOLDER = "data/satellite"
