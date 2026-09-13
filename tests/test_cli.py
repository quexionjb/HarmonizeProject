import unittest

from harmonize_core.cli import build_parser


class CliTests(unittest.TestCase):
    def test_legacy_short_options_remain_available(self):
        args = build_parser().parse_args(
            [
                "-v",
                "-g",
                "7",
                "-b",
                "bridge-id",
                "-i",
                "192.0.2.1",
                "-s",
                "-w",
                "3",
                "-f",
                "sample.mp4",
                "-l",
                "30",
                "-a",
                "8",
            ]
        )
        self.assertTrue(args.verbose)
        self.assertEqual(args.groupid, "7")
        self.assertEqual(args.bridgeid, "bridge-id")
        self.assertEqual(args.bridgeip, "192.0.2.1")
        self.assertTrue(args.single_light)
        self.assertEqual(args.video_wait_time, 3.0)
        self.assertEqual(args.stream_filename, "sample.mp4")
        self.assertEqual(args.light_brightness, 30)
        self.assertEqual(args.auto_restart, 8.0)

    def test_unattended_and_read_only_flags_parse(self):
        args = build_parser().parse_args(
            ["--config", "harmonize.example.toml", "--unattended", "--check-area"]
        )
        self.assertTrue(args.unattended)
        self.assertTrue(args.check_area)


if __name__ == "__main__":
    unittest.main()
