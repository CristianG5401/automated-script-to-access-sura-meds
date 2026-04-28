# EPS Sura Stealthy Playwright Migration Design

**Date:** 2026-04-27

## Goal

Migrate the project from `pydoll-python` to `SeleniumBase` CDP plus `Playwright` in stealth mode while preserving the current behavior exactly: open the public EPS Sura medications page, wait for the SPA, save an initial screenshot, fill the three pre-captcha fields, verify the populated values, and save a second screenshot without touching the captcha.

## Scope

This design covers a technology migration, not a product behavior change.

Included:

- replace `pydoll-python` with `seleniumbase` and `playwright`
- keep the current single-script project shape
- preserve the current screenshots, selectors, field-filling flow, and value verification
- keep the project ready for future `sb.solve_captcha()` usage

Excluded:

- captcha automation in this iteration
- submit or search actions after the captcha
- a multi-engine abstraction layer
- turning the repository into a large E2E framework

## Constraints

- Primary automation API should be `Playwright`
- Browser startup should use SeleniumBase stealth CDP mode
- Runtime should use the system Chrome browser rather than Playwright-managed browser downloads
- Default browser behavior should remain headless for parity with the current project flow, while keeping the launch easy to switch to headed mode later for debugging or captcha-focused iterations
- The captcha must remain untouched in the current implementation
- The repository should remain intentionally small and easy to learn from

## Architecture

The project will continue to use a single Python entry script as the main integration point. SeleniumBase will launch a stealth Chrome session through `sb_cdp.Chrome()`, and Playwright will attach to that session through `chromium.connect_over_cdp(endpoint_url)`.

Within the same run, both `sb` and `page` remain available:

- `sb` exists to control the stealth browser session and to keep a clean path open for future `sb.solve_captcha()` calls
- `page` is the primary API for page navigation, waiting, filling, selecting, reading field values, and taking screenshots

This keeps the current project small while avoiding a design that would need to be rewritten later if captcha handling is added.

## Why This Approach

Three migration approaches were considered:

1. `sb_cdp` plus Playwright sync
2. `SB(uc=True)` plus nested Playwright sync
3. a hybrid multi-runtime design

The selected approach is `sb_cdp` plus Playwright sync.

Reasons:

- it keeps Playwright as the main automation surface
- it is smaller and simpler than `SB(uc=True)`
- it does not require WebDriver or `chromedriver` for this use case
- SeleniumBase documentation already shows `Stealthy Playwright Mode` working with `sb.solve_captcha()` in this setup
- it preserves a future path to captcha handling without adding extra runtime complexity today

## Planned File Responsibilities

### `take_initial_screenshot.py`

Responsibilities:

- define editable demo configuration
- launch the stealth browser session with `sb_cdp`
- connect Playwright over CDP
- wait for the EPS Sura page to become usable
- locate and fill the three pre-captcha fields
- verify the final field values
- save both screenshots
- close Playwright and SeleniumBase cleanly

### `tests/test_take_initial_screenshot.py`

Responsibilities:

- keep unit tests focused on pure logic and small helpers
- validate text normalization and document type matching
- validate expected-value verification behavior
- avoid brittle full-browser mocks

### `requirements.txt`

Responsibilities:

- declare `seleniumbase`
- declare `playwright`

### `README.md`

Responsibilities:

- explain the new runtime stack
- document installation and execution
- explain that the project uses system Chrome in stealth CDP mode
- preserve the learning-oriented explanation of the current automation flow
- note that the structure leaves room for future `solve_captcha()` usage

### `screenshots/`

Responsibilities:

- store `epssura-medicamentos-inicial.png`
- store `epssura-medicamentos-diligenciado.png`

## Runtime Flow

The migrated script should execute this sequence:

1. create `screenshots/` if needed
2. launch a stealth Chrome session with `sb_cdp.Chrome()` while preserving headless behavior for the current iteration
3. obtain the SeleniumBase CDP endpoint URL
4. connect Playwright to the active browser with `connect_over_cdp()`
5. get the first available page from the connected browser context
6. navigate to the EPS Sura medications URL
7. wait for the SPA shell or target form fields to be ready
8. save the initial screenshot
9. select the configured document type
10. fill the document number
11. fill the birth date
12. verify the selected text and the input values
13. save the populated-form screenshot
14. close Playwright resources and stop the SeleniumBase session

## Form Interaction Strategy

The current selectors and user-visible behavior should remain stable.

Target controls:

- `#selectTipoDoc`
- `#numeroDocumento`
- `input[placeholder="dd/mm/aaaa"]`

The document type selection must stay text-based rather than index-based. The site may expose labels such as `CÉDULA DE CIUDADANÍA` while the script configuration stays short and editable as `CC`. Because of that, the current normalization and alias strategy should be preserved.

The migrated helpers should keep these semantics:

- resolve the select and inputs explicitly
- clear text inputs before inserting new values
- read back the selected label and field values after interaction
- fail if the final values do not match expectations

## Waiting Strategy

Playwright should become the default waiting layer.

Preferred behavior:

- use explicit Playwright waits for relevant selectors
- prefer waiting for the actual form fields over broad fixed delays
- allow short tactical waits only if the live site proves timing-sensitive under stealth mode

The migration should not blindly preserve `asyncio.sleep()` behavior from `pydoll`. The goal is the same stability with a more direct and readable Playwright-based wait model.

## Error Handling

The script should fail loudly and specifically when the page does not behave as expected.

Expected failure modes:

- the SPA shell or relevant fields never appear
- the configured document type cannot be matched to any visible option
- the document number field ends with an unexpected value
- the birth date field ends with an unexpected value

For the document type mismatch case, the error message should include the visible options that were found. For value verification failures, the errors should include both expected and actual values.

The second screenshot must only be saved after successful field verification.

## Testing Strategy

The repository already has small unit tests around the helper behavior. That direction should continue.

Unit tests should cover:

- `normalize_text()` behavior
- `document_type_matches()` behavior
- verification logic for matching and mismatching final values

Unit tests should not attempt to simulate a full Playwright browser session. That would add noise without improving confidence meaningfully for this repository.

Real browser validation should remain a manual smoke test that runs the script against the live public page and confirms that:

- navigation succeeds
- both screenshots are created
- the three fields are visibly populated in the final screenshot
- the captcha remains visible and untouched

## Future `solve_captcha()` Compatibility

Captcha automation is intentionally out of scope for this migration, but the design keeps the project ready for it.

Preparation decisions:

- keep the active SeleniumBase `sb` object alive through the whole flow
- keep Playwright as the main page interaction API
- avoid choosing a design that would require switching to a different runtime layer later

When captcha handling is added in a future iteration, the natural insertion point is after the three pre-captcha fields are filled and before any submit or search action. At that point the script can call `sb.solve_captcha()` while still using the same connected Playwright page.

If future requirements expand from only `solve_captcha()` to broader UC or SeleniumBase-specific control patterns, the project can later move to `SB(uc=True)` with a focused migration. That extra complexity is not justified yet.

## Risks

- the EPS Sura DOM may change and invalidate selectors
- stealth mode timing may require minor waits on some runs
- live document type labels may vary from the configured shorthand values
- anti-bot behavior may change independently of the script

## Success Criteria

The migration is successful when:

- `pydoll-python` is removed from the runtime dependencies
- the project runs with `seleniumbase` plus `playwright`
- the script preserves the current two-screenshot flow
- the three pre-captcha fields are populated and verified successfully
- the captcha remains untouched
- the codebase remains small and understandable
- the structure is ready for future `sb.solve_captcha()` usage without redesigning the core flow
