#!/usr/bin/env python3
"""
scripts/submit_upstream_prs.py
Automates forking, branching, committing, and opening Pull Requests
towards Sakura Ryoko's repositories for Masa mod Spanish translations.
"""

from __future__ import annotations

import base64
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

UPSTREAM_ORG = "sakura-ryoko"
TARGET_BRANCH = "DEV/26.3"
TRANSLATION_BRANCH = "translation/es_es"
CENTRAL_REPO_URL = "https://github.com/Aosiika/masa-mods-spanish-translation"

MOD_CONFIGS = {
    "tweakeroo": {
        "title": "Add complete Spanish (es_es) localization",
        "description": f"""### Summary
This PR adds a complete Spanish (`es_es.json`) localization for Tweakeroo covering all 1,055 keys.

### Details & Methodology
- **Natural Phrasing**: Follows the natural technical vocabulary used by the Hispanic Minecraft community (hotkeys, placement grids, freecam, inventory interaction, block rotation).
- **Human-Reviewed**: Drafted with AI assistance and thoroughly reviewed, edited, and context-checked by a human.
- **Validation**: Strict validation passed (UTF-8 without BOM, 100% key parity with `en_us.json`, all variable placeholders `%s`/`%d` and Minecraft color/formatting codes `§` preserved).

---
Maintained and verified in: {CENTRAL_REPO_URL}
""",
    },
    "minihud": {
        "title": "Update and complete Spanish (es_es) localization",
        "description": f"""### Summary
This PR updates and completes the Spanish (`es_es.json`) localization for MiniHUD, translating over 1,200 previously untranslated English strings and bringing coverage to 100% (1,248 keys).

### Details & Methodology
- **Natural Technical Spanish**: Accurately localizes complex HUD widgets (mobcaps, coordinate projections, bounding boxes, light levels, slime chunks, memory stats) avoiding literal calques.
- **Human-Reviewed**: Reviewed by a human editor to guarantee contextual precision and natural fluency.
- **Validation**: All format codes (`§`), coordinate tags, and placeholders (`{{DAY_1}}`, `{{MOON}}`, `%.2f`, etc.) are 100% verified.

---
Maintained and verified in: {CENTRAL_REPO_URL}
""",
    },
    "malilib": {
        "title": "Update and complete Spanish (es_es) localization",
        "description": f"""### Summary
This PR completes the Spanish (`es_es.json`) translation for MaLiLib, updating all missing configuration options, hotkey descriptions, and GUI widget tooltips (471 keys, 100% coverage).

### Details & Methodology
- **Consistency**: Harmonizes terms across the configuration UI (hotkeys, toggle triggers, modifiers, visual overlays).
- **Human-Reviewed**: Polished and audited to match standard in-game Spanish terminology.
- **Validation**: Fully validated against `en_us.json` with zero missing keys and intact format codes.

---
Maintained and verified in: {CENTRAL_REPO_URL}
""",
    },
    "itemscroller": {
        "title": "Update and complete Spanish (es_es) localization",
        "description": f"""### Summary
This PR updates the Spanish (`es_es.json`) localization for ItemScroller, achieving full 100% coverage (195 keys) and translating all newer inventory scrolling and crafting options.

### Details & Methodology
- **Clear Inventory Terminology**: Clearly explains wheel scrolling, modifier click combinations, bulk moving, chest drop actions, and recipe crafting modes.
- **Human-Reviewed**: Reviewed for clarity and technical accuracy in Spanish.
- **Validation**: 100% key parity and verified UTF-8 formatting.

---
Maintained and verified in: {CENTRAL_REPO_URL}
""",
    },
    "litematica": {
        "title": "Improve and modernize Spanish (es_es) localization",
        "description": f"""### Summary
This PR updates and modernizes the Spanish (`es_es.json`) localization for Litematica (1,182 keys, 100% parity).

### Details & Methodology
- **Natural Phrasing**: Replaces robotic and literal translations with natural terminology familiar to the technical Minecraft community (schematic placements, sub-regions, layer modes, verifier differences, material lists).
- **Human-Reviewed**: Proofread and tested for visual alignment in menus and HUD overlays.
- **Validation**: All variables, coordinate references, and Minecraft formatting codes (`§`) strictly verified.

---
Maintained and verified in: {CENTRAL_REPO_URL}
""",
    },
}


def get_github_token() -> str:
    """Retrieves GitHub token from git credential manager."""
    proc = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n",
        capture_output=True,
        text=True,
        check=True,
    )
    token = None
    for line in proc.stdout.splitlines():
        if line.startswith("password="):
            token = line.split("=", 1)[1]
            break
    if not token:
        raise RuntimeError("No GitHub token found in git credential manager.")
    return token


def github_request(
    endpoint: str,
    token: str,
    method: str = "GET",
    data: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Any]:
    """Makes an authenticated GitHub REST API request."""
    url = f"https://api.github.com{endpoint}" if endpoint.startswith("/") else endpoint
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "MasaModsTranslationSync/1.0",
    }
    req_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read().decode("utf-8")
            return resp.status, json.loads(content) if content else {}
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"raw": body}
        return err.code, parsed


def get_authenticated_user(token: str) -> str:
    status, data = github_request("/user", token)
    if status != 200:
        raise RuntimeError(f"Failed to authenticate with GitHub: {data}")
    return data["login"]


def ensure_fork(mod: str, token: str, username: str) -> None:
    """Ensures a fork of sakura-ryoko/<mod> exists under username."""
    status, _ = github_request(f"/repos/{username}/{mod}", token)
    if status == 200:
        print(f"  [+] Fork {username}/{mod} already exists.")
        return

    print(f"  [*] Creating fork {username}/{mod} from {UPSTREAM_ORG}/{mod}...")
    status, resp = github_request(
        f"/repos/{UPSTREAM_ORG}/{mod}/forks",
        token,
        method="POST",
        data={"default_branch_only": False},
    )
    if status not in (200, 202):
        raise RuntimeError(f"Failed to create fork for {mod}: {resp}")

    # Poll until fork is ready
    for _ in range(20):
        time.sleep(2)
        s, _ = github_request(f"/repos/{username}/{mod}", token)
        if s == 200:
            print(f"  [+] Fork {username}/{mod} is ready.")
            return
    raise TimeoutError(f"Fork {username}/{mod} took too long to become available.")


def ensure_branch(mod: str, token: str, username: str) -> str:
    """Ensures translation branch exists on fork based on target branch. Returns branch commit sha."""
    # 1. Get SHA of target branch on upstream or fork
    status, data = github_request(f"/repos/{username}/{mod}/git/ref/heads/{TARGET_BRANCH}", token)
    if status != 200:
        # Fallback to upstream target branch SHA
        status, data = github_request(f"/repos/{UPSTREAM_ORG}/{mod}/git/ref/heads/{TARGET_BRANCH}", token)
        if status != 200:
            raise RuntimeError(f"Could not find {TARGET_BRANCH} on {UPSTREAM_ORG}/{mod}: {data}")

    base_sha = data["object"]["sha"]

    # 2. Check if translation branch already exists
    status, data = github_request(f"/repos/{username}/{mod}/git/ref/heads/{TRANSLATION_BRANCH}", token)
    if status == 200:
        print(f"  [+] Branch {TRANSLATION_BRANCH} exists on {username}/{mod}.")
        return data["object"]["sha"]

    # 3. Create translation branch
    print(f"  [*] Creating branch {TRANSLATION_BRANCH} at {base_sha[:8]}...")
    status, data = github_request(
        f"/repos/{username}/{mod}/git/refs",
        token,
        method="POST",
        data={
            "ref": f"refs/heads/{TRANSLATION_BRANCH}",
            "sha": base_sha,
        },
    )
    if status not in (200, 201):
        raise RuntimeError(f"Failed to create branch {TRANSLATION_BRANCH}: {data}")

    return base_sha


def commit_translation_file(mod: str, token: str, username: str) -> None:
    """Commits local es_es.json to translation branch in fork."""
    local_file = Path(f"mods/{mod}/src/main/resources/assets/{mod}/lang/es_es.json")
    if not local_file.exists():
        raise FileNotFoundError(f"Local translation file not found: {local_file}")

    file_bytes = local_file.read_bytes()
    encoded_content = base64.b64encode(file_bytes).decode("ascii")

    remote_path = f"src/main/resources/assets/{mod}/lang/es_es.json"
    url_endpoint = f"/repos/{username}/{mod}/contents/{remote_path}?ref={TRANSLATION_BRANCH}"

    # Check if file already exists in branch to obtain sha
    status, data = github_request(url_endpoint, token)
    file_sha = data.get("sha") if status == 200 else None

    # Check if content is already identical
    if status == 200 and data.get("content"):
        remote_normalized = data["content"].replace("\n", "").replace("\r", "")
        if remote_normalized == encoded_content:
            print(f"  [+] {remote_path} is already up to date in {TRANSLATION_BRANCH}.")
            return

    commit_payload: Dict[str, Any] = {
        "message": f"Update Spanish (es_es) localization for {mod}",
        "content": encoded_content,
        "branch": TRANSLATION_BRANCH,
    }
    if file_sha:
        commit_payload["sha"] = file_sha

    print(f"  [*] Committing updated {remote_path} to {username}/{mod}:{TRANSLATION_BRANCH}...")
    status, resp = github_request(
        f"/repos/{username}/{mod}/contents/{remote_path}",
        token,
        method="PUT",
        data=commit_payload,
    )
    if status not in (200, 201):
        raise RuntimeError(f"Failed to commit file to {TRANSLATION_BRANCH}: {resp}")
    print(f"  [+] Commit successful: {resp['commit']['sha'][:8]}")


def create_pull_request(mod: str, token: str, username: str) -> str:
    """Creates Pull Request against sakura-ryoko/<mod>."""
    # 1. Check if PR already exists
    status, prs = github_request(
        f"/repos/{UPSTREAM_ORG}/{mod}/pulls?head={username}:{TRANSLATION_BRANCH}&state=open",
        token,
    )
    if status == 200 and prs:
        pr_url = prs[0]["html_url"]
        print(f"  [+] PR already open: {pr_url}")
        return pr_url

    config = MOD_CONFIGS[mod]
    print(f"  [*] Opening Pull Request to {UPSTREAM_ORG}/{mod}:{TARGET_BRANCH}...")
    status, resp = github_request(
        f"/repos/{UPSTREAM_ORG}/{mod}/pulls",
        token,
        method="POST",
        data={
            "title": config["title"],
            "head": f"{username}:{TRANSLATION_BRANCH}",
            "base": TARGET_BRANCH,
            "body": config["description"],
            "maintainer_can_modify": True,
        },
    )
    if status not in (200, 201):
        raise RuntimeError(f"Failed to create PR for {mod}: {resp}")

    pr_url = resp["html_url"]
    print(f"  [SUCCESS] Pull Request created: {pr_url}")
    return pr_url


def main() -> None:
    print("=== Automating Sakura Ryoko Pull Requests for Masa Mods ===")
    token = get_github_token()
    username = get_authenticated_user(token)
    print(f"Authenticated as: {username}")
    print(f"Target Branch: {TARGET_BRANCH}")
    print(f"Translation Branch: {TRANSLATION_BRANCH}")
    print()

    results = {}
    for mod in ["tweakeroo", "minihud", "malilib", "itemscroller", "litematica"]:
        print(f">>> Processing {mod}...")
        try:
            ensure_fork(mod, token, username)
            ensure_branch(mod, token, username)
            commit_translation_file(mod, token, username)
            pr_url = create_pull_request(mod, token, username)
            results[mod] = {"status": "SUCCESS", "url": pr_url}
        except Exception as err:
            print(f"  [ERROR] {err}")
            results[mod] = {"status": "ERROR", "error": str(err)}
        print()

    print("=== Summary of Pull Requests ===")
    for mod, res in results.items():
        if res["status"] == "SUCCESS":
            print(f"  {mod:14}: {res['url']}")
        else:
            print(f"  {mod:14}: ERROR - {res.get('error')}")


if __name__ == "__main__":
    main()
