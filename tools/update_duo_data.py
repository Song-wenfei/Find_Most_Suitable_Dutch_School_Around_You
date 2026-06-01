#!/usr/bin/env python3
"""Build the Schoolradar dataset from DUO Open Onderwijsdata CSV files."""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_FILE = ROOT / "data" / "schools.json"

SOURCE_FILES = {
    "advice": {
        "url": "https://duo.nl/open_onderwijsdata/images/04-leerlingen-bo-sbo-schooladviezen-2024-2025.csv",
        "path": RAW_DIR / "schooladviezen-2024-2025.csv",
        "label": "DUO schooladviezen 2024-2025",
        "page": "https://duo.nl/open_onderwijsdata/primair-onderwijs/aantal-leerlingen/schooladviezen.jsp",
    },
    "pupils": {
        "url": "https://duo.nl/open_onderwijsdata/images/01.-leerlingen-po-soort-po-cluster-leeftijd-2025-2026.csv",
        "path": RAW_DIR / "leerlingen-2025-2026.csv",
        "label": "DUO leerlingen PO 2025-2026",
        "page": "https://duo.nl/open_onderwijsdata/primair-onderwijs/aantal-leerlingen/leerlingen-onderwijssoort-cluster-leeftijd.jsp",
    },
    "addresses": {
        "url": "https://duo.nl/open_onderwijsdata/images/02.-alle-schoolvestigingen-basisonderwijs.csv",
        "path": RAW_DIR / "schoolvestigingen-basisonderwijs.csv",
        "label": "DUO schoolvestigingen basisonderwijs",
        "page": "https://duo.nl/open_onderwijsdata/primair-onderwijs/scholen-en-adressen/schoolvestigingen-basisonderwijs.jsp",
    },
    "locations": {
        "url": "https://onderwijsdata.duo.nl/dataset/c416acd1-e083-4ec6-9203-3b20f98fe143/resource/a7e3f323-6e46-4dca-a834-369d9d520aa8/download/onderwijslocaties.csv",
        "path": RAW_DIR / "onderwijslocaties.csv",
        "label": "DUO RIO onderwijslocaties",
        "page": "https://onderwijsdata.duo.nl/datasets/rio_nfo_po_vo_vavo_mbo_ho/resources/a7e3f323-6e46-4dca-a834-369d9d520aa8",
    },
    "originPostcode4": {
        "url": "https://onderwijsdata.duo.nl/dataset/4ea91ae5-51ef-48a4-aa67-7098343f75bc/resource/402c5a69-eea8-41b4-b8ad-ecac301c28a8/download/brin6_pc4.csv",
        "path": RAW_DIR / "brin6_pc4_2025.csv",
        "label": "DUO leerlingen PO per vestiging naar postcode4",
        "page": "https://onderwijsdata.duo.nl/datasets/popostcode4-v1",
        "api_resource": "402c5a69-eea8-41b4-b8ad-ecac301c28a8",
    },
    "adviceHistory": {
        "url": "https://onderwijsdata.duo.nl/dataset/d6903313-8c64-4b12-b4ac-07e5655ef9f4/resource/454c5dd4-6815-4b52-ae2f-b9eebc6afa6d/download/brin6_advies.csv",
        "path": RAW_DIR / "brin6_advies_recent.csv",
        "label": "DUO leerlingen BO/SBO per vestiging naar advies",
        "page": "https://onderwijsdata.duo.nl/datasets/wpoadvies-v1",
        "api_resource": "454c5dd4-6815-4b52-ae2f-b9eebc6afa6d",
        "api_recent_years": 5,
        "fields": ["INSTELLINGSCODE", "VESTIGINGSCODE", "TYPE_PO", "PEILJAAR", "ADVIES", "AANTAL_LEERLINGEN"],
    },
    "backgroundBo": {
        "url": "https://onderwijsdata.duo.nl/dataset/e3ab98c0-881a-413a-ba8a-676dd1313593/resource/2899e6a2-cfee-41a6-9250-43276db16e69/download/brin6_noat.csv",
        "path": RAW_DIR / "brin6_noat_recent.csv",
        "label": "DUO leerlingen BO per vestiging naar NOAT",
        "page": "https://onderwijsdata.duo.nl/datasets/poachtergrond",
        "api_resource": "2899e6a2-cfee-41a6-9250-43276db16e69",
        "api_recent_years": 5,
        "fields": ["INSTELLINGSCODE", "VESTIGINGSCODE", "TYPE_PO", "PEILJAAR", "NOAT", "AANTAL_LEERLINGEN"],
    },
    "backgroundSbo": {
        "url": "https://onderwijsdata.duo.nl/dataset/e3ab98c0-881a-413a-ba8a-676dd1313593/resource/fb5290c9-b19e-46fb-9496-9582162a106a/download/brin6_cumi.csv",
        "path": RAW_DIR / "brin6_cumi_recent.csv",
        "label": "DUO leerlingen SBO/SO/VSO per vestiging naar CUMI",
        "page": "https://onderwijsdata.duo.nl/datasets/poachtergrond",
        "api_resource": "fb5290c9-b19e-46fb-9496-9582162a106a",
        "api_recent_years": 5,
        "fields": ["INSTELLINGSCODE", "VESTIGINGSCODE", "TYPE_PO", "PEILJAAR", "CUMI", "AANTAL_LEERLINGEN"],
    },
}

ADVICE_COLUMNS = [
    "VSO",
    "PRO",
    "VMBO_B",
    "VMBO_B_K",
    "VMBO_K",
    "VMBO_K_GT",
    "VMBO_GT",
    "VMBO_GT_HAVO",
    "HAVO",
    "HAVO_VWO",
    "VWO",
]

AGE_PREFIX = "LEEFTIJD_"
VWO_CODE = "11"
HAVO_VWO_CODE = "10"
ADVICE_HISTORY_CODES = {str(value) for value in range(1, 12)}
BACKGROUND_REFERENCE_CODES = {"0", "1"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Download the latest source CSVs before building.")
    parser.add_argument("--output", type=Path, default=OUT_FILE, help="Output JSON path.")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    if args.refresh:
        for source in SOURCE_FILES.values():
            if source.get("api_recent_years"):
                download_recent_year_records(
                    source["api_resource"],
                    source["path"],
                    source["fields"],
                    int(source["api_recent_years"]),
                )
            elif source.get("api_resource"):
                download_latest_origin_postcode4(source["api_resource"], source["path"])
            else:
                download(source["url"], source["path"])

    missing = [str(source["path"]) for source in SOURCE_FILES.values() if not source["path"].exists()]
    if missing:
        print("Missing source files:", file=sys.stderr)
        for item in missing:
            print(f"  {item}", file=sys.stderr)
        print("Run with --refresh, or download the CSVs listed in README.md.", file=sys.stderr)
        return 2

    addresses = index_addresses(read_csv(SOURCE_FILES["addresses"]["path"]))
    locations = index_locations(read_csv(SOURCE_FILES["locations"]["path"]))
    schools = build_base_schools(addresses, locations)
    merge_pupils(schools, read_csv(SOURCE_FILES["pupils"]["path"]))
    merge_advice(schools, read_csv(SOURCE_FILES["advice"]["path"]))
    merge_origins(schools, read_csv(SOURCE_FILES["originPostcode4"]["path"]))
    merge_advice_history(schools, read_csv(SOURCE_FILES["adviceHistory"]["path"]))
    merge_background(schools, read_csv(SOURCE_FILES["backgroundBo"]["path"]), "NOAT", "NOAT")
    merge_background(schools, read_csv(SOURCE_FILES["backgroundSbo"]["path"]), "CUMI", "CUMI")

    rows = [school for school in schools.values() if school.get("name")]
    rows.sort(key=lambda item: (item.get("city") or "", item.get("name") or "", item.get("id") or ""))

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sources": [
            {
                "label": source["label"],
                "url": source["url"],
                "page": source["page"],
            }
            for source in SOURCE_FILES.values()
        ],
        "stats": {
            "schoolCount": len(rows),
            "adviceRatioCount": sum(1 for row in rows if (row.get("advice", {}).get("totalMax") or 0) > 0),
            "adviceHistoryCount": sum(1 for row in rows if row.get("history", {}).get("advice")),
            "originRatioCount": sum(1 for row in rows if (row.get("origin", {}).get("totalMax") or 0) > 0),
            "backgroundRatioCount": sum(1 for row in rows if (row.get("background", {}).get("totalMax") or 0) > 0),
            "withCoordinates": sum(1 for row in rows if row.get("latitude") is not None and row.get("longitude") is not None),
        },
        "schools": rows,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(
        f"Wrote {args.output} with {payload['stats']['schoolCount']} schools "
        f"({payload['stats']['withCoordinates']} with coordinates)."
    )
    return 0


def download(url: str, path: Path) -> None:
    print(f"Downloading {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "Schoolradar-VWO/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        path.write_bytes(response.read())


def download_latest_origin_postcode4(resource_id: str, path: Path) -> None:
    first = api_get(
        "https://onderwijsdata.duo.nl/api/3/action/datastore_search",
        {"resource_id": resource_id, "sort": "PEILJAAR desc", "limit": 1},
    )
    records = first.get("result", {}).get("records", [])
    if not records:
        raise RuntimeError("No origin postcode records returned by DUO API.")

    latest_year = int(records[0]["PEILJAAR"])
    filters = json.dumps({"PEILJAAR": latest_year}, separators=(",", ":"))
    fieldnames = ["INSTELLINGSCODE", "VESTIGINGSCODE", "TYPE_PO", "PEILJAAR", "POSTCODE4_DEELNEMER", "AANTAL_LEERLINGEN"]
    limit = 10000
    offset = 0
    total = None
    written = 0
    print(f"Downloading DUO postcode origin records for {latest_year}")

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        while total is None or offset < total:
            payload = api_get(
                "https://onderwijsdata.duo.nl/api/3/action/datastore_search",
                {
                    "resource_id": resource_id,
                    "filters": filters,
                    "limit": limit,
                    "offset": offset,
                },
            )
            result = payload["result"]
            total = int(result["total"])
            rows = result["records"]
            for row in rows:
                writer.writerow({field: row.get(field, "") for field in fieldnames})
            written += len(rows)
            offset += limit
    print(f"Wrote {written} postcode origin records to {path}")


def download_recent_year_records(resource_id: str, path: Path, fieldnames: list[str], year_count: int) -> None:
    first = api_get(
        "https://onderwijsdata.duo.nl/api/3/action/datastore_search",
        {"resource_id": resource_id, "sort": "PEILJAAR desc", "limit": 1},
    )
    records = first.get("result", {}).get("records", [])
    if not records:
        raise RuntimeError(f"No records returned by DUO API for {resource_id}.")

    latest_year = int(records[0]["PEILJAAR"])
    years = list(range(latest_year - year_count + 1, latest_year + 1))
    limit = 10000
    written = 0
    print(f"Downloading DUO records for {years[0]}-{years[-1]} from {resource_id}")

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for year in years:
            filters = json.dumps({"PEILJAAR": year}, separators=(",", ":"))
            offset = 0
            total = None
            while total is None or offset < total:
                payload = api_get(
                    "https://onderwijsdata.duo.nl/api/3/action/datastore_search",
                    {
                        "resource_id": resource_id,
                        "filters": filters,
                        "limit": limit,
                        "offset": offset,
                    },
                )
                result = payload["result"]
                total = int(result["total"])
                rows = result["records"]
                for row in rows:
                    writer.writerow({field: row.get(field, "") for field in fieldnames})
                written += len(rows)
                offset += limit
    print(f"Wrote {written} recent records to {path}")


def api_get(base_url: str, params: dict[str, object]) -> dict:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(f"{base_url}?{query}", headers={"User-Agent": "Schoolradar-VWO/1.0"})
    last_error: Exception | None = None
    for _ in range(3):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception as error:  # pragma: no cover - network resilience
            last_error = error
    raise RuntimeError(f"DUO API request failed: {last_error}") from last_error


def read_csv(path: Path) -> list[dict[str, str]]:
    encoding = detect_encoding(path)
    sample = path.read_text(encoding=encoding, errors="replace")[:4096]
    delimiter = ";" if sample.count(";") >= sample.count(",") else ","
    with path.open("r", encoding=encoding, newline="") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        return [{clean_header(k): (v or "").strip() for k, v in row.items()} for row in reader]


def detect_encoding(path: Path) -> str:
    data = path.read_bytes()[:8192]
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            data.decode(encoding)
        except UnicodeDecodeError:
            continue
        return encoding
    return "utf-8-sig"


def clean_header(value: str | None) -> str:
    return (value or "").strip().strip('"')


def index_addresses(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        inst = row.get("INSTELLINGSCODE", "")
        branch = branch_code(inst, row.get("VESTIGINGSCODE", ""))
        key = make_key(inst, branch)
        if key:
            indexed[key] = row
    return indexed


def index_locations(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    indexed: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        postcode = normalize_postcode(row.get("POSTCODE"))
        if not postcode:
            continue
        indexed.setdefault(postcode, []).append(row)
    return indexed


def build_base_schools(
    addresses: dict[str, dict[str, str]],
    locations: dict[str, list[dict[str, str]]],
) -> dict[str, dict]:
    schools: dict[str, dict] = {}
    for key, address in addresses.items():
        inst, branch = key.split("-", 1)
        location = best_location(address, locations)
        school = {
            "id": key,
            "brin": inst,
            "branch": branch,
            "name": tidy_name(address.get("VESTIGINGSNAAM")),
            "city": address.get("PLAATSNAAM", "").strip(),
            "municipality": title_or_empty(address.get("GEMEENTENAAM")),
            "province": title_or_empty(address.get("PROVINCIE")),
            "postcode": normalize_postcode(address.get("POSTCODE")),
            "type": "",
            "denomination": title_or_empty(address.get("DENOMINATIE")),
            "address": format_address(address.get("STRAATNAAM"), address.get("HUISNUMMER-TOEVOEGING")),
            "phone": blank_to_none(address.get("TELEFOONNUMMER")),
            "website": normalize_url(address.get("INTERNETADRES")),
            "latitude": as_float(location.get("GPS_LATITUDE")) if location else None,
            "longitude": as_float(location.get("GPS_LONGITUDE")) if location else None,
            "pupils": {"min": None, "max": None, "redacted": False},
            "advice": empty_advice(),
            "origin": empty_origin(),
            "background": empty_background(),
            "history": {"advice": []},
            "satisfaction": empty_satisfaction(),
        }
        schools[key] = school
    return schools


def merge_pupils(schools: dict[str, dict], rows: list[dict[str, str]]) -> None:
    for row in rows:
        if row.get("SOORT_PO") not in {"Bo", "Sbo"}:
            continue
        key = make_key(row.get("INSTELLINGSCODE", ""), row.get("VESTIGINGSCODE", ""))
        if not key:
            continue
        school = schools.setdefault(key, fallback_school(row, key))
        school["type"] = row.get("SOORT_PO", school.get("type", ""))
        if not school.get("name"):
            school["name"] = tidy_name(row.get("INSTELLINGSNAAM_VESTIGING"))
        for target, source in [
            ("city", "PLAATSNAAM"),
            ("municipality", "GEMEENTENAAM"),
            ("province", "PROVINCIE"),
            ("postcode", "POSTCODE_VESTIGING"),
        ]:
            if not school.get(target) and row.get(source):
                school[target] = row.get(source, "").strip()

        age_columns = [column for column in row if column.startswith(AGE_PREFIX)]
        pupil_range = sum_range(row, age_columns)
        school["pupils"] = {
            "min": pupil_range["min"],
            "max": pupil_range["max"],
            "redacted": pupil_range["redacted"],
        }


def merge_advice(schools: dict[str, dict], rows: list[dict[str, str]]) -> None:
    for row in rows:
        if row.get("SOORT_PO") not in {"Bo", "Sbo"}:
            continue
        key = make_key(row.get("INSTELLINGSCODE", ""), row.get("VESTIGINGSCODE", ""))
        if not key:
            continue
        school = schools.setdefault(key, fallback_school(row, key))
        school["type"] = row.get("SOORT_PO", school.get("type", ""))
        if not school.get("name"):
            school["name"] = tidy_name(row.get("INSTELLINGSNAAM_VESTIGING"))
        for target, source in [
            ("city", "PLAATSNAAM"),
            ("municipality", "GEMEENTENAAM"),
            ("province", "PROVINCIE"),
            ("postcode", "POSTCODE_VESTIGING"),
        ]:
            if not school.get(target) and row.get(source):
                school[target] = row.get(source, "").strip()

        total = sum_range(row, ADVICE_COLUMNS)
        vwo = sum_range(row, ["VWO"])
        havo_vwo = sum_range(row, ["HAVO_VWO"])
        eligible = add_ranges(vwo, havo_vwo)
        school["advice"] = {
            "totalMin": total["min"],
            "totalMax": total["max"],
            "vwoMin": vwo["min"],
            "vwoMax": vwo["max"],
            "havoVwoMin": havo_vwo["min"],
            "havoVwoMax": havo_vwo["max"],
            "vwoEligibleMin": eligible["min"],
            "vwoEligibleMax": eligible["max"],
            "redacted": total["redacted"] or vwo["redacted"] or havo_vwo["redacted"],
        }


def merge_origins(schools: dict[str, dict], rows: list[dict[str, str]]) -> None:
    years = [
        int(float(row.get("PEILJAAR", "0")))
        for row in rows
        if row.get("TYPE_PO", "").upper() in {"BO", "SBO"} and str(row.get("PEILJAAR", "")).strip()
    ]
    if not years:
        return
    latest_year = max(years)
    grouped: dict[str, dict[str, dict[str, int | bool]]] = {}

    for row in rows:
        if row.get("TYPE_PO", "").upper() not in {"BO", "SBO"}:
            continue
        try:
            year = int(float(row.get("PEILJAAR", "0")))
        except ValueError:
            continue
        if year != latest_year:
            continue
        key = make_key(row.get("INSTELLINGSCODE", ""), row.get("VESTIGINGSCODE", ""))
        postcode4 = normalize_postcode4(row.get("POSTCODE4_DEELNEMER"))
        if not key or not postcode4:
            continue
        parsed = parse_count(row.get("AANTAL_LEERLINGEN"))
        by_postcode = grouped.setdefault(key, {})
        current = by_postcode.setdefault(postcode4, {"min": 0, "max": 0, "redacted": False})
        current["min"] = int(current["min"]) + int(parsed["min"])
        current["max"] = int(current["max"]) + int(parsed["max"])
        current["redacted"] = bool(current["redacted"] or parsed["redacted"])

    for key, by_postcode in grouped.items():
        school = schools.get(key)
        if not school:
            continue
        total = add_many_ranges(by_postcode.values())
        local_postcode4 = normalize_postcode(school.get("postcode"))[:4]
        local = by_postcode.get(local_postcode4, {"min": 0, "max": 0, "redacted": False})
        top = sorted(
            by_postcode.items(),
            key=lambda item: (int(item[1]["min"]) + int(item[1]["max"])) / 2,
            reverse=True,
        )[:5]
        school["origin"] = {
            "year": latest_year,
            "postcode4": local_postcode4 or None,
            "totalMin": total["min"],
            "totalMax": total["max"],
            "localMin": local["min"],
            "localMax": local["max"],
            "localRatioMin": ratio_min(local, total),
            "localRatioMax": ratio_max(local, total),
            "redacted": total["redacted"],
            "top": [
                {
                    "postcode4": postcode4,
                    "min": values["min"],
                    "max": values["max"],
                    "ratioMin": ratio_min(values, total),
                    "ratioMax": ratio_max(values, total),
                    "redacted": values["redacted"],
                }
                for postcode4, values in top
            ],
        }


def merge_advice_history(schools: dict[str, dict], rows: list[dict[str, str]]) -> None:
    grouped: dict[str, dict[int, dict[str, dict[str, int | bool]]]] = {}
    for row in rows:
        if row.get("TYPE_PO", "").upper() not in {"BO", "SBO"}:
            continue
        key = make_key(row.get("INSTELLINGSCODE", ""), row.get("VESTIGINGSCODE", ""))
        if not key:
            continue
        school = schools.get(key)
        if school and not type_matches_school(school, row.get("TYPE_PO")):
            continue
        try:
            year = int(float(row.get("PEILJAAR", "0")))
        except ValueError:
            continue
        code = normalize_code(row.get("ADVIES"))
        if code not in ADVICE_HISTORY_CODES:
            continue
        parsed = parse_count(row.get("AANTAL_LEERLINGEN"))
        bucket = grouped.setdefault(key, {}).setdefault(
            year,
            {
                "total": {"min": 0, "max": 0, "redacted": False},
                "vwo": {"min": 0, "max": 0, "redacted": False},
                "havoVwo": {"min": 0, "max": 0, "redacted": False},
            },
        )
        bucket["total"] = add_ranges(bucket["total"], parsed)
        if code == VWO_CODE:
            bucket["vwo"] = add_ranges(bucket["vwo"], parsed)
        if code == HAVO_VWO_CODE:
            bucket["havoVwo"] = add_ranges(bucket["havoVwo"], parsed)

    for key, by_year in grouped.items():
        school = schools.get(key)
        if not school:
            continue
        history = []
        for year, values in sorted(by_year.items()):
            eligible = add_ranges(values["vwo"], values["havoVwo"])
            total = values["total"]
            history.append(
                {
                    "year": year,
                    "schoolYear": f"{year}-{year + 1}",
                    "totalMin": total["min"],
                    "totalMax": total["max"],
                    "vwoMin": values["vwo"]["min"],
                    "vwoMax": values["vwo"]["max"],
                    "havoVwoMin": values["havoVwo"]["min"],
                    "havoVwoMax": values["havoVwo"]["max"],
                    "vwoEligibleMin": eligible["min"],
                    "vwoEligibleMax": eligible["max"],
                    "vwoRatioMin": ratio_min(values["vwo"], total),
                    "vwoRatioMax": ratio_max(values["vwo"], total),
                    "vwoEligibleRatioMin": ratio_min(eligible, total),
                    "vwoEligibleRatioMax": ratio_max(eligible, total),
                    "redacted": bool(total["redacted"] or eligible["redacted"] or values["vwo"]["redacted"]),
                }
            )
        school["history"] = {"advice": history}


def merge_background(schools: dict[str, dict], rows: list[dict[str, str]], code_column: str, measure: str) -> None:
    grouped: dict[str, dict[int, dict[str, dict[str, int | bool]]]] = {}
    for row in rows:
        if row.get("TYPE_PO", "").upper() not in {"BO", "SBO"}:
            continue
        key = make_key(row.get("INSTELLINGSCODE", ""), row.get("VESTIGINGSCODE", ""))
        if not key:
            continue
        school = schools.get(key)
        if school and not type_matches_school(school, row.get("TYPE_PO")):
            continue
        try:
            year = int(float(row.get("PEILJAAR", "0")))
        except ValueError:
            continue
        code = normalize_code(row.get(code_column))
        parsed = parse_count(row.get("AANTAL_LEERLINGEN"))
        bucket = grouped.setdefault(key, {}).setdefault(
            year,
            {
                "total": {"min": 0, "max": 0, "redacted": False},
                "reference": {"min": 0, "max": 0, "redacted": False},
                "nnca": {"min": 0, "max": 0, "redacted": False},
            },
        )
        bucket["total"] = add_ranges(bucket["total"], parsed)
        if code in BACKGROUND_REFERENCE_CODES:
            bucket["reference"] = add_ranges(bucket["reference"], parsed)
        else:
            bucket["nnca"] = add_ranges(bucket["nnca"], parsed)

    for key, by_year in grouped.items():
        school = schools.get(key)
        if not school:
            continue
        history = []
        for year, values in sorted(by_year.items()):
            total = values["total"]
            nnca = values["nnca"]
            reference = values["reference"]
            history.append(
                {
                    "year": year,
                    "measure": measure,
                    "totalMin": total["min"],
                    "totalMax": total["max"],
                    "nncaMin": nnca["min"],
                    "nncaMax": nnca["max"],
                    "referenceMin": reference["min"],
                    "referenceMax": reference["max"],
                    "nncaRatioMin": ratio_min(nnca, total),
                    "nncaRatioMax": ratio_max(nnca, total),
                    "redacted": bool(total["redacted"] or nnca["redacted"] or reference["redacted"]),
                }
            )
        latest = history[-1] if history else empty_background()
        school["background"] = {
            "year": latest.get("year"),
            "measure": measure,
            "totalMin": latest.get("totalMin"),
            "totalMax": latest.get("totalMax"),
            "nncaMin": latest.get("nncaMin"),
            "nncaMax": latest.get("nncaMax"),
            "referenceMin": latest.get("referenceMin"),
            "referenceMax": latest.get("referenceMax"),
            "nncaRatioMin": latest.get("nncaRatioMin"),
            "nncaRatioMax": latest.get("nncaRatioMax"),
            "redacted": latest.get("redacted", False),
            "history": history,
        }


def fallback_school(row: dict[str, str], key: str) -> dict:
    inst, branch = key.split("-", 1)
    return {
        "id": key,
        "brin": inst,
        "branch": branch,
        "name": tidy_name(row.get("INSTELLINGSNAAM_VESTIGING")),
        "city": row.get("PLAATSNAAM", "").strip(),
        "municipality": title_or_empty(row.get("GEMEENTENAAM")),
        "province": title_or_empty(row.get("PROVINCIE")),
        "postcode": normalize_postcode(row.get("POSTCODE_VESTIGING")),
        "type": row.get("SOORT_PO", ""),
        "denomination": title_or_empty(row.get("DENOMINATIE_VESTIGING")),
        "address": "",
        "phone": None,
        "website": None,
        "latitude": None,
        "longitude": None,
        "pupils": {"min": None, "max": None, "redacted": False},
        "advice": empty_advice(),
        "origin": empty_origin(),
        "background": empty_background(),
        "history": {"advice": []},
        "satisfaction": empty_satisfaction(),
    }


def empty_advice() -> dict:
    return {
        "totalMin": None,
        "totalMax": None,
        "vwoMin": None,
        "vwoMax": None,
        "havoVwoMin": None,
        "havoVwoMax": None,
        "vwoEligibleMin": None,
        "vwoEligibleMax": None,
        "redacted": False,
    }


def empty_origin() -> dict:
    return {
        "year": None,
        "postcode4": None,
        "totalMin": None,
        "totalMax": None,
        "localMin": None,
        "localMax": None,
        "localRatioMin": None,
        "localRatioMax": None,
        "redacted": False,
        "top": [],
    }


def empty_background() -> dict:
    return {
        "year": None,
        "measure": None,
        "totalMin": None,
        "totalMax": None,
        "nncaMin": None,
        "nncaMax": None,
        "referenceMin": None,
        "referenceMax": None,
        "nncaRatioMin": None,
        "nncaRatioMax": None,
        "redacted": False,
        "history": [],
    }


def empty_satisfaction() -> dict:
    return {
        "score": None,
        "year": None,
        "source": None,
    }


def sum_range(row: dict[str, str], columns: list[str]) -> dict[str, int | bool]:
    total_min = 0
    total_max = 0
    redacted = False
    for column in columns:
        parsed = parse_count(row.get(column))
        total_min += parsed["min"]
        total_max += parsed["max"]
        redacted = redacted or parsed["redacted"]
    return {"min": total_min, "max": total_max, "redacted": redacted}


def add_ranges(left: dict[str, int | bool], right: dict[str, int | bool]) -> dict[str, int | bool]:
    return {
        "min": int(left["min"]) + int(right["min"]),
        "max": int(left["max"]) + int(right["max"]),
        "redacted": bool(left["redacted"] or right["redacted"]),
    }


def add_many_ranges(values: object) -> dict[str, int | bool]:
    total = {"min": 0, "max": 0, "redacted": False}
    for value in values:
        total = add_ranges(total, value)
    return total


def ratio_min(numerator: dict[str, int | bool], denominator: dict[str, int | bool]) -> float | None:
    numerator_min = int(numerator["min"])
    numerator_max = int(numerator["max"])
    denominator_max = int(denominator["max"])
    other_max = max(0, denominator_max - numerator_max)
    total = numerator_min + other_max
    if total <= 0:
        return None
    return max(0.0, min(1.0, numerator_min / total))


def ratio_max(numerator: dict[str, int | bool], denominator: dict[str, int | bool]) -> float | None:
    numerator_min = int(numerator["min"])
    numerator_max = int(numerator["max"])
    denominator_min = int(denominator["min"])
    other_min = max(0, denominator_min - numerator_min)
    total = numerator_max + other_min
    if total <= 0:
        return None
    return max(0.0, min(1.0, numerator_max / total))


def parse_count(value: str | None) -> dict[str, int | bool]:
    text = (value or "").strip()
    if not text or text == "0":
        return {"min": 0, "max": 0, "redacted": False}
    if text in {"<5", "-1"}:
        return {"min": 1, "max": 4, "redacted": True}
    text = text.replace(".", "").replace(",", ".")
    try:
        number = int(float(text))
    except ValueError:
        return {"min": 0, "max": 0, "redacted": False}
    return {"min": number, "max": number, "redacted": False}


def best_location(address: dict[str, str], locations: dict[str, list[dict[str, str]]]) -> dict[str, str] | None:
    postcode = normalize_postcode(address.get("POSTCODE"))
    candidates = locations.get(postcode) or []
    if not candidates:
        return None
    street = normalize_text(address.get("STRAATNAAM"))
    house = first_house_number(address.get("HUISNUMMER-TOEVOEGING"))

    def score(candidate: dict[str, str]) -> int:
        value = 1
        if street and normalize_text(candidate.get("STRAATNAAM")) == street:
            value += 3
        if house and str(candidate.get("HUISNUMMER", "")).strip() == house:
            value += 2
        if as_float(candidate.get("GPS_LATITUDE")) is None or as_float(candidate.get("GPS_LONGITUDE")) is None:
            value -= 10
        return value

    return max(candidates, key=score)


def make_key(inst: str, branch: str) -> str:
    inst = (inst or "").strip().upper()
    branch = branch_code(inst, branch)
    if not inst or not branch:
        return ""
    return f"{inst}-{branch}"


def branch_code(inst: str, branch: str) -> str:
    inst = (inst or "").strip().upper()
    branch = (branch or "").strip().upper()
    if inst and branch.startswith(inst):
        branch = branch[len(inst) :]
    return branch or "00"


def format_address(street: str | None, house: str | None) -> str:
    return " ".join(part for part in [(street or "").strip(), (house or "").strip()] if part)


def normalize_postcode(value: str | None) -> str:
    return re.sub(r"\s+", "", value or "").upper()


def normalize_postcode4(value: str | None) -> str:
    text = re.sub(r"\D+", "", str(value or ""))
    if not text:
        return ""
    return text.zfill(4)[:4]


def normalize_code(value: str | None) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    try:
        return str(int(float(text)))
    except ValueError:
        return text


def type_matches_school(school: dict, row_type: str | None) -> bool:
    school_type = str(school.get("type") or "").casefold()
    source_type = str(row_type or "").casefold()
    if not school_type or not source_type:
        return True
    return school_type == source_type


def normalize_text(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").casefold()).strip()


def first_house_number(value: str | None) -> str:
    match = re.search(r"\d+", value or "")
    return match.group(0) if match else ""


def tidy_name(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def title_or_empty(value: str | None) -> str:
    text = (value or "").strip()
    return text[:1].upper() + text[1:].lower() if text.isupper() else text


def blank_to_none(value: str | None) -> str | None:
    text = (value or "").strip()
    return text or None


def normalize_url(value: str | None) -> str | None:
    text = (value or "").strip()
    if not text:
        return None
    if text.startswith(("http://", "https://")):
        return text
    return f"https://{text}"


def as_float(value: str | None) -> float | None:
    try:
        number = float(str(value or "").replace(",", "."))
    except ValueError:
        return None
    return number if math.isfinite(number) else None


if __name__ == "__main__":
    raise SystemExit(main())
