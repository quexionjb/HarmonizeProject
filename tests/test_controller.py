import threading
import unittest

import numpy as np

from harmonize_core.controller import HarmonizeController, LifecycleState
from harmonize_core.errors import HarmonizeError
from harmonize_core.hue import Channel, EntertainmentArea


AREA = EntertainmentArea(
    resource_id="12345678-1234-1234-1234-123456789abc",
    legacy_group_id="7",
    name="TV area",
    channels=(Channel(channel_id=0, x=0.0, y=0.0, z=0.0),),
)


class FakeHue:
    bridge_ip = "192.0.2.1"

    def __init__(self):
        self.actions = []
        self.fail_start = False

    def application_id(self):
        return "test-app"

    def start_streaming(self, area):
        self.actions.append(("start", area.name))
        if self.fail_start:
            raise HarmonizeError("injected lost start response")

    def stop_streaming(self, area):
        self.actions.append(("stop", area.name))


class FakeCapture:
    def __init__(self, fail_open=False):
        self.fail_open = fail_open
        self.opened = False
        self.closed = False
        self.reset_requested = False
        self.reset_count = 0
        self.frame = np.full((4, 4, 3), (10, 20, 30), dtype=np.uint8)

    def open(self):
        if self.fail_open:
            raise HarmonizeError("injected open failure")
        self.opened = True

    def read(self):
        return self.frame.copy()

    def request_reset(self):
        self.reset_requested = True

    def apply_requested_reset(self):
        self.reset_requested = False
        return False

    def reset(self):
        self.reset_count += 1

    def close(self):
        self.closed = True


class FakeTransport:
    instances = []
    fail_start = False
    fail_send = False
    fail_close = False

    def __init__(self, **kwargs):
        self.started = False
        self.closed = False
        self.packets = []
        type(self).instances.append(self)

    def start(self):
        if self.fail_start:
            raise HarmonizeError("injected transport failure")
        self.started = True

    def send(self, packet):
        if self.fail_send:
            raise HarmonizeError("injected send failure")
        self.packets.append(packet)

    def close(self):
        self.closed = True
        if self.fail_close:
            raise HarmonizeError("injected close failure")


def controller(hue, capture):
    return HarmonizeController(
        hue=hue,
        area=AREA,
        capture=capture,
        client_key="hidden",
        brightness_adjustment=0,
        sample_breadth=0.15,
        update_interval_seconds=0.001,
        single_light=False,
        auto_restart_seconds=0,
        transport_factory=FakeTransport,
    )


class ControllerTests(unittest.TestCase):
    def setUp(self):
        FakeTransport.instances = []
        FakeTransport.fail_start = False
        FakeTransport.fail_send = False
        FakeTransport.fail_close = False

    def test_streaming_session_reaches_ready_and_cleans_up(self):
        hue = FakeHue()
        capture = FakeCapture()
        subject = controller(hue, capture)
        subject.start_background()
        self.assertTrue(subject.ready.wait(1.0))
        self.assertEqual(subject.state, LifecycleState.STREAMING)
        subject.request_stop()
        subject.join(1.0)
        self.assertEqual(subject.state, LifecycleState.IDLE)
        self.assertIsNone(subject.error)
        self.assertEqual(hue.actions, [("start", "TV area"), ("stop", "TV area")])
        self.assertTrue(capture.closed)
        self.assertTrue(FakeTransport.instances[0].closed)
        self.assertTrue(FakeTransport.instances[0].packets)

    def test_capture_failure_does_not_start_hue(self):
        hue = FakeHue()
        capture = FakeCapture(fail_open=True)
        subject = controller(hue, capture)
        subject.run()
        self.assertEqual(subject.state, LifecycleState.ERROR)
        self.assertEqual(hue.actions, [])
        self.assertTrue(capture.closed)

    def test_transport_start_failure_stops_hue(self):
        FakeTransport.fail_start = True
        hue = FakeHue()
        capture = FakeCapture()
        subject = controller(hue, capture)
        subject.run()
        self.assertEqual(subject.state, LifecycleState.ERROR)
        self.assertEqual(hue.actions, [("start", "TV area"), ("stop", "TV area")])
        self.assertTrue(FakeTransport.instances[0].closed)
        self.assertTrue(capture.closed)

    def test_uncertain_hue_start_result_still_requests_stop(self):
        hue = FakeHue()
        hue.fail_start = True
        capture = FakeCapture()
        subject = controller(hue, capture)
        subject.run()
        self.assertEqual(subject.state, LifecycleState.ERROR)
        self.assertEqual(hue.actions, [("start", "TV area"), ("stop", "TV area")])
        self.assertTrue(capture.closed)

    def test_transport_failure_is_not_treated_as_capture_restart(self):
        FakeTransport.fail_send = True
        hue = FakeHue()
        capture = FakeCapture()
        subject = controller(hue, capture)
        subject.auto_restart_seconds = 1
        subject.run()
        self.assertEqual(subject.state, LifecycleState.ERROR)
        self.assertEqual(capture.reset_count, 0)
        self.assertEqual(hue.actions, [("start", "TV area"), ("stop", "TV area")])

    def test_cleanup_continues_when_transport_close_fails(self):
        FakeTransport.fail_close = True
        hue = FakeHue()
        capture = FakeCapture()
        subject = controller(hue, capture)
        subject.start_background()
        self.assertTrue(subject.ready.wait(1.0))
        subject.request_stop()
        subject.join(1.0)
        self.assertEqual(subject.state, LifecycleState.ERROR)
        self.assertTrue(capture.closed)
        self.assertEqual(hue.actions, [("start", "TV area"), ("stop", "TV area")])


if __name__ == "__main__":
    unittest.main()
