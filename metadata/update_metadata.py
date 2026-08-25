#!/usr/bin/env python3
"""Update PET metadata requirement lists from the current BIDS schema."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


METADATA_DIR = Path(__file__).resolve().parent
PET_METADATA_FILE = METADATA_DIR / "PET_metadata.json"
BLOOD_METADATA_FILE = METADATA_DIR / "blood_metadata.json"
REPORT_FILE = METADATA_DIR / "metadata_updated.md"
JSR_PACKAGE_URL = "https://jsr.io/@bids/schema"
GITHUB_SCHEMA_URLS = [
    "https://raw.githubusercontent.com/bids-standard/bids-specification/master/schema.json",
    "https://raw.githubusercontent.com/bids-standard/bids-specification/main/schema.json",
    "https://raw.githubusercontent.com/bids-standard/bids-specification/master/src/schema/schema.json",
    "https://raw.githubusercontent.com/bids-standard/bids-specification/main/src/schema/schema.json",
]
READTHEDOCS_SCHEMA_URL = (
    "https://bids-specification.readthedocs.io/en/latest/schema.json"
)

LEVEL_TO_CATEGORY = {
    "required": "mandatory",
    "mandatory": "mandatory",
    "recommended": "recommended",
    "optional": "optional",
}
PET_CATEGORIES = ("mandatory", "recommended", "optional")
BLOOD_CATEGORIES = ("mandatory", "recommended", "optional")


def fetch_url(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "PET2BIDS metadata updater"})
    with urlopen(request, timeout=30) as response:
        return response.read()


def load_json_url(url: str) -> dict[str, Any]:
    return json.loads(fetch_url(url).decode("utf-8"))


def discover_jsr_latest_version() -> str:
    html = fetch_url(JSR_PACKAGE_URL).decode("utf-8", errors="replace")
    version_matches = re.findall(r'aria-label="Version: ([0-9]+\.[0-9]+\.[0-9]+)"', html)
    version_matches.extend(
        re.findall(r"@bids/schema(?:</a>)?</span><span[^>]*>@</span>([0-9][^<\"]+)", html)
    )
    version_matches.extend(re.findall(r"/@bids/schema/([0-9]+\.[0-9]+\.[0-9]+)/schema\.json", html))
    version_matches.extend(re.findall(r"@bids/schema@([0-9]+\.[0-9]+\.[0-9]+)", html))
    if not version_matches:
        raise RuntimeError("Could not find the latest @bids/schema version on JSR.")
    return sorted(set(version_matches), key=version_key)[-1]


def version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", version))


def load_latest_schema() -> tuple[dict[str, Any], str]:
    errors = []

    try:
        version = discover_jsr_latest_version()
        url = f"{JSR_PACKAGE_URL}/{version}/schema.json"
        return load_json_url(url), url
    except (HTTPError, URLError, OSError, RuntimeError, json.JSONDecodeError) as exc:
        errors.append(f"JSR failed: {exc}")

    for url in GITHUB_SCHEMA_URLS:
        try:
            return load_json_url(url), url
        except (HTTPError, URLError, OSError, json.JSONDecodeError) as exc:
            errors.append(f"{url} failed: {exc}")

    try:
        return load_json_url(READTHEDOCS_SCHEMA_URL), READTHEDOCS_SCHEMA_URL
    except (HTTPError, URLError, OSError, json.JSONDecodeError) as exc:
        errors.append(f"{READTHEDOCS_SCHEMA_URL} failed: {exc}")

    raise RuntimeError("Could not load a BIDS schema.\n" + "\n".join(errors))


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, payload: Any) -> None:
    with path.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2)
        stream.write("\n")


def schema_level(field_rule: Any) -> str | None:
    if isinstance(field_rule, str):
        return field_rule
    if isinstance(field_rule, dict):
        return field_rule.get("level")
    return None


def local_category(level: str | None) -> str | None:
    if level is None:
        return None
    return LEVEL_TO_CATEGORY.get(level)


def selectors_have(selectors: list[str], text: str) -> bool:
    return any(text in selector for selector in selectors)


def pet_field_categories(schema: dict[str, Any]) -> dict[str, str]:
    categories: dict[str, str] = {}
    sidecars = schema["rules"]["sidecars"]["pet"]
    for rule in sidecars.values():
        selectors = rule.get("selectors", [])
        is_pet_sidecar = selectors_have(selectors, 'suffix == "pet"') or selectors_have(
            selectors, "suffix == 'pet'"
        )
        is_pet_task = selectors_have(selectors, '"task" in entities') or selectors_have(
            selectors, "'task' in entities"
        )
        has_sidecar_condition = selectors_have(selectors, "sidecar.")
        if not (is_pet_sidecar or is_pet_task) or has_sidecar_condition:
            continue
        for name, field_rule in rule.get("fields", {}).items():
            category = local_category(schema_level(field_rule))
            if category:
                categories[name] = category
    return categories


def blood_sidecar_categories(schema: dict[str, Any]) -> dict[str, str]:
    categories: dict[str, str] = {}
    sidecars = schema["rules"]["sidecars"]["pet"]
    for rule in sidecars.values():
        selectors = rule.get("selectors", [])
        is_blood = selectors_have(selectors, 'suffix == "blood"') or selectors_have(
            selectors, "suffix == 'blood'"
        )
        if not is_blood:
            continue
        for name, field_rule in rule.get("fields", {}).items():
            category = local_category(schema_level(field_rule))
            if category:
                categories[name] = category
    return categories


def blood_grouped_categories(schema: dict[str, Any]) -> dict[str, list[Any]]:
    grouped: dict[str, list[Any]] = {category: [] for category in BLOOD_CATEGORIES}
    sidecars = schema["rules"]["sidecars"]["pet"]
    for rule in sidecars.values():
        selectors = rule.get("selectors", [])
        is_blood = selectors_have(selectors, 'suffix == "blood"') or selectors_have(
            selectors, "suffix == 'blood'"
        )
        if not is_blood:
            continue

        fields_by_category: dict[str, list[str]] = defaultdict(list)
        for name, field_rule in rule.get("fields", {}).items():
            category = local_category(schema_level(field_rule))
            if category:
                fields_by_category[category].append(name)

        conditional = any("sidecar." in selector for selector in selectors)
        for category, fields in fields_by_category.items():
            item: Any = fields if conditional and len(fields) > 1 else fields
            if isinstance(item, list) and item and isinstance(item[0], str):
                if conditional and len(item) > 1:
                    grouped[category].append(item)
                else:
                    grouped[category].extend(item)
    return grouped


def blood_recording_fields(schema: dict[str, Any]) -> list[str]:
    fields: list[str] = []
    for name in blood_sidecar_categories(schema):
        append_unique(fields, name)
    for rule in schema["rules"]["tabular_data"]["pet"].values():
        selectors = rule.get("selectors", [])
        is_blood = selectors_have(selectors, 'suffix == "blood"') or selectors_have(
            selectors, "suffix == 'blood'"
        )
        if not is_blood:
            continue
        for name in rule.get("columns", {}):
            append_unique(fields, name)
    return fields


def item_key(item: Any) -> str:
    return json.dumps(item, sort_keys=True)


def item_names(item: Any) -> set[str]:
    if isinstance(item, str):
        return {item}
    if isinstance(item, list):
        return {name for name in item if isinstance(name, str)}
    return set()


def append_unique(items: list[Any], item: Any) -> None:
    if item_key(item) not in {item_key(existing) for existing in items}:
        items.append(item)


def category_members(metadata: dict[str, Any]) -> dict[str, str]:
    members = {}
    for category in PET_CATEGORIES:
        for item in metadata.get(category, []):
            if isinstance(item, str):
                members[item] = category
    return members


def update_flat_categories(
    current: dict[str, Any], target: dict[str, str], categories: tuple[str, ...]
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated = {key: list(current.get(key, [])) for key in current}
    for category in categories:
        updated.setdefault(category, [])

    changes = {"added": defaultdict(list), "moved": [], "preserved": defaultdict(list)}
    existing_category = category_members(updated)

    for name, target_category in target.items():
        source_category = existing_category.get(name)
        if source_category == target_category:
            continue
        if source_category:
            updated[source_category] = [item for item in updated[source_category] if item != name]
            updated[target_category].append(name)
            changes["moved"].append((name, source_category, target_category))
        else:
            updated[target_category].append(name)
            changes["added"][target_category].append(name)

    target_names = set(target)
    for category in categories:
        for item in current.get(category, []):
            if isinstance(item, str) and item not in target_names:
                changes["preserved"][category].append(item)

    return updated, changes


def update_grouped_categories(
    current: dict[str, Any], grouped_target: dict[str, list[Any]]
) -> tuple[dict[str, Any], dict[str, Any]]:
    updated = {key: copy.deepcopy(value) for key, value in current.items()}
    for category in BLOOD_CATEGORIES:
        updated.setdefault(category, [])

    target_category_by_name = {}
    for category, items in grouped_target.items():
        for item in items:
            for name in item_names(item):
                target_category_by_name[name] = category

    changes = {"added": defaultdict(list), "moved": [], "preserved": defaultdict(list)}
    current_category_by_name = {}
    for category in BLOOD_CATEGORIES:
        for item in updated.get(category, []):
            for name in item_names(item):
                current_category_by_name[name] = category

    for category, items in grouped_target.items():
        for item in items:
            names = item_names(item)
            if not names:
                continue
            present_names = names & set(current_category_by_name)
            if present_names and all(current_category_by_name[name] == category for name in present_names):
                continue

            for old_category in BLOOD_CATEGORIES:
                updated[old_category] = [
                    existing
                    for existing in updated[old_category]
                    if not (item_names(existing) & names)
                ]

            updated[category].append(item)
            if present_names:
                for name in sorted(present_names):
                    old_category = current_category_by_name[name]
                    if old_category != category:
                        changes["moved"].append((name, old_category, category))
            else:
                changes["added"][category].append(item)

    target_names = set(target_category_by_name)
    for category in BLOOD_CATEGORIES:
        for item in current.get(category, []):
            if item_names(item).isdisjoint(target_names):
                changes["preserved"][category].append(item)

    return updated, changes


def update_blood_recording_fields(
    pet_metadata: dict[str, Any], target_fields: list[str]
) -> dict[str, list[str]]:
    current_fields = pet_metadata.setdefault("blood_recording_fields", [])
    changes = {"added": [], "preserved": []}
    for field in target_fields:
        if field not in current_fields:
            current_fields.append(field)
            changes["added"].append(field)
    for field in current_fields:
        if field not in target_fields:
            changes["preserved"].append(field)
    return changes


def format_item(item: Any) -> str:
    if isinstance(item, list):
        return "[" + ", ".join(str(value) for value in item) + "]"
    return str(item)


def report_lines(
    schema: dict[str, Any],
    source: str,
    pet_changes: dict[str, Any],
    blood_changes: dict[str, Any],
    recording_changes: dict[str, list[str]],
) -> list[str]:
    lines = [
        "# Metadata update report",
        "",
        f"- Date: {date.today().isoformat()}",
        f"- BIDS version: {schema.get('bids_version', 'unknown')}",
        f"- Schema version: {schema.get('schema_version', 'unknown')}",
        f"- Schema source: {source}",
        "",
    ]
    lines.extend(format_changes("PET_metadata.json", pet_changes))
    lines.extend(format_changes("blood_metadata.json", blood_changes))
    lines.extend(["## PET_metadata.json blood_recording_fields", ""])
    if recording_changes["added"]:
        lines.append("- Added: " + ", ".join(recording_changes["added"]))
    else:
        lines.append("- Added: none")
    if recording_changes["preserved"]:
        lines.append("- Preserved local fields: " + ", ".join(recording_changes["preserved"]))
    lines.append("")
    return lines


def format_changes(title: str, changes: dict[str, Any]) -> list[str]:
    lines = [f"## {title}", ""]
    any_change = False
    for category in PET_CATEGORIES:
        added = changes["added"].get(category, [])
        if added:
            any_change = True
            lines.append(f"- Added to {category}: " + ", ".join(format_item(item) for item in added))
    if changes["moved"]:
        any_change = True
        for name, old_category, new_category in changes["moved"]:
            lines.append(f"- Moved {name}: {old_category} -> {new_category}")
    for category in PET_CATEGORIES:
        preserved = changes["preserved"].get(category, [])
        if preserved:
            lines.append(
                f"- Preserved local-only {category}: "
                + ", ".join(format_item(item) for item in preserved)
            )
    if not any_change:
        lines.append("- No category changes.")
    lines.append("")
    return lines


def update_metadata(dry_run: bool = False) -> int:
    schema, source = load_latest_schema()
    pet_metadata = read_json(PET_METADATA_FILE)
    blood_metadata = read_json(BLOOD_METADATA_FILE)

    updated_pet, pet_changes = update_flat_categories(
        pet_metadata, pet_field_categories(schema), PET_CATEGORIES
    )
    recording_changes = update_blood_recording_fields(
        updated_pet, blood_recording_fields(schema)
    )
    updated_blood, blood_changes = update_grouped_categories(
        blood_metadata, blood_grouped_categories(schema)
    )

    report = "\n".join(
        report_lines(schema, source, pet_changes, blood_changes, recording_changes)
    )

    if dry_run:
        print(report)
        return 0

    write_json(PET_METADATA_FILE, updated_pet)
    write_json(BLOOD_METADATA_FILE, updated_blood)
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(f"Updated {PET_METADATA_FILE}")
    print(f"Updated {BLOOD_METADATA_FILE}")
    print(f"Wrote {REPORT_FILE}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Update local PET metadata JSON files from the latest BIDS schema."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the report without writing JSON files or metadata_updated.md",
    )
    args = parser.parse_args()
    return update_metadata(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
