#!/usr/bin/env python3
"""Validate Schoolradar source files and the generated DUO dataset."""

from __future__ import annotations

import json
import math
import py_compile
import re
import shutil
import subprocess
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "schools.json"
MIRROR_FILES = [
    ".gitignore",
    "index.html",
    "app.js",
    "styles.css",
    "README.md",
    "HOME_AI_HANDOFF.md",
    "tools/update_duo_data.py",
    "tools/validate_project.py",
    ".github/workflows/pages.yml",
]
EXPECTED_IDS = {
    "filters",
    "searchInput",
    "radiusSelect",
    "typeSelect",
    "voLevelField",
    "voLevelSelect",
    "sortSelect",
    "includeHavoVwo",
    "schoolList",
    "resultSummary",
    "statsGrid",
    "medianMetric",
    "realMap",
    "mapCanvas",
    "distributionMap",
    "scatterCanvas",
    "detailPanel",
}


class SiteHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.assets: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(str(values["id"]))
        asset = values.get("src") if tag == "script" else values.get("href") if tag == "link" else None
        if asset and asset.startswith("./"):
            self.assets.append(asset.split("?", 1)[0])


def add_error(errors: list[str], condition: bool, message: str) -> None:
    if not condition:
        errors.append(message)


def is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def validate_range(errors: list[str], context: str, value: dict, min_key: str, max_key: str) -> None:
    minimum = value.get(min_key)
    maximum = value.get(max_key)
    if minimum is None and maximum is None:
        return
    add_error(errors, is_number(minimum) and is_number(maximum), f"{context}: {min_key}/{max_key} must both be finite numbers or null")
    if is_number(minimum) and is_number(maximum):
        add_error(errors, minimum >= 0, f"{context}: {min_key} is negative")
        add_error(errors, maximum >= minimum, f"{context}: {max_key} is below {min_key}")


def validate_ratio(errors: list[str], context: str, value: object) -> None:
    if value is None:
        return
    add_error(errors, is_number(value) and 0 <= value <= 1, f"{context}: ratio must be between 0 and 1 or null")


def validate_metric_block(errors: list[str], context: str, block: dict) -> None:
    pairs = [
        ("totalMin", "totalMax"),
        ("vwoMin", "vwoMax"),
        ("havoVwoMin", "havoVwoMax"),
        ("vwoEligibleMin", "vwoEligibleMax"),
    ]
    for min_key, max_key in pairs:
        validate_range(errors, context, block, min_key, max_key)

    total_max = block.get("totalMax")
    for key in ("vwoMax", "havoVwoMax", "vwoEligibleMax"):
        if is_number(total_max) and is_number(block.get(key)):
            add_error(errors, block[key] <= total_max, f"{context}: {key} exceeds totalMax")

    if all(is_number(block.get(key)) for key in ("vwoMin", "havoVwoMin", "vwoEligibleMin")):
        add_error(
            errors,
            block["vwoEligibleMin"] == block["vwoMin"] + block["havoVwoMin"],
            f"{context}: vwoEligibleMin does not equal VWO + HAVO/VWO",
        )
    if all(is_number(block.get(key)) for key in ("vwoMax", "havoVwoMax", "vwoEligibleMax")):
        add_error(
            errors,
            block["vwoEligibleMax"] == block["vwoMax"] + block["havoVwoMax"],
            f"{context}: vwoEligibleMax does not equal VWO + HAVO/VWO",
        )


def validate_history(errors: list[str], context: str, history: object) -> None:
    add_error(errors, isinstance(history, list), f"{context}: history must be a list")
    if not isinstance(history, list):
        return
    years = [item.get("year") for item in history if isinstance(item, dict)]
    add_error(errors, len(years) == len(history), f"{context}: every history row must be an object with a year")
    add_error(errors, years == sorted(years), f"{context}: years are not sorted")
    add_error(errors, len(years) == len(set(years)), f"{context}: duplicate years")
    for index, item in enumerate(history):
        if not isinstance(item, dict):
            continue
        row_context = f"{context}[{index}]"
        validate_metric_block(errors, row_context, item)
        for key in ("vwoRatioMin", "vwoRatioMax", "vwoEligibleRatioMin", "vwoEligibleRatioMax"):
            validate_ratio(errors, f"{row_context}.{key}", item.get(key))
        if is_number(item.get("vwoRatioMin")) and is_number(item.get("vwoRatioMax")):
            add_error(errors, item["vwoRatioMin"] <= item["vwoRatioMax"], f"{row_context}: VWO ratio bounds are reversed")
        if is_number(item.get("vwoEligibleRatioMin")) and is_number(item.get("vwoEligibleRatioMax")):
            add_error(errors, item["vwoEligibleRatioMin"] <= item["vwoEligibleRatioMax"], f"{row_context}: eligible ratio bounds are reversed")


def validate_school(errors: list[str], school: object, index: int) -> None:
    context = f"schools[{index}]"
    if not isinstance(school, dict):
        errors.append(f"{context}: school must be an object")
        return

    school_id = school.get("id")
    add_error(errors, isinstance(school_id, str) and bool(school_id), f"{context}: missing id")
    add_error(errors, isinstance(school.get("name"), str) and bool(school.get("name")), f"{context}: missing name")
    add_error(errors, school.get("sector") in {"PO", "VO"}, f"{context}: invalid sector")
    if school.get("sector") == "VO":
        add_error(errors, school.get("type") == "Vo", f"{context}: VO school must have type Vo")
    if school.get("sector") == "PO":
        add_error(errors, school.get("type") in {"", "Bo", "Sbo"}, f"{context}: invalid PO type")

    if all(isinstance(school.get(key), str) for key in ("brin", "branch")):
        add_error(errors, school_id == f"{school['brin']}-{school['branch']}", f"{context}: id does not match BRIN and branch")

    postcode = school.get("postcode")
    add_error(errors, not postcode or bool(re.fullmatch(r"[1-9]\d{3}[A-Z]{2}", str(postcode))), f"{context}: invalid postcode {postcode!r}")

    latitude = school.get("latitude")
    longitude = school.get("longitude")
    add_error(errors, (latitude is None) == (longitude is None), f"{context}: incomplete coordinate pair")
    if latitude is not None and longitude is not None:
        add_error(errors, is_number(latitude) and 50 <= latitude <= 54, f"{context}: latitude outside the Netherlands")
        add_error(errors, is_number(longitude) and 3 <= longitude <= 8, f"{context}: longitude outside the Netherlands")

    website = school.get("website")
    if website:
        parsed = urlsplit(str(website))
        add_error(errors, parsed.scheme in {"http", "https"} and bool(parsed.netloc), f"{context}: unsafe website URL")

    pupils = school.get("pupils") or {}
    validate_range(errors, f"{context}.pupils", pupils, "min", "max")
    validate_metric_block(errors, f"{context}.advice", school.get("advice") or {})
    validate_metric_block(errors, f"{context}.enrollment", school.get("enrollment") or {})

    history = school.get("history") or {}
    validate_history(errors, f"{context}.history.advice", history.get("advice", []))
    validate_history(errors, f"{context}.history.enrollment", history.get("enrollment", []))

    origin = school.get("origin") or {}
    for min_key, max_key in (("totalMin", "totalMax"), ("localMin", "localMax")):
        validate_range(errors, f"{context}.origin", origin, min_key, max_key)
    for key in ("localRatioMin", "localRatioMax"):
        validate_ratio(errors, f"{context}.origin.{key}", origin.get(key))
    for top_index, item in enumerate(origin.get("top") or []):
        validate_range(errors, f"{context}.origin.top[{top_index}]", item, "min", "max")
        validate_ratio(errors, f"{context}.origin.top[{top_index}].ratioMin", item.get("ratioMin"))
        validate_ratio(errors, f"{context}.origin.top[{top_index}].ratioMax", item.get("ratioMax"))

    background = school.get("background") or {}
    for min_key, max_key in (("totalMin", "totalMax"), ("nncaMin", "nncaMax"), ("referenceMin", "referenceMax")):
        validate_range(errors, f"{context}.background", background, min_key, max_key)
    for key in ("nncaRatioMin", "nncaRatioMax"):
        validate_ratio(errors, f"{context}.background.{key}", background.get(key))

    satisfaction = school.get("satisfaction") or {}
    score = satisfaction.get("score")
    add_error(errors, score is None or (is_number(score) and 0 <= score <= 10), f"{context}: satisfaction score must be 0-10 or null")


def validate_sources(errors: list[str]) -> None:
    index_file = ROOT / "index.html"
    parser = SiteHTMLParser()
    parser.feed(index_file.read_text(encoding="utf-8"))
    duplicate_ids = sorted({item for item in parser.ids if parser.ids.count(item) > 1})
    add_error(errors, not duplicate_ids, f"index.html: duplicate ids {duplicate_ids}")
    add_error(errors, EXPECTED_IDS.issubset(set(parser.ids)), f"index.html: missing required ids {sorted(EXPECTED_IDS - set(parser.ids))}")
    for asset in parser.assets:
        add_error(errors, (ROOT / asset[2:]).is_file(), f"index.html: missing local asset {asset}")

    css = (ROOT / "styles.css").read_text(encoding="utf-8")
    add_error(errors, css.count("{") == css.count("}"), "styles.css: unbalanced braces")

    node = shutil.which("node")
    add_error(errors, node is not None, "Node.js is required to validate app.js")
    if node:
        result = subprocess.run([node, "--check", str(ROOT / "app.js")], capture_output=True, text=True, check=False)
        add_error(errors, result.returncode == 0, f"app.js: {result.stderr.strip() or 'syntax check failed'}")

    for python_file in (ROOT / "tools" / "update_duo_data.py", Path(__file__)):
        try:
            py_compile.compile(str(python_file), doraise=True)
        except py_compile.PyCompileError as error:
            errors.append(f"{python_file.name}: {error.msg}")

    workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
    add_error(errors, "\t" not in workflow, "pages.yml: YAML must not contain tab indentation")
    for token in (
        "workflow_dispatch:",
        "actions/checkout@v4",
        "python tools/update_duo_data.py --refresh",
        "python tools/validate_project.py",
        "actions/upload-pages-artifact@v3",
        "actions/deploy-pages@v4",
    ):
        add_error(errors, token in workflow, f"pages.yml: missing {token}")


def validate_dataset(errors: list[str]) -> dict[str, int]:
    add_error(errors, DATA_FILE.is_file(), f"missing generated dataset: {DATA_FILE}")
    if not DATA_FILE.is_file():
        return {}
    try:
        payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"schools.json: {error}")
        return {}

    add_error(errors, isinstance(payload, dict), "schools.json: root must be an object")
    if not isinstance(payload, dict):
        return {}
    schools = payload.get("schools")
    add_error(errors, isinstance(schools, list) and bool(schools), "schools.json: schools must be a non-empty list")
    if not isinstance(schools, list):
        return {}

    generated_at = payload.get("generatedAt")
    try:
        datetime.fromisoformat(str(generated_at).replace("Z", "+00:00"))
    except ValueError:
        errors.append("schools.json: generatedAt is not a valid ISO timestamp")

    ids = [school.get("id") for school in schools if isinstance(school, dict)]
    add_error(errors, len(ids) == len(set(ids)), "schools.json: duplicate school ids")
    for index, school in enumerate(schools):
        validate_school(errors, school, index)

    calculated = {
        "schoolCount": len(schools),
        "primarySchoolCount": sum(1 for school in schools if school.get("sector") == "PO"),
        "secondarySchoolCount": sum(1 for school in schools if school.get("sector") == "VO"),
        "adviceRatioCount": sum(1 for school in schools if (school.get("advice", {}).get("totalMax") or 0) > 0),
        "enrollmentRatioCount": sum(1 for school in schools if (school.get("enrollment", {}).get("totalMax") or 0) > 0),
        "adviceHistoryCount": sum(1 for school in schools if school.get("history", {}).get("advice")),
        "enrollmentHistoryCount": sum(1 for school in schools if school.get("history", {}).get("enrollment")),
        "originRatioCount": sum(1 for school in schools if (school.get("origin", {}).get("totalMax") or 0) > 0),
        "backgroundRatioCount": sum(1 for school in schools if (school.get("background", {}).get("totalMax") or 0) > 0),
        "withCoordinates": sum(1 for school in schools if school.get("latitude") is not None and school.get("longitude") is not None),
    }
    published = payload.get("stats") or {}
    for key, value in calculated.items():
        add_error(errors, published.get(key) == value, f"schools.json: stats.{key} is {published.get(key)!r}, expected {value}")

    sources = payload.get("sources")
    add_error(errors, isinstance(sources, list) and bool(sources), "schools.json: sources must be a non-empty list")
    for index, source in enumerate(sources or []):
        for key in ("url", "page"):
            parsed = urlsplit(str(source.get(key) or ""))
            add_error(errors, parsed.scheme == "https" and bool(parsed.netloc), f"schools.json: sources[{index}].{key} must be HTTPS")

    return calculated


def validate_mirror(errors: list[str]) -> None:
    mirror = ROOT / "github-upload"
    if not mirror.is_dir():
        return
    for relative in MIRROR_FILES:
        source = ROOT / relative
        target = mirror / relative
        add_error(errors, target.is_file(), f"github-upload: missing {relative}")
        if source.is_file() and target.is_file():
            add_error(errors, source.read_bytes() == target.read_bytes(), f"github-upload: stale {relative}")


def main() -> int:
    errors: list[str] = []
    validate_sources(errors)
    stats = validate_dataset(errors)
    validate_mirror(errors)
    if errors:
        print(f"Validation failed with {len(errors)} issue(s):", file=sys.stderr)
        for error in errors[:100]:
            print(f"- {error}", file=sys.stderr)
        if len(errors) > 100:
            print(f"- ... and {len(errors) - 100} more", file=sys.stderr)
        return 1
    print(
        "Validation passed: "
        f"{stats.get('schoolCount', 0)} schools, "
        f"{stats.get('withCoordinates', 0)} coordinates, "
        "source syntax, site structure, workflow, data invariants, and mirror integrity."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
