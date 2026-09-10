# Specification: Upstream Synchronization and Translation Governance

## Metadata
- **Specification ID**: SPEC-SYNC-001
- **Status**: Approved
- **Methodology**: Spec Kit (github/spec-kit)
- **Domain**: Minecraft Mod Internationalization (i18n)
- **Target Upstream Organization**: Sakura Ryoko (https://github.com/sakura-ryoko)
- **Ancestral Upstream Reference**: Masa (https://github.com/maruohon)

---

## 1. Context and Objective

The objective of this workspace is to serve as a decentralized, specification-governed environment for maintaining, translating, and updating Spanish localization files (`es_es.json`) for Sakura Ryoko's active forks of Masa's client-side Minecraft mods.

This workspace is **not** an end-user Minecraft Resource Pack. Instead, it is a developer staging repository designed to facilitate direct upstream contributions via Pull Requests. To ensure direct copyability and patch cleanliness without path remapping, the directory hierarchy must mirror the Java source tree of each mod.

### 1.1 Covered Mod Matrix

| Mod ID | Canonical Upstream Repository | Upstream Role |
| :--- | :--- | :--- |
| `malilib` | `https://github.com/sakura-ryoko/malilib` | Core configuration and GUI library |
| `litematica` | `https://github.com/sakura-ryoko/litematica` | Schematic management and display mod |
| `tweakeroo` | `https://github.com/sakura-ryoko/tweakeroo` | Client-side gameplay tweaks and QoL |
| `minihud` | `https://github.com/sakura-ryoko/minihud` | Configurable on-screen info HUD |
| `itemscroller` | `https://github.com/sakura-ryoko/itemscroller` | Inventory manipulation and scrolling |

---

## 2. Structural Contract (Filesystem Hierarchy)

To eliminate conversion overhead when preparing upstream Pull Requests, all translation assets must strictly adhere to the standard Gradle/Fabric resource location:

```text
mods/
  └── <modid>/
        └── src/
              └── main/
                    └── resources/
                          └── assets/
                                └── <modid>/
                                      └── lang/
                                            ├── en_us.json
                                            └── es_es.json
```

### 2.1 File Role Definitions
- **`en_us.json`**: The source of truth (upstream canonical base language). It represents the contract of all active localization keys for the resolved upstream branch.
- **`es_es.json`**: The target translation file. It must correspond key-for-key with `en_us.json`.

---

## 3. Upstream Synchronization Contract

### 3.1 Source of Truth and Branch Resolution
1. The remote upstream source is `https://github.com/sakura-ryoko/<modid>`.
2. The synchronization system must resolve the current active development branch dynamically (e.g., via `git ls-remote --symref` or GitHub repository metadata for default HEAD, currently `DEV/26.3` or newer).
3. Hardcoding static branch names is forbidden in production synchronization flows to prevent drift when Minecraft versions advance. Manual branch override is permitted as an operational flag.

### 3.2 Asset Retrieval Protocol
1. For each mod in the target matrix:
   - Resolve the active upstream default branch.
   - Fetch the upstream `en_us.json` via HTTPS raw endpoints.
   - Fetch the upstream `es_es.json` if present.
2. **Missing Upstream Translation Fallback**:
   - If `es_es.json` does not exist upstream (HTTP 404, as observed in `tweakeroo`), the synchronization pipeline MUST initialize `es_es.json` by copying the fetched `en_us.json` content as a base template.
   - The generated file must then be staged for complete translation.
3. **Download Hygiene**:
   - Downloads must write atomically directly to the target destination.
   - No orphaned temporary files or incomplete downloads may remain on disk upon termination or failure.

---

## 4. Invariant Rules (Linter and Validation Governance)

Any translation file submitted to this repository or prepared for upstream Pull Request must satisfy the following strict technical invariants:

### 4.1 Encoding and File Format Invariants
- **INV-001 (UTF-8 No BOM)**: All `.json` files must be encoded in UTF-8 without Byte Order Mark (BOM).
- **INV-002 (JSON Syntax)**: Files must parse strictly as valid RFC 8259 JSON key-value string dictionaries (`Record<string, string>`). Trailing commas, non-string values, or duplicate keys are prohibited.
- **INV-003 (Indentation)**: Files must be formatted with 2 spaces indentation and terminated with a single trailing newline (`\n`).

### 4.2 Key Parity Invariants
- **INV-004 (Key Completeness)**: Every key present in `en_us.json` must exist in `es_es.json`.
- **INV-005 (Zero Orphaned Keys)**: Every key present in `es_es.json` must exist in `en_us.json`. Any key in `es_es.json` not present in `en_us.json` is marked as obsolete/orphan and must be removed to avoid bloating upstream.

### 4.3 Variable and Placeholder Preservation Invariants
- **INV-006 (Standard Format Specifiers)**: All standard C/Java string format specifiers present in the source string must be preserved exactly in the translated string, including counts and positional indexes.
  - Examples: `%s`, `%d`, `%f`, `%1$s`, `%-10s`, `%.2f`.
  - Modification, removal, or translation of specifiers (e.g., translating `%s` or altering order without index notation) violates this invariant.
- **INV-007 (Positional Brace Placeholders)**: All positional brace tokens (such as `{0}`, `{1}`, `{name}`) must be preserved identically in quantity and identifier.

### 4.4 Minecraft Formatting Code Invariants
- **INV-008 (Section Sign Format Codes)**: Minecraft formatting and color codes using the section symbol (`§` / `\u00A7`) must be preserved verbatim.
  - Colors: `§0` through `§9`, `§a` through `§f`.
  - Format modifiers: `§k` (obfuscated), `§l` (bold), `§m` (strikethrough), `§n` (underline), `§o` (italic), `§r` (reset).
  - The sequence and frequency of formatting codes must match the functional requirements of the text rendering in Minecraft.

### 4.5 Translation Completeness (Informational / Strict Criteria)
- A key in `es_es.json` whose value is identical to `en_us.json` is categorized as **Pending Translation**, unless the value consists solely of proper nouns, technical acronyms, or non-translatable tokens (e.g., `"Masa"`, `"HUD"`, `"X"`, `"Y"`, `"Z"`).
- In standard linting, pending keys generate warnings. In `--strict` CI validation mode, pending keys may block PR merging if configured.

---

## 5. Acceptance Criteria

1. Running `python scripts/setup_workspace.py` creates the five canonical mod directory trees under `mods/` and downloads valid JSON files.
2. If `es_es.json` is missing upstream (e.g., `tweakeroo`), it is safely initialized from `en_us.json`.
3. Running `python scripts/validate_translations.py` audits all 5 mods, reporting:
   - Total keys
   - Translated vs. identical keys
   - Missing keys
   - Orphaned keys
   - Placeholder and Minecraft formatting code discrepancies
4. Validations exit with status code `0` on compliant files and non-zero on invariant violations.
