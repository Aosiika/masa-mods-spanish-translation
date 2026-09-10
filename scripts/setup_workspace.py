#!/usr/bin/env python3
"""
scripts/setup_workspace.py
Implements SPEC-SYNC-001 (Upstream Synchronization Contract).

Builds the required directory structure:
  mods/<modid>/src/main/resources/assets/<modid>/lang/
Fetches upstream translation assets from Sakura Ryoko's repositories,
and initializes base translation templates when upstream translations do not yet exist.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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

UPSTREAM_ORG = "sakura-ryoko"
RAW_BASE_URL = "https://raw.githubusercontent.com"
API_BASE_URL = "https://api.github.com/repos"
USER_AGENT = "MasaModsTranslationSync/1.0 (+https://github.com/sakura-ryoko)"


def resolve_default_branch(mod_id: str, manual_branch: Optional[str] = None) -> str:
    """Resolves the default upstream development branch for a given mod repository."""
    if manual_branch:
        return manual_branch

    # Strategy 1: Fast git ls-remote (no API rate limiting)
    repo_url = f"https://github.com/{UPSTREAM_ORG}/{mod_id}"
    try:
        proc = subprocess.run(
            ["git", "ls-remote", "--symref", repo_url, "HEAD"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if proc.returncode == 0:
            for line in proc.stdout.splitlines():
                if line.startswith("ref: refs/heads/"):
                    parts = line.split()
                    if len(parts) >= 2:
                        branch = parts[1].replace("refs/heads/", "").strip()
                        if branch:
                            return branch
    except Exception:
        pass

    # Strategy 2: GitHub API repository lookup
    api_url = f"{API_BASE_URL}/{UPSTREAM_ORG}/{mod_id}"
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if "default_branch" in data and data["default_branch"]:
                return data["default_branch"]
    except Exception:
        pass

    # Strategy 3: Fallback heuristic for Sakura Ryoko active branch
    return "DEV/26.3"


def build_raw_url(mod_id: str, branch: str, filename: str) -> str:
    """Builds the raw GitHub URL for a lang resource."""
    return f"{RAW_BASE_URL}/{UPSTREAM_ORG}/{mod_id}/{branch}/src/main/resources/assets/{mod_id}/lang/{filename}"


def fetch_file_content(url: str) -> Tuple[Optional[bytes], int]:
    """Fetches remote URL content cleanly. Returns (content, status_code)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read(), resp.status
    except urllib.error.HTTPError as err:
        return None, err.code
    except Exception:
        return None, 500


def format_json_content(raw_bytes: bytes) -> str:
    """Parses and formats JSON with 2-space indentation and trailing newline."""
    data = json.loads(raw_bytes.decode("utf-8-sig"))
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def atomic_write(target_path: Path, content: str) -> None:
    """Writes string content to a target file atomically, ensuring UTF-8 without BOM."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = target_path.parent
    fd, temp_file_path = tempfile.mkstemp(prefix="sync_", suffix=".tmp", dir=temp_dir)
    try:
        with open(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        os.replace(temp_file_path, target_path)
    except Exception:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise


def setup_mod_workspace(
    base_dir: Path,
    mod_id: str,
    manual_branch: Optional[str] = None,
    force: bool = False,
) -> bool:
    """Sets up folder hierarchy and downloads en_us.json and es_es.json for a mod."""
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
    lang_dir.mkdir(parents=True, exist_ok=True)

    en_us_path = lang_dir / "en_us.json"
    es_es_path = lang_dir / "es_es.json"

    print(f"[{mod_id}] Resolving upstream branch...")
    branch = resolve_default_branch(mod_id, manual_branch)
    print(f"[{mod_id}] Upstream branch: {branch}")

    # Fetch canonical en_us.json
    en_url = build_raw_url(mod_id, branch, "en_us.json")
    en_bytes, en_status = fetch_file_content(en_url)

    if en_status != 200 or not en_bytes:
        print(f"[{mod_id}] ERROR: Failed to fetch en_us.json from {en_url} (HTTP {en_status})")
        return False

    formatted_en = format_json_content(en_bytes)
    atomic_write(en_us_path, formatted_en)
    print(f"[{mod_id}] Updated: {en_us_path.relative_to(base_dir)}")

    # Fetch or generate es_es.json
    if es_es_path.exists() and not force:
        print(f"[{mod_id}] Existing local {es_es_path.relative_to(base_dir)} kept. Use --force to overwrite.")
    else:
        es_url = build_raw_url(mod_id, branch, "es_es.json")
        es_bytes, es_status = fetch_file_content(es_url)

        if es_status == 200 and es_bytes:
            formatted_es = format_json_content(es_bytes)
            atomic_write(es_es_path, formatted_es)
            print(f"[{mod_id}] Downloaded existing upstream: {es_es_path.relative_to(base_dir)}")
        elif es_status == 404:
            # Base template fallback as specified in SPEC-SYNC-001
            print(f"[{mod_id}] Upstream es_es.json not found (HTTP 404).")
            print(f"[{mod_id}] Initializing es_es.json from en_us.json as translation starting template...")
            atomic_write(es_es_path, formatted_en)
            print(f"[{mod_id}] Initialized template: {es_es_path.relative_to(base_dir)}")
        else:
            print(f"[{mod_id}] ERROR: Unexpected response fetching es_es.json (HTTP {es_status})")
            return False

    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Set up workspace hierarchy and download translation assets from Sakura Ryoko upstream repositories."
    )
    parser.add_argument(
        "--mods",
        type=str,
        default="",
        help=f"Comma-separated list of mods to process (defaults to: {', '.join(MOD_LIST)})",
    )
    parser.add_argument(
        "--branch",
        type=str,
        default=None,
        help="Explicit upstream branch override for all target mods",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing local es_es.json files with upstream versions",
    )

    args = parser.parse_args()

    target_mods = [m.strip() for m in args.mods.split(",") if m.strip()] if args.mods else MOD_LIST
    unknown_mods = [m for m in target_mods if m not in MOD_LIST]
    if unknown_mods:
        print(f"Error: Unknown mod(s) requested: {', '.join(unknown_mods)}")
        print(f"Allowed mods: {', '.join(MOD_LIST)}")
        return 1

    workspace_root = Path(__file__).resolve().parent.parent

    print(f"Workspace root: {workspace_root}")
    print(f"Target mods: {', '.join(target_mods)}")
    print("-" * 60)

    success_count = 0
    for mod in target_mods:
        success = setup_mod_workspace(
            base_dir=workspace_root,
            mod_id=mod,
            manual_branch=args.branch,
            force=args.force,
        )
        if success:
            success_count += 1
        print("-" * 60)

    print(f"Setup completed: {success_count}/{len(target_mods)} mods successfully synchronized.")
    return 0 if success_count == len(target_mods) else 1


if __name__ == "__main__":
    sys.exit(main())
