# Contributing Guidelines
# Guía de Contribución

[English](#english) | [Español](#español)

---

<a name="english"></a>
## English

### Overview
This guide explains how to work on the Spanish translations and how to send your work upstream to Sakura Ryoko's official repositories.

Workspace Repository: `https://github.com/Aosiika/masa-mods-spanish-translation`  
Upstream Organization: `https://github.com/sakura-ryoko`

### Golden Rules
1. **Target the Right Repositories**: The ultimate goal is to submit clean Pull Requests directly to Sakura Ryoko's mod repositories (`malilib`, `litematica`, `tweakeroo`, `minihud`, `itemscroller`).
2. **Never Break Variables or Formatting**: Placeholders (`%s`, `%d`, `{0}`) and Minecraft color codes (`§a`, `§c`, `§r`) must remain untouched. If a format code is removed or translated, the game may crash or render broken text.
3. **No Key Desync**: Every key in `en_us.json` must exist in `es_es.json`. Do not invent new keys and do not remove existing ones.
4. **Natural Spanish**: Use clear, natural Spanish used by the technical Minecraft community (redstone, schematic, tick, chunk, etc.), avoiding machine-translation quirks.

### Step-by-Step Workflow

#### 1. Keep Your Files Synced
Before editing, make sure you have the latest English keys from upstream:
```bash
python scripts/setup_workspace.py
```

#### 2. Edit Translations
Open and edit the Spanish translation file for the mod you want to work on:
`mods/<modid>/src/main/resources/assets/<modid>/lang/es_es.json`

Always save your files as **UTF-8 without BOM**.

#### 3. Validate Your Changes
Run our validation tool:
```bash
python scripts/validate_translations.py
```
If you see any warnings or errors regarding placeholders or missing keys, fix them before committing. All checks should pass with exit code `0`.

#### 4. Submitting Upstream to Sakura Ryoko
When your translation is ready, you can submit upstream either automatically or manually:

**Option A (Automated):**
Run our submission script:
```bash
python scripts/submit_upstream_prs.py
```
This automatically forks the repository, creates a dedicated branch (`translation/es_es`), commits the updated `es_es.json`, and opens the Pull Request with complete metadata and reference links.

**Option B (Manual):**
1. Fork Sakura Ryoko's repository for the mod (e.g., `https://github.com/sakura-ryoko/malilib`).
2. Create a new branch based on the active development branch (e.g., `DEV/26.3`).
3. Copy your updated `es_es.json`:
   from `mods/<modid>/src/main/resources/assets/<modid>/lang/es_es.json`
   to `src/main/resources/assets/<modid>/lang/es_es.json` in your fork.
4. Commit with a concise message like:
   `Update Spanish (es_es) localization`
5. Open a Pull Request targeting Sakura Ryoko's active development branch.

---

<a name="español"></a>
## Español

### Introducción
Esta guía explica cómo colaborar en las traducciones al español y cómo enviar tu trabajo directamente a los repositorios oficiales de Sakura Ryoko.

Repositorio de trabajo: `https://github.com/Aosiika/masa-mods-spanish-translation`  
Organización original (Upstream): `https://github.com/sakura-ryoko`

### Reglas Fundamentales
1. **El destino final es Upstream**: El objetivo es enviar Pull Requests limpios a los repositorios de Sakura Ryoko (`malilib`, `litematica`, `tweakeroo`, `minihud`, `itemscroller`).
2. **No toques variables ni códigos de color**: Los marcadores de posición (`%s`, `%d`, `{0}`) y los códigos de color de Minecraft (`§a`, `§c`, `§r`) deben conservarse intactos. Si se alteran o traducen, el juego puede cerrarse o mostrar texto corrupto.
3. **Paridad de claves**: Todas las claves que existan en `en_us.json` deben estar en `es_es.json`. No inventes claves nuevas ni borres claves existentes.
4. **Español natural para Minecraft técnico**: Usa términos familiares para la comunidad técnica hispanohablante (redstone, tick, chunk, hitbox, schematic, etc.), evitando traducciones literales o automáticas.

### Pasos para Colaborar

#### 1. Sincronizar el Espacio de Trabajo
Antes de traducir, asegúrate de tener las últimas claves en inglés descargadas desde upstream:
```bash
python scripts/setup_workspace.py
```

#### 2. Editar las Traducciones
Abre y edita el archivo en español del mod que quieras actualizar:
`mods/<modid>/src/main/resources/assets/<modid>/lang/es_es.json`

Guarda siempre con codificación **UTF-8 sin BOM**.

#### 3. Comprobar la Calidad con el Validador
Ejecuta el script de validación:
```bash
python scripts/validate_translations.py
```
Si el validador señala errores de formato o claves faltantes, revísalos y corrígelos. El script debe terminar con código de salida `0`.

#### 4. Enviar el Pull Request a Sakura Ryoko
Cuando la traducción esté lista, puedes enviarla de forma automática o manual:

**Opción A (Automática):**
Ejecuta nuestro script de publicación:
```bash
python scripts/submit_upstream_prs.py
```
El script creará automáticamente el fork en tu cuenta de GitHub, preparará la rama `translation/es_es`, subirá el archivo `es_es.json` actualizado y abrirá el Pull Request con la descripción y el enlace a este repositorio.

**Opción B (Manual):**
1. Haz un fork del repositorio de Sakura Ryoko del mod que corresponda (por ejemplo, `https://github.com/sakura-ryoko/malilib`).
2. Crea una rama basada en la rama activa de desarrollo (por ejemplo, `DEV/26.3`).
3. Copia tu archivo `es_es.json` actualizado:
   desde `mods/<modid>/src/main/resources/assets/<modid>/lang/es_es.json`
   hacia `src/main/resources/assets/<modid>/lang/es_es.json` en tu fork.
4. Haz un commit con un mensaje claro, como por ejemplo:
   `Update Spanish (es_es) localization`
5. Abre un Pull Request dirigido a la rama de desarrollo activa de Sakura Ryoko detallando los cambios.
