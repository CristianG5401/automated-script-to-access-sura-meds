import unicodedata
from pathlib import Path

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError, sync_playwright
from seleniumbase import sb_cdp

URL = "https://portaleps.epssura.com/ServiciosUnClick/#/solicitudes/medicamentos?App=tramitesExternos"
OUTPUT_PATH = Path("screenshots/epssura-medicamentos-inicial.png")
DOCUMENT_TYPE_TEXT = "CC"
DOCUMENT_NUMBER = "123456789"
BIRTH_DATE = "01/01/1990"
FILLED_OUTPUT_PATH = Path("screenshots/epssura-medicamentos-diligenciado.png")
HEADLESS = True
ELEMENT_TIMEOUT_MS = 10_000
POST_DETECTION_DELAY_MS = 2_000
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


def find_matching_document_type(option_texts: list[str], target_text: str) -> str:
    for option_text in option_texts:
        if document_type_matches(option_text, target_text):
            return option_text

    raise RuntimeError(
        f"Document type '{target_text}' was not found. Available options: {option_texts}"
    )


def wait_for_page_ready(page: Page) -> None:
    page.wait_for_load_state("domcontentloaded")
    container = page.locator(".content-app").first
    container.wait_for(state="visible", timeout=ELEMENT_TIMEOUT_MS)
    page.wait_for_timeout(POST_DETECTION_DELAY_MS)


def get_form_fields(page: Page) -> tuple[Locator, Locator, Locator]:
    document_type_select = page.locator("#selectTipoDoc")
    document_number_input = page.locator("#numeroDocumento")
    birth_date_input = page.get_by_placeholder("dd/mm/aaaa")

    document_type_select.wait_for(state="visible", timeout=ELEMENT_TIMEOUT_MS)
    document_number_input.wait_for(state="visible", timeout=ELEMENT_TIMEOUT_MS)
    birth_date_input.wait_for(state="visible", timeout=ELEMENT_TIMEOUT_MS)

    return document_type_select, document_number_input, birth_date_input


def select_document_type(document_type_select: Locator, target_text: str) -> str:
    option_texts = [text.strip() for text in document_type_select.locator("option").all_text_contents()]
    matching_text = find_matching_document_type(option_texts, target_text)
    document_type_select.select_option(label=matching_text)
    return matching_text


def fill_document_number(document_number_input: Locator, value: str) -> None:
    document_number_input.fill(value)


def fill_birth_date(birth_date_input: Locator, value: str) -> None:
    birth_date_input.fill(value)


def read_selected_document_type(document_type_select: Locator) -> str:
    selected_text = document_type_select.locator("option:checked").first.text_content()
    return (selected_text or "").strip()


def save_screenshot(page: Page, path: str) -> None:
    try:
        page.screenshot(path=path)
    except PlaywrightTimeoutError:
        page.screenshot(path=path)


def verify_populated_values(
    *,
    selected_text: str,
    document_number_value: str,
    birth_date_value: str,
    expected_document_type: str,
    expected_document_number: str,
    expected_birth_date: str,
) -> None:
    if not document_type_matches(selected_text, expected_document_type):
        raise RuntimeError(
            f"Expected document type '{expected_document_type}' but found '{selected_text}'."
        )
    if document_number_value.strip() != expected_document_number.strip():
        raise RuntimeError(
            f"Expected document number '{expected_document_number}' but found '{document_number_value}'."
        )
    if birth_date_value.strip() != expected_birth_date.strip():
        raise RuntimeError(
            f"Expected birth date '{expected_birth_date}' but found '{birth_date_value}'."
        )


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    FILLED_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    sb = sb_cdp.Chrome(headless=HEADLESS)

    try:
        endpoint_url = sb.get_endpoint_url()

        with sync_playwright() as playwright:
            browser = playwright.chromium.connect_over_cdp(endpoint_url)

            try:
                context = browser.contexts[0] if browser.contexts else browser.new_context()
                page = context.pages[0] if context.pages else context.new_page()

                print(f"Opening URL: {URL}")
                page.goto(URL, wait_until="domcontentloaded")
                print("Waiting for SPA shell...")
                wait_for_page_ready(page)

                print(f"Saving screenshot to: {OUTPUT_PATH}")
                save_screenshot(page, str(OUTPUT_PATH))
                print("Screenshot saved successfully.")

                document_type_select, document_number_input, birth_date_input = get_form_fields(page)

                print(f"Selecting document type: {DOCUMENT_TYPE_TEXT}")
                selected_text = select_document_type(document_type_select, DOCUMENT_TYPE_TEXT)

                print(f"Filling document number: {DOCUMENT_NUMBER}")
                fill_document_number(document_number_input, DOCUMENT_NUMBER)

                print(f"Filling birth date: {BIRTH_DATE}")
                fill_birth_date(birth_date_input, BIRTH_DATE)

                verify_populated_values(
                    selected_text=read_selected_document_type(document_type_select) or selected_text,
                    document_number_value=document_number_input.input_value(),
                    birth_date_value=birth_date_input.input_value(),
                    expected_document_type=DOCUMENT_TYPE_TEXT,
                    expected_document_number=DOCUMENT_NUMBER,
                    expected_birth_date=BIRTH_DATE,
                )

                print(f"Saving populated-form screenshot to: {FILLED_OUTPUT_PATH}")
                save_screenshot(page, str(FILLED_OUTPUT_PATH))
                print("Populated-form screenshot saved successfully.")
            finally:
                browser.close()
    finally:
        sb.driver.stop()


if __name__ == "__main__":
    main()
