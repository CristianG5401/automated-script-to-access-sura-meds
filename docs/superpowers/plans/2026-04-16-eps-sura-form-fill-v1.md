# EPS Sura Form Fill v1

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the current proof of concept so it fills the three pre-captcha form fields on the EPS Sura medications page and saves a second screenshot showing the populated form.

**Architecture:** Keep the project intentionally small and continue using a single Python script. Reuse the existing browser startup and SPA wait flow, then add focused helper functions for selecting the document type, filling the document number, filling the birth date, validating the populated values, and saving a final screenshot.

**Tech Stack:** Python, pydoll-python, asyncio, pathlib

---

## Planned File Structure

- `take_initial_screenshot.py`
  Responsibility: open the page, wait for the SPA shell, capture the initial screenshot, fill the three fields, verify the populated values, and save the final screenshot.
- `README.md`
  Responsibility: explain the updated behavior, editable demo values, and the two generated screenshots.
- `screenshots/`
  Responsibility: store both the initial and populated-form PNG outputs.

## Runtime Assumptions

- Target URL stays the same:
  `https://portaleps.epssura.com/ServiciosUnClick/#/solicitudes/medicamentos?App=tramitesExternos`
- Browser mode stays headless.
- Captcha remains out of scope and must not be clicked or solved.
- Demo values are edited directly in the script, not passed as CLI arguments.
- Default demo values:
  - `DOCUMENT_TYPE_TEXT = "CC"`
  - `DOCUMENT_NUMBER = "123456789"`
  - `BIRTH_DATE = "01/01/1990"`
- Final screenshot path:
  `screenshots/epssura-medicamentos-diligenciado.png`

### Task 1: Extend Script Configuration

**Files:**
- Modify: `take_initial_screenshot.py`

- [ ] **Step 1: Add editable constants for the form-fill flow**

Add these constants near the existing URL/output configuration:

```python
DOCUMENT_TYPE_TEXT = "CC"
DOCUMENT_NUMBER = "123456789"
BIRTH_DATE = "01/01/1990"
FILLED_OUTPUT_PATH = Path("screenshots/epssura-medicamentos-diligenciado.png")
```

- [ ] **Step 2: Keep both screenshot outputs inside the same directory**

Ensure the script still creates the parent directory before any screenshot write:

```python
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
```

Expected:
- both `OUTPUT_PATH` and `FILLED_OUTPUT_PATH` resolve inside `screenshots/`
- the script remains easy to edit for learning purposes

### Task 2: Add Focused Helpers for Field Interaction

**Files:**
- Modify: `take_initial_screenshot.py`

- [ ] **Step 1: Add a helper to wait for the form elements**

Add a helper that resolves the three target elements after the SPA shell is ready:

```python
async def get_form_fields(tab):
    document_type_select = await tab.find(id="selectTipoDoc", timeout=10)
    document_number_input = await tab.find(id="numeroDocumento", timeout=10)
    birth_date_input = await tab.find(
        tag_name="input",
        placeholder="dd/mm/aaaa",
        timeout=10,
    )
    return document_type_select, document_number_input, birth_date_input
```

- [ ] **Step 2: Add a helper to select the document type by visible text**

Implement selection by inspecting the `<option>` elements and matching trimmed visible text:

```python
async def select_document_type(document_type_select, target_text: str) -> None:
    options = await document_type_select.find(tag_name="option", find_all=True)

    for option in options:
        option_text = (await option.text).strip()
        if option_text == target_text:
            await option.click_using_js()
            return

    available_options = [(await option.text).strip() for option in options]
    raise RuntimeError(
        f"Document type '{target_text}' was not found. "
        f"Available options: {available_options}"
    )
```

Expected:
- the script selects `CC` through the `selectTipoDoc` control
- if `CC` is not available, the error message lists the visible options

- [ ] **Step 3: Add helpers to fill the text-based fields**

Add one helper per field so the main flow stays readable:

```python
async def fill_document_number(document_number_input, value: str) -> None:
    await document_number_input.clear()
    await document_number_input.insert_text(value)


async def fill_birth_date(birth_date_input, value: str) -> None:
    await birth_date_input.clear()
    await birth_date_input.insert_text(value)
```

Expected:
- both inputs are cleared before inserting demo values
- `insert_text()` dispatches DOM events so the SPA detects the change

### Task 3: Verify the Populated Form Before Final Screenshot

**Files:**
- Modify: `take_initial_screenshot.py`

- [ ] **Step 1: Add a helper to validate the populated values**

Add a verification helper that checks the three fields after interaction:

```python
async def verify_populated_fields(
    document_type_select,
    document_number_input,
    birth_date_input,
) -> None:
    selected_value = await document_type_select.execute_script(
        "function() { return this.options[this.selectedIndex]?.text || ''; }",
        return_by_value=True,
    )
    selected_text = selected_value["result"]["result"]["value"].strip()

    number_value = document_number_input.attributes.get("value", "").strip()
    birth_date_value = birth_date_input.attributes.get("value", "").strip()

    if not selected_text:
        raise RuntimeError("Document type was not selected.")
    if not number_value:
        raise RuntimeError("Document number input is empty after filling.")
    if not birth_date_value:
        raise RuntimeError("Birth date input is empty after filling.")
```

- [ ] **Step 2: Call the helpers in the main flow**

After the SPA wait and initial screenshot, wire the new interaction flow into `main()`:

```python
document_type_select, document_number_input, birth_date_input = await get_form_fields(tab)

print(f"Selecting document type: {DOCUMENT_TYPE_TEXT}")
await select_document_type(document_type_select, DOCUMENT_TYPE_TEXT)

print(f"Filling document number: {DOCUMENT_NUMBER}")
await fill_document_number(document_number_input, DOCUMENT_NUMBER)

print(f"Filling birth date: {BIRTH_DATE}")
await fill_birth_date(birth_date_input, BIRTH_DATE)

print("Verifying populated fields...")
await verify_populated_fields(
    document_type_select,
    document_number_input,
    birth_date_input,
)

print(f"Saving populated-form screenshot to: {FILLED_OUTPUT_PATH}")
await tab.take_screenshot(str(FILLED_OUTPUT_PATH), quality=100)
print("Populated-form screenshot saved successfully.")
```

Expected:
- the captcha remains untouched
- the second screenshot is taken only after successful field verification

### Task 4: Update the Learning Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update the behavior description**

Replace the current one-screenshot summary with a two-stage description:

```md
El script ahora hace este flujo:

1. crea la carpeta `screenshots/` si no existe
2. inicia Chrome en modo headless
3. abre la URL pública de EPS Sura
4. espera el contenedor principal de la SPA
5. guarda un screenshot inicial
6. llena tipo de documento, número de documento y fecha de nacimiento
7. deja el captcha intacto
8. guarda un segundo screenshot con el formulario diligenciado
```

- [ ] **Step 2: Document the editable demo values and outputs**

Add a section like this:

```md
## Valores demo editables

Dentro de `take_initial_screenshot.py` puedes cambiar fácilmente:

- `DOCUMENT_TYPE_TEXT`
- `DOCUMENT_NUMBER`
- `BIRTH_DATE`

## Screenshots generados

- `screenshots/epssura-medicamentos-inicial.png`
- `screenshots/epssura-medicamentos-diligenciado.png`
```

- [ ] **Step 3: Document the captcha boundary explicitly**

Add a note that makes the scope clear:

```md
## Alcance actual

Este proyecto llena únicamente los tres campos previos al captcha.
No intenta resolver, hacer click ni automatizar el captcha.
```

### Task 5: Run a Manual Smoke Test

**Files:**
- Run only: `take_initial_screenshot.py`

- [ ] **Step 1: Execute the updated script**

Run:

```bash
.venv/bin/python take_initial_screenshot.py
```

Expected console flow:
- URL opens successfully
- SPA shell wait completes
- initial screenshot is saved
- document type is selected
- document number is filled
- birth date is filled
- field verification passes
- populated-form screenshot is saved

- [ ] **Step 2: Confirm both output files exist**

Run:

```bash
ls screenshots
```

Expected:

```text
epssura-medicamentos-diligenciado.png
epssura-medicamentos-inicial.png
```

- [ ] **Step 3: Check the visual result**

Expected in `epssura-medicamentos-diligenciado.png`:
- `CC` appears selected in the first field
- the document number field contains `123456789`
- the birth date field contains `01/01/1990`
- the captcha is still visible and untouched

## Risks

- The select may use different visible labels than expected, so `CC` might need to be changed to match the live DOM text.
- The date input may use a mask or framework behavior that requires event-driven text insertion rather than plain typing.
- Imperva or site timing differences may still make the page slower to stabilize in some runs.

## Natural Next Iterations

1. Add optional CLI arguments for document type, document number, and birth date.
2. Add a visible-browser mode for easier inspection while learning.
3. Click the submit/search button after the captcha is solved manually by a human.
