import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
UNIT = ROOT / "deploy/harmonize-http.service"
INSTALL = ROOT / "deploy/install-http.sh"
UNINSTALL = ROOT / "deploy/uninstall-http.sh"


class HTTPDeploymentTests(unittest.TestCase):
    def test_unit_uses_fixed_port_identity_and_socket(self):
        text = UNIT.read_text()
        required = (
            "Wants=harmonize.service",
            "After=harmonize.service",
            "User=harmonize",
            "Group=harmonize",
            "--bind=0.0.0.0 --port=8765",
            "--socket=/run/harmonize/harmonize.sock",
            "Restart=on-failure",
        )
        for setting in required:
            with self.subTest(setting=setting):
                self.assertIn(setting, text)

    def test_unit_hides_credentials_and_state(self):
        text = UNIT.read_text()
        required = (
            "NoNewPrivileges=yes",
            "CapabilityBoundingSet=",
            "PrivateDevices=yes",
            "ProtectSystem=strict",
            "ProtectHome=yes",
            "RestrictAddressFamilies=AF_UNIX AF_INET",
            "InaccessiblePaths=/etc/harmonize /var/lib/harmonize",
        )
        for setting in required:
            with self.subTest(setting=setting):
                self.assertIn(setting, text)

    def test_install_and_rollback_are_non_overwriting_and_scoped(self):
        install = INSTALL.read_text()
        uninstall = UNINSTALL.read_text()
        self.assertIn("Refusing to replace existing path", install)
        self.assertIn("Refusing to use an unrecognized harmonize account", install)
        self.assertIn("Refusing to remove an unrecognized Harmonize HTTP unit", uninstall)
        self.assertIn("Refusing to remove an unrecognized Harmonize HTTP tool", uninstall)
        self.assertNotIn("harmonize.service", " ".join(
            line for line in uninstall.splitlines()
            if line.startswith("systemctl disable")
        ))


if __name__ == "__main__":
    unittest.main()
