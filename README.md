# Masa Mods - Spanish Translations Workspace
# Espacio de Trabajo de Traducción al Español para Mods de Masa

[English](#english) | [Español](#español)

---

<a name="english"></a>
## English

### What is this repository?
This workspace maintains and updates the Spanish (`es_es.json`) translations for Sakura Ryoko's active forks of Masa's client-side Minecraft mods.

Repository: `https://github.com/Aosiika/masa-mods-spanish-translation`

This project is not a Resource Pack. It is a staging ground designed to prepare Pull Requests directly for Sakura Ryoko's upstream repositories without needing to move, rename, or reformat files.

### Covered Mods
- `malilib` (GUI library and configuration core)
- `litematica` (Schematic manager and display mod)
- `tweakeroo` (Client-side gameplay tweaks)
- `minihud` (Customizable on-screen HUD info lines and renderers)
- `itemscroller` (Inventory and chest scrolling operations)

### Directory Structure
To make upstream contributions effortless, this repository copies the exact folder layout used by the mods:

```text
mods/
  └── <modid>/
        └── src/
              └── main/
                    └── resources/
                          └── assets/
                                └── <modid>/
                                      └── lang/
                                            ├── en_us.json  (Canonical English source)
                                            └── es_es.json  (Spanish translation)
```

You can copy `es_es.json` directly into your fork of Sakura Ryoko's repo at the same path without changing anything.

### Workspace Tools

These scripts require Python 3.8+ (no third-party dependencies):

1. **`python scripts/setup_workspace.py`**
   Connects to GitHub, finds the active development branch (e.g., `DEV/26.3`), downloads the latest `en_us.json`, and downloads or creates `es_es.json`.
   Use this whenever a new Minecraft update arrives to pull in any new English keys.

2. **`python scripts/validate_translations.py`**
   Linter and quality check tool. It verifies:
   - All keys match `en_us.json` (no missing keys, no obsolete keys).
   - Format variables (`%s`, `%d`, `{0}`) are intact.
   - Minecraft color and formatting codes (`§a`, `§c`, `§r`) are preserved.
   - UTF-8 encoding without BOM.

### How to Contribute
Check `CONTRIBUTING.md` for our step-by-step guide to contributing and sending Pull Requests to Sakura Ryoko.

---

<a name="español"></a>
## Español

### ¿Qué es este repositorio?
Este espacio de trabajo mantiene y actualiza las traducciones al español (`es_es.json`) de los mods de Minecraft desarrollados por Masa y mantenidos por Sakura Ryoko.

Repositorio: `https://github.com/Aosiika/masa-mods-spanish-translation`

Este proyecto no es un Resource Pack. Es un entorno de trabajo preparado para contribuir directamente a los repositorios originales de Sakura Ryoko mediante Pull Requests, sin tener que transformar rutas ni renombrar carpetas.

### Mods Cubiertos
- `malilib` (Biblioteca base de configuración e interfaces)
- `litematica` (Gestor y visor de esquemáticas)
- `tweakeroo` (Ajustes y comodidades del lado del cliente)
- `minihud` (Líneas de información en pantalla tipo mini-F3 y visualizadores)
- `itemscroller` (Desplazamiento rápido y manipulación de inventarios)

### Estructura del Repositorio
Para que enviar un Pull Request a Sakura Ryoko sea directo y limpio, este repositorio replica exactamente la ruta interna del código fuente de los mods:

```text
mods/
  └── <modid>/
        └── src/
              └── main/
                    └── resources/
                          └── assets/
                                └── <modid>/
                                      └── lang/
                                            ├── en_us.json  (Original en inglés de referencia)
                                            └── es_es.json  (Traducción al español)
```

De este modo, puedes copiar el archivo `es_es.json` directamente en tu fork del mod en la misma ruta sin pasos intermedios.

### Herramientas del Espacio de Trabajo

Los scripts funcionan con Python 3.8 o superior (solo biblioteca estándar, sin instalar librerías externas):

1. **`python scripts/setup_workspace.py`**
   Se conecta a los repositorios de Sakura Ryoko, detecta la rama activa de desarrollo (`DEV/26.3`) y descarga los archivos de idioma oficiales.
   Úsalo cuando salga una nueva versión de Minecraft para obtener las nuevas cadenas en inglés que se hayan añadido.

2. **`python scripts/validate_translations.py`**
   Linter de calidad técnica. Comprueba automáticamente:
   - Que coincidan exactamente todas las claves (sin claves faltantes ni claves obsoletas).
   - Que las variables (`%s`, `%d`, `{0}`) no se hayan roto ni traducido por error.
   - Que los códigos de color y formato de Minecraft (`§a`, `§c`, `§r`) sigan en su lugar.
   - Codificación UTF-8 pura sin BOM.

### Cómo Contribuir
Consulta `CONTRIBUTING.md` para ver la guía paso a paso para editar traducciones y abrir Pull Requests limpios en los repositorios de Sakura Ryoko.
