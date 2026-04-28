# EPS Sura Stealthy Playwright Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `pydoll-python` with `SeleniumBase` CDP plus sync `Playwright` while preserving the current two-screenshot, pre-captcha EPS Sura flow.

**Architecture:** Keep the project intentionally small with a single Python script. Launch system Chrome in stealth with `sb_cdp.Chrome(headless=True)` and attach Playwright through `connect_over_cdp()` so Playwright becomes the main automation API while SeleniumBase stays available for future `solve_captcha()` usage. Keep document-type matching and populated-value verification as pure helper functions covered by unit tests.

**Tech Stack:** Python, seleniumbase, playwright, unittest, pathlib

---

## Planned File Structure

- `requirements.txt`
  Responsibility: declare the runtime dependencies for the migrated stack.
- `take_initial_screenshot.py`
  Responsibility: launch the stealth browser, connect Playwright over CDP, fill the three pre-captcha fields, verify the result, and save both screenshots.
- `tests/test_take_initial_screenshot.py`
  Responsibility: cover pure helper behavior for normalization, document-type matching, and populated-value verification.
- `README.md`
  Responsibility: explain the new SeleniumBase CDP plus Playwright runtime, installation, execution, editable demo values, and screenshots.
- `screenshots/`
  Responsibility: store `epssura-medicamentos-inicial.png` and `epssura-medicamentos-diligenciado.png`.

## Runtime Assumptions

- Target URL stays the same:
  `https://portaleps.epssura.com/ServiciosUnClick/#/solicitudes/medicamentos?App=tramitesExternos`
- Default browser mode remains headless.
- The browser comes from the local system Chrome launched by SeleniumBase CDP mode.
- `playwright install` is not required for this runtime because Playwright attaches to the existing Chrome session over CDP.
- Captcha remains out of scope and must not be clicked or solved in this iteration.
- Demo values stay editable directly in `take_initial_screenshot.py`.

## Execution Status

- Completed on branch `eps-sura-stealthy-playwright`.
- Final implementation included a few focused hardening changes beyond the initial draft:
  - removed the obsolete `pydoll` test shim after the runtime migration
  - hardened masked birth-date entry with typing plus blur
  - switched screenshot capture to `full_page=True` with a retry after `PlaywrightTimeoutError`
  - added `tests/__init__.py` so `python -m unittest` discovers the suite from the repository root

### Task 1: Replace Dependencies And Lock The New Helper API

**Files:**
- Modify: `requirements.txt`
- Modify: `tests/test_take_initial_screenshot.py`

- [x] **Step 1: Replace the dependency file with the new runtime stack**

Write `requirements.txt` as:

```txt
seleniumbase
playwright
```

- [x] **Step 2: Install the migrated dependencies into the existing virtual environment**

Run:

```bash
.venv/bin/python -m pip install -r requirements.txt
```

Expected:
- `seleniumbase` installs successfully
- `playwright` installs successfully
- no extra `playwright install` step is needed for this project

- [x] **Step 3: Rewrite the unit tests around the planned sync helper API**

Replace `tests/test_take_initial_screenshot.py` with:

```python
import unittest

import take_initial_screenshot as script


class DocumentTypeHelpersTests(unittest.TestCase):
    def test_normalize_text_removes_accents_and_symbols(self) -> None:
        self.assertEqual(
            script.normalize_text("CÉDULA DE CIUDADANÍA"),
            "CEDULADECIUDADANIA",
        )
        self.assertEqual(script.normalize_text("C.C."), "CC")

    def test_document_type_matches_supports_eps_sura_aliases(self) -> None:
        self.assertTrue(script.document_type_matches("CÉDULA DE CIUDADANÍA", "CC"))
        self.assertTrue(script.document_type_matches("Tarjeta de identidad", "TI"))

    def test_find_matching_document_type_returns_visible_option(self) -> None:
        option_text = script.find_matching_document_type(
            ["[ Seleccione ]", "CÉDULA DE CIUDADANÍA", "TARJETA DE IDENTIDAD"],
            "CC",
        )

        self.assertEqual(option_text, "CÉDULA DE CIUDADANÍA")

    def test_find_matching_document_type_lists_visible_options_when_missing(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            script.find_matching_document_type(["TI", "CE"], "CC")

        message = str(ctx.exception)
        self.assertIn("Document type 'CC' was not found.", message)
        self.assertIn("TI", message)
        self.assertIn("CE", message)


class VerificationHelpersTests(unittest.TestCase):
    def test_verify_populated_values_accepts_matching_values(self) -> None:
        script.verify_populated_values(
            selected_text="CC",
            document_number_value="123456789",
            birth_date_value="01/01/1990",
            expected_document_type="CC",
            expected_document_number="123456789",
            expected_birth_date="01/01/1990",
        )

    def test_verify_populated_values_accepts_full_eps_sura_label_for_alias(self) -> None:
        script.verify_populated_values(
            selected_text="CÉDULA DE CIUDADANÍA",
            document_number_value="123456789",
            birth_date_value="01/01/1990",
            expected_document_type="CC",
            expected_document_number="123456789",
            expected_birth_date="01/01/1990",
        )

    def test_verify_populated_values_requires_expected_document_type(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            script.verify_populated_values(
                selected_text="[SELECCIONE]",
                document_number_value="123456789",
                birth_date_value="01/01/1990",
                expected_document_type="CC",
                expected_document_number="123456789",
                expected_birth_date="01/01/1990",
            )

        self.assertEqual(
            str(ctx.exception),
            "Expected document type 'CC' but found '[SELECCIONE]'.",
        )

    def test_verify_populated_values_requires_document_number(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            script.verify_populated_values(
                selected_text="CC",
                document_number_value="987654321",
                birth_date_value="01/01/1990",
                expected_document_type="CC",
                expected_document_number="123456789",
                expected_birth_date="01/01/1990",
            )

        self.assertEqual(
            str(ctx.exception),
            "Expected document number '123456789' but found '987654321'.",
        )

    def test_verify_populated_values_requires_birth_date(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            script.verify_populated_values(
                selected_text="CC",
                document_number_value="123456789",
                birth_date_value="02/02/2000",
                expected_document_type="CC",
                expected_document_number="123456789",
                expected_birth_date="01/01/1990",
            )

        self.assertEqual(
            str(ctx.exception),
            "Expected birth date '01/01/1990' but found '02/02/2000'.",
        )


if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 4: Run the rewritten tests and confirm they fail before the implementation changes**

Run:

```bash
.venv/bin/python -m unittest tests/test_take_initial_screenshot.py -v
```

Expected:
- FAIL
- first failure is an API mismatch such as:

```text
AttributeError: module 'take_initial_screenshot' has no attribute 'find_matching_document_type'
```

### Task 2: Replace The Script With Stealthy Playwright Mode

**Files:**
- Modify: `take_initial_screenshot.py`
- Test: `tests/test_take_initial_screenshot.py`

- [x] **Step 1: Replace the script with the sync SeleniumBase CDP plus Playwright implementation**

Replace `take_initial_screenshot.py` with:

```python
import unicodedata
from pathlib import Path

from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from seleniumbase import sb_cdp

# Configuration kept at module level so the script stays easy to tweak.
URL = "https://portaleps.epssura.com/ServiciosUnClick/#/solicitudes/medicamentos?App=tramitesExternos"
OUTPUT_PATH = Path("screenshots/epssura-medicamentos-inicial.png")
DOCUMENT_TYPE_TEXT = "CC"
DOCUMENT_NUMBER = "123456789"
BIRTH_DATE = "01/01/1990"
FILLED_OUTPUT_PATH = Path("screenshots/epssura-medicamentos-diligenciado.png")
HEADLESS = True
ELEMENT_TIMEOUT_MS = 10_000
POST_LOAD_DELAY_MS = 2_000

APP_SHELL_SELECTOR = ".content-app"
DOCUMENT_TYPE_SELECTOR = "#selectTipoDoc"
DOCUMENT_NUMBER_SELECTOR = "#numeroDocumento"
BIRTH_DATE_SELECTOR = 'input[placeholder="dd/mm/aaaa"]'

DOCUMENT_TYPE_ALIASES = {
    "CC": "CEDULADECIUDADANIA",
    "CE": "CEDULADEEXTRANJERIA",
    "CD": "CARNEDIPLOMATICO",
    "CNV": "CERTIFICADODENACIDOVIVO",
    "NUIP": "NUIP",
    "PA": "PASAPORTE",
    "PASAPORTE": "PASAPORTE",
    "PE": "PERMISOESPECIAL",
    "PEP": "PERMISOESPECIAL",
    "PEF": "PERMISOESPECIALFORMALIZACION",
    "PPT": "PERMISOPORPROTECCIONTEMPORAL",
    "RC": "REGISTROCIVIL",
    "SC": "SALVOCONDUCTODEPERMANENCIA",
    "TI": "TARJETADEIDENTIDAD",
}


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = normalized.encode("ascii", "ignore").decode("ascii")
    return "".join(char for char in without_accents.upper() if char.isalnum())


def document_type_matches(option_text: str, target_text: str) -> bool:
    normalized_option = normalize_text(option_text)
    normalized_target = normalize_text(target_text)
    alias_target = DOCUMENT_TYPE_ALIASES.get(normalized_target)
    candidates = {normalized_target}

    if alias_target:
        candidates.add(alias_target)

    return normalized_option in candidates


def find_matching_document_type(option_texts: list[str], target_text: str) -> str:
    visible_options = [option_text.strip() for option_text in option_texts]

    for option_text in visible_options:
        if document_type_matches(option_text, target_text):
            return option_text

    raise RuntimeError(
        f"Document type '{target_text}' was not found. "
        f"Available options: {visible_options}"
    )


def wait_for_page_ready(page: Page) -> None:
    try:
        page.wait_for_selector(APP_SHELL_SELECTOR, timeout=ELEMENT_TIMEOUT_MS)
    except PlaywrightTimeoutError:
        pass

    try:
        page.wait_for_selector(DOCUMENT_TYPE_SELECTOR, timeout=ELEMENT_TIMEOUT_MS)
        page.wait_for_selector(DOCUMENT_NUMBER_SELECTOR, timeout=ELEMENT_TIMEOUT_MS)
        page.wait_for_selector(BIRTH_DATE_SELECTOR, timeout=ELEMENT_TIMEOUT_MS)
    except PlaywrightTimeoutError as exc:
        raise RuntimeError("EPS Sura form fields did not become ready in time.") from exc

    page.wait_for_timeout(POST_LOAD_DELAY_MS)


def get_form_fields(page: Page) -> tuple[Locator, Locator, Locator]:
    return (
        page.locator(DOCUMENT_TYPE_SELECTOR),
        page.locator(DOCUMENT_NUMBER_SELECTOR),
        page.locator(BIRTH_DATE_SELECTOR),
    )


def select_document_type(document_type_select: Locator, target_text: str) -> str:
    option_texts = [
        option_text.strip()
        for option_text in document_type_select.locator("option").all_inner_texts()
    ]
    matching_option_text = find_matching_document_type(option_texts, target_text)
    document_type_select.select_option(label=matching_option_text)
    return matching_option_text


def fill_document_number(document_number_input: Locator, value: str) -> None:
    document_number_input.clear()
    document_number_input.fill(value)


def fill_birth_date(birth_date_input: Locator, value: str) -> None:
    birth_date_input.clear()
    birth_date_input.fill(value)


def read_selected_document_type(document_type_select: Locator) -> str:
    selected_text = document_type_select.locator("option:checked").text_content()
    return (selected_text or "").strip()


def verify_populated_values(
    *,
    selected_text: str,
    document_number_value: str,
    birth_date_value: str,
    expected_document_type: str,
    expected_document_number: str,
    expected_birth_date: str,
) -> None:
    normalized_selected_text = selected_text.strip()
    normalized_document_number = document_number_value.strip()
    normalized_birth_date = birth_date_value.strip()

    if not document_type_matches(normalized_selected_text, expected_document_type):
        raise RuntimeError(
            f"Expected document type '{expected_document_type}' "
            f"but found '{normalized_selected_text}'."
        )
    if normalized_document_number != expected_document_number.strip():
        raise RuntimeError(
            f"Expected document number '{expected_document_number}' "
            f"but found '{normalized_document_number}'."
        )
    if normalized_birth_date != expected_birth_date.strip():
        raise RuntimeError(
            f"Expected birth date '{expected_birth_date}' "
            f"but found '{normalized_birth_date}'."
        )


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    sb = sb_cdp.Chrome(headless=HEADLESS)

    try:
        endpoint_url = sb.get_endpoint_url()

        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(endpoint_url)
            page = browser.contexts[0].pages[0]

            print(f"Opening URL: {URL}")
            page.goto(URL, wait_until="domcontentloaded")

            print("Waiting for EPS Sura form...")
            wait_for_page_ready(page)

            print(f"Saving screenshot to: {OUTPUT_PATH}")
            page.screenshot(path=str(OUTPUT_PATH))
            print("Screenshot saved successfully.")

            document_type_select, document_number_input, birth_date_input = get_form_fields(page)

            print(f"Selecting document type: {DOCUMENT_TYPE_TEXT}")
            select_document_type(document_type_select, DOCUMENT_TYPE_TEXT)

            print(f"Filling document number: {DOCUMENT_NUMBER}")
            fill_document_number(document_number_input, DOCUMENT_NUMBER)

            print(f"Filling birth date: {BIRTH_DATE}")
            fill_birth_date(birth_date_input, BIRTH_DATE)

            print("Verifying populated fields...")
            verify_populated_values(
                selected_text=read_selected_document_type(document_type_select),
                document_number_value=document_number_input.input_value(),
                birth_date_value=birth_date_input.input_value(),
                expected_document_type=DOCUMENT_TYPE_TEXT,
                expected_document_number=DOCUMENT_NUMBER,
                expected_birth_date=BIRTH_DATE,
            )

            print(f"Saving populated-form screenshot to: {FILLED_OUTPUT_PATH}")
            page.screenshot(path=str(FILLED_OUTPUT_PATH))
            print("Populated-form screenshot saved successfully.")
    finally:
        sb.driver.stop()


if __name__ == "__main__":
    main()
```

- [x] **Step 2: Run the unit tests and verify the pure helper layer passes**

Run:

```bash
.venv/bin/python -m unittest tests/test_take_initial_screenshot.py -v
```

Expected:

```text
Ran 9 tests in

OK
```

- [x] **Step 3: Commit the runtime migration once the helper tests pass**

Run:

```bash
git add requirements.txt take_initial_screenshot.py tests/test_take_initial_screenshot.py
git commit -m "refactor: migrate eps sura flow to stealthy playwright"
```

Expected:
- one commit containing the dependency swap, sync Playwright script, and new unit tests

### Task 3: Rewrite The README For The New Runtime

**Files:**
- Modify: `README.md`

- [x] **Step 1: Replace the README with SeleniumBase CDP plus Playwright instructions**

Replace `README.md` with:

```md
# EPS Sura Stealthy Playwright PoC

Pequeño proyecto de aprendizaje en Python usando `seleniumbase` en modo CDP y `playwright` para abrir la URL pública de medicamentos de EPS Sura en modo headless, guardar una captura inicial y producir una segunda captura con el formulario pre-captcha diligenciado.

## Objetivo

La idea de este proyecto es aprender una automatización web mínima:

- lanzar Chrome del sistema en modo stealth desde Python
- conectar Playwright a esa sesión por CDP
- navegar a una SPA
- esperar a que aparezca el formulario
- llenar los tres campos previos al captcha
- tomar screenshots y guardarlos localmente

## Qué hace el script

El archivo [`take_initial_screenshot.py`](./take_initial_screenshot.py) hace este flujo:

1. crea la carpeta `screenshots/` si no existe
2. inicia Chrome del sistema en modo headless con SeleniumBase CDP
3. conecta Playwright a esa sesión con `connect_over_cdp()`
4. abre la URL pública de EPS Sura
5. espera a que el formulario esté disponible
6. guarda un screenshot inicial
7. llena tipo de documento, número de documento y fecha de nacimiento
8. deja el captcha intacto
9. guarda un segundo screenshot con el formulario diligenciado

## Requisitos

- Python 3
- Google Chrome instalado
- acceso a internet

## Instalación

En macOS y en varios entornos modernos, instalar paquetes con el Python del sistema puede fallar por la política de `externally-managed-environment`. Por eso aquí conviene usar un entorno virtual.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

No hace falta ejecutar `playwright install` porque este proyecto no descarga un navegador propio de Playwright. En su lugar, Playwright se conecta por CDP al Chrome del sistema que SeleniumBase ya lanzó en modo stealth.

## Ejecución

Con el entorno virtual activo:

```bash
python take_initial_screenshot.py
```

Salida esperada en consola:

```text
Opening URL: https://portaleps.epssura.com/ServiciosUnClick/#/solicitudes/medicamentos?App=tramitesExternos
Waiting for EPS Sura form...
Saving screenshot to: screenshots/epssura-medicamentos-inicial.png
Screenshot saved successfully.
Selecting document type: CC
Filling document number: 123456789
Filling birth date: 01/01/1990
Verifying populated fields...
Saving populated-form screenshot to: screenshots/epssura-medicamentos-diligenciado.png
Populated-form screenshot saved successfully.
```

## Valores demo editables

Dentro de `take_initial_screenshot.py` puedes cambiar fácilmente:

- `DOCUMENT_TYPE_TEXT`
- `DOCUMENT_NUMBER`
- `BIRTH_DATE`
- `HEADLESS`

Si quieres depurar visualmente el flujo, cambia `HEADLESS = True` por `HEADLESS = False`.

## Screenshots generados

- `screenshots/epssura-medicamentos-inicial.png`
- `screenshots/epssura-medicamentos-diligenciado.png`

## Alcance actual

Este proyecto llena únicamente los tres campos previos al captcha.
No intenta resolver, hacer click ni automatizar el captcha.

La estructura sí deja preparado el flujo para agregar `sb.solve_captcha()` más adelante si esa necesidad entra en alcance.

## Resultado

Los archivos generados quedan en:

```text
screenshots/epssura-medicamentos-inicial.png
screenshots/epssura-medicamentos-diligenciado.png
```

## Estructura del proyecto

```text
.
├── README.md
├── requirements.txt
├── screenshots/
│   ├── epssura-medicamentos-diligenciado.png
│   └── epssura-medicamentos-inicial.png
├── take_initial_screenshot.py
└── tests/
    └── test_take_initial_screenshot.py
```

## Explicación rápida del código

### `sb_cdp.Chrome()`

SeleniumBase abre Chrome del sistema en un modo stealth y expone una URL de depuración remota para que otra herramienta pueda conectarse al navegador ya abierto.

```python
sb = sb_cdp.Chrome(headless=HEADLESS)
endpoint_url = sb.get_endpoint_url()
```

### `connect_over_cdp()`

Playwright no lanza un navegador nuevo. Se conecta a la sesión de Chrome que SeleniumBase ya abrió:

```python
with sync_playwright() as playwright:
    browser = playwright.chromium.connect_over_cdp(endpoint_url)
    page = browser.contexts[0].pages[0]
```

### `Path`

`Path` de `pathlib` hace más claro el manejo de rutas:

```python
OUTPUT_PATH = Path("screenshots/epssura-medicamentos-inicial.png")
```

### Espera del contenido

La página es una SPA. Eso significa que abrir la URL no garantiza que el contenido visible ya esté listo. Por eso el script espera selectores concretos del formulario:

```python
page.wait_for_selector("#selectTipoDoc", timeout=ELEMENT_TIMEOUT_MS)
page.wait_for_selector("#numeroDocumento", timeout=ELEMENT_TIMEOUT_MS)
page.wait_for_selector('input[placeholder="dd/mm/aaaa"]', timeout=ELEMENT_TIMEOUT_MS)
```

### Verificación posterior al llenado

Después de escribir en los campos, el script vuelve a leer los valores y falla si el DOM no refleja exactamente lo esperado.

## Problemas comunes

### `python: command not found`

Usa `python3` para crear el entorno virtual:

```bash
python3 -m venv .venv
```

Después de activar `.venv`, normalmente ya puedes usar `python`.

### `externally-managed-environment`

Eso pasa cuando intentas instalar dependencias en el Python del sistema. La solución es usar `.venv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### `Chrome` no abre o la sesión CDP falla

Revisa:

- que Google Chrome esté instalado
- que puedas abrir Chrome normalmente en tu máquina
- que no haya restricciones del entorno donde corres el script

### Screenshot en blanco o incompleto

Prueba primero:

- subir `POST_LOAD_DELAY_MS` un poco
- cambiar `HEADLESS` a `False` para observar el flujo
- confirmar que los selectores del formulario no cambiaron

## Dependencias usadas

[`requirements.txt`](./requirements.txt):

```text
seleniumbase
playwright
```

## Ideas para seguir aprendiendo

- agregar argumentos CLI como `--url` y `--output`
- insertar `sb.solve_captcha()` antes de un submit futuro
- esperar un selector más específico si el sitio cambia
- capturar errores de red o timeout con mensajes más claros
- guardar screenshots con timestamp para no sobrescribir resultados
```

- [x] **Step 2: Verify the README no longer documents the old stack**

Run:

```bash
rg -n "pydoll|asyncio|ChromiumOptions" README.md
```

Expected:
- no matches

- [x] **Step 3: Commit the documentation rewrite**

Run:

```bash
git add README.md
git commit -m "docs: update seleniumbase playwright setup"
```

Expected:
- one documentation-only commit describing the new runtime and usage

### Task 4: Run A Manual Smoke Test

**Files:**
- Run only: `take_initial_screenshot.py`

- [x] **Step 1: Execute the migrated script**

Run:

```bash
.venv/bin/python take_initial_screenshot.py
```

Expected console flow:
- URL opens successfully
- form wait completes
- initial screenshot is saved
- document type is selected
- document number is filled
- birth date is filled
- field verification passes
- populated-form screenshot is saved

- [x] **Step 2: Confirm both screenshot outputs exist**

Run:

```bash
ls screenshots
```

Expected:

```text
epssura-medicamentos-diligenciado.png
epssura-medicamentos-inicial.png
```

- [x] **Step 3: Check the visual result**

Expected in `epssura-medicamentos-diligenciado.png`:
- the document type field shows the EPS Sura label that corresponds to `CC`
- the document number field contains `123456789`
- the birth date field contains `01/01/1990`
- the captcha is still visible and untouched

- [x] **Step 4: Re-run the unit tests as a final regression check**

Run:

```bash
.venv/bin/python -m unittest tests/test_take_initial_screenshot.py -v
```

Expected:

```text
Ran 9 tests in

OK
```

## Risks

- The site may expose a different visible label for the `CC` option than expected, so the alias mapping may need one more entry.
- Headless stealth timing may still require a slightly larger `POST_LOAD_DELAY_MS` on some runs.
- The form DOM may change independently of this migration and break a selector.

## Natural Next Iterations

1. Add optional CLI arguments for document type, document number, and birth date.
2. Insert `sb.solve_captcha()` after the pre-captcha fields and before a future submit step.
3. Add an explicit submit/search step for workflows that include a human-approved captcha solve.
