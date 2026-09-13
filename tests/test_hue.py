import unittest

from harmonize_core.errors import HarmonizeError
from harmonize_core.hue import (
    resolve_area_name,
    resolve_group_id,
    select_area_interactively,
)


def resource(name="TV area", resource_id="12345678-1234-1234-1234-123456789abc"):
    return {
        "id": resource_id,
        "id_v1": "/groups/7",
        "name": name,
        "status": "inactive",
        "channels": [
            {
                "channel_id": 0,
                "position": {"x": -0.5, "y": 0.0, "z": 0.5},
            }
        ],
    }


class HueResolutionTests(unittest.TestCase):
    def test_exact_name_resolves(self):
        area = resolve_area_name([resource()], "TV area")
        self.assertEqual(area.name, "TV area")
        self.assertEqual(area.legacy_group_id, "7")
        self.assertEqual(area.channels[0].channel_id, 0)
        self.assertEqual(area.status, "inactive")

    def test_name_matching_is_case_sensitive(self):
        with self.assertRaisesRegex(HarmonizeError, '"tv area" was not found'):
            resolve_area_name([resource()], "tv area")

    def test_missing_name_is_actionable(self):
        with self.assertRaisesRegex(HarmonizeError, "hue.entertainment_area"):
            resolve_area_name([resource()], "Missing area")

    def test_duplicate_exact_names_are_rejected(self):
        other = resource(
            resource_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        )
        with self.assertRaisesRegex(HarmonizeError, "2 exact matches"):
            resolve_area_name([resource(), other], "TV area")

    def test_legacy_group_id_resolves(self):
        self.assertEqual(resolve_group_id([resource()], "7").name, "TV area")

    def test_manual_selection_prompts_only_when_multiple(self):
        second = resource(
            name="Desk",
            resource_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )
        second["id_v1"] = "/groups/9"
        prompts = []
        area = select_area_interactively(
            [resource(), second],
            input_fn=lambda prompt: prompts.append(prompt) or "9",
            output_fn=lambda message: None,
        )
        self.assertEqual(area.name, "Desk")
        self.assertEqual(len(prompts), 1)


if __name__ == "__main__":
    unittest.main()
