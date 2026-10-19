import csv
import os
import tempfile
from pathlib import Path


def load_unique_csv_keys(
    output_file: str,
    fieldnames: list[str],
) -> tuple[set[str], set[str]]:
    """Load known IDs/links and repair duplicate or headerless output rows."""
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not path.exists() or path.stat().st_size == 0:
        with path.open("w", newline="", encoding="utf-8") as file:
            csv.DictWriter(file, fieldnames=fieldnames).writeheader()
        return set(), set()

    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        first_row = next(reader, None)
        if first_row is None:
            rows = []
            needs_rewrite = True
        elif set(first_row) == set(fieldnames):
            needs_rewrite = first_row != fieldnames
            rows = list(csv.DictReader(file, fieldnames=first_row, restkey="_extra_values"))
        elif len(first_row) == len(fieldnames) and not {"id", "link"}.intersection(first_row):
            # Migrate existing scraper output that contains rows but no header.
            needs_rewrite = True
            rows = [dict(zip(fieldnames, first_row))]
            rows.extend(csv.DictReader(file, fieldnames=fieldnames, restkey="_extra_values"))
        else:
            raise ValueError(
                f"File '{output_file}' tidak cocok dengan format scraper ini. "
                "Gunakan nama file output lain di config.py atau periksa header CSV."
            )

    unique_rows: dict[str, dict[str, str]] = {}
    aliases_by_identity: dict[str, set[str]] = {}
    identity_by_alias: dict[str, str] = {}
    rows_without_key: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    seen_links: set[str] = set()
    duplicate_found = False

    for row in rows:
        item_id = (row.get("id") or "").strip()
        link = (row.get("link") or "").strip()
        if item_id:
            seen_ids.add(item_id)
        if link:
            seen_links.add(link)

        aliases = set()
        if item_id:
            aliases.add(f"id:{item_id}")
        if link:
            aliases.add(f"link:{link}")

        if not aliases:
            rows_without_key.append(row)
            continue

        duplicate_identities = {identity_by_alias[alias] for alias in aliases if alias in identity_by_alias}
        if duplicate_identities:
            duplicate_found = True
            # Keep the last copy, which is normally the latest observed metrics.
            for identity in duplicate_identities:
                unique_rows.pop(identity, None)
                for old_alias in aliases_by_identity.pop(identity, set()):
                    if identity_by_alias.get(old_alias) == identity:
                        identity_by_alias.pop(old_alias)

        identity = f"id:{item_id}" if item_id else f"link:{link}"
        unique_rows[identity] = row
        aliases_by_identity[identity] = aliases
        for alias in aliases:
            identity_by_alias[alias] = identity

    if needs_rewrite or duplicate_found:
        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                newline="",
                encoding="utf-8",
                dir=path.parent,
                delete=False,
            ) as temporary_file:
                temporary_path = temporary_file.name
                writer = csv.writer(temporary_file)
                writer.writerow(fieldnames)
                for row in [*rows_without_key, *unique_rows.values()]:
                    values = [row.get(field, "") for field in fieldnames]
                    values.extend(row.get("_extra_values") or [])
                    writer.writerow(values)
            os.replace(temporary_path, path)
        finally:
            if temporary_path and os.path.exists(temporary_path):
                os.remove(temporary_path)

    return seen_ids, seen_links
