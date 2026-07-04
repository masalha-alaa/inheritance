import unittest
from unittest.mock import Mock, patch

import settings
from fiqh_engine import create_fiqh, resolve_fiqh_engine_name


class FiqhEngineTest(unittest.TestCase):
    def test_uses_settings_when_cli_argument_is_missing(self):
        self.assertEqual(settings.FIQH_ENGINE, resolve_fiqh_engine_name([]))

    def test_cli_argument_overrides_settings(self):
        self.assertEqual("fiqh_local", resolve_fiqh_engine_name(["--fiqh-engine", "fiqh_local"]))
        self.assertEqual("fiqh", resolve_fiqh_engine_name(["--fiqh-engine=fiqh"]))

    def test_unrelated_cli_arguments_are_ignored(self):
        self.assertEqual(settings.FIQH_ENGINE, resolve_fiqh_engine_name(["--workers", "1"]))

    def test_invalid_settings_value_is_rejected(self):
        with patch("fiqh_engine.FIQH_ENGINE", "invalid"):
            with self.assertRaises(ValueError):
                resolve_fiqh_engine_name([])

    def test_create_fiqh_imports_and_initializes_selected_engine(self):
        fiqh = Mock()
        fiqh_module = Mock()
        fiqh_module.Fiqh.return_value = fiqh

        with patch("fiqh_engine.import_module", return_value=fiqh_module) as import_module:
            result = create_fiqh("fiqh_local")

        self.assertIs(fiqh, result)
        import_module.assert_called_once_with("fiqh_local")
        fiqh_module.Fiqh.assert_called_once_with()
        fiqh.initialize.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
