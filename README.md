# Plastic Pollution Tracking

Scraper untuk mengumpulkan hasil pencarian dari X dan TikTok, serta mengambil tangkapan citra satelit melalui browser.

## Menjalankan

1. Pasang [uv](https://docs.astral.sh/uv/) dan jalankan `uv sync`.
2. Salin `.env.example` menjadi `.env`, lalu isi kredensial platform yang akan digunakan.
3. Atur keyword, tanggal, jumlah scroll, file keluaran, dan scraper aktif di `config.py`.
4. Jalankan `uv run main.py`.

Hasil disimpan ke lokasi yang diatur di `config.py` (default di dalam `data/`).

## Pengaturan

- `ENABLE_X`, `ENABLE_TIKTOK`, dan `ENABLE_SATELLITE` memilih scraper yang dijalankan.
- `SEARCH_QUERY`, `START_DATE`, dan `END_DATE` mengatur pencarian X dan TikTok.
- `SCROLL_COUNT` mengatur jumlah scroll; `SCROLL_DELAY_SECONDS` mengatur jeda antar-scroll untuk X dan TikTok. `X_OUTPUT_FILE` dan `TIKTOK_OUTPUT_FILE` mengatur file hasil.
- `SATELLITE_LATITUDE`, `SATELLITE_LONGITUDE`, `SATELLITE_ZOOM`, `SATELLITE_DATE`, dan `SATELLITE_OUTPUT_FOLDER` mengatur citra satelit.
- `.env` menyimpan `AUTH_TOKEN` dan `CT0` untuk X, serta `MS_TOKEN` dan `SESSION_ID` untuk TikTok. Kredensial hanya perlu diisi untuk scraper yang aktif.

Browser Playwright dibuka saat scraper berjalan.

Scraper melewati postingan yang ID atau link-nya sudah ada di file output. Duplikat lama pada file output akan dirapikan sebelum scraping; jika datanya berbeda, baris terakhir dipertahankan.
