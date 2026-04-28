import asyncio
import inspect
import unicodedata
from pathlib import Path

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

# Configuration kept at module level so the script is easy to tweak while learning.
URL = "https://portaleps.epssura.com/ServiciosUnClick/#/solicitudes/medicamentos?App=tramitesExternos"
OUTPUT_PATH = Path("screenshots/epssura-medicamentos-inicial.png")
DOCUMENT_TYPE_TEXT = "CC"
DOCUMENT_NUMBER = "123456789"
BIRTH_DATE = "01/01/1990"
FILLED_OUTPUT_PATH = Path("screenshots/epssura-medicamentos-diligenciado.png")
ELEMENT_TIMEOUT_SECONDS = 10
FALLBACK_DELAY_SECONDS = 5
POST_DETECTION_DELAY_SECONDS = 2
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
    return normalized_option in {normalized_target, alias_target}


async def get_form_fields(tab):
    document_type_select = await tab.find(id="selectTipoDoc", timeout=10)
    document_number_input = await tab.find(id="numeroDocumento", timeout=10)
    birth_date_input = await tab.find(
        tag_name="input",
        placeholder="dd/mm/aaaa",
        timeout=10,
    )
    return document_type_select, document_number_input, birth_date_input


async def select_document_type(document_type_select, target_text: str) -> None:
    options = await document_type_select.find(tag_name="option", find_all=True)

    for option in options:
        option_text = (await option.text).strip()
        if document_type_matches(option_text, target_text):
            await option.click_using_js()
            return

    available_options = [(await option.text).strip() for option in options]
    raise RuntimeError(
        f"Document type '{target_text}' was not found. "
        f"Available options: {available_options}"
    )


async def fill_document_number(document_number_input, value: str) -> None:
    await document_number_input.clear()
    await document_number_input.insert_text(value)


async def fill_birth_date(birth_date_input, value: str) -> None:
    await birth_date_input.clear()
    await birth_date_input.insert_text(value)


async def _normalize_element_value(value):
    if inspect.isawaitable(value):
        value = await value
    return str(value or "").strip()


async def verify_populated_fields(
    document_type_select,
    document_number_input,
    birth_date_input,
    *,
    expected_document_type: str,
    expected_document_number: str,
    expected_birth_date: str,
) -> None:
    selected_value = await document_type_select.execute_script(
        "function() { return this.options[this.selectedIndex]?.text || ''; }",
        return_by_value=True,
    )
    selected_text = selected_value["result"]["result"]["value"].strip()
    number_value = await _normalize_element_value(document_number_input.value)
    birth_date_value = await _normalize_element_value(birth_date_input.value)

    if not document_type_matches(selected_text, expected_document_type):
        raise RuntimeError(
            f"Expected document type '{expected_document_type}' "
            f"but found '{selected_text}'."
        )
    if number_value != expected_document_number.strip():
        raise RuntimeError(
            f"Expected document number '{expected_document_number}' "
            f"but found '{number_value}'."
        )
    if birth_date_value != expected_birth_date.strip():
        raise RuntimeError(
            f"Expected birth date '{expected_birth_date}' "
            f"but found '{birth_date_value}'."
        )


async def main() -> None:
    # Create the output directory up front so the screenshot write cannot fail
    # just because the folder does not exist yet.
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    options = ChromiumOptions()
    # Run headless so Chrome opens in the background without a visible window.
    options.headless = True

    async with Chrome(options=options) as browser:
        # start() launches the browser process and returns the first tab we can control.
        tab = await browser.start()

        print(f"Opening URL: {URL}")
        await tab.go_to(URL)

        print("Waiting for SPA shell...")
        # EPS Sura is a SPA, so the initial HTML can load before the visible route
        # content is ready. We first wait for a broad container from the app shell.
        app_container = await tab.find(
            class_name="content-app",
            timeout=ELEMENT_TIMEOUT_SECONDS,
            raise_exc=False,
        )

        if app_container is None:
            # If the expected container does not appear, fall back to a fixed delay.
            # This keeps the first prototype simple while still giving the page time to render.
            print(
                f"Container not found after {ELEMENT_TIMEOUT_SECONDS}s. "
                f"Using fallback wait of {FALLBACK_DELAY_SECONDS}s."
            )
            await asyncio.sleep(FALLBACK_DELAY_SECONDS)
        else:
            # Even after the container appears, route-specific content may still be painting.
            # A short extra wait usually produces a more useful first screenshot.
            print(
                "Container detected. Waiting a bit longer for route content "
                "to settle."
            )
            await asyncio.sleep(POST_DETECTION_DELAY_SECONDS)

        print(f"Saving screenshot to: {OUTPUT_PATH}")
        # Pydoll expects the destination as a string path for the screenshot API.
        await tab.take_screenshot(str(OUTPUT_PATH), quality=100)
        print("Screenshot saved successfully.")

        document_type_select, document_number_input, birth_date_input = (
            await get_form_fields(tab)
        )

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
            expected_document_type=DOCUMENT_TYPE_TEXT,
            expected_document_number=DOCUMENT_NUMBER,
            expected_birth_date=BIRTH_DATE,
        )

        print(f"Saving populated-form screenshot to: {FILLED_OUTPUT_PATH}")
        await tab.take_screenshot(str(FILLED_OUTPUT_PATH), quality=100)
        print("Populated-form screenshot saved successfully.")


if __name__ == "__main__":
    asyncio.run(main())
