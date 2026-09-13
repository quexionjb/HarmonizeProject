import unittest

from harmonize_core.capture import CaptureSource


class FakeCapture:
    def __init__(self):
        self.released = False

    def isOpened(self):
        return True

    def set(self, key, value):
        return True

    def read(self):
        return True, object()

    def release(self):
        self.released = True


class FakeCv2:
    CAP_GSTREAMER = 1800
    CAP_V4L2 = 200
    CAP_ANY = 0
    CAP_PROP_BUFFERSIZE = 38

    def __init__(self):
        self.calls = []
        self.captures = []

    def VideoCapture(self, *args):
        self.calls.append(args)
        capture = FakeCapture()
        self.captures.append(capture)
        return capture


class CaptureTests(unittest.TestCase):
    def test_file_reset_preserves_original_source(self):
        fake_cv2 = FakeCv2()
        source = CaptureSource(
            stream_source="sample.mp4", cv2_module=fake_cv2
        )
        source.open()
        source.request_reset()
        self.assertTrue(source.apply_requested_reset())
        self.assertEqual(fake_cv2.calls, [("sample.mp4",), ("sample.mp4",)])
        self.assertTrue(fake_cv2.captures[0].released)
        source.close()

    def test_device_reset_preserves_index_and_backend(self):
        fake_cv2 = FakeCv2()
        source = CaptureSource(
            device_index=4, backend="v4l2", cv2_module=fake_cv2
        )
        source.open()
        source.reset()
        self.assertEqual(fake_cv2.calls, [(4, 200), (4, 200)])
        source.close()


if __name__ == "__main__":
    unittest.main()
