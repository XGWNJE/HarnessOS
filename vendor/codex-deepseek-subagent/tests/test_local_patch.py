import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).parents[1] / "scripts" / "codex_deepseek.py"
SPEC = importlib.util.spec_from_file_location("codex_deepseek", MODULE_PATH)
manager = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = manager
SPEC.loader.exec_module(manager)


class LocalPatchTests(unittest.TestCase):
    def test_current_official_catalog_format_and_flash_slug(self):
        payload = {
            "models": [
                {"slug": "deepseek-flash", "input_modalities": ["text", "image"]},
                {"slug": "deepseek-v4-pro", "input_modalities": ["text"]},
            ]
        }
        script = 'cat > "$1" <<\'CODEX_MODELS_JSON\'\n' + json.dumps(payload) + "\nCODEX_MODELS_JSON\n"
        response = mock.MagicMock()
        response.read.return_value = script.encode()
        response.__enter__.return_value = response
        with mock.patch.object(manager.urllib.request, "urlopen", return_value=response):
            models = manager.fetch_official_deepseek_models()
        self.assertEqual(set(models), {"deepseek-flash", "deepseek-v4-pro"})
        self.assertIn("image", models["deepseek-flash"]["input_modalities"])

    def test_merged_catalog_removes_legacy_flash_entries(self):
        base = {
            "models": [
                {"slug": "gpt-parent", "multi_agent_version": "v2"},
                {"slug": "deepseek-v4-flash"},
                {"slug": "deepseek-v4-flash-vision-exp"},
            ]
        }
        official = {slug: {"slug": slug} for slug in manager.SUPPORTED_MODELS}
        merged = manager.merged_catalog(base, official, "gpt-parent")
        slugs = {item["slug"] for item in merged["models"]}
        self.assertNotIn("deepseek-v4-flash", slugs)
        self.assertNotIn("deepseek-v4-flash-vision-exp", slugs)
        self.assertIn("deepseek-flash", slugs)


if __name__ == "__main__":
    unittest.main()
