import unittest

import take_initial_screenshot as script


class FakeOption:
    def __init__(self, text: str) -> None:
        self._text = text
        self.clicked = False

    @property
    def text(self):
        async def _text():
            return self._text

        return _text()

    async def click_using_js(self) -> None:
        self.clicked = True


class FakeSelect:
    def __init__(self, options: list[FakeOption], selected_text: str = "") -> None:
        self.options = options
        self.selected_text = selected_text

    async def find(self, **kwargs):
        if kwargs.get("tag_name") == "option" and kwargs.get("find_all") is True:
            return self.options
        raise AssertionError(f"Unexpected find kwargs: {kwargs}")

    async def execute_script(self, script_text: str, return_by_value: bool = False):
        del script_text, return_by_value
        return {"result": {"result": {"value": self.selected_text}}}


class FakeInput:
    def __init__(self, value: str = "") -> None:
        self.value = value
        self.actions: list[tuple[str, str | None]] = []

    async def clear(self) -> None:
        self.actions.append(("clear", None))
        self.value = ""

    async def insert_text(self, value: str) -> None:
        self.actions.append(("insert_text", value))
        self.value = value


class FormFillHelpersTests(unittest.IsolatedAsyncioTestCase):
    async def test_select_document_type_clicks_matching_option(self) -> None:
        cc = FakeOption("CC")
        ti = FakeOption("TI")
        select = FakeSelect([ti, cc])

        await script.select_document_type(select, "CC")

        self.assertFalse(ti.clicked)
        self.assertTrue(cc.clicked)

    async def test_select_document_type_supports_eps_sura_aliases(self) -> None:
        cc = FakeOption("CÉDULA DE CIUDADANÍA")
        ti = FakeOption("TARJETA DE IDENTIDAD")
        select = FakeSelect([ti, cc])

        await script.select_document_type(select, "CC")

        self.assertFalse(ti.clicked)
        self.assertTrue(cc.clicked)

    async def test_select_document_type_lists_available_options_when_missing(self) -> None:
        select = FakeSelect([FakeOption("TI"), FakeOption("CE")])

        with self.assertRaises(RuntimeError) as ctx:
            await script.select_document_type(select, "CC")

        message = str(ctx.exception)
        self.assertIn("Document type 'CC' was not found.", message)
        self.assertIn("TI", message)
        self.assertIn("CE", message)

    async def test_fill_document_number_clears_then_inserts(self) -> None:
        document_number_input = FakeInput("old")

        await script.fill_document_number(document_number_input, "123456789")

        self.assertEqual(
            document_number_input.actions,
            [("clear", None), ("insert_text", "123456789")],
        )
        self.assertEqual(document_number_input.value, "123456789")

    async def test_fill_birth_date_clears_then_inserts(self) -> None:
        birth_date_input = FakeInput("old")

        await script.fill_birth_date(birth_date_input, "01/01/1990")

        self.assertEqual(
            birth_date_input.actions,
            [("clear", None), ("insert_text", "01/01/1990")],
        )
        self.assertEqual(birth_date_input.value, "01/01/1990")

    async def test_verify_populated_fields_accepts_complete_values(self) -> None:
        document_type_select = FakeSelect([], selected_text="CC")
        document_number_input = FakeInput("123456789")
        birth_date_input = FakeInput("01/01/1990")

        await script.verify_populated_fields(
            document_type_select,
            document_number_input,
            birth_date_input,
            expected_document_type="CC",
            expected_document_number="123456789",
            expected_birth_date="01/01/1990",
        )

    async def test_verify_populated_fields_accepts_full_eps_sura_label_for_alias(self) -> None:
        document_type_select = FakeSelect(
            [],
            selected_text="CÉDULA DE CIUDADANÍA",
        )

        await script.verify_populated_fields(
            document_type_select,
            FakeInput("123456789"),
            FakeInput("01/01/1990"),
            expected_document_type="CC",
            expected_document_number="123456789",
            expected_birth_date="01/01/1990",
        )

    async def test_verify_populated_fields_requires_expected_document_type(self) -> None:
        document_type_select = FakeSelect([], selected_text="[SELECCIONE]")

        with self.assertRaises(RuntimeError) as ctx:
            await script.verify_populated_fields(
                document_type_select,
                FakeInput("123456789"),
                FakeInput("01/01/1990"),
                expected_document_type="CC",
                expected_document_number="123456789",
                expected_birth_date="01/01/1990",
            )

        self.assertEqual(
            str(ctx.exception),
            "Expected document type 'CC' but found '[SELECCIONE]'.",
        )

    async def test_verify_populated_fields_requires_document_number(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            await script.verify_populated_fields(
                FakeSelect([], selected_text="CC"),
                FakeInput("987654321"),
                FakeInput("01/01/1990"),
                expected_document_type="CC",
                expected_document_number="123456789",
                expected_birth_date="01/01/1990",
            )

        self.assertEqual(
            str(ctx.exception),
            "Expected document number '123456789' but found '987654321'.",
        )

    async def test_verify_populated_fields_requires_birth_date(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            await script.verify_populated_fields(
                FakeSelect([], selected_text="CC"),
                FakeInput("123456789"),
                FakeInput("02/02/2000"),
                expected_document_type="CC",
                expected_document_number="123456789",
                expected_birth_date="01/01/1990",
            )

        self.assertEqual(
            str(ctx.exception),
            "Expected birth date '01/01/1990' but found '02/02/2000'.",
        )
