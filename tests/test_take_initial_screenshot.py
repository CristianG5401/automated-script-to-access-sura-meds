import unittest

import take_initial_screenshot as script


class NormalizeTextTests(unittest.TestCase):
    def test_normalize_text_uppercases_and_strips_non_alphanumeric_characters(self) -> None:
        self.assertEqual(
            script.normalize_text(" Cédula de ciudadanía "),
            "CEDULADECIUDADANIA",
        )

    def test_normalize_text_keeps_digits(self) -> None:
        self.assertEqual(script.normalize_text("PEP 123"), "PEP123")


class DocumentTypeMatchesTests(unittest.TestCase):
    def test_document_type_matches_accepts_exact_match(self) -> None:
        self.assertTrue(script.document_type_matches("CC", "CC"))

    def test_document_type_matches_accepts_configured_alias_match(self) -> None:
        self.assertTrue(
            script.document_type_matches("CÉDULA DE CIUDADANÍA", "CC")
        )

    def test_document_type_matches_rejects_non_matching_option(self) -> None:
        self.assertFalse(script.document_type_matches("TI", "CC"))


class FindMatchingDocumentTypeTests(unittest.TestCase):
    def test_find_matching_document_type_returns_exact_match(self) -> None:
        self.assertEqual(
            script.find_matching_document_type(["TI", "CC", "CE"], "CC"),
            "CC",
        )

    def test_find_matching_document_type_returns_alias_match(self) -> None:
        self.assertEqual(
            script.find_matching_document_type(
                ["TARJETA DE IDENTIDAD", "CÉDULA DE CIUDADANÍA"],
                "CC",
            ),
            "CÉDULA DE CIUDADANÍA",
        )

    def test_find_matching_document_type_raises_with_available_options(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            script.find_matching_document_type(["TI", "CE"], "CC")

        message = str(ctx.exception)
        self.assertIn("Document type 'CC' was not found.", message)
        self.assertIn("TI", message)
        self.assertIn("CE", message)


class VerifyPopulatedValuesTests(unittest.TestCase):
    def test_verify_populated_values_accepts_matching_values(self) -> None:
        script.verify_populated_values(
            selected_text="CÉDULA DE CIUDADANÍA",
            document_number_value="123456789",
            birth_date_value="01/01/1990",
            expected_document_type="CC",
            expected_document_number="123456789",
            expected_birth_date="01/01/1990",
        )

    def test_verify_populated_values_rejects_document_type_mismatch(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            script.verify_populated_values(
                selected_text="TI",
                document_number_value="123456789",
                birth_date_value="01/01/1990",
                expected_document_type="CC",
                expected_document_number="123456789",
                expected_birth_date="01/01/1990",
            )

        self.assertEqual(
            str(ctx.exception),
            "Expected document type 'CC' but found 'TI'.",
        )

    def test_verify_populated_values_rejects_document_number_mismatch(self) -> None:
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

    def test_verify_populated_values_rejects_birth_date_mismatch(self) -> None:
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
