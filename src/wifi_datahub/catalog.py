from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse


REQUIRED_FIELDS = {
    "id", "name", "year", "summary", "tasks", "modalities", "hardware",
    "settings", "scale", "original", "standardization", "sources", "verified_at",
}


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_tasks(root: Path | None = None) -> Dict[str, Dict[str, Any]]:
    root = root or repository_root()
    payload = json.loads((root / "catalog" / "tasks.json").read_text(encoding="utf-8"))
    return {item["id"]: item for item in payload["tasks"]}


def load_datasets(root: Path | None = None) -> List[Dict[str, Any]]:
    root = root or repository_root()
    entries = []
    for path in sorted((root / "catalog" / "datasets").glob("*.json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        item["_catalog_file"] = str(path.relative_to(root))
        entries.append(item)
    return entries


def _is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def validate_catalog(root: Path | None = None) -> Tuple[List[Dict[str, Any]], List[str]]:
    root = root or repository_root()
    tasks = load_tasks(root)
    entries = load_datasets(root)
    errors: List[str] = []
    seen = set()

    for entry in entries:
        file_name = entry.pop("_catalog_file")
        missing = REQUIRED_FIELDS - set(entry)
        if missing:
            errors.append(f"{file_name}: missing fields {sorted(missing)}")
        dataset_id = entry.get("id")
        if dataset_id in seen:
            errors.append(f"{file_name}: duplicate id {dataset_id}")
        seen.add(dataset_id)
        unknown_tasks = sorted(set(entry.get("tasks", [])) - set(tasks))
        if unknown_tasks:
            errors.append(f"{file_name}: unknown tasks {unknown_tasks}")
        if not entry.get("sources"):
            errors.append(f"{file_name}: at least one source is required")
        for source in entry.get("sources", []):
            if not _is_url(source.get("url", "")):
                errors.append(f"{file_name}: invalid source URL {source.get('url')!r}")
        landing = entry.get("original", {}).get("landing_page", "")
        if not _is_url(landing):
            errors.append(f"{file_name}: invalid landing page {landing!r}")

    catalog_ids = {entry.get("id") for entry in entries}
    for registry_name in ("adapters.json", "splits.json"):
        try:
            registry = json.loads((root / "catalog" / registry_name).read_text(encoding="utf-8"))["datasets"]
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
            errors.append(f"catalog/{registry_name}: invalid registry: {exc}")
            continue
        missing = sorted(catalog_ids - set(registry))
        extra = sorted(set(registry) - catalog_ids)
        if missing:
            errors.append(f"catalog/{registry_name}: missing datasets {missing}")
        if extra:
            errors.append(f"catalog/{registry_name}: unknown datasets {extra}")
        if registry_name == "adapters.json":
            for dataset_id, config in registry.items():
                if config.get("handler") not in {"generic", "official-profile", "aril", "ut-har", "wallhack18k", "wiar-intel5300", "xrf-v2"}:
                    errors.append(f"catalog/{registry_name}: {dataset_id} has unknown handler")
                if not config.get("patterns"):
                    errors.append(f"catalog/{registry_name}: {dataset_id} has no source patterns")
                if config.get("implementation") not in {"reference-implemented", "schema-implemented", "format-profile"}:
                    errors.append(f"catalog/{registry_name}: {dataset_id} has invalid implementation tier")
                if not _is_url(config.get("official_reference", "")):
                    errors.append(f"catalog/{registry_name}: {dataset_id} has no valid official reference")
        else:
            kinds = {"random", "predefined", "group_holdout", "trial_order", "external_json", "source_groups"}
            for dataset_id, config in registry.items():
                settings = config.get("settings", [])
                setting_ids = [item.get("id") for item in settings]
                if not settings or config.get("default") not in setting_ids:
                    errors.append(f"catalog/{registry_name}: {dataset_id} has an invalid default")
                if len(setting_ids) != len(set(setting_ids)):
                    errors.append(f"catalog/{registry_name}: {dataset_id} has duplicate setting IDs")
                for setting in settings:
                    if setting.get("kind") not in kinds:
                        errors.append(f"catalog/{registry_name}: {dataset_id}/{setting.get('id')} has unknown kind")
                    if setting.get("provenance") not in {"official", "paper", "hub"}:
                        errors.append(f"catalog/{registry_name}: {dataset_id}/{setting.get('id')} has invalid provenance")
                    if setting.get("kind") in {"group_holdout", "trial_order", "source_groups"} and not setting.get("group_by"):
                        errors.append(f"catalog/{registry_name}: {dataset_id}/{setting.get('id')} needs group_by")

    try:
        examples = json.loads((root / "catalog" / "examples.json").read_text(encoding="utf-8"))["datasets"]
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
        errors.append(f"catalog/examples.json: invalid registry: {exc}")
    else:
        missing = sorted(catalog_ids - set(examples))
        extra = sorted(set(examples) - catalog_ids)
        if missing:
            errors.append(f"catalog/examples.json: missing datasets {missing}")
        if extra:
            errors.append(f"catalog/examples.json: unknown datasets {extra}")
        for dataset_id, example in examples.items():
            for field in ("source_path", "primary_array", "expected_shape", "note"):
                if not isinstance(example.get(field), str) or not example[field].strip():
                    errors.append(f"catalog/examples.json: {dataset_id} has invalid {field}")

    try:
        import jsonschema  # type: ignore
    except ImportError:
        jsonschema = None
    if jsonschema is not None:
        schema = json.loads((root / "schemas" / "dataset.schema.json").read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
        for entry in entries:
            for issue in validator.iter_errors(entry):
                where = ".".join(str(part) for part in issue.path)
                errors.append(f"{entry.get('id')}.{where}: {issue.message}")
    return entries, errors
