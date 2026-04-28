# Initial EPS Sura Screenshot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a minimal Python proof of concept with Pydoll that opens the public EPS Sura medications URL in headless mode and saves a screenshot of the initial viewport.

**Architecture:** Keep the project intentionally small: a `requirements.txt` file for dependencies and a single `take_initial_screenshot.py` script containing all automation logic. The script will launch Chromium in headless mode, navigate to the SPA URL, wait for a likely content container first, fall back to a fixed delay if needed, then save a PNG to a local `screenshots/` directory.

**Tech Stack:** Python, Pydoll (`pydoll-python`), `asyncio`, `pathlib`

---

## Planned File Structure

- `requirements.txt`
  Responsibility: declare the single runtime dependency.
- `take_initial_screenshot.py`
  Responsibility: open the target URL, wait for the page to settle, and save the screenshot.
- `screenshots/`
  Responsibility: store the generated PNG output.

## Runtime Assumptions

- Target URL: `https://portaleps.epssura.com/ServiciosUnClick/#/solicitudes/medicamentos?App=tramitesExternos`
- Browser mode: headless
- Deliverable: screenshot of the initial viewport only
- Primary wait strategy: `tab.find(class_name="content-app", timeout=10, raise_exc=False)`
- Fallback wait strategy: `asyncio.sleep(5)` if the element is not found
- Additional stabilization: wait `2` extra seconds after detecting the container
- Output path: `screenshots/epssura-medicamentos-inicial.png`

### Task 1: Bootstrap Minimal Project

**Files:**
- Create: `requirements.txt`

- [ ] **Step 1: Write the dependency file**

```txt
pydoll-python
```

- [ ] **Step 2: Install the dependency**

Run: `python -m pip install -r requirements.txt`
Expected: `pydoll-python` and its dependencies install without errors.

### Task 2: Implement the Screenshot Script

**Files:**
- Create: `take_initial_screenshot.py`

- [ ] **Step 1: Write the script**

```python
import asyncio
from pathlib import Path

from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

URL = "https://portaleps.epssura.com/ServiciosUnClick/#/solicitudes/medicamentos?App=tramitesExternos"
OUTPUT_PATH = Path("screenshots/epssura-medicamentos-inicial.png")
ELEMENT_TIMEOUT_SECONDS = 10
FALLBACK_DELAY_SECONDS = 5
POST_DETECTION_DELAY_SECONDS = 2


async def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    options = ChromiumOptions()
    options.headless = True

    async with Chrome(options=options) as browser:
        tab = await browser.start()

        print(f"Opening URL: {URL}")
        await tab.go_to(URL)

        print("Waiting for SPA shell...")
        app_container = await tab.find(
            class_name="content-app",
            timeout=ELEMENT_TIMEOUT_SECONDS,
            raise_exc=False,
        )

        if app_container is None:
            print(
                f"Container not found after {ELEMENT_TIMEOUT_SECONDS}s. "
                f"Using fallback wait of {FALLBACK_DELAY_SECONDS}s."
            )
            await asyncio.sleep(FALLBACK_DELAY_SECONDS)
        else:
            print(
                "Container detected. Waiting a bit longer for route content "
                "to settle."
            )
            await asyncio.sleep(POST_DETECTION_DELAY_SECONDS)

        print(f"Saving screenshot to: {OUTPUT_PATH}")
        await tab.take_screenshot(str(OUTPUT_PATH), quality=100)
        print("Screenshot saved successfully.")


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 2: Verify the selector assumption**

Validation target:
- `content-app` exists in the SPA shell HTML and is enough for this first learning-oriented deliverable.
- If the screenshot is still too early, the next iteration should switch to a route-specific selector or longer stabilization.

### Task 3: Run a Manual Smoke Test

**Files:**
- Run only: `take_initial_screenshot.py`

- [ ] **Step 1: Execute the script**

Run: `python take_initial_screenshot.py`
Expected:
- console logs show navigation, waiting, and screenshot stages
- imports succeed
- Chromium runs in the background
- the PNG file is created

- [ ] **Step 2: Confirm the output file exists**

Run: `ls screenshots`
Expected: `epssura-medicamentos-inicial.png`

- [ ] **Step 3: Check the visual result**

Expected:
- the PNG shows the public initial viewport of the target page
- if the page looks blank or incomplete, first increase `FALLBACK_DELAY_SECONDS` from `5` to `8`
- if it is still unstable, the next iteration should temporarily run visible mode for inspection

## Risks

- The site is behind Imperva, so behavior may vary depending on timing, browser fingerprint, or network conditions.
- The SPA shell may render before the route-specific content is ready.
- A first screenshot may capture shell plus partial content; that is acceptable for this learning-focused first deliverable.

## Natural Next Iterations

1. Switch to visible mode temporarily to observe the flow.
2. Wait for a selector that is more specific to the medications route.
3. Add `--url` and `--output` CLI arguments once the basic flow works.
