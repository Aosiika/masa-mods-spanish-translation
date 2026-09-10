#!/usr/bin/env python3
"""
scripts/validate_translations.py
Implements the validation engine and linter rules defined in SPEC-SYNC-001.

Validates:
  - Strict key parity (missing keys, obsolete/orphaned keys)
  - Variable and placeholder preservation (%s, %d, {0}, etc.)
  - Minecraft formatting and color codes (§a, §c, §r, etc.)
  - UTF-8 encoding integrity (no BOM) and valid JSON structure
  - Translation progress tracking (translated vs. identical to source)
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path
from typing import Any, Counter, Dict, List, Set, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

MOD_LIST = [
    "malilib",
    "litematica",
    "tweakeroo",
    "minihud",
    "itemscroller",
]

# Regex patterns for invariants
# Minecraft formatting codes: § followed by [0-9a-fk-or]
MC_FORMAT_PATTERN = re.compile(r"§[0-9a-fk-or]", re.IGNORECASE)

# Standard Java/C printf-style format specifiers: %s, %d, %f, %1$s, %-10s, %.2f, %%
PRINTF_PATTERN = re.compile(r"%(?:[0-9]+\$)?[+-]?\d*(?:\.\d+)?[a-zA-Z%]")

# Positional or named brace tokens: {0}, {1}, {name}
BRACE_PATTERN = re.compile(r"\{[0-9a-zA-Z_]+\}")


def extract_mc_formats(text: str) -> Counter[str]:
    """Returns a counter of all Minecraft formatting codes found in the string (lowercased)."""
    return collections.Counter(c.lower() for c in MC_FORMAT_PATTERN.findall(text))


def extract_placeholders(text: str) -> Counter[str]:
    """Returns a counter of all printf and brace placeholders found in the string."""
    printf_matches = PRINTF_PATTERN.findall(text)
    brace_matches = BRACE_PATTERN.findall(text)
    return collections.Counter(printf_matches + brace_matches)


def check_bom_and_syntax(file_path: Path) -> Tuple[bool, Optional[Dict[str, str]], List[str]]:
    """Checks for BOM and validates JSON syntax. Returns (is_valid, parsed_dict, errors)."""
    errors: List[str] = []

    try:
        raw_bytes = file_path.read_bytes()
    except Exception as exc:
        return False, None, [f"Failed to read file: {exc}"]

    # Check for UTF-8 BOM (\xef\xbb\xbf)
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        errors.append("File contains a UTF-8 BOM (Byte Order Mark), violating INV-001.")

    try:
        content = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        errors.append(f"File is not valid UTF-8: {exc}")
        return False, None, errors

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        errors.append(f"JSON syntax error: {exc}")
        return False, None, errors

    if not isinstance(data, dict):
        errors.append("Root JSON element must be an object (dictionary).")
        return False, None, errors

    for k, v in data.items():
        if not isinstance(k, str) or not isinstance(v, str):
            errors.append(f"Invalid key-value pair. Both must be strings. Offending key: {k!r}")
            return False, None, errors

    return len(errors) == 0, data, errors


class ModValidationReport:
    def __init__(self, mod_id: str):
        self.mod_id: str = mod_id
        self.en_path: Optional[Path] = None
        self.es_path: Optional[Path] = None
        self.total_en_keys: int = 0
        self.total_es_keys: int = 0
        self.missing_keys: List[str] = []
        self.orphaned_keys: List[str] = []
        self.identical_keys: List[str] = []
        self.translated_keys: List[str] = []
        self.mc_format_errors: List[Tuple[str, str, str]] = []  # (key, en_val, es_val)
        self.placeholder_errors: List[Tuple[str, str, str]] = []  # (key, en_val, es_val)
        self.structural_errors: List[str] = []

    @property
    def has_fatal_errors(self) -> bool:
        return bool(
            self.structural_errors
            or self.missing_keys
            or self.orphaned_keys
            or self.mc_format_errors
            or self.placeholder_errors
        )


def validate_mod(base_dir: Path, mod_id: str) -> ModValidationReport:
    report = ModValidationReport(mod_id)
    lang_dir = (
        base_dir
        / "mods"
        / mod_id
        / "src"
        / "main"
        / "resources"
        / "assets"
        / mod_id
        / "lang"
    )

    report.en_path = lang_dir / "en_us.json"
    report.es_path = lang_dir / "es_es.json"

    if not report.en_path.exists():
        report.structural_errors.append(f"Missing en_us.json at: {report.en_path}")
        return report

    if not report.es_path.exists():
        report.structural_errors.append(f"Missing es_es.json at: {report.es_path}")
        return report

    # Validate en_us.json syntax & BOM
    en_valid, en_dict, en_errs = check_bom_and_syntax(report.en_path)
    if not en_valid or en_dict is None:
        report.structural_errors.extend([f"[en_us.json] {e}" for e in en_errs])
        return report

    # Validate es_es.json syntax & BOM
    es_valid, es_dict, es_errs = check_bom_and_syntax(report.es_path)
    if not es_valid or es_dict is None:
        report.structural_errors.extend([f"[es_es.json] {e}" for e in es_errs])
        return report

    report.total_en_keys = len(en_dict)
    report.total_es_keys = len(es_dict)

    en_keys = set(en_dict.keys())
    es_keys = set(es_dict.keys())

    # Key parity
    report.missing_keys = sorted(list(en_keys - es_keys))
    report.orphaned_keys = sorted(list(es_keys - en_keys))

    # Key-level content inspections
    for key in sorted(list(en_keys & es_keys)):
        en_val = en_dict[key]
        es_val = es_dict[key]

        # Translation status
        if en_val.strip() == es_val.strip():
            report.identical_keys.append(key)
        else:
            report.translated_keys.append(key)

        # Minecraft format code verification
        en_mc = extract_mc_formats(en_val)
        es_mc = extract_mc_formats(es_val)
        if en_mc != es_mc:
            report.mc_format_errors.append((key, en_val, es_val))

        # Placeholder verification
        en_ph = extract_placeholders(en_val)
        es_ph = extract_placeholders(es_val)
        if en_ph != es_ph:
            report.placeholder_errors.append((key, en_val, es_val))

    return report


def print_report(report: ModValidationReport, verbose: bool = False) -> None:
    print(f"Mod: {report.mod_id}")
    print(f"  en_us keys: {report.total_en_keys}")
    print(f"  es_es keys: {report.total_es_keys}")

    if report.structural_errors:
        print("  STRUCTURAL ERRORS:")
        for err in report.structural_errors:
            print(f"    - {err}")
        return

    # Parity stats
    pct_translated = (
        (len(report.translated_keys) / report.total_en_keys * 100)
        if report.total_en_keys > 0
        else 0.0
    )
    print(f"  Translated keys: {len(report.translated_keys)} ({pct_translated:.1f}%)")
    print(f"  Identical/Untranslated keys: {len(report.identical_keys)}")

    if report.missing_keys:
        print(f"  MISSING KEYS ({len(report.missing_keys)}):")
        for k in report.missing_keys[: 10 if not verbose else len(report.missing_keys)]:
            print(f"    - {k}")
        if not verbose and len(report.missing_keys) > 10:
            print(f"    ... and {len(report.missing_keys) - 10} more (use --verbose to see all)")

    if report.orphaned_keys:
        print(f"  ORPHANED/OBSOLETE KEYS ({len(report.orphaned_keys)}):")
        for k in report.orphaned_keys[: 10 if not verbose else len(report.orphaned_keys)]:
            print(f"    - {k}")
        if not verbose and len(report.orphaned_keys) > 10:
            print(f"    ... and {len(report.orphaned_keys) - 10} more (use --verbose to see all)")

    if report.mc_format_errors:
        print(f"  MINECRAFT FORMAT CODE ERRORS ({len(report.mc_format_errors)}):")
        for key, en_val, es_val in report.mc_format_errors[: 5 if not verbose else len(report.mc_format_errors)]:
            print(f"    - Key: {key}")
            print(f"      EN: {en_val!r}")
            print(f"      ES: {es_val!r}")
        if not verbose and len(report.mc_format_errors) > 5:
            print(f"    ... and {len(report.mc_format_errors) - 5} more")

    if report.placeholder_errors:
        print(f"  PLACEHOLDER/VARIABLE ERRORS ({len(report.placeholder_errors)}):")
        for key, en_val, es_val in report.placeholder_errors[: 5 if not verbose else len(report.placeholder_errors)]:
            print(f"    - Key: {key}")
            print(f"      EN: {en_val!r}")
            print(f"      ES: {es_val!r}")
        if not verbose and len(report.placeholder_errors) > 5:
            print(f"    ... and {len(report.placeholder_errors) - 5} more")

    if not report.has_fatal_errors:
        print("  Status: PASSED technical invariants (INV-001 through INV-008).")
    else:
        print("  Status: FAILED one or more technical invariants.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Spanish translation files against English source files per SPEC-SYNC-001."
    )
    parser.add_argument(
        "--mods",
        type=str,
        default="",
        help=f"Comma-separated list of mods to validate (defaults to: {', '.join(MOD_LIST)})",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print all individual mismatched keys, placeholders, and formatting discrepancies",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail validation if any key remains untranslated (identical to en_us)",
    )

    args = parser.parse_args()

    target_mods = [m.strip() for m in args.mods.split(",") if m.strip()] if args.mods else MOD_LIST
    workspace_root = Path(__file__).resolve().parent.parent

    print("=" * 70)
    print("Masa / Sakura Ryoko Translations Validator")
    print(f"Workspace: {workspace_root}")
    print(f"Target mods: {', '.join(target_mods)}")
    print("=" * 70)

    overall_failure = False
    reports: List[ModValidationReport] = []

    for mod in target_mods:
        report = validate_mod(workspace_root, mod)
        reports.append(report)
        print_report(report, verbose=args.verbose)
        print("-" * 70)

        if report.has_fatal_errors:
            overall_failure = True
        elif args.strict and report.identical_keys:
            print(f"[{mod}] Strict mode failure: {len(report.identical_keys)} keys remain untranslated.")
            overall_failure = True

    # Summary table
    print("VALIDATION SUMMARY")
    print(f"{'Mod':<15} {'Total EN':<10} {'Total ES':<10} {'Translated':<12} {'Pending':<10} {'Errors':<8}")
    print("-" * 70)
    for r in reports:
        err_count = (
            len(r.structural_errors)
            + len(r.missing_keys)
            + len(r.orphaned_keys)
            + len(r.mc_format_errors)
            + len(r.placeholder_errors)
        )
        print(
            f"{r.mod_id:<15} {r.total_en_keys:<10} {r.total_es_keys:<10} "
            f"{len(r.translated_keys):<12} {len(r.identical_keys):<10} {err_count:<8}"
        )
    print("=" * 70)

    if overall_failure:
        print("Result: FAILED validation checks.")
        return 1

    print("Result: ALL checks passed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
